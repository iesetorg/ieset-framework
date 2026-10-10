#!/usr/bin/env python3
"""Audited parser-only repair for frozen food-production/CPI runner.

The preregistered runner remains byte-identical. This wrapper removes only WDI
aggregate keys excluded by the already committed ISO3-plus-XKX key roster
before its duplicate-key check. No selected-value filter or model rule changes.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = "scripts/run_wdi_food_production_cpi_forward_2026.py"
REPAIR = "scripts/run_wdi_food_production_cpi_forward_2026_parser_repair.py"
ERRATUM = "engine/audits/wdi_food_production_cpi_parser_erratum_2026-10-10.md"
spec = importlib.util.spec_from_file_location("frozen_food_cpi", ROOT / ORIGINAL)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import frozen food/CPI runner")
frozen_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen_runner)
first_registration = frozen_runner.registration


def repaired_registration() -> str:
    frozen_runner.RUNNER = ORIGINAL
    try:
        registration_commit = first_registration()
    finally:
        frozen_runner.RUNNER = REPAIR
    repair_commit = frozen_runner.first_add(REPAIR)
    if frozen_runner.first_add(ERRATUM) != repair_commit:
        raise RuntimeError("parser erratum not committed with repair")
    frozen_runner.frozen(REPAIR, repair_commit)
    frozen_runner.frozen(ERRATUM, repair_commit)
    source_lock_commit, _ = frozen_runner.source_lock(registration_commit)
    if subprocess.run(["git", "merge-base", "--is-ancestor", source_lock_commit,
                       repair_commit], cwd=ROOT).returncode:
        raise RuntimeError("parser repair predates frozen source lock")
    if subprocess.run(["git", "ls-tree", "-r", "--name-only", repair_commit,
                       "--", frozen_runner.RUN], cwd=ROOT, capture_output=True,
                      text=True, check=True).stdout.strip():
        raise RuntimeError("parser-repair commit already contains a measured run")
    return registration_commit


def repaired_cell_map(source_root: Path, role: str):
    source = frozen_runner.SOURCES[role]
    frame = pd.read_parquet(source_root / source["path"], columns=[
        "country_iso3", "indicator_id", "year", "value", "obs_status"])
    if set(frame["indicator_id"].dropna()) != {source["series_id"]}:
        raise RuntimeError(f"indicator mismatch: {role}")
    eligible_countries = {country for country, _ in frozen_runner.roster()}
    frame = frame.loc[frame.country_iso3.isin(eligible_countries)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate national source key: {role}")
    return {(country, int(year)): (value, status) for country, year, value, status in zip(
        frame.country_iso3, frame.year, frame.value, frame.obs_status)}


frozen_runner.RUNNER = REPAIR
frozen_runner.registration = repaired_registration
frozen_runner.cell_map = repaired_cell_map

if __name__ == "__main__":
    raise SystemExit(frozen_runner.main())
