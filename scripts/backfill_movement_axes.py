#!/usr/bin/env python3
"""Backfill axes_summary on movements that lack one, by aggregating axes_moved
from their child policies.

Strategy:
- For each axis appearing in at least one child policy, pick the modal direction
  (ties resolve to "mixed").
- Magnitude is the modal magnitude across child policies (default "moderate").
- Rationale lists the contributing policy_ids.

Only writes axes_summary if it currently doesn't exist (doesn't overwrite).

Inserts the block immediately after `coalition` (or `timeframe` if no coalition)
to preserve YAML ordering used by other movements.

Usage:
    python scripts/backfill_movement_axes.py            # dry run
    python scripts/backfill_movement_axes.py --apply    # write changes
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_policy_axes() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for p in sorted((ROOT / "policies").glob("*.yaml")):
        with p.open() as f:
            doc = yaml.safe_load(f) or {}
        if not doc.get("policy_id"):
            continue
        out[doc["policy_id"]] = doc.get("axes_moved") or []
    return out


def derive_axes_summary(
    movement_id: str,
    policy_ids: list[str],
    policy_axes: dict[str, list[dict]],
) -> list[dict] | None:
    # axis_id -> list of (direction, magnitude, policy_id, rationale)
    by_axis: dict[str, list[tuple[str, str, str, str]]] = {}
    for pid in policy_ids:
        for am in policy_axes.get(pid, []):
            axis = am.get("axis")
            if not axis:
                continue
            direction = am.get("direction") or "mixed"
            magnitude = am.get("magnitude") or "moderate"
            rationale = am.get("rationale") or ""
            by_axis.setdefault(axis, []).append(
                (direction, magnitude, pid, rationale)
            )

    if not by_axis:
        return None

    out: list[dict] = []
    for axis_id, entries in sorted(by_axis.items()):
        directions = [e[0] for e in entries]
        magnitudes = [e[1] for e in entries]
        contributing = sorted({e[2] for e in entries})

        # Modal direction; tie among +/- collapses to mixed
        c = Counter(directions)
        top_count = c.most_common(1)[0][1]
        ties = [d for d, n in c.items() if n == top_count]
        if len(ties) > 1:
            if "+" in ties and "-" in ties:
                direction = "mixed"
            else:
                # Prefer non-zero
                non_zero = [t for t in ties if t != "0"]
                direction = non_zero[0] if non_zero else ties[0]
        else:
            direction = ties[0]

        # Modal magnitude
        magnitude = Counter(magnitudes).most_common(1)[0][0]

        rationale = (
            f"derived from {len(contributing)} child polic"
            + ("y" if len(contributing) == 1 else "ies")
            + ": "
            + ", ".join(contributing[:5])
            + ("…" if len(contributing) > 5 else "")
        )

        out.append(
            {
                "axis": axis_id,
                "direction": direction,
                "magnitude": magnitude,
                "rationale": rationale,
            }
        )

    return out


def insert_axes_summary_yaml(text: str, axes_summary: list[dict]) -> str:
    """Insert an axes_summary block as raw YAML text, preserving comments and
    ordering. Inserts immediately before the `policies:` key.
    """
    lines = text.splitlines(keepends=True)
    block_yaml = "axes_summary:\n"
    for entry in axes_summary:
        block_yaml += f"  - axis: {entry['axis']}\n"
        block_yaml += f"    direction: {yaml.dump(entry['direction']).strip()}\n"
        block_yaml += f"    magnitude: {entry['magnitude']}\n"
        # Quote rationale to be safe
        rationale_str = entry["rationale"].replace('"', '\\"')
        block_yaml += f'    rationale: "{rationale_str}"\n'
    block_yaml += "\n"

    # Find `policies:` line
    insert_at = None
    for i, line in enumerate(lines):
        if line.startswith("policies:"):
            insert_at = i
            break
    if insert_at is None:
        # Fall back: append at end
        return text.rstrip() + "\n\n" + block_yaml

    # Insert before
    return "".join(lines[:insert_at]) + block_yaml + "".join(lines[insert_at:])


def main() -> int:
    apply = "--apply" in sys.argv

    policy_axes = load_policy_axes()
    targets = []
    for movement_path in sorted((ROOT / "movements").glob("*.yaml")):
        with movement_path.open() as f:
            doc = yaml.safe_load(f) or {}
        if doc.get("axes_summary"):
            continue
        if not doc.get("movement_id"):
            continue
        policies = doc.get("policies") or []
        if not policies:
            continue
        derived = derive_axes_summary(
            doc["movement_id"], policies, policy_axes
        )
        if not derived:
            continue
        targets.append((movement_path, doc["movement_id"], derived))

    print(
        f"{'WOULD BACKFILL' if not apply else 'BACKFILLING'}: {len(targets)} movements"
    )
    for path, mid, derived in targets:
        axis_list = ", ".join(f"{e['axis']} {e['direction']}" for e in derived)
        print(f"  {mid}: {len(derived)} axes — {axis_list[:120]}")

    if not apply:
        print("\nDry run only. Re-run with --apply to write changes.")
        return 0

    written = 0
    for path, mid, derived in targets:
        text = path.read_text()
        new_text = insert_axes_summary_yaml(text, derived)
        if new_text != text:
            path.write_text(new_text)
            written += 1

    print(f"\nWrote axes_summary into {written} movement files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
