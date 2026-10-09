#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_second_legacy_panel_geographic_holdouts_v2.py'), '--check', 'regulatory_quality_private_consumption_geographic_holdout_v2'], cwd=root))
