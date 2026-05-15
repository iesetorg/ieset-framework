#!/usr/bin/env python3
"""Replication for `capital_gains_tax_cut_investment_response_panel`.

This hypothesis preregisters two outcomes, so it uses the shared panel loader
and estimator but grades the verdict against both the investment and business-
entry estimates.
"""
from __future__ import annotations

import json
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

RUN_PANEL_FE = ROOT / "scripts" / "run_panel_fe.py"
spec = importlib.util.spec_from_file_location("run_panel_fe", RUN_PANEL_FE)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {RUN_PANEL_FE}")
run_panel_fe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = run_panel_fe
spec.loader.exec_module(run_panel_fe)


HYPOTHESIS_ID = "capital_gains_tax_cut_investment_response_panel"
OUTCOMES = [
    "gross_fixed_capital_formation_share_gdp",
    "new_business_density",
]
TREATMENT = "capital_gains_tax_rate"


def _fmt_estimate(name: str, estimate: dict) -> str:
    if "error" in estimate:
        return f"- `{name}`: error - {estimate['error']}"
    return (
        f"- `{name}`: coef={estimate['coefficient']:+.4g}, "
        f"se={estimate['std_error']:.4g}, p={estimate['p_value']:.4g}, "
        f"n={estimate['n_obs']}, countries={estimate['n_countries']}"
    )


def _is_negative_significant(estimate: dict, alpha: float) -> bool:
    return (
        "error" not in estimate
        and estimate.get("coefficient", 0) < 0
        and estimate.get("p_value", 1) <= alpha
    )


def _is_positive_significant(estimate: dict, alpha: float) -> bool:
    return (
        "error" not in estimate
        and estimate.get("coefficient", 0) > 0
        and estimate.get("p_value", 1) <= alpha
    )


def main() -> int:
    loaded = run_panel_fe.load_spec(HYPOTHESIS_ID)
    if loaded is None:
        raise FileNotFoundError(HYPOTHESIS_ID)
    _, spec = loaded
    panel, status = run_panel_fe.build_panel(spec)
    panel = run_panel_fe.filter_sample(panel, spec)
    alpha = run_panel_fe.infer_significance_alpha(spec)

    missing = [
        name for name in [*OUTCOMES, TREATMENT]
        if name not in panel.columns or not panel[name].notna().any()
    ]
    estimates: dict[str, dict] = {}
    if missing:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = f"missing required variables: {missing}"
    else:
        for outcome in OUTCOMES:
            estimates[outcome] = run_panel_fe.run_panel_ols(
                panel,
                spec,
                outcome,
                TREATMENT,
            )
        investment = estimates[OUTCOMES[0]]
        entry = estimates[OUTCOMES[1]]
        if _is_negative_significant(investment, alpha) and _is_negative_significant(entry, alpha):
            verdict = "SUPPORTED"
            reason = "capital-gains rate is negative and significant for both investment and business-entry outcomes"
        elif _is_positive_significant(investment, alpha):
            verdict = "REFUTED"
            reason = "capital-gains rate is positive and significant for the primary investment outcome"
        elif _is_negative_significant(investment, alpha):
            verdict = "PARTIAL"
            reason = "capital-gains rate is negative and significant for investment, but not for the business-entry outcome"
        else:
            verdict = "PARTIAL"
            reason = "capital-gains rate does not clear the preregistered two-outcome support rule"

    out_dir = Path(__file__).resolve().parent
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HYPOTHESIS_ID,
        "template": (spec.get("estimator") or {}).get("template"),
        "claim_direction_inferred": "-",
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": estimates,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/capital_gains_tax_cut_investment_response_panel/replication.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str) + "\n")

    lines = [
        f"# Result card - {HYPOTHESIS_ID}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim', '').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule', '').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test', '').strip()}",
        "",
        "## Estimates",
    ]
    if estimates:
        for outcome in OUTCOMES:
            lines.append(_fmt_estimate(outcome, estimates[outcome]))
    else:
        lines.append(f"- _Error:_ {reason}")
    lines.extend(
        [
            "",
            "## Variables resolved",
        ]
    )
    for variable in status.get("variables_loaded", []):
        lines.append(
            f"- `{variable['source']}` -> {variable['name']} "
            f"({variable['role']}, publisher={variable['publisher']}, n={variable['n_rows']})"
        )
    if status.get("variables_missing"):
        lines.extend(["", "### Variables missing data"])
        for variable in status["variables_missing"]:
            lines.append(
                f"- `{variable['source']}` ({variable['role']}, name={variable['name']})"
            )
    lines.extend(
        [
            "",
            "_Generated by `engine/runs/capital_gains_tax_cut_investment_response_panel/replication.py` "
            f"at {diag['run_utc']}_",
            "",
        ]
    )
    (out_dir / "result_card.md").write_text("\n".join(lines))
    print(f"{HYPOTHESIS_ID}: {verdict} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
