from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_ireland_rtb_rent_index_panel as builder  # noqa: E402

OUTPUT = REPO_ROOT / "data" / "derived" / "ireland_rtb_rent_index_panel.parquet"

GRAIN = builder.GRAIN


def _spine(tmp_path: Path) -> Path:
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:394",
                "ghsl_city_id": "394",
                "city_rank_2025": 474,
                "city_name": "Dublin",
                "country_name": "Ireland",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2",
                "ghsl_city_id": "2",
                "city_rank_2025": 80,
                "city_name": "Berlin",
                "country_name": "Germany",
            },
        ]
    ).to_parquet(spine, index=False)
    return spine


def _payload():
    """Minimal RIA02-shaped JSON-stat 2.0 cube.

    Dimension order mirrors the live CSO table:
    STATISTIC x TLIST(A1) x bedrooms x property_type x location.
    """
    dim_ids = [
        builder.STATISTIC_DIM,
        builder.TIME_DIM,
        builder.BEDROOMS_DIM,
        builder.PROPTYPE_DIM,
        builder.LOCATION_DIM,
    ]
    stat = ["RIA02"]
    times = ["2019", "2020"]
    beds = ["-", "02"]
    props = ["-", "04"]
    locs = ["120500", "113000", "999999"]  # Dublin, Cork, an unmatched location
    layout = {
        builder.STATISTIC_DIM: stat,
        builder.TIME_DIM: times,
        builder.BEDROOMS_DIM: beds,
        builder.PROPTYPE_DIM: props,
        builder.LOCATION_DIM: locs,
    }
    stat_labels = {"RIA02": "RTB Average Monthly Rent Report"}
    bed_labels = {"-": "All bedrooms", "02": "Two bed"}
    prop_labels = {"-": "All property types", "04": "Apartment"}
    loc_labels = {"120500": "Dublin", "113000": "Cork", "999999": "Nowhere"}
    label_for = {
        builder.STATISTIC_DIM: stat_labels,
        builder.BEDROOMS_DIM: bed_labels,
        builder.PROPTYPE_DIM: prop_labels,
        builder.LOCATION_DIM: loc_labels,
    }
    sizes = [len(layout[d]) for d in dim_ids]
    dimension = {}
    for d in dim_ids:
        codes = layout[d]
        labels = {c: label_for.get(d, {}).get(c, c) for c in codes}
        dimension[d] = {"category": {"index": {c: i for i, c in enumerate(codes)}, "label": labels}}

    # Dense value map: row-major strides.
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    def lin(s, t, b, p, l):
        return s * strides[0] + t * strides[1] + b * strides[2] + p * strides[3] + l * strides[4]

    value_map = {}
    base = 1000.0
    for ti in range(len(times)):
        for bi in range(len(beds)):
            for pi in range(len(props)):
                for li in range(len(locs)):
                    value_map[lin(0, ti, bi, pi, li)] = base + ti * 100 + bi * 10 + pi * 5 + li
    return {"id": dim_ids, "size": sizes, "dimension": dimension, "value": value_map}


def test_build_from_synthetic_jsonstat(tmp_path):
    spine = _spine(tmp_path)
    panel, stats = builder.build_panel(city_spine_path=spine, payload=_payload())

    # Grain uniqueness.
    assert not panel.duplicated(subset=GRAIN).any()
    # Original CSO/RTB codes + labels preserved.
    for col in ("location_code", "location_name", "bedrooms_code", "property_type_code"):
        assert col in panel.columns
    assert set(panel["location_code"].unique()) == {"120500", "113000", "999999"}
    assert "Dublin" in set(panel["location_name"])
    # Positive plausible rents in EUR.
    assert (panel["standardised_avg_rent_eur"] > 0).all()
    assert (panel["currency"] == "EUR").all()
    # Labelled as official RTB standardised rents.
    assert panel["rent_measure"].str.contains("standardised").all()
    # ghsl_match_flag present; Dublin matched to GHSL.
    assert "ghsl_match_flag" in panel.columns
    dublin = panel[panel["location_code"] == "120500"]
    assert dublin["ghsl_match_flag"].all()
    assert (dublin["ghsl_city_id"] == "394").all()
    # Unmatched location flagged false with no ghsl id.
    nowhere = panel[panel["location_code"] == "999999"]
    assert not nowhere["ghsl_match_flag"].any()
    assert nowhere["ghsl_city_id"].isna().all()
    assert stats["dublin_matched"] is True

    output = tmp_path / "out.parquet"
    result = builder.emit(panel, stats, output, datetime(2026, 6, 29, tzinfo=timezone.utc))
    assert output.exists()
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "ireland_rtb_rent_index_panel"
    assert payload["entries"][0]["currency"] == "EUR"


@pytest.mark.skipif(not OUTPUT.exists(), reason="panel not built yet")
def test_built_panel_contract():
    panel = pd.read_parquet(OUTPUT)
    # File exists and has rows.
    assert len(panel) > 0
    # Grain uniqueness.
    assert not panel.duplicated(subset=GRAIN).any()
    # Positive plausible rents (EUR): standardised monthly rents are roughly 100..10000.
    rents = panel["standardised_avg_rent_eur"]
    assert (rents > 0).all()
    assert rents.between(50, 20000).mean() > 0.99
    # ghsl_match_flag present, at least one matched location; Dublin matched.
    assert "ghsl_match_flag" in panel.columns
    assert panel.loc[panel["ghsl_match_flag"], "location_code"].nunique() >= 1
    assert panel.loc[panel["location_code"] == "120500", "ghsl_match_flag"].any()
    # Original CSO/RTB codes preserved and non-null.
    assert panel["location_code"].notna().all()
    assert panel["bedrooms_code"].notna().all()
    assert panel["property_type_code"].notna().all()
    # Labelled official RTB standardised rents.
    assert panel["rent_measure"].str.contains("standardised").all()
