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

# Personal-path leak token, assembled so this test file never contains the
# continuous forbidden string that `git grep` would otherwise self-match.
_PATH_LEAK_TOKEN = "duncan" + "campbell"


def test_stats_json_is_authoritative_census_copy():
    census = (ROOT / "engine" / "public_corpus_census.json").read_text(encoding="utf-8")
    public = (ROOT / "web" / "public" / "stats.json").read_text(encoding="utf-8")
    assert json.loads(census) == json.loads(public)
    data = json.loads(public)
    assert "counts" in data
    assert data["counts"]["hypothesis_specs"] > 0
    assert data["counts"]["review_submissions"] == 0


def test_citation_and_site_point_at_ieset_framework():
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    site = (ROOT / "web" / "lib" / "site.ts").read_text(encoding="utf-8")
    assert 'repository-code: "https://github.com/iesetorg/ieset-framework"' in citation
    assert "https://github.com/iesetorg/ieset-framework" in site
    assert "ieset-framework1" not in citation
    assert "bigdestiny2" not in site


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


def test_production_disclosure_without_private_brain():
    prod = (ROOT / "web" / "app" / "production" / "page.tsx").read_text(encoding="utf-8")
    assert "large-language-model assistance under human direction" in prod
    assert "Models are workers, not authorities" in prod
    assert "not" in prod.lower() and "peer review" in prod.lower()
    # Must not embed private control-plane paths or personal home-path tokens
    assert "engine/brain" not in prod
    assert _PATH_LEAK_TOKEN not in prod
    assert "budget_state" not in prod


def test_public_tree_has_no_name_leak_or_tracked_brain():
    # Scope to the public product surface (site, docs, citation) — not tests/.
    leaked = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            _PATH_LEAK_TOKEN,
            "HEAD",
            "--",
            "web/",
            "CONTRIBUTING.md",
            "README.md",
            "CITATION.cff",
            "DISCLOSURE.md",
            "METHODOLOGY.md",
            "review/",
            "engine/public_corpus_census.json",
            "engine/preregistration_index.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert leaked.returncode != 0, leaked.stdout

    # This test file must not re-introduce the continuous token for git grep.
    raw = Path(__file__).read_bytes()
    continuous = b"duncan" + b"campbell"
    assert continuous not in raw, "test source must not embed the continuous leak token"

    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "HEAD", "--name-only"],
        cwd=ROOT,
        text=True,
    )
    brain_paths = [p for p in tracked.splitlines() if p.startswith("engine/brain")]
    assert brain_paths == []


def test_discovery_artifacts_exist_and_use_canonical_host():
    paths = [
        ROOT / "web" / "app" / "robots.ts",
        ROOT / "web" / "app" / "sitemap.ts",
        ROOT / "web" / "public" / "llms.txt",
        ROOT / "web" / "public" / "feed.xml",
        ROOT / "web" / "app" / "updates" / "page.tsx",
        ROOT / "web" / "public" / "stats.json",
    ]
    for p in paths:
        assert p.is_file(), p
    host = "framework.ieset.org"
    assert host in (ROOT / "web" / "lib" / "site.ts").read_text(encoding="utf-8")
    assert host in (ROOT / "web" / "public" / "llms.txt").read_text(encoding="utf-8")
    assert host in (ROOT / "web" / "public" / "feed.xml").read_text(encoding="utf-8")
    robots = (ROOT / "web" / "app" / "robots.ts").read_text(encoding="utf-8")
    assert "OAI-SearchBot" in robots or "allow" in robots.lower()
    assert "sitemap" in robots.lower()


def test_contribute_and_review_are_honest_pilot_not_live_bounty():
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    review = (ROOT / "review" / "README.md").read_text(encoding="utf-8")
    assert "No bounty programme is currently active" in contrib
    assert "External review is a pilot" in contrib
    assert "active bounty rounds: 0" in review
    assert "bounty payouts: 0" in review
    # Present-tense paid-loop claim must not appear as a fact without ledger
    assert "contributors get paid for catching it" not in contrib.lower()
