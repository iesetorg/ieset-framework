#!/usr/bin/env python3
"""Replay the exact frozen preflight for privatisation_transition_tfp_panel."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HYPOTHESIS_ID = "privatisation_transition_tfp_panel"
RUNNER = "scripts/rerun_privatisation_transition_tfp_frozen.py"

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    raise SystemExit(subprocess.call(
        [sys.executable, str(root / RUNNER), HYPOTHESIS_ID, "--check"], cwd=root,
    ))
