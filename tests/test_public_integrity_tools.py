from __future__ import annotations

import importlib.util
import subprocess
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
    assert census.verdict_bucket("Verdict: **SUPPORTED**. pass") == "supported"
    assert census.verdict_bucket("Verdict: **PARTIAL**. p=0.16") == "partial"
    assert (
        census.verdict_bucket("Verdict: supported_subset — basket gap")
        == "supported_subset"
    )
    assert (
        census.verdict_bucket("Verdict: INCONCLUSIVE_DATA_PENDING — missing")
        == "inconclusive_data_pending"
    )


def test_census_excludes_intent_to_add_paths(tmp_path, monkeypatch):
    census = load_script("report_public_census")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    policies = tmp_path / "policies"
    policies.mkdir()
    (policies / "committed.yaml").write_text("policy_id: committed\n")
    subprocess.run(["git", "add", "policies/committed.yaml"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
         "commit", "-q", "-m", "baseline"],
        cwd=tmp_path, check=True,
    )
    (policies / "draft.yaml").write_text("policy_id: draft\n")
    subprocess.run(["git", "add", "-N", "policies/draft.yaml"], cwd=tmp_path, check=True)
    monkeypatch.setattr(census, "ROOT", tmp_path)
    assert census.tracked_paths() == ["policies/committed.yaml"]


def test_opsec_non_research_path_contract():
    opsec = load_script("check_public_opsec")
    assert opsec.non_research_path("STRATEGY.md")
    assert opsec.non_research_path("HANDOFF_TO_RESEARCH.md")
    assert not opsec.non_research_path("engine/runs/example/result_card.md")
