#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/verify_innovation_productivity_measured_family_2026.py'), '--verify', 'manufacturing_productivity_hightech_export_mix_forward_2026'], cwd=root))
