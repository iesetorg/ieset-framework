"""Structural and replay gates for the three prospective panel holdouts."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "run_legacy_panel_geographic_holdouts_v2.py"
SPEC = importlib.util.spec_from_file_location("run_legacy_panel_geographic_holdouts_v2", MODULE)
assert SPEC is not None and SPEC.loader is not None
holdouts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(holdouts)


def test_three_registered_claims_and_machine_checked_old_rosters() -> None:
    assert len(holdouts.COHORT) == 3
    assert len(holdouts.COHORT) * holdouts.FAMILY_P_MAX == pytest.approx(0.10)
    for hypothesis_id, config in holdouts.COHORT.items():
        spec_path, steelman_path, _ = holdouts.paths(hypothesis_id)
        spec = yaml.safe_load((holdouts.ROOT / spec_path).read_text(encoding="utf-8"))
        threshold = spec["falsification"]["threshold"]
        assert threshold["old_country_ids"] == sorted(config["old_countries"])
        assert threshold["old_country_count"] == len(config["old_countries"])
        assert threshold["family_id"] == holdouts.FAMILY_ID
        assert threshold["family_size"] == 3
        assert threshold["family_p_max"] == holdouts.FAMILY_P_MAX
        assert spec["status"] == "pre_registered"
        assert spec["covers_claims"] == []
        assert (holdouts.ROOT / steelman_path).is_file()


def test_historical_runner_restricted_each_old_fit_to_old_spec_roster() -> None:
    for config in holdouts.COHORT.values():
        revision = config["old_run_commit"]
        old_path = f"hypotheses/{config['topic']}/{config['old_id']}.yaml"
        old_spec = yaml.safe_load(holdouts.git_show(revision, old_path))
        old_runner = holdouts.git_show(revision, "scripts/run_panel_fe.py").decode()
        old_diagnostics = json.loads(holdouts.git_show(
            revision, f"engine/runs/{config['old_id']}/diagnostics.json"
        ))
        assert set(old_spec["sample"]["countries"]) == config["old_countries"]
        assert 'out = out[out["country_iso3"].isin(countries)]' in old_runner
        assert "panel_filt = filter_sample(panel, spec)" in old_runner
        assert "est = run_panel_ols(\n        panel_filt," in old_runner
        assert old_diagnostics["estimate"]["n_countries"] <= len(config["old_countries"])


def test_family_rule_is_sign_symmetric_and_has_no_free_component_verdict() -> None:
    p = holdouts.FAMILY_P_MAX
    assert holdouts.classify(0.1, p)[0] == "SUPPORTED"
    assert holdouts.classify(-0.1, p)[0] == "REFUTED"
    assert holdouts.classify(0.1, p + 1e-5)[0] == "PARTIAL"
    assert holdouts.classify(-0.1, p + 1e-5)[0] == "PARTIAL"


def test_preflight_parquet_projection_excludes_all_value_columns() -> None:
    tree = ast.parse(inspect.getsource(holdouts.load_keys))
    reads = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "read_parquet"]
    assert len(reads) == 1
    columns = next(keyword.value for keyword in reads[0].keywords if keyword.arg == "columns")
    assert ast.literal_eval(columns) == ["country_iso3", "year"]
    assert not any(isinstance(node, ast.Constant) and node.value == "value"
                   for node in ast.walk(tree))


def test_coverage_requires_literal_next_calendar_year_and_five_pairs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hypothesis_id = "fraser_freedom_forward_income_geographic_holdout_v2"
    sources = {role: {"source": role} for role in holdouts.COHORT[hypothesis_id]["sources"]}
    treatment_years = {("ALB", year) for year in range(2000, 2008)}
    treatment_years |= {("BGR", year) for year in range(2000, 2004)}
    outcome_years = {("ALB", year) for year in range(2000, 2009) if year != 2003}
    outcome_years |= {("BGR", year) for year in range(2000, 2005)}
    keys = {role: treatment_years for role in sources}
    keys["outcome"] = outcome_years
    keys["legal_sensitivity"] = set()
    keys["sound_money_sensitivity"] = set()
    monkeypatch.setattr(holdouts, "load_keys", lambda record, old: keys[record["source"]])
    complete = holdouts.complete_keys(hypothesis_id, sources)
    assert complete == {(country, year) for country in ("ALB",) for year in (2000, 2001, 2004, 2005, 2006, 2007)}
    assert ("ALB", 2002) not in complete  # The t+1 observation is absent.
    assert not any(country == "BGR" for country, _ in complete)  # Only four pairs.


def test_run_stops_before_any_estimation_without_preregistration(monkeypatch: pytest.MonkeyPatch) -> None:
    hypothesis_id = next(iter(holdouts.COHORT))

    def no_registration() -> str:
        raise RuntimeError("registration is not committed")

    def forbidden_estimate(*args: object, **kwargs: object) -> None:
        raise AssertionError("outcome estimation was reached")

    monkeypatch.setattr(holdouts, "registration_commit", no_registration)
    monkeypatch.setattr(holdouts, "estimate_one", forbidden_estimate)
    with pytest.raises(RuntimeError, match="registration is not committed"):
        holdouts.run_one(hypothesis_id)


def test_registration_rejects_post_addition_edits_even_when_head_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = [holdouts.RUNNER_REL]
    for hypothesis_id in holdouts.COHORT:
        files.extend(holdouts.paths(hypothesis_id)[:2])
    first_file = files[0]

    def fake_show(revision: str, relative: str) -> bytes:
        current = (holdouts.ROOT / relative).read_bytes()
        return current + b"\n# later edit\n" if revision == "first-add" and relative == first_file else current

    def fake_run(args: list[str], **_kwargs: object) -> SimpleNamespace:
        assert args[:3] == ["git", "log", "--diff-filter=A"]
        return SimpleNamespace(returncode=0, stdout="first-add\n")

    monkeypatch.setattr(holdouts, "git_show", fake_show)
    monkeypatch.setattr(holdouts.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="registration bytes differ from first addition"):
        holdouts.registration_commit()


def test_read_only_check_preserves_packet_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hypothesis_id = next(iter(holdouts.COHORT))
    spec_path, _, run_rel = holdouts.paths(hypothesis_id)
    run_dir = tmp_path / run_rel
    run_dir.mkdir(parents=True)
    (tmp_path / spec_path).parent.mkdir(parents=True)
    (tmp_path / spec_path).write_bytes((holdouts.ROOT / spec_path).read_bytes())
    source = {"outcome": {"source": "synthetic", "vintage_file": "synthetic.parquet", "sha256": "x"}}
    gate = {"observations": 2000, "countries": 100, "old_country_overlap": 0,
            "treatment_years": [2000, 2021], "passed": True}
    estimate = {"coefficient": 0.2, "std_error": 0.05, "p_value": 0.01,
                "r_squared": 0.2, "ci95": [0.1, 0.3], "n_obs": 2000,
                "n_countries": 100,
                "method": "country/year FE OLS, country-clustered standard errors"}
    diagnostic, manifest, packet, card, wrapper, chart, rows = holdouts.artifact_records(
        hypothesis_id, "prereg", source, gate, "SUPPORTED", "synthetic match",
        estimate, "2026-10-09T00:00:00+00:00",
    )
    (run_dir / "hypothesis.yaml").write_bytes((tmp_path / spec_path).read_bytes())
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostic), encoding="utf-8")
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "replication.py").write_text(wrapper, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart), encoding="utf-8")
    (run_dir / "coefficients.parquet").write_bytes(b"synthetic parquet fixture")
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in run_dir.iterdir()}
    monkeypatch.setattr(holdouts, "ROOT", tmp_path)
    monkeypatch.setattr(holdouts, "registration_commit", lambda: "prereg")
    monkeypatch.setattr(holdouts, "validate_spec", lambda _: {})
    monkeypatch.setattr(holdouts, "verified_sources", lambda *_: source)
    def read_synthetic_coefficients(path: Path) -> list[dict[str, object]]:
        if path.read_bytes() != b"synthetic parquet fixture":
            raise AssertionError("coefficients parquet mismatch")
        return rows

    monkeypatch.setattr(holdouts, "read_coefficient_rows", read_synthetic_coefficients)
    monkeypatch.setattr(holdouts, "estimate_one", lambda *_: (
        gate, "SUPPORTED", "synthetic match", estimate,
    ))
    assert holdouts.check_one(hypothesis_id)["wrote_files"] is False
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in run_dir.iterdir()}
    assert after == before

    for changed, mismatch in (
        ({**estimate, "coefficient": 0.25}, "coefficient mismatch"),
        ({**estimate, "n_obs": 2001}, "n_obs mismatch"),
        ({**estimate, "n_countries": 101}, "n_countries mismatch"),
        ({**estimate, "method": "unclustered OLS"}, "method mismatch"),
        ({**estimate, "ci95": [0.1, 0.2, 0.3]}, "ci95 length mismatch"),
    ):
        monkeypatch.setattr(holdouts, "estimate_one", lambda *_, changed=changed: (
            gate, "SUPPORTED", "synthetic match", changed,
        ))
        with pytest.raises(AssertionError, match=mismatch):
            holdouts.check_one(hypothesis_id)
    monkeypatch.setattr(holdouts, "estimate_one", lambda *_: (
        gate, "SUPPORTED", "synthetic match", estimate,
    ))
    for filename, suffix in (
        ("manifest.yaml", b"\ncorrupt: true\n"),
        ("evidence_packet.yaml", b"\ncorrupt: true\n"),
        ("result_card.md", b"\ncorrupt\n"),
        ("chart_data.json", b"\n"),
        ("coefficients.parquet", b"\ncorrupt\n"),
    ):
        path = run_dir / filename
        original = path.read_bytes()
        path.write_bytes(original + suffix)
        if filename == "chart_data.json":
            # JSON whitespace alone is not substantive; alter a stored number.
            path.write_text(json.dumps({**chart, "coefficient": 0.25}), encoding="utf-8")
        with pytest.raises(AssertionError):
            holdouts.check_one(hypothesis_id)
        path.write_bytes(original)
    assert {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in run_dir.iterdir()} == before
