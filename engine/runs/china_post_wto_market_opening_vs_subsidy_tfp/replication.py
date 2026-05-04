#!/usr/bin/env python3
"""Replicate this event-study run from the preregistered hypothesis spec."""
from scripts.run_event_study import run_one

if __name__ == '__main__':
    print(run_one('china_post_wto_market_opening_vs_subsidy_tfp', force=True))
