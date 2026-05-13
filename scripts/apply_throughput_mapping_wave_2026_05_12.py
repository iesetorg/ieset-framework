#!/usr/bin/env python3
"""Apply the first reviewed scoreboard mapping wave for 2026-05-12 throughput.

This wave maps decisive verdict-bearing hypotheses that lacked position claims.
It intentionally skips inconclusive, ambiguous-partial, and duplicate broad-panel
items from `throughput_scoreboard_conversion_2026-05-12`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


MAPPINGS = [
    # Market dynamism / competition
    ("business_dynamism_frontier_income_growth", "classical_liberal", "supported"),
    ("business_dynamism_frontier_income_growth", "austrian", "supported"),
    ("business_dynamism_frontier_income_growth", "ordoliberal", "supported"),
    ("platform_competition_dissipates_monopoly_rent", "classical_liberal", "supported"),
    ("platform_competition_dissipates_monopoly_rent", "ordoliberal", "supported"),
    ("price_controls_food_output_decline_panel", "classical_liberal", "supported"),
    ("price_controls_food_output_decline_panel", "austrian", "supported"),
    ("price_controls_food_output_decline_panel", "ordoliberal", "supported"),
    ("price_controls_food_output_decline_panel", "chicago_monetarism", "supported"),
    ("spectrum_auction_vs_administrative_allocation_telecom", "classical_liberal", "supported"),
    ("spectrum_auction_vs_administrative_allocation_telecom", "ordoliberal", "supported"),
    # Finance, crisis, and debt
    ("banking_crisis_schularick_taylor_credit_boom_panel_post1980", "post_keynesian", "supported"),
    ("banking_crisis_schularick_taylor_credit_boom_panel_post1980", "marxian", "supported"),
    ("banking_crisis_schularick_taylor_credit_boom_panel_post1980", "democratic_socialist", "supported"),
    ("banking_crisis_schularick_taylor_credit_boom_panel_post1980", "mmt", "supported"),
    ("banking_crisis_laeven_valencia_predictors_panel", "post_keynesian", "supported"),
    ("banking_crisis_laeven_valencia_predictors_panel", "marxian", "supported"),
    ("banking_crisis_laeven_valencia_predictors_panel", "democratic_socialist", "supported"),
    ("banking_crisis_laeven_valencia_predictors_panel", "mmt", "supported"),
    ("debt_overhang_private_investment_30yr", "classical_liberal", "supported"),
    ("debt_overhang_private_investment_30yr", "austrian", "supported"),
    ("debt_overhang_private_investment_30yr", "chicago_monetarism", "supported"),
    ("bank_state_ownership_credit_misallocation", "classical_liberal", "supported"),
    ("bank_state_ownership_credit_misallocation", "austrian", "supported"),
    ("bank_state_ownership_credit_misallocation", "developmentalism", "falsified"),
    ("venture_capital_market_depth_innovation", "classical_liberal", "supported"),
    ("venture_capital_market_depth_innovation", "developmentalism", "falsified"),
    # Technology / industrial policy / agriculture
    ("gm_crop_adoption_yield_convergence", "classical_liberal", "supported"),
    ("gm_crop_adoption_yield_convergence", "ordoliberal", "supported"),
    ("china_renewables_global_learning_curve_spillover", "developmentalism", "supported"),
    ("china_renewables_global_learning_curve_spillover", "eco_socialist", "supported"),
    ("china_renewables_global_learning_curve_spillover", "market_socialist", "supported"),
]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100))


def hypothesis_path(hid: str) -> Path:
    matches = list((ROOT / "hypotheses").glob(f"*/{hid}.yaml"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one hypothesis for {hid}, found {len(matches)}")
    return matches[0]


def verdict_bucket(hid: str) -> str:
    diag_path = ROOT / "engine" / "runs" / hid / "diagnostics.json"
    if not diag_path.exists():
        return "untested"
    import json

    verdict = str(json.loads(diag_path.read_text()).get("verdict") or "").lower()
    if verdict.startswith("supported"):
        return "supported"
    if verdict.startswith("refuted"):
        return "falsified"
    if verdict.startswith("partial"):
        return "partial"
    return "untested"


def claim_text(position_id: str, hspec: dict[str, Any], prediction: str) -> str:
    claim = " ".join(str(hspec.get("claim") or "").split())
    prefix = {
        "classical_liberal": "Classical liberalism predicts this market-order claim should hold",
        "austrian": "Austrian political economy predicts this market-process claim should hold",
        "ordoliberal": "Ordoliberalism predicts this competitive-order claim should hold",
        "chicago_monetarism": "Chicago monetarism predicts this rule-and-price-system claim should hold",
        "developmentalism": "Developmentalism predicts this state-capacity or industrial-policy claim should hold",
        "eco_socialist": "Eco-socialism predicts this public-planning or green-industrial-policy claim should hold",
        "market_socialist": "Market socialism predicts this public-direction or coordinated-investment claim should hold",
        "post_keynesian": "Post-Keynesian economics predicts this financial-instability claim should hold",
        "mmt": "MMT predicts this financial-instability or balance-sheet claim should hold",
        "marxian": "Marxian political economy predicts this financial-instability claim should hold",
        "democratic_socialist": "Democratic socialism predicts this financial-instability claim should hold",
    }.get(position_id, "This school predicts this claim should hold")
    if prediction == "falsified":
        prefix = prefix.replace("should hold", "should fail")
    return f"{prefix}: {claim}"


def main() -> None:
    position_docs: dict[str, dict[str, Any]] = {}
    hypothesis_docs: dict[str, tuple[Path, dict[str, Any]]] = {}
    applied: list[tuple[str, str, int]] = []

    for hid, position_id, prediction in MAPPINGS:
        hpath, hspec = hypothesis_docs.get(hid, (None, None))  # type: ignore[assignment]
        if hspec is None:
            hpath = hypothesis_path(hid)
            hspec = load_yaml(hpath)
            hypothesis_docs[hid] = (hpath, hspec)

        ppath = ROOT / "positions" / f"{position_id}.yaml"
        pspec = position_docs.get(position_id)
        if pspec is None:
            pspec = load_yaml(ppath)
            position_docs[position_id] = pspec

        claims = pspec.setdefault("falsifiable_specific_claims", [])
        if any(c.get("linked_hypothesis_id") == hid for c in claims if isinstance(c, dict)):
            claim_index = next(i for i, c in enumerate(claims) if isinstance(c, dict) and c.get("linked_hypothesis_id") == hid)
        else:
            claim_index = len(claims)
            claims.append(
                {
                    "claim": claim_text(position_id, hspec, prediction),
                    "linked_hypothesis_id": hid,
                    "school_prediction": prediction,
                    "claim_polarity": "aligned",
                    "empirical_status": verdict_bucket(hid),
                    "scope": hspec.get("scope") or {},
                    "notes": (
                        "2026-05-12 throughput mapping wave: selected from decisive verdict inventory "
                        "after conversion-gate review; prediction assigned from school mechanism before "
                        "scoreboard recompute."
                    ),
                }
            )

        covers = hspec.setdefault("covers_claims", [])
        if not any(
            c.get("position_id") == position_id and int(c.get("claim_index", -1)) == claim_index
            for c in covers
            if isinstance(c, dict)
        ):
            covers.append(
                {
                    "position_id": position_id,
                    "claim_index": claim_index,
                    "polarity": "aligned",
                    "school_prediction": prediction,
                    "notes": "2026-05-12 throughput mapping wave; reciprocal link for reviewed scoreboard conversion.",
                }
            )
        applied.append((hid, position_id, claim_index))

    for position_id, pspec in position_docs.items():
        dump_yaml(ROOT / "positions" / f"{position_id}.yaml", pspec)
    for hpath, hspec in hypothesis_docs.values():
        dump_yaml(hpath, hspec)

    print(f"Applied {len(applied)} mapping links")
    for hid, position_id, claim_index in applied:
        print(f"{hid}\t{position_id}\t{claim_index}")


if __name__ == "__main__":
    main()
