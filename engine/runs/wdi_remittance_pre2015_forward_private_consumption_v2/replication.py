#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
subprocess.run([sys.executable, str(root / 'scripts/run_wdi_remittance_pre2015_forward_2020_2023_family.py'), '--replay', *sys.argv[1:]], check=True)
