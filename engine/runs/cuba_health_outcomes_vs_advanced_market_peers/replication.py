#!/usr/bin/env python3
"""Replication — Cuba health outcomes vs advanced-market peers, 1960-2000."""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from cuba_health_rank_common import build_run

CONFIG = {
    "hid": "cuba_health_outcomes_vs_advanced_market_peers",
    "peers": ["ESP", "PRT", "GRC", "ISR", "JPN", "KOR"],
    "advanced_subgroup": None,
    "pool_label": "7-country advanced-market subgroup",
    "pool_size_label": "7-country subgroup",
    "le_rank_threshold": 4,
    "imr_rank_threshold": 4,
    "income_gap_threshold": 1.0,
    "min_peer_coverage": 6,
    "income_publisher": "owid",
    "income_series": "gdp-per-capita-maddison-2020",
    "income_value_col": "GDP per capita",
    "card_title": "Cuba health outcomes vs advanced-market peers, 1960-2000",
    "chart_title": "Cuba vs advanced-market comparators, life expectancy 1960-2000",
    "chart_subtitle_template": (
        "Top-half test: Cuba must rank in the upper half on both health metrics and beat its income rank by at least one place. "
        "Observed 2000 ranks: LE #{le_rank}/{le_pool}, IMR #{imr_rank}/{imr_pool}, income #{gdp_rank}/{gdp_pool}; gap {income_gap:+.1f}."
    ),
    "peer_mean_label": "Advanced-market mean",
    "advanced_mean_label": "Advanced-market mean",
    "advanced_subgroup_heading": "",
    "method_note": (
        "This is the intentionally mean stress test. The comparator pool is restricted to Southern European and East Asian / Israeli market economies "
        "that are materially richer than Cuba and often cited as high-performing non-socialist health systems. The threshold asks for upper-half placement "
        "on life expectancy and infant mortality plus at least a one-place health-over-income overperformance. If Cuba still clears that bar, the claim has real reach; "
        "if it does not, the universal-superiority story is much weaker than the LATAM-only framing suggests."
    ),
    "data_quality_caveat": (
        "The Cuban health series still inherits official-reporting risk, and the rich-comparator pool is small enough that one-rank changes matter."
    ),
    "income_caveat": (
        "Income rank again uses OWID's Maddison GDP-per-capita series because the WDI PPP endpoint is missing for Cuba. That choice is transparent, but the ranking should be treated as contextual rather than dispositive in itself."
    ),
    "causal_caveat": (
        "This subgroup test is descriptive, not causal. It is best read as a credibility stress test of broad Marxist-Leninist health-superiority rhetoric, not as a clean estimator of the effect of socialism."
    ),
}


if __name__ == "__main__":
    raise SystemExit(build_run(CONFIG))
