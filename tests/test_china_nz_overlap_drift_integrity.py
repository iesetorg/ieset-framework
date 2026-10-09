"""Overlapping reform narratives must not credit one law or accession twice."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compute_country_drift_china_nz", ROOT / "scripts" / "compute_country_drift.py"
)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)
MOVEMENTS = {movement["movement_id"]: movement for movement in DRIFT.load_movements()}


def trajectory(ids: list[str], country: str, axis: str, year: int) -> float:
    result = DRIFT.build_drift([MOVEMENTS[movement_id] for movement_id in ids])
    return result["countries"][country]["axes"][axis][result["years"].index(year)]


def test_china_early_sez_opening_and_2001_wto_entry_are_distinct_steps() -> None:
    ids = [
        "deng_xiaoping_reforms_1978",
        "china_jiang_era_1989_2002",
        "china_wto_accession_2001",
        "china_hu_era_2002_2012",
    ]
    assert trajectory(ids, "CHN", "regulatory.trade_openness", 1978) == 0.0
    assert trajectory(ids, "CHN", "regulatory.trade_openness", 1980) == 1.0
    assert trajectory(ids, "CHN", "regulatory.trade_openness", 1989) == 1.0
    assert trajectory(ids, "CHN", "regulatory.trade_openness", 2001) == 4.0
    assert trajectory(ids, "CHN", "regulatory.trade_openness", 2002) == 4.0
    assert not any(
        axis["axis"] == "regulatory.trade_openness"
        for axis in MOVEMENTS["china_jiang_era_1989_2002"]["axes_summary"]
    )


def test_bolger_owns_1991_labour_act_and_1994_fiscal_act() -> None:
    rogernomics = MOVEMENTS["nz_rogernomics_1984_1993"]
    bolger = MOVEMENTS["newzealand_bolger_national_1990_1997"]
    assert "nz_employment_contracts_act_1991" not in rogernomics["policies"]
    assert "nz_fiscal_responsibility_act_1994" not in rogernomics["policies"]
    assert "nz_employment_contracts_act_1991" in bolger["policies"]
    assert "nz_fiscal_responsibility_act_1994" in bolger["policies"]
    ids = ["nz_rogernomics_1984_1993", "newzealand_bolger_national_1990_1997"]
    assert trajectory(ids, "NZL", "regulatory.labour_market_flexibility", 1984) == 0.0
    assert trajectory(ids, "NZL", "regulatory.labour_market_flexibility", 1990) == 0.0
    assert trajectory(ids, "NZL", "regulatory.labour_market_flexibility", 1991) == 3.0
    assert trajectory(ids, "NZL", "fiscal.transfer_expansion", 1990) == 0.0
    assert trajectory(ids, "NZL", "fiscal.transfer_expansion", 1991) == -3.0
    assert trajectory(ids, "NZL", "fiscal.spending_level", 1990) == -2.0
    assert trajectory(ids, "NZL", "fiscal.spending_level", 1991) == -4.0
    assert trajectory(ids, "NZL", "institutional.rule_of_law", 1993) == 0.0
    assert trajectory(ids, "NZL", "institutional.rule_of_law", 1994) == 2.0
