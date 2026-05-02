#!/usr/bin/env python3
"""Build a policy-maker evidence index from policies, hypotheses, and run verdicts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICIES = ROOT / "policies"
RUNS = ROOT / "engine" / "runs"
OUT_JSON = ROOT / "engine" / "policy_evidence_index.json"
OUT_MD = ROOT / "engine" / "policy_evidence_index.md"


def verdict_bucket(raw: object) -> str:
    text = str(raw or "").strip().lower()
    if text.startswith("supported") or text.startswith("weakly supported"):
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


def load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as exc:  # keep index generation robust for candidate files
        return {"_load_error": str(exc)}


def load_diagnostic(hypothesis_id: str) -> dict | None:
    path = RUNS / hypothesis_id / "diagnostics.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {"hypothesis_id": hypothesis_id, "verdict": "", "error": str(exc)}
    raw = data.get("verdict_label") or data.get("verdict") or data.get("status") or ""
    return {
        "hypothesis_id": hypothesis_id,
        "verdict": raw,
        "bucket": verdict_bucket(raw),
        "run_dir": str((RUNS / hypothesis_id).relative_to(ROOT)),
    }


def policy_axes(policy: dict) -> list[str]:
    axes = []
    for entry in policy.get("axes_moved") or []:
        if isinstance(entry, dict) and entry.get("axis"):
            axes.append(str(entry["axis"]))
    return axes


def linked_hypotheses(policy: dict) -> list[str]:
    ids = []
    for key in ("linked_hypotheses_inferred", "linked_hypotheses", "hypotheses"):
        value = policy.get(key)
        if isinstance(value, list):
            ids.extend(str(item) for item in value if isinstance(item, (str, int)))
    return sorted(dict.fromkeys(ids))


def main() -> int:
    rows = []
    summary = Counter()
    policy_files = sorted(POLICIES.glob("*.yaml"))

    for path in policy_files:
        policy = load_yaml(path)
        hypothesis_ids = linked_hypotheses(policy)
        evidence = [load_diagnostic(hid) for hid in hypothesis_ids]
        evidence = [item for item in evidence if item is not None]
        buckets = Counter(item["bucket"] for item in evidence)
        tested_count = sum(buckets[b] for b in ("supported", "partial", "refuted"))
        inconclusive_count = buckets["inconclusive"] + buckets["blocked"]

        if tested_count:
            coverage = "tested"
        elif inconclusive_count:
            coverage = "blocked_or_inconclusive"
        elif hypothesis_ids:
            coverage = "linked_unrun"
        else:
            coverage = "no_hypothesis_link"
        summary[coverage] += 1

        rows.append(
            {
                "policy_id": policy.get("policy_id") or path.stem,
                "title": policy.get("title") or path.stem.replace("_", " ").title(),
                "status": policy.get("status", ""),
                "countries": policy.get("countries") or [],
                "timeframe": policy.get("timeframe") or {},
                "axes": policy_axes(policy),
                "linked_hypothesis_count": len(hypothesis_ids),
                "tested_hypothesis_count": tested_count,
                "verdict_counts": dict(buckets),
                "coverage": coverage,
                "evidence": evidence,
                "path": str(path.relative_to(ROOT)),
            }
        )

    rows.sort(
        key=lambda row: (
            row["coverage"] != "tested",
            -row["tested_hypothesis_count"],
            row["policy_id"],
        )
    )

    payload = {
        "summary": {
            "policy_count": len(rows),
            "coverage_counts": dict(summary),
        },
        "policies": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Policy Evidence Index",
        "",
        "This index joins policy files to linked hypotheses and local run verdicts.",
        "",
        "## Summary",
        "",
        f"- Policies indexed: {len(rows)}",
    ]
    for key, value in sorted(summary.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Top Tested Policies",
            "",
            "| policy_id | title | axes | verdicts | tested / linked |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for row in [r for r in rows if r["coverage"] == "tested"][:100]:
        verdicts = ", ".join(f"{k}:{v}" for k, v in sorted(row["verdict_counts"].items()) if v)
        axes = ", ".join(row["axes"][:3])
        if len(row["axes"]) > 3:
            axes += ", ..."
        lines.append(
            f"| `{row['policy_id']}` | {row['title']} | {axes} | {verdicts} | "
            f"{row['tested_hypothesis_count']} / {row['linked_hypothesis_count']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")

    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
