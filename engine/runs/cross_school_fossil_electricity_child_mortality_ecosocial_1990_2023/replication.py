#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_cross_school_next50_2026_05_12.py'), 'cross_school_fossil_electricity_child_mortality_ecosocial_1990_2023']))
