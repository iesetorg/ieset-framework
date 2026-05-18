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
    "hypothesis_id": "heritage_business_freedom_under5_mortality_wgi_rq_panel",
    "source_rank": 18,
    "source_hypothesis_id": "heritage_business_freedom_under5_mortality_income_region_robustness",
    "source_controlled_verdict": "SUPPORTED",
    "source_bh_q_value": 0.0005579982071424246,
    "source_run_path": "engine/runs/heritage_business_freedom_under5_mortality_income_region_robustness",
    "proxy_kind": "single",
    "proxy_label": "WGI regulatory quality estimate",
    "proxy_sources": [
        {
            "name": "regulatory_quality",
            "publisher": "wgi",
            "series": "GOV_WGI_RQ.EST",
            "label": "WGI regulatory quality estimate",
        }
    ],
    "outcome_source": {
        "publisher": "world_bank_wdi",
        "series": "SH.DYN.MORT",
        "label": "Mortality rate, under-5 (per 1,000 live births)",
    },
    "outcome_label": "under-5 mortality rate",
    "expected_sign": "-",
}

raise SystemExit(runner.run(SPEC))
