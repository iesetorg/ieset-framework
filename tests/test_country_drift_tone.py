"""Ordinary military mentions do not imply authoritarian chart tone."""
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


def test_bare_military_references_do_not_set_authoritarian_tone() -> None:
    movement = {
        "movement_id": "civilian_parliamentary_government",
        "coalition": "Elected parliamentary coalition",
        "doctrine": "It expanded military spending and discussed military history.",
        "axes_summary": [
            {"axis": "fiscal.transfer_expansion", "direction": "+", "magnitude": "moderate"}
        ],
    }
    assert DRIFT.classify_movement_tone(movement) == "left"
    movement["coalition"] = "Elected coalition with military-cadre appointments"
    assert DRIFT.classify_movement_tone(movement) == "left"


def test_actual_democratic_and_junta_movements() -> None:
    movements = {m["movement_id"]: m for m in DRIFT.load_movements()}
    for movement_id in (
        "finland_marin_rainbow_2019_2023",
        "germany_merkel_broad_2005_2021",
        "us_biden_administration_broad_2021_2025",
        "brazil_bolsonaro_pl_2019_2022",
    ):
        assert DRIFT.classify_movement_tone(movements[movement_id]) != "auth", movement_id
    for movement_id in (
        "argentina_proceso_military_junta_1976_1983",
        "egypt_scaf_transition_2011_2012",
        "thailand_prayut_junta_pprp_2014_2023",
        "turkey_evren_military_1980_1983",
        "guinea_cnrd_transition_resource_state_2021_present",
        "mmr_burmese_way_to_socialism_1962",
        "ethiopia_derg_1974_1991",
    ):
        assert DRIFT.classify_movement_tone(movements[movement_id]) == "auth", movement_id


def test_existing_strong_terms_remain_authoritarian() -> None:
    movements = {m["movement_id"]: m for m in DRIFT.load_movements()}
    assert DRIFT.classify_movement_tone(
        movements["algeria_fln_socialist_developmental_state_1962_1978"]
    ) == "auth"
    assert DRIFT.classify_movement_tone(
        movements["cuba_post_1959_socialist_economy"]
    ) == "auth"
    assert DRIFT.classify_movement_tone({
        "movement_id": "current_junta",
        "coalition": "Military junta",
        "doctrine": "Governing after a coup",
    }) == "auth"


def test_reviewed_parliamentary_and_historical_triggers_are_not_regime_tags() -> None:
    movements = {m["movement_id"]: m for m in DRIFT.load_movements()}
    assert DRIFT.NON_AUTH_TRIGGER_IDS <= movements.keys()
    assert not DRIFT.NON_AUTH_TRIGGER_IDS & DRIFT.AUTH_MOVEMENT_IDS
    assert not DRIFT.NON_AUTH_TRIGGER_IDS & DRIFT.AUTH_REVIEW_HOLD_IDS
    for movement_id in DRIFT.NON_AUTH_TRIGGER_IDS:
        assert DRIFT.classify_movement_tone(movements[movement_id]) != "auth", movement_id
    for movement_id in (
        "belgium_dehaene_cvp_1992_1999",
        "belgium_verhofstadt_purple_1999_2007",
        "italy_tangentopoli_transition_1992_1994",
        "philippines_aquino_iii_2010_2016",
        "skorea_lee_jaemyung_dp_2025_present",
    ):
        assert DRIFT.classify_movement_tone(movements[movement_id]) != "auth", movement_id


def test_explicit_regime_evidence_and_review_holds_are_preserved() -> None:
    movements = {m["movement_id"]: m for m in DRIFT.load_movements()}
    retained = DRIFT.AUTH_MOVEMENT_IDS | DRIFT.AUTH_REVIEW_HOLD_IDS
    assert retained <= movements.keys()
    for movement_id in retained:
        assert DRIFT.classify_movement_tone(movements[movement_id]) == "auth", movement_id
