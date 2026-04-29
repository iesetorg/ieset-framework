#!/usr/bin/env python3
"""Phase 3 link-reciprocity validator.

The authoritative ownership of claim→hypothesis links now lives on the
hypothesis side, in `hypothesis.covers_claims`. This validator enforces
bidirectional consistency:

  For every position claim with `linked_hypothesis_id: H`:
      H must exist AND
      H.covers_claims must contain {position_id, claim_index} matching
      this claim.

  For every hypothesis coverage entry {position_id: P, claim_index: i}:
      P must exist AND
      P.falsifiable_specific_claims[i] must exist AND
      P.falsifiable_specific_claims[i].linked_hypothesis_id must equal
      this hypothesis's id.

  If BOTH sides declare polarity (position.claim_polarity AND
  hypothesis.covers_claims[].polarity) and they DISAGREE, it's an ERROR.
  The hypothesis side is authoritative, so the fix is either to update
  the position's claim_polarity to match or to correct the hypothesis
  coverage declaration — but the disagreement must be resolved.

  If only the hypothesis side declares, the hypothesis is authoritative.
  If only the position side declares, fall back to position (legacy).
  If NEITHER declares, assume aligned (legacy default).

Usage:
    scripts/validate_link_reciprocity.py           # exit 1 on any ERROR
    scripts/validate_link_reciprocity.py --strict  # also exit 1 on WARN
    scripts/validate_link_reciprocity.py --summary
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSITIONS_DIR = ROOT / "positions"
HYPOTHESES_DIR = ROOT / "hypotheses"
AUDIT_DIR = ROOT / "engine" / "audits"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_positions() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(POSITIONS_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        pid = spec.get("position_id", p.stem)
        out[pid] = spec
    return out


def load_hypotheses() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in HYPOTHESES_DIR.glob("*/*.yaml"):
        if p.parent.name == "steelman":
            continue
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        hid = spec.get("hypothesis_id", p.stem)
        out[hid] = spec
    return out


# ---------------------------------------------------------------------------
# Reciprocity checks
# ---------------------------------------------------------------------------
def check_forward(positions: dict[str, dict], hypotheses: dict[str, dict]) -> list[dict]:
    """Every position-claim link must be reciprocated by a hypothesis coverage entry."""
    errs: list[dict] = []
    for pid, pos in positions.items():
        claims = pos.get("falsifiable_specific_claims", []) or []
        for i, c in enumerate(claims):
            hid = c.get("linked_hypothesis_id", "")
            if not hid:
                continue
            hyp = hypotheses.get(hid)
            if not hyp:
                # NO_HYPOTHESIS — caught by scope validator too, but repeat
                # here in case reciprocity validator is run standalone.
                errs.append({
                    "level": "ERROR", "axis": "linked_hypothesis_id",
                    "position_id": pid, "claim_index": i,
                    "linked_hypothesis_id": hid,
                    "msg": f"position claim links to non-existent hypothesis '{hid}'",
                })
                continue
            covers = hyp.get("covers_claims") or []
            # Find matching coverage entry
            match = next(
                (e for e in covers
                 if e.get("position_id") == pid and e.get("claim_index") == i),
                None,
            )
            if match is None:
                errs.append({
                    "level": "WARN", "axis": "reciprocity",
                    "position_id": pid, "claim_index": i,
                    "linked_hypothesis_id": hid,
                    "msg": (f"position claim links to '{hid}' but hypothesis "
                            f"has no covers_claims entry for this pair "
                            f"(Phase 4 will populate)"),
                })
                continue

            # Polarity consistency
            pos_polarity = c.get("claim_polarity", "aligned")
            hyp_polarity = match.get("polarity")
            if hyp_polarity and pos_polarity and hyp_polarity != pos_polarity:
                errs.append({
                    "level": "ERROR", "axis": "polarity_disagreement",
                    "position_id": pid, "claim_index": i,
                    "linked_hypothesis_id": hid,
                    "msg": (f"polarity disagreement: position says "
                            f"'{pos_polarity}', hypothesis says '{hyp_polarity}'. "
                            f"Hypothesis is authoritative — fix the position or "
                            f"the hypothesis covers_claims entry."),
                })

            # school_prediction consistency (if both declared)
            pos_pred = c.get("school_prediction")
            hyp_pred = match.get("school_prediction")
            if pos_pred and hyp_pred and pos_pred != hyp_pred:
                errs.append({
                    "level": "WARN", "axis": "school_prediction_disagreement",
                    "position_id": pid, "claim_index": i,
                    "linked_hypothesis_id": hid,
                    "msg": (f"school_prediction disagreement: position says "
                            f"'{pos_pred}', hypothesis says '{hyp_pred}'"),
                })

    return errs


def check_reverse(positions: dict[str, dict], hypotheses: dict[str, dict]) -> list[dict]:
    """Every hypothesis covers_claims entry must point to a real position claim
    whose linked_hypothesis_id matches."""
    errs: list[dict] = []
    for hid, hyp in hypotheses.items():
        covers = hyp.get("covers_claims") or []
        for j, e in enumerate(covers):
            pid = e.get("position_id", "")
            idx = e.get("claim_index", -1)
            pos = positions.get(pid)
            if not pos:
                errs.append({
                    "level": "ERROR", "axis": "dangling_coverage",
                    "linked_hypothesis_id": hid,
                    "position_id": pid, "claim_index": idx,
                    "coverage_entry_index": j,
                    "msg": (f"hypothesis '{hid}' covers_claims[{j}] "
                            f"references non-existent position '{pid}'"),
                })
                continue
            claims = pos.get("falsifiable_specific_claims", []) or []
            if idx < 0 or idx >= len(claims):
                errs.append({
                    "level": "ERROR", "axis": "dangling_coverage",
                    "linked_hypothesis_id": hid,
                    "position_id": pid, "claim_index": idx,
                    "coverage_entry_index": j,
                    "msg": (f"hypothesis '{hid}' covers_claims[{j}] "
                            f"references out-of-range claim_index {idx} in "
                            f"position '{pid}' (has {len(claims)} claims)"),
                })
                continue
            claim = claims[idx]
            claim_hid = claim.get("linked_hypothesis_id", "")
            if claim_hid != hid:
                errs.append({
                    "level": "ERROR", "axis": "asymmetric_link",
                    "linked_hypothesis_id": hid,
                    "position_id": pid, "claim_index": idx,
                    "coverage_entry_index": j,
                    "msg": (f"hypothesis '{hid}' claims to cover "
                            f"{pid}#{idx} but that position claim's "
                            f"linked_hypothesis_id is '{claim_hid}'"),
                })
    return errs


def format_rows(rows: list[dict], level_filter: str | None = None) -> str:
    out_lines: list[str] = []
    for r in rows:
        if level_filter and r["level"] != level_filter:
            continue
        out_lines.append(
            f"  [{r['level']}] {r.get('position_id', '?'):25s} "
            f"#{r.get('claim_index', '?'):>3} → "
            f"{r.get('linked_hypothesis_id', '?')}"
        )
        out_lines.append(f"      axis={r.get('axis', '?')}  {r['msg']}")
    return "\n".join(out_lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--json-out", type=Path,
                    default=AUDIT_DIR / "link_reciprocity.json")
    args = ap.parse_args(argv)

    positions = load_positions()
    hypotheses = load_hypotheses()
    print(f"Loaded {len(positions)} positions, {len(hypotheses)} hypotheses")

    rows = check_forward(positions, hypotheses) + check_reverse(positions, hypotheses)

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(rows, indent=2) + "\n")

    errors = [r for r in rows if r["level"] == "ERROR"]
    warns = [r for r in rows if r["level"] == "WARN"]

    stats: Counter[str] = Counter()
    for r in rows:
        stats[r["axis"]] += 1

    # Count total position-claim links for context
    total_links = sum(
        len(p.get("falsifiable_specific_claims", []) or [])
        for p in positions.values()
    )
    total_coverage = sum(
        len(h.get("covers_claims") or [])
        for h in hypotheses.values()
    )

    print(f"\n=== Link-reciprocity validation ===\n")
    print(f"  position-side links:        {total_links}")
    print(f"  hypothesis-side coverages:  {total_coverage}")
    print(f"  errors:                     {len(errors)}")
    print(f"  warnings:                   {len(warns)}")
    if stats:
        print(f"\n  issues by axis:")
        for axis, n in stats.most_common():
            print(f"    {axis:40s}  {n:4d}")

    if not args.summary:
        if errors:
            print("\nERRORS:")
            print(format_rows(errors, "ERROR"))
        if warns and args.strict:
            print("\nWARNINGS (first 20):")
            print(format_rows(warns[:20], "WARN"))

    print(f"\nReport → {args.json_out.relative_to(ROOT)}")

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
