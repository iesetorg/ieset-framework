#!/usr/bin/env python3
"""Replication — Cuba health outcomes vs non-LATAM market peers, 1960-2000."""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from cuba_health_rank_common import build_run

CONFIG = {
    "hid": "cuba_health_outcomes_vs_non_latam_market_peers",
    "peers": [
        "ESP", "PRT", "GRC", "TUR", "ISR", "JPN", "KOR", "THA", "MYS", "IDN",
        "PHL", "IND", "LKA", "PAK", "BGD", "MAR", "TUN", "DZA", "EGY", "JOR",
    ],
    "advanced_subgroup": ["CUB", "ESP", "PRT", "GRC", "ISR", "JPN", "KOR"],
    "pool_label": "21-country non-LATAM market-economy pool",
    "pool_size_label": "21-country pool",
    "le_rank_threshold": 7,
    "imr_rank_threshold": 5,
    "income_gap_threshold": 5.0,
    "min_peer_coverage": 18,
    "income_publisher": "owid",
    "income_series": "gdp-per-capita-maddison-2020",
    "income_value_col": "GDP per capita",
    "card_title": "Cuba health outcomes vs non-LATAM market peers, 1960-2000",
    "chart_title": "Cuba vs non-LATAM market-economy comparators, life expectancy 1960-2000",
    "chart_subtitle_template": (
        "Cuba ranks #{le_rank}/{le_pool} on life expectancy, #{imr_rank}/{imr_pool} on infant mortality, "
        "and #{gdp_rank}/{gdp_pool} on income in 2000; health-vs-income gap {income_gap:+.1f}."
    ),
    "peer_mean_label": "Non-LATAM market-peer mean",
    "advanced_mean_label": "Advanced-market subgroup mean",
    "advanced_subgroup_heading": "Advanced-market subgroup check (ESP, PRT, GRC, ISR, JPN, KOR, plus Cuba)",
    "method_note": (
        "Descriptive rank-table test only. The dispositive question is whether Cuba remains genuinely competitive once the "
        "comparison pool expands beyond a friendlier Latin American frame. Life expectancy and infant mortality come from WDI; "
        "income-rank context comes from the OWID-packaged Maddison GDP-per-capita series because the WDI PPP-per-capita vintage "
        "does not report a usable Cuba 2000 endpoint. Method-validity requires Cuba plus at least 18 of the 20 non-Cuban "
        "comparators at the 2000 endpoint on life expectancy, infant mortality, and income."
    ),
    "data_quality_caveat": (
        "WDI back-fills Cuba's 1960-2000 health series from Cuban official reporting; the usual official-data caveat still applies, "
        "especially for infant mortality classification practices and the lack of a full-window WHO-independent backfill."
    ),
    "income_caveat": (
        "Income rank uses OWID's Maddison GDP-per-capita series rather than WDI PPP-per-capita because Cuba's WDI PPP endpoint is missing. "
        "That preserves cross-country comparability, but the exact income-rank gap should be read as an approximate context metric, not a causal control."
    ),
    "causal_caveat": (
        "A strong or weak rank in this pool does not by itself identify socialism as the cause: Soviet transfers, pre-revolution baseline, sanctions, "
        "public-health prioritisation, and state capacity remain bundled together."
    ),
}


if __name__ == "__main__":
    raise SystemExit(build_run(CONFIG))
