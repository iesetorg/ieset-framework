#!/usr/bin/env python3
"""Run-local replication for eurostat_energy_price_household_distribution_stress."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import graduate_eurostat_household_energy_panels_2026_05_15 as household


def main() -> int:
    price, price_path = household.household_price()
    gdp, gdp_path = household.wdi("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth")
    stress, stress_path = household.warmth_stress()

    base = price.merge(gdp, on=["country", "year"], how="inner")
    base = base[(base["year"] >= household.PERIOD[0]) & (base["year"] <= household.PERIOD[1])].copy()
    stress_panel = base.merge(stress, on=["country", "year"], how="inner")
    stress_est = household.run_fe(stress_panel, "distribution_stress", "household_electricity_price")
    household.write_run(
        hid="eurostat_energy_price_household_distribution_stress",
        outcome="distribution_stress",
        treatment="household_electricity_price",
        expected_sign="+",
        panel=stress_panel,
        estimate=stress_est,
        vintages=[
            ("distribution_stress", "eurostat:ilc_mdes01", stress_path),
            ("household_electricity_price", "eurostat:nrg_pc_204", price_path),
            ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", gdp_path),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
