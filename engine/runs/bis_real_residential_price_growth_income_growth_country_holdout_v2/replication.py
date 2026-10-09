#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_bis_real_residential_price_growth_income_growth_country_holdout_v2.py'), '--check'], cwd=root))
