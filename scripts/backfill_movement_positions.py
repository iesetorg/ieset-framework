#!/usr/bin/env python3
"""Backfill position_alignments on movements that lack them, by comparing each
movement's axes_summary to the centroid axis-direction profile of positions
that DO have curated alignments on similar movements.

Method (axis-profile classifier):

1. Training data: every (position, movement, alignment) triple in already
   curated movements. For each (position, axis) pair, accumulate the
   movement's direction-on-that-axis weighted by alignment label
   (aligned=+1, partially_aligned=+0.5, opposed=-1).

2. Position profile: for each position, the per-axis weighted-mean direction
   the school approved of in curated movements. Direction is -1, 0, +1, or
   "mixed". Profile values are real numbers in [-1, 1].

3. Score uncurated movement against position: dot-product of movement axis
   directions × position profile direction-preferences, normalised by the
   number of axes the movement moves on. Positive → aligned, negative →
   opposed, near-zero → partial.

4. Confidence threshold: only emit alignment if score is at least
   THRESHOLD_HIGH (in absolute terms) for aligned/opposed, or between
   THRESHOLD_PARTIAL and THRESHOLD_HIGH for partially_aligned. Below
   THRESHOLD_PARTIAL the prediction is too noisy to write — skip.

5. Per-position support floor: a position must have at least MIN_TRAINING
   curated alignments to be a valid predictor — else its profile is too
   sparse to trust on a new movement.

Each emitted alignment carries `notes: "derived: confidence=<score>, k=<n>"`
so the downstream audit script can grep these and a human can promote them
from draft to canonical curation later.

Usage:
    python scripts/backfill_movement_positions.py            # dry run
    python scripts/backfill_movement_positions.py --apply
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Direction encoding for axes_summary entries.
DIR_VALUE = {"+": 1.0, "-": -1.0, "0": 0.0, "mixed": 0.0}
ALIGN_WEIGHT = {
    "aligned": 1.0,
    "partially_aligned": 0.5,
    "opposed": -1.0,
}

# Tunable thresholds.
MIN_TRAINING = 5            # position needs ≥ this many curated alignments
THRESHOLD_HIGH = 0.45       # score > this → aligned/opposed
THRESHOLD_PARTIAL = 0.18    # |score| > this but < HIGH → partially_aligned
MIN_OVERLAP_AXES = 2        # movement must share ≥ this many axes with the position profile


def load_movements() -> list[tuple[Path, dict]]:
    out = []
    for p in sorted((ROOT / "movements").glob("*.yaml")):
        with p.open() as f:
            doc = yaml.safe_load(f) or {}
        if not doc.get("movement_id"):
            continue
        out.append((p, doc))
    return out


def axis_direction_map(axes_summary) -> dict[str, float]:
    """Return axis_id → direction value in [-1, 0, 1] from a movement's
    axes_summary entries. 'mixed' rolls to 0; missing rolls to 0."""
    out: dict[str, float] = {}
    for entry in axes_summary or []:
        axis = entry.get("axis")
        if not axis:
            continue
        d = entry.get("direction")
        out[axis] = DIR_VALUE.get(d, 0.0)
    return out


def build_position_profiles(curated: list[tuple[dict, dict]]) -> dict[str, dict[str, float]]:
    """Returns position_id → axis_id → preferred direction (in [-1, 1])."""
    # accum: position -> axis -> list of (axis_dir, alignment_weight)
    accum: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    counts: dict[str, int] = defaultdict(int)
    for movement, alignment in curated:
        axis_dirs = axis_direction_map(movement.get("axes_summary"))
        if not axis_dirs:
            continue
        pos_id = alignment["position_id"]
        weight = ALIGN_WEIGHT.get(alignment.get("alignment"), 0.0)
        if weight == 0.0:
            continue
        counts[pos_id] += 1
        for axis, d in axis_dirs.items():
            accum[pos_id][axis].append((d, weight))

    profiles: dict[str, dict[str, float]] = {}
    for pos_id, axis_table in accum.items():
        if counts[pos_id] < MIN_TRAINING:
            continue
        prof: dict[str, float] = {}
        for axis, samples in axis_table.items():
            # Weighted mean: position's preferred direction on this axis.
            # Direction values * alignment_weights → if alignment was aligned (+1)
            # and movement moved fiscal.tax_corporate by -1, position prefers -1.
            # If alignment was opposed (-1) and movement moved by +1, position
            # prefers -1 as well (opposite of what the opposed movement did).
            num = sum(d * w for d, w in samples)
            denom = sum(abs(w) for d, w in samples)
            if denom == 0 or len(samples) < 2:
                continue
            prof[axis] = num / denom
        if prof:
            profiles[pos_id] = prof
    return profiles, counts


def score_movement(
    movement_axes: dict[str, float], profile: dict[str, float]
) -> tuple[float, int]:
    """Return (score, overlap) for one (movement, position) pair.

    Score is the cosine-like normalised dot product. Overlap is the number of
    axes shared between the movement and the position profile."""
    shared = [a for a in movement_axes if a in profile]
    if len(shared) < MIN_OVERLAP_AXES:
        return 0.0, len(shared)
    dot = sum(movement_axes[a] * profile[a] for a in shared)
    norm = (
        sum(movement_axes[a] ** 2 for a in shared) ** 0.5
        * sum(profile[a] ** 2 for a in shared) ** 0.5
    )
    if norm == 0:
        return 0.0, len(shared)
    return dot / norm, len(shared)


def label_for_score(score: float) -> str | None:
    if abs(score) < THRESHOLD_PARTIAL:
        return None
    if score >= THRESHOLD_HIGH:
        return "aligned"
    if score <= -THRESHOLD_HIGH:
        return "opposed"
    return "partially_aligned"


def predict_alignments(
    movement: dict, profiles: dict[str, dict[str, float]]
) -> list[dict]:
    movement_axes = axis_direction_map(movement.get("axes_summary"))
    if not movement_axes:
        return []
    out = []
    for pos_id, profile in profiles.items():
        score, overlap = score_movement(movement_axes, profile)
        label = label_for_score(score)
        if not label:
            continue
        out.append(
            {
                "position_id": pos_id,
                "alignment": label,
                "notes": (
                    f"derived: score={score:+.2f}, overlap={overlap} axes "
                    f"vs {pos_id} profile (mechanical backfill v1)"
                ),
            }
        )
    out.sort(
        key=lambda a: (
            {"aligned": 0, "partially_aligned": 1, "opposed": 2}[a["alignment"]],
            a["position_id"],
        )
    )
    return out


def insert_position_alignments_yaml(text: str, alignments: list[dict]) -> str:
    """Insert a position_alignments block as raw YAML text. Inserts before
    `outcome_hypotheses:`, `references:`, `notes:`, or at end if none."""
    lines = text.splitlines(keepends=True)

    block = "position_alignments:\n"
    for a in alignments:
        block += f"  - position_id: {a['position_id']}\n"
        block += f"    alignment: {a['alignment']}\n"
        notes_str = a["notes"].replace('"', '\\"')
        block += f'    notes: "{notes_str}"\n'
    block += "\n"

    insert_at = None
    for i, line in enumerate(lines):
        for k in ("outcome_hypotheses:", "references:", "steelman:", "notes:"):
            if line.startswith(k):
                insert_at = i
                break
        if insert_at is not None:
            break
    if insert_at is None:
        return text.rstrip() + "\n\n" + block
    return "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="Only process N targets (for sanity check)")
    args = ap.parse_args()

    movements = load_movements()
    print(f"loaded {len(movements)} movements")

    # Build training set.
    curated_pairs: list[tuple[dict, dict]] = []
    for _, m in movements:
        for a in m.get("position_alignments") or []:
            curated_pairs.append((m, a))
    print(f"  curated pairs: {len(curated_pairs)}")

    profiles, counts = build_position_profiles(curated_pairs)
    print(f"  position profiles built: {len(profiles)} (require ≥{MIN_TRAINING} curated)")
    for pid in sorted(profiles):
        print(f"    {pid}: k={counts[pid]}, axes={len(profiles[pid])}")

    # Predict for movements lacking position_alignments.
    targets = [
        (p, m) for p, m in movements if not m.get("position_alignments")
    ]
    print(f"\ntargets needing backfill: {len(targets)}")

    predictions: list[tuple[Path, dict, list[dict]]] = []
    for p, m in targets:
        preds = predict_alignments(m, profiles)
        if preds:
            predictions.append((p, m, preds))

    if args.limit:
        predictions = predictions[: args.limit]

    print(
        f"movements receiving ≥1 prediction: {len(predictions)} "
        f"(rest skipped — too sparse / low-confidence)"
    )

    # Distribution.
    label_counts: dict[str, int] = defaultdict(int)
    for _, _, preds in predictions:
        for a in preds:
            label_counts[a["alignment"]] += 1
    print(f"\nalignment label distribution:")
    for k, v in sorted(label_counts.items()):
        print(f"  {k}: {v}")

    # Sample per-movement output.
    print(f"\nfirst 8 predictions:")
    for p, m, preds in predictions[:8]:
        print(f"  {m['movement_id']} ({m.get('countries')}, status={m.get('status')}):")
        for a in preds:
            print(
                f"    {a['alignment']:>20s}  {a['position_id']}   "
                f"({a['notes'].split('overlap=')[0].strip().rstrip(',')})"
            )

    if not args.apply:
        print("\nDry run only. Re-run with --apply to write changes.")
        return 0

    written = 0
    for p, m, preds in predictions:
        text = p.read_text()
        new_text = insert_position_alignments_yaml(text, preds)
        if new_text != text:
            p.write_text(new_text)
            written += 1
    print(f"\nWrote position_alignments into {written} movement files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
