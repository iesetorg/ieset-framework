#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_labour_gap_family_2026.py'), '--verify', 'oecd_almp_migrant_unemployment_gap_forward_2026'], cwd=root))
