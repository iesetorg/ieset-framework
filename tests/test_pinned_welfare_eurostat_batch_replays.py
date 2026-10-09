"""Batch 06-09 historical replication uses recorded vintages without writes."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from promote_eurostat_energy_batch06_2026_05_12 import reproduce_one as replay_eurostat  # noqa: E402
from promote_welfare_labour_minwage_batches_07_09_a4_2026_05_12 import reproduce_one as replay_welfare  # noqa: E402

WELFARE_IDS = (
    "oecd_socx_public_social_spending_employment_tradeoff",
    "oecd_socx_open_economy_welfare_compatibility_panel",
    "oecd_epl_low_education_unemployment_panel_1985_2019",
    "oecd_low_education_unemployment_minimum_wage_bite",
    "oecd_activation_spending_low_education_unemployment",
    "bls_qcew_county_food_service_minimum_wage_growth",
    "bls_qcew_state_food_service_minimum_wage_growth",
    "bls_oews_median_bite_food_service_employment_panel",
    "bls_minimum_wage_bite_low_tail_threshold_panel",
)
EUROSTAT_IDS = (
    "eurostat_electricity_price_inflation_pass_through",
    "eurostat_nuclear_retention_industrial_price_panel",
    "eurostat_renewable_share_electricity_price_transition_cost",
    "eurostat_energy_price_unemployment_regional_panel",
    "eurostat_electricity_price_volatility_industrial_exit",
    "eurostat_energy_price_services_vs_industry_reallocation",
)
ALL_IDS = WELFARE_IDS + EUROSTAT_IDS
VINTAGES = (ROOT / "data" / "vintages").resolve()


def packet_hashes(run_dir: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in run_dir.iterdir()
        if path.is_file()
    }


def pinned_paths(run_id: str) -> list[Path]:
    manifest_path = ROOT / "engine" / "runs" / run_id / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    assert manifest.get("hypothesis_id") == run_id
    assert isinstance(manifest.get("vintages"), dict) and manifest["vintages"]
    paths = []
    for source in manifest["vintages"].values():
        raw_path, expected_hash = source.get("vintage_file"), source.get("sha256")
        assert isinstance(raw_path, str) and isinstance(expected_hash, str)
        assert re.fullmatch(r"[0-9a-f]{64}", expected_hash)
        path = (ROOT / raw_path).resolve()
        path.relative_to(VINTAGES)
        assert path.suffix == ".parquet" and "@" in path.stem
        if "publisher" in source:
            assert path.parent.name == source["publisher"]
            assert path.name.startswith(f"{source['series']}@")
        if path.is_file():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
        paths.append(path)
    return paths


def require_local_vintages(paths: list[Path]) -> None:
    if any(not path.is_file() for path in paths):
        pytest.skip("ignored pinned raw vintages are absent from this checkout")


@pytest.mark.parametrize("run_id", ALL_IDS)
def test_pinned_batch_packet_and_manifest_structure(run_id: str) -> None:
    run_dir = ROOT / "engine" / "runs" / run_id
    wrapper = (run_dir / "replication.py").read_text(encoding="utf-8")
    assert "reproduce_one" in wrapper
    assert f"reproduce_one('{run_id}')" in wrapper
    assert "subprocess.call" not in wrapper
    assert "main()" not in wrapper
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text(encoding="utf-8")) or {}
    assert diagnostics["hypothesis_id"] == run_id
    assert diagnostics["verdict"] == diagnostics["verdict_label"] == manifest["verdict_label"]
    assert diagnostics["formula"] == manifest["formula"]
    assert diagnostics["run_utc"] == manifest["run_utc"]
    assert diagnostics["verdict_label"] in {"SUPPORTED", "PARTIAL", "REFUTED"}
    for name in ("coefficients.parquet", "chart_data.json", "result_card.md"):
        assert (run_dir / name).is_file() and (run_dir / name).stat().st_size > 0
    json.loads((run_dir / "chart_data.json").read_text(encoding="utf-8"))
    pinned_paths(run_id)


@pytest.mark.parametrize("run_id", ALL_IDS)
def test_pinned_batch_replay_matches_packet_without_writes(run_id: str) -> None:
    require_local_vintages(pinned_paths(run_id))
    run_dir = ROOT / "engine" / "runs" / run_id
    before = packet_hashes(run_dir)

    replay = replay_welfare if run_id in WELFARE_IDS else replay_eurostat
    result = replay(run_id)

    assert result["verdict_label"] in {"SUPPORTED", "PARTIAL", "REFUTED"}
    assert packet_hashes(run_dir) == before


@pytest.mark.parametrize(
    "run_id,replay",
    [
        (WELFARE_IDS[0], replay_welfare),
        (EUROSTAT_IDS[0], replay_eurostat),
    ],
)
def test_pinned_batch_replay_rejects_changed_source_hash_and_stored_verdict(
    run_id: str, replay, tmp_path: Path,
) -> None:
    require_local_vintages(pinned_paths(run_id))
    source = ROOT / "engine" / "runs" / run_id
    scratch = tmp_path / run_id
    scratch.mkdir()
    for name in (
        "manifest.yaml", "diagnostics.json", "coefficients.parquet",
        "chart_data.json", "result_card.md", "evidence_packet.yaml",
    ):
        path = source / name
        if path.is_file():
            shutil.copy2(path, scratch / name)

    manifest_path = scratch / "manifest.yaml"
    original_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    first = next(iter(manifest["vintages"].values()))
    first["sha256"] = "0" * 64
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        replay(run_id, scratch)

    manifest_path.write_text(yaml.safe_dump(original_manifest), encoding="utf-8")
    diagnostics_path = scratch / "diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    diagnostics["verdict_label"] = "REFUTED" if diagnostics["verdict_label"] != "REFUTED" else "SUPPORTED"
    diagnostics_path.write_text(json.dumps(diagnostics), encoding="utf-8")
    with pytest.raises(ValueError, match="verdict_label"):
        replay(run_id, scratch)


def test_full_replay_skips_when_a_pinned_raw_vintage_is_absent(monkeypatch) -> None:
    original_is_file = Path.is_file
    monkeypatch.setattr(
        Path, "is_file",
        lambda path: False if path.resolve().is_relative_to(VINTAGES) else original_is_file(path),
    )
    test_pinned_batch_packet_and_manifest_structure(WELFARE_IDS[0])
    with pytest.raises(pytest.skip.Exception, match="ignored pinned raw vintages"):
        test_pinned_batch_replay_matches_packet_without_writes(WELFARE_IDS[0])
