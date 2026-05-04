#!/usr/bin/env python3
"""Regenerate the Singapore LKY local checklist wave."""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[3]
runpy.run_path(str(root / 'scripts' / 'generate_singapore_lky_wave.py'), run_name='__main__')
