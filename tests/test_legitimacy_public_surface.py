"""Gating tests for IESET P0 legitimacy + discovery public surface.

These drive the real shipped artifacts (source files, census JSON, prereg
index) — not a reimplementation of the web helpers.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_stats_json_is_authoritative_census_copy():
    census = (ROOT / "engine" / "public_corpus_census.json").read_text(encoding="utf-8")
    public = (ROOT / "web" / "public" / "stats.json").read_text(encoding="utf-8")
    assert json.loads(census) == json.loads(public)
    data = json.loads(public)
    assert "counts" in data
    assert data["counts"]["hypothesis_specs"] > 0
    assert data["counts"]["review_submissions"] == 0
    assert data["schema_version"] == 2
    assert data["counts"]["positions"] == (
        data["counts"]["ranked_schools"]
        + data["counts"]["benchmark_controls"]
    )
    assert data["counts"]["ranked_schools"] == 16
    assert data["counts"]["benchmark_controls"] == 1
    assert data["counts"]["featured_evidence"] > 0
    assert data["counts"]["public_visible_results"] == (
        data["counts"]["featured_evidence"]
        + data["counts"]["calibration_evidence"]
    )


def test_citation_and_site_point_at_ieset_framework():
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    site = (ROOT / "web" / "lib" / "site.ts").read_text(encoding="utf-8")
    assert 'repository-code: "https://github.com/iesetorg/ieset-framework"' in citation
    assert "https://github.com/iesetorg/ieset-framework" in site
    assert "github.com/iesetorg/" in site


def test_prereg_strip_deep_links_first_spec_commit_not_head():
    strip = (ROOT / "web" / "components" / "cards" / "PreRegStrip.tsx").read_text(
        encoding="utf-8"
    )
    content = (ROOT / "web" / "lib" / "content.ts").read_text(encoding="utf-8")
    assert "githubCommitUrl" in strip
    assert "first commit that added" in strip
    assert "not the repository HEAD" in strip
    # Full SHA stored from index (not truncated at load)
    assert "hash: row.spec_commit," in content
    assert "hash: row.spec_commit.slice(0, 7)" not in content


def test_prereg_index_verified_spec_is_not_repository_head():
    index = json.loads(
        (ROOT / "engine" / "preregistration_index.json").read_text(encoding="utf-8")
    )
    regs = index["registrations"]
    row = regs["wid_top_wealth_concentration_rise_post_1980"]
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    assert row["status"] == "verified"
    assert row["spec_commit"] != head
    assert row["spec_commit"] != row["run_first_commit"]
    # SHA must exist in local git (public rewritten history)
    subprocess.check_call(
        ["git", "cat-file", "-e", row["spec_commit"]], cwd=ROOT
    )


def test_production_disclosure_is_research_focused():
    prod = (ROOT / "web" / "app" / "production" / "page.tsx").read_text(encoding="utf-8")
    assert "large-language-model assistance under human direction" in prod
    assert "Models are workers, not authorities" in prod
    assert "not" in prod.lower() and "peer review" in prod.lower()


def test_public_commit_metadata_is_institutional():
    subprocess.check_call(
        ["python3", "scripts/check_public_opsec.py"],
        cwd=ROOT,
    )


def test_discovery_artifacts_exist_and_use_canonical_host():
    paths = [
        ROOT / "web" / "public" / "robots.txt",
        ROOT / "web" / "app" / "sitemap.ts",
        ROOT / "web" / "public" / "llms.txt",
        ROOT / "web" / "public" / "llms-full.txt",
        ROOT / "web" / "public" / "feed.xml",
        ROOT / "web" / "public" / "evidence-tiers.json",
        ROOT / "web" / "app" / "evidence" / "page.tsx",
        ROOT / "METHODS_PAPER.md",
        ROOT / "web" / "app" / "methods-paper" / "page.tsx",
        ROOT / "web" / "app" / "api" / "catalog" / "route.ts",
        ROOT / "web" / "app" / "updates" / "page.tsx",
        ROOT / "web" / "public" / "stats.json",
    ]
    for p in paths:
        assert p.is_file(), p
    host = "framework.ieset.org"
    assert host in (ROOT / "web" / "lib" / "site.ts").read_text(encoding="utf-8")
    assert host in (ROOT / "web" / "public" / "llms.txt").read_text(encoding="utf-8")
    assert host in (ROOT / "web" / "public" / "feed.xml").read_text(encoding="utf-8")
    robots = (ROOT / "web" / "public" / "robots.txt").read_text(encoding="utf-8")
    assert "OAI-SearchBot" in robots
    assert "ai-input=yes" in robots
    assert "ai-train=no" in robots
    assert "sitemap" in robots.lower()


def test_evidence_tier_ledger_is_balanced_and_definition_bearing():
    engine = json.loads(
        (ROOT / "engine" / "evidence_tier_audit.json").read_text(encoding="utf-8")
    )
    public = json.loads(
        (ROOT / "web" / "public" / "evidence-tiers.json").read_text(
            encoding="utf-8"
        )
    )
    assert engine == public
    summary = engine["summary"]
    tiers = summary["tier_counts"]
    assert sum(tiers.values()) == summary["hypotheses"]
    assert summary["public_visible"] == tiers["featured"] + tiers["calibration"]
    assert tiers["featured"] > 0
    assert tiers["archive"] > tiers["featured"]
    assert summary["reference_set"] == 6
    assert summary["registration_counts"]["legacy_same_commit"] > 0
    assert sum(summary["estimator_floor_failures"].values()) > 0
    assert "estimator_floor" in engine["definitions"]
    for record in engine["reference_set"]:
        assert record["tier"] == "featured"


def test_sitemap_only_submits_public_evidence_pages():
    source = (ROOT / "web" / "app" / "sitemap.ts").read_text(encoding="utf-8")
    assert "_evidence_public_visible" in source
    assert '"/evidence/"' in source
    assert '"/methods-paper/"' in source
    assert ".slice(0, 2500)" not in source
    assert ".slice(0, 800)" not in source


def test_contribute_and_review_are_honest_pilot_not_live_bounty():
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    review = (ROOT / "review" / "README.md").read_text(encoding="utf-8")
    assert "No bounty programme is currently active" in contrib
    assert "External review is a pilot" in contrib
    assert "active bounty rounds: 0" in review
    assert "bounty payouts: 0" in review
    # Present-tense paid-loop claim must not appear as a fact without ledger
    assert "contributors get paid for catching it" not in contrib.lower()
