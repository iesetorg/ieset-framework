#!/usr/bin/env python3
"""Map the recovered 2026-05-02 verdict wave into position scoreboards.

This is intentionally narrow and idempotent. It only maps recovered runs that
already have matching hypothesis specs. Evidence-only runs with no spec remain
unmapped until promoted.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from backfill_hypothesis_schools import insert_fsc_yaml, make_claim_paraphrase


MARKET_STRONG = {
    "austrian": "supported",
    "chicago_monetarism": "supported",
    "classical_liberal": "supported",
    "ordoliberal": "supported",
    "empirical_pragmatist": "mixed",
    "institutionalism": "mixed",
    "developmentalism": "mixed",
    "post_keynesian": "falsified",
    "social_democratic": "falsified",
    "democratic_socialist": "falsified",
    "marxist_leninist": "falsified",
}

INSTITUTIONAL = {
    "institutionalism": "supported",
    "empirical_pragmatist": "supported",
    "ordoliberal": "supported",
    "new_keynesian": "supported",
    "developmentalism": "supported",
    "social_democratic": "supported",
    "classical_liberal": "mixed",
    "austrian": "mixed",
    "chicago_monetarism": "mixed",
}

MARKET_INSTITUTION = {
    "classical_liberal": "supported",
    "ordoliberal": "supported",
    "institutionalism": "supported",
    "empirical_pragmatist": "supported",
    "austrian": "mixed",
    "chicago_monetarism": "mixed",
    "developmentalism": "mixed",
    "new_keynesian": "mixed",
    "social_democratic": "mixed",
}

DEVELOPMENTAL_CONDITIONAL = {
    "developmentalism": "supported",
    "institutionalism": "supported",
    "empirical_pragmatist": "supported",
    "new_keynesian": "supported",
    "social_democratic": "supported",
    "ordoliberal": "mixed",
    "classical_liberal": "falsified",
    "austrian": "falsified",
    "chicago_monetarism": "falsified",
}

FLEXICURITY_COMPLEMENT = {
    "ordoliberal": "supported",
    "institutionalism": "supported",
    "empirical_pragmatist": "supported",
    "new_keynesian": "supported",
    "social_democratic": "supported",
    "classical_liberal": "mixed",
    "austrian": "mixed",
    "chicago_monetarism": "mixed",
}

HYPOTHESIS_POLES = {
    "australia_hawke_keating_reform_long_run": MARKET_STRONG,
    "bankruptcy_law_efficiency_capital_reallocation": MARKET_INSTITUTION,
    "canada_market_liberalisation_vs_state_industry_1988_2024": MARKET_STRONG,
    "catch_up_growth_fades_after_middle_income_threshold_v2": MARKET_INSTITUTION,
    "contract_enforcement_fdi_productivity_spillovers": INSTITUTIONAL,
    "firm_entry_rate_long_run_productivity": MARKET_STRONG,
    "frontier_income_volatility_state_allocation": MARKET_STRONG,
    "industrial_policy_high_governance_success": DEVELOPMENTAL_CONDITIONAL,
    "poland_market_transition_30yr_growth": MARKET_STRONG,
    "sweden_1990s_market_reform_recovery": MARKET_STRONG,
    "uk_thatcher_market_reform_40yr_services_frontier": MARKET_STRONG,
    "unilateral_tariff_liberalisation_growth_20yr": MARKET_STRONG,
    "rule_of_law_market_reform_complementarity": MARKET_INSTITUTION,
    "corruption_state_allocation_growth_interaction": INSTITUTIONAL,
    "labour_flexibility_security_complement": FLEXICURITY_COMPLEMENT,
    "constitutional_fiscal_rules_growth_stability": MARKET_INSTITUTION,
    "government_consumption_share_tfp": MARKET_STRONG,
    "judicial_independence_growth_persistence": INSTITUTIONAL,
    "chile_market_reform_long_horizon_with_democracy": MARKET_INSTITUTION,
    "new_zealand_reform_long_run_productivity_recheck": MARKET_INSTITUTION,
    "property_rights_long_run_income_frontier_v2": MARKET_INSTITUTION,
    "state_capacity_precedes_liberal_market": INSTITUTIONAL,
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def hypothesis_paths() -> dict[str, Path]:
    out = {}
    for path in (ROOT / "hypotheses").glob("*/*.yaml"):
        if path.parent.name == "steelman":
            continue
        doc = load_yaml(path)
        hid = doc.get("hypothesis_id")
        if hid:
            out[hid] = path
    return out


def position_paths() -> dict[str, Path]:
    out = {}
    for path in (ROOT / "positions").glob("*.yaml"):
        if path.name.startswith("_"):
            continue
        doc = load_yaml(path)
        pid = doc.get("position_id")
        if pid:
            out[pid] = path
    return out


def verdict_status(hid: str) -> str:
    path = ROOT / "engine" / "runs" / hid / "diagnostics.json"
    if not path.exists():
        return "untested"
    doc = json.loads(path.read_text())
    raw = str(doc.get("verdict_label") or doc.get("verdict") or "").lower()
    if "support" in raw:
        return "supported"
    if "refut" in raw:
        return "falsified"
    if "partial" in raw or "mixed" in raw:
        return "mixed"
    if "inconclusive" in raw or "pending" in raw:
        return "inconclusive"
    return raw.split(" ")[0] if raw else "untested"


def render_covers(entries: list[dict], item_indent: int = 0) -> str:
    pad_item = " " * item_indent
    pad_key = " " * (item_indent + 2)
    out = ""
    for e in entries:
        out += f"{pad_item}- position_id: {e['position_id']}\n"
        out += f"{pad_key}claim_index: {e['claim_index']}\n"
        out += f"{pad_key}polarity: aligned\n"
        out += f"{pad_key}school_prediction: {e['school_prediction']}\n"
        out += f"{pad_key}confidence: {e['confidence']}\n"
        out += f"{pad_key}notes: {e['notes']!r}\n"
    return out


def insert_covers_yaml(text: str, entries: list[dict]) -> str:
    lines = text.splitlines(keepends=True)
    idx = None
    for i, line in enumerate(lines):
        if line.startswith("covers_claims:"):
            idx = i
            break
    if idx is None:
        return text.rstrip() + "\n\ncovers_claims:\n" + render_covers(entries)

    end = len(lines)
    for j in range(idx + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        if line[0] in (" ", "\t", "#") or line.startswith("- "):
            continue
        end = j
        break
    return "".join(lines[:end]) + render_covers(entries) + "".join(lines[end:])


def main() -> int:
    hpaths = hypothesis_paths()
    ppaths = position_paths()
    missing_specs = [hid for hid in HYPOTHESIS_POLES if hid not in hpaths]
    if missing_specs:
        print("missing specs:")
        for hid in missing_specs:
            print(f"  - {hid}")
        return 1

    position_docs = {pid: load_yaml(path) for pid, path in ppaths.items()}
    hypothesis_docs = {hid: load_yaml(path) for hid, path in hpaths.items()}

    per_position: dict[str, list[dict]] = defaultdict(list)
    for hid, mapping in HYPOTHESIS_POLES.items():
        h = hypothesis_docs[hid]
        status = verdict_status(hid)
        for pid, prediction in mapping.items():
            if pid not in ppaths:
                continue
            claims = position_docs[pid].get("falsifiable_specific_claims") or []
            if any(c.get("linked_hypothesis_id") == hid for c in claims):
                continue
            per_position[pid].append(
                {
                    "claim": make_claim_paraphrase(h),
                    "linked_hypothesis_id": hid,
                    "school_prediction": prediction,
                    "claim_polarity": "aligned",
                    "empirical_status": status,
                    "scope": h.get("scope") or {},
                    "notes": (
                        "Phase 4E recovery mapping: recovered 2026-05-02 "
                        "verdict wave; hypothesis-side covers_claims is authoritative."
                    ),
                }
            )

    added_claims = 0
    for pid, blocks in sorted(per_position.items()):
        if not blocks:
            continue
        path = ppaths[pid]
        text = path.read_text()
        new_text = insert_fsc_yaml(text, blocks)
        if new_text != text:
            path.write_text(new_text)
            added_claims += len(blocks)
            print(f"mapped position {pid}: +{len(blocks)} claims")

    # Reload positions after appending so claim indices are exact.
    position_docs = {pid: load_yaml(path) for pid, path in ppaths.items()}
    per_hypothesis_covers: dict[str, list[dict]] = defaultdict(list)
    for hid, mapping in HYPOTHESIS_POLES.items():
        for pid, prediction in mapping.items():
            claims = position_docs[pid].get("falsifiable_specific_claims") or []
            for idx, claim in enumerate(claims):
                if claim.get("linked_hypothesis_id") == hid:
                    hdoc = hypothesis_docs[hid]
                    covers = hdoc.get("covers_claims") or []
                    if any(
                        e.get("position_id") == pid and e.get("claim_index") == idx
                        for e in covers
                    ):
                        break
                    per_hypothesis_covers[hid].append(
                        {
                            "position_id": pid,
                            "claim_index": idx,
                            "school_prediction": prediction,
                            "confidence": "medium",
                            "notes": (
                                "Phase 4E recovery mapping for the 2026-05-02 "
                                "recovered verdict wave; position claim restates "
                                "this pre-registered hypothesis as a school prediction."
                            ),
                        }
                    )
                    break

    added_covers = 0
    for hid, entries in sorted(per_hypothesis_covers.items()):
        if not entries:
            continue
        path = hpaths[hid]
        text = path.read_text()
        new_text = insert_covers_yaml(text, entries)
        if new_text != text:
            path.write_text(new_text)
            added_covers += len(entries)
            print(f"mapped hypothesis {hid}: +{len(entries)} covers_claims")

    print(f"added position claims: {added_claims}")
    print(f"added hypothesis covers_claims: {added_covers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
