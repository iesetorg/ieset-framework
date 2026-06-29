#!/usr/bin/env python3
"""Build a U.S. state housing supply + price panel (us_state_housing_fiscal_v0).

Two key-free, data-confirmed federal sources are joined into one annual
state-year panel:

  1. Census Building Permits Survey (BPS), annual state files
     https://www2.census.gov/econ/bps/State/stYYYYa.txt  (1980-2025)
     Keyed on 2-digit state FIPS. Each file carries, per structure type
     (1-unit / 2-units / 3-4 units / 5+ units), a Bldgs/Units/Value triple for
     the survey estimate (imputed for non-reporting permit-issuing places) and a
     parallel "rep" (reported-only) triple. We emit total permitted units plus
     units by structure type (1-unit, 2-4 unit = 2-units + 3-4 units, 5+ unit),
     and carry the reported-only total as an imputation note.

  2. FHFA All-Transactions House Price Index (NSA), state
     https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv
     Columns (no header): state_abbr, year, quarter, index. Index base
     1980Q1 = 100 for the all-transactions series. KEYS ON POSTAL ABBREVIATION,
     not FIPS, so the abbreviation is crosswalked to state_fips / ieset_state_id
     through the admin-1 state spine. Quarterly index values are collapsed to an
     annual mean (with a count of quarters observed) so quarterly and annual
     frequencies are never mixed.

Both sources are U.S. public-domain. Grain is one row per
(ieset_state_id, year). state_fips and state_abbr are preserved. No future
years are fabricated: only years actually present in the downloaded files are
emitted, and partial calendar years (fewer than 4 FHFA quarters) are flagged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import sys
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

USER_AGENT = "IESET state-level housing data builder"

BPS_DIR_URL = "https://www2.census.gov/econ/bps/State/"
BPS_FILE_TEMPLATE = "https://www2.census.gov/econ/bps/State/st{year}a.txt"
BPS_METHODOLOGY_URL = "https://www.census.gov/construction/bps/"
BPS_LICENSE = "U.S. Census Bureau public domain"

FHFA_AT_STATE_URL = "https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv"
FHFA_METHODOLOGY_URL = "https://www.fhfa.gov/data/hpi/datasets"
FHFA_LICENSE = "U.S. FHFA public data"
FHFA_HPI_BASE_NOTE = "FHFA All-Transactions HPI (NSA); index base 1980Q1 = 100."

PUBLISHER = "us_census_bps_fhfa"
SERIES_ID = "us_state_housing_supply_price_panel"

BPS_DEFAULT_START = 1980
BPS_DEFAULT_END = 2025


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
# Download helpers (key-free static files)
# ---------------------------------------------------------------------------

def http_get(url: str, timeout: int = 120) -> bytes:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.content


# ---------------------------------------------------------------------------
# BPS parsing
# ---------------------------------------------------------------------------

# Column offsets after the 5 identity columns (Date, FIPS, Region, Division,
# State Name): each structure type contributes (Bldgs, Units, Value) for the
# survey-estimate block, then the same 4 types repeat for the "rep" block.
def _to_int(value: str) -> int | None:
    text = value.strip().replace(",", "")
    if text in {"", "-", "(NA)", "NA", "."}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_bps_year(date_code: str) -> int | None:
    """Annual BPS date code is YYYY99 (modern) or YY99 (1980s/90s)."""
    code = date_code.strip()
    if not code.endswith("99") or not code[:-2].isdigit():
        return None
    yy = int(code[:-2])
    if yy < 100:
        # 2-digit years are all 20th century in the BPS annual series (80-99).
        yy = 1900 + yy
    return yy


def parse_bps_file(text: str, year_hint: int) -> list[dict[str, Any]]:
    """Parse one annual BPS state file into per-state rows.

    Returns rows keyed by 2-digit state_fips with units by structure type.
    The first Bldgs/Units/Value block per type is the survey estimate (imputed
    for non-reporting places); the "rep" block is reported-only.
    """
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 17:
            continue
        date_code = parts[0]
        # Skip the two banner lines (non-numeric date code).
        year = parse_bps_year(date_code)
        if year is None:
            continue
        fips = parts[1].zfill(2)
        if not fips.isdigit():
            continue
        # Survey-estimate Units columns: type i -> parts[5 + i*3 + 1].
        # 1-unit Units = parts[6], 2-units Units = parts[9],
        # 3-4 units Units = parts[12], 5+ units Units = parts[15].
        units_1 = _to_int(parts[6])
        units_2 = _to_int(parts[9])
        units_34 = _to_int(parts[12])
        units_5p = _to_int(parts[15])
        # Reported-only Units columns begin after the 12 estimate fields
        # (4 types x 3), i.e. type i -> parts[5 + 12 + i*3 + 1].
        rep_units_1 = _to_int(parts[18]) if len(parts) > 18 else None
        rep_units_2 = _to_int(parts[21]) if len(parts) > 21 else None
        rep_units_34 = _to_int(parts[24]) if len(parts) > 24 else None
        rep_units_5p = _to_int(parts[27]) if len(parts) > 27 else None

        def _sum(values: list[int | None]) -> int | None:
            present = [v for v in values if v is not None]
            if not present:
                return None
            return int(sum(present))

        units_24 = _sum([units_2, units_34])
        total_units = _sum([units_1, units_2, units_34, units_5p])
        rep_total = _sum([rep_units_1, rep_units_2, rep_units_34, rep_units_5p])
        rows.append(
            {
                "state_fips": fips,
                "year": int(year),
                "bps_total_permit_units": total_units,
                "bps_units_1_unit": units_1,
                "bps_units_2_to_4_unit": units_24,
                "bps_units_5_plus_unit": units_5p,
                "bps_reported_total_permit_units": rep_total,
            }
        )
    if not rows:
        raise ValueError(f"BPS file for {year_hint} produced no state rows")
    return rows


def fetch_bps_years(
    years: list[int],
    *,
    cache_dir: Path | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch + parse BPS annual files; returns (frame, provenance, gaps)."""
    frames: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for year in years:
        url = BPS_FILE_TEMPLATE.format(year=year)
        try:
            if cache_dir is not None:
                local = cache_dir / f"st{year}a.txt"
                payload = local.read_bytes()
            else:
                payload = http_get(url)
        except Exception as exc:  # noqa: BLE001
            gaps.append({"source": "us_census_bps_state_permits", "year": year, "url": url, "error": str(exc)})
            continue
        text = payload.decode("latin-1")
        try:
            rows = parse_bps_file(text, year)
        except ValueError as exc:
            gaps.append({"source": "us_census_bps_state_permits", "year": year, "url": url, "error": str(exc)})
            continue
        frames.extend(rows)
        provenance.append({"source": "us_census_bps_state_permits", "year": year, "url": url, "sha256": sha256_bytes(payload), "bytes": len(payload)})
    if not frames:
        raise RuntimeError("No BPS annual files could be parsed; aborting build.")
    return pd.DataFrame(frames), provenance, gaps


# ---------------------------------------------------------------------------
# FHFA parsing
# ---------------------------------------------------------------------------

def fetch_fhfa_state(*, cache_dir: Path | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch FHFA all-transactions state HPI and collapse to annual means."""
    if cache_dir is not None:
        payload = (cache_dir / "hpi_at_state.csv").read_bytes()
    else:
        payload = http_get(FHFA_AT_STATE_URL)
    raw = pd.read_csv(
        io.BytesIO(payload),
        header=None,
        names=["state_abbr", "year", "quarter", "fhfa_hpi_index"],
    )
    raw["state_abbr"] = raw["state_abbr"].astype(str).str.upper().str.strip()
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").astype("Int64")
    raw["quarter"] = pd.to_numeric(raw["quarter"], errors="coerce").astype("Int64")
    raw["fhfa_hpi_index"] = pd.to_numeric(raw["fhfa_hpi_index"], errors="coerce")
    raw = raw.dropna(subset=["state_abbr", "year", "quarter", "fhfa_hpi_index"])
    annual = (
        raw.groupby(["state_abbr", "year"], as_index=False)
        .agg(
            fhfa_hpi_at_index=("fhfa_hpi_index", "mean"),
            fhfa_hpi_quarters_observed=("quarter", "nunique"),
        )
    )
    annual["year"] = annual["year"].astype(int)
    annual["fhfa_hpi_partial_year"] = annual["fhfa_hpi_quarters_observed"] < 4
    provenance = {
        "source": "fhfa_house_price_index_state",
        "url": FHFA_AT_STATE_URL,
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        "index_base": FHFA_HPI_BASE_NOTE,
    }
    return annual, provenance


# ---------------------------------------------------------------------------
# Spine + assembly
# ---------------------------------------------------------------------------

def load_spine(spine_path: Path) -> pd.DataFrame:
    spine = pd.read_parquet(spine_path)
    spine = spine[
        ["ieset_state_id", "state_fips", "state_abbr", "state_name", "admin1_kind", "is_state_equivalent"]
    ].copy()
    spine["state_fips"] = spine["state_fips"].astype(str).str.zfill(2)
    spine["state_abbr"] = spine["state_abbr"].astype(str).str.upper()
    return spine


def build_panel(
    *,
    spine_path: Path,
    bps_years: list[int],
    bps_cache: Path | None = None,
    fhfa_cache: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    spine = load_spine(spine_path)

    bps, bps_prov, bps_gaps = fetch_bps_years(bps_years, cache_dir=bps_cache)
    fhfa, fhfa_prov = fetch_fhfa_state(cache_dir=fhfa_cache)

    # BPS joins by FIPS; FHFA joins by abbreviation -> FIPS via the spine.
    abbr_to_fips = spine.set_index("state_abbr")["state_fips"].to_dict()
    fhfa = fhfa.copy()
    fhfa["state_fips"] = fhfa["state_abbr"].map(abbr_to_fips)
    fhfa_unmatched = sorted(fhfa.loc[fhfa["state_fips"].isna(), "state_abbr"].unique().tolist())
    fhfa = fhfa.dropna(subset=["state_fips"]).drop(columns=["state_abbr"])

    # Union the (state_fips, year) grain across both sources, then attach IDs.
    keys = pd.concat(
        [bps[["state_fips", "year"]], fhfa[["state_fips", "year"]]],
        ignore_index=True,
    ).drop_duplicates()
    panel = keys.merge(bps, on=["state_fips", "year"], how="left")
    panel = panel.merge(fhfa, on=["state_fips", "year"], how="left")

    # Restrict to canonical spine units and attach ieset_state_id + names.
    panel = spine.merge(panel, on="state_fips", how="inner")

    measure_cols = [
        "bps_total_permit_units",
        "bps_units_1_unit",
        "bps_units_2_to_4_unit",
        "bps_units_5_plus_unit",
        "fhfa_hpi_at_index",
    ]
    panel["measures_present"] = panel[measure_cols].notna().sum(axis=1).astype(int)

    ordered = [
        "ieset_state_id",
        "state_fips",
        "state_abbr",
        "state_name",
        "admin1_kind",
        "is_state_equivalent",
        "year",
        "bps_total_permit_units",
        "bps_units_1_unit",
        "bps_units_2_to_4_unit",
        "bps_units_5_plus_unit",
        "bps_reported_total_permit_units",
        "fhfa_hpi_at_index",
        "fhfa_hpi_quarters_observed",
        "fhfa_hpi_partial_year",
        "measures_present",
    ]
    panel = panel[ordered].sort_values(["ieset_state_id", "year"]).reset_index(drop=True)

    most_recent_year = int(panel.loc[panel["bps_total_permit_units"].notna(), "year"].max())
    states_recent = set(
        panel.loc[
            (panel["year"] == most_recent_year) & (panel["bps_total_permit_units"].notna()),
            "ieset_state_id",
        ]
    )
    bps_year_min = int(panel.loc[panel["bps_total_permit_units"].notna(), "year"].min())
    fhfa_year_min = int(panel.loc[panel["fhfa_hpi_at_index"].notna(), "year"].min())
    fhfa_year_max = int(panel.loc[panel["fhfa_hpi_at_index"].notna(), "year"].max())

    stats = {
        "panel_rows": int(len(panel)),
        "unique_states": int(panel["ieset_state_id"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "bps_year_min": bps_year_min,
        "bps_year_max": int(panel.loc[panel["bps_total_permit_units"].notna(), "year"].max()),
        "fhfa_year_min": fhfa_year_min,
        "fhfa_year_max": fhfa_year_max,
        "states_with_bps_most_recent_year": len(states_recent),
        "most_recent_bps_year": most_recent_year,
        "measure_columns": measure_cols,
        "fhfa_unmatched_abbrs": fhfa_unmatched,
        "bps_gaps": bps_gaps,
        "bps_imputation_note": (
            "bps_total_permit_units and the per-structure-type columns are the BPS "
            "survey estimate, which imputes permit activity for non-reporting "
            "permit-issuing places. bps_reported_total_permit_units carries the "
            "reported-only total for comparison."
        ),
        "structure_type_note": (
            "bps_units_2_to_4_unit = BPS '2-units' + '3-4 units'. "
            "bps_total_permit_units = 1-unit + 2-units + 3-4 units + 5+ units, so "
            "bps_units_1_unit + bps_units_2_to_4_unit + bps_units_5_plus_unit equals "
            "the total exactly (no separate residual category)."
        ),
        "fhfa_index_base_note": FHFA_HPI_BASE_NOTE,
        "fhfa_frequency_note": (
            "FHFA quarterly index values are collapsed to an annual mean; "
            "fhfa_hpi_quarters_observed records the quarters averaged and "
            "fhfa_hpi_partial_year flags years with fewer than 4 quarters "
            "(e.g. the latest, still-incomplete calendar year)."
        ),
    }
    provenance = {"bps_files": bps_prov, "fhfa_file": fhfa_prov}
    return panel, stats, provenance


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
    path = manifest_dir / f"fetch_run_{run_stamp}_us_state_housing_supply_price.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "us_state_housing_supply_price_panel",
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
    return FetchResult(
        publisher=PUBLISHER,
        series_id=SERIES_ID,
        source_url=f"{BPS_DIR_URL} ; {FHFA_AT_STATE_URL}",
        methodology_url=f"{BPS_METHODOLOGY_URL} ; {FHFA_METHODOLOGY_URL}",
        license="U.S. Census Bureau (BPS) and U.S. FHFA (HPI) public domain data",
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual (state-year)",
        units="permitted housing units (counts); FHFA HPI index (1980Q1=100)",
        currency=None,
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
                "Annual U.S. state housing supply + price panel. Census Building "
                "Permits Survey annual state files (stYYYYa.txt, FIPS-keyed) supply "
                "total permitted units and units by structure type (1-unit, 2-4 "
                "unit, 5+ unit). FHFA All-Transactions state HPI (abbr-keyed, "
                "crosswalked to FIPS via the admin-1 spine) supplies the annual-mean "
                "house price index. Both are public domain; one row per "
                "(ieset_state_id, year); state_fips and state_abbr preserved."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spine", default="data/derived/state_universe_admin1.parquet")
    parser.add_argument("--output", default="data/derived/us_state_housing_supply_price_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--bps-start", type=int, default=BPS_DEFAULT_START)
    parser.add_argument("--bps-end", type=int, default=BPS_DEFAULT_END)
    parser.add_argument("--bps-cache", help="Optional local dir of stYYYYa.txt files (offline build).")
    parser.add_argument("--fhfa-cache", help="Optional local dir holding hpi_at_state.csv (offline build).")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    bps_years = list(range(args.bps_start, args.bps_end + 1))
    bps_cache = path_arg(args.bps_cache).resolve() if args.bps_cache else None
    fhfa_cache = path_arg(args.fhfa_cache).resolve() if args.fhfa_cache else None

    panel, stats, provenance = build_panel(
        spine_path=path_arg(args.spine).resolve(),
        bps_years=bps_years,
        bps_cache=bps_cache,
        fhfa_cache=fhfa_cache,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, provenance, output_path, fetch_ts)
    methodology = {
        "build_utc": fetch_ts.isoformat(),
        "row_count": int(len(panel)),
        "columns": list(panel.columns),
        "measure_columns": stats["measure_columns"],
        "bps_imputation_note": stats["bps_imputation_note"],
        "structure_type_note": stats["structure_type_note"],
        "fhfa_index_base_note": stats["fhfa_index_base_note"],
        "fhfa_frequency_note": stats["fhfa_frequency_note"],
        "bps_gaps": stats["bps_gaps"],
        "fhfa_unmatched_abbrs": stats["fhfa_unmatched_abbrs"],
        "inputs": provenance,
        "spine": rel(path_arg(args.spine).resolve()),
    }
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts), methodology)
    print(
        f"OK {PUBLISHER}:{SERIES_ID} rows={result.rows} "
        f"years={stats['year_min']}->{stats['year_max']} states={stats['unique_states']} "
        f"bps_recent_year={stats['most_recent_bps_year']} "
        f"states_recent={stats['states_with_bps_most_recent_year']} "
        f"fhfa={stats['fhfa_year_min']}->{stats['fhfa_year_max']}"
    )
    if stats["bps_gaps"]:
        print(f"WARN bps_gaps={len(stats['bps_gaps'])} (see manifest)")
    if stats["fhfa_unmatched_abbrs"]:
        print(f"WARN fhfa_unmatched_abbrs={stats['fhfa_unmatched_abbrs']}")
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
