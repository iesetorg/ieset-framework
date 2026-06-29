from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_us_state_acs_saipe_incidence_panel as builder  # noqa: E402

OUTPUT = REPO_ROOT / "data" / "derived" / "us_state_acs_saipe_incidence_panel.parquet"
MANIFEST_DIR = REPO_ROOT / "data" / "manifests"

# 50 states + DC fips codes.
STATES_PLUS_DC_FIPS = {
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
}

# Every output column must trace to an input vintage (raw or a documented
# derivation/coverage flag). No column outside this set may appear -- that
# would signal a fabricated dimension.
ALLOWED_COLUMNS = {
    # spine-provided identity columns
    "ieset_state_id",
    "state_fips",
    "state_abbr",
    "state_name",
    "is_state_equivalent",
    "year",
    # SAIPE
    "saipe_poverty_rate_all_ages",
    "saipe_median_household_income",
    "saipe_obs",
    # ACS state profile
    "acs_median_household_income",
    "acs_total_population",
    "acs_profile_obs",
    # ACS education attainment (B15003)
    "acs_bachelors_or_higher_share",
    "acs_population_25_plus",
    "acs_education_obs",
    # ACS school enrollment (B14001)
    "acs_school_enrolled_share",
    "acs_enrollment_universe_3_plus",
    "acs_enrollment_obs",
    # derived completeness counter
    "incidence_measures_present",
}


def _load() -> pd.DataFrame:
    return pd.read_parquet(OUTPUT)


def _latest_manifest() -> dict:
    matches = sorted(
        glob.glob(str(MANIFEST_DIR / "fetch_run_*_us_state_acs_saipe_incidence.yaml"))
    )
    assert matches, "expected an incidence manifest under data/manifests/"
    return yaml.safe_load(Path(matches[-1]).read_text())


def test_output_file_exists():
    assert OUTPUT.exists(), f"expected built panel at {OUTPUT}"


def test_grain_uniqueness():
    df = _load()
    assert df.duplicated(subset=["ieset_state_id", "year"]).sum() == 0


def test_state_fips_preserved():
    df = _load()
    assert "state_fips" in df.columns
    assert df["state_fips"].notna().all()
    assert df["state_fips"].str.fullmatch(r"\d{2}").all()


def test_ieset_state_id_present():
    df = _load()
    assert "ieset_state_id" in df.columns
    assert df["ieset_state_id"].notna().all()
    assert df["ieset_state_id"].str.fullmatch(r"US-[A-Z]{2}").all()


def test_50_states_plus_dc_present_recent_year():
    df = _load()
    recent = int(df["year"].max())
    fips_recent = set(df.loc[df["year"] == recent, "state_fips"])
    missing = STATES_PLUS_DC_FIPS - fips_recent
    assert not missing, f"missing 50 states + DC fips in {recent}: {sorted(missing)}"


def test_poverty_rate_within_plausible_range():
    df = _load()
    pov = df["saipe_poverty_rate_all_ages"].dropna()
    assert len(pov) > 0
    # SAIPE all-ages poverty rate is a percentage; US states sit roughly 5-25%.
    assert pov.between(2.0, 40.0).all()


def test_median_income_within_plausible_range():
    df = _load()
    for col in ["saipe_median_household_income", "acs_median_household_income"]:
        vals = df[col].dropna()
        assert len(vals) > 0
        # Plausible US state median household income window (USD).
        assert vals.between(15_000, 200_000).all(), f"{col} out of range"


def test_derived_shares_within_unit_interval():
    df = _load()
    for col in ["acs_bachelors_or_higher_share", "acs_school_enrolled_share"]:
        vals = df[col].dropna()
        assert len(vals) > 0
        assert vals.between(0.0, 100.0).all(), f"{col} not a valid percent"


def test_no_fabricated_columns():
    df = _load()
    extra = set(df.columns) - ALLOWED_COLUMNS
    assert not extra, f"unexpected (potentially fabricated) columns: {sorted(extra)}"


def test_coverage_flags_are_binary():
    df = _load()
    for flag in ["saipe_obs", "acs_profile_obs", "acs_education_obs", "acs_enrollment_obs"]:
        assert set(df[flag].unique()).issubset({0, 1}), f"{flag} not binary"


def test_documented_gaps_recorded_in_manifest():
    manifest = _latest_manifest()
    gaps = manifest.get("documented_gaps")
    assert gaps, "manifest must record documented_gaps"
    dims = {g["dimension"] for g in gaps}
    # Canonical incidence dimensions known to be absent from the vintages.
    for expected in [
        "rent_burden_cost_burdened_share",
        "homeownership_tenure_rate",
        "median_gross_rent",
        "spm_child_poverty_rate_state_grain",
    ]:
        assert expected in dims, f"missing documented gap: {expected}"
    for g in gaps:
        assert g.get("reason"), f"gap {g.get('dimension')} lacks a reason"


def test_manifest_pins_inputs_with_sha():
    manifest = _latest_manifest()
    inputs = manifest["methodology"]["inputs"]
    assert len(inputs) == 4
    for item in inputs:
        assert item["path"]
        assert item["sha256"] and len(item["sha256"]) == 64
        assert item["rows"] > 0
        assert item["columns"]


def test_builder_rebuild_matches(tmp_path):
    """Rebuild deterministically and confirm grain + row count are stable."""
    out = tmp_path / "panel.parquet"
    rc = builder.main(
        [
            "--output",
            str(out),
            "--manifest-dir",
            str(tmp_path),
            "--fetch-utc",
            "2026-01-01T000000Z",
        ]
    )
    assert rc == 0
    rebuilt = pd.read_parquet(out)
    on_disk = _load()
    assert len(rebuilt) == len(on_disk)
    assert rebuilt.duplicated(subset=["ieset_state_id", "year"]).sum() == 0
    assert list(rebuilt.columns) == list(on_disk.columns)
