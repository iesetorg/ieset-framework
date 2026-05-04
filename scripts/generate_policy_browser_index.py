#!/usr/bin/env python3
"""Build a policy-maker browser index.

This is a richer, UI-oriented companion to ``generate_policy_evidence_index``.
It joins policies, hypotheses, local run verdicts, and position-scoreboard
claims into one static artifact that the web app can query without crawling
YAML at request time.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICIES = ROOT / "policies"
HYPOTHESES = ROOT / "hypotheses"
POSITIONS = ROOT / "positions"
RUNS = ROOT / "engine" / "runs"
OUT_JSON = ROOT / "engine" / "policy_browser_index.json"
OUT_MD = ROOT / "engine" / "policy_browser_index.md"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except Exception as exc:
        return {"_load_error": str(exc)}
    return doc if isinstance(doc, dict) else {}


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {"_load_error": str(exc)}
    return doc if isinstance(doc, dict) else {}


def verdict_bucket(raw: object) -> str:
    text = str(raw or "").strip().lower()
    if text.startswith(("supported", "weakly supported")):
        return "supported"
    if text.startswith(("refuted", "falsified", "not supported")):
        return "refuted"
    if text.startswith(("partial", "mixed", "weakened")):
        return "partial"
    if text.startswith("inconclusive"):
        return "inconclusive"
    if text.startswith("blocked"):
        return "blocked"
    if not text:
        return "missing"
    return "other"


def evidence_strength(bucket: str, diagnostics: dict[str, Any] | None, hypothesis: dict[str, Any] | None) -> str:
    if bucket in {"missing", "blocked", "inconclusive", "other"}:
        return "unresolved"
    if not diagnostics:
        return "unresolved"
    evidence_type = str((hypothesis or {}).get("evidence_type") or "").lower()
    template = str((diagnostics or {}).get("template") or ((hypothesis or {}).get("estimator") or {}).get("template") or "").lower()
    if evidence_type == "causal" or template in {"synthetic_control", "synth_did", "did_callaway_santanna", "did_chaisemartin", "event_study", "local_projections"}:
        return "strong"
    if template in {"panel_fe", "panel_fe_decomposition", "multi_metric_checklist"}:
        return "moderate"
    return "screening"


def load_hypotheses() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in HYPOTHESES.glob("*/*.yaml"):
        if path.parent.name in {"steelman", "conditional_taxonomy"}:
            continue
        doc = load_yaml(path)
        hid = str(doc.get("hypothesis_id") or path.stem)
        doc["_path"] = str(path.relative_to(ROOT))
        out[hid] = doc
    return out


def load_positions() -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    positions: dict[str, dict[str, Any]] = {}
    by_hypothesis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(POSITIONS.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = load_yaml(path)
        pid = str(doc.get("position_id") or path.stem)
        positions[pid] = doc
        for i, claim in enumerate(doc.get("falsifiable_specific_claims") or []):
            if not isinstance(claim, dict):
                continue
            hid = str(claim.get("linked_hypothesis_id") or "").strip()
            if not hid:
                continue
            by_hypothesis[hid].append(
                {
                    "position_id": pid,
                    "school": doc.get("school") or pid,
                    "claim_index": i,
                    "school_prediction": claim.get("school_prediction") or "",
                    "claim_polarity": claim.get("claim_polarity") or "aligned",
                    "empirical_status": claim.get("empirical_status") or "untested",
                }
            )
    return positions, by_hypothesis


def linked_hypotheses(policy: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in ("linked_hypotheses", "linked_hypotheses_inferred", "hypotheses"):
        value = policy.get(key)
        if isinstance(value, list):
            ids.extend(str(item) for item in value if isinstance(item, (str, int)))
    return sorted(dict.fromkeys(ids))


def policy_axes(policy: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in policy.get("axes_moved") or []:
        if not isinstance(item, dict) or not item.get("axis"):
            continue
        axis = str(item.get("axis"))
        out.append(
            {
                "axis": axis,
                "channel": axis.split(".", 1)[0],
                "direction": str(item.get("direction") or ""),
                "magnitude": item.get("magnitude") or "",
                "intended": item.get("intended"),
            }
        )
    return out


def load_run(hid: str) -> dict[str, Any] | None:
    doc = load_json(RUNS / hid / "diagnostics.json")
    if not doc:
        return None
    raw = doc.get("verdict_label") or doc.get("verdict") or doc.get("status") or ""
    return {
        "verdict": raw,
        "bucket": verdict_bucket(raw),
        "template": doc.get("template") or "",
        "run_dir": str((RUNS / hid).relative_to(ROOT)),
        "diagnostics": doc,
    }


def search_terms(policy: dict[str, Any], axes: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[str]:
    tokens = [
        policy.get("policy_id") or "",
        policy.get("title") or "",
        " ".join(policy.get("countries") or []),
        " ".join(a["axis"] for a in axes),
        " ".join(e.get("hypothesis_id", "") for e in evidence),
        " ".join(e.get("topic", "") for e in evidence),
    ]
    return sorted({part.lower() for text in tokens for part in str(text).replace("_", " ").replace(".", " ").split() if len(part) >= 3})


def decision_lens(verdicts: Counter, strengths: Counter, axes: list[dict[str, Any]]) -> dict[str, Any]:
    tested = sum(verdicts[b] for b in ("supported", "partial", "refuted"))
    unresolved = sum(verdicts[b] for b in ("inconclusive", "blocked", "missing", "other"))
    if tested == 0:
        posture = "evidence_gap"
    elif verdicts["supported"] > verdicts["refuted"] and verdicts["supported"] >= verdicts["partial"]:
        posture = "promising"
    elif verdicts["refuted"] > verdicts["supported"]:
        posture = "caution"
    else:
        posture = "mixed"
    watch_points = []
    channels = {a["channel"] for a in axes}
    if "fiscal" in channels:
        watch_points.extend(["debt and deficit path", "private investment response"])
    if "regulatory" in channels:
        watch_points.extend(["entry, competition, and compliance burden", "prices, shortages, or quality deterioration"])
    if "monetary" in channels:
        watch_points.extend(["inflation expectations", "credit and asset-price channels"])
    if "institutional" in channels:
        watch_points.extend(["rule of law and corruption indicators", "implementation capacity"])
    if unresolved:
        watch_points.append("missing-data or inconclusive evidence blockers")
    return {
        "posture": posture,
        "tested_hypotheses": tested,
        "unresolved_hypotheses": unresolved,
        "best_available_evidence": strengths.most_common(1)[0][0] if strengths else "unresolved",
        "watch_points": sorted(dict.fromkeys(watch_points)),
    }


def main() -> int:
    hypotheses = load_hypotheses()
    _positions, claims_by_hypothesis = load_positions()
    rows: list[dict[str, Any]] = []
    global_verdicts = Counter()
    coverage = Counter()
    axis_counts = Counter()
    country_counts = Counter()
    school_counts = Counter()

    for path in sorted(POLICIES.glob("*.yaml")):
        policy = load_yaml(path)
        pid = str(policy.get("policy_id") or path.stem)
        axes = policy_axes(policy)
        hids = linked_hypotheses(policy)
        evidence: list[dict[str, Any]] = []
        verdicts = Counter()
        strengths = Counter()

        for hid in hids:
            hyp = hypotheses.get(hid)
            run = load_run(hid)
            bucket = run["bucket"] if run else "missing"
            verdicts[bucket] += 1
            global_verdicts[bucket] += 1
            strength = evidence_strength(bucket, run["diagnostics"] if run else None, hyp)
            strengths[strength] += 1
            claims = claims_by_hypothesis.get(hid, [])
            for claim in claims:
                school_counts[claim["position_id"]] += 1
            evidence.append(
                {
                    "hypothesis_id": hid,
                    "topic": (hyp or {}).get("topic") or "",
                    "evidence_type": (hyp or {}).get("evidence_type") or "",
                    "verdict": run["verdict"] if run else "",
                    "bucket": bucket,
                    "evidence_strength": strength,
                    "template": run["template"] if run else (((hyp or {}).get("estimator") or {}).get("template") or ""),
                    "run_dir": run["run_dir"] if run else "",
                    "position_ids": sorted({claim["position_id"] for claim in claims}),
                }
            )

        tested = sum(verdicts[b] for b in ("supported", "partial", "refuted"))
        if tested:
            cov = "tested"
        elif verdicts["inconclusive"] or verdicts["blocked"]:
            cov = "blocked_or_inconclusive"
        elif hids:
            cov = "linked_unrun"
        else:
            cov = "no_hypothesis_link"
        coverage[cov] += 1
        for axis in axes:
            axis_counts[axis["axis"]] += 1
        for country in policy.get("countries") or []:
            country_counts[str(country)] += 1

        row = {
            "policy_id": pid,
            "title": policy.get("title") or pid.replace("_", " ").title(),
            "status": policy.get("status") or "",
            "countries": policy.get("countries") or [],
            "timeframe": policy.get("timeframe") or {},
            "description": policy.get("description") or "",
            "path": str(path.relative_to(ROOT)),
            "axes": axes,
            "coverage": cov,
            "linked_hypothesis_count": len(hids),
            "tested_hypothesis_count": tested,
            "verdict_counts": dict(verdicts),
            "evidence_strength_counts": dict(strengths),
            "decision_lens": decision_lens(verdicts, strengths, axes),
            "evidence": evidence,
        }
        row["search_terms"] = search_terms(policy, axes, evidence)
        rows.append(row)

    rows.sort(
        key=lambda row: (
            row["coverage"] != "tested",
            -row["tested_hypothesis_count"],
            row["policy_id"],
        )
    )

    payload = {
        "schema_version": 1,
        "generated_by": "scripts/generate_policy_browser_index.py",
        "summary": {
            "policy_count": len(rows),
            "coverage_counts": dict(coverage),
            "verdict_counts": dict(global_verdicts),
            "top_axes": axis_counts.most_common(25),
            "top_countries": country_counts.most_common(25),
            "position_claim_link_counts": dict(school_counts),
        },
        "policies": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Policy Browser Index",
        "",
        "Joined policy, hypothesis, run-verdict, and position-claim evidence for the policy browser.",
        "",
        "## Summary",
        "",
        f"- Policies indexed: {len(rows)}",
    ]
    for key, value in sorted(coverage.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Highest-Coverage Policies", "", "| policy | title | verdicts | tested / linked | posture |", "| --- | --- | --- | ---: | --- |"])
    for row in [r for r in rows if r["coverage"] == "tested"][:50]:
        verdict_text = ", ".join(f"{k}:{v}" for k, v in sorted(row["verdict_counts"].items()) if v)
        lines.append(
            f"| `{row['policy_id']}` | {row['title']} | {verdict_text} | "
            f"{row['tested_hypothesis_count']} / {row['linked_hypothesis_count']} | {row['decision_lens']['posture']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
