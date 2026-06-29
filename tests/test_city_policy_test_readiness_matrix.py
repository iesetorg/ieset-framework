from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_city_policy_test_readiness_matrix as readiness_builder  # noqa: E402


def test_city_policy_test_readiness_matrix_marks_ready_and_partial_cities(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "city_rank_2025": 22,
                "city_name": "New York City",
                "country_name": "United States",
                "country_iso3": "USA",
                "population_2025": 19000000,
                "area_km2_2025": 1000,
                "density_per_km2_2025": 19000,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "city_rank_2025": 96,
                "city_name": "San Francisco",
                "country_name": "United States",
                "country_iso3": "USA",
                "population_2025": 4700000,
                "area_km2_2025": 1600,
                "density_per_km2_2025": 2900,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5816",
                "city_rank_2025": 35,
                "city_name": "London",
                "country_name": "United Kingdom",
                "country_iso3": "GBR",
                "population_2025": 12000000,
                "area_km2_2025": 1800,
                "density_per_km2_2025": 6500,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2878",
                "city_rank_2025": 40,
                "city_name": "Paris",
                "country_name": "France",
                "country_iso3": "FRA",
                "population_2025": 11000000,
                "area_km2_2025": 2800,
                "density_per_km2_2025": 3900,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5071",
                "city_rank_2025": 118,
                "city_name": "Barcelona",
                "country_name": "Spain",
                "country_iso3": "ESP",
                "population_2025": 5600000,
                "area_km2_2025": 1100,
                "density_per_km2_2025": 5091,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:231",
                "city_rank_2025": 215,
                "city_name": "Lisbon",
                "country_name": "Portugal",
                "country_iso3": "PRT",
                "population_2025": 2900000,
                "area_km2_2025": 1000,
                "density_per_km2_2025": 2900,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8121",
                "city_rank_2025": 50,
                "city_name": "Rome",
                "country_name": "Italy",
                "country_iso3": "ITA",
                "population_2025": 3700000,
                "area_km2_2025": 1200,
                "density_per_km2_2025": 3083,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3338",
                "city_rank_2025": 60,
                "city_name": "Madrid",
                "country_name": "Spain",
                "country_iso3": "ESP",
                "population_2025": 6600000,
                "area_km2_2025": 1500,
                "density_per_km2_2025": 4400,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2879",
                "city_rank_2025": 130,
                "city_name": "Lyon",
                "country_name": "France",
                "country_iso3": "FRA",
                "population_2025": 1700000,
                "area_km2_2025": 900,
                "density_per_km2_2025": 1889,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5483",
                "city_rank_2025": 140,
                "city_name": "Berlin",
                "country_name": "Germany",
                "country_iso3": "DEU",
                "population_2025": 4400000,
                "area_km2_2025": 1300,
                "density_per_km2_2025": 3385,
            },
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
                "ieset_city_id": "ghsl_ucdb_r2024a:178",
                "city_rank_2025": 85,
                "city_name": "Singapore",
                "country_name": "Singapore",
                "country_iso3": "SGP",
                "population_2025": 5117759,
                "area_km2_2025": 683,
                "density_per_km2_2025": 7493,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:345",
                "city_rank_2025": 547,
                "city_name": "Sembawang",
                "country_name": "Singapore",
                "country_iso3": "SGP",
                "population_2025": 960308,
                "area_km2_2025": 119,
                "density_per_km2_2025": 8070,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:11185",
                "city_rank_2025": 93,
                "city_name": "Hong Kong",
                "country_name": "China",
                "country_iso3": None,
                "population_2025": 4807599,
                "area_km2_2025": 280,
                "density_per_km2_2025": 17170,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "city_rank_2025": 334,
                "city_name": "Stockholm",
                "country_name": "Sweden",
                "country_iso3": None,
                "population_2025": 1543892,
                "area_km2_2025": 240,
                "density_per_km2_2025": 6433,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1007",
                "city_rank_2025": 100,
                "city_name": "Dubai",
                "country_name": "United Arab Emirates",
                "country_iso3": None,
                "population_2025": 4565478,
                "area_km2_2025": 854,
                "density_per_km2_2025": 5346,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1142",
                "city_rank_2025": 37,
                "city_name": "Taipei",
                "country_name": "Taiwan",
                "country_iso3": None,
                "population_2025": 9686521,
                "area_km2_2025": 972,
                "density_per_km2_2025": 9966,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2324",
                "city_rank_2025": 104,
                "city_name": "Sydney",
                "country_name": "Australia",
                "country_iso3": "AUS",
                "population_2025": 4900000,
                "area_km2_2025": 1700,
                "density_per_km2_2025": 2882,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1147",
                "city_rank_2025": 147,
                "city_name": "Auckland",
                "country_name": "New Zealand",
                "country_iso3": "NZL",
                "population_2025": 1650000,
                "area_km2_2025": 1100,
                "density_per_km2_2025": 1500,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:109",
                "city_rank_2025": 290,
                "city_name": "Sofia",
                "country_name": "Bulgaria",
                "country_iso3": "BGR",
                "population_2025": 1300000,
                "area_km2_2025": 490,
                "density_per_km2_2025": 2653,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1689",
                "city_rank_2025": 360,
                "city_name": "Zurich",
                "country_name": "Switzerland",
                "country_iso3": "CHE",
                "population_2025": 1400000,
                "area_km2_2025": 870,
                "density_per_km2_2025": 1609,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:394",
                "city_rank_2025": 220,
                "city_name": "Dublin",
                "country_name": "Ireland",
                "country_iso3": "IRL",
                "population_2025": 1270000,
                "area_km2_2025": 318,
                "density_per_km2_2025": 3994,
            },
        ]
    ).to_parquet(spine, index=False)

    zillow = tmp_path / "zillow.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "zillow_region_id": 1,
                "month_end": "2025-01-31",
                "zori_usd": 3000,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "zillow_region_id": 2,
                "month_end": "2025-01-31",
                "zori_usd": 3200,
            },
        ]
    ).to_parquet(zillow, index=False)

    permits = tmp_path / "permits.parquet"
    pd.DataFrame(
        [
            {"ieset_city_id": "ghsl_ucdb_r2024a:1461", "year": 2025, "total_units": 100},
        ]
    ).to_parquet(permits, index=False)

    nyc_quality = tmp_path / "nyc_quality.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "year": 2025,
                "source_dataset_key": "dob_permit_issuance",
                "value": 10,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "year": 2025,
                "source_dataset_key": "hpd_violation",
                "value": 20,
            },
        ]
    ).to_parquet(nyc_quality, index=False)

    sf_quality = tmp_path / "sf_quality.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "year": 2025,
                "source_dataset_key": "building_permit",
                "value": 30,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "year": 2025,
                "source_dataset_key": "rent_board_inventory",
                "value": 40,
            },
        ]
    ).to_parquet(sf_quality, index=False)

    nyc_reg = tmp_path / "nyc_reg.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "year": 2026,
                "benefit_family": "421a",
                "value_count": 5,
                "unit_count": 100,
                "restricted_unit_count": 20,
            }
        ]
    ).to_parquet(nyc_reg, index=False)

    catalonia_rent_contracts = tmp_path / "catalonia.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5071",
                "year": 2025,
                "municipality_code": "08019",
                "avg_monthly_rent_eur": 1230.5,
                "contracts": 1000,
            }
        ]
    ).to_parquet(catalonia_rent_contracts, index=False)

    france_reference = tmp_path / "france_reference.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2878",
                "year": 2024,
                "zone_id": "1",
                "reference_rent_eur_m2": 28.3,
                "ceiling_rent_eur_m2": 34.0,
            }
        ]
    ).to_parquet(france_reference, index=False)

    uk_private_rents = tmp_path / "uk_private_rents.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5816",
                "period_end_year": 2023,
                "local_authority_code": "E09000001",
                "bedroom_category": "all_categories",
                "median_monthly_rent_gbp": 2159,
            }
        ]
    ).to_parquet(uk_private_rents, index=False)

    uk_house_building = tmp_path / "uk_house_building.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5816",
                "fiscal_year": "2023-24",
                "fiscal_year_start": 2023,
                "fiscal_year_end": 2024,
                "local_authority_code": "E09000001",
                "all_starts": 30,
                "all_completions": 40,
            }
        ]
    ).to_parquet(uk_house_building, index=False)

    colombia_dane_ipc = tmp_path / "colombia_dane_ipc.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3881",
                "period": "2024-05",
                "item_name_norm": "ARRIENDO EFECTIVO",
                "index_value": 123.4,
            }
        ]
    ).to_parquet(colombia_dane_ipc, index=False)

    singapore_hdb = tmp_path / "singapore_hdb.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:178",
                "quarter": "2026-Q1",
                "town_norm": "ANG MO KIO",
                "flat_type": "3-RM",
                "median_monthly_rent_sgd": 2800,
            }
        ]
    ).to_parquet(singapore_hdb, index=False)

    singapore_hdb_ura = tmp_path / "singapore_hdb_ura.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:345",
                "period": "2026-05",
                "period_start": "2026-05-01",
                "period_end": "2026-05-31",
                "source_dataset_key": "hdb_approval",
                "town_norm": "SEMBAWANG",
                "flat_type": "4-ROOM",
                "project_name_norm": None,
                "postal_district": None,
                "monthly_rent_sgd": 3200,
                "rental_contracts": None,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:178",
                "period": "2026-Q1",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
                "source_dataset_key": "ura_private_non_landed",
                "town_norm": None,
                "flat_type": None,
                "project_name_norm": "AMBER PARK",
                "postal_district": 15,
                "monthly_rent_sgd": None,
                "rental_contracts": 28,
            },
        ]
    ).to_parquet(singapore_hdb_ura, index=False)

    hong_kong_rvd = tmp_path / "hong_kong_rvd.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:11185",
                "year": 2025,
                "measure": "rental_index",
                "value": 196.7,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:11185",
                "year": 2025,
                "measure": "completions",
                "value": 25000,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:11185",
                "year": 2025,
                "measure": "vacancy_rate",
                "value": 0.043,
            },
        ]
    ).to_parquet(hong_kong_rvd, index=False)

    stockholm_queue = tmp_path / "stockholm_queue.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "year": 2025,
                "queue_name": "Bostadskön",
                "measure": "rent_band_count",
                "allocated_dwellings": 1455,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "year": 2025,
                "queue_name": "Bostadskön",
                "measure": "queue_time_band_count",
                "allocated_dwellings": 722,
            },
        ]
    ).to_parquet(stockholm_queue, index=False)

    sweden_scb = tmp_path / "sweden_scb.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "year": 2025,
                "measure": "municipal_rent_per_sqm",
                "value": 1734,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "year": 2025,
                "measure": "completed_new_dwellings",
                "value": 1200,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "year": 2025,
                "measure": "dwelling_stock",
                "value": 500000,
            },
        ]
    ).to_parquet(sweden_scb, index=False)

    dubai_data = tmp_path / "dubai_data.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1007",
                "period": "2026-01",
                "source_dataset_key": "residential_rent_price_index",
                "segment_norm": "RRPI GENERAL INDEX",
                "housing_supply_relevant": False,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1007",
                "period": "2026-01",
                "source_dataset_key": "building_permits",
                "segment_norm": "NUMBER",
                "housing_supply_relevant": True,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1007",
                "period": "2026-01",
                "source_dataset_key": "completed_buildings",
                "segment_norm": "NUMBER",
                "housing_supply_relevant": True,
            },
        ]
    ).to_parquet(dubai_data, index=False)

    taiwan_moi = tmp_path / "taiwan_moi.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1142",
                "period": "2026-05",
                "municipality_name_en": "Taipei",
                "total_rent_ntd": 9300,
            }
        ]
    ).to_parquet(taiwan_moi, index=False)

    australia_rental_bond = tmp_path / "australia_rental_bond.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2324",
                "ghsl_match_flag": True,
                "period": "2026-05",
                "geography_id": "greater_sydney",
                "dwelling_type_label": "flat_unit",
                "bond_lodgement_count": 5712,
                "rent_measure": "observed_bond_lodgement_weekly_rent",
            },
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "period": "2026-05",
                "geography_id": "rest_of_nsw",
                "dwelling_type_label": "house",
                "bond_lodgement_count": 100,
                "rent_measure": "observed_bond_lodgement_weekly_rent",
            },
        ]
    ).to_parquet(australia_rental_bond, index=False)

    nz_rental_bond = tmp_path / "nz_rental_bond.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1147",
                "ghsl_match_flag": True,
                "period": "2026-04",
                "location": "Auckland",
                "bedroom_band": "ALL",
                "lodged_bonds": 4200,
                "rent_basis": "observed_bond_lodgement_weekly_rent",
            },
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "period": "2026-04",
                "location": "Far North District",
                "bedroom_band": "ALL",
                "lodged_bonds": 42,
                "rent_basis": "observed_bond_lodgement_weekly_rent",
            },
        ]
    ).to_parquet(nz_rental_bond, index=False)

    eurostat_urban_audit = tmp_path / "eurostat_urban_audit.parquet"
    pd.DataFrame(
        [
            # Sofia: observed rent per m2 (SA1049V) + dwelling stock -> rent_supply_ready
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:109",
                "ghsl_match_flag": True,
                "year": 2022,
                "indicator": "SA1049V",
                "value": 42.23,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:109",
                "ghsl_match_flag": True,
                "year": 2021,
                "indicator": "SA1001V",
                "value": 600000.0,
            },
            # Zurich: dwelling stock + tenure + purchase price proxy, NO observed rent -> supply only
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1689",
                "ghsl_match_flag": True,
                "year": 2021,
                "indicator": "SA1001V",
                "value": 220000.0,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1689",
                "ghsl_match_flag": True,
                "year": 2021,
                "indicator": "SA1013V",
                "value": 120000.0,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1689",
                "ghsl_match_flag": True,
                "year": 2021,
                "indicator": "SA1051V",
                "value": 1200000.0,
            },
            # unmatched row must be ignored
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "year": 2020,
                "indicator": "SA1049V",
                "value": 10.0,
            },
        ]
    ).to_parquet(eurostat_urban_audit, index=False)

    ireland_rtb = tmp_path / "ireland_rtb.parquet"
    pd.DataFrame(
        [
            # Dublin: matched GHSL 394 observed RTB standardised rent -> first_order rent
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:394",
                "ghsl_match_flag": True,
                "location_name": "Dublin",
                "year": 2025,
                "property_type_label": "All property types",
                "bedrooms_label": "All bedrooms",
                "standardised_avg_rent_eur": 2100.5,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:394",
                "ghsl_match_flag": True,
                "location_name": "Dublin",
                "year": 2024,
                "property_type_label": "Apartment",
                "bedrooms_label": "Two bed",
                "standardised_avg_rent_eur": 1980.0,
            },
            # unmatched RTB location must be ignored
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "location_name": "Carlow",
                "year": 2025,
                "property_type_label": "All property types",
                "bedrooms_label": "All bedrooms",
                "standardised_avg_rent_eur": 1100.0,
            },
        ]
    ).to_parquet(ireland_rtb, index=False)

    portugal_ine = tmp_path / "portugal_ine.parquet"
    pd.DataFrame(
        [
            # Lisbon: matched GHSL 231 observed new-lease median rent -> first_order rent
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:231",
                "ghsl_match_flag": True,
                "municipality_name": "Lisboa",
                "period": "2023Q4",
                "year": 2023,
                "median_rent_eur_per_m2": 12.4,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:231",
                "ghsl_match_flag": True,
                "municipality_name": "Lisboa",
                "period": "2023Q3",
                "year": 2023,
                "median_rent_eur_per_m2": 12.1,
            },
            # unmatched municipality must be ignored
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "municipality_name": "Evora",
                "period": "2023Q4",
                "year": 2023,
                "median_rent_eur_per_m2": 6.0,
            },
        ]
    ).to_parquet(portugal_ine, index=False)

    italy_omi = tmp_path / "italy_omi.parquet"
    pd.DataFrame(
        [
            # Rome: matched assessor quotation rent band -> first_order rent
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8121",
                "ghsl_match_flag": True,
                "comune_istat_code": "12058091",
                "semester_label": "2018-S2",
                "year": 2018,
                "rent_mid_eur_m2_month": 14.5,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8121",
                "ghsl_match_flag": True,
                "comune_istat_code": "12058091",
                "semester_label": "2018-S1",
                "year": 2018,
                "rent_mid_eur_m2_month": 14.2,
            },
            # unmatched comune ignored
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "comune_istat_code": "12999999",
                "semester_label": "2018-S2",
                "year": 2018,
                "rent_mid_eur_m2_month": 5.0,
            },
        ]
    ).to_parquet(italy_omi, index=False)

    spain_reference = tmp_path / "spain_reference.parquet"
    pd.DataFrame(
        [
            # Madrid: matched official reference index (legal cap basis) -> rent-board layer
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3338",
                "ghsl_match_flag": True,
                "municipality_code": "28079",
                "year": 2024,
                "ref_rent_per_m2_eur_median": 13.97,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3338",
                "ghsl_match_flag": True,
                "municipality_code": "28079",
                "year": 2023,
                "ref_rent_per_m2_eur_median": 13.10,
            },
            # unmatched municipality ignored
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "municipality_code": "09999",
                "year": 2024,
                "ref_rent_per_m2_eur_median": 6.0,
            },
        ]
    ).to_parquet(spain_reference, index=False)

    france_oll = tmp_path / "france_oll.parquet"
    pd.DataFrame(
        [
            # Lyon: matched observed OLL market rent -> first_order rent
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2879",
                "ghsl_match_flag": True,
                "agglomeration": "Lyon",
                "data_year": 2024,
                "rent_eur_m2_median": 12.8,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2879",
                "ghsl_match_flag": True,
                "agglomeration": "Lyon",
                "data_year": 2023,
                "rent_eur_m2_median": 12.4,
            },
            # unmatched agglomeration ignored
            {
                "ieset_city_id": None,
                "ghsl_match_flag": False,
                "agglomeration": "Nice",
                "data_year": 2024,
                "rent_eur_m2_median": 14.0,
            },
        ]
    ).to_parquet(france_oll, index=False)

    berlin_mietspiegel = tmp_path / "berlin_mietspiegel.parquet"
    pd.DataFrame(
        [
            # Berlin: qualified rent index (legal reference) -> rent-board layer only
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5483",
                "ghsl_match_flag": True,
                "edition_year": 2026,
                "net_cold_rent_mean_eur_m2": 9.4,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5483",
                "ghsl_match_flag": True,
                "edition_year": 2026,
                "net_cold_rent_mean_eur_m2": 12.1,
            },
        ]
    ).to_parquet(berlin_mietspiegel, index=False)

    inputs = {
        "city_spine": spine,
        "zillow_rent": zillow,
        "census_permits": permits,
        "nyc_quality": nyc_quality,
        "datasf_quality": sf_quality,
        "nyc_regulation_proxy": nyc_reg,
        "acs_incidence": tmp_path / "missing_acs.parquet",
        "catalonia_rent_contracts": catalonia_rent_contracts,
        "france_reference_rents": france_reference,
        "uk_private_rents": uk_private_rents,
        "uk_house_building": uk_house_building,
        "colombia_dane_ipc_city_rent": colombia_dane_ipc,
        "singapore_hdb_median_rent": singapore_hdb,
        "singapore_hdb_ura_rentals": singapore_hdb_ura,
        "hong_kong_rvd_private_domestic": hong_kong_rvd,
        "stockholm_bostadsformedlingen_queue": stockholm_queue,
        "sweden_scb_municipal_housing": sweden_scb,
        "dubai_data_housing": dubai_data,
        "taiwan_moi_rental_transactions": taiwan_moi,
        "eurostat_city_urban_audit": eurostat_urban_audit,
        "australia_rental_bond": australia_rental_bond,
        "nz_tenancy_rental_bond": nz_rental_bond,
        "ireland_rtb_rent_index": ireland_rtb,
        "portugal_ine_municipal_rents": portugal_ine,
        "italy_omi_rent": italy_omi,
        "spain_rental_reference_index": spain_reference,
        "france_oll_rent": france_oll,
        "berlin_mietspiegel": berlin_mietspiegel,
    }
    matrix, stats = readiness_builder.build_matrix(inputs)

    nyc = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:8099")].iloc[0]
    assert nyc["rent_control_readiness_tier"] == "case_ready_local_panel"
    assert nyc["rent_control_core_layer_count"] == 4
    assert nyc["supply_response_layer"]
    assert nyc["regulated_stock_or_rent_board_layer"]

    sf = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1461")].iloc[0]
    assert sf["rent_control_readiness_tier"] == "case_ready_local_panel"
    assert sf["census_permit_total_units"] == 100

    london = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:5816")].iloc[0]
    assert london["uk_private_rent_rows"] == 1
    assert london["uk_house_building_rows"] == 1
    assert london["first_order_rent_layer"]
    assert london["supply_response_layer"]
    assert london["rent_control_readiness_tier"] == "rent_supply_ready"

    paris = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:2878")].iloc[0]
    assert paris["france_reference_rent_rows"] == 1
    assert not paris["first_order_rent_layer"]
    assert paris["regulated_stock_or_rent_board_layer"]
    assert paris["rent_control_readiness_tier"] == "partial_local_outcome"

    barcelona = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:5071")].iloc[0]
    assert barcelona["catalonia_rent_contract_rows"] == 1
    assert barcelona["catalonia_rent_contract_years"] == 1
    assert barcelona["catalonia_rent_contract_total_contracts"] == 1000
    assert barcelona["first_order_rent_layer"]
    assert barcelona["rent_control_readiness_tier"] == "rent_only"

    bogota = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:3881")].iloc[0]
    assert bogota["colombia_dane_ipc_rent_rows"] == 1
    assert bogota["colombia_dane_ipc_rent_months"] == 1
    assert bogota["first_order_rent_layer"]
    assert bogota["rent_control_readiness_tier"] == "rent_only"

    singapore = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:178")].iloc[0]
    assert singapore["singapore_hdb_median_rent_rows"] == 1
    assert singapore["singapore_hdb_median_rent_quarters"] == 1
    assert singapore["singapore_hdb_ura_rental_rows"] == 1
    assert singapore["singapore_ura_private_rent_projects"] == 1
    assert singapore["singapore_ura_private_rental_contracts"] == 28
    assert singapore["first_order_rent_layer"]
    assert singapore["rent_control_readiness_tier"] == "rent_only"

    sembawang = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:345")].iloc[0]
    assert sembawang["singapore_hdb_ura_rental_rows"] == 1
    assert sembawang["singapore_hdb_approval_rows"] == 1
    assert sembawang["singapore_hdb_approval_towns"] == 1
    assert sembawang["first_order_rent_layer"]
    assert sembawang["rent_control_readiness_tier"] == "rent_only"

    hong_kong = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:11185")].iloc[0]
    assert hong_kong["hong_kong_rvd_rental_index_rows"] == 1
    assert hong_kong["hong_kong_rvd_supply_rows"] == 2
    assert hong_kong["first_order_rent_layer"]
    assert hong_kong["supply_response_layer"]
    assert hong_kong["rent_control_readiness_tier"] == "rent_supply_ready"

    stockholm = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1693")].iloc[0]
    assert stockholm["stockholm_queue_rent_band_rows"] == 1
    assert stockholm["stockholm_queue_time_band_rows"] == 1
    assert stockholm["stockholm_queue_allocated_dwellings"] == 1455
    assert stockholm["sweden_scb_rent_rows"] == 1
    assert stockholm["sweden_scb_completion_rows"] == 1
    assert stockholm["sweden_scb_stock_rows"] == 1
    assert stockholm["sweden_scb_completed_new_dwellings"] == 1200
    assert stockholm["first_order_rent_layer"]
    assert stockholm["supply_response_layer"]
    assert stockholm["regulated_stock_or_rent_board_layer"]
    assert stockholm["rent_control_core_layer_count"] == 3
    assert stockholm["rent_control_readiness_tier"] == "rent_supply_ready"

    dubai = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1007")].iloc[0]
    assert dubai["dubai_rent_index_rows"] == 1
    assert dubai["dubai_rent_index_segments"] == 1
    assert dubai["dubai_housing_supply_rows"] == 2
    assert dubai["dubai_building_permit_rows"] == 1
    assert dubai["dubai_completed_building_rows"] == 1
    assert dubai["first_order_rent_layer"]
    assert dubai["supply_response_layer"]
    assert dubai["rent_control_readiness_tier"] == "rent_supply_ready"

    taipei = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1142")].iloc[0]
    assert taipei["taiwan_moi_rental_rows"] == 1
    assert taipei["taiwan_moi_rental_months"] == 1
    assert taipei["taiwan_moi_rental_municipalities"] == 1
    assert taipei["taiwan_moi_rental_total_rent_ntd"] == 9300
    assert taipei["first_order_rent_layer"]
    assert taipei["rent_control_readiness_tier"] == "rent_only"

    sydney = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:2324")].iloc[0]
    assert sydney["australia_rental_bond_rows"] == 1
    assert sydney["australia_rental_bond_total_lodgements"] == 5712
    assert sydney["first_order_rent_layer"]
    assert not sydney["supply_response_layer"]
    assert sydney["rent_control_readiness_tier"] == "rent_only"

    auckland = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1147")].iloc[0]
    assert auckland["nz_rental_bond_rows"] == 1
    assert auckland["nz_rental_bond_total_lodgements"] == 4200
    assert auckland["first_order_rent_layer"]
    assert not auckland["supply_response_layer"]
    assert auckland["rent_control_readiness_tier"] == "rent_only"

    # Eurostat city carrying observed rent per m2 (SA1049V) + dwelling stock
    sofia = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:109")].iloc[0]
    assert sofia["eurostat_urban_audit_rows"] == 2
    assert sofia["eurostat_rent_per_m2_rows"] == 1
    assert sofia["eurostat_dwelling_stock_rows"] == 1
    assert sofia["first_order_rent_layer"]
    assert sofia["supply_response_layer"]
    assert sofia["rent_control_readiness_tier"] == "rent_supply_ready"

    # Eurostat city with dwelling stock + tenure + price proxy but NO observed rent
    zurich = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1689")].iloc[0]
    assert zurich["eurostat_dwelling_stock_rows"] == 1
    assert zurich["eurostat_tenure_rows"] == 1
    assert zurich["eurostat_price_proxy_rows"] == 1
    assert zurich["eurostat_rent_per_m2_rows"] == 0
    assert not zurich["first_order_rent_layer"]
    assert zurich["supply_response_layer"]
    assert zurich["rent_control_readiness_tier"] == "partial_local_outcome"

    # Dublin: matched RTB observed standardised rent -> first_order rent only
    dublin = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:394")].iloc[0]
    assert dublin["ireland_rtb_rent_rows"] == 2  # only the 2 matched Dublin rows
    assert dublin["ireland_rtb_rent_years"] == 2
    assert dublin["ireland_rtb_rent_locations"] == 1
    assert dublin["first_order_rent_layer"]
    assert not dublin["supply_response_layer"]
    assert dublin["rent_control_readiness_tier"] == "rent_only"

    # Lisbon: matched INE observed new-lease median rent -> first_order rent only
    lisbon = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:231")].iloc[0]
    assert lisbon["portugal_ine_rent_rows"] == 2  # only the 2 matched Lisboa rows
    assert lisbon["portugal_ine_rent_municipalities"] == 1
    assert lisbon["first_order_rent_layer"]
    assert not lisbon["supply_response_layer"]
    assert lisbon["rent_control_readiness_tier"] == "rent_only"

    # Rome: matched OMI assessor quotation rent band -> first_order rent only
    rome = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:8121")].iloc[0]
    assert rome["italy_omi_rent_rows"] == 2  # only matched Rome rows
    assert rome["first_order_rent_layer"]
    assert rome["rent_control_readiness_tier"] == "rent_only"

    # Madrid: matched SERPAVI reference index (legal cap basis) -> rent-board layer only
    madrid = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:3338")].iloc[0]
    assert madrid["spain_reference_index_rows"] == 2
    assert not madrid["first_order_rent_layer"]
    assert madrid["regulated_stock_or_rent_board_layer"]
    assert madrid["rent_control_readiness_tier"] == "partial_local_outcome"

    # Lyon: matched OLL observed market rent -> first_order rent only
    lyon = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:2879")].iloc[0]
    assert lyon["france_oll_rent_rows"] == 2
    assert lyon["first_order_rent_layer"]
    assert lyon["rent_control_readiness_tier"] == "rent_only"

    # Berlin: Mietspiegel qualified rent index (legal reference) -> rent-board layer only
    berlin = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:5483")].iloc[0]
    assert berlin["berlin_mietspiegel_rows"] == 2
    assert not berlin["first_order_rent_layer"]
    assert berlin["regulated_stock_or_rent_board_layer"]
    assert berlin["rent_control_readiness_tier"] == "partial_local_outcome"

    assert stats["tier_counts"]["case_ready_local_panel"] == 2
    assert stats["tier_counts"]["rent_supply_ready"] == 5
    assert stats["tier_counts"]["rent_only"] == 11
    assert stats["tier_counts"]["partial_local_outcome"] == 4
    assert stats["layer_counts"]["first_order_rent_layer"] == 18
    assert stats["layer_counts"]["supply_response_layer"] == 8
    assert stats["layer_counts"]["regulated_stock_or_rent_board_layer"] == 6
    assert stats["missing_optional_inputs"] == ["acs_incidence"]

    output = tmp_path / "readiness.parquet"
    artifacts = readiness_builder.write_outputs(
        matrix,
        stats,
        output,
        tmp_path / "manifests",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
        tmp_path / "summary.json",
        tmp_path / "summary.md",
    )
    assert output.exists()
    assert output.with_suffix(".csv").exists()
    assert output.with_suffix(".json").exists()
    manifest = yaml.safe_load(Path(artifacts["manifest_path"]).read_text())
    assert manifest["entries"][0]["series_id"] == "city_policy_test_readiness_matrix"
