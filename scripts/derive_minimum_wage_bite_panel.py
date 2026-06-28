#!/usr/bin/env python3
"""Derive the minimum-wage bite-ratio panel used by the high-bite minimum-wage
hypotheses.

Bite ratio = statutory minimum wage / local median wage.

Sources (both already fetchable):
  - usdol:state_minimum_wage_history   (USD/hour, state-year, with federal floor)
  - bls:OEWS_state_median_hourly_wage_panel  (USD/hour, state-year)

Output vintage (publisher=derived, series=minimum_wage_bite_ratio_subnational_panel):
  country_iso3, unit_id, state_abbr, state_fips, year,
  minimum_wage (USD/hr), median_wage (USD/hr), bite_ratio (min/median)

Usage:
    python3 scripts/derive_minimum_wage_bite_panel.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import utc_now, write_vintage

VINTAGES = ROOT / "data" / "vintages"


def _latest(publisher: str, series: str) -> Path:
    pub_dir = VINTAGES / publisher
    candidates = list(pub_dir.glob(f"{series}@*.parquet"))
    candidates.extend(pub_dir.glob(f"{series}.parquet"))
    if not candidates:
        raise FileNotFoundError(
            f"No vintage for {publisher}:{series}. Run the upstream fetcher first."
        )
    return max(candidates, key=lambda p: p.name)


def main() -> int:
    try:
        mw_path = _latest("usdol", "state_minimum_wage_history")
        wage_path = _latest("bls", "OEWS_state_median_hourly_wage_panel")
    except FileNotFoundError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1

    mw = pd.read_parquet(mw_path)
    wage = pd.read_parquet(wage_path)

    # Normalise join keys.
    mw_keys = mw[["state_fips", "state_abbr", "year", "value"]].rename(
        columns={"value": "minimum_wage"}
    )
    mw_keys["state_fips"] = mw_keys["state_fips"].astype(str).str.zfill(2)
    mw_keys["year"] = pd.to_numeric(mw_keys["year"], errors="coerce").astype("Int64")
    mw_keys["minimum_wage"] = pd.to_numeric(mw_keys["minimum_wage"], errors="coerce")

    wage_keys = wage[["state_fips", "year", "value"]].rename(
        columns={"value": "median_wage"}
    )
    wage_keys["state_fips"] = wage_keys["state_fips"].astype(str).str.zfill(2)
    wage_keys["year"] = pd.to_numeric(wage_keys["year"], errors="coerce").astype("Int64")
    wage_keys["median_wage"] = pd.to_numeric(wage_keys["median_wage"], errors="coerce")

    merged = mw_keys.merge(wage_keys, on=["state_fips", "year"], how="inner")
    merged = merged.dropna(subset=["minimum_wage", "median_wage"])
    merged = merged[merged["median_wage"] > 0]
    merged["bite_ratio"] = merged["minimum_wage"] / merged["median_wage"]
    merged["country_iso3"] = "USA"
    merged["unit_id"] = "US-" + merged["state_abbr"]
    merged = merged[[
        "country_iso3", "unit_id", "state_abbr", "state_fips", "year",
        "minimum_wage", "median_wage", "bite_ratio",
    ]].sort_values(["state_abbr", "year"]).reset_index(drop=True)

    if merged.empty:
        print("BLOCKED: no overlap between minimum wage and median wage panels", file=sys.stderr)
        return 1

    fetch_ts = utc_now()
    out, sha = write_vintage(
        publisher="derived",
        series_id="minimum_wage_bite_ratio_subnational_panel",
        frame=merged,
        fetch_utc=fetch_ts,
    )

    print(f"OK rows={len(merged)} years={int(merged['year'].min())}-{int(merged['year'].max())} "
          f"states={merged['state_abbr'].nunique()}")
    print(f"   {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
