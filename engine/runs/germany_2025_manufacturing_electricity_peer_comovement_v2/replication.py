#!/usr/bin/env python3
"""Read-only exact replay of the Germany descriptive packet."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_germany_2025_manufacturing_electricity_peer_comovement_v2.py'), '--check'], cwd=root))
