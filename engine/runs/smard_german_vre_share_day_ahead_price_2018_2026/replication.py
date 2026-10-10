#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else root
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_smard_german_vre_share_day_ahead_price_2018_2026.py'), '--verify', '--source-root', str(source_root)], cwd=root))
