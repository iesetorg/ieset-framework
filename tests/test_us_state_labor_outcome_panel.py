from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_us_state_labor_outcome_panel as builder  # noqa: E402

OUTPUT = REPO_ROOT / "data" / "derived" / "us_state_labor_outcome_panel.parquet"

OUTCOME_COLS = [
    "unemployment_rate",
    "employment_population_ratio",
    "median_hourly_wage",
    "p10_hourly_wage",
    "qcew_total_employment",
    "qcew_avg_weekly_wage",
    "qcew_food_service_employment",
    "qcew_food_service_avg_weekly_wage",
]

# 50 states + DC fips codes.
STATES_PLUS_DC_FIPS = {
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
}


def test_output_file_exists():
    assert OUTPUT.exists(), f"expected built panel at {OUTPUT}"


def _load() -> pd.DataFrame:
    return pd.read_parquet(OUTPUT)


def test_grain_uniqueness():
    df = _load()
    assert df.duplicated(subset=["ieset_state_id", "year"]).sum() == 0


def test_state_fips_preserved():
    df = _load()
    assert "state_fips" in df.columns
    assert df["state_fips"].notna().all()
    # zero-padded two-character fips
    assert df["state_fips"].str.fullmatch(r"\d{2}").all()


def test_ieset_state_id_present():
    df = _load()
    assert "ieset_state_id" in df.columns
    assert df["ieset_state_id"].notna().all()
    assert df["ieset_state_id"].str.startswith("US-").all()


def test_all_50_states_plus_dc_present_most_recent_year():
    df = _load()
    most_recent = int(df["year"].max())
    recent = df[(df["year"] == most_recent)]
    # Among rows that actually carry outcome data in the most recent year,
    # every one of the 50 states + DC must be represented.
    have_data = recent[recent[OUTCOME_COLS].notna().any(axis=1)]
    present = set(have_data["state_fips"])
    missing = STATES_PLUS_DC_FIPS - present
    assert not missing, f"missing states in most recent year {most_recent}: {sorted(missing)}"


def test_no_all_null_outcome_columns():
    df = _load()
    for col in OUTCOME_COLS:
        assert col in df.columns, f"missing outcome column {col}"
        assert df[col].notna().any(), f"outcome column {col} is entirely null"


def test_monthly_not_mixed_into_annual():
    df = _load()
    # LAU collapse columns must record a 12-month average where present.
    for months_col in (
        "unemployment_rate_months_observed",
        "employment_population_ratio_months_observed",
    ):
        assert months_col in df.columns
        observed = df[months_col].dropna()
        assert (observed <= 12).all(), f"{months_col} exceeds 12 months"
        assert (observed > 0).all(), f"{months_col} has non-positive counts"
    # Year is an integer annual key, not a monthly period code.
    assert pd.api.types.is_integer_dtype(df["year"])


def test_build_and_manifest_roundtrip(tmp_path: Path):
    inputs = builder.resolve_inputs(builder.VINTAGE_DIR)
    panel, stats = builder.build_panel(
        inputs=inputs,
        spine_path=REPO_ROOT / "data" / "derived" / "state_universe_admin1.parquet",
    )
    assert stats["panel_rows"] == len(panel)
    assert stats["states_with_data_most_recent_year"] >= 51

    provenance = builder.build_provenance(inputs)
    assert all(len(p["sha256"]) == 64 for p in provenance)

    out = tmp_path / "panel.parquet"
    result = builder.emit(
        panel, stats, provenance, out, datetime(2026, 6, 29, tzinfo=timezone.utc)
    )
    manifest = builder.write_manifest(
        result,
        tmp_path / "manifests",
        "2026-06-29T000000Z",
        {"build_utc": "2026-06-29T00:00:00+00:00", "inputs": provenance},
    )
    assert out.exists()
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "us_state_labor_outcome_panel"
    assert payload["methodology"]["inputs"]
