"""Heritage Foundation Index of Economic Freedom fetcher.

Annual XLSX published at the static subdomain:
    https://static.heritage.org/index/data/<year>/<year>_indexofeconomicfreedom_data.xlsx

The main heritage.org pages block automated access (Cloudflare/Akamai) but
the static subdomain ships files cleanly. curl_cffi with Chrome fingerprint
recommended; plain requests also works on the static subdomain.
"""
from __future__ import annotations

import io
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from curl_cffi import requests as cffi_requests
except ModuleNotFoundError:  # Optional dependency; plain requests works on static.heritage.org.
    cffi_requests = None
    import requests as plain_requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "academic_citation"
ROOT = Path(__file__).resolve().parents[2]

COUNTRY_ALIASES = {
    "BAHAMAS": "BHS",
    "THE BAHAMAS": "BHS",
    "BRUNEI": "BRN",
    "BURMA": "MMR",
    "CAPE VERDE": "CPV",
    "COTE D IVOIRE": "CIV",
    "COTE D'IVOIRE": "CIV",
    "CZECH REPUBLIC": "CZE",
    "DEMOCRATIC REPUBLIC OF CONGO": "COD",
    "EGYPT": "EGY",
    "ESWATINI": "SWZ",
    "GAMBIA": "GMB",
    "THE GAMBIA": "GMB",
    "HONG KONG": "HKG",
    "IRAN": "IRN",
    "KYRGYZ REPUBLIC": "KGZ",
    "LAOS": "LAO",
    "MACAU": "MAC",
    "MICRONESIA": "FSM",
    "NORTH KOREA": "PRK",
    "REPUBLIC OF CONGO": "COG",
    "RUSSIA": "RUS",
    "SAO TOME AND PRINCIPE": "STP",
    "SAINT LUCIA": "LCA",
    "SAINT VINCENT AND THE GRENADINES": "VCT",
    "SLOVAK REPUBLIC": "SVK",
    "SLOVAKIA": "SVK",
    "SOMALIA": "SOM",
    "SOUTH KOREA": "KOR",
    "ST. LUCIA": "LCA",
    "ST. VINCENT AND THE GRENADINES": "VCT",
    "SYRIA": "SYR",
    "TAIWAN": "TWN",
    "TURKEY": "TUR",
    "UNITED STATES": "USA",
    "UNITED KINGDOM": "GBR",
    "VENEZUELA": "VEN",
    "VIETNAM": "VNM",
    "YEMEN": "YEM",
}


class HeritageError(RuntimeError):
    pass


def _norm_country_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").strip().upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _wdi_country_map() -> dict[str, str]:
    """Build a best-effort country-name -> ISO3 map from cached WDI vintages."""
    out: dict[str, str] = {}
    wdi_dir = ROOT / "data" / "vintages" / "world_bank_wdi"
    for path in sorted(wdi_dir.glob("SP.POP.TOTL@*.parquet"), reverse=True):
        try:
            frame = pd.read_parquet(path, columns=["country_iso3", "country_name"])
        except Exception:
            continue
        frame = frame.dropna(subset=["country_iso3", "country_name"]).drop_duplicates()
        for _, row in frame.iterrows():
            iso3 = str(row["country_iso3"]).strip().upper()
            if len(iso3) == 3 and iso3.isalpha():
                out.setdefault(_norm_country_name(row["country_name"]), iso3)
        if out:
            break
    out.update(COUNTRY_ALIASES)
    return out


def _slug_header(value: object) -> str:
    text = str(value or "").strip()
    text = text.replace("Efectiveness", "Effectiveness").replace("Monitary", "Monetary")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text.lower()).strip("_")
    return text


def _clean_index_frame(raw: pd.DataFrame, release_year: int) -> pd.DataFrame:
    header_idx = None
    for idx, row in raw.iterrows():
        values = {str(v).strip().lower() for v in row.dropna().tolist()}
        if "country" in values and "overall score" in values:
            header_idx = idx
            break
    if header_idx is None:
        raise HeritageError("Could not find Country / Overall Score header row")

    headers = [_slug_header(v) or f"unnamed_{i}" for i, v in enumerate(raw.loc[header_idx])]
    df = raw.loc[header_idx + 1:].copy()
    df.columns = headers
    df = df.dropna(how="all")

    if "country" not in df.columns:
        raise HeritageError(f"Country column missing after header normalization: {headers}")
    if "overall_score" not in df.columns:
        raise HeritageError(f"Overall Score column missing after header normalization: {headers}")

    df = df.rename(columns={"country": "country_name"})
    if "year" not in df.columns:
        df["year"] = release_year
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(release_year).astype("Int64")
    for col in df.columns:
        if col not in {"country_name", "region"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif df[col].dtype == "object":
            df[col] = df[col].astype("string")

    country_map = _wdi_country_map()
    df["country_iso3"] = df["country_name"].map(lambda v: country_map.get(_norm_country_name(v)))
    df["value"] = df["overall_score"]

    ordered = [
        "country_iso3", "country_name", "region", "year", "value", "overall_score",
        "property_rights", "judicial_effectiveness", "government_integrity",
        "tax_burden", "government_spending", "fiscal_health", "business_freedom",
        "labor_freedom", "monetary_freedom", "trade_freedom", "investment_freedom",
        "financial_freedom",
    ]
    return df[[c for c in ordered if c in df.columns]].reset_index(drop=True)


def _latest_release_frames() -> list[pd.DataFrame]:
    pub_dir = ROOT / "data" / "vintages" / "heritage_ief"
    latest_by_year: dict[str, Path] = {}
    for path in sorted(pub_dir.glob("ief_20[0-9][0-9]@*.parquet")):
        year = path.name.split("@", 1)[0].removeprefix("ief_")
        latest_by_year[year] = path
    frames = []
    for path in latest_by_year.values():
        frame = pd.read_parquet(path)
        if {"country_iso3", "year", "overall_score"}.issubset(frame.columns):
            frames.append(frame)
    return frames


def fetch(series_id: str = "ief_2026", *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id: e.g. 'ief_2026', 'ief_2024'. Maps to the release-year file."""
    fetch_ts = utc_now()
    if series_id == "ief_panel":
        frames = _latest_release_frames()
        if not frames:
            raise HeritageError("No cleaned annual Heritage IEF releases found; fetch ief_YYYY first")
        df = (
            pd.concat(frames, ignore_index=True)
            .dropna(subset=["country_iso3", "year"])
            .drop_duplicates(["country_iso3", "year"], keep="last")
            .sort_values(["country_iso3", "year"], na_position="last")
            .reset_index(drop=True)
        )
        path_out, sha = write_vintage(
            publisher="heritage_ief",
            series_id=series_id,
            frame=df,
            fetch_utc=fetch_ts,
        )
        years = pd.to_numeric(df["year"], errors="coerce").dropna()
        return FetchResult(
            publisher="heritage_ief",
            series_id=series_id,
            source_url="local://data/vintages/heritage_ief/ief_YYYY",
            methodology_url="https://www.heritage.org/index/about",
            license=LICENSE,
            fetch_utc=fetch_ts,
            rows=len(df),
            frequency="annual",
            units="Index score 0-100 + component pillars",
            currency=None,
            start_date=str(int(years.min())) if not years.empty else None,
            end_date=str(int(years.max())) if not years.empty else None,
            sha256=sha,
            parquet_path=path_out,
            extra={
                "component_releases": sorted(
                    str(int(y)) for y in pd.to_numeric(df["year"], errors="coerce").dropna().unique()
                ),
                "n_columns": len(df.columns),
                "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
            },
        )

    year = series_id.split("_")[-1] if "_" in series_id else "2026"
    if not year.isdigit():
        raise HeritageError(f"Cannot parse year from series_id {series_id!r}; use 'ief_YYYY'")
    url = f"https://static.heritage.org/index/data/{year}/{year}_indexofeconomicfreedom_data.xlsx"
    if cffi_requests is not None:
        r = cffi_requests.get(url, impersonate="chrome", timeout=60)
    else:
        r = plain_requests.get(url, timeout=60)
    r.raise_for_status()
    if len(r.content) < 1000:
        raise HeritageError(f"Heritage returned small payload: {len(r.content)} bytes (may be HTML error)")

    xls = pd.ExcelFile(io.BytesIO(r.content))
    # Heritage files usually have a single data sheet + legend
    sheet = next(
        (s for s in xls.sheet_names if "data" in s.lower() or s.lower().startswith(("country", "score"))),
        xls.sheet_names[0],
    )
    df = _clean_index_frame(xls.parse(sheet, header=None), int(year))

    path_out, sha = write_vintage(
        publisher="heritage_ief",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="heritage_ief",
        series_id=series_id,
        source_url=url,
        methodology_url=f"https://www.heritage.org/index/about",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="Index score 0-100 + component pillars",
        currency=None,
        start_date=str(year),
        end_date=str(year),
        sha256=sha,
        parquet_path=path_out,
        extra={
            "release_year": year,
            "sheet_used": sheet,
            "n_columns": len(df.columns),
            "columns": list(df.columns)[:20],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
