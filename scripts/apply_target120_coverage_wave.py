#!/usr/bin/env python3
"""Add a bounded target-120 school-coverage wave.

This is a link/claim expansion wave, not a scoring wave. It only links
hypotheses that already pass the public tested gate and it stops each selected
school at 120 unique linked hypotheses. The selection lists below are
mechanism-based and fixed before application; verdicts are not inspected for
whether they help or hurt a school.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from apply_market_order_opposition_coverage_wave import insert_covers_yaml
from audit_school_coverage_balance import build_web_hypothesis_index, has_web_public_verdict
from backfill_hypothesis_schools import insert_fsc_yaml


ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ROOT / "positions"
HYPOTHESES = ROOT / "hypotheses"
AUDITS = ROOT / "engine" / "audits"
TARGET_FLOOR = 120

PROGRESSIVE_TARGETS = [
    "democratic_socialist",
    "eco_socialist",
    "marxist_leninist",
    "market_socialist",
    "marxian",
    "social_democratic",
    "degrowth",
    "mmt",
    "new_keynesian",
    "post_keynesian",
]

POSITION_LABELS = {
    "democratic_socialist": "Democratic socialism",
    "eco_socialist": "Eco-socialism",
    "marxist_leninist": "Marxist-Leninist political economy",
    "market_socialist": "Market socialism",
    "marxian": "Marxian political economy",
    "social_democratic": "Social democracy",
    "degrowth": "Degrowth",
    "mmt": "MMT",
    "new_keynesian": "New Keynesian economics",
    "post_keynesian": "Post-Keynesian economics",
    "institutionalism": "Institutional economics",
    "chicago_monetarism": "Chicago monetarism",
}

POSITION_RATIONALE = {
    "democratic_socialist": "Democratic socialism has an explicit stake in redistribution, decommodified public goods, worker power, and democratic public ownership.",
    "eco_socialist": "Eco-socialism has an explicit stake in public control, ecological planning, fossil-fuel lock-in, and wellbeing beyond GDP.",
    "marxist_leninist": "Marxist-Leninist theory has an explicit stake in state direction, public ownership, socialist catch-up, and market-allocation failure claims.",
    "market_socialist": "Market socialism has an explicit stake in worker ownership, socialized capital, public investment, and market-compatible social provision.",
    "marxian": "Marxian political economy has an explicit stake in labour share, financial instability, accumulation, class power, and state-capital relations.",
    "social_democratic": "Social democracy has an explicit stake in welfare states, unions, fiscal stabilization, public services, and coordinated market institutions.",
    "degrowth": "Degrowth has an explicit stake in wellbeing/GDP divergence, material throughput, reduced working time, universal basic services, and ecological limits.",
    "mmt": "MMT has an explicit stake in fiscal capacity, unemployment, inflation mechanisms, and whether real-resource constraints dominate household-budget analogies.",
    "new_keynesian": "New Keynesian economics has an explicit stake in market failures, fiscal multipliers, hysteresis, ZLB regimes, and state-contingent stabilization.",
    "post_keynesian": "Post-Keynesian economics has an explicit stake in demand-led growth, financial fragility, fiscal policy, distribution, and hysteresis.",
    "institutionalism": "Institutional economics has an explicit stake in rule-of-law, state capacity, complementary institutions, and path-dependent development.",
    "chicago_monetarism": "Chicago monetarism has an explicit stake in price controls, fiscal credibility, monetary transmission, expectations, and rule-like policy regimes.",
}

WAVE_NOTE = (
    "2026-05-04 target-120 coverage wave; mechanism-based selection from already "
    "public-tested hypotheses, independent of observed score effects."
)

# Fixed progressive/Keynesian/socialist sequence. Mechanism names drive the
# school_prediction mapping below; all entries must already be public-tested.
PROGRESSIVE_SEQUENCE = [
    ("oecd_market_to_disposable_gini_compression_panel", "redistribution_support"),
    ("oecd_union_density_disposable_gini_panel", "labour_bargaining_support"),
    ("clinton_welfare_reform_deep_poverty_effect", "welfare_state_support"),
    ("r_minus_g_wealth_income_ratio_post_1980", "inequality_drift_support"),
    ("gfc_household_debt_wage_stagnation_link", "financial_instability_support"),
    ("great_depression_fiscal_counterfactual", "fiscal_expansion_support"),
    ("eurozone_austerity_distributional_incidence", "austerity_critique_support"),
    ("uk_cameron_osborne_austerity_output_effect", "austerity_critique_support"),
    ("uk_furlough_2020_unemployment_output_shield", "labour_stabilizer_support"),
    ("reduced_working_time_output_employment", "labour_decommodification_support"),
    ("ubs_material_throughput_efficiency", "wellbeing_services_support"),
    ("gdp_wellbeing_divergence_income_threshold", "wellbeing_beyond_gdp_support"),
    ("japan_stagnation_wellbeing_outcomes", "wellbeing_beyond_gdp_support"),
    ("material_footprint_cap_feasibility", "ecological_limits_support"),
    ("indigenous_managed_land_biodiversity_outcomes", "ecological_commons_support"),
    ("public_electricity_generator_carbon_intensity", "public_ownership_support"),
    ("major_fossil_firm_reserve_vs_carbon_budget", "fossil_lockin_support"),
    ("single_payer_cost_outcome_comparison", "healthcare_decommodification_support"),
    ("cuba_health_outcomes_vs_non_latam_market_peers", "healthcare_decommodification_support"),
    ("latam_resource_nationalisation_social_outcome_tradeoff", "public_ownership_support"),
    ("russia_china_transition_comparison", "gradual_public_ownership_support"),
    ("china_soe_vs_cee_privatised_growth", "public_ownership_support"),
    ("singapore_temasek_public_ownership_efficiency", "public_ownership_conditional"),
    ("yugoslav_self_management_productivity", "worker_ownership_support"),
    ("worker_coop_conversion_employment_preservation", "worker_ownership_support"),
    ("esop_firm_survival_productivity", "worker_ownership_support"),
    ("us_1945_1973_labour_compact_productivity_wage_link", "labour_bargaining_support"),
    ("labour_market_hysteresis_persistent_unemployment", "hysteresis_support"),
    ("fiscal_multipliers_state_dependent", "fiscal_expansion_conditional"),
    ("spain_2021_2023_inflation_unemployment_resilience", "stabilization_support"),
    ("australia_2008_fiscal_stimulus_output_effect", "fiscal_expansion_support"),
    ("us_household_debt_sustains_demand_1990_2008", "financial_instability_support"),
    ("maoist_precondition_for_deng_reform_growth", "socialist_precondition_support"),
    ("soviet_industrial_catch_up_1928_1940", "socialist_catchup_support"),
    ("taiwan_itri_frontier_capability_effect", "industrial_policy_support"),
    ("korea_hci_drive_capability_effect", "industrial_policy_support"),
    ("industrial_policy_export_discipline_conditionality", "industrial_policy_conditional"),
    ("gradualist_vs_shock_therapy_transition_outcomes", "gradualism_support"),
    ("pinochet_chile_rapid_liberalisation_growth_collapse", "shock_therapy_skepticism"),
]

INSTITUTIONAL_SEQUENCE = [
    ("rule_of_law_institutional_growth", "rule_of_law_support"),
    ("market_reform_without_state_capacity_failure", "state_capacity_condition"),
    ("shock_therapy_institutional_preconditions_conditionality", "state_capacity_condition"),
    ("eu_single_market_productivity_and_trade_gains", "rules_based_market_support"),
    ("botswana_institutional_exceptionalism", "institutional_quality_support"),
    ("market_order_economic_freedom_employment_rate_panel", "institutional_market_order_support"),
    ("market_order_economic_freedom_gdp_pc_growth_panel", "institutional_market_order_support"),
    ("market_order_economic_freedom_high_tech_exports_panel", "institutional_market_order_support"),
    ("market_order_economic_freedom_investment_share_panel", "institutional_market_order_support"),
    ("liberalisation_episodes_growth_trajectory", "state_capacity_condition"),
    ("post_soviet_transition_institutional_variation", "institutional_quality_support"),
    ("singapore_temasek_public_ownership_efficiency", "state_capacity_condition"),
    ("vietnam_doi_moi_developmental_pattern_growth_effect", "state_capacity_condition"),
    ("washington_consensus_vs_developmental_state_performance", "state_capacity_condition"),
    ("wdi_tertiary_attainment_growth_nonpenalty_2000_2023", "human_capital_institution_support"),
    ("wdi_tertiary_attainment_labor_productivity_2000_2023", "human_capital_institution_support"),
    ("wdi_electrification_life_expectancy_followthrough_1990_2023", "state_capacity_public_goods_support"),
    ("wdi_electrification_under5_mortality_followthrough_1990_2023", "state_capacity_public_goods_support"),
]

CHICAGO_SEQUENCE = [
    ("price_controls_shortage_effect", "price_system_support"),
    ("procyclical_fiscal_expansion_boom_bust", "fiscal_rules_support"),
    ("fiscal_consolidation_credibility_growth", "fiscal_rules_support"),
    ("debt_brake_fiscal_discipline_without_output_cost", "fiscal_rules_support"),
    ("maastricht_convergence_discipline_effect", "fiscal_rules_support"),
    ("inflation_expectations_anchoring_flattens_phillips_curve", "monetary_expectations_support"),
    ("bis_policy_rate_credit_gap_compression_panel", "monetary_transmission_support"),
    ("yield_curve_inversion_unemployment_us_1976_2026", "monetary_indicator_support"),
    ("unfunded_fiscal_expansion_above_zlb_bond_market_response", "bond_market_discipline_support"),
    ("uk_truss_mini_budget_currency_sovereign_mechanism", "bond_market_discipline_support"),
    ("classical_gold_standard_vs_fiat_long_run_inflation_comparison", "monetary_rules_support"),
    ("qe_base_money_cpi_transmission_failure", "quantity_theory_challenge"),
    ("currency_monetisation_consumer_price_effect", "quantity_theory_challenge"),
    ("fiscal_multipliers_state_dependent", "stabilization_conditional"),
    ("phillips_curve_flattening_post_1990", "monetary_expectations_support"),
    ("volcker_disinflation_output_cost_magnitude", "monetary_disinflation_support"),
    ("argentina_fx_obligation_inflation_mechanism", "fiscal_dominance_support"),
    ("argentina_default_collapse_output_effects", "monetary_rules_support"),
    ("uk_erm_exit_1992_output_unemployment_inflation", "monetary_regime_support"),
]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def hypothesis_path(hypothesis_id: str) -> Path:
    matches = sorted(HYPOTHESES.glob(f"*/{hypothesis_id}.yaml"))
    if not matches:
        raise FileNotFoundError(hypothesis_id)
    return matches[0]


def existing_links(position: dict[str, Any]) -> set[str]:
    return {
        claim.get("linked_hypothesis_id")
        for claim in position.get("falsifiable_specific_claims") or []
        if claim.get("linked_hypothesis_id")
    }


def prediction_for(position_id: str, mechanism: str) -> tuple[str, str]:
    if position_id == "chicago_monetarism":
        if mechanism in {"quantity_theory_challenge", "stabilization_conditional"}:
            return "mixed", "medium"
        return "supported", "medium"

    if position_id == "institutionalism":
        if mechanism in {"institutional_market_order_support", "rules_based_market_support"}:
            return "mixed", "medium"
        return "supported", "high"

    if mechanism in {
        "redistribution_support",
        "labour_bargaining_support",
        "welfare_state_support",
        "inequality_drift_support",
        "financial_instability_support",
        "fiscal_expansion_support",
        "austerity_critique_support",
        "labour_stabilizer_support",
        "healthcare_decommodification_support",
        "hysteresis_support",
        "fiscal_expansion_conditional",
        "stabilization_support",
    }:
        if position_id in {"new_keynesian"} and mechanism in {
            "labour_bargaining_support",
            "inequality_drift_support",
            "financial_instability_support",
        }:
            return "mixed", "medium"
        return "supported", "medium"

    if mechanism in {
        "wellbeing_services_support",
        "wellbeing_beyond_gdp_support",
        "ecological_limits_support",
        "ecological_commons_support",
        "fossil_lockin_support",
        "labour_decommodification_support",
    }:
        if position_id in {"degrowth", "eco_socialist"}:
            return "supported", "high"
        if position_id in {"new_keynesian", "mmt"}:
            return "mixed", "medium"
        return "supported", "medium"

    if mechanism in {
        "public_ownership_support",
        "gradual_public_ownership_support",
        "worker_ownership_support",
        "socialist_precondition_support",
        "socialist_catchup_support",
    }:
        if position_id in {"new_keynesian", "post_keynesian", "mmt", "degrowth"}:
            return "mixed", "medium"
        return "supported", "medium"

    if mechanism in {
        "public_ownership_conditional",
        "industrial_policy_support",
        "industrial_policy_conditional",
        "gradualism_support",
        "shock_therapy_skepticism",
    }:
        if position_id in {"new_keynesian", "post_keynesian", "mmt", "social_democratic"}:
            return "mixed", "medium"
        return "supported", "medium"

    return "mixed", "medium"


def claim_text(position_id: str, prediction: str, mechanism: str, hypothesis: dict[str, Any]) -> str:
    school = POSITION_LABELS[position_id]
    clean_claim = " ".join(str(hypothesis.get("claim") or "").split())
    if len(clean_claim) > 320:
        clean_claim = clean_claim[:317] + "..."
    mechanism_label = mechanism.replace("_", " ")
    if prediction == "mixed":
        return (
            f"{school} treats this {mechanism_label} claim as conditional rather "
            f"than dispositive: {clean_claim}"
        )
    if prediction == "falsified":
        return f"{school} predicts this {mechanism_label} claim should not hold as a general rule: {clean_claim}"
    return f"{school} predicts this {mechanism_label} claim should hold in the stated scope: {clean_claim}"


def claim_block(position_id: str, mechanism: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    prediction, _confidence = prediction_for(position_id, mechanism)
    return {
        "claim": claim_text(position_id, prediction, mechanism, hypothesis),
        "linked_hypothesis_id": hypothesis["hypothesis_id"],
        "school_prediction": prediction,
        "claim_polarity": "aligned",
        "empirical_status": "untested",
        "scope": hypothesis.get("scope") or {},
        "notes": f"{WAVE_NOTE} Mechanism family: {mechanism}. {POSITION_RATIONALE[position_id]}",
    }


def target_sequences() -> dict[str, list[tuple[str, str]]]:
    out = {position_id: PROGRESSIVE_SEQUENCE for position_id in PROGRESSIVE_TARGETS}
    out["institutionalism"] = INSTITUTIONAL_SEQUENCE
    out["chicago_monetarism"] = CHICAGO_SEQUENCE
    return out


def apply_wave(dry_run: bool = False) -> dict[str, Any]:
    hypotheses = build_web_hypothesis_index()
    sequences = target_sequences()
    added_position_entries: list[dict[str, Any]] = []
    skipped_non_public: list[str] = []

    for position_id, sequence in sequences.items():
        path = POSITIONS / f"{position_id}.yaml"
        position = load_yaml(path)
        claims = position.get("falsifiable_specific_claims") or []
        links = existing_links(position)
        needed = max(0, TARGET_FLOOR - len(links))
        blocks: list[dict[str, Any]] = []

        for hypothesis_id, mechanism in sequence:
            if needed == 0:
                break
            if hypothesis_id in links:
                continue
            hypothesis = hypotheses.get(hypothesis_id)
            if not hypothesis or not has_web_public_verdict(hypothesis_id, hypotheses):
                skipped_non_public.append(hypothesis_id)
                continue

            prediction, confidence = prediction_for(position_id, mechanism)
            claim_index = len(claims) + len(blocks)
            blocks.append(claim_block(position_id, mechanism, hypothesis))
            links.add(hypothesis_id)
            needed -= 1
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
            raise RuntimeError(f"{position_id} still needs {needed} links; add more curated public-tested hypotheses")

        if blocks and not dry_run:
            path.write_text(insert_fsc_yaml(path.read_text(), blocks))

    entries_by_hypothesis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in added_position_entries:
        entries_by_hypothesis[entry["hypothesis_id"]].append(entry)

    if not dry_run:
        for hypothesis_id, entries in entries_by_hypothesis.items():
            path = hypothesis_path(hypothesis_id)
            doc = load_yaml(path)
            existing = {
                (entry.get("position_id"), entry.get("claim_index"))
                for entry in doc.get("covers_claims") or []
            }
            cover_entries = []
            for entry in entries:
                key = (entry["position_id"], entry["claim_index"])
                if key in existing:
                    continue
                cover_entries.append(
                    {
                        "position_id": entry["position_id"],
                        "claim_index": entry["claim_index"],
                        "school_prediction": entry["school_prediction"],
                        "confidence": entry["confidence"],
                        "notes": (
                            f"{WAVE_NOTE} Mechanism family: {entry['mechanism']}. "
                            f"{POSITION_RATIONALE[entry['position_id']]}"
                        ),
                    }
                )
            if cover_entries:
                path.write_text(insert_covers_yaml(path.read_text(), cover_entries))

    by_position = defaultdict(int)
    by_hypothesis = defaultdict(int)
    for entry in added_position_entries:
        by_position[entry["position_id"]] += 1
        by_hypothesis[entry["hypothesis_id"]] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "target_floor": TARGET_FLOOR,
        "methodology": {
            "unit": "unique linked hypotheses per school; all selected hypotheses must already pass the public tested gate",
            "selection_rule": "fixed mechanism sequences per school family; no verdict-benefit filtering",
            "score_policy": "no diagnostics, verdicts, school predictions outside the added claims, or score weights are changed",
        },
        "added_claims": len(added_position_entries),
        "positions_touched": dict(sorted(by_position.items())),
        "hypotheses_touched": dict(sorted(by_hypothesis.items())),
        "skipped_non_public": sorted(set(skipped_non_public)),
        "entries": added_position_entries,
    }


def write_audit(audit: dict[str, Any]) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    json_path = AUDITS / f"target120_coverage_wave_{stamp}.json"
    md_path = AUDITS / f"target120_coverage_wave_{stamp}.md"
    json_path.write_text(json.dumps(audit, indent=2) + "\n")

    lines = [
        "# Target-120 Coverage Wave",
        "",
        f"Generated: {audit['generated_at']}",
        f"Dry run: `{audit['dry_run']}`",
        "",
        "## Methodology Gate",
        "",
        "- Stops selected schools at 120 unique linked hypotheses.",
        "- Only already-public-tested hypotheses are eligible.",
        "- Selection is mechanism-based and fixed before application; verdict effects are not used for selection.",
        "- Reciprocal position claims and hypothesis `covers_claims` entries are written together.",
        "",
        "## Summary",
        "",
        f"- Added claims: {audit['added_claims']}",
        f"- Positions touched: `{audit['positions_touched']}`",
        f"- Skipped non-public candidates: `{audit['skipped_non_public']}`",
        "",
        "## Entries",
        "",
        "| position | claim index | hypothesis | mechanism | prediction | confidence |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for entry in audit["entries"]:
        lines.append(
            f"| `{entry['position_id']}` | {entry['claim_index']} | `{entry['hypothesis_id']}` | "
            f"`{entry['mechanism']}` | `{entry['school_prediction']}` | `{entry['confidence']}` |"
        )
    md_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    audit = apply_wave(dry_run=args.dry_run)
    write_audit(audit)
    print(json.dumps({k: audit[k] for k in ("added_claims", "positions_touched", "skipped_non_public")}, indent=2))


if __name__ == "__main__":
    main()
