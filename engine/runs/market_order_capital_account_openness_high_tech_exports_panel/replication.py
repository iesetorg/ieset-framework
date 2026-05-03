#!/usr/bin/env python3
"""Replicate the registered panel-FE run for market_order_capital_account_openness_high_tech_exports_panel."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.run_panel_fe import run_one


if __name__ == "__main__":
    print(run_one("market_order_capital_account_openness_high_tech_exports_panel", force=True, persist_preflight_inconclusive=True))
