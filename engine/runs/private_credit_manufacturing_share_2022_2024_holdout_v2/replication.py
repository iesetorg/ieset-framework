#!/usr/bin/env python3
"""Exact replay through the frozen source-pinned runner."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_private_credit_manufacturing_2024_v2.py'), '--verify', *sys.argv[1:]]))
