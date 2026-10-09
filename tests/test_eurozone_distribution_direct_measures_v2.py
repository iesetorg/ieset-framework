"""Synthetic integrity checks; candidate outcome values are never read here."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "run_eurozone_distribution_direct_measures_v2.py"
SPEC = importlib.util.spec_from_file_location("run_eurozone_distribution_direct_measures_v2", MODULE)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def synthetic_rows(role: str, periphery_change: float = 0.0,
                   core_change: float = 0.0,
                   missing: tuple[str, int] | None = None) -> list[dict[str, Any]]:
    rows = []
    for country in runner.COUNTRIES:
        for year in runner.YEARS:
            change = periphery_change if country in runner.PERIPHERY else core_change
            value: float | None = 20.0 + (change if year == 2014 else 0.0)
            if (country, year) == missing:
                value = None
            rows.append({**runner.SOURCES[role]["dimensions"],
                         "geo_code": runner.GEO_CODES[country],
                         "period": str(year), "value": value})
    return rows


def test_frozen_spec_is_narrow_descriptive_calibration() -> None:
    spec = runner.validate_spec()
    assert spec["falsification"]["threshold"] == runner.THRESHOLD
    assert spec["status"] == "pre_registered"
    assert spec["evidence_type"] == "descriptive"
    assert spec["covers_claims"] == []
    assert "neither an out-of-time" in spec["methodology_note"]
    assert "no automatic" in spec["disclosure"]
    assert "survey waves" in spec["claim"]
    assert "income-share change at least 0.5 percentage points lower" in spec["claim"]
    assert "relative-poverty-rate change at least 2.0 percentage points higher" in spec["claim"]
    assert "Ireland used a rolling 12 months" in spec["methodology_note"]
    assert "status flags" in spec["disclosure"]
    assert runner.GEO_CODES["GRC"] == "EL"
    assert set(runner.GEO_CODES.values()) == {
        "EL", "ES", "PT", "IE", "IT", "AT", "BE", "DE", "FR", "FI", "NL"
    }


def test_preflight_reads_only_dimension_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, ...]] = []

    def keys(role: str, *, include_value: bool) -> list[dict[str, Any]]:
        assert include_value is False
        columns = runner.KEY_COLUMNS[role]
        seen.append(tuple(columns))
        return [{key: row[key] for key in columns}
                for row in synthetic_rows(role)]

    monkeypatch.setattr(runner, "verified_sources", lambda: runner.SOURCES)
    monkeypatch.setattr(runner, "read_candidate_rows", keys)
    gate, _ = runner.preflight()
    assert gate["country_year_keys_by_indicator"] == {
        "income_share": 22, "poverty_rate": 22,
    }
    assert gate["values_accessed"] is False
    assert gate["value_completeness_unchecked"] is True
    assert "survey-wave labels" in gate["period_semantics"]
    assert "not preserved" in gate["quality_flags"]
    assert len(seen) == 2


def test_duplicate_or_missing_structural_keys_fail() -> None:
    keys = [(country, year) for country in runner.COUNTRIES for year in runner.YEARS]
    with pytest.raises(ValueError, match="22 unique"):
        runner.complete_keys(keys[:-1], "income_share")
    with pytest.raises(ValueError, match="22 unique"):
        runner.complete_keys(keys + keys[:1], "poverty_rate")


@pytest.mark.parametrize(
    ("share_gap", "poverty_gap", "expected"),
    [(-0.5, 2.0, "SUPPORTED"), (0.5, -2.0, "REFUTED"),
     (-0.5, 1.99, "PARTIAL"), (0.0, 0.0, "PARTIAL"),
     (0.5, 2.0, "PARTIAL")],
)
def test_joint_directional_rule(share_gap: float, poverty_gap: float,
                                expected: str) -> None:
    assert runner.classify(share_gap, poverty_gap)[0] == expected


@pytest.mark.parametrize(
    ("share_change", "poverty_change", "expected"),
    [(-1.0, 3.0, "SUPPORTED"), (1.0, -3.0, "REFUTED"),
     (0.0, 1.0, "PARTIAL")],
)
def test_synthetic_endpoint_estimator(
    share_change: float, poverty_change: float, expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def values(role: str, *, include_value: bool) -> list[dict[str, Any]]:
        assert include_value is True
        change = share_change if role == "income_share" else poverty_change
        return synthetic_rows(role, periphery_change=change)

    monkeypatch.setattr(runner, "read_candidate_rows", values)
    monkeypatch.setattr(runner, "registration_files", lambda: ("first", []))
    label, _, estimate = runner.evaluate()
    assert label == expected
    assert estimate["n_complete_values"] == 44
    assert estimate["bottom_quintile_share_gap_pp"] == pytest.approx(share_change)
    assert estimate["relative_poverty_rate_gap_pp"] == pytest.approx(poverty_change)


def test_any_missing_value_is_inconclusive_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    def values(role: str, *, include_value: bool) -> list[dict[str, Any]]:
        assert include_value is True
        missing = ("GRC", 2008) if role == "income_share" else None
        return synthetic_rows(role, missing=missing)

    monkeypatch.setattr(runner, "read_candidate_rows", values)
    monkeypatch.setattr(runner, "registration_files", lambda: ("first", []))
    with pytest.raises(ValueError, match="missing value"):
        runner.evaluate()


def test_relative_support_does_not_require_absolute_deterioration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def values(role: str, *, include_value: bool) -> list[dict[str, Any]]:
        assert include_value is True
        if role == "income_share":
            return synthetic_rows(role, periphery_change=1.0, core_change=2.0)
        return synthetic_rows(role, periphery_change=-1.0, core_change=-4.0)

    monkeypatch.setattr(runner, "read_candidate_rows", values)
    monkeypatch.setattr(runner, "registration_files", lambda: ("first", []))
    label, _, estimate = runner.evaluate()
    assert label == "SUPPORTED"
    assert estimate["bottom_quintile_share_gap_pp"] == pytest.approx(-1.0)
    assert estimate["relative_poverty_rate_gap_pp"] == pytest.approx(3.0)


def test_run_requires_commit_before_preflight_or_values(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_registration() -> None:
        raise RuntimeError("registration not committed")

    def forbidden() -> None:
        raise AssertionError("candidate values reached")

    monkeypatch.setattr(runner, "registration_files", no_registration)
    monkeypatch.setattr(runner, "calculate", forbidden)
    with pytest.raises(RuntimeError, match="registration not committed"):
        runner.run_once()


def test_direct_evaluate_requires_commit_before_value_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_registration() -> None:
        raise RuntimeError("registration not committed")

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("candidate values reached")

    monkeypatch.setattr(runner, "registration_files", no_registration)
    monkeypatch.setattr(runner, "read_candidate_rows", forbidden)
    with pytest.raises(RuntimeError, match="registration not committed"):
        runner.evaluate()


def test_direct_value_reader_requires_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_registration() -> None:
        raise RuntimeError("registration not committed")

    monkeypatch.setattr(runner, "registration_files", no_registration)
    with pytest.raises(RuntimeError, match="registration not committed"):
        runner.read_candidate_rows("income_share", include_value=True)


def test_registration_rejects_changed_first_addition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = {}
    for relative in runner.REGISTRATION_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())
        payloads[relative] = path.read_bytes()
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def git(*args: str) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "show":
            revision, relative = args[1].split(":", 1)
            payload = payloads[relative]
            if revision == "first" and relative == runner.SPEC_REL:
                payload += b"\naltered"
            return subprocess.CompletedProcess(args, 0, payload, b"")
        if args[0] == "log":
            return subprocess.CompletedProcess(args, 0, b"first\n", b"")
        if args[0] == "ls-tree":
            return subprocess.CompletedProcess(args, 0, b"", b"")
        raise AssertionError(args)

    monkeypatch.setattr(runner, "_git", git)
    with pytest.raises(RuntimeError, match="changed since first addition"):
        runner.registration_files()


def test_registration_rejects_early_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = {}
    for relative in runner.REGISTRATION_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())
        payloads[relative] = path.read_bytes()
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def git(*args: str) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "show":
            return subprocess.CompletedProcess(
                args, 0, payloads[args[1].split(":", 1)[1]], b"")
        if args[0] == "log":
            return subprocess.CompletedProcess(args, 0, b"first\n", b"")
        if args[0] == "ls-tree":
            return subprocess.CompletedProcess(
                args, 0, f"{runner.RUN_REL}/diagnostics.json\n".encode(), b"")
        raise AssertionError(args)

    monkeypatch.setattr(runner, "_git", git)
    with pytest.raises(RuntimeError, match="artifacts existed"):
        runner.registration_files()


def test_read_only_replay_detects_packet_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / runner.RUN_REL
    run_dir.mkdir(parents=True)
    spec_path = tmp_path / runner.SPEC_REL
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / runner.SPEC_REL).read_bytes())
    gate = {"passed": True, "values_accessed": False}
    sources = runner.SOURCES
    label, reason = runner.classify(-1.0, 3.0)
    estimate = {
        "method": "synthetic", "n_countries": 11,
        "n_country_years_per_indicator": 22, "n_complete_values": 44,
        "group_means": {
            "income_share": {"periphery_mean_change_pp": -1.0,
                             "core_mean_change_pp": 0.0},
            "poverty_rate": {"periphery_mean_change_pp": 3.0,
                             "core_mean_change_pp": 0.0},
        },
        "bottom_quintile_share_gap_pp": -1.0,
        "relative_poverty_rate_gap_pp": 3.0,
        "country_changes_pp": {role: {c: 0.0 for c in runner.COUNTRIES}
                               for role in runner.ROLES},
    }
    packet = runner.artifacts("stamp", "first", [], gate, sources,
                              label, reason, estimate)
    assert "Wave labels: 2008 and 2014" in packet["result_card.md"]
    assert "status flags" in packet["result_card.md"]
    for name, contents in packet.items():
        if name != "coefficient_rows":
            (run_dir / name).write_text(contents, encoding="utf-8")
    (run_dir / "hypothesis.yaml").write_bytes(spec_path.read_bytes())
    runner.write_coefficients(run_dir / "coefficients.parquet",
                              packet["coefficient_rows"])
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "registration_files", lambda: ("first", []))
    monkeypatch.setattr(runner, "calculate", lambda: (
        gate, sources, label, reason, estimate))
    before = {p.name: p.read_bytes() for p in run_dir.iterdir()}
    assert runner.check_once()["verified"] is True
    assert {p.name: p.read_bytes() for p in run_dir.iterdir()} == before
    (run_dir / "result_card.md").write_text("tampered", encoding="utf-8")
    with pytest.raises(AssertionError, match="packet differs"):
        runner.check_once()
