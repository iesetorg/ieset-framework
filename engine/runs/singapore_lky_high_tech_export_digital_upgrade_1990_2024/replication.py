#!/usr/bin/env python3
"""Regenerate the Singapore/UAE case-study checklist wave."""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[3]
runpy.run_path(str(root / 'scripts' / 'generate_singapore_uae_case_wave.py'), run_name='__main__')
