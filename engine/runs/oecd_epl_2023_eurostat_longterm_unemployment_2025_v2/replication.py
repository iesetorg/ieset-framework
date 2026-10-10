#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_oecd_epl_duration_2025_v2.py'), '--verify'], cwd=root))
