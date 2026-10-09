#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/check_heritage_wgi_geographic_holdouts_v2.py'), 'heritage_business_freedom_life_expectancy_wgi_panel_geographic_holdout_v2'], cwd=root))
