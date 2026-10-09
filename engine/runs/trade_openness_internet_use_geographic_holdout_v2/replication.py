#!/usr/bin/env python3
"""Read-only exact replay of this pinned geographic-holdout result."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_trade_openness_measured_endpoint_holdouts_v2.py'), '--check', 'trade_openness_internet_use_geographic_holdout_v2'], cwd=root))
