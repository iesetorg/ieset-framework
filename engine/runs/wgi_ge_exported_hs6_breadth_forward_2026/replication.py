#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_wgi_ge_wits_exported_hs6_breadth_2026.py'), '--verify'], cwd=root))
