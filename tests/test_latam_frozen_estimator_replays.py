"""Focused evidence checks for the frozen estimator repairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rerun_latam_capital_interaction_frozen as capital  # noqa: E402
import rerun_latam_group_time_frozen as did  # noqa: E402
import rerun_privatisation_transition_tfp_frozen as privatisation  # noqa: E402
import rerun_czech_slovak_frozen as czech_slovak  # noqa: E402
import frozen_source_lock  # noqa: E402

RAW_VINTAGES_PRESENT = all(
    (ROOT / row["path"]).is_file()
    for rows in json.loads((ROOT / "scripts" / "frozen_source_vintages.json").read_text())["cases"].values()
    for row in rows
)
needs_raw_vintages = pytest.mark.skipif(
    not RAW_VINTAGES_PRESENT,
    reason="local raw vintages are absent in this checkout",
)


@needs_raw_vintages
def test_frozen_adoption_dates_override_bad_constructed_vintage() -> None:
    hid = "latam_extra_inflation_targeting_diff_in_diff_1999_2024"
    panel, _, _, _ = did.prepare(hid)
    treatment = did.CASES[hid]["treatment"]

    def value(country: str, year: int) -> int:
        row = panel[(panel.country_iso3 == country) & (panel.year == year)]
        assert len(row) == 1
        return int(row.iloc[0][treatment])

    assert value("BRA", 1998) == 0
    assert value("BRA", 1999) == 1
    assert value("PER", 2001) == 0
    assert value("PER", 2002) == 1
    assert not panel.country_iso3.isin(["ECU", "SLV", "PAN"]).any()
    assert panel[(panel.country_iso3 == "VEN") & (panel.year > 1999)].empty


def test_conjunctive_did_rule_refutes_on_failed_primary() -> None:
    primary = {"coefficient": -0.1, "p_value": 0.8, "treated_countries_missing": []}
    verdict, _, parts = did.decision(
        "latam_extra_inflation_targeting_diff_in_diff_1999_2024",
        primary, {"passes": None}, {"passes": True},
    )
    assert verdict == "REFUTED"
    assert parts == {
        "a_negative_att_p_below_0_10": False,
        "b_dispersion_declines": None,
        "c_no_growth_penalty": True,
    }


def test_packet_check_tolerates_roundoff_but_not_substantive_drift() -> None:
    expected = {"verdict_label": "REFUTED", "estimate": {"coefficient": -0.021804688218885825,
                                                       "n_obs": 125}}
    rounded = {"verdict_label": "REFUTED", "estimate": {"coefficient": -0.021804688218886994,
                                                      "n_obs": 125}}
    assert frozen_source_lock.same_packet(expected, rounded)
    assert frozen_source_lock.same_result_card(
        "Verdict: REFUTED; ATT=-0.021804688218885825; n=125",
        "Verdict: REFUTED; ATT=-0.021804688218886994; n=125",
    )
    rounded["estimate"]["n_obs"] = 126
    assert not frozen_source_lock.same_packet(expected, rounded)
    assert not frozen_source_lock.same_result_card(
        "Verdict: REFUTED; ATT=-0.021804688218885825; n=125",
        "Verdict: SUPPORTED; ATT=-0.021804688218886994; n=125",
    )


def test_missing_registered_cohort_prevents_full_sample_graduation() -> None:
    primary = {
        "coefficient": -1.0, "p_value": 0.01,
        "treated_countries_missing": ["BRA", "PER"],
    }
    verdict, reason, parts = did.decision(
        "latam_extra_fiscal_rule_adoption_panel_1999_2024",
        primary, {"passes": False}, {"passes": True},
    )
    assert verdict == "INCONCLUSIVE_DATA_PENDING"
    assert "BRA, PER" in reason
    assert parts["a_negative_att_p_below_0_10"] is None


def test_capital_interaction_grades_all_three_frozen_conditions() -> None:
    growth = {"fdi_coefficient": 0.2, "fdi_p_value": 0.05,
              "fdi_x_wgi_coefficient": 0.03}
    volatility = {"fdi_x_wgi_coefficient": -0.1}
    verdict, components, _ = capital.decision(growth, volatility)
    assert verdict == "SUPPORTED"
    assert all(components.values())

    growth["fdi_x_wgi_coefficient"] = -0.03
    verdict, components, _ = capital.decision(growth, volatility)
    assert verdict == "REFUTED"
    assert components["b_fdi_x_wgi_growth_positive"] is False


@needs_raw_vintages
def test_privatisation_frozen_controls_eliminate_within_country_treatment_variation() -> None:
    diagnostics, _ = privatisation.build()
    assert diagnostics["verdict_label"] == "INCONCLUSIVE_DATA_PENDING"
    preflight = diagnostics["preflight"]
    assert preflight["wgi_first_observed_year"] > preflight["latest_mass_adoption_year"]
    assert preflight["within_country_mass_treatment_variation_countries"] == []
    assert preflight["ex_russia_treatment_variation_countries"] == []
    assert diagnostics["frozen_rule_components"] == {
        "mass_coefficient_positive_p_below_0_10_and_at_least_0_5pp": None,
        "mass_coefficient_larger_than_eu_candidate": None,
        "ex_russia_sign_robustness": None,
    }


@needs_raw_vintages
def test_czech_slovak_registered_long_difference_has_no_complete_endpoint_pairs() -> None:
    diagnostics, _ = czech_slovak.build()
    assert diagnostics["verdict_label"] == "INCONCLUSIVE_DATA_PENDING"
    preflight = diagnostics["preflight"]
    assert preflight["long_difference_endpoints"] == [1993, 2024]
    assert preflight["countries_with_complete_both_endpoints"] == []
    assert {"CZE", "SVK"}.issubset(set(
        preflight["generic_initial_gdp_control_wrongly_time_varying_countries"]
    ))


@needs_raw_vintages
def test_frozen_source_lock_rejects_latest_vintage_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    hid = "latam_extra_capital_account_openness_panel_1990_2024"
    original = frozen_source_lock.run_panel_fe.latest_vintage

    def drifted(publisher: str, series: str):
        if (publisher, series) == ("fred", "FEDFUNDS"):
            return ROOT / "data" / "vintages" / "fred" / "not-the-pinned-file.parquet"
        return original(publisher, series)

    monkeypatch.setattr(frozen_source_lock.run_panel_fe, "latest_vintage", drifted)
    with pytest.raises(RuntimeError, match="latest vintage drifted from pin"):
        frozen_source_lock.source_rows(hid)
