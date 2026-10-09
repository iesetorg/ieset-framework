"""Conservative policy-link credit derived from the live hypothesis tier audit.

A shared axis is a navigation link, and a saved run is not automatically
public evidence.  Even a curated public link is a linked result, not proof that
the named policy caused the result.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import audit_evidence_tiers


RESULT_BUCKETS = frozenset({"supported", "partial", "refuted"})
PUBLIC_TIERS = frozenset({"featured", "calibration"})


def tier_records() -> dict[str, dict[str, Any]]:
    """Recompute gates so a stale generated audit cannot grant policy credit."""
    return {
        str(row["hypothesis_id"]): row
        for row in audit_evidence_tiers.build()["records"]
    }


def policy_links(policy: dict[str, Any]) -> list[dict[str, Any]]:
    sources_by_id: dict[str, set[str]] = defaultdict(set)
    for key in ("linked_hypotheses", "linked_hypotheses_inferred", "hypotheses"):
        value = policy.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, (str, int)):
                sources_by_id[str(item)].add(key)
    links = []
    for hypothesis_id, sources in sorted(sources_by_id.items()):
        link_type = (
            "explicit" if "linked_hypotheses" in sources
            else "inferred" if "linked_hypotheses_inferred" in sources
            else "legacy"
        )
        links.append({
            "hypothesis_id": hypothesis_id,
            "link_sources": sorted(sources),
            "link_type": link_type,
        })
    return links


def link_status(
    link_type: str,
    tier_record: dict[str, Any] | None,
    bucket: str,
    has_run: bool,
) -> str:
    """The only scored link is a curated, public, decisive result."""
    if not has_run:
        return "unrun"
    if not tier_record or tier_record.get("tier") not in PUBLIC_TIERS or not tier_record.get("public_visible"):
        return "archive"
    if link_type != "explicit":
        return "related_public"
    return "curated_public_result" if bucket in RESULT_BUCKETS else "curated_public_unresolved"


def coverage_status(statuses: list[str]) -> str:
    if "curated_public_result" in statuses:
        return "tested"
    if "curated_public_unresolved" in statuses:
        return "blocked_or_inconclusive"
    if "related_public" in statuses:
        return "related_public_only"
    if "archive" in statuses:
        return "archive_only"
    if statuses:
        return "linked_unrun"
    return "no_hypothesis_link"
