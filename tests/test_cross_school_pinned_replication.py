"""Cross-school historical replay must use frozen sources and leave packets intact."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import promote_cross_school_next50_2026_05_12 as batch  # noqa: E402

WRAPPERS = sorted(
    path for path in (ROOT / "engine" / "runs").glob("cross_school_*/replication.py")
    if "from promote_cross_school_next50_2026_05_12 import reproduce_one" in path.read_text()
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("wrapper", WRAPPERS, ids=lambda path: path.parent.name)
def test_frozen_packet_structure_and_local_source_hashes(wrapper: Path) -> None:
    assert len(WRAPPERS) == 25
    hid = wrapper.parent.name
    case, stored, manifest, pinned = batch.pinned_packet(hid)
    assert case["hid"] == hid
    assert stored["verdict"] == manifest["verdict_label"]
    assert f"reproduce_one('{hid}')" in wrapper.read_text()
    assert "subprocess" not in wrapper.read_text()
    for key, path in pinned.items():
        if path.is_file():
            assert digest(path) == manifest["vintages"][key]["sha256"]


def test_replay_is_read_only_when_local_vintages_exist() -> None:
    hid = "cross_school_capital_openness_fdi_1990_2023"
    _, _, _, pinned = batch.pinned_packet(hid)
    if not all(path.is_file() for path in pinned.values()):
        pytest.skip("the ignored pinned raw vintages are not installed")
    run_dir = ROOT / "engine" / "runs" / hid
    before = {path.name: digest(path) for path in run_dir.iterdir() if path.is_file()}
    result = batch.reproduce_one(hid)
    after = {path.name: digest(path) for path in run_dir.iterdir() if path.is_file()}
    assert result == {"hypothesis_id": hid, "verdict": "PARTIAL", "verified": True, "artifacts_written": False}
    assert after == before


def test_canonical_verdict_drift_is_rejected_without_raw_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hid = "cross_school_capital_openness_fdi_1990_2023"
    original = ROOT / "engine" / "runs" / hid
    test_run = tmp_path / hid
    test_run.mkdir()
    shutil.copy2(original / "manifest.yaml", test_run / "manifest.yaml")
    diagnostics = json.loads((original / "diagnostics.json").read_text())
    diagnostics["verdict"] = "SUPPORTED"
    (test_run / "diagnostics.json").write_text(json.dumps(diagnostics))
    monkeypatch.setattr(batch, "RUNS", tmp_path)
    with pytest.raises(ValueError, match="canonical verdict"):
        batch.pinned_packet(hid)
