#!/usr/bin/env python3
"""Bulk-populate `linked_hypotheses_inferred` on every policy via axis overlap.

Mirrors the runtime logic in `web/lib/matching.ts::hypothesesForPolicy` but
persists the result so the policy YAMLs carry their own empirical bearing
instead of recomputing at page-render time. Top-K (default 8) hypotheses
ranked by axis-overlap score are written to each policy's
`linked_hypotheses_inferred:` field. The human-curated `linked_hypotheses:`
field is preserved untouched.

Score: sum over axes the policy moves of `max(1, hypothesis_axis_score) ×
magnitude_weight`. magnitude_weight = 1.0 strong, 0.7 moderate, 0.4 weak.

Usage:
    python3 scripts/link_policies_to_hypotheses.py            # apply
    python3 scripts/link_policies_to_hypotheses.py --dry-run  # preview only
    python3 scripts/link_policies_to_hypotheses.py --limit N  # cap top-K (default 8)
"""
from __future__ import annotations

import argparse
import glob
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_hyp_axis_index() -> dict:
    """Returns {hypothesis_id: [{"axis": ..., "score": ...}, ...]}."""
    with (ROOT / "hypotheses" / "_axis_index.yaml").open() as f:
        doc = yaml.safe_load(f)
    return doc.get("index", {})


def magnitude_weight(m: str | None) -> float:
    s = (m or "").lower().strip()
    return {"strong": 1.0, "moderate": 0.7, "weak": 0.4}.get(s, 0.6)


def score_policy(
    policy: dict, hyp_axis_index: dict
) -> list[tuple[str, float, list[str]]]:
    """Return [(hypothesis_id, score, [shared_axes]), ...] sorted desc."""
    axes_moved = policy.get("axes_moved") or []
    if not axes_moved:
        return []

    # policy_axis -> magnitude_weight (max if duplicates)
    pol_axes: dict[str, float] = {}
    for am in axes_moved:
        if not isinstance(am, dict):
            continue
        ax = am.get("axis")
        if not ax:
            continue
        w = magnitude_weight(am.get("magnitude"))
        if ax not in pol_axes or pol_axes[ax] < w:
            pol_axes[ax] = w

    # candidate hypothesis -> (score, shared_axes)
    out: dict[str, tuple[float, list[str]]] = {}
    for hid, tags in hyp_axis_index.items():
        score = 0.0
        shared: list[str] = []
        for t in tags:
            ax = t.get("axis") if isinstance(t, dict) else None
            if not ax or ax not in pol_axes:
                continue
            s = max(1.0, float(t.get("score", 1.0)))
            score += s * pol_axes[ax]
            shared.append(ax)
        if score > 0:
            out[hid] = (score, sorted(set(shared)))

    return sorted(
        ((hid, sc, sh) for hid, (sc, sh) in out.items()),
        key=lambda x: -x[1],
    )


def update_policy_yaml(
    path: Path, top_hids: list[str], dry_run: bool
) -> tuple[bool, str]:
    """Read, set linked_hypotheses_inferred, write back. Preserves comments
    by editing the raw text rather than re-dumping (yaml.safe_dump strips
    comments).

    Strategy: load YAML to get the parsed shape; if linked_hypotheses_inferred
    already exists with the same content, skip. Otherwise rewrite the file
    with a re-dumped YAML body, preserving the leading comment header.
    """
    with path.open() as f:
        raw = f.read()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return False, "yaml-parse-error"
    if not data:
        return False, "empty"
    existing = data.get("linked_hypotheses_inferred") or []
    if list(existing) == list(top_hids):
        return False, "unchanged"

    data["linked_hypotheses_inferred"] = list(top_hids)

    if dry_run:
        return True, "would-write"

    # Preserve any leading `# ...` comment header.
    header_lines: list[str] = []
    for line in raw.splitlines():
        if line.strip().startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=200)
    new = "\n".join(header_lines)
    if header_lines:
        new += "\n"
    new += body
    path.write_text(new)
    return True, "wrote"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=8,
                    help="top-K hypotheses to keep per policy (default 8)")
    args = ap.parse_args()

    print(f"Loading hypothesis axis index…")
    hyp_idx = load_hyp_axis_index()
    print(f"  {len(hyp_idx)} hypotheses indexed")

    files = sorted(ROOT.glob("policies/*.yaml"))
    print(f"Walking {len(files)} policy specs…")

    stats = Counter()
    histogram: list[int] = []
    for path in files:
        try:
            with path.open() as f:
                policy = yaml.safe_load(f)
        except yaml.YAMLError:
            stats["yaml-error"] += 1
            continue
        if not policy:
            stats["empty"] += 1
            continue
        ranked = score_policy(policy, hyp_idx)
        if not ranked:
            stats["no_axes_moved_or_no_overlap"] += 1
            histogram.append(0)
            continue
        top = [hid for hid, _, _ in ranked[: args.limit]]
        histogram.append(len(top))
        changed, status = update_policy_yaml(path, top, args.dry_run)
        stats[status] += 1
        if changed and stats["wrote"] + stats["would-write"] in (1, 50, 500, 1000, 2000, 2500):
            print(f"  {stats['wrote'] + stats['would-write']} done…")

    print()
    print(f"Result: {dict(stats)}")
    if histogram:
        print(f"  link distribution: median={sorted(histogram)[len(histogram)//2]}, "
              f"mean={sum(histogram)/len(histogram):.1f}, "
              f"with≥1: {sum(1 for x in histogram if x>0)}/{len(histogram)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
