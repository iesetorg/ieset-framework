#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_mexico_eu4_baci_2026.py'), 'verify', '--case', 'mexico_eu_fta_eu4_baci_exports_2000_v2'], cwd=root))
