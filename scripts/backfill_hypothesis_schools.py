#!/usr/bin/env python3
"""Backfill school predictions on orphan hypotheses (those with no
falsifiable_specific_claims pointing at them from any position file).

Method (pole-classified mechanical projection):

1. Each orphan hypothesis is hand-classified into one of 5 ideological poles
   based on its claim's directional implication:

   - MARKET_LIBERAL_POLE: hypothesis claims a market-liberal policy works
     (small state, deregulation, anti-rent-control, anti-wealth-tax) or that
     a non-market regime fails (Venezuela, Cuba, USSR, Great Leap Forward).
   - INTERVENTIONIST_POLE: hypothesis claims redistribution / state action /
     coordination works (Lula Bolsa Familia, industrial policy).
   - INSTITUTIONAL_POLE: hypothesis claims institutional quality matters
     more than market depth (Nordic decomposition, intergen mobility).
   - ECOLOGICAL_POLE: hypothesis claims green-transition costs are
     acceptable / phaseouts succeed.
   - EMPIRICAL_NEUTRAL: pure measurement / decomposition, no clear pole.

2. For each (pole, school) cell, a pre-defined verdict captures what that
   school would expect a hypothesis at that pole to find.

3. For each orphan: lookup its pole; for each school in the pole-row, emit
   a falsifiable_specific_claim with school_prediction = matrix[pole][school].

4. Scope is copied from the hypothesis (canonical scope). Polarity is
   "aligned" — i.e. the claim is paraphrased in the same direction as the
   hypothesis's pre-reg claim, so verdict labels mean what they say.

5. Each emitted block carries notes "derived: pole=<X> (mechanical
   backfill v1)" so audits can grep these and a human can curate later.

Usage:
    python scripts/backfill_hypothesis_schools.py            # dry run
    python scripts/backfill_hypothesis_schools.py --apply    # write
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


# Hand-classified pole assignments for the 56 orphan hypotheses.
# "market" = market-liberal-pole (anti-state / pro-deregulation / case study
#   showing socialist regime fails)
# "intervene" = interventionist-pole (state / redistribution / industrial
#   policy works)
# "institution" = institutional-quality-pole (governance matters more than
#   policy direction; Nordic/intergen)
# "ecological" = ecological-pole (green policy succeeds)
# "neutral" = empirical_neutral (decomposition without an ideological pole)
ORPHAN_POLES = {
    # institutional_quality
    "nordic_outcome_persistence_decomposition_v2": "institution",
    "nordic_outcome_persistence_decomposition_v3": "institution",
    "bukele_mass_incarceration_homicide_impact_2019_2024": "market",
    "venezuela_chavismo_canonical_case_multi_metric": "market",
    "resource_rent_capture_outperforms_laissez_faire": "intervene",
    # fiscal
    "bukele_fiscal_trajectory_tax_cuts_imf_2019_2024": "market",
    "universal_transfer_programmes_labour_force_participation_decline": "market",
    "wealth_tax_capital_flight_revenue_yield_gap": "market",
    "state_size_reduces_household_income_growth": "market",
    # energy
    "eu_post_2021_gas_shock_industrial_output_impact": "market",
    "green_transition_cost_trajectory_electricity_prices": "market",
    "nuclear_phaseout_energy_cost_industry_exit": "market",
    "nuclear_phaseout_grid_reliability_cost_tradeoff": "market",
    # distribution
    "housing_cost_driven_real_wage_divergence": "market",
    "uk_real_wage_stagnation_2008_present_decomposition": "neutral",
    "intergenerational_mobility_cross_country": "institution",
    "lula_bolsa_familia_poverty_reduction_decomposition_2003_2010": "intervene",
    # regulatory
    "germany_decline_2018_2025_regulatory_not_fiscal": "market",
    "precautionary_regulation_innovation_productivity_gap_eu_us": "market",
    "gdpr_digital_sector_firm_scale_effect": "market",
    "eu_chemical_reach_regulation_firm_exit_effect": "market",
    "price_controls_shortage_black_market_progression": "market",
    "eu_cbam_export_competitiveness_2023_onwards": "market",
    # housing
    "rent_control_housing_supply_quality_decay_chain": "market",
    # monetary
    "argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023": "market",
    "bitcoin_legal_tender_remittance_adoption_2021_2024": "neutral",
    "monetary_finance_deficit_currency_collapse_chain": "market",
    # growth
    "italian_stagnation_decomposition_1999_2023": "market",
    "bukele_fdi_gdp_investment_climate_2019_2024": "market",
    "india_1991_liberalisation_growth_acceleration": "market",
    "chile_vs_venezuela_divergence_1999_2023": "market",
    "uk_economic_decline_multi_movement": "market",
    "canada_gdp_per_capita_stagnation_post_2015": "market",
    "nationalisation_investment_productivity_decline_venezuela": "market",
    "german_manufacturing_va_decline_2017_2024": "market",
    "spain_sanchez_economic_trajectory_2018_2023": "market",
    "us_eu_divergence_decomposition": "market",
    "great_leap_forward_famine_output_collapse_1959_1961": "market",
    "china_deng_reform_growth_acceleration_1978": "market",
    "hong_kong_minimal_state_growth_miracle_1960_1997": "market",
    "asian_convergence_vs_western_stagnation_2000_2023": "market",
    "cuba_socialist_economy_stagnation_1960_2023": "market",
    "west_east_germany_economic_system_divergence_1950_1989": "market",
    "north_south_korea_development_divergence_1953_present": "market",
    "industrial_policy_developmentalist_states_growth": "intervene",
    "el_salvador_bukele_gdp_crime_tradeoff_2019_2024": "market",
    "estonia_market_reform_post_soviet_growth_1991_2007": "market",
    "soviet_union_central_planning_gdp_collapse_1989_1991": "market",
    # labour
    "spain_reported_sexual_assault_rate_definition_controlled": "neutral",
    "immigration_crime_rate_vs_native_controlled": "neutral",
    "labour_market_flexibility_unemployment_duration": "market",
    "canada_real_disposable_income_post_2015": "market",
    "immigration_net_fiscal_contribution_by_origin_skill_duration": "neutral",
    "second_generation_education_outcomes_by_origin": "neutral",
    "strong_union_labour_law_youth_unemployment_south_europe": "market",
    "minimum_wage_above_median_employment_teen_effects": "market",
}


# Pole × school verdict matrix.
# Cell value: "supported" | "falsified" | "mixed" | None (skip).
# Schools that aren't strongly aligned with the pole get "mixed" so they
# are visible-but-uncommitted; schools way out of pole get None to avoid
# noise.
POLE_VERDICTS: dict[str, dict[str, str | None]] = {
    "market": {
        "austrian": "supported",
        "chicago_monetarism": "supported",
        "classical_liberal": "supported",
        "ordoliberal": "supported",
        "new_keynesian": "mixed",
        "empirical_pragmatist": "mixed",
        "institutionalism": "mixed",
        "developmentalism": "mixed",
        "post_keynesian": "falsified",
        "mmt": "falsified",
        "social_democratic": "falsified",
        "democratic_socialist": "falsified",
        "market_socialist": "falsified",
        "marxian": "falsified",
        "marxist_leninist": "falsified",
        "eco_socialist": "falsified",
        "degrowth": "falsified",
    },
    "intervene": {
        "austrian": "falsified",
        "chicago_monetarism": "falsified",
        "classical_liberal": "falsified",
        "ordoliberal": "mixed",
        "new_keynesian": "mixed",
        "empirical_pragmatist": "mixed",
        "institutionalism": "supported",
        "developmentalism": "supported",
        "post_keynesian": "supported",
        "mmt": "supported",
        "social_democratic": "supported",
        "democratic_socialist": "supported",
        "market_socialist": "supported",
        "marxian": "supported",
        "marxist_leninist": "mixed",
        "eco_socialist": "supported",
        "degrowth": "mixed",
    },
    "institution": {
        "austrian": "mixed",
        "chicago_monetarism": "mixed",
        "classical_liberal": "mixed",
        "ordoliberal": "supported",
        "new_keynesian": "supported",
        "empirical_pragmatist": "supported",
        "institutionalism": "supported",
        "developmentalism": "supported",
        "post_keynesian": "supported",
        "mmt": "mixed",
        "social_democratic": "supported",
        "democratic_socialist": "supported",
        "market_socialist": "supported",
        "marxian": "mixed",
        "marxist_leninist": "mixed",
        "eco_socialist": "mixed",
        "degrowth": "mixed",
    },
    "ecological": {
        "austrian": "falsified",
        "chicago_monetarism": "falsified",
        "classical_liberal": "falsified",
        "ordoliberal": "mixed",
        "new_keynesian": "mixed",
        "empirical_pragmatist": "mixed",
        "institutionalism": "mixed",
        "developmentalism": "mixed",
        "post_keynesian": "mixed",
        "mmt": "mixed",
        "social_democratic": "supported",
        "democratic_socialist": "supported",
        "market_socialist": "mixed",
        "marxian": "mixed",
        "marxist_leninist": "mixed",
        "eco_socialist": "supported",
        "degrowth": "supported",
    },
    "neutral": {},  # emit nothing — too descriptive to assign poles
}


def load_hypotheses() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in (ROOT / "hypotheses").rglob("*.yaml"):
        with p.open() as f:
            doc = yaml.safe_load(f) or {}
        if not doc.get("hypothesis_id"):
            continue
        out[doc["hypothesis_id"]] = doc
    return out


def load_positions() -> list[tuple[Path, dict]]:
    out = []
    for p in sorted((ROOT / "positions").glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        with p.open() as f:
            doc = yaml.safe_load(f) or {}
        if not doc.get("position_id"):
            continue
        out.append((p, doc))
    return out


def find_orphan_hypotheses(
    positions: list[tuple[Path, dict]], hypotheses: dict[str, dict]
) -> list[dict]:
    referenced: set[str] = set()
    for _, pos_doc in positions:
        for fsc in pos_doc.get("falsifiable_specific_claims") or []:
            hid = fsc.get("linked_hypothesis_id")
            if hid:
                referenced.add(hid)
    return [h for hid, h in hypotheses.items() if hid not in referenced]


def make_claim_paraphrase(h: dict) -> str:
    raw_claim = (h.get("claim") or "").strip()
    first = raw_claim.split(". ")[0].strip()
    if first.endswith(","):
        first = first[:-1]
    if len(first) > 220:
        first = first[:217] + "..."
    return first


def yaml_quote(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def yaml_scalar(v) -> str:
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        if any(c in v for c in " :,'\"") or v in ("true", "false", "null"):
            return yaml_quote(v)
        return v
    return yaml_quote(str(v))


def yaml_inline(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(yaml_scalar(x) for x in v) + "]"
    return yaml_scalar(v)


def render_fsc_yaml(blocks: list[dict], item_indent: int = 2) -> str:
    """Render fsc blocks as YAML text. `item_indent` is the column the `-`
    starts at; key indentation is item_indent + 2."""
    pad_item = " " * item_indent
    pad_key = " " * (item_indent + 2)
    pad_inner = " " * (item_indent + 4)
    out = ""
    for b in blocks:
        out += f"{pad_item}- claim: " + yaml_quote(b["claim"]) + "\n"
        out += f"{pad_key}linked_hypothesis_id: {b['linked_hypothesis_id']}\n"
        out += f"{pad_key}school_prediction: {b['school_prediction']}\n"
        out += f"{pad_key}claim_polarity: {b['claim_polarity']}\n"
        out += f"{pad_key}empirical_status: {b['empirical_status']}\n"
        out += f"{pad_key}scope:\n"
        scope = b["scope"] or {}
        for k in ("period", "countries", "outcome_dim", "policy_family",
                  "treatment_tags"):
            v = scope.get(k)
            if v is None:
                continue
            out += f"{pad_inner}{k}: {yaml_inline(v)}\n"
        out += f"{pad_key}notes: " + yaml_quote(b["notes"]) + "\n"
    return out


def detect_fsc_indent(lines: list[str], fsc_idx: int) -> int:
    """Look at the first item line after fsc_idx and return its column-of-`-`.
    Defaults to 2 if no item exists yet."""
    for j in range(fsc_idx + 1, min(fsc_idx + 100, len(lines))):
        line = lines[j].rstrip("\n")
        # Find the first list-item line: leading whitespace then `-`
        stripped = line.lstrip(" ")
        if stripped.startswith("- "):
            return len(line) - len(stripped)
        # If we hit a non-empty line that doesn't start with `-`/space, stop
        if line.strip() and not line.startswith((" ", "\t", "#")):
            break
    return 2


def insert_fsc_yaml(text: str, blocks: list[dict]) -> str:
    lines = text.splitlines(keepends=True)

    # Look for an existing falsifiable_specific_claims: section
    fsc_idx = None
    for i, line in enumerate(lines):
        if line.startswith("falsifiable_specific_claims:"):
            fsc_idx = i
            break

    if fsc_idx is not None:
        item_indent = detect_fsc_indent(lines, fsc_idx)
        new_yaml = render_fsc_yaml(blocks, item_indent=item_indent)
        # Find end of the fsc section by scanning until we hit a top-level
        # YAML key (line at column 0 that's not a list item starting `- `).
        end = len(lines)
        for j in range(fsc_idx + 1, len(lines)):
            line = lines[j]
            if not line.strip():
                continue
            # `- foo:` at column 0 is still a fsc list item if items are
            # 0-indented; only a non-list, non-indented key ends the section.
            if line[0] in (" ", "\t", "#"):
                continue
            if line.startswith("- "):
                continue  # still a list item at column 0
            end = j
            break
        return "".join(lines[:end]) + new_yaml + "".join(lines[end:])

    # No existing section: create one before empirical_record_summary, etc.
    new_yaml = render_fsc_yaml(blocks, item_indent=2)
    block_yaml = "falsifiable_specific_claims:\n" + new_yaml
    insert_at = None
    for i, line in enumerate(lines):
        for k in ("empirical_record_summary:", "scope_decisions:",
                  "linked_hypotheses:", "map:", "notes:"):
            if line.startswith(k):
                insert_at = i
                break
        if insert_at is not None:
            break
    if insert_at is None:
        return text.rstrip() + "\n\n" + block_yaml
    return "".join(lines[:insert_at]) + block_yaml + "\n" + "".join(
        lines[insert_at:]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    hypotheses = load_hypotheses()
    print(f"loaded {len(hypotheses)} hypotheses")

    positions = load_positions()
    print(f"loaded {len(positions)} positions")

    orphans = find_orphan_hypotheses(positions, hypotheses)
    print(f"\norphan hypotheses (no school predictions): {len(orphans)}")

    # Sanity-check pole classification covers all orphans
    missing_poles = [h["hypothesis_id"] for h in orphans
                     if h["hypothesis_id"] not in ORPHAN_POLES]
    if missing_poles:
        print(f"\nORPHANS WITHOUT POLE ASSIGNMENT ({len(missing_poles)}):")
        for hid in missing_poles:
            print(f"  - {hid}")
        print("Add these to ORPHAN_POLES dict before running.")
        return 1

    # Build per-position prediction batches
    per_position: dict[str, list[dict]] = defaultdict(list)
    skipped_orphans = []
    label_dist: Counter = Counter()
    pole_dist: Counter = Counter()
    pos_ids = {pd["position_id"] for _, pd in positions}

    for h in orphans:
        pole = ORPHAN_POLES[h["hypothesis_id"]]
        pole_dist[pole] += 1
        verdicts = POLE_VERDICTS.get(pole) or {}
        if not verdicts:
            skipped_orphans.append(h["hypothesis_id"])
            continue
        for pos_id, verdict in verdicts.items():
            if verdict is None:
                continue
            if pos_id not in pos_ids:
                continue  # position file doesn't exist
            block = {
                "claim": make_claim_paraphrase(h),
                "linked_hypothesis_id": h["hypothesis_id"],
                "school_prediction": verdict,
                "claim_polarity": "aligned",
                "empirical_status": "untested",
                "scope": h.get("scope") or {},
                "notes": (
                    f"derived: pole={pole} (mechanical backfill v1; "
                    f"please curate)"
                ),
            }
            per_position[pos_id].append(block)
            label_dist[verdict] += 1

    print(f"\npole distribution across orphans:")
    for k, v in sorted(pole_dist.items()):
        print(f"  {k:14s}: {v}")
    print(f"  skipped (neutral or unknown pole): {len(skipped_orphans)}")
    if skipped_orphans:
        for hid in skipped_orphans[:8]:
            print(f"    - {hid}")
        if len(skipped_orphans) > 8:
            print(f"    ... and {len(skipped_orphans)-8} more")

    print(f"\nverdict distribution: {dict(label_dist)}")
    print(f"total new specific claims: {sum(len(v) for v in per_position.values())}")

    print(f"\npredictions per position:")
    for pid in sorted(per_position):
        blocks = per_position[pid]
        verdict_counts = Counter(b["school_prediction"] for b in blocks)
        print(
            f"  {pid:25s}  +{len(blocks):3d}  "
            + " ".join(f"{k}={v}" for k, v in verdict_counts.most_common())
        )

    # Sample 3 from a polar opposite (austrian and post_keynesian)
    for sample_pid in ("austrian", "post_keynesian"):
        blocks = per_position.get(sample_pid) or []
        if blocks:
            print(f"\nsample {sample_pid}:")
            for b in blocks[:3]:
                print(f"  → {b['linked_hypothesis_id']}: {b['school_prediction']}")
                print(f"    \"{b['claim'][:100]}\"")

    if args.apply:
        print(f"\napplying...")
    else:
        print(f"\nDry run only. Re-run with --apply to write changes.")
        return 0

    written = 0
    for pos_path, pos_doc in positions:
        pos_id = pos_doc["position_id"]
        blocks = per_position.get(pos_id) or []
        if not blocks:
            continue
        if args.limit and written >= args.limit:
            break
        text = pos_path.read_text()
        new_text = insert_fsc_yaml(text, blocks)
        if new_text != text:
            pos_path.write_text(new_text)
            written += 1
            print(f"  wrote {pos_id}: +{len(blocks)} claims")
    print(f"\nWrote {written} position files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
