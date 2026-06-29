#!/usr/bin/env python3
"""Build top-1000 city readiness matrix from landed city-level panels."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


DEFAULT_INPUTS = {
    "city_spine": "data/derived/city_universe_top1000.parquet",
    "zillow_rent": "data/derived/us_city_rent_panel.parquet",
    "census_permits": "data/derived/us_city_permits_panel.parquet",
    "nyc_quality": "data/derived/us_city_rent_control_quality_leakage_panel.parquet",
    "datasf_quality": "data/derived/us_sf_rent_control_quality_leakage_panel.parquet",
    "nyc_regulation_proxy": "data/derived/nyc_rent_regulation_tax_benefit_panel.parquet",
    "acs_incidence": "data/derived/us_acs_place_housing_incidence_panel.parquet",
    "catalonia_rent_contracts": "data/derived/catalonia_rent_contracts_panel.parquet",
    "france_reference_rents": "data/derived/france_reference_rents_panel.parquet",
    "uk_private_rents": "data/derived/uk_ons_voa_private_rents_panel.parquet",
    "uk_house_building": "data/derived/uk_mhclg_house_building_panel.parquet",
    "colombia_dane_ipc_city_rent": "data/derived/colombia_dane_ipc_city_rent_panel.parquet",
    "singapore_hdb_median_rent": "data/derived/singapore_hdb_median_rent_panel.parquet",
    "singapore_hdb_ura_rentals": "data/derived/singapore_hdb_ura_rental_panel.parquet",
    "hong_kong_rvd_private_domestic": "data/derived/hong_kong_rvd_private_domestic_panel.parquet",
    "stockholm_bostadsformedlingen_queue": "data/derived/stockholm_bostadsformedlingen_queue_panel.parquet",
    "sweden_scb_municipal_housing": "data/derived/sweden_scb_municipal_housing_panel.parquet",
    "dubai_data_housing": "data/derived/dubai_data_housing_panel.parquet",
    "taiwan_moi_rental_transactions": "data/derived/taiwan_moi_rental_transactions_panel.parquet",
    "eurostat_city_urban_audit": "data/derived/eurostat_city_urban_audit_panel.parquet",
    "australia_rental_bond": "data/derived/australia_rental_bond_panel.parquet",
    "nz_tenancy_rental_bond": "data/derived/nz_tenancy_rental_bond_panel.parquet",
}


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fetch_utc(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"unsupported input format: {path}")


def ensure_city_id(frame: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if "ieset_city_id" not in frame.columns:
        raise ValueError(f"{source_name} is missing ieset_city_id")
    return frame[frame["ieset_city_id"].notna()].copy()


def merge_agg(base: pd.DataFrame, agg: pd.DataFrame, fill_values: dict[str, Any]) -> pd.DataFrame:
    base = base.drop(columns=[column for column in fill_values if column in base.columns])
    out = base.merge(agg, on="ieset_city_id", how="left")
    for column, value in fill_values.items():
        if column in out.columns:
            if value is not None:
                out[column] = out[column].fillna(value)
    return out


def add_zillow(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "zori_rows": 0,
        "zori_regions": 0,
        "zori_months": 0,
        "zori_start_month": None,
        "zori_end_month": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "zillow_rent")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            zori_rows=("zori_usd", "size"),
            zori_regions=("zillow_region_id", "nunique"),
            zori_months=("month_end", "nunique"),
            zori_start_month=("month_end", "min"),
            zori_end_month=("month_end", "max"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_permits(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "census_permit_rows": 0,
        "census_permit_years": 0,
        "census_permit_start_year": None,
        "census_permit_end_year": None,
        "census_permit_total_units": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "census_permits")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            census_permit_rows=("year", "size"),
            census_permit_years=("year", "nunique"),
            census_permit_start_year=("year", "min"),
            census_permit_end_year=("year", "max"),
            census_permit_total_units=("total_units", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_local_quality(base: pd.DataFrame, frame: pd.DataFrame | None, prefix: str, supply_key: str | None) -> pd.DataFrame:
    columns = {
        f"{prefix}_rows": 0,
        f"{prefix}_datasets": 0,
        f"{prefix}_start_year": None,
        f"{prefix}_end_year": None,
        f"{prefix}_value_sum": 0,
        f"{prefix}_supply_rows": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, prefix)
    supply = frame["source_dataset_key"].eq(supply_key) if supply_key else pd.Series(False, index=frame.index)
    frame = frame.assign(_supply_row=supply.astype(int))
    value_col = "value" if "value" in frame.columns else "value_count"
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            **{
                f"{prefix}_rows": ("year", "size"),
                f"{prefix}_datasets": ("source_dataset_key", "nunique"),
                f"{prefix}_start_year": ("year", "min"),
                f"{prefix}_end_year": ("year", "max"),
                f"{prefix}_value_sum": (value_col, "sum"),
                f"{prefix}_supply_rows": ("_supply_row", "sum"),
            }
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_nyc_regulation(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "nyc_regulation_proxy_rows": 0,
        "nyc_regulation_proxy_families": 0,
        "nyc_regulation_proxy_start_year": None,
        "nyc_regulation_proxy_end_year": None,
        "nyc_regulation_proxy_value_count": 0,
        "nyc_regulation_proxy_units": 0,
        "nyc_regulation_proxy_restricted_units": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "nyc_regulation_proxy")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            nyc_regulation_proxy_rows=("year", "size"),
            nyc_regulation_proxy_families=("benefit_family", "nunique"),
            nyc_regulation_proxy_start_year=("year", "min"),
            nyc_regulation_proxy_end_year=("year", "max"),
            nyc_regulation_proxy_value_count=("value_count", "sum"),
            nyc_regulation_proxy_units=("unit_count", "sum"),
            nyc_regulation_proxy_restricted_units=("restricted_unit_count", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_acs(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "acs_incidence_rows": 0,
        "acs_incidence_years": 0,
        "acs_incidence_start_year": None,
        "acs_incidence_end_year": None,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "acs_incidence")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            acs_incidence_rows=("acs_year", "size"),
            acs_incidence_years=("acs_year", "nunique"),
            acs_incidence_start_year=("acs_year", "min"),
            acs_incidence_end_year=("acs_year", "max"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_catalonia_rent_contracts(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "catalonia_rent_contract_rows": 0,
        "catalonia_rent_contract_years": 0,
        "catalonia_rent_contract_start_year": None,
        "catalonia_rent_contract_end_year": None,
        "catalonia_rent_contract_municipalities": 0,
        "catalonia_rent_contract_total_contracts": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "catalonia_rent_contracts")
    frame = frame.assign(_contracts=frame["contracts"].fillna(0))
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            catalonia_rent_contract_rows=("avg_monthly_rent_eur", "size"),
            catalonia_rent_contract_years=("year", "nunique"),
            catalonia_rent_contract_start_year=("year", "min"),
            catalonia_rent_contract_end_year=("year", "max"),
            catalonia_rent_contract_municipalities=("municipality_code", "nunique"),
            catalonia_rent_contract_total_contracts=("_contracts", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_france_reference_rents(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "france_reference_rent_rows": 0,
        "france_reference_rent_years": 0,
        "france_reference_rent_start_year": None,
        "france_reference_rent_end_year": None,
        "france_reference_rent_zones": 0,
        "france_reference_rent_cells": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "france_reference_rents")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            france_reference_rent_rows=("year", "size"),
            france_reference_rent_years=("year", "nunique"),
            france_reference_rent_start_year=("year", "min"),
            france_reference_rent_end_year=("year", "max"),
            france_reference_rent_zones=("zone_id", "nunique"),
            france_reference_rent_cells=("reference_rent_eur_m2", "size"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_uk_private_rents(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "uk_private_rent_rows": 0,
        "uk_private_rent_years": 0,
        "uk_private_rent_start_year": None,
        "uk_private_rent_end_year": None,
        "uk_private_rent_local_authorities": 0,
        "uk_private_rent_bedroom_categories": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "uk_private_rents")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            uk_private_rent_rows=("period_end_year", "size"),
            uk_private_rent_years=("period_end_year", "nunique"),
            uk_private_rent_start_year=("period_end_year", "min"),
            uk_private_rent_end_year=("period_end_year", "max"),
            uk_private_rent_local_authorities=("local_authority_code", "nunique"),
            uk_private_rent_bedroom_categories=("bedroom_category", "nunique"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_uk_house_building(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "uk_house_building_rows": 0,
        "uk_house_building_years": 0,
        "uk_house_building_start_year": None,
        "uk_house_building_end_year": None,
        "uk_house_building_local_authorities": 0,
        "uk_house_building_total_starts": 0,
        "uk_house_building_total_completions": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "uk_house_building")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            uk_house_building_rows=("fiscal_year_start", "size"),
            uk_house_building_years=("fiscal_year", "nunique"),
            uk_house_building_start_year=("fiscal_year_start", "min"),
            uk_house_building_end_year=("fiscal_year_end", "max"),
            uk_house_building_local_authorities=("local_authority_code", "nunique"),
            uk_house_building_total_starts=("all_starts", "sum"),
            uk_house_building_total_completions=("all_completions", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_colombia_dane_ipc_city_rent(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "colombia_dane_ipc_rent_rows": 0,
        "colombia_dane_ipc_rent_months": 0,
        "colombia_dane_ipc_rent_start_period": None,
        "colombia_dane_ipc_rent_end_period": None,
        "colombia_dane_ipc_rent_items": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "colombia_dane_ipc_city_rent")
    item_col = "item_name_norm" if "item_name_norm" in frame.columns else "item_name"
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            colombia_dane_ipc_rent_rows=("index_value", "size"),
            colombia_dane_ipc_rent_months=("period", "nunique"),
            colombia_dane_ipc_rent_start_period=("period", "min"),
            colombia_dane_ipc_rent_end_period=("period", "max"),
            colombia_dane_ipc_rent_items=(item_col, "nunique"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_singapore_hdb_median_rent(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "singapore_hdb_median_rent_rows": 0,
        "singapore_hdb_median_rent_quarters": 0,
        "singapore_hdb_median_rent_start_quarter": None,
        "singapore_hdb_median_rent_end_quarter": None,
        "singapore_hdb_median_rent_towns": 0,
        "singapore_hdb_median_rent_flat_types": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "singapore_hdb_median_rent")
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            singapore_hdb_median_rent_rows=("median_monthly_rent_sgd", "size"),
            singapore_hdb_median_rent_quarters=("quarter", "nunique"),
            singapore_hdb_median_rent_start_quarter=("quarter", "min"),
            singapore_hdb_median_rent_end_quarter=("quarter", "max"),
            singapore_hdb_median_rent_towns=("town_norm", "nunique"),
            singapore_hdb_median_rent_flat_types=("flat_type", "nunique"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_singapore_hdb_ura_rentals(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "singapore_hdb_ura_rental_rows": 0,
        "singapore_hdb_ura_rental_periods": 0,
        "singapore_hdb_ura_rental_start_date": None,
        "singapore_hdb_ura_rental_end_date": None,
        "singapore_hdb_approval_rows": 0,
        "singapore_hdb_approval_towns": 0,
        "singapore_hdb_approval_flat_types": 0,
        "singapore_ura_private_rent_rows": 0,
        "singapore_ura_private_rent_projects": 0,
        "singapore_ura_private_rent_postal_districts": 0,
        "singapore_ura_private_rental_contracts": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "singapore_hdb_ura_rentals")
    hdb_rows = frame["source_dataset_key"].eq("hdb_approval")
    ura_rows = frame["source_dataset_key"].eq("ura_private_non_landed")
    frame = frame.assign(_hdb_row=hdb_rows.astype(int), _ura_row=ura_rows.astype(int))
    frame["_hdb_town"] = frame["town_norm"].where(hdb_rows)
    frame["_hdb_flat_type"] = frame["flat_type"].where(hdb_rows)
    frame["_ura_project"] = frame["project_name_norm"].where(ura_rows)
    frame["_ura_postal_district"] = frame["postal_district"].where(ura_rows)
    frame["_ura_contracts"] = frame["rental_contracts"].where(ura_rows).fillna(0)
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            singapore_hdb_ura_rental_rows=("period", "size"),
            singapore_hdb_ura_rental_periods=("period", "nunique"),
            singapore_hdb_ura_rental_start_date=("period_start", "min"),
            singapore_hdb_ura_rental_end_date=("period_end", "max"),
            singapore_hdb_approval_rows=("_hdb_row", "sum"),
            singapore_hdb_approval_towns=("_hdb_town", "nunique"),
            singapore_hdb_approval_flat_types=("_hdb_flat_type", "nunique"),
            singapore_ura_private_rent_rows=("_ura_row", "sum"),
            singapore_ura_private_rent_projects=("_ura_project", "nunique"),
            singapore_ura_private_rent_postal_districts=("_ura_postal_district", "nunique"),
            singapore_ura_private_rental_contracts=("_ura_contracts", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_hong_kong_rvd_private_domestic(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "hong_kong_rvd_rows": 0,
        "hong_kong_rvd_years": 0,
        "hong_kong_rvd_start_year": None,
        "hong_kong_rvd_end_year": None,
        "hong_kong_rvd_rental_index_rows": 0,
        "hong_kong_rvd_supply_rows": 0,
        "hong_kong_rvd_measures": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "hong_kong_rvd_private_domestic")
    rent_rows = frame["measure"].eq("rental_index")
    supply_rows = frame["measure"].isin(["completions", "stock", "take_up", "vacancy_units", "vacancy_rate"])
    frame = frame.assign(_rental_index_row=rent_rows.astype(int), _supply_row=supply_rows.astype(int))
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            hong_kong_rvd_rows=("year", "size"),
            hong_kong_rvd_years=("year", "nunique"),
            hong_kong_rvd_start_year=("year", "min"),
            hong_kong_rvd_end_year=("year", "max"),
            hong_kong_rvd_rental_index_rows=("_rental_index_row", "sum"),
            hong_kong_rvd_supply_rows=("_supply_row", "sum"),
            hong_kong_rvd_measures=("measure", "nunique"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_stockholm_bostadsformedlingen_queue(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "stockholm_queue_rows": 0,
        "stockholm_queue_years": 0,
        "stockholm_queue_start_year": None,
        "stockholm_queue_end_year": None,
        "stockholm_queue_queues": 0,
        "stockholm_queue_rent_band_rows": 0,
        "stockholm_queue_time_band_rows": 0,
        "stockholm_queue_allocated_dwellings": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "stockholm_bostadsformedlingen_queue")
    positive = frame["allocated_dwellings"].fillna(0).gt(0)
    rent_rows = frame["measure"].eq("rent_band_count") & positive
    queue_time_rows = frame["measure"].eq("queue_time_band_count") & positive
    frame = frame.assign(
        _rent_band_row=rent_rows.astype(int),
        _queue_time_band_row=queue_time_rows.astype(int),
        _rent_allocations=frame["allocated_dwellings"].where(rent_rows).fillna(0),
    )
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            stockholm_queue_rows=("year", "size"),
            stockholm_queue_years=("year", "nunique"),
            stockholm_queue_start_year=("year", "min"),
            stockholm_queue_end_year=("year", "max"),
            stockholm_queue_queues=("queue_name", "nunique"),
            stockholm_queue_rent_band_rows=("_rent_band_row", "sum"),
            stockholm_queue_time_band_rows=("_queue_time_band_row", "sum"),
            stockholm_queue_allocated_dwellings=("_rent_allocations", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_sweden_scb_municipal_housing(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "sweden_scb_rows": 0,
        "sweden_scb_years": 0,
        "sweden_scb_start_year": None,
        "sweden_scb_end_year": None,
        "sweden_scb_rent_rows": 0,
        "sweden_scb_completion_rows": 0,
        "sweden_scb_stock_rows": 0,
        "sweden_scb_completed_new_dwellings": 0,
        "sweden_scb_dwelling_stock_observations": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "sweden_scb_municipal_housing")
    rent_rows = frame["measure"].eq("municipal_rent_per_sqm")
    completion_rows = frame["measure"].eq("completed_new_dwellings")
    stock_rows = frame["measure"].eq("dwelling_stock")
    frame = frame.assign(
        _rent_row=rent_rows.astype(int),
        _completion_row=completion_rows.astype(int),
        _stock_row=stock_rows.astype(int),
        _completed_new_dwellings=frame["value"].where(completion_rows).fillna(0),
        _dwelling_stock_observation=frame["value"].where(stock_rows).fillna(0),
    )
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            sweden_scb_rows=("year", "size"),
            sweden_scb_years=("year", "nunique"),
            sweden_scb_start_year=("year", "min"),
            sweden_scb_end_year=("year", "max"),
            sweden_scb_rent_rows=("_rent_row", "sum"),
            sweden_scb_completion_rows=("_completion_row", "sum"),
            sweden_scb_stock_rows=("_stock_row", "sum"),
            sweden_scb_completed_new_dwellings=("_completed_new_dwellings", "sum"),
            sweden_scb_dwelling_stock_observations=("_dwelling_stock_observation", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_dubai_data_housing(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "dubai_data_rows": 0,
        "dubai_data_periods": 0,
        "dubai_data_start_period": None,
        "dubai_data_end_period": None,
        "dubai_rent_index_rows": 0,
        "dubai_rent_index_segments": 0,
        "dubai_housing_supply_rows": 0,
        "dubai_building_permit_rows": 0,
        "dubai_completed_building_rows": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "dubai_data_housing")
    rent_rows = frame["source_dataset_key"].eq("residential_rent_price_index")
    supply_relevant = frame["housing_supply_relevant"].fillna(False).astype(bool)
    permit_rows = frame["source_dataset_key"].eq("building_permits") & supply_relevant
    completed_rows = frame["source_dataset_key"].eq("completed_buildings") & supply_relevant
    frame = frame.assign(
        _rent_row=rent_rows.astype(int),
        _rent_segment=frame["segment_norm"].where(rent_rows),
        _supply_row=(permit_rows | completed_rows).astype(int),
        _permit_row=permit_rows.astype(int),
        _completed_row=completed_rows.astype(int),
    )
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            dubai_data_rows=("period", "size"),
            dubai_data_periods=("period", "nunique"),
            dubai_data_start_period=("period", "min"),
            dubai_data_end_period=("period", "max"),
            dubai_rent_index_rows=("_rent_row", "sum"),
            dubai_rent_index_segments=("_rent_segment", "nunique"),
            dubai_housing_supply_rows=("_supply_row", "sum"),
            dubai_building_permit_rows=("_permit_row", "sum"),
            dubai_completed_building_rows=("_completed_row", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_taiwan_moi_rental_transactions(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "taiwan_moi_rental_rows": 0,
        "taiwan_moi_rental_months": 0,
        "taiwan_moi_rental_start_period": None,
        "taiwan_moi_rental_end_period": None,
        "taiwan_moi_rental_municipalities": 0,
        "taiwan_moi_rental_total_rent_ntd": 0,
    }
    if frame is None:
        return base.assign(**columns)
    frame = ensure_city_id(frame, "taiwan_moi_rental_transactions")
    municipality_col = "municipality_name_en" if "municipality_name_en" in frame.columns else "municipality_code"
    frame = frame.assign(_total_rent_ntd=frame["total_rent_ntd"].fillna(0))
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            taiwan_moi_rental_rows=("period", "size"),
            taiwan_moi_rental_months=("period", "nunique"),
            taiwan_moi_rental_start_period=("period", "min"),
            taiwan_moi_rental_end_period=("period", "max"),
            taiwan_moi_rental_municipalities=(municipality_col, "nunique"),
            taiwan_moi_rental_total_rent_ntd=("_total_rent_ntd", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_eurostat_city_urban_audit(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "eurostat_urban_audit_rows": 0,
        "eurostat_urban_audit_years": 0,
        "eurostat_urban_audit_start_year": None,
        "eurostat_urban_audit_end_year": None,
        "eurostat_urban_audit_indicators": 0,
        # SA1049V: average annual rent per m2 (observed transaction rent)
        "eurostat_rent_per_m2_rows": 0,
        # SA1001V / SA1025V: dwelling stock + empty dwellings (supply/covariate)
        "eurostat_dwelling_stock_rows": 0,
        # SA1011V / SA1012V / SA1013V: owner / social / private-rented tenure (covariate)
        "eurostat_tenure_rows": 0,
        # SA1050V / SA1051V: house/apartment purchase prices (price proxy, NOT observed rent)
        "eurostat_price_proxy_rows": 0,
    }
    if frame is None:
        return base.assign(**columns)
    if "ghsl_match_flag" in frame.columns:
        frame = frame[frame["ghsl_match_flag"].fillna(False).astype(bool)].copy()
    frame = ensure_city_id(frame, "eurostat_city_urban_audit")
    if frame.empty:
        return base.assign(**columns)
    rent_rows = frame["indicator"].eq("SA1049V")
    dwelling_rows = frame["indicator"].isin(["SA1001V", "SA1025V"])
    tenure_rows = frame["indicator"].isin(["SA1011V", "SA1012V", "SA1013V"])
    price_rows = frame["indicator"].isin(["SA1050V", "SA1051V"])
    frame = frame.assign(
        _rent_row=rent_rows.astype(int),
        _dwelling_row=dwelling_rows.astype(int),
        _tenure_row=tenure_rows.astype(int),
        _price_row=price_rows.astype(int),
    )
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            eurostat_urban_audit_rows=("year", "size"),
            eurostat_urban_audit_years=("year", "nunique"),
            eurostat_urban_audit_start_year=("year", "min"),
            eurostat_urban_audit_end_year=("year", "max"),
            eurostat_urban_audit_indicators=("indicator", "nunique"),
            eurostat_rent_per_m2_rows=("_rent_row", "sum"),
            eurostat_dwelling_stock_rows=("_dwelling_row", "sum"),
            eurostat_tenure_rows=("_tenure_row", "sum"),
            eurostat_price_proxy_rows=("_price_row", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_australia_rental_bond(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "australia_rental_bond_rows": 0,
        "australia_rental_bond_months": 0,
        "australia_rental_bond_start_period": None,
        "australia_rental_bond_end_period": None,
        "australia_rental_bond_geographies": 0,
        "australia_rental_bond_dwelling_types": 0,
        "australia_rental_bond_total_lodgements": 0,
    }
    if frame is None:
        return base.assign(**columns)
    if "ghsl_match_flag" in frame.columns:
        frame = frame[frame["ghsl_match_flag"].fillna(False).astype(bool)].copy()
    frame = ensure_city_id(frame, "australia_rental_bond")
    if frame.empty:
        return base.assign(**columns)
    frame = frame.assign(_lodgements=frame["bond_lodgement_count"].fillna(0))
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            australia_rental_bond_rows=("period", "size"),
            australia_rental_bond_months=("period", "nunique"),
            australia_rental_bond_start_period=("period", "min"),
            australia_rental_bond_end_period=("period", "max"),
            australia_rental_bond_geographies=("geography_id", "nunique"),
            australia_rental_bond_dwelling_types=("dwelling_type_label", "nunique"),
            australia_rental_bond_total_lodgements=("_lodgements", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def add_nz_tenancy_rental_bond(base: pd.DataFrame, frame: pd.DataFrame | None) -> pd.DataFrame:
    columns = {
        "nz_rental_bond_rows": 0,
        "nz_rental_bond_months": 0,
        "nz_rental_bond_start_period": None,
        "nz_rental_bond_end_period": None,
        "nz_rental_bond_locations": 0,
        "nz_rental_bond_bedroom_bands": 0,
        "nz_rental_bond_total_lodgements": 0,
    }
    if frame is None:
        return base.assign(**columns)
    if "ghsl_match_flag" in frame.columns:
        frame = frame[frame["ghsl_match_flag"].fillna(False).astype(bool)].copy()
    frame = ensure_city_id(frame, "nz_tenancy_rental_bond")
    if frame.empty:
        return base.assign(**columns)
    frame = frame.assign(_lodgements=frame["lodged_bonds"].fillna(0))
    agg = (
        frame.groupby("ieset_city_id")
        .agg(
            nz_rental_bond_rows=("period", "size"),
            nz_rental_bond_months=("period", "nunique"),
            nz_rental_bond_start_period=("period", "min"),
            nz_rental_bond_end_period=("period", "max"),
            nz_rental_bond_locations=("location", "nunique"),
            nz_rental_bond_bedroom_bands=("bedroom_band", "nunique"),
            nz_rental_bond_total_lodgements=("_lodgements", "sum"),
        )
        .reset_index()
    )
    return merge_agg(base.assign(**{k: v for k, v in columns.items() if k not in base.columns}), agg, columns)


def assign_layers(matrix: pd.DataFrame) -> pd.DataFrame:
    out = matrix.copy()
    out["first_order_rent_layer"] = (
        out["zori_rows"].gt(0)
        | out["catalonia_rent_contract_rows"].gt(0)
        | out["uk_private_rent_rows"].gt(0)
        | out["colombia_dane_ipc_rent_rows"].gt(0)
        | out["singapore_hdb_median_rent_rows"].gt(0)
        | out["singapore_hdb_ura_rental_rows"].gt(0)
        | out["hong_kong_rvd_rental_index_rows"].gt(0)
        | out["stockholm_queue_rent_band_rows"].gt(0)
        | out["sweden_scb_rent_rows"].gt(0)
        | out["dubai_rent_index_rows"].gt(0)
        | out["taiwan_moi_rental_rows"].gt(0)
        | out["eurostat_rent_per_m2_rows"].gt(0)
        | out["australia_rental_bond_rows"].gt(0)
        | out["nz_rental_bond_rows"].gt(0)
    )
    out["supply_response_layer"] = (
        out["census_permit_rows"].gt(0)
        | out["nyc_quality_supply_rows"].gt(0)
        | out["datasf_quality_supply_rows"].gt(0)
        | out["uk_house_building_rows"].gt(0)
        | out["hong_kong_rvd_supply_rows"].gt(0)
        | out["sweden_scb_completion_rows"].gt(0)
        | out["dubai_housing_supply_rows"].gt(0)
        | out["eurostat_dwelling_stock_rows"].gt(0)
    )
    out["quality_or_leakage_layer"] = out["nyc_quality_rows"].gt(0) | out["datasf_quality_rows"].gt(0)
    out["regulated_stock_or_rent_board_layer"] = (
        out["nyc_regulation_proxy_rows"].gt(0)
        | (out["datasf_quality_rows"].gt(0) & out["ieset_city_id"].eq("ghsl_ucdb_r2024a:1461"))
        | out["france_reference_rent_rows"].gt(0)
        | out["stockholm_queue_time_band_rows"].gt(0)
    )
    out["distributional_incidence_layer"] = out["acs_incidence_rows"].gt(0)
    layer_cols = [
        "first_order_rent_layer",
        "supply_response_layer",
        "quality_or_leakage_layer",
        "regulated_stock_or_rent_board_layer",
        "distributional_incidence_layer",
    ]
    out["rent_control_core_layer_count"] = out[layer_cols].sum(axis=1).astype(int)

    def tier(row: pd.Series) -> str:
        if (
            row["first_order_rent_layer"]
            and row["supply_response_layer"]
            and row["quality_or_leakage_layer"]
            and row["regulated_stock_or_rent_board_layer"]
        ):
            return "case_ready_local_panel"
        if row["first_order_rent_layer"] and row["supply_response_layer"] and row["quality_or_leakage_layer"]:
            return "outcomes_ready_needs_regulated_stock"
        if row["first_order_rent_layer"] and row["supply_response_layer"]:
            return "rent_supply_ready"
        if row["first_order_rent_layer"]:
            return "rent_only"
        if row["supply_response_layer"] or row["quality_or_leakage_layer"] or row["regulated_stock_or_rent_board_layer"]:
            return "partial_local_outcome"
        return "spine_only"

    out["rent_control_readiness_tier"] = out.apply(tier, axis=1)
    return out


def build_matrix(inputs: dict[str, Path]) -> tuple[pd.DataFrame, dict[str, Any]]:
    spine_path = inputs["city_spine"]
    if not spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {spine_path}")
    spine = pd.read_parquet(spine_path) if spine_path.suffix == ".parquet" else pd.read_csv(spine_path)
    base_cols = [
        "ieset_city_id",
        "city_rank_2025",
        "city_name",
        "country_name",
        "country_iso3",
        "population_2025",
        "area_km2_2025",
        "density_per_km2_2025",
    ]
    matrix = spine[base_cols].copy()
    matrix = add_zillow(matrix, read_optional(inputs["zillow_rent"]))
    matrix = add_permits(matrix, read_optional(inputs["census_permits"]))
    matrix = add_local_quality(matrix, read_optional(inputs["nyc_quality"]), "nyc_quality", "dob_permit_issuance")
    matrix = add_local_quality(matrix, read_optional(inputs["datasf_quality"]), "datasf_quality", "building_permit")
    matrix = add_nyc_regulation(matrix, read_optional(inputs["nyc_regulation_proxy"]))
    matrix = add_acs(matrix, read_optional(inputs["acs_incidence"]))
    matrix = add_catalonia_rent_contracts(matrix, read_optional(inputs["catalonia_rent_contracts"]))
    matrix = add_france_reference_rents(matrix, read_optional(inputs["france_reference_rents"]))
    matrix = add_uk_private_rents(matrix, read_optional(inputs["uk_private_rents"]))
    matrix = add_uk_house_building(matrix, read_optional(inputs["uk_house_building"]))
    matrix = add_colombia_dane_ipc_city_rent(matrix, read_optional(inputs["colombia_dane_ipc_city_rent"]))
    matrix = add_singapore_hdb_median_rent(matrix, read_optional(inputs["singapore_hdb_median_rent"]))
    matrix = add_singapore_hdb_ura_rentals(matrix, read_optional(inputs["singapore_hdb_ura_rentals"]))
    matrix = add_hong_kong_rvd_private_domestic(matrix, read_optional(inputs["hong_kong_rvd_private_domestic"]))
    matrix = add_stockholm_bostadsformedlingen_queue(matrix, read_optional(inputs["stockholm_bostadsformedlingen_queue"]))
    matrix = add_sweden_scb_municipal_housing(matrix, read_optional(inputs["sweden_scb_municipal_housing"]))
    matrix = add_dubai_data_housing(matrix, read_optional(inputs["dubai_data_housing"]))
    matrix = add_taiwan_moi_rental_transactions(matrix, read_optional(inputs["taiwan_moi_rental_transactions"]))
    matrix = add_eurostat_city_urban_audit(matrix, read_optional(inputs["eurostat_city_urban_audit"]))
    matrix = add_australia_rental_bond(matrix, read_optional(inputs["australia_rental_bond"]))
    matrix = add_nz_tenancy_rental_bond(matrix, read_optional(inputs["nz_tenancy_rental_bond"]))
    matrix = assign_layers(matrix)
    matrix = matrix.sort_values(
        ["rent_control_core_layer_count", "population_2025", "city_rank_2025"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    stats = {
        "city_rows": int(len(matrix)),
        "countries": int(matrix["country_name"].nunique()),
        "tier_counts": {str(k): int(v) for k, v in matrix["rent_control_readiness_tier"].value_counts().to_dict().items()},
        "layer_counts": {
            "first_order_rent_layer": int(matrix["first_order_rent_layer"].sum()),
            "supply_response_layer": int(matrix["supply_response_layer"].sum()),
            "quality_or_leakage_layer": int(matrix["quality_or_leakage_layer"].sum()),
            "regulated_stock_or_rent_board_layer": int(matrix["regulated_stock_or_rent_board_layer"].sum()),
            "distributional_incidence_layer": int(matrix["distributional_incidence_layer"].sum()),
        },
        "ready_city_ids": matrix.loc[
            matrix["rent_control_readiness_tier"].eq("case_ready_local_panel"),
            ["ieset_city_id", "city_name", "country_name"],
        ].to_dict("records"),
        "input_paths": {key: rel(path) for key, path in inputs.items()},
        "missing_optional_inputs": [key for key, path in inputs.items() if key != "city_spine" and not path.exists()],
    }
    return matrix, stats


def write_outputs(
    matrix: pd.DataFrame,
    stats: dict[str, Any],
    output_path: Path,
    manifest_dir: Path,
    fetch_ts: datetime,
    summary_path: Path | None = None,
    summary_md_path: Path | None = None,
) -> dict[str, Path | str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output_path.with_suffix(".csv")
    json_path = output_path.with_suffix(".json")
    summary_path = summary_path or ROOT / "engine" / "city_policy_test_readiness_summary.json"
    summary_md_path = summary_md_path or ROOT / "engine" / "city_policy_test_readiness_summary.md"

    matrix.to_parquet(output_path, engine="pyarrow", index=False)
    matrix.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(matrix.to_dict("records"), indent=2))
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(stats, indent=2))
    summary_md_path.write_text(render_summary_md(stats))

    manifest_dir.mkdir(parents=True, exist_ok=True)
    run_stamp = utc_stamp(fetch_ts)
    manifest_path = manifest_dir / f"fetch_run_{run_stamp}_city_policy_test_readiness.yaml"
    sha = sha256_path(output_path)
    payload = {
        "run_utc": run_stamp,
        "pipeline": "city_policy_test_readiness_matrix",
        "entries": [
            {
                "publisher": "ieset_derived",
                "series_id": "city_policy_test_readiness_matrix",
                "source_url": "derived from landed IESET city-level panels",
                "methodology_url": "data/city_level/README.md",
                "license": "derived metadata; inherit source licenses for underlying panels",
                "fetch_utc": fetch_ts.isoformat(),
                "rows": int(len(matrix)),
                "frequency": "snapshot",
                "units": "city-level readiness flags and coverage counts",
                "currency": None,
                "start_date": None,
                "end_date": None,
                "sha256": sha,
                "parquet_path": rel(output_path),
                "extra": {
                    "artifacts": {
                        "parquet_path": rel(output_path),
                        "csv_path": rel(csv_path),
                        "json_path": rel(json_path),
                        "summary_json_path": rel(summary_path),
                        "summary_md_path": rel(summary_md_path),
                    },
                    "stats": stats,
                    "columns": list(matrix.columns),
                },
            }
        ],
    }
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return {
        "parquet_path": output_path,
        "csv_path": csv_path,
        "json_path": json_path,
        "summary_path": summary_path,
        "summary_md_path": summary_md_path,
        "manifest_path": manifest_path,
        "sha256": sha,
    }


def render_summary_md(stats: dict[str, Any]) -> str:
    lines = [
        "# City Policy Test Readiness Summary",
        "",
        f"- City rows: {stats['city_rows']}",
        f"- Countries: {stats['countries']}",
        f"- Missing optional inputs: {', '.join(stats['missing_optional_inputs']) or 'none'}",
        "",
        "## Tiers",
        "",
    ]
    for tier, count in stats["tier_counts"].items():
        lines.append(f"- `{tier}`: {count}")
    lines.extend(["", "## Layers", ""])
    for layer, count in stats["layer_counts"].items():
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Case-Ready Cities", ""])
    if stats["ready_city_ids"]:
        for row in stats["ready_city_ids"]:
            lines.append(f"- `{row['ieset_city_id']}`: {row['city_name']}, {row['country_name']}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for key, default in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", default=default)
    parser.add_argument("--output", default="data/derived/city_policy_test_readiness_matrix.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inputs = {key: path_arg(getattr(args, key.replace("-", "_"), DEFAULT_INPUTS[key])).resolve() for key in DEFAULT_INPUTS}
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    matrix, stats = build_matrix(inputs)
    artifacts = write_outputs(matrix, stats, path_arg(args.output).resolve(), path_arg(args.manifest_dir).resolve(), fetch_ts)
    print(
        "OK ieset_derived:city_policy_test_readiness_matrix "
        f"rows={len(matrix)} tiers={stats['tier_counts']} layers={stats['layer_counts']}"
    )
    print(f"artifact: {rel(artifacts['parquet_path'])} sha256={artifacts['sha256']}")
    print(f"manifest: {rel(artifacts['manifest_path'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
