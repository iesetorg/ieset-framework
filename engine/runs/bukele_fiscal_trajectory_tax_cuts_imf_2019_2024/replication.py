#!/usr/bin/env python3
"""Replicate this panel run from the preregistered hypothesis spec."""
from scripts.run_panel_fe import run_one

if __name__ == '__main__':
    print(run_one('bukele_fiscal_trajectory_tax_cuts_imf_2019_2024', force=True, persist_preflight_inconclusive=True))
