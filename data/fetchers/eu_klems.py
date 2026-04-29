"""EU KLEMS Productivity & Growth Accounts fetcher.

Source (LUISS-hosted, current vintage):
    https://euklems-intanprod-llee.luiss.it/

EU KLEMS publishes annual productivity-and-growth-accounts for EU countries
plus US/JP at country and industry (NACE Rev.2) level. The 2024 vintage
covers data through 2022. License is academic / non-commercial use with
attribution required.

Strategy
--------
1. Try auto-download of the bulk zip from the LUISS site (one-shot, ~tens of
   MB). If the vintage URL or hosting URL changes, fall through to step 2.
2. Manual-drop fallback: parse the latest file in data/manual/eu_klems/
   (xlsx, xls, csv, or zip). Same parser used for both paths.

Series (cited by IESET specs)
-------------------------------
    tfp                      — total factor productivity (country level)
    tfp_industry             — TFP at industry level
    unit_labour_cost         — unit labour cost (country / industry)
    value_added_per_hour     — labour productivity per hour
    value_added_per_worker   — labour productivity per worker

Each series is sliced from the full panel into a tidy frame keyed by
(country_iso3, year, [industry_code,] value). Country-level series drop
the industry dimension by selecting the EU KLEMS aggregate code "TOT"
(total economy) when present.
"""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import MANUAL_ROOT, ManualDropError, find_latest

LICENSE = "academic_citation"
PUBLISHER = "eu_klems"

# Best-known current bulk URL (2024 vintage). If this 404s the fetcher falls
# back to manual-drop. Update this as new vintages are published.
BULK_URL = (
    "https://euklems-intanprod-llee.luiss.it/wp-content/uploads/2024/03/"
    "EUKLEMS_INTANProd_2024.zip"
)
METHOD_URL = "https://euklems-intanprod-llee.luiss.it/"

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15 ieset-fetcher"}

# EU KLEMS series_id → (variable code(s) in the published files, dimension).
# EU KLEMS uses short variable codes inside its files; the codes are stable
# across vintages but we accept several aliases each, in case the spreadsheet
# tab/column naming differs by release.
SERIES_SPEC: dict[str, dict] = {
    "tfp": {
        "var_codes": ["TFPva_I", "TFPva", "TFP", "tfp"],
        "industry_level": False,
        "units": "index (1995=100 or per-vintage base year)",
    },
    "tfp_industry": {
        "var_codes": ["TFPva_I", "TFPva", "TFP", "tfp"],
        "industry_level": True,
        "units": "index (1995=100 or per-vintage base year)",
    },
    "unit_labour_cost": {
        "var_codes": ["ULC", "ULC_I", "ulc"],
        "industry_level": True,
        "units": "index",
    },
    "value_added_per_hour": {
        "var_codes": ["VA_QI_PerHour", "LP_H", "VA_per_hour", "LP_hour"],
        "industry_level": True,
        "units": "index / EUR per hour",
    },
    "value_added_per_worker": {
        "var_codes": ["VA_QI_PerPerson", "LP_PER", "LP_pers", "VA_per_worker"],
        "industry_level": True,
        "units": "index / EUR per worker",
    },
}

# EU KLEMS country labels are 2-letter codes. Map to ISO3 for spec consistency.
_ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE",
    "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC", "GR": "GRC",
    "ES": "ESP", "FI": "FIN", "FR": "FRA", "HR": "HRV", "HU": "HUN",
    "IE": "IRL", "IT": "ITA", "LT": "LTU", "LU": "LUX", "LV": "LVA",
    "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU",
    "SE": "SWE", "SI": "SVN", "SK": "SVK", "UK": "GBR", "GB": "GBR",
    "US": "USA", "JP": "JPN",
}


class EUKlemsError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Path / blob acquisition
# ---------------------------------------------------------------------------

def _try_auto_download() -> bytes | None:
    """Attempt to fetch the bulk zip. Return bytes on success, None on failure."""
    try:
        r = requests.get(BULK_URL, headers=UA, timeout=300)
        r.raise_for_status()
        if not r.content or len(r.content) < 1024:
            return None
        return r.content
    except (requests.RequestException, requests.Timeout):
        return None


def _bytes_to_excel_frames(blob: bytes) -> list[tuple[str, pd.DataFrame]]:
    """Given an arbitrary blob (zip-of-xlsx or xlsx), return [(sheet_name, df), ...]."""
    out: list[tuple[str, pd.DataFrame]] = []
    # Is it a zip?
    if blob[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(blob))
        for name in z.namelist():
            lower = name.lower()
            if lower.endswith(".xlsx") or lower.endswith(".xls"):
                with z.open(name) as f:
                    data = f.read()
                try:
                    xls = pd.ExcelFile(io.BytesIO(data))
                except Exception:
                    continue
                for s in xls.sheet_names:
                    try:
                        df = xls.parse(s)
                    except Exception:
                        continue
                    if not df.empty:
                        out.append((f"{Path(name).stem}::{s}", df))
            elif lower.endswith(".csv"):
                with z.open(name) as f:
                    try:
                        df = pd.read_csv(f, low_memory=False)
                    except Exception:
                        continue
                if not df.empty:
                    out.append((Path(name).stem, df))
        return out
    # Plain xlsx/xls bytes
    try:
        xls = pd.ExcelFile(io.BytesIO(blob))
    except Exception:
        return out
    for s in xls.sheet_names:
        try:
            df = xls.parse(s)
        except Exception:
            continue
        if not df.empty:
            out.append((s, df))
    return out


def _path_to_frames(path: Path) -> list[tuple[str, pd.DataFrame]]:
    suf = path.suffix.lower()
    if suf == ".zip":
        return _bytes_to_excel_frames(path.read_bytes())
    if suf in (".xlsx", ".xls"):
        return _bytes_to_excel_frames(path.read_bytes())
    if suf == ".csv":
        df = pd.read_csv(path, low_memory=False)
        return [(path.stem, df)] if not df.empty else []
    raise EUKlemsError(f"unsupported manual-drop file extension: {path.suffix}")


def _acquire_frames() -> tuple[list[tuple[str, pd.DataFrame]], str]:
    """Try auto-download, else manual-drop. Return (frames, source_url)."""
    blob = _try_auto_download()
    if blob is not None:
        frames = _bytes_to_excel_frames(blob)
        if frames:
            return frames, BULK_URL
    # Manual-drop fallback
    try:
        path = find_latest(PUBLISHER, "zip", "xlsx", "xls", "csv")
    except ManualDropError as e:
        target = (MANUAL_ROOT / PUBLISHER).as_posix()
        raise EUKlemsError(
            f"EU KLEMS auto-download failed and no manual file present. "
            f"Either fix BULK_URL in eu_klems.py or place the latest EU KLEMS "
            f"release archive in {target}/. Original error: {e}"
        ) from e
    frames = _path_to_frames(path)
    if not frames:
        raise EUKlemsError(
            f"EU KLEMS manual file {path.name} parsed empty. "
            f"Expected a zip/xlsx with tabular data."
        )
    return frames, f"manual://{path.name}"


# ---------------------------------------------------------------------------
# Reshape: detect tidy long form vs wide-by-year
# ---------------------------------------------------------------------------

_VAR_CANDIDATE_COLS = ("var", "variable", "varcode", "indicator", "code")
_COUNTRY_CANDIDATE_COLS = ("geo", "geo_code", "country", "ctry", "iso", "iso2", "iso3", "nation")
_INDUSTRY_CANDIDATE_COLS = ("nace", "nace_r2", "nace_r2_code", "industry", "ind_code", "ind", "code_industry")
_YEAR_CANDIDATE_COLS = ("year", "time", "period", "yr")
_VALUE_CANDIDATE_COLS = ("value", "obs_value", "val")


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _find_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]
    # substring match
    for cand in candidates:
        for lc, orig in cols_lower.items():
            if cand in lc:
                return orig
    return None


def _melt_if_wide(df: pd.DataFrame) -> pd.DataFrame:
    """If years are columns (e.g. '1995','1996',...), melt to long with 'year','value'."""
    year_cols = [c for c in df.columns if re.fullmatch(r"(19|20)\d{2}", str(c))]
    if not year_cols:
        return df
    id_cols = [c for c in df.columns if c not in year_cols]
    long = df.melt(id_vars=id_cols, value_vars=year_cols,
                   var_name="year", value_name="value")
    long["year"] = pd.to_numeric(long["year"], errors="coerce").astype("Int64")
    return long


def _to_iso3(ser: pd.Series) -> pd.Series:
    s = ser.astype(str).str.strip().str.upper()
    return s.map(lambda v: _ISO2_TO_ISO3.get(v, v if len(v) == 3 else None))


def _slice_series(
    frames: list[tuple[str, pd.DataFrame]],
    series_id: str,
) -> pd.DataFrame:
    spec = SERIES_SPEC[series_id]
    var_codes = {v.lower() for v in spec["var_codes"]}
    industry_level = spec["industry_level"]

    pieces: list[pd.DataFrame] = []
    for sheet_name, raw in frames:
        df = _normalise_columns(raw)
        df = _melt_if_wide(df)

        var_col = _find_col(df, _VAR_CANDIDATE_COLS)
        country_col = _find_col(df, _COUNTRY_CANDIDATE_COLS)
        year_col = _find_col(df, _YEAR_CANDIDATE_COLS)
        value_col = _find_col(df, _VALUE_CANDIDATE_COLS)
        ind_col = _find_col(df, _INDUSTRY_CANDIDATE_COLS)

        # Path A: tidy long with explicit variable column.
        if var_col and country_col and year_col and value_col:
            mask = df[var_col].astype(str).str.strip().str.lower().isin(var_codes)
            sub = df[mask].copy()
            if sub.empty:
                continue
        # Path B: sheet whose name matches the var code; values column already named.
        elif (
            country_col and year_col and value_col
            and any(vc.lower() in sheet_name.lower() for vc in spec["var_codes"])
        ):
            keep_set = {c for c in (country_col, year_col, value_col, ind_col) if c is not None}
            sub = df[[c for c in df.columns if c in keep_set]].copy()
        else:
            continue

        sub = sub.rename(columns={
            country_col: "country_iso3_raw",
            year_col: "year",
            value_col: "value",
        })
        if ind_col and ind_col in sub.columns:
            sub = sub.rename(columns={ind_col: "industry_code"})
        else:
            sub["industry_code"] = pd.NA

        sub["country_iso3"] = _to_iso3(sub["country_iso3_raw"])
        sub["year"] = pd.to_numeric(sub["year"], errors="coerce").astype("Int64")
        sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
        sub = sub.dropna(subset=["country_iso3", "year", "value"])

        keep = ["country_iso3", "year", "industry_code", "value"]
        pieces.append(sub[keep])

    if not pieces:
        raise EUKlemsError(
            f"could not locate series {series_id!r} (var codes: {spec['var_codes']}) "
            f"in EU KLEMS frames. Inspect the source file structure; "
            f"may need to update SERIES_SPEC."
        )

    out = pd.concat(pieces, ignore_index=True).drop_duplicates()

    if not industry_level:
        # Drop industry dimension; prefer aggregate "TOT" if present, else first
        # industry code per (country, year) — defensive when the file lacks TOT.
        if out["industry_code"].notna().any():
            tot_mask = out["industry_code"].astype(str).str.upper().isin(
                {"TOT", "TOTAL", "MARKT", "MKT", "A-U", "A_U", "A-S", "A_S"}
            )
            tot = out[tot_mask]
            if not tot.empty:
                out = tot
        out = (out.groupby(["country_iso3", "year"], as_index=False)["value"]
               .mean())

    return out.sort_values(["country_iso3", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch(
    series_id: str = "tfp",
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id not in SERIES_SPEC:
        raise EUKlemsError(
            f"unknown EU KLEMS series_id {series_id!r}. "
            f"Known: {sorted(SERIES_SPEC)}"
        )

    fetch_ts = utc_now()
    frames, source_url = _acquire_frames()
    df = _slice_series(frames, series_id)

    path_out, sha = write_vintage(
        publisher=PUBLISHER,
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    spec = SERIES_SPEC[series_id]
    start = str(int(df["year"].min())) if len(df) else None
    end = str(int(df["year"].max())) if len(df) else None

    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=source_url,
        methodology_url=METHOD_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=spec["units"],
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "industry_level": spec["industry_level"],
            "var_codes_tried": spec["var_codes"],
            "n_countries": int(df["country_iso3"].nunique()) if len(df) else 0,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from data.fetchers import eu_klems as _self

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series", default="tfp", choices=sorted(SERIES_SPEC))
    args = p.parse_args()
    res = _self.fetch(args.series)
    print(f"OK rows={res.rows} {res.start_date}->{res.end_date}")
    print(f"   {res.parquet_path}")
