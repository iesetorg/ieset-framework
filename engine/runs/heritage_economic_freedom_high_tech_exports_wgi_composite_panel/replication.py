#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "engine" / "runs" / "heritage_business_freedom_electricity_access_wgi_rq_panel" / "panel_proxy_runner.py"
MODULE_SPEC = importlib.util.spec_from_file_location("panel_proxy_runner", HELPER)
runner = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(runner)

SPEC = {
    "hypothesis_id": "heritage_economic_freedom_high_tech_exports_wgi_composite_panel",
    "source_rank": 20,
    "source_hypothesis_id": "heritage_economic_freedom_high_tech_exports_income_region_robustness",
    "source_controlled_verdict": "SUPPORTED",
    "source_bh_q_value": 0.0026557639799479767,
    "source_run_path": "engine/runs/heritage_economic_freedom_high_tech_exports_income_region_robustness",
    "proxy_kind": "composite",
    "proxy_label": "within-year z-score composite of WGI regulatory quality, rule of law, and control of corruption",
    "proxy_sources": [
        {
            "name": "regulatory_quality",
            "publisher": "wgi",
            "series": "GOV_WGI_RQ.EST",
            "label": "WGI regulatory quality estimate",
        },
        {
            "name": "rule_of_law",
            "publisher": "wgi",
            "series": "GOV_WGI_RL.EST",
            "label": "WGI rule of law estimate",
        },
        {
            "name": "control_of_corruption",
            "publisher": "wgi",
            "series": "GOV_WGI_CC.EST",
            "label": "WGI control of corruption estimate",
        },
    ],
    "outcome_source": {
        "publisher": "world_bank_wdi",
        "series": "TX.VAL.TECH.MF.ZS",
        "label": "High-technology exports (% of manufactured exports)",
    },
    "outcome_label": "high-technology exports share",
    "expected_sign": "+",
}

raise SystemExit(runner.run(SPEC))
