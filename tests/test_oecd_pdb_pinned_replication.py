"""Historical OECD PDB replication must use the recorded inputs and be read-only."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from promote_oecd_pdb_batch03_2026_05_12 import reproduce_one  # noqa: E402


def test_reproduction_does_not_rewrite_frozen_spec_or_run():
    run_id = "oecd_pdb_gdp_hour_frontier_convergence_1950_2025"
    files = [ROOT / "hypotheses" / "growth" / f"{run_id}.yaml"]
    files += sorted((ROOT / "engine" / "runs" / run_id).glob("*"))
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files if path.is_file()}

    reproduced = reproduce_one(run_id)

    assert reproduced["status"] == "SUPPORTED"
    assert reproduced["n_obs"] == 1122
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before}
