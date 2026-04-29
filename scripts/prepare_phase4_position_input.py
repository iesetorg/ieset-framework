#!/usr/bin/env python3
"""Split the reviewed claim-hypothesis audit into per-position slices so Phase 4
agents can each focus on one position file. Output files go to
engine/audits/phase4_inputs/<position_id>.json and include each claim's
audit row plus the linked hypothesis's claim text / period / countries /
outcome_dim / policy_family (for cross-check).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "engine" / "audits" / "claim_hypothesis_link_audit_reviewed.json"
HYPS_DIR = ROOT / "hypotheses"
OUT_DIR = ROOT / "engine" / "audits" / "phase4_inputs"


def load_hypotheses() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in HYPS_DIR.glob("*/*.yaml"):
        if p.parent.name == "steelman":
            continue
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        hid = spec.get("hypothesis_id", p.stem)
        spec["_file"] = str(p.relative_to(ROOT))
        out[hid] = spec
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = json.loads(AUDIT.read_text())
    hyps = load_hypotheses()

    by_pos: dict[str, list[dict]] = {}
    for row in rows:
        pid = row["position_id"]
        hid = row["linked_hypothesis_id"]
        hyp = hyps.get(hid, {})
        enriched = dict(row)
        enriched["hyp_file"] = hyp.get("_file", "")
        enriched["hyp_claim"] = hyp.get("claim", "")
        enriched["hyp_topic"] = hyp.get("topic", "")
        hsample = hyp.get("sample") or {}
        enriched["hyp_sample_countries"] = hsample.get("countries", [])
        enriched["hyp_sample_period"] = hsample.get("period", [])
        enriched["hyp_existing_scope"] = hyp.get("scope")
        by_pos.setdefault(pid, []).append(enriched)

    for pid, items in by_pos.items():
        items.sort(key=lambda r: int(r.get("claim_index", 0)))
        out = OUT_DIR / f"{pid}.json"
        out.write_text(json.dumps(items, indent=2) + "\n")
        print(f"{pid:30s}  {len(items)} claims  -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
