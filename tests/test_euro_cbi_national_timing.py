"""National central-bank steps follow domestic law, not an EMU umbrella date."""
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

CBI = "monetary.central_bank_independence"


def _movement(movement_id: str) -> dict:
    return yaml.safe_load((ROOT / "movements" / f"{movement_id}.yaml").read_text())


def _axis(movement_id: str, axis: str) -> dict | None:
    return next(
        (a for a in _movement(movement_id).get("axes_summary", []) if a["axis"] == axis),
        None,
    )


def test_domestic_law_years_and_policy_reciprocity() -> None:
    cases = {
        "austria_klima_central_bank_statute_1997_2000": (1998, "at_nationalbank_independence_amendment_1998"),
        "belgium_dehaene_cvp_1992_1999": (1993, "be_nbb_monetary_autonomy_law_1993"),
        "finland_lipponen_rainbow_1995_2003": (1998, "fi_bank_of_finland_independence_1997_1998"),
        "france_mitterrand_second_term_1988_1995": (1994, "france_bdf_independence_law_1993"),
        "greece_simitis_pasok_1996_2004": (1997, "greece_bank_of_greece_independence_1997"),
        "netherlands_kok_purple_1994_2002": (1998, "nl_bank_act_independence_1998"),
        "portugal_guterres_ps_1995_2002": (1998, "portugal_bdp_independence_1998"),
        "spain_gonzalez_psoe_later_1989_1996": (1994, "spain_bde_independence_law_1994"),
    }
    for movement_id, (year, policy_id) in cases.items():
        movement = _movement(movement_id)
        axis = _axis(movement_id, CBI)
        assert axis is not None and axis["direction"] == "+"
        assert axis["drift_attribution_year"] == year
        assert axis["drift_attribution_basis"]
        assert policy_id in movement["policies"]
        policy = yaml.safe_load((ROOT / "policies" / f"{policy_id}.yaml").read_text())
        assert movement_id in policy["enacted_by"]
        assert policy["countries"] == movement["countries"]

    assert _movement("france_mitterrand_second_term_1988_1995")["timeframe"]["start"] == 1988
    assert yaml.safe_load((ROOT / "policies" / "france_bdf_independence_law_1993.yaml").read_text())["timeframe"]["effective_date"] == "1994-01-01"
    assert yaml.safe_load((ROOT / "policies" / "spain_bde_independence_law_1994.yaml").read_text())["timeframe"]["effective_date"] == "1994-06-03"
    assert yaml.safe_load((ROOT / "policies" / "greece_bank_of_greece_independence_1997.yaml").read_text())["timeframe"]["enacted_date"] == "1997-12-12"


def test_no_duplicate_euro_or_peg_independence_step() -> None:
    duplicate_ids = (
        "austria_kreisky_spo_1970_1983",
        "austria_vranitzky_grand_coalition_1986_1997",
        "finland_aho_centre_1991_1995",
        "france_giscard_udf_1974_1981",
        "france_chirac_presidency_first_1995_2002",
        "france_jospin_ps_cohabitation_1997_2002",
        "germany_schmidt_spd_fdp_1974_1982",
        "greek_fiscal_dominance_post_euro_2001",
        "italy_prodi_ulivo_1996_1998",
        "italy_euro_entry_non_reform_1999",
        "portugal_cavaco_silva_psd_1985_1995",
        "spain_gonzalez_psoe_first_1982_1989",
        "spain_aznar_pp_1996_2004",
    )
    for movement_id in duplicate_ids:
        assert _axis(movement_id, CBI) is None
    assert _axis("germany_kohl_reunification_era_1987_1998", CBI)["direction"] == "0"
    assert _axis("germany_merkel_i_grand_coalition_2005_2009", "monetary.monetary_expansion_direction") is None

    # These national fiscal changes survive the monetary-scope repair.
    for movement_id, fiscal_axis in (
        ("austria_vranitzky_grand_coalition_1986_1997", "fiscal.spending_level"),
        ("spain_aznar_pp_1996_2004", "fiscal.spending_level"),
        ("greek_fiscal_dominance_post_euro_2001", "fiscal.spending_level"),
        ("italy_prodi_ulivo_1996_1998", "fiscal.spending_level"),
        ("italy_euro_entry_non_reform_1999", "fiscal.spending_level"),
    ):
        assert _axis(movement_id, fiscal_axis) is not None


def test_country_map_cbi_steps_follow_national_decision_years() -> None:
    drift = DRIFT.build_drift(DRIFT.load_movements())
    start = drift["year_min"]
    assert start == 1789
    assert drift["year_max"] == 2026
    expected = {
        "AUT": {1998: 2},
        "BEL": {1993: 3},
        "ESP": {1994: 3},
        "FIN": {1998: 3},
        "FRA": {1994: 3},
        "GRC": {1997: 3},
        "ITA": {1992: 3},
        "NLD": {1998: 3},
        "PRT": {1998: 3},
    }
    for country, increments in expected.items():
        series = drift["countries"][country]["axes"][CBI]
        observed = {
            year: round(series[year - start] - series[year - start - 1], 3)
            for year in range(1986, 2002)
            if round(series[year - start] - series[year - start - 1], 3)
        }
        assert observed == increments
    germany = drift["countries"]["DEU"]["axes"][CBI]
    assert all(germany[year - start] == germany[1986 - start] for year in range(1987, 2002))

    # The 1948 Bank deutscher Länder was already independent of German
    # political authorities. The 1957 Bundesbank Act and 1974 monetary
    # targeting did not replace that founding step in the country series.
    assert germany[1948 - start] - germany[1947 - start] == 3
    assert germany[1957 - start] - germany[1956 - start] == 0
    assert germany[1974 - start] - germany[1973 - start] == 0
    assert "de_bank_deutscher_laender_1948" in _movement("germany_wirtschaftswunder_erhard_1948_1966")["policies"]
    italy = drift["countries"]["ITA"]["axes"][CBI]
    assert italy[1981 - start] - italy[1980 - start] == 3
    assert italy[1976 - start] - italy[1975 - start] == 0
    assert _axis("italy_andreotti_forlani_dc_1976_1983", CBI)["drift_attribution_year"] == 1981


def test_euro_entry_policy_records_do_not_claim_fresh_domestic_independence() -> None:
    for policy_id in (
        "at_hartwaehrungspolitik_1976",
        "fi_emu_membership_1999",
        "fi_markka_devaluation_free_float_1991_1992",
        "fr_france_euro_entry_1999_2002",
        "fr_jospin_privatisations_1997_2002",
        "france_ems_joining_1979",
        "greece_euro_entry_2001",
        "italy_euro_entry_1999",
        "italy_euro_entry_qualification_1998",
        "portugal_euro_entry_1999",
        "portugal_escudo_erm_entry_1992",
        "spain_emu_entry_convergence_1998",
    ):
        policy = yaml.safe_load((ROOT / "policies" / f"{policy_id}.yaml").read_text())
        cbi = [a for a in policy.get("axes_moved", []) if a["axis"] == CBI]
        assert all(a["direction"] == "0" for a in cbi), policy_id
