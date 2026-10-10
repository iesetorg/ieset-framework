#!/usr/bin/env python3
"""Exact replay of wgi_ge_oecd_treatable_mortality_forward_2026; requires the committed result packet."""
import argparse
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-root", type=Path)
args = parser.parse_args()
command = [sys.executable, str(root / "scripts/run_wgi_ge_oecd_treatable_mortality_2026.py"), "verify"]
if args.source_root is not None:
    command += ["--source-root", str(args.source_root)]
raise SystemExit(subprocess.call(command, cwd=root))
