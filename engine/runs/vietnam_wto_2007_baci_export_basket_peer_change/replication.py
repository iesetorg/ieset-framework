#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_vietnam_wto_2007_baci_export_basket_peer_change.py'), 'verify'], cwd=root))
