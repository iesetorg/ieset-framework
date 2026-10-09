#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_oecd_almp_epl_low_education_unemployment_temporal_holdout_v2.py'), '--check'], cwd=root))
