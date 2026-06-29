from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_colombia_dane_ipc_city_rent_panel as builder  # noqa: E402


def write_colombia_spine(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3881",
                "city_rank_2025": 33,
                "city_name": "Bogota",
                "country_name": "Colombia",
                "country_iso3": "COL",
                "population_2025": 10419361,
                "area_km2_2025": 793,
                "density_per_km2_2025": 13139,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2676",
                "city_rank_2025": 159,
                "city_name": "Medellin",
                "country_name": "Colombia",
                "country_iso3": "COL",
                "population_2025": 4250000,
                "area_km2_2025": 450,
                "density_per_km2_2025": 9444,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1158",
                "city_rank_2025": 189,
                "city_name": "Cali",
                "country_name": "Colombia",
                "country_iso3": "COL",
                "population_2025": 3300000,
                "area_km2_2025": 360,
                "density_per_km2_2025": 9167,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3275",
                "city_rank_2025": 270,
                "city_name": "Cartagena",
                "country_name": "Colombia",
                "country_iso3": "COL",
                "population_2025": 1100000,
                "area_km2_2025": 260,
                "density_per_km2_2025": 4231,
            },
        ]
    ).to_parquet(path, index=False)


def test_build_colombia_dane_ipc_panel_from_year_month_export(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    write_colombia_spine(spine)
    rows = [
        {
            "Ciudad": "Bogota D.C.",
            "Año": "2024",
            "Mes": "Mayo",
            "Codigo": "0411",
            "Gasto Basico": "Arriendo efectivo",
            "Indice": "123,4",
            "Variacion mensual": "0,5",
            "Variacion anual": "8,2",
            "Ponderacion": "17,6",
        },
        {
            "Ciudad": "Medellín",
            "Año": "2024",
            "Mes": "5",
            "Codigo": "411",
            "Gasto Basico": "Servicios de vivienda ocupada",
            "Indice": "118.2",
            "Variacion mensual": 0.2,
            "Variacion anual": 7.5,
            "Ponderacion": 15.0,
        },
        {
            "Ciudad": "Cali",
            "Año": "2024",
            "Mes": "Mayo",
            "Codigo": "0451",
            "Gasto Basico": "Electricidad",
            "Indice": "99,9",
            "Variacion mensual": "1,1",
            "Variacion anual": "6,0",
            "Ponderacion": "4,0",
        },
    ]

    panel, stats = builder.build_panel(city_spine_path=spine, rows=rows)

    assert len(panel) == 2
    assert set(panel["period"]) == {"2024-05"}
    assert set(panel["dane_city_name_norm"]) == {"BOGOTA D C", "MEDELLIN"}
    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:3881", "ghsl_ucdb_r2024a:2676"}
    assert panel.loc[panel["dane_city_name_norm"].eq("BOGOTA D C"), "index_value"].iloc[0] == 123.4
    assert stats["matched_cities"] == 2
    assert stats["matched_observation_rows"] == 2


def test_build_colombia_dane_ipc_panel_from_period_export_and_manifest(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    write_colombia_spine(spine)
    rows = [
        {
            "Dominio": "Cali",
            "Periodo": "2024-06-01",
            "Producto": "Arriendo efectivo",
            "Indice": "101.5",
        }
    ]

    panel, stats = builder.build_panel(city_spine_path=spine, rows=rows)
    assert panel["period"].tolist() == ["2024-06"]
    assert panel["month"].tolist() == [6]
    assert panel["ieset_city_id"].tolist() == ["ghsl_ucdb_r2024a:1158"]

    output = tmp_path / "colombia.parquet"
    fetch_ts = datetime(2026, 6, 29, 4, tzinfo=timezone.utc)
    result = builder.emit(panel, stats, output, fetch_ts)
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T040000Z")

    assert output.exists()
    payload = yaml.safe_load(manifest.read_text())
    assert payload["pipeline"] == "colombia_dane_ipc_city_rent_panel"
    assert payload["entries"][0]["series_id"] == "colombia_dane_ipc_city_rent_panel"


def test_build_colombia_dane_ipc_panel_from_official_annex_workbook(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    write_colombia_spine(spine)
    workbook = tmp_path / "anex-IPC-may2026.xlsx"
    housing = "Alojamiento, Agua, Electricidad, Gas Y Otros Combustibles"

    def sheet(title: str, bogota_value: float, cartagena_value: float) -> pd.DataFrame:
        rows = [[pd.NA] * 6 for _ in range(9)]
        rows[2][0] = title
        rows[5][0] = "Mayo de 2026"
        rows[6] = ["Ciudades", "Alimentos Y Bebidas No Alcohólicas", "Bebidas Alcohólicas Y Tabaco", housing, "Total", pd.NA]
        rows[7] = ["Total Nacional", 1.0, 2.0, 3.0, 4.0, pd.NA]
        rows[8] = ["Bogotá D.C.", 0.1, 0.2, bogota_value, 0.4, pd.NA]
        rows.append(["Cartagena De Indias", 0.5, 0.6, cartagena_value, 0.8, pd.NA])
        return pd.DataFrame(rows)

    with pd.ExcelWriter(workbook) as writer:
        sheet("IPC. Variación mensual, total y por divisiones de bienes y servicios, según ciudades", 0.73, 0.53).to_excel(
            writer, sheet_name="4", header=False, index=False
        )
        sheet(
            "IPC. Variación año corrido, total y por divisiones de bienes y servicios, según ciudades",
            2.78,
            3.03,
        ).to_excel(writer, sheet_name="5", header=False, index=False)
        sheet("IPC. Variación anual, total y por divisiones de bienes y servicios, según ciudades", 4.32, 3.43).to_excel(
            writer, sheet_name="6", header=False, index=False
        )

    panel, stats = builder.build_panel(city_spine_path=spine, input_path=workbook)

    assert len(panel) == 2
    assert set(panel["period"]) == {"2026-05"}
    assert set(panel["item_code"]) == {"04"}
    assert panel["index_value"].isna().all()
    bogota = panel[panel["ghsl_city_name"].eq("Bogota")].iloc[0]
    assert bogota["monthly_variation_pct"] == 0.73
    assert bogota["year_to_date_variation_pct"] == 2.78
    assert bogota["annual_variation_pct"] == 4.32
    assert bool(panel[panel["ghsl_city_name"].eq("Cartagena")]["manual_review_required"].iloc[0]) is False
    assert stats["matched_cities"] == 2
    assert stats["source_workbook_count"] == 1
