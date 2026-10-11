"""Project full engine audits into publication-safe site artifacts.

The hold registry controls publication only; research verdicts and tiers in the
engine audit remain unchanged.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "engine" / "publication_rights_holds.json"


def load_holds() -> tuple[set[str], int]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if (
        registry.get("schema") != "ieset-publication-rights-holds-v1"
        or registry.get("status") != "active_publication_hold"
        or not isinstance(registry.get("groups"), list)
    ):
        raise ValueError("Invalid publication-rights hold registry")
    ids: set[str] = set()
    qualified = 0
    for group in registry["groups"]:
        entries = group.get("hypothesis_ids")
        count = group.get("count")
        public_count = group.get("currently_public")
        if (
            not group.get("source")
            or not isinstance(entries, list)
            or len(entries) != count
            or not isinstance(public_count, int)
            or not 0 <= public_count <= count
        ):
            raise ValueError(f"Invalid publication-rights hold group: {group.get('source')}")
        qualified += public_count
        for item in entries:
            if not isinstance(item, str) or not item or item in ids:
                raise ValueError(f"Duplicate or invalid publication-rights hold ID: {item}")
            ids.add(item)
    return ids, qualified


def project_evidence_audit(source: dict[str, Any]) -> dict[str, Any]:
    ids, qualified = load_holds()
    by_id = {record["hypothesis_id"]: record for record in source["records"]}
    missing = ids - by_id.keys()
    if missing:
        raise ValueError(f"Publication hold IDs missing from evidence audit: {sorted(missing)}")
    actual_qualified = sum(bool(by_id[item]["public_visible"]) for item in ids)
    if actual_qualified != qualified:
        raise ValueError(
            f"Publication hold public count drift: registry {qualified}, audit {actual_qualified}"
        )

    records = [record for record in source["records"] if record["hypothesis_id"] not in ids]
    summary = {
        **source["summary"],
        "hypotheses": len(records),
        "public_visible": sum(bool(record["public_visible"]) for record in records),
        "reference_set": sum(bool(record["reference_set"]) for record in records),
        "tier_counts": dict(Counter(record["tier"] for record in records)),
        "registration_counts": dict(Counter(record["registration_status"] for record in records)),
        "verdict_counts": dict(Counter(record["verdict_bucket"] for record in records)),
        "estimator_floor_failures": dict(
            Counter(failure for record in records for failure in record["estimator_floor_failures"])
        ),
        "exclusion_counts": dict(
            Counter(reason for record in records for reason in record["exclusion_reasons"])
        ),
    }
    return {
        **source,
        "records": records,
        "reference_set": [
            record for record in source["reference_set"] if record["hypothesis_id"] not in ids
        ],
        "summary": summary,
    }


def project_public_census(
    source: dict[str, Any],
    public_audit: dict[str, Any],
    verdict_bucket: Callable[[str], str],
) -> dict[str, Any]:
    ids, qualified = load_holds()
    verdict_counts = Counter(source["verdict_counts"])
    held_runs = 0
    held_cards = 0
    for item in ids:
        run = ROOT / "engine" / "runs" / item
        if run.is_dir():
            held_runs += 1
        card = run / "result_card.md"
        if card.is_file():
            held_cards += 1
            bucket = verdict_bucket(card.read_text(encoding="utf-8", errors="replace"))
            if verdict_counts[bucket] <= 0:
                raise ValueError(f"Missing held verdict bucket: {bucket}")
            verdict_counts[bucket] -= 1

    summary = public_audit["summary"]
    counts = {
        **source["counts"],
        "hypothesis_specs": summary["hypotheses"],
        "run_directories": source["counts"]["run_directories"] - held_runs,
        "result_card_files": source["counts"]["result_card_files"] - held_cards,
        "public_visible_results": summary["public_visible"],
        "featured_evidence": summary["tier_counts"].get("featured", 0),
        "calibration_evidence": summary["tier_counts"].get("calibration", 0),
        "archive_records": summary["tier_counts"].get("archive", 0),
        "reference_set": summary["reference_set"],
        "publication_rights_held_records": len(ids),
        "publication_rights_held_evidence_qualified": qualified,
    }
    definitions = {
        **source["definitions"],
        "hypothesis_specs": "Hypothesis specs available in the published site, excluding source-rights holds.",
        "run_directories": "Result runs available in the published site, excluding source-rights holds.",
        "result_card_files": "Result cards available in the published site, excluding source-rights holds.",
        "public_visible_results": "Evidence-qualified results available in the published site; source-rights holds are counted separately.",
        "publication_rights_held_records": "Research records held from publication during publisher-rights review; evidence grades are unchanged.",
        "publication_rights_held_evidence_qualified": "Evidence-qualified records held from publication during publisher-rights review.",
    }
    return {
        **source,
        "counts": counts,
        "definitions": definitions,
        "verdict_counts": {key: value for key, value in verdict_counts.items() if value},
        "registration_counts": summary["registration_counts"],
        "estimator_floor_failure_counts": summary["estimator_floor_failures"],
        "evidence_exclusion_counts": summary["exclusion_counts"],
    }
