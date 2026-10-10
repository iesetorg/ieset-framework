#!/usr/bin/env python3
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[3]
subprocess.run(['python3', 'scripts/run_union_density_low_education_unemployment_calibration_2026.py', '--verify'], cwd=root, check=True)
