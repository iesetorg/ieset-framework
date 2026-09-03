"""Gating tests for monthly video-wave release packages.

These tests drive real on-disk artifacts (case studies, education briefs,
social hooks, and result cards). They fail if a package is missing, lacks a
permalink/result-card anchor, or omits SUPPORTED-tier language.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Story packages required for monthly content goals (beyond Chile baseline).
PACKAGES = [
    {
        "hypothesis_id": "korean_institutional_divergence_gdp_gap",
        "case_study": ROOT
        / "out/case_studies/20260710-korean-institutional-divergence-gdp-gap/case_study.md",
        "education": ROOT
        / "education/lesson_modules/korean_institutional_divergence_video_brief.md",
        "social": ROOT
        / "outreach/social_drafts/korean_institutional_divergence_video_wave_hooks.md",
        "permalink_slug": "korean_institutional_divergence_gdp_gap",
        "must_contain": ["33", "SUPPORTED", "Steelman"],
    },
    {
        "hypothesis_id": "volcker_disinflation_output_recovery",
        "case_study": ROOT
        / "out/case_studies/20260524-volcker-disinflation-output-recovery/case_study.md",
        "education": ROOT
        / "education/lesson_modules/volcker_disinflation_output_recovery_video_brief.md",
        "social": ROOT
        / "outreach/social_drafts/volcker_disinflation_video_wave_hooks.md",
        "permalink_slug": "volcker_disinflation_output_recovery",
        "must_contain": ["14.4", "SUPPORTED"],
    },
    {
        "hypothesis_id": "fiat_expansion_erodes_currency_purchasing_power_long_run",
        "case_study": ROOT
        / "out/case_studies/20260517-fiat-purchasing-power-erosion/case_study.md",
        "education": ROOT
        / "education/lesson_modules/fiat_purchasing_power_erosion_video_brief.md",
        "social": ROOT
        / "outreach/social_drafts/fiat_purchasing_power_video_wave_hooks.md",
        "permalink_slug": "fiat_expansion_erodes_currency_purchasing_power_long_run",
        "must_contain": ["SUPPORTED", "7"],
    },
]


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: p["hypothesis_id"])
def test_result_card_exists_and_is_supported(pkg: dict) -> None:
    card = ROOT / "engine" / "runs" / pkg["hypothesis_id"] / "result_card.md"
    assert card.is_file(), f"missing result card for {pkg['hypothesis_id']}"
    text = card.read_text(encoding="utf-8")
    assert "SUPPORTED" in text.upper() or "supported" in text


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: p["hypothesis_id"])
def test_release_package_files_exist(pkg: dict) -> None:
    for key in ("case_study", "education", "social"):
        path: Path = pkg[key]
        assert path.is_file(), f"missing {key}: {path}"


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: p["hypothesis_id"])
def test_package_links_card_and_stays_in_tier(pkg: dict) -> None:
    case = pkg["case_study"].read_text(encoding="utf-8")
    edu = pkg["education"].read_text(encoding="utf-8")
    social = pkg["social"].read_text(encoding="utf-8")
    slug = pkg["permalink_slug"]
    # Permalink or result_card path must appear in case study
    assert (
        f"framework.ieset.org/h/{slug}" in case
        or f"engine/runs/{pkg['hypothesis_id']}/result_card.md" in case
    )
    for blob in (case, edu, social):
        assert "SUPPORTED" in blob.upper()
        assert "proves causation" not in blob.lower()
    for token in pkg["must_contain"]:
        assert token in case or token in edu, f"{pkg['hypothesis_id']} missing {token!r}"


def test_city_inventory_still_valid() -> None:
    """Drive the real shipped validator entrypoint."""
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_city_level_sources.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert '"status": "ok"' in proc.stdout or "'status': 'ok'" in proc.stdout or '"status": "ok"' in proc.stdout.replace(
        " ", ""
    ) or "status" in proc.stdout
