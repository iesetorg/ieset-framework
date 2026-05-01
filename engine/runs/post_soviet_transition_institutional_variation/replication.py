#!/usr/bin/env python3
"""Replication script for post_soviet_transition_institutional_variation."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CMD = [str(ROOT / "venv/bin/python"), str(ROOT / "scripts/run_panel_fe.py"), "post_soviet_transition_institutional_variation", "--force"]

if __name__ == "__main__":
    raise SystemExit(subprocess.run(CMD, cwd=ROOT).returncode)
