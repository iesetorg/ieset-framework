#!/usr/bin/env python3
"""Add a bounded school-coverage wave for market-order panel hypotheses.

This wave is coverage balancing, not verdict shopping. It links the same fixed
set of fiscal/monetary market-order panel hypotheses to under-covered schools
whose theories have an opposition or conditional stake in those claims. The
selection rule is mechanism-based and independent of the observed verdicts.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

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
    "market_order_sound_money_investment_share_panel",
    "market_order_sound_money_gdp_pc_growth_panel",
    "market_order_sound_money_private_credit_depth_panel",
    "market_order_sound_money_employment_rate_panel",
    "market_order_tax_burden_investment_share_panel",
    "market_order_tax_burden_gdp_pc_growth_panel",
]

POSITION_PREDICTIONS = {
    "mmt": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "MMT",
        "rationale": "MMT disputes broad claims that larger public sectors, tax capacity, or non-accommodating anti-inflation regimes mechanically depress real outcomes.",
    },
    "market_socialist": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "Market socialism",
        "rationale": "Market socialism disputes the small-state implication and predicts market allocation can coexist with socialized capital and public investment.",
    },
    "degrowth": {
        "prediction": "mixed",
        "confidence": "low",
        "school_label": "Degrowth",
        "rationale": "Degrowth treats GDP, investment, and private-credit outcomes as welfare-ambiguous, so these are conditional stakes rather than directional wins.",
    },
    "marxian": {
        "prediction": "falsified",
        "confidence": "medium",
        "school_label": "Marxian political economy",
        "rationale": "Marxian theory disputes that market-order fiscal and monetary proxies generally deliver broad real-economy gains once class and accumulation dynamics are considered.",
    },
}

WAVE_NOTE = (
    "2026-05-03 market-order opposition coverage wave; fixed mechanism-based selection "
    "from pre-registered panel hypotheses, independent of observed verdicts."
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
        return f"{school} treats this market-order panel claim as conditional rather than dispositive: {claim}"
    return f"{school} predicts this market-order panel claim should not hold as a general rule: {claim}"


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


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_cover_entries(entries: list[dict], item_indent: int = 0) -> str:
    pad_item = " " * item_indent
    pad_key = " " * (item_indent + 2)
    out = ""
    for entry in entries:
        out += f"{pad_item}- position_id: {entry['position_id']}\n"
        out += f"{pad_key}claim_index: {entry['claim_index']}\n"
        out += f"{pad_key}polarity: aligned\n"
        out += f"{pad_key}school_prediction: {entry['school_prediction']}\n"
        out += f"{pad_key}confidence: {entry['confidence']}\n"
        out += f"{pad_key}notes: {yaml_quote(entry['notes'])}\n"
    return out


def detect_cover_indent(lines: list[str], covers_idx: int) -> int:
    for line in lines[covers_idx + 1:]:
        if not line.strip():
            continue
        stripped = line.lstrip(" ")
        if stripped.startswith("- "):
            return len(line) - len(stripped)
        if line[0] not in (" ", "\t", "#"):
            break
    return 0


def insert_covers_yaml(text: str, entries: list[dict]) -> str:
    if not entries:
        return text
    lines = text.splitlines(keepends=True)
    covers_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("covers_claims:"):
            covers_idx = idx
            break

    if covers_idx is None:
        insert_at = None
        for idx, line in enumerate(lines):
            if line.startswith("notes:"):
                insert_at = idx
                break
        rendered = render_cover_entries(entries, item_indent=0)
        block = "covers_claims:\n" + rendered
        if insert_at is None:
            return text.rstrip() + "\n" + block
        return "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])

    item_indent = detect_cover_indent(lines, covers_idx)
    rendered = render_cover_entries(entries, item_indent=item_indent)
    end = len(lines)
    for idx in range(covers_idx + 1, len(lines)):
        line = lines[idx]
        if not line.strip():
            continue
        if line[0] in (" ", "\t", "#") or line.startswith("- "):
            continue
        end = idx
        break
    return "".join(lines[:end]) + rendered + "".join(lines[end:])


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
            claim_indexes[(position_id, hypothesis_id)] = start_index[position_id] + len(blocks_by_position[position_id])
            blocks_by_position[position_id].append(block)

    for position_id, blocks in blocks_by_position.items():
        if not blocks:
            continue
        path = POSITIONS / f"{position_id}.yaml"
        text = path.read_text()
        path.write_text(insert_fsc_yaml(text, blocks))

    return claim_indexes


def update_hypothesis_covers(hypotheses: dict[str, dict], claim_indexes: dict[tuple[str, str], int]) -> list[dict]:
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
        "wave": "market_order_opposition_coverage_wave",
        "methodology_gate": {
            "selection_rule": "Fixed 10 fiscal/monetary market-order panel hypotheses crossed with 4 under-covered schools.",
            "not_selected_by": "observed verdicts or school score effect",
            "verdict_policy": "No verdicts changed; only reciprocal position links and covers_claims were added.",
            "score_caution": "Degrowth links are mixed/low-confidence because the outcomes are welfare-ambiguous under degrowth theory.",
        },
        "hypotheses": HYPOTHESIS_IDS,
        "positions": POSITION_PREDICTIONS,
        "new_links": len(entries),
        "new_links_by_position": dict(sorted(by_position.items())),
        "new_links_by_school_prediction": dict(sorted(by_prediction.items())),
        "entries": entries,
    }
    json_path = AUDITS / f"market_order_opposition_coverage_wave_{stamp}.json"
    md_path = AUDITS / f"market_order_opposition_coverage_wave_{stamp}.md"
    json_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Market-Order Opposition Coverage Wave",
        "",
        f"Generated: {doc['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- Fixed 10 fiscal/monetary market-order panel hypotheses crossed with 4 under-covered schools.",
        "- Selection is mechanism-based, not verdict-based.",
        "- No verdicts changed; only reciprocal position links and `covers_claims` entries were added.",
        "- Degrowth links are `mixed` because GDP, investment, and private-credit outcomes are welfare-ambiguous under degrowth theory.",
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
    entries = update_hypothesis_covers(hypotheses, claim_indexes)
    write_audit(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
