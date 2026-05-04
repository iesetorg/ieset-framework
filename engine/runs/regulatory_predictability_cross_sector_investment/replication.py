#!/usr/bin/env python3
"""Replicate this panel run from the preregistered hypothesis spec."""
from scripts.run_panel_fe import run_one

if __name__ == '__main__':
    print(run_one('regulatory_predictability_cross_sector_investment', force=True, persist_preflight_inconclusive=True))
