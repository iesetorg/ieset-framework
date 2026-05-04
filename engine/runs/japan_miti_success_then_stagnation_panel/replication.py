#!/usr/bin/env python3
"""Replicate this panel run from the preregistered hypothesis spec."""
from scripts.run_panel_fe import run_one

if __name__ == '__main__':
    print(run_one('japan_miti_success_then_stagnation_panel', force=True, persist_preflight_inconclusive=True))
