#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_cepii_new_fta_partners_manufactures_share_forward_2026.py'), '--verify'], cwd=root))
