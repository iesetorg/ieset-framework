"""Structural and adversarial checks for the unfitted Germany registration."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_germany_2025_manufacturing_electricity_peer_comovement_v2.py"
SPEC = importlib.util.spec_from_file_location("germany_2025_peer_comovement", RUNNER)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_fixed_registration_and_old_fit_disclosure() -> None:
    spec = module.validate_spec()
    boundary = module.old_run_boundary()
    assert spec["covers_claims"] == []
    assert spec["falsification"]["threshold"]["quality_flag_status"] == "unavailable_in_pinned_parquet"
    assert boundary["old_2024_wdi_industrial_values_present"] is True
    assert boundary["old_2025_wdi_industrial_values_present"] is False
    assert boundary["calendar_disjoint_2024_2025"] is False


def test_preflight_projects_keys_without_selected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    original = pd.read_parquet

    def key_only(*args: object, **kwargs: object) -> pd.DataFrame:
        assert "value" not in kwargs.get("columns", [])
        return original(*args, **kwargs)

    monkeypatch.setattr(module.pd, "read_parquet", key_only)
    gate, sources = module.preflight()
    assert gate["passed"] is True
    assert gate["heldout_values_accessed"] is False
    assert gate["selected_keys"] == {"manufacturing": 22, "electricity": 44}
    assert len(sources) == 2


@pytest.mark.parametrize(
    ("manufacturing_gap", "electricity_gap", "label"),
    [
        (-0.01, 0.02, "SUPPORTED"),
        (0.01, -0.02, "REFUTED"),
        (-0.01, -0.02, "PARTIAL"),
        (0.01, 0.02, "PARTIAL"),
        (0.0, 0.02, "PARTIAL"),
        (-0.01, 0.0, "PARTIAL"),
    ],
)
def test_joint_sign_rule(manufacturing_gap: float, electricity_gap: float, label: str) -> None:
    assert module.classify(manufacturing_gap, electricity_gap)[0] == label


def test_registration_gate_precedes_any_value_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked() -> None:
        raise RuntimeError("synthetic uncommitted registration")

    def forbidden() -> None:
        pytest.fail("selected values read before registration gate")

    monkeypatch.setattr(module, "registration_files", blocked)
    monkeypatch.setattr(module, "calculate", forbidden)
    with pytest.raises(RuntimeError, match="synthetic uncommitted registration"):
        module.run_one()


def test_duplicate_or_missing_key_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    source = module.SOURCES["manufacturing"]
    original = module.selected_rows

    def damaged(role: str, *, include_value: bool) -> pd.DataFrame:
        rows = original(role, include_value=include_value)
        return rows.iloc[1:] if role == "manufacturing" else rows

    monkeypatch.setattr(module, "selected_rows", damaged)
    with pytest.raises(ValueError, match="fixed manufacturing key coverage"):
        module.preflight()
    assert source["selector"]["unit"] == "CLV_I20"
