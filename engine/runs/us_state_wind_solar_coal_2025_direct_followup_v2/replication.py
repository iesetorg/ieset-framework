#!/usr/bin/env python3
"""Read-only exact replay of the EIA state-generation packet."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_us_state_wind_solar_coal_2025_direct_followup_v2.py'), '--check'], cwd=root))
