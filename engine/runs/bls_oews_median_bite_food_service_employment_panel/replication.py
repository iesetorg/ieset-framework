#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_welfare_labour_minwage_batches_07_09_a4_2026_05_12.py'), 'bls_oews_median_bite_food_service_employment_panel']))
