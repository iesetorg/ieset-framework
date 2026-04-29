#!/usr/bin/env python3
"""Build per-position Phase 4C triage input files.

For each scope-alignment ERROR triple (position_id, claim_index, hypothesis_id),
emit the full context an agent needs to decide: WIDEN hypothesis scope, RELINK
the claim, or FLAG for new hypothesis. Output partitioned by position_id so
parallel agents don't write-conflict on position files.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE_AUDIT = ROOT / "engine" / "audits" / "scope_validation.json"
POSITIONS_DIR = ROOT / "positions"
HYPS_DIR = ROOT / "hypotheses"
OUT_DIR = ROOT / "engine" / "audits" / "phase4c_inputs"


def load_hyps() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in HYPS_DIR.glob("*/*.yaml"):
        if p.parent.name == "steelman":
            continue
        try:
            spec = yaml.safe_load(p.read_text()) or {}
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        hid = spec.get("hypothesis_id", p.stem)
        spec["_file"] = str(p.relative_to(ROOT))
        spec["_topic"] = p.parent.name
        out[hid] = spec
    return out


def load_positions() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(POSITIONS_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        spec = yaml.safe_load(p.read_text()) or {}
        spec["_file"] = str(p.relative_to(ROOT))
        out[spec.get("position_id", p.stem)] = spec
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    errs = [r for r in json.loads(SCOPE_AUDIT.read_text()) if r["level"] == "ERROR"]
    hyps = load_hyps()
    poss = load_positions()

    # Group axes by triple
    by_triple: dict[tuple, list[str]] = defaultdict(list)
    msgs_by_triple: dict[tuple, list[str]] = defaultdict(list)
    for r in errs:
        key = (r["position_id"], r["claim_index"], r["linked_hypothesis_id"])
        by_triple[key].append(r["axis"])
        msgs_by_triple[key].append(f"{r['axis']}: {r['msg']}")

    # Build minimal hyp index (id, topic, claim, scope) for relink-target lookup
    hyp_index = []
    for hid, spec in sorted(hyps.items()):
        hyp_index.append({
            "hypothesis_id": hid,
            "topic": spec.get("_topic"),
            "file": spec.get("_file"),
            "claim": (spec.get("claim", "") or "")[:240],
            "scope": spec.get("scope") or {},
        })

    # Per-position rows
    by_pos: dict[str, list[dict]] = defaultdict(list)
    for (pid, ci, hid), axes in by_triple.items():
        pos = poss.get(pid, {})
        claim = (pos.get("falsifiable_specific_claims") or [])[ci] if ci < len(pos.get("falsifiable_specific_claims") or []) else {}
        hyp = hyps.get(hid, {})
        # Find any covers_claims entry for this triple
        cov_entry = None
        for cc in (hyp.get("covers_claims") or []):
            if cc.get("position_id") == pid and int(cc.get("claim_index", -1)) == ci:
                cov_entry = cc
                break
        row = {
            "position_id": pid,
            "position_file": pos.get("_file"),
            "claim_index": ci,
            "claim_text": claim.get("claim", ""),
            "claim_school_prediction": claim.get("school_prediction"),
            "claim_polarity": claim.get("claim_polarity", "aligned"),
            "claim_scope": claim.get("scope") or {},
            "claim_notes": claim.get("notes"),
            "linked_hypothesis_id": hid,
            "hypothesis_file": hyp.get("_file"),
            "hypothesis_topic": hyp.get("_topic"),
            "hypothesis_claim": hyp.get("claim", ""),
            "hypothesis_scope": hyp.get("scope") or {},
            "hypothesis_sample_countries": (hyp.get("sample") or {}).get("countries", []),
            "hypothesis_sample_period": (hyp.get("sample") or {}).get("period", []),
            "covers_claims_entry": cov_entry,
            "error_axes": sorted(set(axes)),
            "error_messages": msgs_by_triple[(pid, ci, hid)],
            # Tag the heuristic action class so the agent has a starting point
            "suggested_action_class": (
                "RELINK_OR_NEW_HYP" if any(a in ("period", "countries", "outcome_dim") for a in axes)
                else "WIDEN_OR_RELINK"
            ),
        }
        by_pos[pid].append(row)

    # Write hyp_index.json
    (OUT_DIR / "_hypothesis_index.json").write_text(json.dumps(hyp_index, indent=2) + "\n")
    print(f"  _hypothesis_index.json  {len(hyp_index)} hyps")

    # Per-position files
    for pid, items in sorted(by_pos.items()):
        items.sort(key=lambda r: r["claim_index"])
        out = OUT_DIR / f"{pid}.json"
        out.write_text(json.dumps(items, indent=2) + "\n")
        relink = sum(1 for r in items if r["suggested_action_class"] == "RELINK_OR_NEW_HYP")
        widen = len(items) - relink
        print(f"  {pid:25s}  {len(items):2d} errors ({relink} hard, {widen} tags-only) -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
