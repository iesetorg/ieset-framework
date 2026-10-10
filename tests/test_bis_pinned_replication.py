"""The 28 promoted BIS packets replay from recorded vintages without writes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN_IDS = (
    # These historical packets retain a frozen verdict_label but no canonical
    # verdict field. Their replay path must remain read-only and archived.
    "bis_corporate_credit_boom_investment_slowdown_panel_1970_2025",
    "bis_corporate_dsr_investment_slowdown_panel_1999_2025",
    "bis_credit_gap_private_investment_reversal_panel",
    "bis_credit_gap_private_investment_slowdown_panel_1970_2025",
    "bis_reer_volatility_investment_drag_panel_1964_2026",
    "bis_credit_gap_consumption_slowdown_panel_1970_2025",
    "bis_credit_gap_current_account_interaction_panel_1970_2025",
    "bis_credit_gap_current_account_twin_deficit_risk",
    "bis_credit_gap_dsr_joint_crisis_risk_panel_1999_2025",
    "bis_credit_gap_dsr_joint_fragility_panel_1999_2025",
    "bis_credit_gap_export_growth_drag_panel_1970_2025",
    "bis_credit_gap_house_price_reversal_oecd_1970_2025",
    "bis_credit_gap_low_real_rate_amplifier_panel",
    "bis_credit_gap_manufacturing_share_drag_panel_1970_2025",
    "bis_credit_gap_property_price_interaction_panel_1970_2025",
    "bis_credit_gap_unemployment_lag_panel_1970_2025",
    "bis_dsr_current_account_deficit_unemployment_panel_1999_2025",
    "bis_dsr_house_price_boom_reversal_panel_1999_2025",
    "bis_house_price_credit_gap_boom_bust_panel",
    "bis_household_dsr_consumption_slowdown_panel_1999_2025",
    "bis_long_horizon_credit_cycle_market_discipline_panel",
    "bis_reer_appreciation_export_growth_panel_1964_2026",
    "bis_reer_appreciation_industrial_share_panel_1964_2026",
    "bis_reer_appreciation_inflation_relief_panel_1964_2026",
    "bis_reer_depreciation_current_account_repair_panel_1964_2026",
    "bis_reer_devaluation_inflation_tradeoff_panel_1964_2026",
    "bis_reer_misalignment_current_account_repair_panel_1964_2026",
    "bis_reer_volatility_export_drag_panel_1964_2026",
)
PACKET_FILES = (
    "diagnostics.json", "manifest.yaml", "coefficients.parquet",
    "chart_data.json", "result_card.md",
)


def _wrapper(run_id: str):
    path = ROOT / "engine" / "runs" / run_id / "replication.py"
    spec = importlib.util.spec_from_file_location(f"bis_replication_{run_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_archived_sources(run_id: str) -> None:
    manifest = yaml.safe_load((ROOT / "engine" / "runs" / run_id / "manifest.yaml").read_text())
    absent = [
        source["vintage_file"] for source in manifest["vintages"].values()
        if not (ROOT / source["vintage_file"]).is_file()
    ]
    if absent:
        pytest.skip("archived BIS/WDI vintages are absent from this checkout")


@pytest.mark.parametrize("run_id", RUN_IDS)
def test_promoted_bis_wrapper_is_source_pinned_and_read_only(run_id: str) -> None:
    wrapper_path = ROOT / "engine" / "runs" / run_id / "replication.py"
    source = wrapper_path.read_text()
    assert "from replay_bis_pinned import replay_one" in source
    assert "subprocess" not in source
    _require_archived_sources(run_id)

    packet = [ROOT / "engine" / "runs" / run_id / name for name in PACKET_FILES]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in packet}
    assert _wrapper(run_id).main() == 0
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in packet}


@pytest.mark.parametrize("run_id", (
    "bis_credit_gap_low_real_rate_amplifier_panel",
    "bis_reer_appreciation_export_growth_panel_1964_2026",
))
def test_bis_replay_rejects_packet_and_source_drift(run_id: str, tmp_path: Path) -> None:
    _require_archived_sources(run_id)
    wrapper = _wrapper(run_id)
    archived = ROOT / "engine" / "runs" / run_id
    scratch = tmp_path / run_id
    scratch.mkdir()
    for name in PACKET_FILES:
        shutil.copy2(archived / name, scratch / name)
    wrapper.RUN_DIR = scratch

    diagnostics = json.loads((scratch / "diagnostics.json").read_text())
    diagnostics["verdict_label"] = "SUPPORTED" if diagnostics["verdict_label"] != "SUPPORTED" else "REFUTED"
    (scratch / "diagnostics.json").write_text(json.dumps(diagnostics))
    with pytest.raises(ValueError, match="diagnostics.verdict_label"):
        wrapper.main()

    shutil.copy2(archived / "diagnostics.json", scratch / "diagnostics.json")
    manifest = yaml.safe_load((scratch / "manifest.yaml").read_text())
    first = next(iter(manifest["vintages"].values()))
    first["sha256"] = "0" * 64
    (scratch / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    with pytest.raises(ValueError, match="pinned vintage mismatch"):
        wrapper.main()


def test_legacy_packet_without_canonical_verdict_still_rejects_label_drift(tmp_path: Path) -> None:
    run_id = "bis_credit_gap_private_investment_reversal_panel"
    _require_archived_sources(run_id)
    wrapper = _wrapper(run_id)
    archived = ROOT / "engine" / "runs" / run_id
    scratch = tmp_path / run_id
    scratch.mkdir()
    for name in PACKET_FILES:
        shutil.copy2(archived / name, scratch / name)
    assert "verdict" not in json.loads((scratch / "diagnostics.json").read_text())
    wrapper.RUN_DIR = scratch

    diagnostics = json.loads((scratch / "diagnostics.json").read_text())
    diagnostics["verdict_label"] = "SUPPORTED"
    (scratch / "diagnostics.json").write_text(json.dumps(diagnostics))
    with pytest.raises(ValueError, match="diagnostics.verdict_label"):
        wrapper.main()
