#!/usr/bin/env python3
"""Classify recent throughput verdicts before scoreboard conversion.

This audit is intentionally stricter than the raw run tally. It answers:

- Which new verdicts are already linked to school claims?
- Which verdicts need claim mapping before they can affect the scoreboard?
- Which broad-panel or duplicate-fingerprint results should be held for QA?
- Which inconclusive runs are data/model repair items, not scoreboard evidence?

The output is advisory. It does not mutate positions, hypotheses, verdicts, or
scoreboard files.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "engine" / "audits"
RUNS = ROOT / "engine" / "runs"
LEGACY_HYPOTHESIS_ID_MAP = {
    "oecd_minimum_wage_bite_low_education_unemployment": "oecd_low_education_unemployment_minimum_wage_bite",
    "us_qcew_county_food_service_minimum_wage_panel": "bls_qcew_county_food_service_minimum_wage_growth",
}
BATCH_FILES = [
    AUDIT_DIR / "monthly_hypothesis_throughput_kickoff_2026-05-12.md",
    AUDIT_DIR / "monthly_hypothesis_throughput_batch_02_2026-05-12.md",
    AUDIT_DIR / "monthly_hypothesis_throughput_batch_03_2026-05-12.md",
    AUDIT_DIR / "monthly_hypothesis_throughput_batch_04_2026-05-12.md",
]


def canonical_hypothesis_id(hypothesis_id: str) -> str:
    return LEGACY_HYPOTHESIS_ID_MAP.get(hypothesis_id, hypothesis_id)


def resolve_run_dir(hypothesis_id: str, legacy_hypothesis_id: str | None = None) -> Path:
    primary = RUNS / hypothesis_id
    if primary.exists():
        return primary
    if legacy_hypothesis_id:
        legacy = RUNS / legacy_hypothesis_id
        if legacy.exists():
            return legacy
    for legacy, mapped in LEGACY_HYPOTHESIS_ID_MAP.items():
        if mapped == hypothesis_id and (RUNS / legacy).exists():
            return RUNS / legacy
    return primary


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def verdict_bucket(verdict: str | None) -> str:
    if not verdict:
        return "missing"
    value = verdict.strip().lower()
    if value.startswith(("supported", "supported_subset")):
        return "supported"
    if value.startswith(("refuted", "not supported", "not_supported")):
        return "refuted"
    if value.startswith(("partial", "mixed", "weakly supported", "weakly_supported")):
        return "partial"
    if value.startswith(("inconclusive", "blocked", "error", "no verdict")):
        return "inconclusive"
    return "other"


def extract_batch_ids() -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for path in BATCH_FILES:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            match = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
            if not match:
                continue
            hid = canonical_hypothesis_id(match.group(1))
            if hid not in seen and not hid.startswith(("engine/", "scripts/")):
                ids.append(hid)
                seen.add(hid)
    return ids


def build_hypothesis_index() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "hypotheses").glob("*/*.yaml")):
        if path.parent.name == "steelman":
            continue
        spec = load_yaml(path)
        hid = canonical_hypothesis_id(str(spec.get("hypothesis_id") or path.stem))
        out[hid] = {"path": str(path.relative_to(ROOT)), "spec": spec}
    for legacy, canonical in LEGACY_HYPOTHESIS_ID_MAP.items():
        if canonical in out:
            out[legacy] = out[canonical]
    return out


def build_position_link_index() -> dict[str, list[dict[str, Any]]]:
    links: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        claims = position.get("falsifiable_specific_claims") or []
        for i, claim in enumerate(claims):
            hid = claim.get("linked_hypothesis_id")
            if not hid:
                continue
            hid = canonical_hypothesis_id(str(hid))
            links[hid].append(
                {
                    "position_id": position_id,
                    "claim_index": i,
                    "school_prediction": claim.get("school_prediction"),
                    "claim_polarity": claim.get("claim_polarity", "aligned"),
                }
            )
    return links


def canonical_fingerprint(diag: dict[str, Any]) -> str:
    reason = str(diag.get("verdict_reason") or diag.get("verdict") or "").strip()
    reason = re.sub(r"\s+", " ", reason)
    reason = re.sub(r"p=([0-9.eE+-]+)", lambda m: f"p={float(m.group(1)):.4g}" if _is_float(m.group(1)) else m.group(0), reason)
    return reason[:180]


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def broad_panel_flags(hid: str, spec: dict[str, Any], diag: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(x or "")
        for x in [
            hid,
            spec.get("claim"),
            spec.get("methodology_note"),
            diag.get("verdict_reason"),
            diag.get("falsification_rule_text"),
        ]
    ).lower()
    flags: list[str] = []
    if "broad" in text or "qol" in hid or "quality-of-life" in text or "quality of life" in text:
        flags.append("broad_scope")
    if "effect magnitude effectively zero" in text:
        flags.append("zero_effect_partial")
    if "claim direction ambiguous" in text or "claim direction not auto-inferred" in text:
        flags.append("direction_ambiguous")
    if "direction inconclusive" in text:
        flags.append("direction_inconclusive")
    if diag.get("template") == "panel_fe" and (spec.get("evidence_type") or "").lower() == "associational":
        flags.append("associational_panel")
    return flags


def classify_record(
    record: dict[str, Any],
    duplicate_fingerprints: set[str],
) -> str:
    if record["bucket"] == "inconclusive":
        return "repair_data_or_design"
    if record["bucket"] not in {"supported", "partial", "refuted"}:
        return "repair_missing_verdict"
    if "duplicate_fingerprint" in record["qa_flags"]:
        return "hold_duplicate_broad_panel_qa"
    if any(flag in record["qa_flags"] for flag in ("zero_effect_partial", "direction_ambiguous", "direction_inconclusive")):
        return "hold_interpretation_qa"
    if "broad_scope" in record["qa_flags"] and "associational_panel" in record["qa_flags"]:
        return "hold_broad_panel_upgrade"
    if record["position_links"] == 0:
        return "needs_position_claim_mapping"
    if record["covers_claims"] == 0:
        return "needs_hypothesis_covers_claims"
    return "scoreboard_ready_existing_mapping"


def build_audit() -> dict[str, Any]:
    ids = extract_batch_ids()
    hypotheses = build_hypothesis_index()
    position_links = build_position_link_index()

    base_records: list[dict[str, Any]] = []
    fingerprints: Counter[str] = Counter()

    for hid in ids:
        legacy_hid = None
        for legacy, canonical in LEGACY_HYPOTHESIS_ID_MAP.items():
            if canonical == hid:
                legacy_hid = legacy
                break
        run_dir = resolve_run_dir(hid, legacy_hypothesis_id=legacy_hid)
        diag = load_json(run_dir / "diagnostics.json")
        spec_entry = hypotheses.get(hid) or {"path": None, "spec": {}}
        spec = spec_entry["spec"]
        verdict = diag.get("verdict") or diag.get("verdict_label")
        bucket = verdict_bucket(verdict)
        fp = canonical_fingerprint(diag) if bucket in {"supported", "partial", "refuted"} else ""
        if fp:
            fingerprints[fp] += 1
        base_records.append(
            {
                "hypothesis_id": hid,
                "legacy_hypothesis_id": legacy_hid,
                "hypothesis_path": spec_entry["path"],
                "verdict": verdict,
                "bucket": bucket,
                "evidence_type": spec.get("evidence_type", "unknown"),
                "template": diag.get("template"),
                "fingerprint": fp,
                "covers_claims": len(spec.get("covers_claims") or []),
                "position_links": len(position_links.get(hid) or []),
                "position_link_examples": (position_links.get(hid) or [])[:5],
                "qa_flags": broad_panel_flags(hid, spec, diag),
            }
        )

    duplicate_fps = {fp for fp, count in fingerprints.items() if fp and count >= 2 and len(fp) >= 40}
    records: list[dict[str, Any]] = []
    for record in base_records:
        if record["fingerprint"] in duplicate_fps and (
            "associational_panel" in record["qa_flags"]
            or "broad_scope" in record["qa_flags"]
            or "zero_effect_partial" in record["qa_flags"]
        ):
            record["qa_flags"].append("duplicate_fingerprint")
        record["conversion_bucket"] = classify_record(record, duplicate_fps)
        records.append(record)

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Raw verdict throughput is not scoreboard conversion. Conversion requires a real verdict, non-ambiguous interpretation, claim mapping, and no duplicate broad-panel QA hold.",
            "scoreboard_ready": "Already has position links and hypothesis covers_claims, with no broad/duplicate/ambiguous QA hold.",
            "mapping_needed": "Verdict exists but no position claim link or missing covers_claims.",
            "qa_hold": "Do not score until the hypothesis-specific evidence is upgraded or the duplicate broad-panel fingerprint is explained.",
        },
        "summary": {
            "batch_files": [str(path.relative_to(ROOT)) for path in BATCH_FILES if path.exists()],
            "hypotheses_reviewed": len(records),
            "verdict_counts": dict(Counter(r["bucket"] for r in records)),
            "conversion_counts": dict(Counter(r["conversion_bucket"] for r in records)),
            "qa_flag_counts": dict(Counter(flag for r in records for flag in r["qa_flags"])),
            "duplicate_fingerprint_groups": sum(1 for fp in duplicate_fps),
        },
        "records": records,
    }


def write_audit(audit: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    lines: list[str] = [
        "# Throughput Scoreboard Conversion Audit",
        "",
        f"Generated: {audit['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        f"- {audit['methodology']['principle']}",
        "- `scoreboard_ready_existing_mapping`: safe to include in the next scoreboard recompute, subject to normal validation.",
        "- `needs_position_claim_mapping` / `needs_hypothesis_covers_claims`: evidence exists, but the school-claim mapping is incomplete.",
        "- `hold_*`: evidence exists, but interpretation or duplicate broad-panel QA must be fixed before scoreboard conversion.",
        "- `repair_data_or_design`: not a verdict-bearing result.",
        "",
        "## Summary",
        "",
    ]
    for key, value in audit["summary"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Conversion Buckets",
            "",
            "| bucket | count |",
            "| --- | ---: |",
        ]
    )
    for bucket, count in sorted(audit["summary"]["conversion_counts"].items()):
        lines.append(f"| `{bucket}` | {count} |")

    lines.extend(
        [
            "",
            "## Records",
            "",
            "| hypothesis | verdict | evidence | links | covers | conversion bucket | QA flags |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for r in audit["records"]:
        flags = ", ".join(r["qa_flags"]) if r["qa_flags"] else "-"
        lines.append(
            f"| `{r['hypothesis_id']}` | {r['bucket']} | {r['evidence_type']} | "
            f"{r['position_links']} | {r['covers_claims']} | `{r['conversion_bucket']}` | {flags} |"
        )

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    audit = build_audit()
    out_base = AUDIT_DIR / "throughput_scoreboard_conversion_2026-05-12"
    write_audit(audit, out_base)
    print(f"Wrote {out_base.with_suffix('.json')}")
    print(f"Wrote {out_base.with_suffix('.md')}")
    print(json.dumps(audit["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
