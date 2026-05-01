#!/usr/bin/env python3
"""Replication script for fiscal_dominance_japan_debt_non_crisis."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CMD = [
    str(ROOT / "venv/bin/python"),
    str(ROOT / "scripts/run_multi_metric_checklist.py"),
    "fiscal_dominance_japan_debt_non_crisis",
    "--force",
]

if __name__ == "__main__":
    raise SystemExit(subprocess.run(CMD, cwd=ROOT).returncode)
