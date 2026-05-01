#!/usr/bin/env python3
"""Replication script for norway_gpfg_resource_curse_avoidance."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CMD = [str(ROOT / "venv/bin/python"), str(ROOT / "scripts/run_synth_did.py"), "norway_gpfg_resource_curse_avoidance", "--force"]

if __name__ == "__main__":
    raise SystemExit(subprocess.run(CMD, cwd=ROOT).returncode)
