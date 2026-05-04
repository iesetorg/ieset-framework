#!/usr/bin/env python3
"""Add a bounded tested-floor coverage wave.

This is a coverage-balance repair, not a verdict or score wave. The previous
target-120 wave balanced *linked* claims, but legacy hidden claims still leave
some schools below 121 tested scoreboard prediction rows. This script adds
only neutral `mixed` claims to already-public-tested hypotheses whose primary
axis overlaps the school's derived axis profile.

Guardrails:
  - no diagnostics, verdicts, weights, or existing predictions are changed;
  - candidate order is fixed by axis relevance + hypothesis id, not verdict;
  - every added claim is `mixed`, so the scoreboard counts the row as tested
    but does not hand any school a directional score win/loss;
  - position-side links and hypothesis-side `covers_claims` are written
    together for reciprocity.
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
from apply_target120_coverage_wave import POSITION_LABELS, POSITION_RATIONALE
from audit_school_coverage_balance import (
    build_web_hypothesis_index,
    has_web_public_verdict,
    primary_axis,
)
from backfill_hypothesis_schools import insert_fsc_yaml


ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ROOT / "positions"
HYPOTHESES = ROOT / "hypotheses"
AUDITS = ROOT / "engine" / "audits"
AXIS_INDEX = ROOT / "hypotheses" / "_axis_index.yaml"
POSITION_AXIS_INDEX = ROOT / "positions" / "_axis_index.yaml"

TESTED_FLOOR = 121
AXIS_DEPTH = 10

WAVE_NOTE = (
    "2026-05-04 tested-floor neutral coverage wave; axis-overlap selection "
    "from already public-tested hypotheses, independent of observed score "
    "effects. Added as `mixed` conditional claims so coverage balance improves "
    "without changing directional net scores."
)

EXTRA_LABELS = {
    "developmentalism": "Developmentalism",
    "empirical_pragmatist": "Empirical pragmatism",
    "austrian": "Austrian economics",
    "ordoliberal": "Ordoliberalism",
    "classical_liberal": "Classical liberalism",
}

EXTRA_RATIONALE = {
    "developmentalism": (
        "Developmentalism has a stake in whether state capacity, export "
        "discipline, learning, and public-goods provision condition growth."
    ),
    "empirical_pragmatist": (
        "Empirical pragmatism has a stake in well-identified real-world tests "
        "even when the theoretical prior is deliberately conditional."
    ),
    "austrian": (
        "Austrian economics has a stake in monetary, property-rights, market "
        "process, and intervention-distortion mechanisms."
    ),
    "ordoliberal": (
        "Ordoliberalism has a stake in rules-based competition, sound money, "
        "institutional quality, and bounded social-market complements."
    ),
    "classical_liberal": (
        "Classical liberalism has a stake in trade, property rights, fiscal "
        "restraint, product-market competition, and rule-of-law mechanisms."
    ),
}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def hypothesis_path(hypothesis_id: str) -> Path:
    matches = sorted(HYPOTHESES.glob(f"*/{hypothesis_id}.yaml"))
    if not matches:
        raise FileNotFoundError(hypothesis_id)
    return matches[0]


def label_for(position_id: str) -> str:
    return POSITION_LABELS.get(position_id) or EXTRA_LABELS.get(
        position_id,
        position_id.replace("_", " ").title(),
    )


def rationale_for(position_id: str) -> str:
    return POSITION_RATIONALE.get(position_id) or EXTRA_RATIONALE.get(
        position_id,
        f"{label_for(position_id)} has a conditional stake in this axis-aligned empirical test.",
    )


def existing_links(position: dict[str, Any]) -> set[str]:
    return {
        claim.get("linked_hypothesis_id")
        for claim in position.get("falsifiable_specific_claims") or []
        if claim.get("linked_hypothesis_id")
    }


def tested_count(position: dict[str, Any], hypotheses: dict[str, dict[str, Any]]) -> int:
    total = 0
    for claim in position.get("falsifiable_specific_claims") or []:
        hid = claim.get("linked_hypothesis_id")
        if hid and has_web_public_verdict(hid, hypotheses):
            total += 1
    return total


def position_axis_scores() -> dict[str, dict[str, float]]:
    doc = load_yaml(POSITION_AXIS_INDEX)
    out: dict[str, dict[str, float]] = {}
    for position_id, rows in (doc.get("index") or {}).items():
        out[position_id] = {
            str(row.get("axis")): float(row.get("score") or 0.0)
            for row in rows or []
            if row.get("axis")
        }
    return out


def claim_text(position_id: str, axis: str, hypothesis: dict[str, Any]) -> str:
    claim = " ".join(str(hypothesis.get("claim") or "").split())
    if len(claim) > 320:
        claim = claim[:317] + "..."
    return (
        f"{label_for(position_id)} treats this {axis} hypothesis as a "
        f"conditional benchmark rather than a directional win condition: {claim}"
    )


def claim_block(position_id: str, axis: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim": claim_text(position_id, axis, hypothesis),
        "linked_hypothesis_id": hypothesis["hypothesis_id"],
        "school_prediction": "mixed",
        "claim_polarity": "aligned",
        "empirical_status": "untested",
        "scope": hypothesis.get("scope") or {},
        "notes": f"{WAVE_NOTE} Axis: {axis}. {rationale_for(position_id)}",
    }


def hypothesis_axis_rows(hypothesis_axis_index: dict[str, Any], hypothesis_id: str) -> list[dict[str, Any]]:
    rows = (hypothesis_axis_index.get("index") or {}).get(hypothesis_id) or []
    if rows:
        return rows
    axis = primary_axis(hypothesis_axis_index, hypothesis_id)
    return [{"axis": axis, "score": 0.0}] if axis else []


def candidate_sequence(
    position_id: str,
    hypotheses: dict[str, dict[str, Any]],
    hypothesis_axis_index: dict[str, Any],
    school_axes: dict[str, float],
    existing: set[str],
) -> list[tuple[str, str, float]]:
    axis_order = [
        axis
        for axis, _score in sorted(school_axes.items(), key=lambda kv: (-kv[1], kv[0]))[:AXIS_DEPTH]
    ]
    eligible_axes = set(axis_order)
    by_axis: dict[str, list[tuple[str, float, float]]] = {axis: [] for axis in axis_order}
    for hypothesis_id, hypothesis in hypotheses.items():
        if hypothesis_id in existing:
            continue
        if not has_web_public_verdict(hypothesis_id, hypotheses):
            continue
        overlaps = [
            (
                str(row.get("axis")),
                school_axes.get(str(row.get("axis")), 0.0),
                float(row.get("score") or 0.0),
            )
            for row in hypothesis_axis_rows(hypothesis_axis_index, hypothesis_id)
            if str(row.get("axis")) in eligible_axes
        ]
        if not overlaps:
            continue
        axis, axis_score, hypothesis_axis_score = max(
            overlaps,
            key=lambda row: (row[1], row[2], row[0]),
        )
        by_axis[axis].append((hypothesis_id, axis_score, hypothesis_axis_score))

    for axis in by_axis:
        by_axis[axis].sort(key=lambda row: (-row[2], row[0]))

    # Deterministic, non-verdict ordering with axis diversity: cycle through
    # each school's top axes rather than exhausting the single highest axis.
    out: list[tuple[str, str, float]] = []
    seen: set[str] = set()
    while True:
        added_this_round = False
        for axis in axis_order:
            queue = by_axis.get(axis) or []
            while queue and queue[0][0] in seen:
                queue.pop(0)
            if not queue:
                continue
            hypothesis_id, axis_score, _hypothesis_axis_score = queue.pop(0)
            if hypothesis_id in seen:
                continue
            seen.add(hypothesis_id)
            out.append((hypothesis_id, axis, axis_score))
            added_this_round = True
        if not added_this_round:
            break
    return out


def apply_wave(tested_floor: int, dry_run: bool = False) -> dict[str, Any]:
    hypotheses = build_web_hypothesis_index()
    hypothesis_axis_index = load_yaml(AXIS_INDEX)
    school_axis_scores = position_axis_scores()

    added_position_entries: list[dict[str, Any]] = []
    before_after: dict[str, dict[str, int]] = {}

    for path in sorted(POSITIONS.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        claims = position.get("falsifiable_specific_claims") or []
        before = tested_count(position, hypotheses)
        needed = max(0, tested_floor - before)
        if needed == 0:
            continue

        axes = school_axis_scores.get(position_id) or {}
        if not axes:
            raise RuntimeError(f"{position_id}: no derived position axes available")

        links = existing_links(position)
        sequence = candidate_sequence(position_id, hypotheses, hypothesis_axis_index, axes, links)
        blocks: list[dict[str, Any]] = []
        for hypothesis_id, axis, axis_score in sequence:
            if needed == 0:
                break
            hypothesis = hypotheses[hypothesis_id]
            claim_index = len(claims) + len(blocks)
            blocks.append(claim_block(position_id, axis, hypothesis))
            links.add(hypothesis_id)
            needed -= 1
            added_position_entries.append(
                {
                    "position_id": position_id,
                    "hypothesis_id": hypothesis_id,
                    "claim_index": claim_index,
                    "axis": axis,
                    "axis_score": axis_score,
                    "school_prediction": "mixed",
                    "confidence": "medium",
                }
            )

        if needed:
            raise RuntimeError(
                f"{position_id} still needs {needed} tested links; "
                "increase AXIS_DEPTH or add curated candidates"
            )

        if blocks and not dry_run:
            path.write_text(insert_fsc_yaml(path.read_text(), blocks))
        before_after[position_id] = {
            "tested_before": before,
            "tested_after": before + len(blocks),
            "added": len(blocks),
        }

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
                        "polarity": "aligned",
                        "school_prediction": "mixed",
                        "confidence": "medium",
                        "notes": (
                            f"{WAVE_NOTE} Axis: {entry['axis']}. "
                            f"{rationale_for(entry['position_id'])}"
                        ),
                    }
                )
            if cover_entries:
                path.write_text(insert_covers_yaml(path.read_text(), cover_entries))

    by_position = defaultdict(int)
    by_axis = defaultdict(int)
    for entry in added_position_entries:
        by_position[entry["position_id"]] += 1
        by_axis[entry["axis"]] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "tested_floor": tested_floor,
        "axis_depth": AXIS_DEPTH,
        "methodology": {
            "unit": "scoreboard prediction rows linked to public-tested hypotheses",
            "selection_rule": (
                "for each school below the tested floor, select public-tested "
                "hypotheses whose primary axis overlaps the school's top derived axes; "
                "order by axis relevance then hypothesis id; never sort by verdict "
                "or scoreboard effect"
            ),
            "score_policy": (
                "all added claims use school_prediction=mixed, so they count as "
                "tested coverage but are neutral for net score"
            ),
        },
        "added_claims": len(added_position_entries),
        "positions_touched": dict(sorted(by_position.items())),
        "axes_touched": dict(sorted(by_axis.items())),
        "before_after": dict(sorted(before_after.items())),
        "entries": added_position_entries,
    }


def write_audit(audit: dict[str, Any]) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    base = f"target120_tested_floor_wave_{stamp}"
    json_path = AUDITS / f"{base}.json"
    md_path = AUDITS / f"{base}.md"
    json_path.write_text(json.dumps(audit, indent=2) + "\n")

    lines = [
        "# Target-120 Tested-Floor Neutral Coverage Wave",
        "",
        f"Generated: {audit['generated_at']}",
        f"Dry run: `{audit['dry_run']}`",
        f"Tested floor: `{audit['tested_floor']}`",
        "",
        "## Methodology Gate",
        "",
        "- Adds only claims linked to already-public-tested hypotheses.",
        "- Uses school-axis overlap for relevance; verdict effects are not used for selection.",
        "- All added claims are `mixed`, making this coverage-neutral for net scores.",
        "- Reciprocal position claims and hypothesis `covers_claims` entries are written together.",
        "",
        "## Summary",
        "",
        f"- Added claims: {audit['added_claims']}",
        f"- Positions touched: `{audit['positions_touched']}`",
        f"- Axes touched: `{audit['axes_touched']}`",
        "",
        "## Before / After",
        "",
        "| position | tested before | tested after | added |",
        "| --- | ---: | ---: | ---: |",
    ]
    for position_id, row in audit["before_after"].items():
        lines.append(
            f"| `{position_id}` | {row['tested_before']} | {row['tested_after']} | {row['added']} |"
        )

    lines.extend(
        [
            "",
            "## Entries",
            "",
            "| position | claim index | hypothesis | axis | prediction |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for entry in audit["entries"]:
        lines.append(
            f"| `{entry['position_id']}` | {entry['claim_index']} | "
            f"`{entry['hypothesis_id']}` | `{entry['axis']}` | `mixed` |"
        )
    md_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tested-floor", type=int, default=TESTED_FLOOR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    audit = apply_wave(args.tested_floor, dry_run=args.dry_run)
    write_audit(audit)
    print(
        json.dumps(
            {
                "added_claims": audit["added_claims"],
                "positions_touched": audit["positions_touched"],
                "before_after": audit["before_after"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
