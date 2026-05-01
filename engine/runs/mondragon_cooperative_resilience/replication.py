#!/usr/bin/env python3
"""Replication script for mondragon_cooperative_resilience."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CMD = [
    str(ROOT / "venv/bin/python"),
    str(ROOT / "scripts/run_multi_metric_checklist.py"),
    'mondragon_cooperative_resilience',
    '--force',
]

if __name__ == "__main__":
    raise SystemExit(subprocess.run(CMD, cwd=ROOT).returncode)
