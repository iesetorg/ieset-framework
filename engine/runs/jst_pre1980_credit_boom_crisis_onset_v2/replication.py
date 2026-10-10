#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_jst_pre1980_credit_crisis_2026.py'), 'verify', *sys.argv[1:]], cwd=root))
