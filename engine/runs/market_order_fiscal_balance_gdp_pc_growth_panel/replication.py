#!/usr/bin/env python3
"""Replicate the registered panel-FE run for market_order_fiscal_balance_gdp_pc_growth_panel."""

from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[3]

RUN_PANEL_FE = ROOT / "scripts" / "run_panel_fe.py"
spec = importlib.util.spec_from_file_location("run_panel_fe", RUN_PANEL_FE)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {RUN_PANEL_FE}")
run_panel_fe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = run_panel_fe
spec.loader.exec_module(run_panel_fe)


if __name__ == "__main__":
    print(run_panel_fe.run_one("market_order_fiscal_balance_gdp_pc_growth_panel", force=True, persist_preflight_inconclusive=True))
