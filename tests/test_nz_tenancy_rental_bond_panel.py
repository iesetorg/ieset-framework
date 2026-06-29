from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_nz_tenancy_rental_bond_panel as builder  # noqa: E402


CSV_HEADER = (
    '"Time Frame","Location Id","Location","Lodged Bonds","Active Bonds","Closed Bonds",'
    '"Median Rent","Geometric Mean Rent","Upper Quartile Rent","Lower Quartile Rent",'
    '"Log Std Dev Weekly Rent"'
)


def sample_csv() -> bytes:
    rows = [
        CSV_HEADER,
        '"1993-02-01"," -99","ALL","9,147","92,070","7116","150","151","200","120","0.43"',
        '"1993-02-01"," -1","NA","417","6,540","345","130","129","165","100","0.46"',
        '"2026-04-01","6","Auckland","2,500","30,000","1200","650","640","760","560","0.30"',
        '"2026-04-01","47","Wellington City","800","9,000","400","620","610","700","540","0.28"',
        '"2026-04-01","60","Christchurch City","900","11,000","500","520","515","600","460","0.25"',
        '"1993-02-01","6","Auckland","300","4,000","150","170","168","210","140","0.31"',
    ]
    return ("\n".join(rows) + "\n").encode("utf-8")


def make_spine(tmp_path: Path) -> Path:
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1147",
                "city_rank_2025": 312,
                "city_name": "Auckland",
                "country_name": "New Zealand",
            }
        ]
    ).to_parquet(spine, index=False)
    return spine


def test_build_nz_tenancy_rental_bond_panel_from_official_style_csv(tmp_path: Path):
    spine = make_spine(tmp_path)
    panel, stats = builder.build_panel(city_spine_path=spine, csv_bytes=sample_csv())

    # Aggregate roll-up rows (ALL / NA) are dropped.
    assert set(panel["location"]) == {"Auckland", "Wellington City", "Christchurch City"}
    assert "ALL" not in set(panel["location"])
    assert "NA" not in set(panel["location"])

    # Grain uniqueness: one row per (location_id, period, bedroom_band).
    grain = ["location_id", "period", "bedroom_band"]
    assert not panel.duplicated(grain).any()

    # Period normalisation.
    assert set(panel["period"]) == {"1993-02", "2026-04"}

    # Positive, plausible weekly rents.
    assert (panel["median_weekly_rent_nzd"] > 0).all()
    assert panel["median_weekly_rent_nzd"].between(50, 5000).all()
    assert (panel["geometric_mean_weekly_rent_nzd"] > 0).all()

    # ghsl_match_flag present and a major metro matched.
    assert "ghsl_match_flag" in panel.columns
    auckland = panel.loc[panel["location"].eq("Auckland")]
    assert auckland["ghsl_match_flag"].all()
    assert set(auckland["ieset_city_id"]) == {"ghsl_ucdb_r2024a:1147"}
    assert stats["unique_ieset_city_ids"] == 1

    # Non-top1000 TLAs remain unmatched but preserved with labels.
    wellington = panel.loc[panel["location"].eq("Wellington City")]
    assert not wellington["ghsl_match_flag"].any()
    assert wellington["ieset_city_id"].isna().all()

    # Observed bond-lodgement labelling and preserved original codes.
    assert (panel["rent_basis"] == "observed_bond_lodgement_weekly_rent").all()
    assert set(panel["location_id"]) == {"6", "47", "60"}
    assert (panel["bedroom_band"] == "ALL").all()
    assert len(stats["source_csv_sha256"]) == 64


def test_emit_and_manifest(tmp_path: Path):
    spine = make_spine(tmp_path)
    panel, stats = builder.build_panel(city_spine_path=spine, csv_bytes=sample_csv())

    output = tmp_path / "nz.parquet"
    result = builder.emit(panel, stats, output, datetime(2026, 6, 29, 5, tzinfo=timezone.utc))
    assert output.exists()
    reloaded = pd.read_parquet(output)
    assert len(reloaded) == len(panel)

    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T050000Z")
    payload = yaml.safe_load(manifest.read_text())
    entry = payload["entries"][0]
    assert entry["series_id"] == "nz_tenancy_rental_bond_panel"
    assert entry["publisher"] == "nz_tenancy_services_mbie"
    assert entry["currency"] == "NZD"
    assert len(entry["sha256"]) == 64
