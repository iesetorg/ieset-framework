"""IMF IFS / BOP / AREAER manual-drop fetcher.

The IMF deprecated its public SDMX 2.1 endpoint (`dataservices.imf.org`)
in 2024 and migrated to a Power BI Embedded portal at `data.imf.org`
that has no programmatic API. The DataMapper API (used by `imf_weo.py`)
covers the WEO database only — about 132 indicators, missing IFS
(International Financial Statistics), BOP (Balance of Payments),
AREAER (exchange-rate regime classification), and FSI (Financial
Soundness Indicators).

This fetcher loads bulk-export CSVs from `data/manual/imf_ifs/`. Users
download the relevant IMF database CSV from the IMF Data Portal once,
place it in that directory, and this fetcher resolves any cited
series_id from the curated `SUPPORTED` registry.

To obtain source data:
    1. Visit  https://data.imf.org/  and sign in (free).
    2. Navigate to the dataset (IFS / BOP / IIP / AREAER / FSI) you need.
    3. "Export → CSV (Full dataset)" produces a wide-form table.
    4. Save the resulting `<dataset>.csv` (or `.xlsx`) to
       `<repo>/data/manual/imf_ifs/`.

Series_id resolution: this fetcher accepts the IMF mnemonic codes that
appear across hypothesis citations (BFOAFA, BFXFA, AREAER, BCA_NGDPD when
not in WEO, FSI series, etc.) and reads them from whichever bulk CSV
contains them. The CSV's column layout is normalised to long-form
(country_iso3, year, value) regardless of the source dataset's wide-form
shape.

If no manual file is staged, raises `IfsManualDropError` with a clear
prompt — callers (the runner) treat that as INCONCLUSIVE_DATA_PENDING.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest, MANUAL_ROOT, ManualDropError

LICENSE = "imf_terms"
PUBLISHER = "imf_ifs"


class IfsManualDropError(RuntimeError):
    """Raised when the manual-drop directory is empty / no matching file."""


# Curated registry of supported IMF mnemonic series. Each entry maps the
# IESET-cited series_id to the canonical column name(s) in the bulk CSV
# and a one-line description. Add new entries as specs are wired.
SUPPORTED: dict[str, dict[str, str]] = {
    # ---------- Balance of Payments / IIP ----------
    "BFOAFA": {
        "title": "External assets (foreign assets), USD millions, BPM6",
        "frequency": "annual",
        "series_match": r"BFOAFA|External assets.*total.*BP6",
        "dataset_hint": "IIP / BOP",
    },
    "BFXFA": {
        "title": "External liabilities (foreign liabilities), USD millions, BPM6",
        "frequency": "annual",
        "series_match": r"BFXFA|External liabilities.*total.*BP6",
        "dataset_hint": "IIP / BOP",
    },
    "BCA_NGDPD_IFS": {
        # alias for IFS-side BCA where DataMapper returns no values
        "title": "Current account balance, % of GDP (IFS variant)",
        "frequency": "annual",
        "series_match": r"BCA_NGDPD|Current account",
        "dataset_hint": "IFS / BOP",
    },
    # ---------- AREAER (exchange-rate regime classification) ----------
    "AREAER": {
        "title": "Exchange-rate regime classification, annual",
        "frequency": "annual",
        "series_match": r"AREAER|exchange.*rate.*regime",
        "dataset_hint": "AREAER",
    },
    # ---------- FSI (Financial Soundness Indicators) ----------
    "FSI": {
        "title": "Financial Soundness Indicators (multiple)",
        "frequency": "quarterly",
        "series_match": r"FSI|Financial Soundness",
        "dataset_hint": "FSI",
    },
    # ---------- IFS macro aggregates not in DataMapper ----------
    "FIDR_PA": {
        "title": "Lending interest rate, %",
        "frequency": "annual",
        "series_match": r"FIDR_PA|Lending rate",
        "dataset_hint": "IFS",
    },
    "FIGB_PA": {
        "title": "Government bond yield, %",
        "frequency": "annual",
        "series_match": r"FIGB_PA|Government Bond",
        "dataset_hint": "IFS",
    },
    "FILR_PA": {
        "title": "Lending rate (alt), %",
        "frequency": "annual",
        "series_match": r"FILR_PA|Lending rate",
        "dataset_hint": "IFS",
    },
    "FMA_USD": {
        "title": "Monetary base, USD-equivalent",
        "frequency": "monthly",
        "series_match": r"FMA_USD|Monetary base",
        "dataset_hint": "IFS",
    },
}


# ---------------------------------------------------------------------------
# Resolver helpers
# ---------------------------------------------------------------------------


_ISO3_PATTERN = re.compile(r"^[A-Z]{3}$")


def _normalise_country(val: Any) -> str | None:
    """Map an IMF country label or 2/3-letter code to ISO3.

    IMF bulk CSVs typically have either:
      - 'Country Code' column with 3-letter ISO codes (preferred)
      - 'Country Name' column with full names (fallback — uses a small map)
    """
    if val is None:
        return None
    s = str(val).strip()
    if _ISO3_PATTERN.match(s):
        return s
    # Common name → ISO3 map for the headline countries this fetcher serves.
    NAME_MAP = {
        "United States": "USA", "United Kingdom": "GBR", "Germany": "DEU",
        "France": "FRA", "Italy": "ITA", "Spain": "ESP", "Japan": "JPN",
        "Canada": "CAN", "Australia": "AUS", "Switzerland": "CHE",
        "Netherlands": "NLD", "Belgium": "BEL", "Sweden": "SWE",
        "Norway": "NOR", "Denmark": "DNK", "Finland": "FIN", "Ireland": "IRL",
        "Argentina": "ARG", "Brazil": "BRA", "Mexico": "MEX", "Chile": "CHL",
        "Colombia": "COL", "Venezuela": "VEN", "Turkey": "TUR", "Türkiye": "TUR",
        "Korea, Rep.": "KOR", "Korea": "KOR", "China": "CHN", "India": "IND",
        "Indonesia": "IDN", "South Africa": "ZAF", "Israel": "ISR",
    }
    return NAME_MAP.get(s)


def _normalise_year(val: Any) -> int | None:
    if val is None:
        return None
    s = str(val).strip()
    # Plain year
    m = re.match(r"^(\d{4})", s)
    if m:
        try:
            y = int(m.group(1))
            if 1900 < y < 2100:
                return y
        except ValueError:
            pass
    return None


def _read_manual_csv(path: Path) -> pd.DataFrame:
    """Read a CSV/XLSX file robustly, normalising headers."""
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        # Try a few delimiters
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(path, sep=sep)
                if df.shape[1] > 1:
                    break
            except Exception:
                continue
        else:
            df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _melt_imf_wide_csv(df: pd.DataFrame, series_match: str) -> pd.DataFrame:
    """Convert an IMF bulk CSV (wide-by-year) to (country_iso3, year, value).

    IMF CSVs typically have:
      - one or two ID columns ('Country Code', 'Country Name', 'Indicator Name', 'Indicator Code')
      - many year columns ('1995', '1996', ..., '2024')
    We melt into long form, filter to rows matching series_match, normalise
    the country and year columns.
    """
    cols = list(df.columns)
    # Identify country columns
    country_col = None
    for cand in ("Country Code", "ISO", "ISO Code", "ISO3", "country_iso3", "Reference Area"):
        if cand in cols:
            country_col = cand
            break
    if country_col is None:
        for cand in ("Country", "Country Name", "Economy"):
            if cand in cols:
                country_col = cand
                break
    if country_col is None:
        return pd.DataFrame()

    # Identify the indicator column
    ind_col = None
    for cand in ("Indicator Code", "Indicator Name", "Series Name",
                 "Indicator", "Series", "Concept"):
        if cand in cols:
            ind_col = cand
            break

    # Year columns: any column whose name parses as a 4-digit year
    year_cols = [c for c in cols if re.match(r"^\d{4}([Q\-/]\d+)?$", str(c).strip())]
    if not year_cols:
        return pd.DataFrame()

    keep_cols = [country_col] + ([ind_col] if ind_col else []) + year_cols
    sub = df[keep_cols].copy()
    long = sub.melt(
        id_vars=[c for c in keep_cols if c not in year_cols],
        value_vars=year_cols, var_name="period", value_name="value",
    )
    long["year"] = long["period"].apply(_normalise_year)
    long["country_iso3"] = long[country_col].apply(_normalise_country)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")

    # Filter on indicator if present
    if ind_col is not None:
        long = long[long[ind_col].astype(str).str.contains(series_match, regex=True, na=False, case=False)]

    long = long.dropna(subset=["country_iso3", "year", "value"])
    return long[["country_iso3", "year", "value"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Public fetch
# ---------------------------------------------------------------------------


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """Resolve `series_id` against any bulk CSV under data/manual/imf_ifs/.

    Tries each file in turn until one yields rows matching the series.
    """
    spec = SUPPORTED.get(series_id)
    if spec is None:
        # Permissive: try as raw substring match
        spec = {
            "title": f"IMF series '{series_id}' (no curated entry)",
            "frequency": "unknown",
            "series_match": re.escape(series_id),
            "dataset_hint": "unknown",
        }

    manual_dir = MANUAL_ROOT / "imf_ifs"
    if not manual_dir.exists():
        raise ManualDropError(
            f"data/manual/imf_ifs/ does not exist. To enable IFS/BOP/AREAER "
            f"fetches, download the relevant IMF bulk CSV from "
            f"https://data.imf.org/ (signed-in CSV export) and place it in "
            f"data/manual/imf_ifs/. Series {series_id!r} is documented as "
            f"{spec['title']!r} ({spec['dataset_hint']})."
        )

    fetch_ts = utc_now()
    candidates = sorted(
        list(manual_dir.glob("*.csv"))
        + list(manual_dir.glob("*.xlsx"))
        + list(manual_dir.glob("*.xls"))
    )
    if not candidates:
        raise ManualDropError(
            f"data/manual/imf_ifs/ is empty. Drop the IMF bulk CSV for "
            f"{spec['dataset_hint']!r} (containing {series_id!r}) into "
            f"this directory."
        )

    last_path = None
    df = pd.DataFrame()
    for path in candidates:
        try:
            raw = _read_manual_csv(path)
            df = _melt_imf_wide_csv(raw, spec["series_match"])
        except Exception:
            continue
        if not df.empty:
            last_path = path
            break

    if df.empty:
        raise ManualDropError(
            f"None of the {len(candidates)} file(s) in data/manual/imf_ifs/ "
            f"contains rows matching series_id={series_id!r} "
            f"(pattern {spec['series_match']!r}). Verify the bulk CSV "
            f"includes this indicator."
        )

    df = (
        df.sort_values(["country_iso3", "year"])
        .reset_index(drop=True)
        .assign(indicator_id=series_id)
    )
    path_out, sha = write_vintage(
        publisher=PUBLISHER, series_id=series_id, frame=df, fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=f"manual://{last_path.name}" if last_path else "manual://imf_ifs",
        methodology_url="https://data.imf.org/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec.get("frequency", "unknown"),
        units="see source CSV (varies by series)",
        currency=None,
        start_date=str(int(df["year"].min())) if not df.empty else None,
        end_date=str(int(df["year"].max())) if not df.empty else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "manual_file": last_path.name if last_path else None,
            "dataset_hint": spec.get("dataset_hint", "unknown"),
            "series_match_pattern": spec["series_match"],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
