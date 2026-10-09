#!/usr/bin/env python3
"""Replay both frozen V-Dem/WDI results from their pinned source lock."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / "scripts/run_vdem_wdi_distinct_mechanisms_2026.py"), "--verify"], cwd=root))
