"""Umbrella narratives and dated policy phases must not multiply drift steps."""
from __future__ import annotations

import importlib.util
from pathlib import Path

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
        "vietnam_trong_era_2011_2024",
    ]
    assert trajectory(ids, "VNM", "institutional.property_rights", 1987) == 3.0
    assert trajectory(ids, "VNM", "regulatory.product_market_competition", 1988) == 3.0
    assert trajectory(ids, "VNM", "regulatory.sectoral_licensing", 1990) == -3.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 1986) == 0.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2000) == 0.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2001) == 3.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2007) == 6.0
    assert trajectory(ids, "VNM", "regulatory.trade_openness", 2019) == 9.0


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
