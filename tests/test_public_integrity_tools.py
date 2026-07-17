from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_census_verdict_bucket_normalises_public_tiers():
    census = load_script("report_public_census")
    assert census.verdict_bucket("**Verdict:** SUPPORTED — pass") == "supported"
    assert (
        census.verdict_bucket("Verdict: supported_subset — basket gap")
        == "supported_subset"
    )
    assert (
        census.verdict_bucket("Verdict: INCONCLUSIVE_DATA_PENDING — missing")
        == "inconclusive_data_pending"
    )


def test_opsec_private_path_contract():
    opsec = load_script("check_public_opsec")
    assert opsec.private_path("engine/agent_briefs/internal.md")
    assert opsec.private_path("scripts/report_brain_budget_state.py")
    assert opsec.private_path("HANDOFF_TO_RESEARCH_AGENT.md")
    assert not opsec.private_path("engine/runs/brain_drain/result_card.md")
