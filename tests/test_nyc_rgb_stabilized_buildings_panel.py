"""NYC RGB stabilized building list panel — fetch/validation tests.

Drives the real builder pipeline (scripts/build_nyc_rgb_stabilized_buildings_panel.py)
end to end against a pinned one-page extract of the actual 2024 DHCR building
file PDF, then asserts the promoted repository artifacts (panel, vintage,
manifest) are present and internally consistent.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_nyc_rgb_stabilized_buildings_panel as rgb_builder  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "nyc_rgb_stabilized_staten_island_p1.pdf"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_parse_building_line_accepts_real_layout_and_rejects_garbage():
    row = rgb_builder.parse_building_line(
        "10301 6 TO 14 ARLO RD STATEN ISLAND 64 MULTIPLE DWELLING A GARDEN COMPLEX 595 15",
        "staten-island",
    )
    assert row == {
        "zip": "10301",
        "address": "6 TO 14 ARLO RD",
        "county_code": "64",
        "status_codes": "MULTIPLE DWELLING A GARDEN COMPLEX",
        "block": 595,
        "lot": 15,
        "borough": "staten-island",
    }
    # wrong borough anchor must not parse
    assert rgb_builder.parse_building_line(
        "10301 6 TO 14 ARLO RD STATEN ISLAND 64 MULTIPLE DWELLING A 595 15", "manhattan"
    ) is None
    # non-row noise must not parse
    assert rgb_builder.parse_building_line("List of Staten Island Buildings", "staten-island") is None
    assert rgb_builder.parse_building_line("12", "staten-island") is None
    assert rgb_builder.parse_building_line("10301 ARLO RD 64 MULTIPLE 595", "staten-island") is None


def test_full_pipeline_builds_panel_vintage_and_manifest_from_fixture(tmp_path: Path):
    fixture_bytes = FIXTURE.read_bytes()

    def fixture_fetch(url: str) -> bytes:
        assert "2024-DHCR-Bldg-File-Staten-Island.pdf" in url, url
        return fixture_bytes

    result = rgb_builder.build(
        fetch=fixture_fetch,
        run_utc=datetime(2026, 9, 3, tzinfo=timezone.utc),
        boroughs={"staten-island": rgb_builder.BOROUGHS["staten-island"]},
        root=tmp_path,
    )

    panel = pd.read_parquet(tmp_path / result["panel"])
    assert len(panel) > 0
    assert (panel["ieset_city_id"] == "ghsl_ucdb_r2024a:8099").all()
    assert (panel["borough"] == "staten-island").all()
    assert (panel["list_year"] == 2024).all()
    assert (panel["stabilized_buildings"] > 0).all()
    # zip grain rows sum to the borough building count
    assert panel["zip_stabilized_buildings"].sum() == panel["stabilized_buildings"].sum()

    vintage = pd.read_parquet(tmp_path / result["vintage"])
    assert len(vintage) == result["rows"] > 0
    assert vintage["zip"].str.fullmatch(r"\d{5}").all()
    assert (vintage["block"] > 0).all() and (vintage["lot"] > 0).all()

    manifest = yaml.safe_load((tmp_path / result["manifest"]).read_text())
    assert manifest["pipeline"] == "nyc_rgb_stabilized_buildings_panel"
    entry = manifest["entries"][0]
    assert entry["sha256"] == hashlib.sha256(fixture_bytes).hexdigest()
    assert entry["rows_parsed"] == result["rows"]
    assert manifest["artifacts"]["panel_sha256"] == sha256_path(tmp_path / result["panel"])


def test_promoted_repository_artifacts_are_present_and_consistent():
    """The live promotion (2026-09-03) must be backed by on-disk evidence."""
    panel_path = REPO_ROOT / "data" / "derived" / "nyc_rgb_stabilized_buildings_panel.parquet"
    manifests = sorted((REPO_ROOT / "data" / "manifests").glob("fetch_run_*_nyc_rgb_stabilized_buildings.yaml"))
    assert panel_path.exists(), "promoted panel parquet missing"
    assert manifests, "promotion fetch manifest missing"

    manifest = yaml.safe_load(manifests[-1].read_text())
    assert manifest["artifacts"]["panel_sha256"] == sha256_path(panel_path)
    assert manifest["artifacts"]["total_stabilized_buildings"] > 1000

    panel = pd.read_parquet(panel_path)
    assert set(panel["borough"]) == set(rgb_builder.BOROUGHS), "all five boroughs must be promoted"
    assert (panel["stabilized_buildings"] > 0).all()

    vintage_path = REPO_ROOT / manifest["artifacts"]["vintage_parquet"]
    assert vintage_path.exists(), "pinned vintage parquet missing"
    vintage = pd.read_parquet(vintage_path)
    assert len(vintage) == manifest["artifacts"]["total_stabilized_buildings"]
    for entry in manifest["entries"]:
        raw = REPO_ROOT / "data" / "raw" / "city_level" / "nyc_rgb_stabilized_buildings" / f"2024-{entry['borough']}.pdf"
        assert raw.exists(), f"raw PDF for {entry['borough']} missing"
        assert sha256_path(raw) == entry["sha256"]
