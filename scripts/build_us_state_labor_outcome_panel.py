#!/usr/bin/env python3
"""Build a tidy U.S. state-year labor-outcome panel from on-disk BLS vintages.

Merges the newest BLS state vintages already fetched under data/vintages/bls/:
  - LAU state unemployment-rate panel (measure_code 03, monthly M01-M12)
  - LAU state employment-population-ratio panel (measure_code 07, monthly)
  - OEWS state median hourly wage panel (datatype_code 08, annual A01)
  - OEWS state p10 hourly wage panel (annual A01)
  - QCEW state total-employment panel (own 0 / industry 10 / agglvl 50, annual)
  - QCEW state NAICS722 food-service panel (own 5 / industry 722, annual)

LAU monthly series are collapsed to an annual mean (12-month average) so that
monthly and annual frequencies are never silently mixed. Every output row is
joined to the canonical ieset_state_id via state_fips from the admin-1 spine,
and state_fips is preserved. QCEW disclosure flags and OEWS observation counts
per state-year are carried through as note columns.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
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

VINTAGE_DIR = ROOT / "data" / "vintages" / "bls"

SOURCE_URL = "https://www.bls.gov/data/"
METHODOLOGY_URL = "https://www.bls.gov/lau/ https://www.bls.gov/oes/ https://www.bls.gov/cew/"
LICENSE = "U.S. Bureau of Labor Statistics public domain data"
PUBLISHER = "us_bureau_of_labor_statistics"
SERIES_ID = "us_state_labor_outcome_panel"

# Newest-vintage glob prefixes for each input panel.
INPUT_GLOBS = {
    "lau_unemployment_rate": "LAU_state_unemployment_rate_panel@*.parquet",
    "lau_emp_pop_ratio": "LAU_state_employment_population_ratio_panel@*.parquet",
    "oews_median_hourly_wage": "OEWS_state_median_hourly_wage_panel@*.parquet",
    "oews_p10_hourly_wage": "OEWS_state_p10_hourly_wage_panel@*.parquet",
    "qcew_total_employment": "QCEW_state_total_employment_panel@*.parquet",
    "qcew_naics722_employment": "QCEW_state_NAICS722_employment_panel@*.parquet",
}


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


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


def newest_vintage(vintage_dir: Path, pattern: str) -> Path:
    """Return the path with the newest @timestamp for the given glob pattern."""
    matches = sorted(glob.glob(str(vintage_dir / pattern)))
    if not matches:
        raise FileNotFoundError(f"No vintage found under {vintage_dir} matching {pattern}")
    # Filenames sort lexicographically by the trailing @<UTC-ISO> timestamp.
    return Path(matches[-1])


def resolve_inputs(vintage_dir: Path) -> dict[str, Path]:
    return {key: newest_vintage(vintage_dir, pattern) for key, pattern in INPUT_GLOBS.items()}


# ---------------------------------------------------------------------------
# Per-source transforms (each returns a state_fips-keyed annual frame)
# ---------------------------------------------------------------------------

def _lau_annual(path: Path, measure_code: str, value_col: str) -> pd.DataFrame:
    """Collapse LAU monthly (M01-M12) observations to an annual mean per state-year.

    Only true monthly periods are averaged; any non-monthly period codes are
    dropped so monthly and annual frequencies are never mixed.
    """
    df = pd.read_parquet(path)
    df = df[df["measure_code"].astype(str) == measure_code].copy()
    monthly = df["period"].astype(str).str.match(r"^M(0[1-9]|1[0-2])$")
    df = df[monthly]
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    grp = (
        df.groupby(["state_fips", "year"], as_index=False)
        .agg(value=("value", "mean"), months_observed=("value", "size"))
    )
    grp = grp.rename(columns={"value": value_col, "months_observed": f"{value_col}_months_observed"})
    return grp


def _oews_annual(path: Path, value_col: str) -> pd.DataFrame:
    """OEWS state annual hourly-wage series (period A01). One row per state-year."""
    df = pd.read_parquet(path)
    df = df[df["period"].astype(str) == "A01"].copy()
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    out = (
        df.groupby(["state_fips", "year"], as_index=False)
        .agg(**{value_col: ("value", "first"), f"{value_col}_obs": ("value", "size")})
    )
    return out


def _qcew_annual(
    path: Path,
    emp_col: str,
    wage_col: str | None = None,
    estabs_col: str | None = None,
    disclosure_col: str | None = None,
) -> pd.DataFrame:
    """QCEW state annual (qtr='A') employment + weekly wage, keyed by state_fips.

    state_fips is derived from the 5-char area_fips (first two characters).
    Disclosure code is carried through under the requested column name.
    """
    df = pd.read_parquet(path)
    df = df[df["qtr"].astype(str) == "A"].copy()
    df["state_fips"] = df["area_fips"].astype(str).str.zfill(5).str[:2]
    agg: dict[str, Any] = {emp_col: ("annual_avg_emplvl", "first")}
    if wage_col is not None:
        agg[wage_col] = ("annual_avg_wkly_wage", "first")
    if estabs_col is not None:
        agg[estabs_col] = ("annual_avg_estabs", "first")
    if disclosure_col is not None:
        df[disclosure_col] = df["disclosure_code"].astype("string")
        agg[disclosure_col] = (disclosure_col, "first")
    out = df.groupby(["state_fips", "year"], as_index=False).agg(**agg)
    return out


def load_spine(spine_path: Path) -> pd.DataFrame:
    spine = pd.read_parquet(spine_path)
    spine = spine[["ieset_state_id", "state_fips", "state_abbr", "state_name", "is_state_equivalent"]].copy()
    spine["state_fips"] = spine["state_fips"].astype(str).str.zfill(2)
    return spine


def build_panel(
    *,
    inputs: dict[str, Path],
    spine_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    spine = load_spine(spine_path)

    parts = [
        _lau_annual(inputs["lau_unemployment_rate"], "03", "unemployment_rate"),
        _lau_annual(inputs["lau_emp_pop_ratio"], "07", "employment_population_ratio"),
        _oews_annual(inputs["oews_median_hourly_wage"], "median_hourly_wage"),
        _oews_annual(inputs["oews_p10_hourly_wage"], "p10_hourly_wage"),
        _qcew_annual(
            inputs["qcew_total_employment"],
            emp_col="qcew_total_employment",
            wage_col="qcew_avg_weekly_wage",
            estabs_col="qcew_total_establishments",
            disclosure_col="qcew_total_disclosure_code",
        ),
        _qcew_annual(
            inputs["qcew_naics722_employment"],
            emp_col="qcew_food_service_employment",
            wage_col="qcew_food_service_avg_weekly_wage",
            estabs_col="qcew_food_service_establishments",
            disclosure_col="qcew_food_service_disclosure_code",
        ),
    ]

    # Union the (state_fips, year) grain across all sources.
    keys = pd.concat([p[["state_fips", "year"]] for p in parts], ignore_index=True).drop_duplicates()
    panel = keys.copy()
    for part in parts:
        panel = panel.merge(part, on=["state_fips", "year"], how="left")

    # Restrict to states/territories present in the canonical spine and attach IDs.
    panel = spine.merge(panel, on="state_fips", how="inner")

    outcome_cols = [
        "unemployment_rate",
        "employment_population_ratio",
        "median_hourly_wage",
        "p10_hourly_wage",
        "qcew_total_employment",
        "qcew_avg_weekly_wage",
        "qcew_food_service_employment",
        "qcew_food_service_avg_weekly_wage",
    ]
    # Build an observation-completeness note per row.
    panel["outcomes_present"] = panel[outcome_cols].notna().sum(axis=1).astype(int)

    ordered = [
        "ieset_state_id",
        "state_fips",
        "state_abbr",
        "state_name",
        "is_state_equivalent",
        "year",
        "unemployment_rate",
        "unemployment_rate_months_observed",
        "employment_population_ratio",
        "employment_population_ratio_months_observed",
        "median_hourly_wage",
        "median_hourly_wage_obs",
        "p10_hourly_wage",
        "p10_hourly_wage_obs",
        "qcew_total_employment",
        "qcew_avg_weekly_wage",
        "qcew_total_establishments",
        "qcew_total_disclosure_code",
        "qcew_food_service_employment",
        "qcew_food_service_avg_weekly_wage",
        "qcew_food_service_establishments",
        "qcew_food_service_disclosure_code",
        "outcomes_present",
    ]
    panel = panel[ordered].sort_values(["ieset_state_id", "year"]).reset_index(drop=True)

    most_recent_year = int(panel["year"].max())
    states_recent = set(
        panel.loc[
            (panel["year"] == most_recent_year) & (panel["outcomes_present"] > 0),
            "ieset_state_id",
        ]
    )
    stats = {
        "panel_rows": int(len(panel)),
        "unique_states": int(panel["ieset_state_id"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": most_recent_year,
        "states_with_data_most_recent_year": len(states_recent),
        "outcome_columns": outcome_cols,
        "frequency_note": (
            "LAU unemployment_rate (measure 03) and employment_population_ratio "
            "(measure 07) are collapsed from monthly M01-M12 observations to an "
            "annual 12-month mean; *_months_observed records the count averaged. "
            "OEWS and QCEW inputs are already annual (A01 / qtr='A'). Monthly and "
            "annual frequencies are never mixed."
        ),
        "qcew_disclosure_note": (
            "qcew_*_disclosure_code carries the BLS QCEW disclosure flag verbatim "
            "(null when not suppressed)."
        ),
    }
    return panel, stats


def build_provenance(inputs: dict[str, Path]) -> list[dict[str, Any]]:
    prov = []
    for key, path in inputs.items():
        prov.append(
            {
                "input": key,
                "path": rel(path),
                "sha256": sha256_path(path),
            }
        )
    return prov


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
    path = manifest_dir / f"fetch_run_{run_stamp}_us_state_labor_outcome.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "us_state_labor_outcome_panel",
        "methodology": methodology,
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(
    panel: pd.DataFrame,
    stats: dict[str, Any],
    provenance: list[dict[str, Any]],
    output_path: Path,
    fetch_ts: datetime,
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher=PUBLISHER,
        series_id=SERIES_ID,
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual (state-year)",
        units="percent, US dollars per hour, employment counts, US dollars per week",
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
                "Tidy U.S. state-year labor-outcome panel merging the newest BLS "
                "LAU/OEWS/QCEW state vintages on disk. LAU monthly series are "
                "averaged to annual means; OEWS and QCEW are already annual. Every "
                "row is joined to ieset_state_id via state_fips from "
                "state_universe_admin1; state_fips is preserved and QCEW disclosure "
                "flags plus OEWS observation counts are carried as note columns."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vintage-dir", default=str(VINTAGE_DIR))
    parser.add_argument("--spine", default="data/derived/state_universe_admin1.parquet")
    parser.add_argument("--output", default="data/derived/us_state_labor_outcome_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    inputs = resolve_inputs(path_arg(args.vintage_dir).resolve())
    panel, stats = build_panel(inputs=inputs, spine_path=path_arg(args.spine).resolve())
    provenance = build_provenance(inputs)
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, provenance, output_path, fetch_ts)
    methodology = {
        "build_utc": fetch_ts.isoformat(),
        "inputs": provenance,
        "row_count": int(len(panel)),
        "columns": list(panel.columns),
        "outcome_columns": stats["outcome_columns"],
        "frequency_note": stats["frequency_note"],
        "qcew_disclosure_note": stats["qcew_disclosure_note"],
        "spine": rel(path_arg(args.spine).resolve()),
    }
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts), methodology)
    print(
        f"OK {PUBLISHER}:{SERIES_ID} rows={result.rows} "
        f"years={stats['year_min']}->{stats['year_max']} states={stats['unique_states']} "
        f"states_recent_year={stats['states_with_data_most_recent_year']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
