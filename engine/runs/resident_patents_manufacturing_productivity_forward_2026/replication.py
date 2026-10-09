#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/verify_innovation_productivity_measured_family_2026.py'), '--verify', 'resident_patents_manufacturing_productivity_forward_2026'], cwd=root))
