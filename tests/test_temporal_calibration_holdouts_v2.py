"""Structural guards for the two unrun temporal holdouts.

Candidate parquet access is mocked; these tests do not inspect held-out values.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "run_temporal_calibration_holdouts_v2.py"
SPEC = importlib.util.spec_from_file_location("run_temporal_calibration_holdouts_v2", MODULE)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize("study", ["canada", "rrp"])
def test_frozen_spec_and_calibration_scope(study: str) -> None:
    spec = runner.validate_spec(study)
    assert spec["status"] == "pre_registered"
    assert spec["evidence_type"] == "descriptive"
    assert spec["covers_claims"] == []
    assert spec["falsification"]["threshold"] == runner.THRESHOLDS[study]
    assert "no" in spec["disclosure"].lower() and "causal" in spec["disclosure"].lower()
    if study == "rrp":
        assert spec["falsification"]["threshold"]["source_file"]["fetch_time_manifest"] is None
        assert "fetch-time manifest" in spec["methodology_note"]
        steelman = (ROOT / runner.STEELMAN_RELS[study]).read_text(encoding="utf-8")
        assert "No fetch-time manifest" in steelman


def test_canada_preflight_never_reads_outcome_or_null_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[list[str]] = []

    def keys(_path: Path, columns: list[str]) -> list[dict[str, object]]:
        assert columns == ["country_iso3", "year", "indicator_id"]
        seen.append(columns)
        return [{"country_iso3": country, "year": year,
                 "indicator_id": runner.SOURCES["canada"]["series_id"]}
                for country in runner.CANADA_COUNTRIES for year in runner.CANADA_YEARS]

    monkeypatch.setattr(runner, "verified_source", lambda _: runner.SOURCES["canada"])
    monkeypatch.setattr(runner, "_read_parquet", keys)
    gate, _ = runner.preflight("canada")
    assert gate["country_year_keys"] == 14
    assert gate["heldout_values_accessed"] is False
    assert gate["value_completeness_unchecked"] is True
    assert len(seen) == 1


def test_rrp_preflight_never_reads_amount_or_null_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[list[str]] = []

    def keys(_path: Path, columns: list[str]) -> list[dict[str, object]]:
        assert columns == ["date"]
        seen.append(columns)
        return [{"date": f"2025-{month:02d}-{day:02d}"}
                for month in range(1, 13) for day in range(1, 21)]

    monkeypatch.setattr(runner, "verified_source", lambda _: runner.SOURCES["rrp"])
    monkeypatch.setattr(runner, "_read_parquet", keys)
    gate, _ = runner.preflight("rrp")
    assert gate["date_keys_by_quarter"] == {q: 60 for q in runner.RRP_QUARTERS}
    assert gate["heldout_values_accessed"] is False
    assert gate["value_completeness_unchecked"] is True
    assert len(seen) == 1


@pytest.mark.parametrize("study", ["canada", "rrp"])
def test_run_checks_registration_before_any_value_access(
    study: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_registration() -> None:
        raise RuntimeError("registration is not committed")

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("outcome access reached")

    monkeypatch.setattr(runner, "registration_files", no_registration)
    monkeypatch.setattr(runner, "preflight", forbidden)
    monkeypatch.setattr(runner, "evaluate", forbidden)
    with pytest.raises(RuntimeError, match="registration is not committed"):
        runner.run_one(study)


def test_registration_rejects_result_in_first_addition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_bytes = {}
    for relative in runner.REGISTRATION_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())
        file_bytes[relative] = path.read_bytes()
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def fake_git(*args: str) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "show":
            return subprocess.CompletedProcess(args, 0,
                                               file_bytes[args[1].split(":", 1)[1]], b"")
        if args[0] == "log":
            return subprocess.CompletedProcess(args, 0, b"first\n", b"")
        if args[0] == "ls-tree":
            return subprocess.CompletedProcess(
                args, 0, f"engine/runs/{runner.CANADA}/diagnostics.json\n".encode(), b""
            )
        raise AssertionError(args)

    monkeypatch.setattr(runner, "_git", fake_git)
    with pytest.raises(RuntimeError, match="run artifacts existed"):
        runner.registration_files()


def test_registration_rejects_changed_first_addition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_bytes = {}
    for relative in runner.REGISTRATION_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())
        file_bytes[relative] = path.read_bytes()
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def fake_git(*args: str) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "show":
            ref, relative = args[1].split(":", 1)
            payload = file_bytes[relative]
            if ref == "first" and relative == runner.SPEC_RELS["canada"]:
                payload += b"\nchanged"
            return subprocess.CompletedProcess(args, 0, payload, b"")
        if args[0] == "log":
            return subprocess.CompletedProcess(args, 0, b"first\n", b"")
        if args[0] == "ls-tree":
            return subprocess.CompletedProcess(args, 0, b"", b"")
        raise AssertionError(args)

    monkeypatch.setattr(runner, "_git", fake_git)
    with pytest.raises(RuntimeError, match="registration changed"):
        runner.registration_files()


def test_predeclared_directional_rules() -> None:
    assert runner.classify_canada(0.0, -0.01)[0] == "SUPPORTED"
    assert runner.classify_canada(0.01, 0.01)[0] == "REFUTED"
    assert runner.classify_canada(0.01, -0.01)[0] == "PARTIAL"
    assert runner.classify_rrp({q: 499 for q in runner.RRP_QUARTERS})[0] == "SUPPORTED"
    assert runner.classify_rrp({"2025Q1": 1000, "2025Q2": 1000,
                                "2025Q3": 100, "2025Q4": 100})[0] == "REFUTED"
    assert runner.classify_rrp({"2025Q1": 600, "2025Q2": 400,
                                "2025Q3": 400, "2025Q4": 400})[0] == "PARTIAL"


@pytest.mark.parametrize("study", ["canada", "rrp"])
def test_check_is_read_only_and_detects_packet_tamper(
    study: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    hid = runner.HIDS[study]
    run_dir = tmp_path / "engine" / "runs" / hid
    run_dir.mkdir(parents=True)
    spec_path = tmp_path / runner.SPEC_RELS[study]
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / runner.SPEC_RELS[study]).read_bytes())
    gate = {"passed": True, "heldout_values_accessed": False}
    source = runner.SOURCES[study]
    if study == "canada":
        label, reason = runner.classify_canada(0.0, -0.02)
        estimate = {"method": "synthetic", "n_countries": 7, "n_country_years": 14,
                    "canada_log_growth": 0.0, "peer_median_log_growth": 0.02,
                    "peer_gap_log_points": -0.02}
    else:
        medians = {q: 100.0 for q in runner.RRP_QUARTERS}
        label, reason = runner.classify_rrp(medians)
        estimate = {"method": "synthetic", "n_daily_observations": 240,
                    "n_days_by_quarter": {q: 60 for q in runner.RRP_QUARTERS},
                    "quarter_medians_usd_bn": medians}
    files = runner.artifacts(study, "stamp", "prereg", [], gate, source,
                             label, reason, estimate)
    for name, content in files.items():
        if name != "coefficient_rows":
            (run_dir / name).write_text(content, encoding="utf-8")
    (run_dir / "hypothesis.yaml").write_bytes(spec_path.read_bytes())
    (run_dir / "coefficients.parquet").write_bytes(b"mock coefficients")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "registration_files", lambda: ("prereg", []))
    monkeypatch.setattr(runner, "calculate", lambda _study: (gate, source, label, reason, estimate))
    monkeypatch.setattr(runner, "_read_coefficients", lambda _path: files["coefficient_rows"])
    before = {p.name: p.read_bytes() for p in run_dir.iterdir()}
    assert runner.check_one(study)["wrote_files"] is False
    assert {p.name: p.read_bytes() for p in run_dir.iterdir()} == before

    card = run_dir / "result_card.md"
    card.write_bytes(card.read_bytes() + b"changed\n")
    tampered = {p.name: p.read_bytes() for p in run_dir.iterdir()}
    with pytest.raises(AssertionError, match="result_card.md"):
        runner.check_one(study)
    assert {p.name: p.read_bytes() for p in run_dir.iterdir()} == tampered
    card.write_bytes(before["result_card.md"])
    if study == "canada":
        changed = {**estimate, "canada_log_growth": 0.001}
    else:
        changed = {**estimate,
                   "quarter_medians_usd_bn": {**estimate["quarter_medians_usd_bn"],
                                              "2025Q1": 101.0}}
    monkeypatch.setattr(runner, "calculate", lambda _study: (
        gate, source, label, reason, changed
    ))
    with pytest.raises(AssertionError, match="diagnostics.json"):
        runner.check_one(study)
