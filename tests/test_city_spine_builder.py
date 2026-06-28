from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_city_spine_top1000 as city_spine  # noqa: E402


def test_city_spine_builder_ranks_and_writes_artifacts(tmp_path: Path):
    fixture = tmp_path / "ghsl_fixture.csv"
    fixture.write_text(
        "\n".join(
            [
                "ID_HDC_G0,GC_UCN_MAI_2025,GC_CNT_GAD_2025,GC_ISO3_2025,GC_POP_TOT_2025,GC_UCA_KM2_2025,GC_X_CTR_2025,GC_Y_CTR_2025",
                "uc_lagos,Lagos,Nigeria,NGA,21500000,1200,3.38,6.52",
                "uc_paris,Paris,France,FRA,11000000,2800,2.35,48.85",
                "uc_tokyo,Tokyo,Japan,JPN,37200000,8500,139.69,35.68",
                "uc_small,Smallville,Freedonia,FRE,1000,10,1,1",
            ]
        )
        + "\n"
    )

    result = city_spine.build_city_spine(
        input_path=fixture,
        limit=2,
        output_dir=tmp_path / "derived",
        manifest_dir=tmp_path / "manifests",
        fetch_ts=datetime(2026, 6, 28, tzinfo=timezone.utc),
    )

    universe = result["universe"]
    assert universe["city_name"].tolist() == ["Tokyo", "Lagos"]
    assert universe["city_rank_2025"].tolist() == [1, 2]
    assert universe["ieset_city_id"].tolist() == [
        "ghsl_ucdb_r2024a:uc_tokyo",
        "ghsl_ucdb_r2024a:uc_lagos",
    ]
    assert universe.loc[0, "source_population_2025_column"] == "GC_POP_TOT_2025"
    assert round(float(universe.loc[1, "density_per_km2_2025"]), 2) == 17916.67

    crosswalks = result["crosswalks"]
    assert len(crosswalks) == 2
    assert set(crosswalks["source_system"]) == {"ghsl_ucdb_r2024a"}
    assert set(crosswalks["match_type"]) == {"canonical_native_id"}
    assert not crosswalks["manual_review_required"].any()

    artifacts = result["artifacts"]["city_universe_top1000"]
    for key in ("csv_path", "json_path", "parquet_path"):
        assert Path(artifacts[key]).exists()

    manifest = result["manifest"]
    assert manifest.name == "fetch_run_2026-06-28T000000Z_city_spine.yaml"
    payload = yaml.safe_load(manifest.read_text())
    assert payload["run_utc"] == "2026-06-28T000000Z"
    assert [entry["series_id"] for entry in payload["entries"]] == [
        "city_universe_top1000",
        "city_crosswalks",
    ]


def test_city_spine_builder_selects_valid_xlsx_sheet(tmp_path: Path):
    workbook_path = tmp_path / "ghsl_multisheet.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Description"
    ws.append(["Name", "not the data table"])

    data = wb.create_sheet("GENERAL_CHARACTERISTICS")
    data.append(["ID_UC_G0", "GC_UCN_MAI_2025", "GC_CNT_GAD_2025", "GC_POP_TOT_2025", "GC_UCA_KM2_2025"])
    data.append([10933, "Guangzhou", "China", 42987704, 6454])
    data.append([5472, "Jakarta", "Indonesia", 40545126, 4614])
    wb.save(workbook_path)

    frame, sheet_name = city_spine.read_table(workbook_path)

    assert sheet_name["input_sheet"] == "GENERAL_CHARACTERISTICS"
    universe, _crosswalks, _spec, stats = city_spine.build_frames(frame, limit=1)
    assert universe.loc[0, "ieset_city_id"] == "ghsl_ucdb_r2024a:10933"
    assert stats["country_name_count"] == 1
    assert stats["missing_country_iso3_rows"] == 1
