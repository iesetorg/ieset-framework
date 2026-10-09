"""Pinned Eurostat run wrappers verify historical results without writing."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN_IDS = (
    "eurostat_energy_price_export_competitiveness_panel",
    "eurostat_industrial_electricity_price_manufacturing_va_2007_2025",
)


def load_wrapper(run_id: str):
    path = ROOT / "engine" / "runs" / run_id / "replication.py"
    spec = importlib.util.spec_from_file_location(f"replication_{run_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("run_id", RUN_IDS)
def test_pinned_replay_is_read_only_and_rejects_stored_verdict_drift(
    run_id: str, tmp_path: Path,
) -> None:
    wrapper = load_wrapper(run_id)
    run_dir = ROOT / "engine" / "runs" / run_id
    packet = [run_dir / name for name in (
        "diagnostics.json", "manifest.yaml", "coefficients.parquet",
        "chart_data.json", "result_card.md",
    )]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in packet}
    assert wrapper.main() == 0
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in packet}

    # A changed result label must fail even when the pinned vintage still loads.
    scratch = tmp_path / run_id
    scratch.mkdir()
    shutil.copy2(run_dir / "coefficients.parquet", scratch / "coefficients.parquet")
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text())
    diagnostics["verdict_label"] = "SUPPORTED"
    (scratch / "diagnostics.json").write_text(json.dumps(diagnostics))
    wrapper.RUN_DIR = scratch
    with pytest.raises(ValueError, match="verdict_label"):
        wrapper.main()
