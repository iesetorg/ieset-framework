#!/usr/bin/env python3
"""Per-topic input files for Phase 4B agents (hypothesis-side scope + covers_claims).

For each hypothesis topic directory under hypotheses/, write a JSON file listing
every linked hypothesis with the inbound claim coverage (position_id,
claim_index, claim_text, claim_scope, school_prediction, claim_polarity).
Agents use this to populate hypothesis.scope (drawing on existing sample +
union/intersection of claim scopes) and hypothesis.covers_claims.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSITIONS_DIR = ROOT / "positions"
HYPS_DIR = ROOT / "hypotheses"
OUT_DIR = ROOT / "engine" / "audits" / "phase4b_inputs"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build: hid -> [coverage_entry]
    coverage: dict[str, list[dict]] = defaultdict(list)
    for p in sorted(POSITIONS_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        data = yaml.safe_load(p.read_text()) or {}
        pid = data.get("position_id", p.stem)
        for i, c in enumerate(data.get("falsifiable_specific_claims", []) or []):
            hid = c.get("linked_hypothesis_id")
            if not hid:
                continue
            coverage[hid].append({
                "position_id": pid,
                "claim_index": i,
                "claim_text": c.get("claim", ""),
                "school_prediction": c.get("school_prediction"),
                "claim_polarity": c.get("claim_polarity", "aligned"),
                "claim_scope": c.get("scope") or {},
                "claim_notes": c.get("notes"),
            })

    # Group hypotheses by topic dir, attach hyp metadata
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for hp in HYPS_DIR.glob("*/*.yaml"):
        if hp.parent.name == "steelman":
            continue
        try:
            spec = yaml.safe_load(hp.read_text()) or {}
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        hid = spec.get("hypothesis_id", hp.stem)
        if hid not in coverage:
            continue
        topic = hp.parent.name
        by_topic[topic].append({
            "hypothesis_id": hid,
            "file": str(hp.relative_to(ROOT)),
            "topic": spec.get("topic"),
            "claim": spec.get("claim", ""),
            "evidence_type": spec.get("evidence_type"),
            "sample_countries": (spec.get("sample") or {}).get("countries", []),
            "sample_period": (spec.get("sample") or {}).get("period", []),
            "existing_scope": spec.get("scope"),
            "existing_covers": spec.get("covers_claims"),
            "covers_claims_inbound": coverage[hid],
        })

    # Write per-topic files
    for topic, items in sorted(by_topic.items()):
        items.sort(key=lambda r: r["hypothesis_id"])
        out = OUT_DIR / f"{topic}.json"
        out.write_text(json.dumps(items, indent=2) + "\n")
        print(f"  {topic:25s}  {len(items):3d} linked hyps  -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
