"""Policy indexes cannot promote saved or inferred runs into policy credit."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_policy_browser_index import evidence_strength  # noqa: E402
from policy_evidence_gate import coverage_status, link_status  # noqa: E402


def test_link_credit_requires_a_curated_public_result():
    public = {"tier": "calibration", "public_visible": True}
    quarantined = {"tier": "archive", "public_visible": False}
    assert link_status("explicit", public, "supported", True) == "curated_public_result"
    assert link_status("inferred", public, "supported", True) == "related_public"
    assert link_status("legacy", public, "supported", True) == "related_public"
    assert link_status("explicit", quarantined, "supported", True) == "archive"
    assert link_status("explicit", public, "inconclusive", True) == "curated_public_unresolved"
    assert link_status("explicit", public, "missing", False) == "unrun"
    assert coverage_status(["archive", "related_public"]) == "related_public_only"


def test_calibration_causal_label_cannot_receive_strong_design_strength():
    hypothesis = {"evidence_type": "causal"}
    diagnostics = {"template": "event_study"}
    assert evidence_strength("supported", diagnostics, hypothesis, "calibration") == "screening"
    assert evidence_strength("supported", diagnostics, hypothesis, "featured") == "strong"


def test_generated_policy_indexes_only_credit_curated_public_links():
    tiers = {
        row["hypothesis_id"]: row
        for row in json.loads((ROOT / "engine/evidence_tier_audit.json").read_text())["records"]
    }
    browser = json.loads((ROOT / "engine/policy_browser_index.json").read_text())
    evidence_index = json.loads((ROOT / "engine/policy_evidence_index.json").read_text())
    evidence_by_policy = {row["policy_id"]: row for row in evidence_index["policies"]}
    coverage = Counter()
    public_links = 0
    for row in browser["policies"]:
        credited = [
            item for item in row["evidence"]
            if item["policy_evidence_status"] == "curated_public_result"
        ]
        assert len(credited) == row["tested_hypothesis_count"]
        assert len(credited) == evidence_by_policy[row["policy_id"]]["tested_hypothesis_count"]
        assert sum(row["context_counts"].values()) == row["linked_hypothesis_count"]
        assert sum(row["verdict_counts"].values()) <= row["linked_hypothesis_count"]
        for item in row["evidence"]:
            tier = tiers.get(item["hypothesis_id"], {})
            if item["policy_evidence_status"] == "curated_public_result":
                assert item["link_type"] == "explicit"
                assert tier.get("tier") in {"featured", "calibration"}
                assert tier.get("public_visible") is True
                assert item["bucket"] in {"supported", "partial", "refuted"}
            else:
                assert item["evidence_strength"] == "unresolved"
        public_links += len(credited)
        coverage[row["coverage"]] += 1
    assert browser["summary"]["coverage_counts"] == dict(coverage)
    assert sum(browser["summary"]["verdict_counts"].values()) == public_links
    assert public_links > 0

    # A policy-specific inconclusive result remains inspectable, but is not
    # replaced by an unrelated axis-match verdict in the credited mix.
    peru = next(row for row in browser["policies"] if row["policy_id"] == "pe_us_fta_implementation_2009")
    peru_run = next(item for item in peru["evidence"] if item["hypothesis_id"] == "peru_us_fta_bilateral_exports_2009")
    assert peru_run["link_type"] == "explicit"
    assert peru_run["policy_evidence_status"] == "archive"
    assert peru_run["bucket"] == "inconclusive"
    assert peru["tested_hypothesis_count"] == 0
