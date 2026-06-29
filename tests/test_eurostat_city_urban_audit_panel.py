from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_eurostat_city_urban_audit_panel as builder  # noqa: E402

OUTPUT = REPO_ROOT / "data" / "derived" / "eurostat_city_urban_audit_panel.parquet"

GRAIN = ["eurostat_city_code", "year", "indicator"]
REQUESTED_INDICATORS = {
    code for spec in builder.DATASETS.values() for code in spec["indicators"]
}


CITY_LABELS = {
    "AT": "Austria",
    "AT001C": "Wien",
    "DE001C": "Berlin (greater city)",
}


def _fake_jsonstat(dim_ids, indic, cities, times, value_map):
    """Construct a minimal JSON-stat 2.0 cube for the given dimensions."""
    sizes = []
    dimension = {}
    layout = {"indic_ur": indic, "cities": cities, "time": times, "freq": ["A"]}
    for did in dim_ids:
        codes = layout[did]
        sizes.append(len(codes))
        if did == "cities":
            labels = {code: CITY_LABELS.get(code, code) for code in codes}
        else:
            labels = {code: f"{code} label" for code in codes}
        dimension[did] = {
            "category": {
                "index": {code: i for i, code in enumerate(codes)},
                "label": labels,
            }
        }
    return {"id": dim_ids, "size": sizes, "dimension": dimension, "value": value_map}


def _spine(tmp_path: Path) -> Path:
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1",
                "ghsl_city_id": "1",
                "city_rank_2025": 50,
                "city_name": "Wien",
                "country_name": "Austria",
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


def _payloads():
    # urb_clivcon-like cube: freq x indic x cities x time
    dim_ids = ["freq", "indic_ur", "cities", "time"]
    indic = ["SA1001V", "SA1049V"]
    cities = ["AT", "AT001C", "DE001C"]  # AT national aggregate must be dropped
    times = ["2019", "2020"]
    # linear index: freq(size1) outer; strides computed row-major.
    # sizes = [1, 2, 3, 2] -> strides = [12, 6, 2, 1]
    # value at (0, i, c, t) = i*6 + c*2 + t
    value_map = {}
    # SA1001V (i=0), AT001C (c=1): 2019 and 2020
    value_map[0 * 6 + 1 * 2 + 0] = 100.0
    value_map[0 * 6 + 1 * 2 + 1] = 110.0
    # SA1049V (i=1), AT001C (c=1), 2020
    value_map[1 * 6 + 1 * 2 + 1] = 12.5
    # SA1001V (i=0), DE001C (c=2), 2020
    value_map[0 * 6 + 2 * 2 + 1] = 200.0
    # AT national aggregate (c=0) has a value that must be excluded
    value_map[0 * 6 + 0 * 2 + 0] = 999.0
    clivcon = _fake_jsonstat(dim_ids, indic, cities, times, value_map)

    # urb_cpop1-like cube: single indicator DE1001V
    indic2 = ["DE1001V"]
    cities2 = ["AT001C", "DE001C"]
    times2 = ["2020"]
    # sizes [1,1,2,1] strides [2,2,1,1]; value (0,0,c,0) = c
    pop_map = {0: 50000.0, 1: 60000.0}
    cpop1 = _fake_jsonstat(dim_ids, indic2, cities2, times2, pop_map)
    return {"urb_clivcon": clivcon, "urb_cpop1": cpop1}


def test_build_from_synthetic_jsonstat(tmp_path):
    spine = _spine(tmp_path)
    panel, stats = builder.build_panel(city_spine_path=spine, payloads=_payloads())

    # National aggregate AT is excluded; only AT001C and DE001C remain.
    assert set(panel["eurostat_city_code"].unique()) == {"AT001C", "DE001C"}
    # Eurostat code and name both preserved.
    assert "eurostat_city_code" in panel.columns
    assert "eurostat_city_name" in panel.columns
    # "(greater city)" qualifier is stripped for display/matching.
    assert set(panel.loc[panel["eurostat_city_code"].eq("DE001C"), "eurostat_city_name"]) == {"Berlin"}
    # ghsl_match_flag present and both seeded cities matched (Wien, Berlin).
    assert "ghsl_match_flag" in panel.columns
    assert panel["ghsl_match_flag"].any()
    assert stats["matched_city_count"] == 2
    # Indicators restricted to the requested set.
    assert set(panel["indicator"]).issubset(REQUESTED_INDICATORS)
    # Grain uniqueness.
    assert not panel.duplicated(subset=GRAIN).any()
    # No all-null value column.
    assert panel["value"].notna().any()

    output = tmp_path / "out.parquet"
    result = builder.emit(panel, stats, output, datetime(2026, 6, 29, tzinfo=timezone.utc))
    assert output.exists()
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "eurostat_city_urban_audit_panel"
    assert payload["entries"][0]["extra"]["stats"]["indicator_count"] >= 1


@pytest.mark.skipif(not OUTPUT.exists(), reason="panel not built yet")
def test_built_panel_contract():
    panel = pd.read_parquet(OUTPUT)
    # File exists and has rows.
    assert len(panel) > 0
    # Grain uniqueness.
    assert not panel.duplicated(subset=GRAIN).any()
    # ghsl_match_flag present, at least one matched city.
    assert "ghsl_match_flag" in panel.columns
    assert panel.loc[panel["ghsl_match_flag"], "eurostat_city_code"].nunique() >= 1
    # No all-null value column.
    for col in panel.columns:
        assert not panel[col].isna().all(), f"column {col} is entirely null"
    # Indicators come from the requested set.
    assert set(panel["indicator"]).issubset(REQUESTED_INDICATORS)
    # Eurostat code + name retained; codes are city-level (end in C).
    assert (panel["eurostat_city_code"].str.endswith("C")).all()
    assert panel["eurostat_city_name"].notna().any()
