"""Local adapter for reproducible IESET-derived policy panels.

These are not independent primary sources. They are versioned joins and
transformations of registered upstream publishers, with construction recipes
and input hashes stored in their fetch manifests. The adapter makes the
``ieset_derived`` namespace resolvable under the normal fetcher contract.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd

from ._base import FetchResult, ROOT, utc_now


DATASETS = {
    "us_state_minimum_wage_treatment_panel": {
        "path": "data/derived/us_state_minimum_wage_treatment_panel.parquet",
        "builder": "scripts/build_us_state_minimum_wage_treatment_panel.py",
    },
    "us_state_labor_outcome_panel": {
        "path": "data/derived/us_state_labor_outcome_panel.parquet",
        "builder": "scripts/build_us_state_labor_outcome_panel.py",
    },
    "us_state_acs_saipe_incidence_panel": {
        "path": "data/derived/us_state_acs_saipe_incidence_panel.parquet",
        "builder": "scripts/build_us_state_acs_saipe_incidence_panel.py",
    },
    "us_state_gov_finances_panel": {
        "path": "data/derived/us_state_gov_finances_panel.parquet",
        "builder": "scripts/build_us_state_gov_finances_panel.py",
    },
    "us_state_housing_supply_price_panel": {
        "path": "data/derived/us_state_housing_supply_price_panel.parquet",
        "builder": "scripts/build_us_state_housing_supply_price_panel.py",
    },
}

COLUMN_TO_DATASET = {
    "binding_premium": "us_state_minimum_wage_treatment_panel",
    "bite_ratio": "us_state_minimum_wage_treatment_panel",
    "increase_event": "us_state_minimum_wage_treatment_panel",
    "employment_population_ratio": "us_state_labor_outcome_panel",
    "median_hourly_wage": "us_state_labor_outcome_panel",
    "p10_hourly_wage": "us_state_labor_outcome_panel",
    "qcew_avg_weekly_wage": "us_state_labor_outcome_panel",
    "qcew_food_service_avg_weekly_wage": "us_state_labor_outcome_panel",
    "qcew_food_service_employment": "us_state_labor_outcome_panel",
    "qcew_food_service_establishments": "us_state_labor_outcome_panel",
    "unemployment_rate": "us_state_labor_outcome_panel",
    "saipe_median_household_income": "us_state_acs_saipe_incidence_panel",
    "saipe_poverty_rate_all_ages": "us_state_acs_saipe_incidence_panel",
    "individual_income_tax": "us_state_gov_finances_panel",
    "sales_gross_receipts_tax": "us_state_gov_finances_panel",
    "total_debt_outstanding": "us_state_gov_finances_panel",
    "total_tax_revenue": "us_state_gov_finances_panel",
    "bps_total_permit_units": "us_state_housing_supply_price_panel",
    "hpi_growth": "us_state_housing_supply_price_panel",
}

COLUMN_BACKING = {
    "binding_premium": "effective_minimum_wage",
    "increase_event": "minimum_wage_increase",
    "hpi_growth": "fhfa_hpi_at_index",
}


class IESETDerivedError(RuntimeError):
    pass


def _year_bounds(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    for column in ("year", "fiscal_year", "period_year"):
        if column not in frame:
            continue
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if not values.empty:
            return str(int(values.min())), str(int(values.max()))
    return None, None


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    dataset_id = COLUMN_TO_DATASET.get(series_id, series_id)
    record = DATASETS.get(dataset_id)
    if record is None:
        known = ", ".join(sorted(set(DATASETS) | set(COLUMN_TO_DATASET)))
        raise IESETDerivedError(
            f"unsupported series_id {series_id!r}; known dataset/column ids: {known}"
        )

    path = ROOT / record["path"]
    if not path.exists():
        raise IESETDerivedError(
            f"missing {path.relative_to(ROOT)}; run {record['builder']}"
        )
    frame = pd.read_parquet(path)
    backing_column = COLUMN_BACKING.get(series_id, series_id)
    if series_id in COLUMN_TO_DATASET and backing_column not in frame.columns:
        raise IESETDerivedError(
            f"backing column {backing_column!r} for {series_id!r} is not "
            f"present in {path.relative_to(ROOT)}"
        )

    start, end = _year_bounds(frame)
    fetch_ts = vintage_utc or utc_now()
    return FetchResult(
        publisher="ieset_derived",
        series_id=series_id,
        source_url=f"derived://{path.relative_to(ROOT)}",
        methodology_url=f"repo://{record['builder']}",
        license="mixed_upstream_terms",
        fetch_utc=fetch_ts,
        rows=len(frame),
        frequency="annual",
        units="mixed; see column metadata and fetch manifest",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        parquet_path=path,
        extra={
            "dataset_id": dataset_id,
            "requested_column": (
                series_id if series_id in COLUMN_TO_DATASET else None
            ),
            "backing_column": (
                backing_column if series_id in COLUMN_TO_DATASET else None
            ),
            "builder": record["builder"],
            "provenance_note": (
                "Derived artifact; consult its fetch manifest for upstream "
                "publisher vintages, hashes, and construction details."
            ),
        },
    )
