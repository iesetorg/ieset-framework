#!/usr/bin/env python3
"""Build the Argentina Milei stabilisation panel from live BCRA + INDEC APIs.

Farms the monthly monetary/price series for the Milei-window case study and
the Peronism-cycle contrast: INDEC national CPI, monetary base, private M2,
official and retail FX (the cepo gap), reserves, and the 1-month LELIQ
policy proxy. Lands pinned vintages per fetch and a joined monthly panel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers import argentina as arg  # noqa: E402

MILEI_TOOK_OFFICE = "2023-12-10"
BCRA_SERIES = {
    "1": "reserves_usd",
    "4": "fx_retail_ars_usd",
    "5": "fx_wholesale_ars_usd",
    "15": "monetary_base_ars_mmn",
    "25": "m2_private_yoy_pct",
    "109": "m2_total_ars_mmn",
    "155": "leliq_notalq_ars_mmn",
    "166": "leliq_1m_rate_pct",
}
INDEC_CPI = "148.3_INIVELNAL_DICI_M_26"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def monthly_index(frame: pd.DataFrame, date_col: str, value_col: str) -> pd.Series:
    s = frame[[date_col, value_col]].copy()
    s[date_col] = pd.to_datetime(s[date_col])
    s = s.set_index(date_col)[value_col].sort_index()
    return s.resample("MS").last().ffill()


def build(
    fetch: Callable[..., Any] | None = None,
    run_utc: datetime | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    fetch = fetch or arg.fetch
    run_utc = run_utc or datetime.now(tz=timezone.utc)
    root = root or ROOT
    stamp = run_utc.strftime("%Y-%m-%dT%H%M%SZ")
    entries: list[dict[str, Any]] = []
    series: dict[str, pd.Series] = {}

    result = fetch(INDEC_CPI, publisher_id="indec", limit=5000)
    entries.append(result.as_manifest_entry())
    cpi_frame = pd.read_parquet(result.parquet_path)
    date_col = next(c for c in cpi_frame.columns if c.lower() in {"fecha", "date", "indice_tiempo"})
    value_col = next(c for c in cpi_frame.columns if c not in {date_col})
    cpi = monthly_index(cpi_frame, date_col, value_col)
    series["cpi_index"] = cpi

    for var, name in BCRA_SERIES.items():
        result = fetch(var, publisher_id="bcra", desde="2015-01-01")
        entries.append(result.as_manifest_entry())
        frame = pd.read_parquet(result.parquet_path)
        date_col = next(c for c in frame.columns if c.lower() in {"fecha", "date"})
        value_col = next(c for c in frame.columns if c not in {date_col})
        series[name] = monthly_index(frame, date_col, value_col)

    panel = pd.DataFrame(series)
    panel = panel.loc["2015-01-01":].copy()
    # CPI index ffills ahead of INDEC publication; derived price stats are
    # only valid where the underlying observation actually advanced (first
    # observed month counts as observed).
    panel["cpi_observed"] = (
        panel["cpi_index"].notna() & panel["cpi_index"].diff().fillna(1).ne(0)
    )
    panel["cpi_mom_pct"] = panel["cpi_index"].pct_change(fill_method=None) * 100
    panel["cpi_yoy_pct"] = panel["cpi_index"].pct_change(12, fill_method=None) * 100
    panel["cpi_12m_annualised_pct"] = ((1 + panel["cpi_mom_pct"] / 100) ** 12 - 1) * 100
    panel.loc[~panel["cpi_observed"], ["cpi_mom_pct", "cpi_yoy_pct", "cpi_12m_annualised_pct"]] = float("nan")
    panel["monetary_base_yoy_pct"] = panel["monetary_base_ars_mmn"].pct_change(12, fill_method=None) * 100
    panel["fx_gap_pct"] = (panel["fx_retail_ars_usd"] / panel["fx_wholesale_ars_usd"] - 1) * 100
    panel["milei_era"] = panel.index >= pd.Timestamp(MILEI_TOOK_OFFICE)

    panel.index.name = "month_start"
    panel = panel.reset_index()

    output_path = root / "data" / "derived" / "argentina_milei_stabilisation_panel.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)

    manifest_dir = root / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"fetch_run_{stamp}_argentina_milei_panel.yaml"
    manifest_path.write_text(yaml.safe_dump({
        "run_utc": stamp,
        "pipeline": "argentina_milei_stabilisation_panel",
        "milei_window_from": MILEI_TOOK_OFFICE,
        "entries": entries,
        "artifacts": {
            "panel_parquet": str(output_path.relative_to(root)),
            "panel_sha256": sha256_path(output_path),
            "panel_rows": len(panel),
            "months_covered": f"{panel['month_start'].min().date()}..{panel['month_start'].max().date()}",
        },
    }, sort_keys=False))
    return {
        "rows": len(panel),
        "panel": str(output_path.relative_to(root)),
        "manifest": str(manifest_path.relative_to(root)),
        "last_month": str(panel["month_start"].max().date()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = build()
    print(json.dumps(result) if args.json else result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
