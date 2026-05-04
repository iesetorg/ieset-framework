#!/usr/bin/env python3
"""Replicate this panel run from the preregistered hypothesis spec."""
from scripts.run_panel_fe import run_one

if __name__ == '__main__':
    print(run_one('banking_crisis_schularick_taylor_credit_boom_panel_post1980', force=True, persist_preflight_inconclusive=True))
