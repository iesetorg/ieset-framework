#!/usr/bin/env python3
"""Build derived US state minimum-wage bite-ratio panels.

Inputs:
- USDOL state minimum wage history
- BLS OEWS state median hourly wage panel
- BLS OEWS state 10th percentile hourly wage panel

Outputs:
- `derived:minimum_wage_bite_ratio_state_panel`
- `derived:minimum_wage_low_tail_bite_ratio_state_panel`
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, write_manifest, write_vintage  # noqa: E402


def latest(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return matches[-1]


def build(kind: str, wage_path: Path, minwage_path: Path, fetch_ts: datetime) -> FetchResult:
    minwage = pd.read_parquet(minwage_path)
    wage = pd.read_parquet(wage_path)
    minwage = minwage[["state_fips", "state_abbr", "state_name", "year", "value"]].rename(
        columns={"value": "minimum_wage"}
    )
    wage = wage[["state_fips", "state_iso", "year", "value"]].rename(columns={"value": "denominator_wage"})
    panel = minwage.merge(wage, on=["state_fips", "year"], how="inner")
    panel["bite_ratio"] = panel["minimum_wage"] / panel["denominator_wage"]
    panel["denominator"] = kind
    panel = panel.dropna(subset=["minimum_wage", "denominator_wage", "bite_ratio"])
    panel = panel.sort_values(["state_fips", "year"]).reset_index(drop=True)
    series_id = (
        "minimum_wage_bite_ratio_state_panel"
        if kind == "median"
        else "minimum_wage_low_tail_bite_ratio_state_panel"
    )
    out, sha = write_vintage(
        publisher="derived",
        series_id=series_id,
        frame=panel,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="derived",
        series_id=series_id,
        source_url="derived://usdol:state_minimum_wage_history + bls:OEWS_state_*_hourly_wage_panel",
        methodology_url="engine/audits/data_gap_unlock_assessment_2026-05-12.md",
        license="composite; see input vintages",
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="ratio",
        currency=None,
        start_date=str(int(panel["year"].min())) if len(panel) else None,
        end_date=str(int(panel["year"].max())) if len(panel) else None,
        sha256=sha,
        parquet_path=out,
        extra={
            "input_minimum_wage_vintage": str(minwage_path.relative_to(ROOT)),
            "input_wage_vintage": str(wage_path.relative_to(ROOT)),
            "state_count": int(panel["state_fips"].nunique()),
            "denominator": kind,
        },
    )


def main() -> int:
    fetch_ts = utc_now()
    minwage = latest("data/vintages/usdol/state_minimum_wage_history@*.parquet")
    median = latest("data/vintages/bls/OEWS_state_median_hourly_wage_panel@*.parquet")
    p10 = latest("data/vintages/bls/OEWS_state_p10_hourly_wage_panel@*.parquet")
    results = [
        build("median", median, minwage, fetch_ts),
        build("p10", p10, minwage, fetch_ts),
    ]
    manifest = write_manifest(results)
    audit = ROOT / "engine" / "audits" / f"minimum_wage_bite_panel_build_{fetch_ts.strftime('%Y-%m-%dT%H%M%SZ')}.json"
    audit.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2) + "\n")
    for result in results:
        print(
            f"OK derived:{result.series_id} rows={result.rows} "
            f"period={result.start_date}->{result.end_date} vintage={result.parquet_path.relative_to(ROOT)}"
        )
    print(f"manifest: {manifest.relative_to(ROOT)}")
    print(f"audit: {audit.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
