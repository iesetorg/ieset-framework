from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_us_state_policy_test_readiness_matrix as readiness_builder  # noqa: E402


ALLOWED_TIERS = set(readiness_builder.TIERS)
ALLOWED_LAYERS = set(readiness_builder.LAYER_FLAGS)


def _make_inputs(tmp_path: Path) -> dict[str, Path]:
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_state_id": "US-CA",
                "country_iso3": "USA",
                "country_name": "United States",
                "state_name": "California",
                "state_abbr": "CA",
                "state_fips": "06",
                "iso_3166_2": "US-CA",
                "admin1_kind": "state",
                "is_state_equivalent": True,
            },
            {
                "ieset_state_id": "US-NY",
                "country_iso3": "USA",
                "country_name": "United States",
                "state_name": "New York",
                "state_abbr": "NY",
                "state_fips": "36",
                "iso_3166_2": "US-NY",
                "admin1_kind": "state",
                "is_state_equivalent": True,
            },
            {
                "ieset_state_id": "US-AL",
                "country_iso3": "USA",
                "country_name": "United States",
                "state_name": "Alabama",
                "state_abbr": "AL",
                "state_fips": "01",
                "iso_3166_2": "US-AL",
                "admin1_kind": "state",
                "is_state_equivalent": True,
            },
            {
                "ieset_state_id": "US-GU",
                "country_iso3": "USA",
                "country_name": "United States",
                "state_name": "Guam",
                "state_abbr": "GU",
                "state_fips": "66",
                "iso_3166_2": "US-GU",
                "admin1_kind": "territory",
                "is_state_equivalent": True,
            },
        ]
    ).to_parquet(spine, index=False)

    # CA: treatment + outcome + housing => case_ready
    # NY: treatment + outcome => treatment_plus_outcome
    # AL: treatment only (federal floor, no outcome rows)
    # GU: outcome only (no treatment rows)
    mw = tmp_path / "mw.parquet"
    pd.DataFrame(
        [
            {
                "ieset_state_id": "US-CA",
                "year": 2018,
                "binds_above_federal": True,
                "is_first_bind_event": True,
                "event_type": "first_bind",
            },
            {
                "ieset_state_id": "US-CA",
                "year": 2019,
                "binds_above_federal": True,
                "is_first_bind_event": False,
                "event_type": "increase",
            },
            {
                "ieset_state_id": "US-NY",
                "year": 2017,
                "binds_above_federal": True,
                "is_first_bind_event": True,
                "event_type": "first_bind",
            },
            {
                "ieset_state_id": "US-AL",
                "year": 2010,
                "binds_above_federal": False,
                "is_first_bind_event": False,
                "event_type": "no_change",
            },
        ]
    ).to_parquet(mw, index=False)

    labor = tmp_path / "labor.parquet"
    pd.DataFrame(
        [
            {
                "ieset_state_id": "US-CA",
                "year": 2020,
                "unemployment_rate": 5.5,
                "employment_population_ratio": 60.0,
                "median_hourly_wage": 22.0,
                "qcew_total_employment": 100,
            },
            {
                "ieset_state_id": "US-NY",
                "year": 2020,
                "unemployment_rate": 6.0,
                "employment_population_ratio": 58.0,
                "median_hourly_wage": 24.0,
                "qcew_total_employment": 200,
            },
            {
                "ieset_state_id": "US-GU",
                "year": 2020,
                "unemployment_rate": 7.0,
                "employment_population_ratio": 55.0,
                "median_hourly_wage": None,
                "qcew_total_employment": None,
            },
        ]
    ).to_parquet(labor, index=False)

    housing = tmp_path / "housing.parquet"
    pd.DataFrame(
        [
            {
                "ieset_state_id": "US-CA",
                "year": 2021,
                "bps_total_permits": 1000,
                "fhfa_hpi": 320.5,
            }
        ]
    ).to_parquet(housing, index=False)

    return {
        "state_spine": spine,
        "minimum_wage_treatment": mw,
        "labor_outcome": labor,
        "housing_supply_price": housing,
        "fiscal": tmp_path / "missing_fiscal.parquet",
        "distributional_incidence": tmp_path / "missing_incidence.parquet",
    }


def test_matrix_one_row_per_spine_state_with_consistent_layers(tmp_path: Path):
    inputs = _make_inputs(tmp_path)
    spine = pd.read_parquet(inputs["state_spine"])
    matrix, stats = readiness_builder.build_matrix(inputs)

    # one row per state in the spine, no duplicates, no extras
    assert len(matrix) == len(spine)
    assert set(matrix["ieset_state_id"]) == set(spine["ieset_state_id"])
    assert matrix["ieset_state_id"].is_unique

    # tiers and layer values come from the allowed sets
    assert set(matrix["state_policy_readiness_tier"]).issubset(ALLOWED_TIERS)
    for layer in ALLOWED_LAYERS:
        assert matrix[layer].dtype == bool

    # present-layer flags consistent with the underlying panels
    mw_states = set(pd.read_parquet(inputs["minimum_wage_treatment"])["ieset_state_id"])
    labor_states = set(pd.read_parquet(inputs["labor_outcome"])["ieset_state_id"])
    housing_states = set(pd.read_parquet(inputs["housing_supply_price"])["ieset_state_id"])
    flagged_mw = set(matrix.loc[matrix["minimum_wage_treatment_layer"], "ieset_state_id"])
    flagged_labor = set(matrix.loc[matrix["labor_outcome_layer"], "ieset_state_id"])
    flagged_housing = set(matrix.loc[matrix["housing_supply_price_layer"], "ieset_state_id"])
    assert flagged_mw == mw_states
    assert flagged_labor == labor_states
    assert flagged_housing == housing_states

    # missing layers explicitly listed and consistent with flags
    for _, row in matrix.iterrows():
        listed_missing = set(filter(None, row["missing_layers"].split(";")))
        actual_missing = {layer for layer in ALLOWED_LAYERS if not bool(row[layer])}
        assert listed_missing == actual_missing

    # per-state tier checks
    ca = matrix[matrix["ieset_state_id"].eq("US-CA")].iloc[0]
    assert ca["minimum_wage_treatment_layer"]
    assert ca["labor_outcome_layer"]
    assert ca["housing_supply_price_layer"]
    assert ca["mw_binds_above_federal_years"] == 2
    assert ca["mw_first_bind_events"] == 1
    assert ca["mw_increase_events"] == 1
    assert ca["mw_first_bind_year"] == 2018
    assert ca["labor_qcew_obs"] == 1
    assert ca["housing_permit_obs"] == 1
    assert ca["housing_hpi_obs"] == 1
    assert ca["state_policy_readiness_tier"] == "case_ready_state_panel"
    assert ca["state_policy_core_layer_count"] == 3

    ny = matrix[matrix["ieset_state_id"].eq("US-NY")].iloc[0]
    assert ny["minimum_wage_treatment_layer"]
    assert ny["labor_outcome_layer"]
    assert not ny["housing_supply_price_layer"]
    assert ny["state_policy_readiness_tier"] == "treatment_plus_outcome"

    al = matrix[matrix["ieset_state_id"].eq("US-AL")].iloc[0]
    assert al["minimum_wage_treatment_layer"]
    assert not al["labor_outcome_layer"]
    assert al["mw_binds_above_federal_years"] == 0
    assert al["state_policy_readiness_tier"] == "treatment_only"

    gu = matrix[matrix["ieset_state_id"].eq("US-GU")].iloc[0]
    assert not gu["minimum_wage_treatment_layer"]
    assert gu["labor_outcome_layer"]
    assert gu["state_policy_readiness_tier"] == "outcome_only"

    # summary counts reconcile with the matrix
    assert stats["state_rows"] == len(matrix)
    for tier, count in stats["tier_counts"].items():
        assert count == int((matrix["state_policy_readiness_tier"] == tier).sum())
    for layer, count in stats["layer_counts"].items():
        assert count == int(matrix[layer].sum())
    assert stats["tier_counts"]["case_ready_state_panel"] == 1
    assert stats["tier_counts"]["treatment_plus_outcome"] == 1
    assert stats["tier_counts"]["treatment_only"] == 1
    assert stats["tier_counts"]["outcome_only"] == 1
    assert stats["layer_counts"]["minimum_wage_treatment_layer"] == 3
    assert stats["layer_counts"]["labor_outcome_layer"] == 3
    assert stats["layer_counts"]["housing_supply_price_layer"] == 1
    assert set(stats["missing_optional_inputs"]) == {"fiscal", "distributional_incidence"}
    assert "fiscal_layer" in stats["documented_gap_layers"]
    assert "distributional_incidence_layer" in stats["documented_gap_layers"]

    # case-ready and closest reconcile
    assert [r["ieset_state_id"] for r in stats["case_ready_state_ids"]] == ["US-CA"]
    closest_ids = {r["ieset_state_id"] for r in stats["closest_to_case_ready"]}
    assert {"US-CA", "US-NY"}.issubset(closest_ids)


def test_write_outputs_emits_all_artifacts(tmp_path: Path):
    inputs = _make_inputs(tmp_path)
    matrix, stats = readiness_builder.build_matrix(inputs)

    output = tmp_path / "readiness.parquet"
    artifacts = readiness_builder.write_outputs(
        matrix,
        stats,
        output,
        tmp_path / "manifests",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
        tmp_path / "summary.json",
        tmp_path / "summary.md",
    )
    assert output.exists()
    assert output.with_suffix(".csv").exists()
    assert output.with_suffix(".json").exists()
    assert Path(artifacts["summary_path"]).exists()
    assert Path(artifacts["summary_md_path"]).exists()

    manifest = yaml.safe_load(Path(artifacts["manifest_path"]).read_text())
    assert manifest["entries"][0]["series_id"] == "us_state_policy_test_readiness_matrix"
    assert manifest["entries"][0]["rows"] == len(matrix)
    assert Path(artifacts["manifest_path"]).name.endswith("_us_state_policy_test_readiness.yaml")

    # round-trip the parquet keeps one row per state
    reread = pd.read_parquet(output)
    assert len(reread) == len(matrix)
