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
    "hypothesis_id": "heritage_property_rights_high_tech_exports_wgi_rl_panel",
    "source_rank": 32,
    "source_hypothesis_id": "heritage_property_rights_high_tech_exports_income_region_robustness",
    "source_controlled_verdict": "SUPPORTED",
    "source_bh_q_value": 0.013880438376879302,
    "source_run_path": "engine/runs/heritage_property_rights_high_tech_exports_income_region_robustness",
    "proxy_kind": "single",
    "proxy_label": "WGI rule of law estimate",
    "proxy_sources": [
        {
            "name": "rule_of_law",
            "publisher": "wgi",
            "series": "GOV_WGI_RL.EST",
            "label": "WGI rule of law estimate",
        }
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
