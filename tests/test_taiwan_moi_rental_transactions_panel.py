from __future__ import annotations

import csv
import io
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_taiwan_moi_rental_transactions_panel as builder  # noqa: E402


RENT_HEADER = [
    "鄉鎮市區",
    "交易標的",
    "土地位置建物門牌",
    "土地面積平方公尺",
    "都市土地使用分區",
    "非都市土地使用分區",
    "非都市土地使用編定",
    "租賃年月日",
    "租賃筆棟數",
    "租賃層次",
    "總樓層數",
    "建物型態",
    "主要用途",
    "主要建材",
    "建築完成年月",
    "建物總面積平方公尺",
    "建物現況格局-房",
    "建物現況格局-廳",
    "建物現況格局-衛",
    "建物現況格局-隔間",
    "有無管理組織",
    "有無附傢俱",
    "總額元",
    "單價元平方公尺",
    "車位類別",
    "車位面積平方公尺",
    "車位總額元",
    "備註",
    "編號",
    "出租型態",
    "有無管理員",
    "租賃期間",
    "有無電梯",
    "附屬設備",
    "租賃住宅服務",
]


def rent_csv(rows: list[dict[str, object]]) -> str:
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=RENT_HEADER)
    writer.writeheader()
    writer.writerow({"鄉鎮市區": "The villages and towns urban district"})
    for row in rows:
        output = {column: "" for column in RENT_HEADER}
        output.update(row)
        writer.writerow(output)
    return handle.getvalue()


def test_build_taiwan_moi_rental_transactions_panel_from_official_style_zip(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1142",
                "city_rank_2025": 37,
                "city_name": "Taipei",
                "country_name": "Taiwan",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:501",
                "city_rank_2025": 765,
                "city_name": "Hsinchu",
                "country_name": "Taiwan",
            },
        ]
    ).to_parquet(spine, index=False)

    zip_path = tmp_path / "lvr_landcsv.zip"
    manifest = "\n".join(
        [
            "name,schema,description",
            "a_lvr_land_c.csv,schema-main-rent.csv,臺北市不動產租賃",
            "o_lvr_land_c.csv,schema-main-rent.csv,新竹市不動產租賃",
            "a_lvr_land_a.csv,schema-main.csv,臺北市不動產買賣",
        ]
    )
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("manifest.csv", manifest)
        archive.writestr(
            "build_time.xml",
            "<root><rent>租賃案件契約日期115年5月1日至115年5月10日</rent></root>",
        )
        archive.writestr(
            "a_lvr_land_c.csv",
            rent_csv(
                [
                    {
                        "鄉鎮市區": "中山區",
                        "交易標的": "租賃房屋",
                        "土地位置建物門牌": "臺北市中山區測試路一段1號",
                        "土地面積平方公尺": "0",
                        "租賃年月日": "1150501",
                        "租賃筆棟數": "土地0建物1車位0",
                        "租賃層次": "三層",
                        "總樓層數": "5",
                        "建物型態": "公寓",
                        "主要用途": "住家用",
                        "主要建材": "鋼筋混凝土造",
                        "建築完成年月": "0710506",
                        "建物總面積平方公尺": "11.0",
                        "建物現況格局-房": "4",
                        "建物現況格局-廳": "1",
                        "建物現況格局-衛": "2",
                        "建物現況格局-隔間": "有",
                        "有無管理組織": "無",
                        "有無附傢俱": "有",
                        "總額元": "9300",
                        "單價元平方公尺": "845",
                        "備註": "測試列",
                        "編號": "RPTAIPEI001",
                        "出租型態": "分租雅房",
                        "有無管理員": "無",
                        "租賃期間": "1150501~1160430",
                        "有無電梯": "無",
                        "附屬設備": "冷氣",
                        "租賃住宅服務": "否",
                    }
                ]
            ),
        )
        archive.writestr(
            "o_lvr_land_c.csv",
            rent_csv(
                [
                    {
                        "鄉鎮市區": "東區",
                        "交易標的": "租賃房屋",
                        "土地位置建物門牌": "新竹市東區測試路二段2號",
                        "租賃年月日": "1150502",
                        "建築完成年月": "11505",
                        "建物總面積平方公尺": "22.0",
                        "總額元": "21000",
                        "單價元平方公尺": "955",
                        "編號": "RPHSC001",
                        "出租型態": "整層住家",
                        "租賃期間": "1150502~1160501",
                    }
                ]
            ),
        )

    panel, stats = builder.build_panel(city_spine_path=spine, input_zip=zip_path)

    assert len(panel) == 2
    assert "土地位置建物門牌" not in panel.columns
    assert "address" not in panel.columns
    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:1142", "ghsl_ucdb_r2024a:501"}
    assert set(panel["period"]) == {"2026-05"}
    assert panel.loc[panel["municipality_name_en"].eq("Taipei"), "total_rent_ntd"].iloc[0] == 9300
    assert panel.loc[panel["municipality_name_en"].eq("Taipei"), "building_completion_month"].iloc[0] == "1982-05"
    assert panel.loc[panel["municipality_name_en"].eq("Hsinchu"), "building_completion_month"].iloc[0] == "2026-05"
    assert stats["panel_rows"] == 2
    assert stats["source_rent_files"] == 2
    assert stats["unique_ieset_city_ids"] == 2
    assert len(stats["source_archive_sha256"]) == 64
    assert stats["address_policy"].startswith("Publisher street address field is intentionally omitted")

    output = tmp_path / "taiwan.parquet"
    result = builder.emit(panel, stats, output, datetime(2026, 6, 29, 23, tzinfo=timezone.utc))
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T230000Z")
    assert output.exists()
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "taiwan_moi_rental_transactions_panel"
