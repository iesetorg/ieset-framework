#!/usr/bin/env python3
"""Build a U.S. state-government FISCAL panel (us_state_housing_fiscal_v0).

Source: Census Annual Survey of State & Local Government Finances, public-use
files. Per-year ZIPs (no API key):

    https://www2.census.gov/programs-surveys/gov-finances/tables/{year}/{year}_Individual_Unit_File.zip

Confirmed live 2026-06-29 (STATE-AGENT-6) per
engine/agent_briefs/state_level_housing_fiscal_verification_2026-06-29.md sec 5a.

Each year ZIP ships (for vintages that publish it) a public-use
"State by level of estimate" file `YYstatetypepu.txt` (35-char fixed length).
That file carries the OFFICIAL published, survey-weighted/imputed aggregate
estimates of every item code at each level of estimate for each state:

    Positions (1-indexed)            Field
    1-2    FIPS state code           (00 = United States total)
    3      Level of estimate code    (1 = state+local total, 2 = state govt
                                       total, 3 = local govt total, ...)
    5-7    Item code                 (3-char Census finance item code)
    9-20   Amount (thousands of $)
    23-32  Coefficient of variation  (sampling-reliability flag)
    34-35  Last two digits of year

We filter to level-of-estimate code 2 (State government total) and aggregate the
headline state-government fiscal lines by summing their constituent item codes
exactly as defined in the survey's own `Finance_Aggregate_Lines_YYYY.xlsx`
"State" sheet (item-code lists pinned in ITEM_CODE_AGGREGATES below). This
reproduces the Census published aggregate lines (Revenue, Tax revenue,
Intergovernmental revenue, Expenditure, Debt outstanding, ...).

IMPORTANT — official aggregate vs raw micro-data: the level-2 estimates in
`YYstatetypepu.txt` are the weighted/imputed survey totals. Aggregating the raw
individual-unit file (type-of-government = 0) instead yields *unweighted
respondent* sums that diverge from the published totals for some revenue/expend
lines (tax lines happen to match). We therefore use the published state-type
file as the authoritative path and only emit vintages that ship it. A vintage
whose ZIP exists but lacks `statetypepu.txt` (e.g. 2022 at time of build) is
recorded as a documented gap, not fabricated.

FISCAL-YEAR NOTE: this is a fiscal-year survey. Most state governments use a
June-30 fiscal year end (the four exceptions are AL/MI Sep-30, NY Mar-31, TX
Aug-31). The `year` column is the survey reference year (the Census survey
year); `period_type` is set to "fiscal_year" on every row and `fiscal_year`
mirrors `year`. We do NOT claim these are calendar-year figures.

Grain: one row per (ieset_state_id, year). state_fips preserved. Amounts in
USD thousands (Census native unit). Coefficient-of-variation columns are
carried as disclosure/reliability flags. No future years are fabricated: only
survey years actually downloaded and parsed are emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import sys
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location(
        "ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not load data/fetchers/_base.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FETCHER_BASE = load_fetcher_base()
FetchResult = _FETCHER_BASE.FetchResult
utc_now = _FETCHER_BASE.utc_now
utc_stamp = _FETCHER_BASE.utc_stamp

USER_AGENT = "IESET state-level fiscal data builder"

GOVFIN_ZIP_TEMPLATE = (
    "https://www2.census.gov/programs-surveys/gov-finances/tables/"
    "{year}/{year}_Individual_Unit_File.zip"
)
GOVFIN_DATASET_HUB = (
    "https://www.census.gov/data/datasets/{year}/econ/local/public-use-datasets.html"
)
GOVFIN_METHODOLOGY_URL = "https://www.census.gov/programs-surveys/gov-finances.html"
GOVFIN_CLASSIFICATION_URL = (
    "https://www2.census.gov/govs/pubs/classification/2006_classification_manual.pdf"
)
GOVFIN_LICENSE = "U.S. Census Bureau public domain"

PUBLISHER = "us_census"
SERIES_ID = "us_state_gov_finances_panel"

# Level-of-estimate codes in YYstatetypepu.txt:
#   1 = State and local government total
#   2 = State government total   <- default state-government-fiscal layer
#   3 = Local government total
STATE_GOVT_LEVEL_CODE = "2"
STATE_LOCAL_TOTAL_LEVEL_CODE = "1"

# The District of Columbia is a consolidated city-state: the Census survey
# classifies ALL of its government as LOCAL, so DC carries NO level-2 (state
# government total) records — only level 1 (state+local total) and level 3
# (local total). For DC we therefore use level-1 as the state-EQUIVALENT fiscal
# aggregate and flag it via level_of_estimate_used. (FIPS 11 = DC.)
DC_STATE_FIPS = "11"

DEFAULT_START_YEAR = 2017
DEFAULT_END_YEAR = 2021

# Headline state-government fiscal aggregates. Item-code lists are taken verbatim
# from the survey's own Finance_Aggregate_Lines_YYYY.xlsx "State" sheet (2021
# vintage; the Census item-code taxonomy is stable across these vintages). Each
# aggregate = sum of its constituent item codes at level-of-estimate 2.
ITEM_CODE_AGGREGATES: dict[str, list[str]] = {
    "total_revenue": [
        "A01", "A03", "A09", "A10", "A12", "A16", "A18", "A21", "A36", "A44",
        "A45", "A50", "A54", "A56", "A59", "A60", "A61", "A80", "A81", "A87",
        "A89", "A90", "A91", "A92", "A93", "A94", "B01", "B21", "B22", "B30",
        "B42", "B43", "B46", "B50", "B54", "B59", "B79", "B80", "B89", "B91",
        "B92", "B93", "B94", "D21", "D30", "D42", "D46", "D50", "D79", "D80",
        "D89", "D91", "D92", "D93", "D94", "T01", "T09", "T10", "T11", "T12",
        "T13", "T14", "T15", "T16", "T19", "T20", "T21", "T22", "T23", "T24",
        "T25", "T27", "T28", "T29", "T40", "T41", "T50", "T51", "T53", "T99",
        "U01", "U11", "U20", "U21", "U30", "U40", "U41", "U50", "U95", "U99",
        "X01", "X30", "X50", "X71", "Y01", "Y02", "Y04", "Y11", "Y12", "Y51",
        "Y52",
    ],
    "intergovernmental_revenue": [
        "B01", "B21", "B22", "B30", "B42", "B43", "B46", "B50", "B54", "B59",
        "B79", "B80", "B89", "B91", "B92", "B93", "B94", "D21", "D30", "D42",
        "D46", "D50", "D79", "D80", "D89", "D91", "D92", "D93", "D94",
    ],
    "general_revenue_own_sources": [
        "A01", "A03", "A09", "A10", "A12", "A16", "A18", "A21", "A36", "A44",
        "A45", "A50", "A54", "A56", "A59", "A60", "A61", "A80", "A81", "A87",
        "A89", "T01", "T09", "T10", "T11", "T12", "T13", "T14", "T15", "T16",
        "T19", "T20", "T21", "T22", "T23", "T24", "T25", "T27", "T28", "T29",
        "T40", "T41", "T50", "T51", "T53", "T99", "U01", "U11", "U20", "U21",
        "U30", "U40", "U41", "U50", "U95", "U99",
    ],
    "total_tax_revenue": [
        "T01", "T09", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T19",
        "T20", "T21", "T22", "T23", "T24", "T25", "T27", "T28", "T29", "T40",
        "T41", "T50", "T51", "T53", "T99",
    ],
    "property_tax": ["T01"],
    "sales_gross_receipts_tax": [
        "T09", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T19",
    ],
    "individual_income_tax": ["T40"],
    "corporate_income_tax": ["T41"],
    "total_expenditure": [
        "E01", "E03", "E04", "E05", "E12", "E16", "E18", "E21", "E22", "E23",
        "E25", "E26", "E27", "E29", "E31", "E32", "E36", "E44", "E45", "E50",
        "E52", "E54", "E55", "E56", "E59", "E60", "E61", "E62", "E66", "E74",
        "E75", "E77", "E79", "E80", "E81", "E85", "E87", "E89", "E90", "E91",
        "E92", "E93", "E94", "F01", "F03", "F04", "F05", "F12", "F16", "F18",
        "F21", "F22", "F23", "F25", "F26", "F27", "F29", "F31", "F32", "F36",
        "F44", "F45", "F50", "F52", "F54", "F55", "F56", "F59", "F60", "F61",
        "F62", "F66", "F77", "F79", "F80", "F81", "F85", "F87", "F89", "F90",
        "F91", "F92", "F93", "F94", "G01", "G03", "G04", "G05", "G12", "G16",
        "G18", "G21", "G22", "G23", "G25", "G26", "G27", "G29", "G31", "G32",
        "G36", "G44", "G45", "G50", "G52", "G54", "G55", "G56", "G59", "G60",
        "G61", "G62", "G66", "G77", "G79", "G80", "G81", "G85", "G87", "G89",
        "G90", "G91", "G92", "G93", "G94", "I89", "I91", "I92", "I93", "I94",
        "J19", "J67", "J68", "J85", "M01", "M04", "M05", "M12", "M18", "M21",
        "M23", "M25", "M27", "M29", "M30", "M32", "M36", "M44", "M50", "M52",
        "M54", "M55", "M56", "M59", "M60", "M61", "M62", "M66", "M67", "M68",
        "M79", "M80", "M81", "M87", "M89", "M91", "M92", "M93", "M94", "Q12",
        "Q18", "S67", "S89", "X40", "X80", "Y05", "Y06", "Y14", "Y53",
    ],
    "intergovernmental_expenditure": [
        "M01", "M04", "M05", "M12", "M18", "M21", "M23", "M25", "M27", "M29",
        "M30", "M32", "M36", "M44", "M50", "M52", "M54", "M55", "M56", "M59",
        "M60", "M61", "M62", "M66", "M67", "M68", "M79", "M80", "M81", "M87",
        "M89", "M91", "M92", "M93", "M94", "Q12", "Q18", "S67", "S89",
    ],
    "direct_expenditure": [
        "E01", "E03", "E04", "E05", "E12", "E16", "E18", "E21", "E22", "E23",
        "E25", "E26", "E27", "E29", "E31", "E32", "E36", "E44", "E45", "E50",
        "E52", "E54", "E55", "E56", "E59", "E60", "E61", "E62", "E66", "E74",
        "E75", "E77", "E79", "E80", "E81", "E85", "E87", "E89", "E90", "E91",
        "E92", "E93", "E94", "F01", "F03", "F04", "F05", "F12", "F16", "F18",
        "F21", "F22", "F23", "F25", "F26", "F27", "F29", "F31", "F32", "F36",
        "F44", "F45", "F50", "F52", "F54", "F55", "F56", "F59", "F60", "F61",
        "F62", "F66", "F77", "F79", "F80", "F81", "F85", "F87", "F89", "F90",
        "F91", "F92", "F93", "F94", "G01", "G03", "G04", "G05", "G12", "G16",
        "G18", "G21", "G22", "G23", "G25", "G26", "G27", "G29", "G31", "G32",
        "G36", "G44", "G45", "G50", "G52", "G54", "G55", "G56", "G59", "G60",
        "G61", "G62", "G66", "G77", "G79", "G80", "G81", "G85", "G87", "G89",
        "G90", "G91", "G92", "G93", "G94", "I89", "I91", "I92", "I93", "I94",
        "J19", "J67", "J68", "J85", "X40", "X80", "Y05", "Y06", "Y14", "Y53",
    ],
    "total_debt_outstanding": ["44T", "49U", "64V"],
}

# Carry a coefficient-of-variation disclosure flag for these headline measures.
# A measure's CV is taken as the maximum CV across its constituent item codes
# present in the file (a conservative reliability bound).
CV_FLAG_MEASURES = [
    "total_revenue",
    "total_tax_revenue",
    "total_expenditure",
    "total_debt_outstanding",
    "intergovernmental_revenue",
]

MEASURE_COLUMNS = list(ITEM_CODE_AGGREGATES.keys())


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fetch_utc(value: str | None) -> datetime:
    if not value:
        return utc_now()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


# ---------------------------------------------------------------------------
# Download helpers (key-free static ZIPs)
# ---------------------------------------------------------------------------

def http_get(url: str, timeout: int = 240) -> bytes:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.content


# ---------------------------------------------------------------------------
# State-type file parsing
# ---------------------------------------------------------------------------

def _to_int(value: str) -> int | None:
    text = value.strip().replace(",", "")
    if text in {"", "-", ".", "(NA)", "NA"}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _to_float(value: str) -> float | None:
    text = value.strip().replace(",", "")
    if text in {"", "-", ".", "(NA)", "NA"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def find_statetype_member(names: list[str]) -> str | None:
    """Locate the YYstatetypepu.txt member inside a gov-finances ZIP."""
    candidates = [
        n for n in names
        if n.lower().endswith(".txt") and "statetypepu" in Path(n).name.lower()
    ]
    return candidates[0] if candidates else None


def parse_statetype_text(text: str) -> pd.DataFrame:
    """Parse YYstatetypepu.txt rows (levels 1 and 2) into long form.

    Returns columns: state_fips, level, item_code, amount_thousands, cv,
    survey_yy. Level-of-estimate code 2 (State government total) is the default
    state-government-fiscal layer; level 1 (State and local total) is retained
    only as the DC state-equivalent fallback (DC has no level-2 records).
    """
    keep_levels = {STATE_GOVT_LEVEL_CODE, STATE_LOCAL_TOTAL_LEVEL_CODE}
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if len(line) < 35:
            continue
        level = line[2:3]
        if level not in keep_levels:
            continue
        state_fips = line[0:2]
        if not state_fips.isdigit():
            continue
        item_code = line[4:7].strip()
        if not item_code:
            continue
        amount = _to_int(line[8:20])
        cv = _to_float(line[22:32])
        survey_yy = line[33:35].strip()
        records.append(
            {
                "state_fips": state_fips,
                "level": level,
                "item_code": item_code,
                "amount_thousands": amount,
                "cv": cv,
                "survey_yy": survey_yy,
            }
        )
    if not records:
        raise ValueError("no level-1/level-2 rows parsed")
    return pd.DataFrame.from_records(records)


def _select_level_for_state(state_fips: str, available_levels: set[str]) -> str | None:
    """Pick the level-of-estimate to use for a given state.

    Normal states use level 2 (State government total). DC has no level-2
    records, so it falls back to level 1 (State and local government total) as
    its state-equivalent aggregate.
    """
    if STATE_GOVT_LEVEL_CODE in available_levels:
        return STATE_GOVT_LEVEL_CODE
    if state_fips == DC_STATE_FIPS and STATE_LOCAL_TOTAL_LEVEL_CODE in available_levels:
        return STATE_LOCAL_TOTAL_LEVEL_CODE
    return None


def aggregate_state_year(long_df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Collapse long item-code rows into headline aggregates per state.

    For each state the appropriate level-of-estimate is selected (level 2 for
    normal states; level 1 for DC, which has no level-2 records). The chosen
    level is recorded in level_of_estimate_used.
    """
    rows: list[dict[str, Any]] = []
    for state in sorted(long_df["state_fips"].unique()):
        sub = long_df[long_df["state_fips"] == state]
        level = _select_level_for_state(state, set(sub["level"].unique()))
        if level is None:
            continue
        sub = sub[sub["level"] == level]
        amounts = (
            sub.dropna(subset=["amount_thousands"]).set_index("item_code")["amount_thousands"]
        )
        # Guard against any duplicate (state, level, item) rows.
        amounts = amounts[~amounts.index.duplicated(keep="first")]
        cvs = sub.dropna(subset=["cv"]).set_index("item_code")["cv"]
        cvs = cvs[~cvs.index.duplicated(keep="first")]

        row: dict[str, Any] = {
            "state_fips": state,
            "year": year,
            "level_of_estimate_used": level,
        }
        for measure, codes in ITEM_CODE_AGGREGATES.items():
            present = [c for c in codes if c in amounts.index]
            row[measure] = int(amounts.loc[present].sum()) if present else None
            if measure in CV_FLAG_MEASURES:
                cv_present = [c for c in codes if c in cvs.index]
                row[f"{measure}_max_cv"] = (
                    float(cvs.loc[cv_present].max()) if cv_present else None
                )
        rows.append(row)
    return pd.DataFrame(rows)


def fetch_year(
    year: int,
    *,
    cache_dir: Path | None = None,
) -> tuple[pd.DataFrame | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Fetch + parse one survey year. Returns (frame, provenance, gap)."""
    url = GOVFIN_ZIP_TEMPLATE.format(year=year)
    try:
        if cache_dir is not None:
            payload = (cache_dir / f"{year}_Individual_Unit_File.zip").read_bytes()
        else:
            payload = http_get(url)
    except Exception as exc:  # noqa: BLE001
        return None, None, {
            "source": "us_census_state_local_gov_finances",
            "year": year,
            "url": url,
            "error": f"download failed: {exc}",
        }

    try:
        zf = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        return None, None, {
            "source": "us_census_state_local_gov_finances",
            "year": year,
            "url": url,
            "error": f"not a valid ZIP: {exc}",
        }

    member = find_statetype_member(zf.namelist())
    if member is None:
        return None, None, {
            "source": "us_census_state_local_gov_finances",
            "year": year,
            "url": url,
            "error": (
                "ZIP present but ships no YYstatetypepu.txt (published "
                "state-government-total aggregates not in this vintage); "
                "skipped rather than aggregating unweighted micro-data."
            ),
            "zip_members": zf.namelist(),
        }

    raw = zf.read(member)
    text = raw.decode("latin-1")
    try:
        long_df = parse_statetype_text(text)
    except ValueError as exc:
        return None, None, {
            "source": "us_census_state_local_gov_finances",
            "year": year,
            "url": url,
            "member": member,
            "error": str(exc),
        }

    frame = aggregate_state_year(long_df, year)
    provenance = {
        "source": "us_census_state_local_gov_finances",
        "year": year,
        "url": url,
        "zip_sha256": sha256_bytes(payload),
        "zip_bytes": len(payload),
        "statetype_member": member,
        "statetype_sha256": sha256_bytes(raw),
        "level_of_estimate": "2 (State government total)",
        "rows_parsed": int(len(frame)),
    }
    return frame, provenance, None


# ---------------------------------------------------------------------------
# Spine + assembly
# ---------------------------------------------------------------------------

def load_spine(spine_path: Path) -> pd.DataFrame:
    spine = pd.read_parquet(spine_path)
    spine = spine[
        ["ieset_state_id", "state_fips", "state_abbr", "state_name",
         "admin1_kind", "is_state_equivalent"]
    ].copy()
    spine["state_fips"] = spine["state_fips"].astype(str).str.zfill(2)
    spine["state_abbr"] = spine["state_abbr"].astype(str).str.upper()
    return spine


def build_panel(
    *,
    spine_path: Path,
    years: list[int],
    cache_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    spine = load_spine(spine_path)

    frames: list[pd.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for year in years:
        frame, prov, gap = fetch_year(year, cache_dir=cache_dir)
        if gap is not None:
            gaps.append(gap)
        if frame is not None and prov is not None:
            frames.append(frame)
            provenance.append(prov)

    if not frames:
        raise RuntimeError(
            "No gov-finances state-type files could be parsed; aborting build. "
            f"gaps={gaps}"
        )

    stacked = pd.concat(frames, ignore_index=True)
    # Drop the national total (state_fips 00); the spine join keeps only the
    # canonical 50 states + DC anyway, but be explicit.
    stacked = stacked[stacked["state_fips"] != "00"].copy()

    # Fiscal-year fields: this survey is fiscal-year. year == survey reference
    # year; period_type marks it; fiscal_year mirrors year.
    stacked["period_type"] = "fiscal_year"
    stacked["fiscal_year"] = stacked["year"].astype(int)

    panel = spine.merge(stacked, on="state_fips", how="inner")

    measure_cols = MEASURE_COLUMNS
    panel["measures_present"] = panel[measure_cols].notna().sum(axis=1).astype(int)

    cv_cols = [f"{m}_max_cv" for m in CV_FLAG_MEASURES]
    ordered = (
        [
            "ieset_state_id",
            "state_fips",
            "state_abbr",
            "state_name",
            "admin1_kind",
            "is_state_equivalent",
            "year",
            "period_type",
            "fiscal_year",
            "level_of_estimate_used",
        ]
        + measure_cols
        + cv_cols
        + ["measures_present"]
    )
    panel = panel[ordered].sort_values(["ieset_state_id", "year"]).reset_index(drop=True)

    most_recent_year = int(panel.loc[panel["total_revenue"].notna(), "year"].max())
    states_recent = set(
        panel.loc[
            (panel["year"] == most_recent_year) & (panel["total_revenue"].notna()),
            "ieset_state_id",
        ]
    )

    stats = {
        "panel_rows": int(len(panel)),
        "unique_states": int(panel["ieset_state_id"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "most_recent_year": most_recent_year,
        "states_with_revenue_most_recent_year": len(states_recent),
        "measure_columns": measure_cols,
        "cv_flag_columns": cv_cols,
        "gaps": gaps,
        "amount_unit_note": (
            "All fiscal amounts are in thousands of U.S. dollars (Census native "
            "unit): a value of 1027008 represents $1,027,008,000."
        ),
        "aggregate_method_note": (
            "Headline aggregates are sums of their constituent Census finance "
            "item codes at level-of-estimate 2 (State government total) from "
            "YYstatetypepu.txt, per the survey's Finance_Aggregate_Lines 'State' "
            "sheet. These reproduce the published Census aggregate lines (the "
            "weighted/imputed survey estimates), not unweighted micro-data sums."
        ),
        "fiscal_year_note": (
            "The Annual Survey of State & Local Government Finances is a "
            "FISCAL-YEAR survey. period_type='fiscal_year' on every row; "
            "fiscal_year mirrors the survey reference year. Most states use a "
            "June-30 FY end (exceptions: AL/MI Sep-30, NY Mar-31, TX Aug-31). "
            "These are not calendar-year figures."
        ),
        "cv_note": (
            "*_max_cv columns carry the maximum coefficient of variation across "
            "a measure's constituent item codes (a conservative sampling-"
            "reliability bound; lower is more reliable). These are the survey's "
            "own disclosure/reliability flags."
        ),
        "vintage_gap_note": (
            "Only survey years whose ZIP ships the published YYstatetypepu.txt "
            "state-government-total file are emitted. A vintage whose ZIP exists "
            "but lacks that file (e.g. 2022 at build time) is recorded in gaps "
            "and NOT fabricated."
        ),
        "level_of_estimate_note": (
            "level_of_estimate_used = '2' (State government total) for all 50 "
            "states. The District of Columbia is a consolidated city-state with "
            "no level-2 records, so it uses level '1' (State and local government "
            "total) as its state-equivalent fiscal aggregate."
        ),
        "dc_level_used": (
            "1 (state+local total; DC has no level-2 state-government records)"
        ),
    }
    provenance_out = {"gov_finances_years": provenance}
    return panel, stats, provenance_out


# ---------------------------------------------------------------------------
# Emit + manifest
# ---------------------------------------------------------------------------

def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(
    result: FetchResult,
    manifest_dir: Path,
    run_stamp: str,
    methodology: dict[str, Any],
) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_us_state_gov_finances.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "us_state_gov_finances_panel",
        "methodology": methodology,
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(
    panel: pd.DataFrame,
    stats: dict[str, Any],
    provenance: dict[str, Any],
    output_path: Path,
    fetch_ts: datetime,
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    year_urls = "; ".join(
        sorted({p["url"] for p in provenance.get("gov_finances_years", [])})
    )
    return FetchResult(
        publisher=PUBLISHER,
        series_id=SERIES_ID,
        source_url=year_urls or GOVFIN_ZIP_TEMPLATE,
        methodology_url=f"{GOVFIN_METHODOLOGY_URL} ; {GOVFIN_CLASSIFICATION_URL}",
        license=GOVFIN_LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual (state-year, fiscal-year survey)",
        units="USD thousands (Census native unit)",
        currency="USD",
        start_date=str(stats["year_min"]),
        end_date=str(stats["year_max"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "inputs": provenance,
            "construction": (
                "Annual U.S. state-government fiscal panel from the Census Annual "
                "Survey of State & Local Government Finances public-use ZIPs. "
                "Per-year YYstatetypepu.txt level-of-estimate 2 (State government "
                "total) item-code amounts are summed into headline aggregates "
                "(revenue, tax revenue, intergovernmental revenue, expenditure, "
                "debt outstanding, plus major own-source tax categories) per the "
                "survey's Finance_Aggregate_Lines definitions. Amounts in USD "
                "thousands. Fiscal-year survey: period_type='fiscal_year'. One "
                "row per (ieset_state_id, year); state_fips preserved."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spine", default="data/derived/state_universe_admin1.parquet")
    parser.add_argument("--output", default="data/derived/us_state_gov_finances_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    parser.add_argument(
        "--cache-dir",
        help="Optional local dir of {year}_Individual_Unit_File.zip files (offline build).",
    )
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    years = list(range(args.start_year, args.end_year + 1))
    cache_dir = path_arg(args.cache_dir).resolve() if args.cache_dir else None

    panel, stats, provenance = build_panel(
        spine_path=path_arg(args.spine).resolve(),
        years=years,
        cache_dir=cache_dir,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, provenance, output_path, fetch_ts)
    methodology = {
        "build_utc": fetch_ts.isoformat(),
        "row_count": int(len(panel)),
        "columns": list(panel.columns),
        "measure_columns": stats["measure_columns"],
        "cv_flag_columns": stats["cv_flag_columns"],
        "amount_unit_note": stats["amount_unit_note"],
        "aggregate_method_note": stats["aggregate_method_note"],
        "fiscal_year_note": stats["fiscal_year_note"],
        "cv_note": stats["cv_note"],
        "vintage_gap_note": stats["vintage_gap_note"],
        "level_of_estimate_note": stats["level_of_estimate_note"],
        "gaps": stats["gaps"],
        "inputs": provenance,
        "spine": rel(path_arg(args.spine).resolve()),
        "item_code_aggregates": ITEM_CODE_AGGREGATES,
    }
    manifest = write_manifest(
        result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts), methodology
    )
    print(
        f"OK {PUBLISHER}:{SERIES_ID} rows={result.rows} "
        f"years={stats['year_min']}->{stats['year_max']} "
        f"states={stats['unique_states']} "
        f"recent_year={stats['most_recent_year']} "
        f"states_recent={stats['states_with_revenue_most_recent_year']}"
    )
    if stats["gaps"]:
        print(f"WARN gaps={len(stats['gaps'])} (see manifest)")
        for g in stats["gaps"]:
            print(f"  - {g['year']}: {g['error'][:80]}")
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
