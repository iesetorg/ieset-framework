#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,'-B',str(root/'scripts/run_physician_education_family_2026.py'),'--verify']))
