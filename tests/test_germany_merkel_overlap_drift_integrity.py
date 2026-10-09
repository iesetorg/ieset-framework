"""Dated Merkel-era decisions should appear once in Germany's drift series."""
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

MOVEMENT_IDS = {
    "germany_merkel_broad_2005_2021",
    "germany_merkel_ii_cdu_fdp_2009_2013",
    "germany_merkel_nuclear_phaseout_2011",
    "germany_merkel_iii_2013_2017",
    "germany_merkel_iv_2017_2021",
}


def test_merkel_decisions_have_one_national_step_at_each_reviewed_year() -> None:
    movements = [
        movement for movement in DRIFT.load_movements()
        if movement["movement_id"] in MOVEMENT_IDS
    ]
    assert {movement["movement_id"] for movement in movements} == MOVEMENT_IDS
    drift = DRIFT.build_drift(movements)
    years = drift["years"]
    axes = drift["countries"]["DEU"]["axes"]

    def value(axis: str, year: int) -> float:
        return axes[axis][years.index(year)]

    # The 2011 nuclear exit is the first environmental and supply-security
    # decision, not an extra step at the start of the broad or Merkel II era.
    assert value("regulatory.environmental_stringency", 2010) == 0.0
    assert value("regulatory.environmental_stringency", 2011) == 3.0
    assert value("regulatory.environmental_stringency", 2018) == 3.0
    assert value("regulatory.environmental_stringency", 2019) == 6.0
    assert value("regulatory.energy_supply_security", 2010) == 0.0
    assert value("regulatory.energy_supply_security", 2011) == -3.0
    assert value("regulatory.energy_supply_security", 2018) == -6.0  # Nord Stream 2 permit
    assert value("regulatory.energy_supply_security", 2020) == -8.0  # Coal exit

    # The 2015 refugee response and 2014 social legislation are not credited
    # to the 2005 umbrella or to the Merkel III coalition's 2013 start.
    assert value("regulatory.immigration_openness", 2014) == 0.0
    assert value("regulatory.immigration_openness", 2015) == 3.0
    assert value("fiscal.transfer_expansion", 2013) == 0.0
    assert value("fiscal.transfer_expansion", 2014) == 2.0
    assert value("regulatory.labour_market_flexibility", 2013) == 0.0
    assert value("regulatory.labour_market_flexibility", 2014) == -2.0

    # The remaining fiscal and subsidy decisions retain their own dates.
    assert value("fiscal.spending_level", 2009) == 0.0
    assert value("fiscal.spending_level", 2010) == -2.0
    assert value("fiscal.spending_level", 2019) == -2.0
    assert value("fiscal.spending_level", 2020) == 1.0
    assert value("fiscal.sectoral_subsidy", 2010) == 0.0
    assert value("fiscal.sectoral_subsidy", 2011) == 2.0
    assert value("fiscal.sectoral_subsidy", 2019) == 2.0
    assert value("fiscal.sectoral_subsidy", 2020) == 4.0
