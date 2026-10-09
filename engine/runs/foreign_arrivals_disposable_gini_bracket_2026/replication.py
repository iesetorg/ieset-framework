#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/verify_cross_domain_measured_followups_2026.py'), '--verify', 'foreign_arrivals_disposable_gini_bracket_2026'], cwd=root))
