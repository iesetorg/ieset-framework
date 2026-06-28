#!/usr/bin/env python3
"""Build top-1000 city readiness matrix from landed city-level panels."""
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
    "city_spine": "data/derived/city_universe_top1000.parquet",
    "zillow_rent": "data/derived/us_city_rent_panel.parquet",
    "census_permits": "data/derived/us_city_permits_panel.parquet",
    "nyc_quality": "data/derived/us_city_rent_control_quality_leakage_panel.parquet",
    "datasf_quality": "data/derived/us_sf_rent_control_quality_leakage_panel.parquet",
    "nyc_regulation_proxy": "data/derived/nyc_rent_regulation_tax_benefit_panel.parquet",
    "acs_incidence": "data/derived/us_acs_place_housing_incidence_panel.parquet",
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


def ensure_city_id(frame: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if "ieset_city_id" not in frame.columns:
        raise ValueError(f"{source_name} is missing ieset_city_id")
    return frame[frame["ieset_city_id"].notna()].copy()


def merge_agg(base: pd.DataFrame, agg: pd.DataFrame, fill_values: dict[str, Any]) -> pd.DataFrame:
    base = base.drop(columns=[column for column in fill_values if column in base.columns])
    out = base.merge(agg, on="ieset_city_id", how="left")
    for column, value in fill_values.items():
        if column in out.columns:
            if value is not None:
                out[column] = out[column].fillna(value)
    return out


def add_zillow(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "zori_rows": 0,
        "zori_regions": 0,
        "zori_months": 0,
        "zori_start_month": None,
        "zori_end_month": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "zillow_rent")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            zori_rows=("zori_usd", "size"),
            zori_regions=("zillow_region_id", "nunique"),
            zori_months=("month_end", "nunique"),
            zori_start_month=("month_end", "min"),
            zori_end_month=("month_end", "max"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_permits(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "census_permit_rows": 0,
        "census_permit_years": 0,
        "census_permit_start_year": None,
        "census_permit_end_year": None,
        "census_permit_total_units": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "census_permits")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            census_permit_rows=("year", "size"),
            census_permit_years=("year", "nunique"),
            census_permit_start_year=("year", "min"),
            census_permit_end_year=("year", "max"),
            census_permit_total_units=("total_units", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_local_quality(base: pd.DataFrame, frame: pd.DataFrame | None, prefix: str, supply_key: str | None) -> pd.DataFrame:
    columns = {
        f"{prefix}_rows": 0,
        f"{prefix}_datasets": 0,
        f"{prefix}_start_year": None,
        f"{prefix}_end_year": None,
        f"{prefix}_value_sum": 0,
        f"{prefix}_supply_rows": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, prefix)
    supply = frame["source_dataset_key"].eq(supply_key) if supply_key else pd.Series(False, index=frame.index)
    frame = frame.assign(_supply_row=supply.astype(int))
    value_col = "value" if "value" in frame.columns else "value_count"
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            **{
                f"{prefix}_rows": ("year", "size"),
                f"{prefix}_datasets": ("source_dataset_key", "nunique"),
                f"{prefix}_start_year": ("year", "min"),
                f"{prefix}_end_year": ("year", "max"),
                f"{prefix}_value_sum": (value_col, "sum"),
                f"{prefix}_supply_rows": ("_supply_row", "sum"),
            }
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_nyc_regulation(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "nyc_regulation_proxy_rows": 0,
        "nyc_regulation_proxy_families": 0,
        "nyc_regulation_proxy_start_year": None,
        "nyc_regulation_proxy_end_year": None,
        "nyc_regulation_proxy_value_count": 0,
        "nyc_regulation_proxy_units": 0,
        "nyc_regulation_proxy_restricted_units": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "nyc_regulation_proxy")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            nyc_regulation_proxy_rows=("year", "size"),
            nyc_regulation_proxy_families=("benefit_family", "nunique"),
            nyc_regulation_proxy_start_year=("year", "min"),
            nyc_regulation_proxy_end_year=("year", "max"),
            nyc_regulation_proxy_value_count=("value_count", "sum"),
            nyc_regulation_proxy_units=("unit_count", "sum"),
            nyc_regulation_proxy_restricted_units=("restricted_unit_count", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_acs(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "acs_incidence_rows": 0,
        "acs_incidence_years": 0,
        "acs_incidence_start_year": None,
        "acs_incidence_end_year": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "acs_incidence")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            acs_incidence_rows=("acs_year", "size"),
            acs_incidence_years=("acs_year", "nunique"),
            acs_incidence_start_year=("acs_year", "min"),
            acs_incidence_end_year=("acs_year", "max"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def assign_layers(matrix: pd.DataFrame) -> pd.DataFrame:
    out = matrix.copy()
    out["first_order_rent_layer"] = out["zori_rows"].gt(0)
    out["supply_response_layer"] = (
        out["census_permit_rows"].gt(0)
        | out["nyc_quality_supply_rows"].gt(0)
        | out["datasf_quality_supply_rows"].gt(0)
    )
    out["quality_or_leakage_layer"] = out["nyc_quality_rows"].gt(0) | out["datasf_quality_rows"].gt(0)
    out["regulated_stock_or_rent_board_layer"] = (
        out["nyc_regulation_proxy_rows"].gt(0)
        | out["datasf_quality_rows"].gt(0)
        & out["ieset_city_id"].eq("ghsl_ucdb_r2024a:1461")
    )
    out["distributional_incidence_layer"] = out["acs_incidence_rows"].gt(0)
    layer_cols = [
        "first_order_rent_layer",
        "supply_response_layer",
        "quality_or_leakage_layer",
        "regulated_stock_or_rent_board_layer",
        "distributional_incidence_layer",
    ]
    out["rent_control_core_layer_count"] = out[layer_cols].sum(axis=1).astype(int)

    def tier(row: pd.Series) -> str:
        if (
            row["first_order_rent_layer"]
            and row["supply_response_layer"]
            and row["quality_or_leakage_layer"]
            and row["regulated_stock_or_rent_board_layer"]
        ):
            return "case_ready_local_panel"
        if row["first_order_rent_layer"] and row["supply_response_layer"] and row["quality_or_leakage_layer"]:
            return "outcomes_ready_needs_regulated_stock"
        if row["first_order_rent_layer"] and row["supply_response_layer"]:
            return "rent_supply_ready"
        if row["first_order_rent_layer"]:
            return "rent_only"
        if row["supply_response_layer"] or row["quality_or_leakage_layer"] or row["regulated_stock_or_rent_board_layer"]:
            return "partial_local_outcome"
        return "spine_only"

    out["rent_control_readiness_tier"] = out.apply(tier, axis=1)
    return out


def build_matrix(inputs: dict[str, Path]) -> tuple[pd.DataFrame, dict[str, Any]]:
    spine_path = inputs["city_spine"]
    if not spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {spine_path}")
    spine = pd.read_parquet(spine_path) if spine_path.suffix == ".parquet" else pd.read_csv(spine_path)
    base_cols = [
        "ieset_city_id",
        "city_rank_2025",
        "city_name",
        "country_name",
        "country_iso3",
        "population_2025",
        "area_km2_2025",
        "density_per_km2_2025",
    ]
    matrix = spine[base_cols].copy()
    matrix = add_zillow(matrix, read_optional(inputs["zillow_rent"]))
    matrix = add_permits(matrix, read_optional(inputs["census_permits"]))
    matrix = add_local_quality(matrix, read_optional(inputs["nyc_quality"]), "nyc_quality", "dob_permit_issuance")
    matrix = add_local_quality(matrix, read_optional(inputs["datasf_quality"]), "datasf_quality", "building_permit")
    matrix = add_nyc_regulation(matrix, read_optional(inputs["nyc_regulation_proxy"]))
    matrix = add_acs(matrix, read_optional(inputs["acs_incidence"]))
    matrix = assign_layers(matrix)
    matrix = matrix.sort_values(
        ["rent_control_core_layer_count", "population_2025", "city_rank_2025"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    stats = {
        "city_rows": int(len(matrix)),
        "countries": int(matrix["country_name"].nunique()),
        "tier_counts": {str(k): int(v) for k, v in matrix["rent_control_readiness_tier"].value_counts().to_dict().items()},
        "layer_counts": {
            "first_order_rent_layer": int(matrix["first_order_rent_layer"].sum()),
            "supply_response_layer": int(matrix["supply_response_layer"].sum()),
            "quality_or_leakage_layer": int(matrix["quality_or_leakage_layer"].sum()),
            "regulated_stock_or_rent_board_layer": int(matrix["regulated_stock_or_rent_board_layer"].sum()),
            "distributional_incidence_layer": int(matrix["distributional_incidence_layer"].sum()),
        },
        "ready_city_ids": matrix.loc[
            matrix["rent_control_readiness_tier"].eq("case_ready_local_panel"),
            ["ieset_city_id", "city_name", "country_name"],
        ].to_dict("records"),
        "input_paths": {key: rel(path) for key, path in inputs.items()},
        "missing_optional_inputs": [key for key, path in inputs.items() if key != "city_spine" and not path.exists()],
    }
    return matrix, stats


def write_outputs(matrix: pd.DataFrame, stats: dict[str, Any], output_path: Path, manifest_dir: Path, fetch_ts: datetime) -> dict[str, Path | str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output_path.with_suffix(".csv")
    json_path = output_path.with_suffix(".json")
    summary_path = ROOT / "engine" / "city_policy_test_readiness_summary.json"
    summary_md_path = ROOT / "engine" / "city_policy_test_readiness_summary.md"

    matrix.to_parquet(output_path, engine="pyarrow", index=False)
    matrix.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(matrix.to_dict("records"), indent=2))
    summary_path.write_text(json.dumps(stats, indent=2))
    summary_md_path.write_text(render_summary_md(stats))

    manifest_dir.mkdir(parents=True, exist_ok=True)
    run_stamp = utc_stamp(fetch_ts)
    manifest_path = manifest_dir / f"fetch_run_{run_stamp}_city_policy_test_readiness.yaml"
    sha = sha256_path(output_path)
    payload = {
        "run_utc": run_stamp,
        "pipeline": "city_policy_test_readiness_matrix",
        "entries": [
            {
                "publisher": "ieset_derived",
                "series_id": "city_policy_test_readiness_matrix",
                "source_url": "derived from landed IESET city-level panels",
                "methodology_url": "data/city_level/README.md",
                "license": "derived metadata; inherit source licenses for underlying panels",
                "fetch_utc": fetch_ts.isoformat(),
                "rows": int(len(matrix)),
                "frequency": "snapshot",
                "units": "city-level readiness flags and coverage counts",
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
        "# City Policy Test Readiness Summary",
        "",
        f"- City rows: {stats['city_rows']}",
        f"- Countries: {stats['countries']}",
        f"- Missing optional inputs: {', '.join(stats['missing_optional_inputs']) or 'none'}",
        "",
        "## Tiers",
        "",
    ]
    for tier, count in stats["tier_counts"].items():
        lines.append(f"- `{tier}`: {count}")
    lines.extend(["", "## Layers", ""])
    for layer, count in stats["layer_counts"].items():
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Case-Ready Cities", ""])
    if stats["ready_city_ids"]:
        for row in stats["ready_city_ids"]:
            lines.append(f"- `{row['ieset_city_id']}`: {row['city_name']}, {row['country_name']}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for key, default in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", default=default)
    parser.add_argument("--output", default="data/derived/city_policy_test_readiness_matrix.parquet")
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
        "OK ieset_derived:city_policy_test_readiness_matrix "
        f"rows={len(matrix)} tiers={stats['tier_counts']} layers={stats['layer_counts']}"
    )
    print(f"artifact: {rel(artifacts['parquet_path'])} sha256={artifacts['sha256']}")
    print(f"manifest: {rel(artifacts['manifest_path'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
