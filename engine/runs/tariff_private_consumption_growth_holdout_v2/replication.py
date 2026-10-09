#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_fourth_legacy_panel_geographic_holdouts_v2.py'), '--check', 'tariff_private_consumption_growth_holdout_v2'], cwd=root))
