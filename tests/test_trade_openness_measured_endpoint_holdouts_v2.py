"""Registration and read-only replay guards for the nine-test trade family."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts import run_trade_openness_measured_endpoint_holdouts_v2 as holdouts


def test_nine_test_family_and_disjoint_old_roster() -> None:
    assert len(holdouts.COHORT) == 8
    assert holdouts.FAMILY_SIZE == len(holdouts.COHORT) + 1
    assert holdouts.FAMILY_SIZE * holdouts.P_MAX <= 0.10
    assert len(holdouts.OLD_COUNTRIES) == 40
    for hypothesis_id, (_, outcome, old_id, sign) in holdouts.COHORT.items():
        old_paths = list((holdouts.ROOT / "hypotheses").glob(f"*/{old_id}.yaml"))
        assert len(old_paths) == 1
        old = yaml.safe_load(old_paths[0].read_text(encoding="utf-8"))
        assert set(old["sample"]["countries"]) == holdouts.OLD_COUNTRIES
        assert old["variables"]["outcome"][0]["source"] == holdouts.VINTAGES[outcome][0]
        assert old["variables"]["treatment"][0]["source"] == holdouts.VINTAGES["trade"][0]
        spec = holdouts.validate_spec(hypothesis_id)
        assert spec["claim_direction"] == sign
        assert spec["falsification"]["threshold"]["family_size"] == 9
        assert (holdouts.ROOT / spec["steelman"]).is_file()


@pytest.mark.parametrize("sign", ["+", "-"])
def test_two_sided_family_rule_counts_adverse_results(sign: str) -> None:
    favorable = 1.0 if sign == "+" else -1.0
    assert holdouts.classify(favorable, 0.01, sign)[0] == "SUPPORTED"
    assert holdouts.classify(-favorable, 0.01, sign)[0] == "REFUTED"
    assert holdouts.classify(favorable, 0.010001, sign)[0] == "PARTIAL"
    assert holdouts.classify(-favorable, 0.010001, sign)[0] == "PARTIAL"


def test_run_stops_before_estimation_without_committed_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    hypothesis_id = next(iter(holdouts.COHORT))

    def stale_git_show(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=b"stale preregistration")

    def forbidden_estimation(*args: object, **kwargs: object) -> None:
        raise AssertionError("estimation was reached before registration")

    monkeypatch.setattr(holdouts.subprocess, "run", stale_git_show)
    monkeypatch.setattr(holdouts, "estimate_one", forbidden_estimation)
    with pytest.raises(RuntimeError, match="commit the entire nine-test preregistration"):
        holdouts.run_one(hypothesis_id)


def test_registration_requires_committed_ninth_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    hypothesis_id = next(iter(holdouts.COHORT))
    inspected: list[str] = []

    def git_show_with_stale_private_runner(
        command: list[str], **kwargs: object,
    ) -> subprocess.CompletedProcess[bytes]:
        assert command[:2] == ["git", "show"]
        relative_path = command[2].removeprefix("HEAD:")
        inspected.append(relative_path)
        if relative_path == holdouts.PRIVATE_RUNNER_REL:
            return subprocess.CompletedProcess(command, 0, stdout=b"stale private runner")
        return subprocess.CompletedProcess(
            command, 0, stdout=(holdouts.ROOT / relative_path).read_bytes()
        )

    monkeypatch.setattr(holdouts.subprocess, "run", git_show_with_stale_private_runner)
    with pytest.raises(RuntimeError, match=holdouts.PRIVATE_RUNNER_REL):
        holdouts.registration_commit(hypothesis_id)
    assert holdouts.PRIVATE_RUNNER_REL in inspected


def test_existing_run_check_replays_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    hypothesis_id = next(iter(holdouts.COHORT))
    run_dir = tmp_path / "engine" / "runs" / hypothesis_id
    run_dir.mkdir(parents=True)
    gate = {"observations": 2000, "countries": 100, "passed": True}
    sources = [{"role": "outcome", "vintage_file": "pinned.parquet", "sha256": "abc"}]
    estimate = {"coefficient": 0.3, "std_error": 0.1, "p_value": 0.005,
                "r_squared": 0.2, "ci95": [0.1, 0.5], "n_obs": 2000, "n_countries": 100}
    (run_dir / "diagnostics.json").write_text(json.dumps({
        "preregistration_commit": "prereg", "preflight": gate,
        "verdict_label": "SUPPORTED", "estimate": estimate,
    }), encoding="utf-8")
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "preregistration_commit": "prereg", "vintages": sources, "status": "SUPPORTED",
    }), encoding="utf-8")
    before = {file.name: file.read_bytes() for file in run_dir.iterdir()}
    monkeypatch.setattr(holdouts, "ROOT", tmp_path)
    monkeypatch.setattr(holdouts, "registration_commit", lambda _: "prereg")
    monkeypatch.setattr(holdouts, "estimate_one", lambda _: (
        gate, sources, "SUPPORTED", "expected sign and p", estimate,
    ))
    assert holdouts.check_one(hypothesis_id)["wrote_files"] is False
    assert {file.name: file.read_bytes() for file in run_dir.iterdir()} == before

    changed = {**estimate, "coefficient": 0.4}
    monkeypatch.setattr(holdouts, "estimate_one", lambda _: (
        gate, sources, "SUPPORTED", "expected sign and p", changed,
    ))
    with pytest.raises(AssertionError, match="coefficient mismatch"):
        holdouts.check_one(hypothesis_id)
    assert {file.name: file.read_bytes() for file in run_dir.iterdir()} == before
