#!/usr/bin/env python3
"""Audit positions/*.yaml claim_polarity vs linked hypothesis pre-reg claim.

For every claim in every positions file, this script:
  1. Loads the school's narrative `claim` text
  2. Loads the linked hypothesis's pre-registered `claim` text
  3. Emits a TSV review table with school-claim, hypothesis-claim, current
     school_prediction, current polarity, and a heuristic polarity guess

Produces engine/audits/claim_polarity_audit.tsv and a JSON index for tooling.

The heuristic is NOT trustworthy on its own — the purpose of the TSV is to let
a human (or LLM with access to both claim texts) assign each claim's final
polarity. The script can be re-run after hand annotations to validate.

Usage:
    scripts/audit_claim_polarity.py              # produce review TSV
    scripts/audit_claim_polarity.py --apply FILE # apply annotations from FILE
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSITIONS_DIR = ROOT / "positions"
HYPOTHESES_DIR = ROOT / "hypotheses"
AUDIT_DIR = ROOT / "engine" / "audits"

# Direction keywords. "positive" / "negative" here is about the valence of the
# outcome described, not about the school's normative stance.
POSITIVE_OUTCOME = (
    "increased", "raised", "improved", "boosted", "accelerated", "recovered",
    "expanded", "grew", "rose", "faster growth", "faster recovery", "gained",
    "reduced poverty", "extended healthcare", "broadened access", "lifted",
)
NEGATIVE_OUTCOME = (
    "declining", "decline", "declined", "reduced", "fell", "fallen", "collapsed",
    "collapse", "contracted", "contraction", "stagnated", "stagnation",
    "deteriorated", "worsened", "diverged negatively", "shrank", "eroded",
    "caused decline", "produced declining", "harmed", "crisis", "mortality crisis",
    "rising mortality",
)
# Causal attribution phrases — the "X caused Y" vs "not X caused Y, it was Z"
ATTRIBUTION_NOT = (
    "not due to", "not because of", "rather than", "not attributable to",
    "attributable to ... rather than", "not driven by", "external", "exogenous",
)


def load_hypotheses() -> dict[str, dict]:
    out = {}
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
        out[hid] = {"path": str(p.relative_to(ROOT)), "spec": spec}
    return out


def normalise(t: str) -> str:
    return " ".join((t or "").split()).lower()


def polarity_hint(school_claim: str, hyp_claim: str) -> str:
    """Crude heuristic: classify whether the school's claim direction matches
    the hypothesis's claim direction.

    Returns one of: 'aligned_guess', 'inverted_guess', 'uncertain'.
    """
    s = normalise(school_claim)
    h = normalise(hyp_claim)

    s_pos = any(w in s for w in POSITIVE_OUTCOME)
    s_neg = any(w in s for w in NEGATIVE_OUTCOME)
    h_pos = any(w in h for w in POSITIVE_OUTCOME)
    h_neg = any(w in h for w in NEGATIVE_OUTCOME)

    s_not_attribution = any(w in s for w in ATTRIBUTION_NOT)
    h_not_attribution = any(w in h for w in ATTRIBUTION_NOT)

    # Strongly opposite-signed outcome direction
    if s_pos and h_neg and not s_neg and not h_pos:
        return "inverted_guess"
    if s_neg and h_pos and not s_pos and not h_neg:
        return "inverted_guess"
    # Attribution inversion ("not X, rather Z" vs "X caused Y")
    if s_not_attribution and not h_not_attribution:
        return "inverted_guess"
    if h_not_attribution and not s_not_attribution:
        return "inverted_guess"
    # Both positive, or both negative, or both attribution-neutral
    if (s_pos and h_pos) or (s_neg and h_neg):
        return "aligned_guess"
    return "uncertain"


def build_audit() -> list[dict]:
    hyps = load_hypotheses()
    rows = []
    for p in sorted(POSITIONS_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        spec = yaml.safe_load(p.read_text())
        if not isinstance(spec, dict):
            continue
        position_id = spec.get("position_id", p.stem)
        claims = spec.get("falsifiable_specific_claims", []) or []
        for i, c in enumerate(claims):
            hid = c.get("linked_hypothesis_id", "")
            sc = c.get("claim", "")
            hyp = hyps.get(hid, {}).get("spec", {})
            hc = hyp.get("claim", "") if hyp else ""
            existing_polarity = c.get("claim_polarity", "aligned")
            guess = polarity_hint(sc, hc) if hc else "no_hypothesis"
            rows.append({
                "position_id": position_id,
                "position_file": p.name,
                "claim_index": i,
                "linked_hypothesis_id": hid,
                "hypothesis_found": bool(hyp),
                "school_claim": sc,
                "hypothesis_claim": hc,
                "school_prediction": c.get("school_prediction", ""),
                "current_polarity": existing_polarity,
                "heuristic_guess": guess,
            })
    return rows


def write_outputs(rows: list[dict]):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    # TSV for human review
    tsv = AUDIT_DIR / "claim_polarity_audit.tsv"
    headers = [
        "position_id", "claim_index", "linked_hypothesis_id",
        "school_prediction", "current_polarity", "heuristic_guess",
        "school_claim", "hypothesis_claim",
    ]
    lines = ["\t".join(headers)]
    for r in rows:
        vals = []
        for h in headers:
            v = str(r.get(h, ""))
            v = v.replace("\t", " ").replace("\n", " ")
            vals.append(v)
        lines.append("\t".join(vals))
    tsv.write_text("\n".join(lines) + "\n")

    # JSON mirror
    (AUDIT_DIR / "claim_polarity_audit.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print(f"Wrote {tsv} ({len(rows)} rows)")


def summarise(rows: list[dict]):
    from collections import Counter
    by_guess = Counter(r["heuristic_guess"] for r in rows)
    for g, n in by_guess.most_common():
        print(f"  {n:3d}  {g}")
    # Rows where current polarity is 'aligned' but guess is 'inverted'
    suspicious = [r for r in rows
                  if r["current_polarity"] in ("aligned", None, "")
                  and r["heuristic_guess"] == "inverted_guess"]
    print(f"\n{len(suspicious)} currently-aligned entries flagged as likely inverted")
    for r in suspicious[:20]:
        print(f"  {r['position_id']:22s} claim #{r['claim_index']:2d}  hid={r['linked_hypothesis_id']}")


def apply_annotations(annotations_path: Path, dry_run: bool = False) -> int:
    """Apply polarity annotations from a TSV/JSON file back to positions/*.yaml.

    Expected annotation file: TSV with columns (position_id, claim_index,
    final_polarity) — only rows with final_polarity != blank are applied.
    """
    # Accept JSON or TSV
    data = []
    if annotations_path.suffix == ".json":
        data = json.loads(annotations_path.read_text())
    else:
        lines = annotations_path.read_text().splitlines()
        headers = lines[0].split("\t")
        for line in lines[1:]:
            cols = line.split("\t")
            if len(cols) < len(headers):
                cols += [""] * (len(headers) - len(cols))
            data.append(dict(zip(headers, cols)))

    # Group by position_id
    by_pos: dict[str, dict[int, str]] = {}
    for r in data:
        fp = r.get("final_polarity", "").strip()
        if fp not in ("aligned", "inverted"):
            continue
        pid = r["position_id"]
        ci = int(r["claim_index"])
        by_pos.setdefault(pid, {})[ci] = fp

    n_changed = 0
    for pid, changes in by_pos.items():
        p = POSITIONS_DIR / f"{pid}.yaml"
        if not p.exists():
            print(f"  WARN: no file for {pid}", file=sys.stderr)
            continue
        spec = yaml.safe_load(p.read_text())
        claims = spec.get("falsifiable_specific_claims", []) or []
        dirty = False
        for ci, fp in changes.items():
            if ci >= len(claims):
                continue
            c = claims[ci]
            current = c.get("claim_polarity", "aligned")
            if current != fp:
                # Insert polarity at a stable position within the claim dict
                # (after school_prediction)
                new_claim = {}
                for k, v in c.items():
                    new_claim[k] = v
                    if k == "school_prediction":
                        new_claim["claim_polarity"] = fp
                if "claim_polarity" not in new_claim:
                    new_claim["claim_polarity"] = fp
                claims[ci] = new_claim
                dirty = True
                n_changed += 1
        if dirty and not dry_run:
            spec["falsifiable_specific_claims"] = claims
            p.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=100))
            print(f"  updated {p.name}: {len(changes)} claim(s)")
    return n_changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", type=Path, help="Apply annotations from TSV/JSON file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.apply:
        n = apply_annotations(args.apply, dry_run=args.dry_run)
        print(f"Applied {n} polarity changes")
        return

    rows = build_audit()
    write_outputs(rows)
    print()
    print("Summary by heuristic guess:")
    summarise(rows)


if __name__ == "__main__":
    main()
