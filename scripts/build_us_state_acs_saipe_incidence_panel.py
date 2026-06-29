#!/usr/bin/env python3
"""Build a U.S. state-year distributional-incidence panel from on-disk Census vintages.

Merges the newest Census state vintages already fetched under
data/vintages/us_census/:
  - ACS@*.parquet (Census ACS state profile) -> total population (B01003_001E),
    median household income (B19013_001E).
  - saipe@*.parquet (Small Area Income and Poverty Estimates, state) ->
    all-ages poverty rate (SAEPOVRTALL_PT), median household income (SAEMHI_PT).
  - acs_education_attainment@*.parquet (ACS table B15003) -> population 25+,
    counts at bachelor's/master's/professional/doctorate, from which a
    bachelor's-degree-or-higher share is derived.
  - acs_school_enrollment@*.parquet (ACS table B14001) -> enrollment-universe
    population (3+) and enrolled count, from which an enrolled share is derived.

Every row is joined to the canonical ieset_state_id via state_fips from the
admin-1 spine (state_universe_admin1), and state_fips is preserved. Each source
contributes a *_obs coverage flag (1 when that source supplied a value for the
state-year, else 0).

NEVER fabricated: only variables actually present in the on-disk vintages are
used. Canonical incidence dimensions that are NOT available in these vintages
(homeownership/tenure, median gross rent, median housing cost, rent burden /
cost-burdened share, income-distribution/Gini measures, and state-grain SPM
child poverty -- the spm_child_poverty_rate vintage is national-only) are
omitted and recorded under documented_gaps in the manifest, not invented.
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

VINTAGE_DIR = ROOT / "data" / "vintages" / "us_census"

SOURCE_URL = "https://www.census.gov/data/developers/data-sets.html"
METHODOLOGY_URL = (
    "https://www.census.gov/programs-surveys/acs/ "
    "https://www.census.gov/programs-surveys/saipe.html"
)
LICENSE = "U.S. Census Bureau public domain data"
PUBLISHER = "us_census_bureau"
SERIES_ID = "us_state_acs_saipe_incidence_panel"

# Newest-vintage glob prefixes for each input panel.
INPUT_GLOBS = {
    "acs_state_profile": "ACS@*.parquet",
    "saipe_state": "saipe@*.parquet",
    "acs_education_attainment": "acs_education_attainment@*.parquet",
    "acs_school_enrollment": "acs_school_enrollment@*.parquet",
}

# Canonical incidence dimensions sought but absent from the on-disk vintages.
DOCUMENTED_GAPS = [
    {
        "dimension": "homeownership_tenure_rate",
        "reason": (
            "The ACS state-profile vintage carries only total population "
            "(B01003) and median household income (B19013); no owner/renter "
            "tenure table (B25003) is present."
        ),
    },
    {
        "dimension": "median_gross_rent",
        "reason": "No ACS gross-rent table (B25064) present in the on-disk ACS vintage.",
    },
    {
        "dimension": "median_housing_cost",
        "reason": (
            "No ACS selected-monthly-owner-cost / housing-cost table (B25088/B25105) "
            "present in the on-disk ACS vintage."
        ),
    },
    {
        "dimension": "rent_burden_cost_burdened_share",
        "reason": (
            "No ACS gross-rent-as-percentage-of-income table (B25070) or "
            "selected-monthly-owner-costs-as-percentage-of-income table (B25091) "
            "present; cost-burdened share cannot be derived without fabrication."
        ),
    },
    {
        "dimension": "income_distribution_gini",
        "reason": (
            "No ACS Gini index (B19083) or household-income-quintile table (B19080) "
            "present in the on-disk ACS vintage; only median household income is available."
        ),
    },
    {
        "dimension": "spm_child_poverty_rate_state_grain",
        "reason": (
            "The spm_child_poverty_rate vintage is national-only (geo_area='USA'); "
            "it carries no state-level rows and cannot populate a state-year panel."
        ),
    },
]


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
# Per-source transforms (each returns a state_fips/year-keyed annual frame)
# ---------------------------------------------------------------------------

def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _acs_profile(path: Path) -> pd.DataFrame:
    """ACS state profile -> total population + median household income per state-year."""
    df = pd.read_parquet(path)
    df["state_fips"] = df["state"].astype(str).str.zfill(2)
    out = pd.DataFrame(
        {
            "state_fips": df["state_fips"],
            "year": df["year"].astype(int),
            "acs_total_population": _to_num(df["B01003_001E"]),
            "acs_median_household_income": _to_num(df["B19013_001E"]),
        }
    )
    out = out.groupby(["state_fips", "year"], as_index=False).first()
    out["acs_profile_obs"] = out[
        ["acs_total_population", "acs_median_household_income"]
    ].notna().any(axis=1).astype(int)
    return out


def _saipe(path: Path) -> pd.DataFrame:
    """SAIPE state -> all-ages poverty rate + median household income per state-year."""
    df = pd.read_parquet(path)
    df["state_fips"] = df["state"].astype(str).str.zfill(2)
    out = pd.DataFrame(
        {
            "state_fips": df["state_fips"],
            "year": df["year"].astype(int),
            "saipe_poverty_rate_all_ages": _to_num(df["SAEPOVRTALL_PT"]),
            "saipe_median_household_income": _to_num(df["SAEMHI_PT"]),
        }
    )
    out = out.groupby(["state_fips", "year"], as_index=False).first()
    out["saipe_obs"] = out[
        ["saipe_poverty_rate_all_ages", "saipe_median_household_income"]
    ].notna().any(axis=1).astype(int)
    return out


def _acs_education(path: Path) -> pd.DataFrame:
    """ACS B15003 -> bachelor's-degree-or-higher share of population 25+.

    B15003_001E = total population 25 years and over.
    B15003_022E = bachelor's degree, _023E = master's, _024E = professional
    school degree, _025E = doctorate. The share is the sum of those four counts
    divided by the 25+ total -- a derivation over counts that are all present in
    the vintage (no value is invented).
    """
    df = pd.read_parquet(path)
    df["state_fips"] = df["state"].astype(str).str.zfill(2)
    total = _to_num(df["B15003_001E"])
    ba_plus = (
        _to_num(df["B15003_022E"])
        + _to_num(df["B15003_023E"])
        + _to_num(df["B15003_024E"])
        + _to_num(df["B15003_025E"])
    )
    share = (ba_plus / total * 100.0).where(total > 0)
    out = pd.DataFrame(
        {
            "state_fips": df["state_fips"],
            "year": df["year"].astype(int),
            "acs_population_25_plus": total,
            "acs_bachelors_or_higher_share": share,
        }
    )
    out = out.groupby(["state_fips", "year"], as_index=False).first()
    out["acs_education_obs"] = out["acs_bachelors_or_higher_share"].notna().astype(int)
    return out


def _acs_enrollment(path: Path) -> pd.DataFrame:
    """ACS B14001 -> enrolled share of the school-enrollment universe (pop 3+).

    B14001_001E = total population 3 years and over (enrollment universe).
    B14001_002E = enrolled in school. Share = enrolled / universe.
    """
    df = pd.read_parquet(path)
    df["state_fips"] = df["state"].astype(str).str.zfill(2)
    universe = _to_num(df["B14001_001E"])
    enrolled = _to_num(df["B14001_002E"])
    share = (enrolled / universe * 100.0).where(universe > 0)
    out = pd.DataFrame(
        {
            "state_fips": df["state_fips"],
            "year": df["year"].astype(int),
            "acs_enrollment_universe_3_plus": universe,
            "acs_school_enrolled_share": share,
        }
    )
    out = out.groupby(["state_fips", "year"], as_index=False).first()
    out["acs_enrollment_obs"] = out["acs_school_enrolled_share"].notna().astype(int)
    return out


def load_spine(spine_path: Path) -> pd.DataFrame:
    spine = pd.read_parquet(spine_path)
    spine = spine[
        ["ieset_state_id", "state_fips", "state_abbr", "state_name", "is_state_equivalent"]
    ].copy()
    spine["state_fips"] = spine["state_fips"].astype(str).str.zfill(2)
    return spine


def build_panel(
    *,
    inputs: dict[str, Path],
    spine_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    spine = load_spine(spine_path)

    parts = [
        _saipe(inputs["saipe_state"]),
        _acs_profile(inputs["acs_state_profile"]),
        _acs_education(inputs["acs_education_attainment"]),
        _acs_enrollment(inputs["acs_school_enrollment"]),
    ]

    # Union the (state_fips, year) grain across all sources.
    keys = (
        pd.concat([p[["state_fips", "year"]] for p in parts], ignore_index=True)
        .drop_duplicates()
    )
    panel = keys.copy()
    for part in parts:
        panel = panel.merge(part, on=["state_fips", "year"], how="left")

    # Coverage flags default to 0 where a source supplied no row.
    for flag in ["saipe_obs", "acs_profile_obs", "acs_education_obs", "acs_enrollment_obs"]:
        panel[flag] = panel[flag].fillna(0).astype(int)

    # Restrict to states/territories present in the canonical spine; attach IDs.
    panel = spine.merge(panel, on="state_fips", how="inner")

    incidence_cols = [
        "saipe_poverty_rate_all_ages",
        "saipe_median_household_income",
        "acs_median_household_income",
        "acs_bachelors_or_higher_share",
        "acs_school_enrolled_share",
    ]
    panel["incidence_measures_present"] = (
        panel[incidence_cols].notna().sum(axis=1).astype(int)
    )

    ordered = [
        "ieset_state_id",
        "state_fips",
        "state_abbr",
        "state_name",
        "is_state_equivalent",
        "year",
        "saipe_poverty_rate_all_ages",
        "saipe_median_household_income",
        "saipe_obs",
        "acs_median_household_income",
        "acs_total_population",
        "acs_profile_obs",
        "acs_bachelors_or_higher_share",
        "acs_population_25_plus",
        "acs_education_obs",
        "acs_school_enrolled_share",
        "acs_enrollment_universe_3_plus",
        "acs_enrollment_obs",
        "incidence_measures_present",
    ]
    panel = panel[ordered].sort_values(["ieset_state_id", "year"]).reset_index(drop=True)

    most_recent_year = int(panel["year"].max())
    states_recent = set(
        panel.loc[
            (panel["year"] == most_recent_year) & (panel["incidence_measures_present"] > 0),
            "ieset_state_id",
        ]
    )
    stats = {
        "panel_rows": int(len(panel)),
        "unique_states": int(panel["ieset_state_id"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": most_recent_year,
        "states_with_data_most_recent_year": len(states_recent),
        "incidence_columns": incidence_cols,
        "covered_dimensions": [
            "median_household_income (SAIPE SAEMHI_PT + ACS B19013_001E)",
            "poverty_rate_all_ages (SAIPE SAEPOVRTALL_PT)",
            "educational_attainment_bachelors_or_higher_share (ACS B15003)",
            "school_enrolled_share (ACS B14001)",
        ],
        "derivation_note": (
            "acs_bachelors_or_higher_share = (B15003_022E+023E+024E+025E)/B15003_001E*100. "
            "acs_school_enrolled_share = B14001_002E/B14001_001E*100. saipe_poverty_rate_all_ages "
            "and median household incomes are pulled verbatim from the source estimate columns."
        ),
        "coverage_note": (
            "*_obs flags are 1 when the named source supplied a value for the state-year, "
            "else 0. ACS profile/education/enrollment vintages cover ACS 1-year 2022 only; "
            "SAIPE covers 2018-2022, so SAIPE-only measures populate earlier years."
        ),
    }
    return panel, stats


def build_provenance(inputs: dict[str, Path]) -> list[dict[str, Any]]:
    prov = []
    for key, path in inputs.items():
        df = pd.read_parquet(path)
        prov.append(
            {
                "input": key,
                "path": rel(path),
                "sha256": sha256_path(path),
                "rows": int(len(df)),
                "columns": list(df.columns),
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
    path = manifest_dir / f"fetch_run_{run_stamp}_us_state_acs_saipe_incidence.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "us_state_acs_saipe_incidence_panel",
        "methodology": methodology,
        "documented_gaps": DOCUMENTED_GAPS,
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
        units="percent, US dollars, population counts",
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
            "documented_gaps": DOCUMENTED_GAPS,
            "construction": (
                "U.S. state-year distributional-incidence panel merging the newest "
                "Census ACS state-profile, SAIPE, ACS education-attainment, and ACS "
                "school-enrollment vintages on disk. Every row is joined to "
                "ieset_state_id via state_fips from state_universe_admin1; state_fips "
                "is preserved. Bachelor's-or-higher and enrolled shares are derived "
                "from counts present in the vintages; no incidence dimension absent "
                "from the vintages is fabricated -- gaps are listed under documented_gaps."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vintage-dir", default=str(VINTAGE_DIR))
    parser.add_argument("--spine", default="data/derived/state_universe_admin1.parquet")
    parser.add_argument(
        "--output", default="data/derived/us_state_acs_saipe_incidence_panel.parquet"
    )
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
        "incidence_columns": stats["incidence_columns"],
        "covered_dimensions": stats["covered_dimensions"],
        "derivation_note": stats["derivation_note"],
        "coverage_note": stats["coverage_note"],
        "spine": rel(path_arg(args.spine).resolve()),
    }
    manifest = write_manifest(
        result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts), methodology
    )
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
