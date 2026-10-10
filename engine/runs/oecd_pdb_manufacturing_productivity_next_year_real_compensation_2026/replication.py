#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
runner = Path(__file__).resolve().parents[3] / 'scripts/run_oecd_pdb_sector_real_compensation_2026_metadata_fix.py'
raise SystemExit(subprocess.call([sys.executable, str(runner), 'verify', *sys.argv[1:]]))
