"""Synthetic checks for the prospectively frozen tourism response runner."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts/run_wdi_tourism_response_six_outcome_2026.py"
SPEC = importlib.util.spec_from_file_location("wdi_tourism_response_six_outcome", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def synthetic_panel(beta: float) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(20631)
    rows = []
    for index in range(40):
        country = f"C{index:02d}"
        country_effect = rng.normal(scale=0.3)
        for year in range(2007, 2017):
            x = float(rng.uniform(-0.24, 0.24))
            baseline = float(50 + rng.normal(scale=2))
            log_gdp_pc = float(9 + rng.normal(scale=0.5))
            response = (beta * x + country_effect + 0.03 * (year - 2011)
                        + 0.04 * baseline - 0.05 * log_gdp_pc + rng.normal(scale=0.015))
            rows.append({"country": country, "year": year, "x": x,
                         "baseline": baseline, "log_gdp_pc": log_gdp_pc,
                         "response": response})
    frame = pd.DataFrame(rows)
    material = frame[frame.x.abs() >= runner.MATERIAL_LOG_CHANGE]
    sample = {"valid_rows": len(frame), "valid_countries": frame.country.nunique(),
              "material_exposure_rows": len(material),
              "material_exposure_countries": material.country.nunique()}
    return frame, sample


def test_synthetic_positive_and_negative_signs_clear_frozen_gates():
    positive, positive_sample = synthetic_panel(2.0)
    negative, negative_sample = synthetic_panel(-2.0)
    supported, _, supported_result = runner.fit_case("employment", positive, positive_sample)
    refuted, _, refuted_result = runner.fit_case("employment", negative, negative_sample)
    assert supported == "SUPPORTED"
    assert refuted == "REFUTED"
    assert supported_result["p_value_two_sided"] <= runner.P_MAX
    assert refuted_result["p_value_two_sided"] <= runner.P_MAX
    assert positive_sample["top_country_residualized_exposure_share"] <= runner.MAX_COUNTRY_RESIDUAL_SHARE


def test_material_floor_prevents_directional_verdict():
    panel, sample = synthetic_panel(2.0)
    sample["material_exposure_rows"] = runner.MIN_MATERIAL_ROWS - 1
    verdict, _, result = runner.fit_case("employment", panel, sample)
    assert verdict == "INCONCLUSIVE"
    assert result["gates_failed"] == ["material_exposure_floor"]


def test_business_density_uses_each_year_population():
    country, year = "USA", 2010
    data = {
        "registrations": {(country, year): (100.0, None), (country, year + 1): (150.0, "A")},
        "population": {(country, year): (1_000_000.0, None),
                       (country, year + 1): (2_000_000.0, None)},
    }
    baseline, followup = runner.baseline_followup("registrations", country, year, data)
    assert np.isclose(baseline, np.log1p(100.0))
    assert np.isclose(followup, np.log1p(75.0))
    data["population"][(country, year + 1)] = (0.0, None)
    assert runner.baseline_followup("registrations", country, year, data) is None
