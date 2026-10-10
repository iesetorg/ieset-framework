#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else root
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_oecd_cit_cbcr_profit_booking_2019_v2.py'), '--verify', '--source-root', str(source_root)], cwd=root))
