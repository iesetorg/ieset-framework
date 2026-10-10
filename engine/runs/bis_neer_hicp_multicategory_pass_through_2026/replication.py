#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_bis_neer_eurostat_goods_hicp_2026.py'), '--verify'], cwd=root))
