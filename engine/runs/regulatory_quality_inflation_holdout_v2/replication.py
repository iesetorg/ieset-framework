#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_sixth_legacy_panel_geographic_holdouts_v2.py'), '--check', 'regulatory_quality_inflation_holdout_v2'], cwd=root))
