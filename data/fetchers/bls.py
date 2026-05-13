"""US Bureau of Labor Statistics (BLS) Public API v2.

Endpoint: https://api.bls.gov/publicAPI/v2
Auth: optional (free registration for higher rate limits). Without key: 25
queries/day per IP, 10 series per query, 10 years max. With key: 500 queries/day.

BLS covers US labor at higher resolution than FRED's mirror: CPI detailed,
PPI by industry, employment by state/industry, earnings, productivity.
"""
from __future__ import annotations

import io
import os
import zipfile
from datetime import datetime
from itertools import islice

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._http import get as http_get

BASE = "https://api.bls.gov/publicAPI/v2"
QCEW_BASE = "https://data.bls.gov/cew/data/api"
OEWS_BULK_URL = "https://download.bls.gov/pub/time.series/oe/oe.data.1.AllData"
OEWS_ARCHIVE_BASE = "https://www.bls.gov/oes/special-requests"
LICENSE = "public_domain"


class BlsError(RuntimeError):
    pass


STATE_AREA_FIPS = [
    "01000", "02000", "04000", "05000", "06000", "08000", "09000", "10000",
    "11000", "12000", "13000", "15000", "16000", "17000", "18000", "19000",
    "20000", "21000", "22000", "23000", "24000", "25000", "26000", "27000",
    "28000", "29000", "30000", "31000", "32000", "33000", "34000", "35000",
    "36000", "37000", "38000", "39000", "40000", "41000", "42000", "44000",
    "45000", "46000", "47000", "48000", "49000", "50000", "51000", "53000",
    "54000", "55000", "56000",
]

QCEW_PANEL_SPECS = {
    "QCEW_state_total_employment_panel": {
        "industry_code": "10",
        "geography": "state",
        "own_code": "0",
        "agglvl_code": None,
    },
    "QCEW_state_NAICS72_employment_panel": {
        "industry_code": "722",
        "geography": "state",
        "own_code": "5",
        "agglvl_code": "55",
    },
    "QCEW_state_NAICS722_employment_panel": {
        "industry_code": "722",
        "geography": "state",
        "own_code": "5",
        "agglvl_code": "55",
    },
    "QCEW_county_NAICS722_employment_panel": {
        "industry_code": "722",
        "geography": "county",
        "own_code": "5",
        "agglvl_code": "75",
    },
    "QCEW_county_total_employment_panel": {
        "industry_code": "10",
        "geography": "county",
        "own_code": "0",
        "agglvl_code": "70",
    },
}

LAU_PANEL_SPECS = {
    "LAU_state_unemployment_rate_panel": {
        "measure_code": "03",
        "units": "percent unemployment rate",
        "desc": "State monthly unemployment rate, not seasonally adjusted",
    },
    "LAU_state_employment_population_ratio_panel": {
        "measure_code": "07",
        "units": "percent employment-population ratio",
        "desc": "State monthly employment-population ratio, not seasonally adjusted",
    },
}

OEWS_STATE_WAGE_SPECS = {
    "OEWS_state_p10_hourly_wage_panel": {
        "datatype_code": "06",
        "units": "hourly 10th percentile wage, USD",
        "desc": "State all-occupations hourly 10th percentile wage from OEWS/OES time series",
    },
    "OEWS_state_median_hourly_wage_panel": {
        "datatype_code": "08",
        "units": "hourly median wage, USD",
        "desc": "State all-occupations hourly median wage from OEWS/OES time series",
    },
    # Historical OES alias retained because preregistered specs often use OES naming.
    "OES_state_p10_hourly_wage_panel": {
        "datatype_code": "06",
        "units": "hourly 10th percentile wage, USD",
        "desc": "State all-occupations hourly 10th percentile wage from OEWS/OES time series",
    },
    "OES_state_median_hourly_wage_panel": {
        "datatype_code": "08",
        "units": "hourly median wage, USD",
        "desc": "State all-occupations hourly median wage from OEWS/OES time series",
    },
}


def _qcew_years() -> range:
    start = int(os.environ.get("BLS_QCEW_START_YEAR", "1990"))
    end = int(os.environ.get("BLS_QCEW_END_YEAR", "2024"))
    if start > end:
        raise BlsError("BLS_QCEW_START_YEAR must be <= BLS_QCEW_END_YEAR")
    return range(start, end + 1)


def _year_windows(start: int, end: int, width: int = 10) -> list[tuple[int, int]]:
    windows = []
    y = start
    while y <= end:
        z = min(y + width - 1, end)
        windows.append((y, z))
        y = z + 1
    return windows


def _chunks(values: list[str], size: int) -> list[list[str]]:
    it = iter(values)
    out = []
    while chunk := list(islice(it, size)):
        out.append(chunk)
    return out


def _lau_year_bounds() -> tuple[int, int]:
    start = int(os.environ.get("BLS_LAU_START_YEAR", "1990"))
    end = int(os.environ.get("BLS_LAU_END_YEAR", "2024"))
    if start > end:
        raise BlsError("BLS_LAU_START_YEAR must be <= BLS_LAU_END_YEAR")
    return start, end


def _lau_series_id(state_fips: str, measure_code: str) -> str:
    return f"LAUST{state_fips}00000000000{measure_code}"


def _oews_state_series_id(state_fips: str, datatype_code: str) -> str:
    # OE + unadjusted + state area type + area_code + all industries +
    # all occupations + datatype.
    area_code = f"{state_fips}00000"
    return f"OEUS{area_code}000000000000{datatype_code}"


def _post_bls_batch(series_ids: list[str], *, start_year: int, end_year: int) -> dict:
    payload: dict = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    key = os.environ.get("BLS_API_KEY")
    if key:
        payload["registrationkey"] = key
    r = requests.post(
        f"{BASE}/timeseries/data/",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    r.raise_for_status()
    doc = r.json()
    if doc.get("status") != "REQUEST_SUCCEEDED":
        raise BlsError(f"BLS batch failed: {doc.get('status')} — {doc.get('message')}")
    return doc


def _iter_oews_bulk_lines() -> tuple[str, list[str]]:
    """Return transport label plus lines from the blocked OEWS bulk text file.

    The file is large (~300MB). curl_cffi is used first because BLS blocks plain
    bot-like clients on download.bls.gov.
    """
    try:
        from curl_cffi import requests as cffi_requests  # type: ignore
    except Exception:  # noqa: BLE001
        cffi_requests = None

    if cffi_requests is not None:
        r = cffi_requests.get(OEWS_BULK_URL, timeout=240, impersonate="chrome")
        r.raise_for_status()
        text = r.content.decode("utf-8", errors="replace")
        return "curl_cffi.chrome", text.splitlines()

    r = requests.get(
        OEWS_BULK_URL,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"},
        timeout=240,
    )
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace")
    if "Access Denied" in text[:2000]:
        raise BlsError("BLS OEWS bulk download returned Access Denied")
    return "requests", text.splitlines()


def _oews_archive_url(year: int) -> str:
    return f"{OEWS_ARCHIVE_BASE}/oesm{year % 100:02d}st.zip"


def _read_oews_archive_year(year: int, spec: dict[str, str]) -> tuple[pd.DataFrame, str, str]:
    """Read one official OEWS/OES yearly state archive.

    BLS publishes annual state XLSX files in ZIP archives. These are the right
    source for long state wage-percentile panels; the time-series bulk endpoint
    is useful for current-year smoke tests but does not expose the same history.
    """
    url = _oews_archive_url(year)
    payload = http_get(url, timeout=240, zenrows_js_render=False)
    with zipfile.ZipFile(io.BytesIO(payload.content)) as zf:
        names = [
            n for n in zf.namelist()
            if n.lower().endswith((".xlsx", ".xls"))
            and f"state_m{year}" in n.lower()
        ]
        if not names:
            raise BlsError(f"BLS OEWS archive {url}: no spreadsheet found")
        data = zf.read(names[0])
    df = pd.read_excel(io.BytesIO(data), dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]
    needed = {"AREA", "OCC_CODE", "H_PCT10", "H_MEDIAN"}
    missing = needed - set(df.columns)
    if missing:
        raise BlsError(f"BLS OEWS archive {url}: missing columns {sorted(missing)}")
    mask = df["OCC_CODE"].astype(str).str.strip() == "00-0000"
    if "AREA_TYPE" in df.columns:
        mask &= df["AREA_TYPE"].astype(str).str.strip() == "2"
    if "NAICS" in df.columns:
        mask &= df["NAICS"].astype(str).str.strip().isin({"0", "000000"})
    col = "H_PCT10" if spec["datatype_code"] == "06" else "H_MEDIAN"
    state_col = "PRIM_STATE" if "PRIM_STATE" in df.columns else "ST"
    out = df.loc[mask, ["AREA", state_col, col]].copy()
    out = out.rename(columns={col: "value", "AREA": "state_fips", state_col: "state_iso"})
    out["state_fips"] = out["state_fips"].astype(str).str.extract(r"(\d+)")[0].str.zfill(2)
    out["year"] = year
    out["period"] = "A01"
    out["datatype_code"] = spec["datatype_code"]
    out["series_id"] = out["state_fips"].map(lambda s: _oews_state_series_id(s, spec["datatype_code"]))
    out["value"] = pd.to_numeric(out["value"].replace({"#": None, "*": None, "**": None}), errors="coerce")
    out = out.dropna(subset=["value"])
    return out, url, payload.transport


def _fetch_lau_panel(series_id: str, *, fetch_ts: datetime) -> FetchResult:
    spec = LAU_PANEL_SPECS.get(series_id)
    if spec is None:
        raise BlsError(f"unknown LAU panel {series_id!r}")
    start_year, end_year = _lau_year_bounds()
    states = [area[:2] for area in STATE_AREA_FIPS]
    series_to_state = {
        _lau_series_id(state, spec["measure_code"]): state
        for state in states
    }

    rows: list[dict] = []
    for y0, y1 in _year_windows(start_year, end_year):
        for batch in _chunks(list(series_to_state), 10):
            doc = _post_bls_batch(batch, start_year=y0, end_year=y1)
            for series in doc.get("Results", {}).get("series", []):
                sid = series.get("seriesID")
                state_fips = series_to_state.get(sid)
                for obs in series.get("data", []):
                    period = str(obs.get("period") or "")
                    if not period.startswith("M"):
                        continue
                    rows.append(
                        {
                            "series_id": sid,
                            "state_fips": state_fips,
                            "year": obs.get("year"),
                            "period": period,
                            "month": period[1:],
                            "value": obs.get("value"),
                            "measure_code": spec["measure_code"],
                        }
                    )
    out = pd.DataFrame(rows)
    if out.empty:
        raise BlsError(f"BLS LAU {series_id}: no observations")
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["month"] = pd.to_numeric(out["month"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.drop_duplicates(["series_id", "year", "period"]).sort_values(
        ["state_fips", "year", "month"]
    )

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=f"{BASE}/timeseries/data/",
        methodology_url="https://www.bls.gov/lau/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="monthly",
        units=spec["units"],
        currency=None,
        start_date=str(int(out["year"].min())) if len(out) else None,
        end_date=str(int(out["year"].max())) if len(out) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "description": spec["desc"],
            "measure_code": spec["measure_code"],
            "state_count": out["state_fips"].nunique(),
            "bls_registration_key_used": bool(os.environ.get("BLS_API_KEY")),
            "year_start_requested": start_year,
            "year_end_requested": end_year,
        },
    )


def _fetch_oews_state_wage_panel(series_id: str, *, fetch_ts: datetime) -> FetchResult:
    spec = OEWS_STATE_WAGE_SPECS.get(series_id)
    if spec is None:
        raise BlsError(f"unknown OEWS state wage panel {series_id!r}")
    start_year = int(os.environ.get("BLS_OEWS_START_YEAR", "1997"))
    end_year = int(os.environ.get("BLS_OEWS_END_YEAR", "2024"))
    if start_year > end_year:
        raise BlsError("BLS_OEWS_START_YEAR must be <= BLS_OEWS_END_YEAR")

    frames: list[pd.DataFrame] = []
    source_urls: list[str] = []
    transports: set[str] = set()
    archive_start = max(start_year, 2014)
    archive_end = min(end_year, 2024)
    for year in range(archive_start, archive_end + 1):
        try:
            df_year, url, transport = _read_oews_archive_year(year, spec)
        except Exception:
            continue
        if not df_year.empty:
            frames.append(df_year)
            source_urls.append(url)
            transports.add(transport)

    if frames:
        out = pd.concat(frames, ignore_index=True)
        transport = ",".join(sorted(transports))
    else:
        rows: list[dict] = []
        transport, lines = _iter_oews_bulk_lines()
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            sid, year, period, value = parts[:4]
            if len(sid) < 25 or period != "A01":
                continue
            if sid[:2] != "OE" or sid[2] != "U" or sid[3] != "S":
                continue
            area_code = sid[4:11]
            industry_code = sid[11:17]
            occupation_code = sid[17:23]
            datatype_code = sid[23:25]
            if industry_code != "000000" or occupation_code != "000000":
                continue
            if datatype_code != spec["datatype_code"]:
                continue
            state_fips = area_code[:2]
            if f"{state_fips}000" not in STATE_AREA_FIPS:
                continue
            y = int(year)
            if y < start_year or y > end_year:
                continue
            rows.append(
                {
                    "series_id": sid.strip(),
                    "state_fips": state_fips,
                    "year": y,
                    "period": period,
                    "value": value,
                    "datatype_code": datatype_code,
                }
            )
        out = pd.DataFrame(rows)
        source_urls = [OEWS_BULK_URL]
    if out.empty:
        raise BlsError(f"BLS OEWS {series_id}: no observations")
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.drop_duplicates(["series_id", "year", "period"]).sort_values(["state_fips", "year"])

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=source_urls[0] if len(source_urls) == 1 else f"{OEWS_ARCHIVE_BASE}/oesmYYst.zip",
        methodology_url="https://download.bls.gov/pub/time.series/oe/oe.txt",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="annual",
        units=spec["units"],
        currency="USD",
        start_date=str(int(out["year"].min())) if len(out) else None,
        end_date=str(int(out["year"].max())) if len(out) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "description": spec["desc"],
            "datatype_code": spec["datatype_code"],
            "state_count": out["state_fips"].nunique(),
            "source_files": source_urls,
            "http_transport": transport,
            "year_start_requested": start_year,
            "year_end_requested": end_year,
        },
    )


def _fetch_qcew_year(
    year: int,
    *,
    industry_code: str,
    geography: str,
    own_code: str,
    agglvl_code: str | None,
) -> pd.DataFrame:
    url = f"{QCEW_BASE}/{year}/a/industry/{industry_code}.csv"
    r = requests.get(url, timeout=60)
    if r.status_code == 404:
        return pd.DataFrame()
    r.raise_for_status()
    text = r.text.strip()
    if not text:
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(text), dtype=str)
    mask = (
        (df["own_code"] == own_code)
        & (df["industry_code"] == industry_code)
    )
    if agglvl_code is not None:
        mask &= df["agglvl_code"] == agglvl_code
    if geography == "state":
        mask &= df["area_fips"].isin(set(STATE_AREA_FIPS))
    elif geography == "county":
        mask &= df["area_fips"].str.match(r"^\d{5}$", na=False)
        mask &= ~df["area_fips"].str.endswith("000", na=False)
    else:
        raise BlsError(f"unknown QCEW geography {geography!r}")
    return df.loc[mask].copy()


def _fetch_qcew_panel(series_id: str, *, fetch_ts: datetime) -> FetchResult:
    spec = QCEW_PANEL_SPECS.get(series_id)
    if spec is None:
        raise BlsError(f"unknown QCEW panel {series_id!r}")
    industry_code = spec["industry_code"]

    frames: list[pd.DataFrame] = []
    for year in _qcew_years():
        df = _fetch_qcew_year(year, **spec)
        if not df.empty:
            frames.append(df)
    if not frames:
        raise BlsError(f"BLS QCEW {series_id}: no observations")

    out = pd.concat(frames, ignore_index=True)
    numeric_cols = [
        "annual_avg_estabs", "annual_avg_emplvl", "total_annual_wages",
        "taxable_annual_wages", "annual_contributions", "annual_avg_wkly_wage",
        "avg_annual_pay",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "year" in out.columns:
        out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=f"{QCEW_BASE}/{{year}}/a/industry/{industry_code}.csv",
        methodology_url="https://www.bls.gov/cew/downloadable-data-files.htm",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="annual",
        units="establishments, employment, wages, and pay by QCEW area/industry",
        currency="USD",
        start_date=str(int(out["year"].min())) if len(out) else None,
        end_date=str(int(out["year"].max())) if len(out) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "qcew_year_start": min(_qcew_years()),
            "qcew_year_end": max(_qcew_years()),
            "qcew_geography": spec["geography"],
            "qcew_area_count": out["area_fips"].nunique() if "area_fips" in out else None,
            "qcew_industry_code": industry_code,
            "qcew_ownership_code": spec["own_code"],
            "qcew_agglvl_code": spec["agglvl_code"],
        },
    )


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> FetchResult:
    """series_id: BLS series code (e.g., 'CUUR0000SA0' = CPI-U all items)."""
    fetch_ts = utc_now()
    if series_id.startswith("QCEW_"):
        return _fetch_qcew_panel(series_id, fetch_ts=fetch_ts)
    if series_id.startswith("LAU_state_"):
        return _fetch_lau_panel(series_id, fetch_ts=fetch_ts)
    if series_id in OEWS_STATE_WAGE_SPECS:
        return _fetch_oews_state_wage_panel(series_id, fetch_ts=fetch_ts)

    payload: dict = {"seriesid": [series_id]}
    if start_year:
        payload["startyear"] = str(start_year)
    if end_year:
        payload["endyear"] = str(end_year)
    key = os.environ.get("BLS_API_KEY")
    if key:
        payload["registrationkey"] = key
    r = requests.post(
        f"{BASE}/timeseries/data/",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    doc = r.json()
    if doc.get("status") != "REQUEST_SUCCEEDED":
        raise BlsError(f"BLS {series_id} failed: {doc.get('status')} — {doc.get('message')}")
    series_list = doc.get("Results", {}).get("series", [])
    if not series_list:
        raise BlsError(f"BLS {series_id}: no series returned")
    data = series_list[0].get("data", [])
    if not data:
        raise BlsError(f"BLS {series_id}: no observations")
    df = pd.DataFrame(data)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=f"{BASE}/timeseries/data/{series_id}",
        methodology_url=f"https://data.bls.gov/timeseries/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",
        units="per series (index, rate, dollars)",
        currency=None,
        start_date=str(int(df["year"].min())) if len(df) else None,
        end_date=str(int(df["year"].max())) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "bls_registration_key_used": bool(key),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
