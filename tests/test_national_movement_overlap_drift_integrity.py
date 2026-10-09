"""Umbrella narratives and dated policy phases must not multiply drift steps."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compute_country_drift", ROOT / "scripts" / "compute_country_drift.py"
)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)
MOVEMENTS = {m["movement_id"]: m for m in DRIFT.load_movements()}


def trajectory(ids: list[str], country: str, axis: str, year: int) -> float:
    result = DRIFT.build_drift([MOVEMENTS[id] for id in ids])
    return result["countries"][country]["axes"][axis][result["years"].index(year)]


def test_narrative_umbrellas_retain_policies_without_double_counting() -> None:
    for movement_id in (
        "us_obama_ara_2009_recovery",
        "thatcherism",
        "vietnam_doi_moi_1986",
        "canada_mulroney_chretien_fiscal_consolidation_1984_2006",
    ):
        movement = MOVEMENTS[movement_id]
        assert movement["policies"]
        assert movement["axes_summary"] == []


def test_us_decisions_are_coded_once_in_their_enactment_year() -> None:
    obama = ["us_obama_ara_2009_recovery", "us_obama_first_term_2009_2013"]
    assert trajectory(obama, "USA", "fiscal.spending_level", 2009) == 3.0
    assert trajectory(obama, "USA", "regulatory.financial_deregulation", 2009) == 0.0
    assert trajectory(obama, "USA", "regulatory.financial_deregulation", 2010) == 3.0
    assert trajectory(obama, "USA", "regulatory.immigration_openness", 2011) == 0.0
    assert trajectory(obama, "USA", "regulatory.immigration_openness", 2012) == 1.0

    trump = [
        "us_trump_first_term_broad_2017_2021",
        "us_trump_tcja_2017",
        "us_trump_tariffs_2018_2019",
    ]
    assert trajectory(trump, "USA", "fiscal.tax_corporate", 2017) == 0.0
    assert trajectory(trump, "USA", "fiscal.tax_corporate", 2018) == -3.0
    assert trajectory(trump, "USA", "regulatory.trade_openness", 2017) == 0.0
    assert trajectory(trump, "USA", "regulatory.trade_openness", 2018) == -3.0
    assert trajectory(trump, "USA", "regulatory.financial_deregulation", 2018) == -2.0
    assert trajectory(trump, "USA", "fiscal.spending_level", 2019) == 0.0
    assert trajectory(trump, "USA", "fiscal.spending_level", 2020) == 3.0
    broad_axes = {a["axis"] for a in MOVEMENTS[trump[0]]["axes_summary"]}
    narrow_axes = {
        a["axis"] for movement_id in trump[1:]
        for a in MOVEMENTS[movement_id]["axes_summary"]
    }
    assert broad_axes.isdisjoint(narrow_axes)


def test_thatcher_terms_place_big_bang_and_tax_cuts_when_enacted() -> None:
    ids = [
        "thatcherism",
        "uk_thatcher_first_term_1979_1983",
        "uk_thatcher_second_term_1983_1987",
        "uk_thatcher_third_term_1987_1990",
    ]
    assert trajectory(ids, "GBR", "regulatory.financial_deregulation", 1985) == -3.0
    assert trajectory(ids, "GBR", "regulatory.financial_deregulation", 1986) == -6.0
    assert trajectory(ids, "GBR", "fiscal.tax_progressivity", 1987) == -3.0
    assert trajectory(ids, "GBR", "fiscal.tax_progressivity", 1988) == -6.0


def test_doi_moi_phases_do_not_credit_later_treaties_to_1986() -> None:
    ids = [
        "vietnam_doi_moi_1986",
        "vietnam_linh_doi_moi_implementation_1986_1991",
        "vietnam_khai_manh_doi_moi_deepening_1997_2006",
        "vietnam_dung_pm_2006_2016",
        "vietnam_phuc_pm_2016_2021",
        "vietnam_trong_era_2011_2024",
        "vietnam_to_lam_2024_present",
    ]
    assert trajectory(ids, "VNM", "institutional.property_rights", 1987) == 3.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 1988) == 3.0
    assert trajectory(ids, "VNM", "regulatory.sectoral_licensing", 1990) == -3.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 1986) == 0.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2000) == 0.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2001) == 3.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2007) == 6.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2018) == 6.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2019) == 9.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2025) == 9.0


def test_vietnam_overlapping_leaders_do_not_recredit_shared_decisions() -> None:
    ids = [
        "vietnam_phuc_pm_2016_2021",
        "vietnam_trong_era_2011_2024",
        "vietnam_to_lam_2024_present",
    ]
    assert trajectory(ids, "VNM", "institutional.rule_of_law", 2016) == 2.0
    assert trajectory(ids, "VNM", "institutional.rule_of_law", 2021) == 2.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 2018) == 0.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 2019) == 1.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 2023) == 1.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 2024) == 3.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 2025) == 5.0
    assert trajectory(ids, "VNM", "fiscal.sectoral_subsidy", 2023) == 0.0
    assert trajectory(ids, "VNM", "fiscal.sectoral_subsidy", 2024) == 3.0


def test_canadian_trade_tax_and_program_review_keep_distinct_dates() -> None:
    ids = [
        "canada_mulroney_chretien_fiscal_consolidation_1984_2006",
        "canada_mulroney_pc_first_1984_1988",
        "canada_mulroney_pc_second_1988_1993",
        "canada_chretien_liberal_first_1993_1997",
    ]
    assert trajectory(ids, "CAN", "regulatory.trade_openness", 1987) == 0.0
    assert trajectory(ids, "CAN", "regulatory.trade_openness", 1988) == 3.0
    assert trajectory(ids, "CAN", "regulatory.trade_openness", 1994) == 5.0
    assert trajectory(ids, "CAN", "monetary.central_bank_independence", 1990) == 0.0
    assert trajectory(ids, "CAN", "monetary.central_bank_independence", 1991) == 2.0
    assert trajectory(ids, "CAN", "fiscal.spending_level", 1994) == 0.0
    assert trajectory(ids, "CAN", "fiscal.spending_level", 1995) == -3.0
    assert trajectory(ids, "CAN", "fiscal.transfer_expansion", 1996) == -2.0


def test_correa_umbrella_does_not_repeat_term_level_transfer_and_licensing() -> None:
    ids = [
        "ecuador_correa_21st_century_socialism_2007_2017",
        "ecuador_correa_alianza_pais_i_2007_2013",
        "ecuador_correa_alianza_pais_ii_2013_2017",
    ]
    assert trajectory(ids, "ECU", "fiscal.transfer_expansion", 2007) == 2.0
    assert trajectory(ids, "ECU", "fiscal.transfer_expansion", 2017) == 2.0
    assert trajectory(ids, "ECU", "regulatory.sectoral_licensing", 2007) == 2.0
    assert trajectory(ids, "ECU", "regulatory.sectoral_licensing", 2013) == 3.0


def test_chretien_second_term_does_not_score_unmeasured_tax_incidence() -> None:
    ids = ["canada_chretien_liberal_second_third_1997_2003"]
    assert trajectory(ids, "CAN", "fiscal.tax_progressivity", 2000) == 0.0
    assert trajectory(ids, "CAN", "institutional.rule_of_law", 2000) == 2.0
    assert trajectory(ids, "CAN", "regulatory.environmental_stringency", 2001) == 0.0
    assert trajectory(ids, "CAN", "regulatory.environmental_stringency", 2002) == 1.0


def test_kok_ii_does_not_recredit_flexwet_or_the_existing_zalm_rule() -> None:
    ids = [
        "netherlands_kok_purple_1994_2002",
        "netherlands_kok_ii_purple_1998_2002",
    ]
    assert trajectory(ids, "NLD", "regulatory.labour_market_flexibility", 1998) == 0.0
    assert trajectory(ids, "NLD", "regulatory.labour_market_flexibility", 1999) == 3.0
    assert trajectory(ids, "NLD", "fiscal.spending_level", 1994) == -2.0
    assert trajectory(ids, "NLD", "fiscal.spending_level", 1999) == -2.0
    assert trajectory(ids, "NLD", "monetary.central_bank_independence", 1998) == 0.0
    assert trajectory(ids, "NLD", "monetary.central_bank_independence", 1999) == 3.0


def test_modi_era_reforms_are_dated_and_gst_is_not_counted_twice() -> None:
    ids = [
        "india_modi_first_second_term_2014_2024",
        "modi_demonetisation_gst_2016_2017",
    ]
    assert trajectory(ids, "IND", "regulatory.product_market_competition", 2015) == 0.0
    assert trajectory(ids, "IND", "regulatory.product_market_competition", 2016) == 2.0
    assert trajectory(ids, "IND", "regulatory.product_market_competition", 2017) == 4.0
    assert trajectory(ids, "IND", "fiscal.transfer_expansion", 2017) == 0.0
    assert trajectory(ids, "IND", "fiscal.transfer_expansion", 2018) == 2.0
    assert trajectory(ids, "IND", "fiscal.tax_corporate", 2018) == 0.0
    assert trajectory(ids, "IND", "fiscal.tax_corporate", 2019) == -3.0
    assert trajectory(ids, "IND", "fiscal.sectoral_subsidy", 2019) == 0.0
    assert trajectory(ids, "IND", "fiscal.sectoral_subsidy", 2020) == 3.0
    assert not any(
        axis["axis"] == "institutional.judicial_independence"
        for axis in MOVEMENTS[ids[0]]["axes_summary"]
    )


def test_mitterrand_workweek_and_later_pivots_are_dated_once() -> None:
    ids = [
        "france_mitterrand_first_term_1981_1988",
        "mitterrand_nationalisations_1981_1983",
    ]
    assert trajectory(ids, "FRA", "regulatory.labour_market_flexibility", 1981) == 0.0
    assert trajectory(ids, "FRA", "regulatory.labour_market_flexibility", 1982) == -3.0
    assert trajectory(ids, "FRA", "monetary.monetary_expansion_direction", 1982) == 0.0
    assert trajectory(ids, "FRA", "monetary.monetary_expansion_direction", 1983) == -2.0
    assert trajectory(ids, "FRA", "regulatory.financial_deregulation", 1985) == 0.0
    assert trajectory(ids, "FRA", "regulatory.financial_deregulation", 1986) == -2.0


def test_uae_dubai_support_is_not_counted_in_both_khalifa_records() -> None:
    ids = [
        "uae_khalifa_early_era_2004_2014",
        "uae_khalifa_global_financial_crisis_2008_2010",
    ]
    subset = DRIFT.build_drift([MOVEMENTS[id] for id in ids])
    assert "fiscal.spending_level" not in subset["countries"]["ARE"]["axes"]
    assert trajectory(ids, "ARE", "fiscal.transfer_expansion", 2010) == 0.0
    assert trajectory(ids, "ARE", "fiscal.transfer_expansion", 2011) == 2.0


def test_ireland_pillar_two_is_scored_on_2023_law_not_2021_agreement_or_harris() -> None:
    ids = [
        "ireland_martin_ff_rotating_2020_2022",
        "ireland_varadkar_fg_2022_2024",
        "ireland_harris_fg_2024_present",
    ]
    assert trajectory(ids, "IRL", "fiscal.tax_corporate", 2021) == 0.0
    assert trajectory(ids, "IRL", "fiscal.tax_corporate", 2022) == 0.0
    assert trajectory(ids, "IRL", "fiscal.tax_corporate", 2023) == 2.0
    assert trajectory(ids, "IRL", "fiscal.tax_corporate", 2024) == 2.0
    assert trajectory(ids, "IRL", "fiscal.spending_level", 2023) == 6.0
    assert trajectory(ids, "IRL", "fiscal.spending_level", 2024) == 9.0
    assert trajectory(ids, "IRL", "regulatory.labour_market_flexibility", 2023) == -2.0
    assert trajectory(ids, "IRL", "regulatory.labour_market_flexibility", 2024) == -3.0


def test_ireland_2024_savings_funds_are_dated_and_unscored_assets() -> None:
    policy = yaml.safe_load((ROOT / "policies" / "ie_future_ireland_fund_2024.yaml").read_text())
    assert policy["timeframe"]["enacted_date"] == "2024-06-18"
    assert policy["enacted_by"] == ["ireland_harris_fg_2024_present"]
    assert "axes_moved" not in policy
    assert "ie_future_ireland_fund_2024" not in MOVEMENTS["ireland_varadkar_fg_2022_2024"]["policies"]
    assert "ie_future_ireland_fund_2024" in MOVEMENTS["ireland_harris_fg_2024_present"]["policies"]
    budget = yaml.safe_load((ROOT / "policies" / "ie_budget_2025_giveaway_package.yaml").read_text())
    assert "enacted_date" not in budget["timeframe"]


def test_czech_windfall_and_general_corporate_tax_are_distinct_dated_steps() -> None:
    ids = ["czech_republic_fiala_spolu_2021_2025"]
    assert trajectory(ids, "CZE", "fiscal.tax_corporate", 2022) == 0.0
    assert trajectory(ids, "CZE", "fiscal.tax_corporate", 2023) == 1.0
    assert trajectory(ids, "CZE", "fiscal.tax_corporate", 2024) == 2.0
    subset = DRIFT.build_drift([MOVEMENTS[ids[0]]])
    axes = subset["countries"]["CZE"]["axes"]
    assert "regulatory.trade_openness" not in axes
    assert "monetary.central_bank_independence" not in axes


def test_unlegislated_canadian_capital_gains_proposal_has_no_opposite_steps() -> None:
    ids = ["canada_trudeau_2015_present", "canada_carney_liberal_2025_present"]
    axes = DRIFT.build_drift([MOVEMENTS[id] for id in ids])["countries"]["CAN"]["axes"]
    assert "fiscal.tax_capital" not in axes
    for policy_id in (
        "canada_capital_gains_inclusion_2024",
        "ca_capital_gains_inclusion_cancellation_2025",
    ):
        policy = yaml.safe_load((ROOT / "policies" / f"{policy_id}.yaml").read_text())
        assert policy["status"] == "draft"
        assert "axes_moved" not in policy
        assert "enacted_by" not in policy


def test_colonial_cpf_has_one_non_fiscal_1955_step() -> None:
    ids = ["singapore_cpf_forced_saving_architecture_1955", "lky_singapore_founding_1955_1990"]
    axes = DRIFT.build_drift([MOVEMENTS[id] for id in ids])["countries"]["SGP"]["axes"]
    assert "fiscal.transfer_expansion" not in axes
    assert "fiscal.spending_level" not in axes
    assert trajectory(ids, "SGP", "institutional.property_rights", 1955) == 1.0
    assert MOVEMENTS[ids[1]]["timeframe"]["start"] == 1959
    legacy = yaml.safe_load((ROOT / "policies" / "singapore_cpf_establishment_1955.yaml").read_text())
    assert legacy["status"] == "draft"
    assert legacy["timeframe"]["effective_date"] == "1955-07-01"
    assert "enacted_date" not in legacy["timeframe"]
    assert "axes_moved" not in legacy


def test_bank_indonesia_law_is_scored_once_in_1999() -> None:
    ids = ["indonesia_reformasi_1998_present", "indonesia_habibie_transition_1998_1999"]
    assert MOVEMENTS[ids[0]]["axes_summary"] == []
    assert trajectory(ids, "IDN", "monetary.central_bank_independence", 1998) == 0.0
    assert trajectory(ids, "IDN", "monetary.central_bank_independence", 1999) == 3.0
    legacy = yaml.safe_load((ROOT / "policies" / "indonesia_bank_indonesia_independence_1999.yaml").read_text())
    assert legacy["status"] == "draft"
    assert "axes_moved" not in legacy


def test_japan_budget_and_jfic_are_dated_to_operative_2026_decisions() -> None:
    ids = ["japan_takaichi_ldp_2025_present"]
    axes = DRIFT.build_drift([MOVEMENTS[id] for id in ids])["countries"]["JPN"]["axes"]
    assert trajectory(ids, "JPN", "fiscal.spending_level", 2025) == 0.0
    assert trajectory(ids, "JPN", "fiscal.spending_level", 2026) == 2.0
    assert trajectory(ids, "JPN", "fiscal.sectoral_subsidy", 2026) == 3.0
    assert trajectory(ids, "JPN", "regulatory.sectoral_licensing", 2025) == 0.0
    assert trajectory(ids, "JPN", "regulatory.sectoral_licensing", 2026) == 1.0
    assert "regulatory.trade_openness" not in axes
    screening = yaml.safe_load((ROOT / "policies" / "jp_takaichi_economic_security_screening_2026.yaml").read_text())
    assert screening["status"] == "candidate"
    assert screening["timeframe"]["enacted_date"] == "2026-06-29"
    assert [axis["axis"] for axis in screening["axes_moved"]] == ["regulatory.sectoral_licensing"]
    for policy_id in (
        "jp_fy2026_initial_budget_strategic_investment_2026",
        "jp_fy2026_free_education_lunch_expansion_2026",
        "jp_takaichi_social_security_cost_sharing_2026",
    ):
        policy = yaml.safe_load((ROOT / "policies" / f"{policy_id}.yaml").read_text())
        assert policy["timeframe"]["enacted_date"] == "2026-04-07"


def test_moreno_does_not_recredit_correa_eu_treaty_in_2017() -> None:
    ids = ["ecuador_correa_alianza_pais_ii_2013_2017", "ecuador_moreno_2017_2021"]
    assert trajectory(ids, "ECU", "regulatory.trade_openness", 2016) == 0.0
    assert trajectory(ids, "ECU", "regulatory.trade_openness", 2017) == 1.0
    assert not any(
        axis["axis"] == "regulatory.trade_openness"
        for axis in MOVEMENTS[ids[1]]["axes_summary"]
    )
