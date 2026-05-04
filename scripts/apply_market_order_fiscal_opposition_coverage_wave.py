#!/usr/bin/env python3
"""Add a bounded fiscal market-order opposition coverage wave.

This wave links already tested, pre-registered fiscal market-order panel
hypotheses to under-covered schools with a clear theoretical stake in public
spending and tax-burden claims. It is coverage balancing only: no verdicts are
changed and selection is fixed before considering any school score effect.
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

HYPOTHESIS_IDS = [
    "market_order_government_spending_investment_share_panel",
    "market_order_government_spending_gdp_pc_growth_panel",
    "market_order_government_spending_private_credit_depth_panel",
    "market_order_government_spending_employment_rate_panel",
    "market_order_tax_burden_investment_share_panel",
    "market_order_tax_burden_gdp_pc_growth_panel",
]

POSITION_PREDICTIONS = {
    "eco_socialist": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "Eco-socialism",
        "rationale": "Eco-socialism disputes the premise that larger public sectors or tax capacity generally depress real outcomes when spending redirects investment toward social and ecological goals.",
    },
    "marxist_leninist": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "Marxist-Leninist political economy",
        "rationale": "Marxist-Leninist theory disputes small-state fiscal claims and expects state-directed accumulation to substitute for private allocation in strategic sectors.",
    },
    "democratic_socialist": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "Democratic socialism",
        "rationale": "Democratic socialism disputes broad claims that tax-financed public provision and public investment generally reduce employment, growth, or investment.",
    },
    "post_keynesian": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "Post-Keynesian economics",
        "rationale": "Post-Keynesian theory emphasizes demand, uncertainty, and crowding-in channels, so it disputes mechanical fiscal crowding-out claims in broad panels.",
    },
    "new_keynesian": {
        "prediction": "mixed",
        "confidence": "medium",
        "school_label": "New Keynesian economics",
        "rationale": "New Keynesian models make fiscal effects state-contingent: crowding out can occur near capacity, while stabilization and demand channels can offset it.",
    },
}

WAVE_NOTE = (
    "2026-05-03 market-order fiscal opposition coverage wave; fixed mechanism-based "
    "selection from pre-registered fiscal panel hypotheses, independent of observed verdicts."
)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def hypothesis_path(hypothesis_id: str) -> Path:
    matches = sorted(HYPOTHESES.glob(f"*/{hypothesis_id}.yaml"))
    if not matches:
        raise FileNotFoundError(hypothesis_id)
    return matches[0]


def claim_text(position_id: str, prediction: str, hypothesis: dict) -> str:
    school = POSITION_PREDICTIONS[position_id]["school_label"]
    claim = " ".join(str(hypothesis.get("claim") or "").split())
    if len(claim) > 300:
        claim = claim[:297] + "..."
    if prediction == "mixed":
        return f"{school} treats this fiscal market-order panel claim as state-contingent rather than general: {claim}"
    return f"{school} predicts this fiscal market-order panel claim should not hold as a general rule: {claim}"


def claim_block(position_id: str, hypothesis: dict) -> dict:
    prediction = POSITION_PREDICTIONS[position_id]["prediction"]
    return {
        "claim": claim_text(position_id, prediction, hypothesis),
        "linked_hypothesis_id": hypothesis["hypothesis_id"],
        "school_prediction": prediction,
        "claim_polarity": "aligned",
        "empirical_status": "untested",
        "scope": hypothesis.get("scope") or {},
        "notes": f"{WAVE_NOTE} {POSITION_PREDICTIONS[position_id]['rationale']}",
    }


def existing_links(position: dict) -> set[str]:
    return {
        claim.get("linked_hypothesis_id")
        for claim in position.get("falsifiable_specific_claims") or []
        if claim.get("linked_hypothesis_id")
    }


def append_position_claims(hypotheses: dict[str, dict]) -> dict[tuple[str, str], int]:
    claim_indexes: dict[tuple[str, str], int] = {}
    blocks_by_position: dict[str, list[dict]] = defaultdict(list)
    start_index: dict[str, int] = {}

    for position_id in POSITION_PREDICTIONS:
        path = POSITIONS / f"{position_id}.yaml"
        position = load_yaml(path)
        claims = position.get("falsifiable_specific_claims") or []
        links = existing_links(position)
        start_index[position_id] = len(claims)
        for hypothesis_id in HYPOTHESIS_IDS:
            if hypothesis_id in links:
                for idx, claim in enumerate(claims):
                    if claim.get("linked_hypothesis_id") == hypothesis_id:
                        claim_indexes[(position_id, hypothesis_id)] = idx
                        break
                continue
            block = claim_block(position_id, hypotheses[hypothesis_id])
            offset = len(blocks_by_position[position_id])
            claim_indexes[(position_id, hypothesis_id)] = start_index[position_id] + offset
            blocks_by_position[position_id].append(block)

    for position_id, blocks in blocks_by_position.items():
        if not blocks:
            continue
        path = POSITIONS / f"{position_id}.yaml"
        path.write_text(insert_fsc_yaml(path.read_text(), blocks))

    return claim_indexes


def update_hypothesis_covers(claim_indexes: dict[tuple[str, str], int]) -> list[dict]:
    entries: list[dict] = []
    for hypothesis_id in HYPOTHESIS_IDS:
        path = hypothesis_path(hypothesis_id)
        doc = load_yaml(path)
        covers = doc.setdefault("covers_claims", [])
        existing = {(entry.get("position_id"), entry.get("claim_index")) for entry in covers}
        path_entries: list[dict] = []

        for position_id in POSITION_PREDICTIONS:
            claim_index = claim_indexes[(position_id, hypothesis_id)]
            if (position_id, claim_index) in existing:
                continue
            pred = POSITION_PREDICTIONS[position_id]
            entry = {
                "position_id": position_id,
                "claim_index": claim_index,
                "polarity": "aligned",
                "school_prediction": pred["prediction"],
                "confidence": pred["confidence"],
                "notes": f"{WAVE_NOTE} {pred['rationale']}",
            }
            covers.append(entry)
            path_entries.append(entry)
            entries.append({"hypothesis_id": hypothesis_id, **entry})

        if path_entries:
            path.write_text(insert_covers_yaml(path.read_text(), path_entries))

    return entries


def write_audit(entries: list[dict]) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    stamp = "2026-05-03"
    by_position: dict[str, int] = defaultdict(int)
    by_prediction: dict[str, int] = defaultdict(int)
    for entry in entries:
        by_position[entry["position_id"]] += 1
        by_prediction[entry["school_prediction"]] += 1

    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "wave": "market_order_fiscal_opposition_coverage_wave",
        "methodology_gate": {
            "selection_rule": "Fixed 6 fiscal market-order panel hypotheses crossed with 5 under-covered schools.",
            "not_selected_by": "observed verdicts or school score effect",
            "verdict_policy": "No verdicts changed; only reciprocal position links and covers_claims were added.",
            "score_caution": "New Keynesian links are mixed because fiscal effects are state-contingent in the theory.",
        },
        "hypotheses": HYPOTHESIS_IDS,
        "positions": POSITION_PREDICTIONS,
        "new_links": len(entries),
        "new_links_by_position": dict(sorted(by_position.items())),
        "new_links_by_school_prediction": dict(sorted(by_prediction.items())),
        "entries": entries,
    }

    json_path = AUDITS / f"market_order_fiscal_opposition_coverage_wave_{stamp}.json"
    md_path = AUDITS / f"market_order_fiscal_opposition_coverage_wave_{stamp}.md"
    json_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Market-Order Fiscal Opposition Coverage Wave",
        "",
        f"Generated: {doc['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- Fixed 6 fiscal market-order panel hypotheses crossed with 5 under-covered schools.",
        "- Selection is mechanism-based, not verdict-based.",
        "- No verdicts changed; only reciprocal position links and `covers_claims` entries were added.",
        "- New Keynesian links are `mixed` because fiscal effects are state-contingent in the theory.",
        "",
        "## Counts",
        "",
        f"- New reciprocal links: {len(entries)}",
    ]
    for position_id, count in sorted(by_position.items()):
        lines.append(f"- {position_id}: {count}")
    lines += ["", "## Hypotheses", ""]
    for hypothesis_id in HYPOTHESIS_IDS:
        lines.append(f"- `{hypothesis_id}`")
    md_path.write_text("\n".join(lines) + "\n")

    print(f"wrote {json_path.relative_to(ROOT)}")
    print(f"wrote {md_path.relative_to(ROOT)}")
    print(json.dumps({"new_links": len(entries), "by_position": dict(by_position)}, sort_keys=True))


def main() -> int:
    hypotheses = {hypothesis_id: load_yaml(hypothesis_path(hypothesis_id)) for hypothesis_id in HYPOTHESIS_IDS}
    claim_indexes = append_position_claims(hypotheses)
    entries = update_hypothesis_covers(claim_indexes)
    write_audit(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
