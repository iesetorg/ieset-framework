"""Structural checks for the unrun Spain temporal holdout.

All parquet access is mocked. These tests never read 2024-25 outcome values.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "run_spain_sanchez_2024_2025_macro_holdout_v2.py"
SPEC = importlib.util.spec_from_file_location("run_spain_sanchez_2024_2025_macro_holdout_v2", MODULE)
assert SPEC is not None and SPEC.loader is not None
spain = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spain)


def test_frozen_two_endpoint_contract_and_direct_sources() -> None:
    spec = spain.validate_spec()
    assert spec["covers_claims"] == []
    assert spec["sample"]["countries"] == list(spain.COUNTRIES)
    assert spain.PEERS == ("FRA", "ITA", "PRT", "GRC", "DEU", "NLD", "BEL")
    assert spain.MIN_COUNTRY_YEARS == 16
    assert spec["falsification"]["threshold"] == spain.EXPECTED_THRESHOLD
    assert spec["evidence_type"] == "descriptive"
    assert all(source["publisher"] == "eurostat" for source in spain.SOURCES.values())
    assert len(spain.SOURCES) == 3
    assert len(spec["variables"]["outcome"]) == 2
    assert all(source["sha256"] and source["manifest"] for source in spain.SOURCES.values())
    assert "no causal credit" in spec["disclosure"].lower() or "cannot be credited" in spec["disclosure"].lower()


def test_joint_directional_rule_has_no_single_leg_success() -> None:
    assert spain.classify(0.0, 0.0)[0] == "SUPPORTED"
    assert spain.classify(-0.001, -0.001)[0] == "REFUTED"
    assert spain.classify(0.001, -0.001)[0] == "PARTIAL"
    assert spain.classify(-0.001, 0.001)[0] == "PARTIAL"


def test_preflight_reads_only_dimension_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    read_columns = []

    def key_frame(path: Path, *, columns: list[str]) -> pd.DataFrame:
        assert "value" not in columns
        read_columns.append((path, columns))
        role = next(role for role, source in spain.SOURCES.items()
                    if path == spain.ROOT / source["path"])
        source = spain.SOURCES[role]
        return pd.DataFrame([
            {"geo_code": geo, "period": str(year), **source["selector"]}
            for geo in spain.ISO3_TO_EUROSTAT.values() for year in spain.YEARS
        ])

    monkeypatch.setattr(spain, "verified_sources", lambda: [{"role": role} for role in spain.SOURCES])
    monkeypatch.setattr(spain.pd, "read_parquet", key_frame)
    gate, _ = spain.preflight()
    assert gate["passed"] is True
    assert gate["heldout_values_accessed"] is False
    assert gate["country_years_per_source"] == {role: 16 for role in spain.SOURCES}
    assert len(read_columns) == 3


def test_run_requires_registration_before_value_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_registration() -> tuple[str, list[dict[str, str]]]:
        raise RuntimeError("registration is not committed")

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("outcome access was reached")

    monkeypatch.setattr(spain, "registration_files", no_registration)
    monkeypatch.setattr(spain, "preflight", forbidden)
    monkeypatch.setattr(spain, "evaluate", forbidden)
    with pytest.raises(RuntimeError, match="registration is not committed"):
        spain.run_one()


def test_registration_rejects_run_artifacts_at_first_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_bytes = {}
    for relative_path in spain.REGISTRATION_FILES:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative_path.encode())
        file_bytes[relative_path] = path.read_bytes()
    monkeypatch.setattr(spain, "ROOT", tmp_path)

    def git_with_early_run(*args: str) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "show":
            return subprocess.CompletedProcess(args, 0, file_bytes[args[1].split(":", 1)[1]], b"")
        if args[0] == "log":
            return subprocess.CompletedProcess(args, 0, b"firstcommit\n", b"")
        if args[0] == "ls-tree":
            return subprocess.CompletedProcess(args, 0,
                                               f"{spain.RUN_REL}/diagnostics.json\n".encode(), b"")
        raise AssertionError(args)

    monkeypatch.setattr(spain, "_git", git_with_early_run)
    with pytest.raises(RuntimeError, match="run artifacts existed"):
        spain.registration_files()


def test_read_only_check_preserves_packet_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    gate = {"passed": True, "heldout_values_accessed": False}
    sources = [{"role": "synthetic", "path": "synthetic.parquet", "sha256": "source"}]
    registration = [{"path": spain.SPEC_REL, "sha256": "spec"},
                    {"path": spain.STEELMAN_REL, "sha256": "steelman"},
                    {"path": spain.RUNNER_REL, "sha256": "runner"}]
    estimate = {"method": "synthetic", "gdp_pc_log_growth_gap": 0.01,
                "employment_change_gap_pp": 0.2}
    reason = spain.classify(0.01, 0.2)[1]
    diagnostics, manifest, packet, card, chart, rows = spain.artifact_records(
        "stamp", "prereg", registration, gate, sources, "SUPPORTED", reason, estimate
    )
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics), encoding="utf-8")
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(
        yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart), encoding="utf-8")
    (run_dir / "replication.py").write_text(spain.replication_wrapper(), encoding="utf-8")
    snapshot = tmp_path / spain.SPEC_REL
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes((spain.ROOT / spain.SPEC_REL).read_bytes())
    (run_dir / "hypothesis.yaml").write_bytes(snapshot.read_bytes())
    pd.DataFrame(rows, columns=list(spain.COEFFICIENT_COLUMNS)).to_parquet(
        run_dir / "coefficients.parquet", index=False)
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in run_dir.iterdir()}
    monkeypatch.setattr(spain, "RUN_DIR", run_dir)
    monkeypatch.setattr(spain, "ROOT", tmp_path)
    monkeypatch.setattr(spain, "registration_files", lambda: ("prereg", registration))
    monkeypatch.setattr(spain, "preflight", lambda: (gate, sources))
    monkeypatch.setattr(spain, "evaluate", lambda _: ("SUPPORTED", reason, estimate))
    assert spain.check_one()["wrote_files"] is False
    assert {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in run_dir.iterdir()} == before

    monkeypatch.setattr(spain, "evaluate", lambda _: ("SUPPORTED", reason,
                                                       {**estimate, "gdp_pc_log_growth_gap": 0.02}))
    with pytest.raises(AssertionError, match="does not match"):
        spain.check_one()
    assert {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in run_dir.iterdir()} == before

    monkeypatch.setattr(spain, "evaluate", lambda _: ("SUPPORTED", reason, estimate))
    for name in ("evidence_packet.yaml", "result_card.md", "chart_data.json", "replication.py"):
        path = run_dir / name
        original = path.read_bytes()
        if name.endswith(".json"):
            changed = json.loads(original)
            changed["registered_zero_threshold"] = 0.1
            path.write_text(json.dumps(changed), encoding="utf-8")
        else:
            path.write_bytes(original + (b"\n# changed after run\n" if name.endswith(".yaml")
                                         else b"\nchanged after run\n"))
        tampered = {item.name: hashlib.sha256(item.read_bytes()).hexdigest()
                    for item in run_dir.iterdir()}
        with pytest.raises(AssertionError, match="does not match"):
            spain.check_one()
        assert {item.name: hashlib.sha256(item.read_bytes()).hexdigest()
                for item in run_dir.iterdir()} == tampered
        path.write_bytes(original)


def test_failed_source_gate_is_inconclusive_without_value_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def failed_preflight() -> None:
        raise ValueError("pinned source hash mismatch")

    def forbidden_evaluate(*_args: object) -> None:
        raise AssertionError("held-out values were read")

    monkeypatch.setattr(spain, "preflight", failed_preflight)
    monkeypatch.setattr(spain, "evaluate", forbidden_evaluate)
    gate, sources, verdict, reason, estimate = spain.calculate()
    assert gate["passed"] is False
    assert gate["heldout_values_accessed"] is False
    assert sources == []
    assert verdict == "INCONCLUSIVE"
    assert "source hash mismatch" in reason
    assert estimate is None
