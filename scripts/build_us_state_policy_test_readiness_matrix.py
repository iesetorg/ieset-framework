#!/usr/bin/env python3
"""Build the U.S. state policy-test readiness matrix from landed state-level panels.

Mirrors scripts/build_city_policy_test_readiness_matrix.py for the
``us_state_labor_policy_v0`` wave: one row per admin1 in the state spine,
scoring which policy-test layers each state actually has on disk, and exposing
the missing layers rather than hiding them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


DEFAULT_INPUTS = {
    "state_spine": "data/derived/state_universe_admin1.parquet",
    "minimum_wage_treatment": "data/derived/us_state_minimum_wage_treatment_panel.parquet",
    "labor_outcome": "data/derived/us_state_labor_outcome_panel.parquet",
    "housing_supply_price": "data/derived/us_state_housing_supply_price_panel.parquet",
    "fiscal": "data/derived/us_state_gov_finances_panel.parquet",
    "distributional_incidence": "data/derived/us_state_acs_saipe_incidence_panel.parquet",
}

# Layers that are documented gaps this round if the optional panel is absent.
LAYER_FLAGS = [
    "minimum_wage_treatment_layer",
    "labor_outcome_layer",
    "housing_supply_price_layer",
    "fiscal_layer",
    "distributional_incidence_layer",
]

TIERS = [
    "spine_only",
    "treatment_only",
    "outcome_only",
    "treatment_plus_outcome",
    "case_ready_state_panel",
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
        return datetime.now(tz=timezone.utc)
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


def utc_stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"unsupported input format: {path}")


def ensure_state_id(frame: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if "ieset_state_id" not in frame.columns:
        raise ValueError(f"{source_name} is missing ieset_state_id")
    return frame[frame["ieset_state_id"].notna()].copy()


def merge_agg(base: pd.DataFrame, agg: pd.DataFrame, fill_values: dict[str, Any]) -> pd.DataFrame:
    base = base.drop(columns=[column for column in fill_values if column in base.columns])
    out = base.merge(agg, on="ieset_state_id", how="left")
    for column, value in fill_values.items():
        if column in out.columns and value is not None:
            out[column] = out[column].fillna(value)
    return out


def add_minimum_wage_treatment(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "mw_treatment_rows": 0,
        "mw_treatment_years": 0,
        "mw_treatment_start_year": None,
        "mw_treatment_end_year": None,
        "mw_binds_above_federal_years": 0,
        "mw_first_bind_events": 0,
        "mw_increase_events": 0,
        "mw_first_bind_year": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_state_id(frame, "minimum_wage_treatment")
    frame = frame.assign(
        _binds=frame["binds_above_federal"].fillna(False).astype(bool).astype(int),
        _first_bind=frame["is_first_bind_event"].fillna(False).astype(bool).astype(int),
        _increase=frame["event_type"].eq("increase").astype(int),
        _first_bind_year=frame["year"].where(frame["is_first_bind_event"].fillna(False).astype(bool)),
    )
    agg = (
        frame.groupby("ieset_state_id")
        .agg(
            mw_treatment_rows=("year", "size"),
            mw_treatment_years=("year", "nunique"),
            mw_treatment_start_year=("year", "min"),
            mw_treatment_end_year=("year", "max"),
            mw_binds_above_federal_years=("_binds", "sum"),
            mw_first_bind_events=("_first_bind", "sum"),
            mw_increase_events=("_increase", "sum"),
            mw_first_bind_year=("_first_bind_year", "min"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_labor_outcome(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "labor_outcome_rows": 0,
        "labor_outcome_years": 0,
        "labor_outcome_start_year": None,
        "labor_outcome_end_year": None,
        "labor_unemployment_obs": 0,
        "labor_emp_pop_obs": 0,
        "labor_wage_obs": 0,
        "labor_qcew_obs": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_state_id(frame, "labor_outcome")
    frame = frame.assign(
        _unemp=frame["unemployment_rate"].notna().astype(int),
        _emp_pop=frame["employment_population_ratio"].notna().astype(int),
        _wage=frame["median_hourly_wage"].notna().astype(int),
        _qcew=frame["qcew_total_employment"].notna().astype(int),
    )
    agg = (
        frame.groupby("ieset_state_id")
        .agg(
            labor_outcome_rows=("year", "size"),
            labor_outcome_years=("year", "nunique"),
            labor_outcome_start_year=("year", "min"),
            labor_outcome_end_year=("year", "max"),
            labor_unemployment_obs=("_unemp", "sum"),
            labor_emp_pop_obs=("_emp_pop", "sum"),
            labor_wage_obs=("_wage", "sum"),
            labor_qcew_obs=("_qcew", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_housing_supply_price(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "housing_supply_price_rows": 0,
        "housing_supply_price_years": 0,
        "housing_supply_price_start_year": None,
        "housing_supply_price_end_year": None,
        "housing_permit_obs": 0,
        "housing_hpi_obs": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_state_id(frame, "housing_supply_price")
    year_col = "year" if "year" in frame.columns else frame.columns[1]
    permit_col = next((c for c in frame.columns if "permit" in c.lower() or "bps" in c.lower() or "unit" in c.lower()), None)
    hpi_col = next((c for c in frame.columns if "hpi" in c.lower() or "price_index" in c.lower() or "fhfa" in c.lower()), None)
    frame = frame.assign(
        _permit=frame[permit_col].notna().astype(int) if permit_col else 0,
        _hpi=frame[hpi_col].notna().astype(int) if hpi_col else 0,
    )
    agg = (
        frame.groupby("ieset_state_id")
        .agg(
            housing_supply_price_rows=(year_col, "size"),
            housing_supply_price_years=(year_col, "nunique"),
            housing_supply_price_start_year=(year_col, "min"),
            housing_supply_price_end_year=(year_col, "max"),
            housing_permit_obs=("_permit", "sum"),
            housing_hpi_obs=("_hpi", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_fiscal(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "fiscal_rows": 0,
        "fiscal_years": 0,
        "fiscal_start_year": None,
        "fiscal_end_year": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_state_id(frame, "fiscal")
    year_col = "year" if "year" in frame.columns else frame.columns[1]
    agg = (
        frame.groupby("ieset_state_id")
        .agg(
            fiscal_rows=(year_col, "size"),
            fiscal_years=(year_col, "nunique"),
            fiscal_start_year=(year_col, "min"),
            fiscal_end_year=(year_col, "max"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_distributional_incidence(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "distributional_incidence_rows": 0,
        "distributional_incidence_years": 0,
        "distributional_incidence_start_year": None,
        "distributional_incidence_end_year": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_state_id(frame, "distributional_incidence")
    year_col = "year" if "year" in frame.columns else frame.columns[1]
    agg = (
        frame.groupby("ieset_state_id")
        .agg(
            distributional_incidence_rows=(year_col, "size"),
            distributional_incidence_years=(year_col, "nunique"),
            distributional_incidence_start_year=(year_col, "min"),
            distributional_incidence_end_year=(year_col, "max"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def assign_layers(matrix: pd.DataFrame) -> pd.DataFrame:
    out = matrix.copy()
    out["minimum_wage_treatment_layer"] = out["mw_treatment_rows"].gt(0)
    out["labor_outcome_layer"] = out["labor_outcome_rows"].gt(0)
    out["housing_supply_price_layer"] = out["housing_supply_price_rows"].gt(0)
    out["fiscal_layer"] = out["fiscal_rows"].gt(0)
    out["distributional_incidence_layer"] = out["distributional_incidence_rows"].gt(0)

    out["state_policy_core_layer_count"] = out[LAYER_FLAGS].sum(axis=1).astype(int)

    def missing(row: pd.Series) -> list[str]:
        return [layer for layer in LAYER_FLAGS if not bool(row[layer])]

    out["missing_layers"] = out.apply(lambda row: ";".join(missing(row)), axis=1)

    def tier(row: pd.Series) -> str:
        treatment = bool(row["minimum_wage_treatment_layer"])
        outcome = bool(row["labor_outcome_layer"])
        housing = bool(row["housing_supply_price_layer"])
        if treatment and outcome and housing:
            return "case_ready_state_panel"
        if treatment and outcome:
            return "treatment_plus_outcome"
        if treatment:
            return "treatment_only"
        if outcome:
            return "outcome_only"
        return "spine_only"

    out["state_policy_readiness_tier"] = out.apply(tier, axis=1)
    return out


def build_matrix(inputs: dict[str, Path]) -> tuple[pd.DataFrame, dict[str, Any]]:
    spine_path = inputs["state_spine"]
    if not spine_path.exists():
        raise FileNotFoundError(f"missing state spine: {spine_path}")
    spine = pd.read_parquet(spine_path) if spine_path.suffix == ".parquet" else pd.read_csv(spine_path)
    base_cols = [
        "ieset_state_id",
        "country_iso3",
        "country_name",
        "state_name",
        "state_abbr",
        "state_fips",
        "iso_3166_2",
        "admin1_kind",
        "is_state_equivalent",
    ]
    base_cols = [c for c in base_cols if c in spine.columns]
    matrix = spine[base_cols].copy()
    matrix = add_minimum_wage_treatment(matrix, read_optional(inputs["minimum_wage_treatment"]))
    matrix = add_labor_outcome(matrix, read_optional(inputs["labor_outcome"]))
    matrix = add_housing_supply_price(matrix, read_optional(inputs["housing_supply_price"]))
    matrix = add_fiscal(matrix, read_optional(inputs["fiscal"]))
    matrix = add_distributional_incidence(matrix, read_optional(inputs["distributional_incidence"]))
    matrix = assign_layers(matrix)
    matrix = matrix.sort_values(
        ["state_policy_core_layer_count", "mw_binds_above_federal_years", "state_name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    closest = matrix.loc[
        matrix["state_policy_readiness_tier"].isin(["treatment_plus_outcome", "case_ready_state_panel"]),
        [
            "ieset_state_id",
            "state_name",
            "state_policy_readiness_tier",
            "state_policy_core_layer_count",
            "mw_binds_above_federal_years",
            "missing_layers",
        ],
    ].sort_values(
        ["state_policy_core_layer_count", "mw_binds_above_federal_years"],
        ascending=[False, False],
    )

    stats = {
        "state_rows": int(len(matrix)),
        "countries": int(matrix["country_name"].nunique()) if "country_name" in matrix.columns else 1,
        "tier_counts": {str(k): int(v) for k, v in matrix["state_policy_readiness_tier"].value_counts().to_dict().items()},
        "layer_counts": {layer: int(matrix[layer].sum()) for layer in LAYER_FLAGS},
        "case_ready_state_ids": matrix.loc[
            matrix["state_policy_readiness_tier"].eq("case_ready_state_panel"),
            ["ieset_state_id", "state_name", "country_name"],
        ].to_dict("records"),
        "closest_to_case_ready": closest.head(15)[
            ["ieset_state_id", "state_name", "state_policy_readiness_tier", "mw_binds_above_federal_years", "missing_layers"]
        ].to_dict("records"),
        "input_paths": {key: rel(path) for key, path in inputs.items()},
        "missing_optional_inputs": [key for key, path in inputs.items() if key != "state_spine" and not path.exists()],
        "documented_gap_layers": sorted(
            {layer for layer in LAYER_FLAGS if int(matrix[layer].sum()) == 0}
        ),
    }
    return matrix, stats


def write_outputs(
    matrix: pd.DataFrame,
    stats: dict[str, Any],
    output_path: Path,
    manifest_dir: Path,
    fetch_ts: datetime,
    summary_path: Path | None = None,
    summary_md_path: Path | None = None,
) -> dict[str, Path | str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output_path.with_suffix(".csv")
    json_path = output_path.with_suffix(".json")
    summary_path = summary_path or ROOT / "engine" / "state_policy_test_readiness_summary.json"
    summary_md_path = summary_md_path or ROOT / "engine" / "state_policy_test_readiness_summary.md"

    matrix.to_parquet(output_path, engine="pyarrow", index=False)
    matrix.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(matrix.to_dict("records"), indent=2, default=str))
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(stats, indent=2, default=str))
    summary_md_path.write_text(render_summary_md(stats))

    manifest_dir.mkdir(parents=True, exist_ok=True)
    run_stamp = utc_stamp(fetch_ts)
    manifest_path = manifest_dir / f"fetch_run_{run_stamp}_us_state_policy_test_readiness.yaml"
    sha = sha256_path(output_path)
    payload = {
        "run_utc": run_stamp,
        "pipeline": "us_state_policy_test_readiness_matrix",
        "entries": [
            {
                "publisher": "ieset_derived",
                "series_id": "us_state_policy_test_readiness_matrix",
                "source_url": "derived from landed IESET state-level panels",
                "methodology_url": "data/city_level/README.md",
                "license": "derived metadata; inherit source licenses for underlying panels",
                "fetch_utc": fetch_ts.isoformat(),
                "rows": int(len(matrix)),
                "frequency": "snapshot",
                "units": "state-level readiness flags and coverage counts",
                "currency": None,
                "start_date": None,
                "end_date": None,
                "sha256": sha,
                "parquet_path": rel(output_path),
                "extra": {
                    "artifacts": {
                        "parquet_path": rel(output_path),
                        "csv_path": rel(csv_path),
                        "json_path": rel(json_path),
                        "summary_json_path": rel(summary_path),
                        "summary_md_path": rel(summary_md_path),
                    },
                    "stats": stats,
                    "columns": list(matrix.columns),
                },
            }
        ],
    }
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return {
        "parquet_path": output_path,
        "csv_path": csv_path,
        "json_path": json_path,
        "summary_path": summary_path,
        "summary_md_path": summary_md_path,
        "manifest_path": manifest_path,
        "sha256": sha,
    }


def render_summary_md(stats: dict[str, Any]) -> str:
    lines = [
        "# State Policy Test Readiness Summary",
        "",
        f"- State rows: {stats['state_rows']}",
        f"- Countries: {stats['countries']}",
        f"- Missing optional inputs: {', '.join(stats['missing_optional_inputs']) or 'none'}",
        f"- Documented gap layers (zero coverage): {', '.join(stats['documented_gap_layers']) or 'none'}",
        "",
        "## Tiers",
        "",
    ]
    for tier, count in stats["tier_counts"].items():
        lines.append(f"- `{tier}`: {count}")
    lines.extend(["", "## Layers", ""])
    for layer, count in stats["layer_counts"].items():
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Case-Ready States", ""])
    if stats["case_ready_state_ids"]:
        for row in stats["case_ready_state_ids"]:
            lines.append(f"- `{row['ieset_state_id']}`: {row['state_name']}, {row['country_name']}")
    else:
        lines.append("- none (housing-supply/price layer is a documented gap this round)")
    lines.extend(["", "## Closest To Case-Ready", ""])
    if stats["closest_to_case_ready"]:
        for row in stats["closest_to_case_ready"]:
            lines.append(
                f"- `{row['ieset_state_id']}`: {row['state_name']} "
                f"({row['state_policy_readiness_tier']}, "
                f"binds_above_federal_years={row['mw_binds_above_federal_years']}); "
                f"missing: {row['missing_layers'] or 'none'}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for key, default in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", default=default)
    parser.add_argument("--output", default="data/derived/us_state_policy_test_readiness_matrix.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inputs = {key: path_arg(getattr(args, key.replace("-", "_"), DEFAULT_INPUTS[key])).resolve() for key in DEFAULT_INPUTS}
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    matrix, stats = build_matrix(inputs)
    artifacts = write_outputs(matrix, stats, path_arg(args.output).resolve(), path_arg(args.manifest_dir).resolve(), fetch_ts)
    print(
        "OK ieset_derived:us_state_policy_test_readiness_matrix "
        f"rows={len(matrix)} tiers={stats['tier_counts']} layers={stats['layer_counts']}"
    )
    print(f"gap_layers={stats['documented_gap_layers']}")
    print(f"artifact: {rel(artifacts['parquet_path'])} sha256={artifacts['sha256']}")
    print(f"manifest: {rel(artifacts['manifest_path'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
