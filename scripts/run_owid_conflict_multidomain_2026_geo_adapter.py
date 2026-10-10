#!/usr/bin/env python3
"""Post-lock, pre-estimate national-scope adapter for the OWID conflict vintage.

The original frozen runner rejected duplicate (null ISO3, year) regional rows
before reading any selected outcome. This wrapper filters exactly those 834
non-ISO3 rows, then uses the frozen runner's same validity checks and model.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import pycountry

import run_owid_conflict_multidomain_2026 as frozen

ORIGINAL = "scripts/run_owid_conflict_multidomain_2026.py"
ADAPTER = "scripts/run_owid_conflict_multidomain_2026_geo_adapter.py"
ISO3 = {country.alpha_3 for country in pycountry.countries} | {"XKX"}
original_verify_locks = frozen.verify_locks
original_numeric_values = frozen.numeric_values
EXCLUDED_NUMERIC_ROWS = {
    "life": 374, "mean_school": 374, "expected_school": 374, "gni": 374,
    "patents": 3300, "breadth": 421, "concentration": 177,
    "investment": 3300, "population": 3300,
}


def national_conflict_values(source_root: Path) -> dict[tuple[str, int], int]:
    item = frozen.SOURCE_DICT["conflict"]
    columns = ["country_iso3", "year", *frozen.CONFLICT_COLS]
    frame = pd.read_parquet(source_root / item["path"], columns=columns)
    excluded = frame.loc[~frame.country_iso3.isin(ISO3)]
    expected = {
        None: 309, "OWID_AFR": 79, "OWID_EUR": 79, "OWID_WRL": 79,
        "OWID_ABK": 36, "OWID_CZS": 36, "OWID_GDR": 36, "OWID_KOS": 36,
        "OWID_SOS": 36, "OWID_GFR": 36, "OWID_YPR": 36, "OWID_YGS": 36,
    }
    actual = excluded.country_iso3.value_counts(dropna=False).to_dict()
    if actual != expected:
        raise RuntimeError("OWID non-ISO3 row census differs from documented pinned source")
    frame = frame.loc[frame.country_iso3.isin(ISO3)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate national conflict country-year keys")
    out = {}
    for row in frame.itertuples(index=False, name=None):
        country, year, *raws = row
        values = [frozen.finite(v) for v in raws]
        if any(v is None or v < 0 or v > 100 or not v.is_integer() for v in values):
            continue
        out[(str(country), int(year))] = int(sum(values))
    return out


def national_numeric_values(source_root: Path, role: str) -> dict[tuple[str, int], float]:
    """Restrict the pinned source to the registered ISO3 roster, then use frozen validation."""
    expected_path = source_root / frozen.SOURCE_DICT[role]["path"]
    read_parquet = pd.read_parquet

    def national_read(path, *args, **kwargs):
        frame = read_parquet(path, *args, **kwargs)
        if Path(path) != expected_path:
            raise RuntimeError("numeric adapter intercepted an unexpected source path")
        excluded = frame.loc[~frame.country_iso3.isin(ISO3)]
        if len(excluded) != EXCLUDED_NUMERIC_ROWS[role]:
            raise RuntimeError("numeric source non-ISO3 census changed: " + role)
        return frame.loc[frame.country_iso3.isin(ISO3)].copy()

    pd.read_parquet = national_read
    try:
        return original_numeric_values(source_root, role)
    finally:
        pd.read_parquet = read_parquet


def verify_original_locks(source_root: Path, specs: dict[str, dict]) -> dict[str, str]:
    frozen.RUNNER = ORIGINAL
    try:
        return original_verify_locks(source_root, specs)
    finally:
        frozen.RUNNER = ADAPTER


def main() -> None:
    if "--lock-case" in sys.argv:
        raise SystemExit("source locks belong to the original frozen runner")
    frozen.conflict_values = national_conflict_values
    frozen.numeric_values = national_numeric_values
    frozen.verify_locks = verify_original_locks
    frozen.RUNNER = ADAPTER
    frozen.main()


if __name__ == "__main__":
    main()
