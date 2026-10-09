"""Registration, key-only preflight, and equivalence gates for the hours holdout."""

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
MODULE = ROOT / "scripts" / "run_working_time_employment_oecd_geographic_holdout_v2.py"
SPEC = importlib.util.spec_from_file_location("run_working_time_holdout", MODULE)
assert SPEC is not None and SPEC.loader is not None
holdout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(holdout)


def test_country_disjoint_registration_and_historical_filter() -> None:
    spec = holdout.validate_spec()
    assert len(holdout.OLD_COUNTRIES) == 23
    assert len(holdout.HOLDOUT_COUNTRIES) == 15
    assert not (holdout.OLD_COUNTRIES & holdout.HOLDOUT_COUNTRIES)
    assert spec["covers_claims"] == []
    assert spec["evidence_type"] == "associational"
    assert "FRA" not in spec["sample"]["countries"]
    threshold = spec["falsification"]["threshold"]
    assert threshold["old_run_commit"] == holdout.OLD_COMMIT
    assert threshold["old_country_ids"] == sorted(holdout.OLD_COUNTRIES)
    assert threshold["holdout_country_ids"] == sorted(holdout.HOLDOUT_COUNTRIES)


def test_preflight_projects_only_country_and_year_keys() -> None:
    tree = ast.parse(inspect.getsource(holdout.load_keys))
    reads = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "read_table"
    ]
    assert len(reads) == 1
    columns = next(keyword.value for keyword in reads[0].keywords if keyword.arg == "columns")
    assert ast.literal_eval(columns) == ["country_iso3", "year"]
    assert not any(
        isinstance(node, ast.Constant) and node.value in {"value", "avh"}
        for node in ast.walk(tree)
    )


def test_key_envelope_requires_all_six_sources_and_eight_years(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    common = {("CZE", year) for year in range(2000, 2009)}
    too_short = {("EST", year) for year in range(2000, 2007)}
    record_sets = {role: common | too_short for role in holdout.ROLES}
    record_sets["services"] -= {("CZE", 2004)}
    monkeypatch.setattr(holdout, "load_keys", lambda record: record_sets[record["role"]])
    records = {role: {"role": role} for role in holdout.ROLES}
    keys = holdout.key_envelope(records)
    assert len(keys) == 8
    assert {country for country, _ in keys} == {"CZE"}
    assert ("CZE", 2004) not in keys


def test_equivalence_requires_interval_inside_margin() -> None:
    assert holdout.classify([-0.2, 0.2], 0.2)[0] == "SUPPORTED"
    assert holdout.classify([-0.6, 0.2], 0.4)[0] == "PARTIAL"
    assert holdout.classify([0.6, 0.9], 0.15)[0] == "REFUTED"
    assert holdout.classify([-0.9, -0.6], 0.15)[0] == "REFUTED"
    assert holdout.classify([-0.6, 0.6], 0.6)[0] == "INCONCLUSIVE"
    assert holdout.classify([-0.5, 0.4], 0.45)[0] == "PARTIAL"


def test_run_cannot_reach_values_without_preregistration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_registration() -> str:
        raise RuntimeError("registration missing")

    def no_estimate(*_args: object) -> None:
        raise AssertionError("held-out values reached")

    monkeypatch.setattr(holdout, "registration_commit", no_registration)
    monkeypatch.setattr(holdout, "estimate_one", no_estimate)
    with pytest.raises(RuntimeError, match="registration missing"):
        holdout.run_one()


def test_registration_rejects_post_addition_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_show(revision: str, relative: str) -> bytes:
        current = (ROOT / relative).read_bytes()
        if revision == "first-add" and relative == holdout.STEELMAN_REL:
            return current + b"\npost-result edit\n"
        return current

    def fake_run(args: list[str], **_kwargs: object) -> SimpleNamespace:
        assert args[:3] == ["git", "log", "--diff-filter=A"]
        return SimpleNamespace(returncode=0, stdout="first-add\n")

    monkeypatch.setattr(holdout, "git_show", fake_show)
    monkeypatch.setattr(holdout.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="bytes differ from first addition"):
        holdout.registration_commit()


def test_source_manifest_pins_match_registered_paths() -> None:
    spec = yaml.safe_load((ROOT / holdout.SPEC_REL).read_text(encoding="utf-8"))
    manifest = yaml.safe_load((ROOT / holdout.SOURCE_MANIFEST).read_text(encoding="utf-8"))
    indexed = {(entry["parquet_path"], entry["sha256"]) for entry in manifest["entries"]
               if entry.get("parquet_path") and entry.get("sha256")}
    pins = spec["falsification"]["threshold"]["source_files"]
    assert set(pins) == set(holdout.ROLES)
    for pin in pins.values():
        assert (pin["path"], pin["sha256"]) in indexed
        assert pin["source_manifest"] == holdout.SOURCE_MANIFEST


def test_read_only_replay_compares_stored_packet_and_estimate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / holdout.RUN_REL
    run_dir.mkdir(parents=True)
    spec_path = tmp_path / holdout.SPEC_REL
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / holdout.SPEC_REL).read_bytes())
    sources = {role: {"source": role, "vintage_file": f"{role}.parquet",
                      "sha256": role, "source_manifest": holdout.SOURCE_MANIFEST}
               for role in holdout.ROLES}
    gate = {"observations": 200, "countries": 11, "min_years_per_country": 8,
            "old_country_overlap": 0, "years": [1990, 2019], "sample_passed": True,
            "source_custody_verified": True, "outcome_values_loaded": True,
            "value_read_attempted": True, "estimation_attempted": True,
            "failure": None}
    estimate = {"coefficient": 0.1, "std_error": 0.1, "p_value": 0.3,
                "ci90": [-0.1, 0.3], "ci90_half_width": 0.2,
                "n_obs": 200, "n_countries": 11, "r_squared": 0.2,
                "method": "country/year FE OLS; country-clustered CR1; t interval df=clusters-1",
                "gfc_2008_2010_exclusion_sensitivity": {"verdict": None}}
    stamp = "2026-10-09T00:00:00+00:00"
    records = holdout.artifact_records("prereg", sources, gate, "SUPPORTED", "inside", estimate, stamp)
    diagnostics, manifest, packet, card, wrapper, chart, coefficients = records
    (run_dir / "hypothesis.yaml").write_bytes(spec_path.read_bytes())
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics), encoding="utf-8")
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "replication.py").write_text(wrapper, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart), encoding="utf-8")
    (run_dir / "coefficients.parquet").write_bytes(b"synthetic fixture")
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in run_dir.iterdir()}
    monkeypatch.setattr(holdout, "ROOT", tmp_path)
    monkeypatch.setattr(holdout, "registration_commit", lambda: "prereg")
    monkeypatch.setattr(holdout, "validate_spec", lambda: {})
    monkeypatch.setattr(holdout, "verified_sources", lambda _: sources)
    monkeypatch.setattr(holdout, "key_envelope", lambda _: set())
    monkeypatch.setattr(holdout, "read_coefficient_rows", lambda _: coefficients)
    monkeypatch.setattr(holdout, "estimate_one", lambda _: (gate, "SUPPORTED", "inside", estimate))
    assert holdout.check_one()["wrote_files"] is False
    assert {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in run_dir.iterdir()} == before
    (run_dir / "chart_data.json").write_text(json.dumps({**chart, "coefficient": 0.25}))
    with pytest.raises(AssertionError):
        holdout.check_one()


def test_source_failure_persists_unverified_packet_and_replays_without_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / holdout.SPEC_REL
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / holdout.SPEC_REL).read_bytes())
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    monkeypatch.setattr(holdout, "ROOT", tmp_path)
    monkeypatch.setattr(holdout, "registration_commit", lambda: "prereg")
    monkeypatch.setattr(holdout, "validate_spec", lambda: spec)

    def bad_custody(_: object) -> None:
        raise ValueError("source SHA-256 mismatch: fixture")

    monkeypatch.setattr(holdout, "verified_sources", bad_custody)
    monkeypatch.setattr(holdout, "estimate_one", lambda _: (_ for _ in ()).throw(
        AssertionError("estimation reached after source failure")
    ))
    result = holdout.run_one()
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["evidence_state"] == "UNVERIFIED_INCONCLUSIVE"
    run_dir = tmp_path / holdout.RUN_REL
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    assert diagnostics["preflight"]["failure"]["phase"] == "source_custody"
    assert diagnostics["preflight"]["outcome_values_loaded"] is False
    assert diagnostics["preflight"]["estimation_attempted"] is False
    assert diagnostics["data_status"]["source_custody_verified"] is False
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run_dir.iterdir()}
    replay = holdout.check_one()
    assert replay["failure_reproduced"] and not replay["wrote_files"]
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run_dir.iterdir()} == before


@pytest.mark.parametrize("phase", ["key_preflight", "panel_construction"])
def test_early_failure_replay_never_fits(
    phase: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / holdout.SPEC_REL
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / holdout.SPEC_REL).read_bytes())
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    monkeypatch.setattr(holdout, "ROOT", tmp_path)
    monkeypatch.setattr(holdout, "registration_commit", lambda: "prereg")
    monkeypatch.setattr(holdout, "validate_spec", lambda: spec)
    monkeypatch.setattr(holdout, "verified_sources", lambda _: holdout.declared_sources(spec, "verified"))
    if phase == "key_preflight":
        def bad_keys(_: object) -> None:
            raise ValueError("duplicate country-year keys: fixture")
        monkeypatch.setattr(holdout, "key_envelope", bad_keys)
        monkeypatch.setattr(holdout, "estimate_one", lambda _: (_ for _ in ()).throw(
            AssertionError("estimation reached after key failure")
        ))
    else:
        keys = {(country, year) for country in sorted(holdout.HOLDOUT_COUNTRIES)[:10]
                for year in range(2000, 2015)}
        monkeypatch.setattr(holdout, "key_envelope", lambda _: keys)
        def bad_panel(_: object) -> None:
            raise KeyError("avh")
        monkeypatch.setattr(holdout, "build_panel", bad_panel)
        monkeypatch.setattr(holdout, "fit_model", lambda _: (_ for _ in ()).throw(
            AssertionError("fit reached after panel failure")
        ))
    assert holdout.run_one()["evidence_state"] == "UNVERIFIED_INCONCLUSIVE"
    run_dir = tmp_path / holdout.RUN_REL
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    assert diagnostics["preflight"]["failure"]["phase"] == phase
    assert diagnostics["preflight"]["estimation_attempted"] is False
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run_dir.iterdir()}
    assert holdout.check_one()["failure_reproduced"]
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run_dir.iterdir()} == before


def test_packet_is_complete_before_atomic_publish_and_failed_rename_cleans_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / holdout.SPEC_REL
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / holdout.SPEC_REL).read_bytes())
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    sources = holdout.declared_sources(spec, "unverified")
    gate = holdout.unverified_gate("source_custody", ValueError("fixture"), False, False)
    monkeypatch.setattr(holdout, "ROOT", tmp_path)
    real_replace = holdout.os.replace
    required = {
        "hypothesis.yaml", "diagnostics.json", "manifest.yaml",
        "evidence_packet.yaml", "result_card.md", "replication.py",
        "chart_data.json", "coefficients.parquet",
    }

    def interrupted_replace(source: str | Path, target: str | Path) -> None:
        assert {p.name for p in Path(source).iterdir()} == required
        assert not Path(target).exists()
        raise OSError("interrupted publish")

    monkeypatch.setattr(holdout.os, "replace", interrupted_replace)
    with pytest.raises(OSError, match="interrupted publish"):
        holdout.write_run("prereg", sources, gate, "INCONCLUSIVE", "fixture", None)
    assert not (tmp_path / holdout.RUN_REL).exists()
    assert not list((tmp_path / "engine" / "runs").glob(f".{holdout.HID}.tmp-*"))

    def complete_replace(source: str | Path, target: str | Path) -> None:
        assert {p.name for p in Path(source).iterdir()} == required
        assert not Path(target).exists()
        real_replace(source, target)

    monkeypatch.setattr(holdout.os, "replace", complete_replace)
    holdout.write_run("prereg", sources, gate, "INCONCLUSIVE", "fixture", None)
    assert {p.name for p in (tmp_path / holdout.RUN_REL).iterdir()} == required


def test_packet_write_failure_cleans_stage_and_allows_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pandas as pd

    spec_path = tmp_path / holdout.SPEC_REL
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((ROOT / holdout.SPEC_REL).read_bytes())
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    sources = holdout.declared_sources(spec, "unverified")
    gate = holdout.unverified_gate("source_custody", ValueError("fixture"), False, False)
    monkeypatch.setattr(holdout, "ROOT", tmp_path)
    original_writer = pd.DataFrame.to_parquet

    def interrupted_write(self: pd.DataFrame, path: Path, **kwargs: object) -> None:
        Path(path).write_bytes(b"partial parquet")
        raise OSError("interrupted artifact write")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", interrupted_write)
    with pytest.raises(OSError, match="interrupted artifact write"):
        holdout.write_run("prereg", sources, gate, "INCONCLUSIVE", "fixture", None)
    assert not (tmp_path / holdout.RUN_REL).exists()
    assert not list((tmp_path / "engine" / "runs").glob(f".{holdout.HID}.tmp-*"))

    monkeypatch.setattr(pd.DataFrame, "to_parquet", original_writer)
    holdout.write_run("prereg", sources, gate, "INCONCLUSIVE", "fixture", None)
    assert (tmp_path / holdout.RUN_REL / "coefficients.parquet").is_file()
