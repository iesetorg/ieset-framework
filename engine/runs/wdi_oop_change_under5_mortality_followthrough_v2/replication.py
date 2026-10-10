#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
subprocess.run([sys.executable, str(root / 'scripts/run_wdi_oop_change_under5_mortality_followthrough_v2.py'), '--replay', *sys.argv[1:]], check=True)
