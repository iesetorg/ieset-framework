#!/usr/bin/env python3
"""Replication wrapper for market_order_rule_of_law_private_credit_depth_panel."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.run([
    sys.executable,
    str(ROOT / "scripts" / "run_panel_fe.py"),
    "market_order_rule_of_law_private_credit_depth_panel",
    "--force",
], cwd=ROOT).returncode)
