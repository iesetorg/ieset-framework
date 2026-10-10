#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
subprocess.run([sys.executable, str(root / 'scripts/run_wdi_protected_land_forward_forest_food_2026_family.py'), '--replay', *sys.argv[1:]], check=True)
