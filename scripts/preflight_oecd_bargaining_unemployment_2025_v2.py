#!/usr/bin/env python3
"""Key-only outcome preflight for the 2025 OECD bargaining holdout.

Never reads selected unemployment values, null masks, or status fields.
The sole numeric column opened is the 2023 bargaining-coverage exposure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROSTER = "data/pinned_evidence/oecd_bargaining_unemployment_2025_temporal_holdout_v2_key_roster.csv"
ROSTER_SHA = "0160f69e5ff5a0995ba95da2d1dec1ace90aa251a07e1084414653591c81eebd"
COVERAGE = "data/vintages/oecd/OECD.ELS.SAE_DSD_TUD_CBC_DF_CBC_1.0@2026-05-01T071721Z.parquet"
COVERAGE_SHA = "45010f706f77803e30cb98d9383e2f19ec54a23c119f693c875e124aa7441086"
OLD_LFS = "data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-05-01T071721Z.parquet"
OLD_LFS_SHA = "46a244d6223b09908dd778a8125e383c853574f6d63b7daa03a83c329f31dd62"
NEW_LFS = "data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-07-23T151216Z.parquet"
NEW_LFS_SHA = "ac58f9ea05eb07e0d4696a81334021120cd679f58847a2fb32dc70e06074e6ae"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def keys(frame: pd.DataFrame, years: set[int]) -> dict[int, set[str]]:
    selected = frame[
        frame.MEASURE.eq("UNE_RATE")
        & frame.SEX.eq("_T")
        & frame.AGE.eq("Y15T64")
        & frame.LABOUR_FORCE_STATUS.eq("UNE")
    ]
    return {
        year: set(selected.loc[selected.period.eq(year), "REF_AREA"].astype(str))
        for year in years
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    roster_path = ROOT / ROSTER
    assert digest(roster_path) == ROSTER_SHA, "frozen roster changed"
    with roster_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 26 and len({row["country_iso3"] for row in rows}) == 26
    assert all(
        row["exposure_year"] == "2023"
        and row["baseline_year"] == "2023"
        and row["outcome_year"] == "2025"
        for row in rows
    )
    roster = {row["country_iso3"] for row in rows}

    for relative, expected in [
        (COVERAGE, COVERAGE_SHA), (OLD_LFS, OLD_LFS_SHA), (NEW_LFS, NEW_LFS_SHA)
    ]:
        assert digest(source_root / relative) == expected, f"source hash changed: {relative}"

    coverage = pd.read_parquet(
        source_root / COVERAGE,
        columns=["REF_AREA", "MEASURE", "period", "value", "OBS_STATUS"],
    )
    exposure = coverage[
        coverage.MEASURE.eq("ERB")
        & coverage.period.eq(2023)
        & coverage.OBS_STATUS.eq("A")
        & coverage.REF_AREA.isin(roster)
    ]
    assert len(exposure) == 26 and exposure.REF_AREA.nunique() == 26
    values = pd.to_numeric(exposure.value, errors="coerce")
    assert values.notna().all() and values.between(0, 100).all()
    iqr = float(values.quantile(.75) - values.quantile(.25))
    centered = (values - values.mean()) ** 2
    max_share = float(centered.max() / centered.sum())

    columns = ["REF_AREA", "MEASURE", "SEX", "AGE", "LABOUR_FORCE_STATUS", "period"]
    old = pd.read_parquet(source_root / OLD_LFS, columns=columns)
    new = pd.read_parquet(source_root / NEW_LFS, columns=columns)
    old_keys = keys(old, {2023, 2025})
    new_keys = keys(new, {2023, 2025})
    assert not old_keys[2025], "2025 is not new relative to the old source"
    joint = new_keys[2023] & new_keys[2025] & set(exposure.REF_AREA)
    assert joint == roster, "key-only roster changed"
    assert iqr >= 20.0 and max_share <= 0.20

    print(json.dumps({
        "status": "key_only_preflight_pass",
        "source_root": str(source_root),
        "selected_unemployment_values_or_status_read": False,
        "roster_count": len(roster),
        "old_lfs_2025_key_count": len(old_keys[2025]),
        "new_lfs_joint_key_count": len(joint),
        "exposure_iqr_pp": round(iqr, 6),
        "max_centered_exposure_square_share": round(max_share, 6),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
