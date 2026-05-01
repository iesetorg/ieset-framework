#!/usr/bin/env python3
"""Replication script for industrial_policy_governance_capacity_conditionality."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CMD = [
    str(ROOT / "venv/bin/python"),
    str(ROOT / "scripts/run_panel_fe.py"),
    'industrial_policy_governance_capacity_conditionality',
    '--force',
]

if __name__ == "__main__":
    raise SystemExit(subprocess.run(CMD, cwd=ROOT).returncode)
