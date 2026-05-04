#!/usr/bin/env python3
"""Close the V1 linked-coverage floor with curated mechanism stakes.

The earlier waves lifted under-covered schools but left a residual linked
coverage gap. This script closes that floor by linking tested hypotheses from
mechanism families where the remaining schools have explicit theoretical
stakes: redistribution, labour bargaining, financial instability, natural
monopoly regulation, industrial policy, and ecological public investment.

It intentionally stops each school at the V1 floor (100 unique linked
hypotheses) to improve balance without spraying extra links onto schools that
are already covered.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from apply_market_order_opposition_coverage_wave import insert_covers_yaml
from backfill_hypothesis_schools import insert_fsc_yaml


ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ROOT / "positions"
HYPOTHESES = ROOT / "hypotheses"
AUDITS = ROOT / "engine" / "audits"

TARGET_FLOOR = 100

TARGET_POSITIONS = [
    "mmt",
    "market_socialist",
    "degrowth",
    "eco_socialist",
    "marxian",
    "marxist_leninist",
    "democratic_socialist",
    "post_keynesian",
    "new_keynesian",
    "social_democratic",
]

POSITION_LABELS = {
    "mmt": "MMT",
    "market_socialist": "Market socialism",
    "degrowth": "Degrowth",
    "eco_socialist": "Eco-socialism",
    "marxian": "Marxian political economy",
    "marxist_leninist": "Marxist-Leninist political economy",
    "democratic_socialist": "Democratic socialism",
    "post_keynesian": "Post-Keynesian economics",
    "new_keynesian": "New Keynesian economics",
    "social_democratic": "Social democracy",
}

POSITION_DEFAULT_RATIONALE = {
    "mmt": "MMT has a stake in whether public spending, transfers, and labour-market institutions are constrained by real resources rather than household-budget analogies.",
    "market_socialist": "Market socialism has a stake in whether worker voice, public investment, and socialized-capital mechanisms can coexist with productive allocation.",
    "degrowth": "Degrowth has a stake in whether welfare, emissions, and labour-security outcomes can improve without treating GDP growth as the sole objective.",
    "eco_socialist": "Eco-socialism has a stake in whether public ownership, green investment, and labour-protective institutions outperform market-only climate and welfare mechanisms.",
    "marxian": "Marxian theory has a stake in whether capital mobility, financial liberalisation, and labour bargaining dynamics shape observed distributional outcomes.",
    "marxist_leninist": "Marxist-Leninist theory has a stake in whether state direction, industrial policy, and decommodified welfare can outperform market allocation.",
    "democratic_socialist": "Democratic socialism has a stake in whether democratic public provision, worker power, and redistribution improve social outcomes without destroying employment.",
    "post_keynesian": "Post-Keynesian theory has a stake in demand-led growth, wage-led regimes, financial instability, and fiscal-transfer effectiveness.",
    "new_keynesian": "New Keynesian theory has a stake in state-contingent fiscal, labour-market, and market-failure mechanisms rather than unconditional laissez-faire claims.",
    "social_democratic": "Social democracy has a stake in whether redistribution, public services, and coordinated labour-market institutions can improve welfare inside market economies.",
}

WAVE_NOTE = (
    "2026-05-04 V1 balance-floor coverage wave; curated mechanism-family selection "
    "from already tested hypotheses, independent of observed score effects."
)

HYPOTHESIS_SEQUENCE = [
    ("oecd_public_transfers_poverty_reduction_panel", "redistribution_support"),
    ("tax_inequality_biden_ctc_2021_child_poverty", "redistribution_support"),
    ("tax_inequality_korea_progressive_turn_2017_2020", "redistribution_support"),
    ("tax_inequality_france_2017_isf_to_ifi_abolition", "redistribution_support"),
    ("tax_inequality_spain_top_rate_dynamics", "redistribution_support"),
    ("wage_led_vs_profit_led_growth_oecd", "worker_bargaining_support"),
    ("capital_mobility_worker_bargaining_power", "worker_bargaining_support"),
    ("worker_coop_conversion_employment_preservation", "worker_bargaining_support"),
    ("german_codetermination_competitiveness", "worker_bargaining_support"),
    ("minimum_wage_disemployment_at_high_bite_ratios", "labour_drag_opposition"),
    ("unemployment_benefit_duration_long_term_unemployment", "labour_drag_opposition"),
    ("unemployment_benefit_generosity_employment_drag", "labour_drag_opposition"),
    ("workfare_conditionality_employment_effect", "labour_drag_opposition"),
    ("active_labour_market_policy_conditionality_works", "labour_institution_conditional"),
    ("apprenticeship_employer_chamber_quality", "labour_institution_conditional"),
    ("financial_liberalisation_crisis_risk", "financial_instability_support"),
    ("banking_crisis_nordic_1991_1993_panel", "financial_instability_support"),
    ("banking_crisis_us_sl_crisis_1986_1995", "financial_instability_support"),
    ("banking_crisis_2008_gfc_canonical_multimetric", "financial_instability_support"),
    ("natural_monopoly_private_failure", "market_failure_support"),
    ("asia_taiwan_tsmc_industrial_policy_1985_2024", "industrial_policy_support"),
    ("china_renewables_industrial_policy_learning_curve", "industrial_policy_support"),
    ("public_transport_investment_emissions_per_capita", "ecological_public_investment_support"),
    ("carbon_tax_revenue_neutral_double_dividend", "ecological_policy_conditional"),
    ("eu_ets_emissions_reduction_vs_1p5c_pathway", "ecological_market_mechanism_skepticism"),
    ("fossil_subsidy_persistence_private_ownership_link", "ecological_market_mechanism_skepticism"),
    ("energy_crisis_2022_european_industrial_relocation", "ecological_policy_conditional"),
    ("energy_market_competition_reliability", "market_energy_opposition"),
    ("energy_market_competition_household_cost", "market_energy_opposition"),
]


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def hypothesis_path(hypothesis_id: str) -> Path:
    matches = sorted(HYPOTHESES.glob(f"*/{hypothesis_id}.yaml"))
    if not matches:
        raise FileNotFoundError(hypothesis_id)
    return matches[0]


def existing_links(position: dict) -> set[str]:
    return {
        claim.get("linked_hypothesis_id")
        for claim in position.get("falsifiable_specific_claims") or []
        if claim.get("linked_hypothesis_id")
    }


def prediction_for(position_id: str, mechanism: str) -> tuple[str, str]:
    if mechanism in {
        "redistribution_support",
        "worker_bargaining_support",
        "financial_instability_support",
        "market_failure_support",
        "industrial_policy_support",
        "ecological_public_investment_support",
        "ecological_market_mechanism_skepticism",
    }:
        if position_id == "new_keynesian" and mechanism in {
            "worker_bargaining_support",
            "industrial_policy_support",
            "ecological_market_mechanism_skepticism",
        }:
            return "mixed", "medium"
        if position_id == "degrowth" and mechanism in {
            "industrial_policy_support",
            "financial_instability_support",
        }:
            return "mixed", "low"
        return "supported", "medium"

    if mechanism == "labour_drag_opposition":
        if position_id in {"new_keynesian", "social_democratic", "degrowth"}:
            return "mixed", "medium"
        return "falsified", "medium"

    if mechanism == "labour_institution_conditional":
        if position_id in {"new_keynesian", "social_democratic", "post_keynesian"}:
            return "supported", "medium"
        return "mixed", "medium"

    if mechanism == "ecological_policy_conditional":
        if position_id in {"eco_socialist", "social_democratic", "new_keynesian"}:
            return "supported", "medium"
        return "mixed", "medium"

    if mechanism == "market_energy_opposition":
        if position_id in {"eco_socialist", "degrowth", "market_socialist", "marxian", "marxist_leninist"}:
            return "falsified", "medium"
        return "mixed", "medium"

    raise ValueError(f"unknown mechanism: {mechanism}")


def claim_text(position_id: str, prediction: str, mechanism: str, hypothesis: dict) -> str:
    school = POSITION_LABELS[position_id]
    claim = " ".join(str(hypothesis.get("claim") or "").split())
    if len(claim) > 300:
        claim = claim[:297] + "..."
    if prediction == "mixed":
        return f"{school} treats this {mechanism.replace('_', ' ')} claim as conditional rather than dispositive: {claim}"
    if prediction == "falsified":
        return f"{school} predicts this {mechanism.replace('_', ' ')} claim should not hold as a general rule: {claim}"
    return f"{school} predicts this {mechanism.replace('_', ' ')} claim should hold in the stated scope: {claim}"


def claim_block(position_id: str, mechanism: str, hypothesis: dict) -> dict:
    prediction, confidence = prediction_for(position_id, mechanism)
    return {
        "claim": claim_text(position_id, prediction, mechanism, hypothesis),
        "linked_hypothesis_id": hypothesis["hypothesis_id"],
        "school_prediction": prediction,
        "claim_polarity": "aligned",
        "empirical_status": "untested",
        "scope": hypothesis.get("scope") or {},
        "notes": f"{WAVE_NOTE} Mechanism family: {mechanism}. {POSITION_DEFAULT_RATIONALE[position_id]}",
    }


def append_position_claims(hypotheses: dict[str, dict]) -> tuple[dict[tuple[str, str], int], list[dict]]:
    claim_indexes: dict[tuple[str, str], int] = {}
    added_position_entries: list[dict] = []

    for position_id in TARGET_POSITIONS:
        path = POSITIONS / f"{position_id}.yaml"
        position = load_yaml(path)
        claims = position.get("falsifiable_specific_claims") or []
        links = existing_links(position)
        needed = max(0, TARGET_FLOOR - len(links))
        blocks: list[dict] = []
        if needed == 0:
            continue

        for hypothesis_id, mechanism in HYPOTHESIS_SEQUENCE:
            if needed == 0:
                break
            if hypothesis_id in links:
                continue
            hypothesis = hypotheses[hypothesis_id]
            block = claim_block(position_id, mechanism, hypothesis)
            claim_index = len(claims) + len(blocks)
            blocks.append(block)
            links.add(hypothesis_id)
            needed -= 1
            claim_indexes[(position_id, hypothesis_id)] = claim_index
            prediction, confidence = prediction_for(position_id, mechanism)
            added_position_entries.append(
                {
                    "position_id": position_id,
                    "hypothesis_id": hypothesis_id,
                    "claim_index": claim_index,
                    "mechanism": mechanism,
                    "school_prediction": prediction,
                    "confidence": confidence,
                }
            )

        if needed:
            raise RuntimeError(f"{position_id} still needs {needed} links; add more curated hypotheses")
        if blocks:
            path.write_text(insert_fsc_yaml(path.read_text(), blocks))

    return claim_indexes, added_position_entries


def update_hypothesis_covers(entries: list[dict]) -> list[dict]:
    entries_by_hypothesis: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        entries_by_hypothesis[entry["hypothesis_id"]].append(entry)

    cover_entries: list[dict] = []
    for hypothesis_id, hypothesis_entries in entries_by_hypothesis.items():
        path = hypothesis_path(hypothesis_id)
        doc = load_yaml(path)
        covers = doc.setdefault("covers_claims", [])
        existing = {(entry.get("position_id"), entry.get("claim_index")) for entry in covers}
        path_entries: list[dict] = []

        for entry in hypothesis_entries:
            key = (entry["position_id"], entry["claim_index"])
            if key in existing:
                continue
            cover = {
                "position_id": entry["position_id"],
                "claim_index": entry["claim_index"],
                "polarity": "aligned",
                "school_prediction": entry["school_prediction"],
                "confidence": entry["confidence"],
                "notes": (
                    f"{WAVE_NOTE} Mechanism family: {entry['mechanism']}. "
                    f"{POSITION_DEFAULT_RATIONALE[entry['position_id']]}"
                ),
            }
            covers.append(cover)
            path_entries.append(cover)
            cover_entries.append({"hypothesis_id": hypothesis_id, "mechanism": entry["mechanism"], **cover})

        if path_entries:
            path.write_text(insert_covers_yaml(path.read_text(), path_entries))

    return cover_entries


def write_audit(entries: list[dict]) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    stamp = "2026-05-04"
    by_position: dict[str, int] = defaultdict(int)
    by_prediction: dict[str, int] = defaultdict(int)
    by_mechanism: dict[str, int] = defaultdict(int)
    for entry in entries:
        by_position[entry["position_id"]] += 1
        by_prediction[entry["school_prediction"]] += 1
        by_mechanism[entry["mechanism"]] += 1

    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "wave": "v1_balance_floor_coverage_wave",
        "methodology_gate": {
            "selection_rule": "Curated tested hypotheses from declared mechanism families; links stop when each target school reaches 100 unique linked hypotheses.",
            "not_selected_by": "observed verdicts or school score effect",
            "verdict_policy": "No verdicts changed; only reciprocal position links and covers_claims were added.",
            "mixed_policy": "School predictions are marked mixed when the theory has a conditional stake but not a clean directional commitment.",
        },
        "target_floor": TARGET_FLOOR,
        "hypotheses": [hypothesis_id for hypothesis_id, _ in HYPOTHESIS_SEQUENCE],
        "new_links": len(entries),
        "new_links_by_position": dict(sorted(by_position.items())),
        "new_links_by_school_prediction": dict(sorted(by_prediction.items())),
        "new_links_by_mechanism": dict(sorted(by_mechanism.items())),
        "entries": entries,
    }

    json_path = AUDITS / f"v1_balance_floor_coverage_wave_{stamp}.json"
    md_path = AUDITS / f"v1_balance_floor_coverage_wave_{stamp}.md"
    json_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    lines = [
        "# V1 Balance-Floor Coverage Wave",
        "",
        f"Generated: {doc['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- Curated tested hypotheses from declared mechanism families.",
        "- Selection is mechanism-based, not verdict-based.",
        "- No verdicts changed; only reciprocal position links and `covers_claims` entries were added.",
        "- Links stop once each target school reaches 100 unique linked hypotheses.",
        "- `mixed` is used when a school has a conditional stake but not a clean directional commitment.",
        "",
        "## Counts",
        "",
        f"- New reciprocal links: {len(entries)}",
    ]
    for position_id, count in sorted(by_position.items()):
        lines.append(f"- {position_id}: {count}")
    lines += ["", "## Mechanism Families", ""]
    for mechanism, count in sorted(by_mechanism.items()):
        lines.append(f"- {mechanism}: {count}")
    md_path.write_text("\n".join(lines) + "\n")

    print(f"wrote {json_path.relative_to(ROOT)}")
    print(f"wrote {md_path.relative_to(ROOT)}")
    print(json.dumps({"new_links": len(entries), "by_position": dict(by_position)}, sort_keys=True))


def main() -> int:
    hypotheses = {
        hypothesis_id: load_yaml(hypothesis_path(hypothesis_id))
        for hypothesis_id, _ in HYPOTHESIS_SEQUENCE
    }
    _, position_entries = append_position_claims(hypotheses)
    cover_entries = update_hypothesis_covers(position_entries)
    write_audit(cover_entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
