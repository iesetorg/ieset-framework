#!/usr/bin/env python3
"""Replicate the registered panel-FE run for market_order_public_debt_gdp_pc_growth_panel."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_panel_fe import run_one


if __name__ == "__main__":
    print(run_one("market_order_public_debt_gdp_pc_growth_panel", force=True, persist_preflight_inconclusive=True))
