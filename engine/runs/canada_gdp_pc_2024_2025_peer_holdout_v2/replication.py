#!/usr/bin/env python3
"""Read-only exact replay of canada_gdp_pc_2024_2025_peer_holdout_v2."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_temporal_calibration_holdouts_v2.py'), '--study', 'canada', '--check'], cwd=root))
