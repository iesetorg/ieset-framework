#!/usr/bin/env python3
"""Build the Anglo public/private stagnation panel from pinned WDI vintages.

Annual series 2000-2024 for GBR, CAN, AUS, NZL (the centre-left welfare-state
Anglo set) with USA as contrast: real GDP growth, GDP-per-capita growth,
broad money growth, government consumption share, government expense share,
gross savings, private consumption growth, and industry employment share
(private-sector proxy). Supports the money-growth / public-crowding-out /
real-income-stagnation hypothesis family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages" / "world_bank_wdi"

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_real_growth_pct",
    "NY.GDP.PCAP.KD.ZG": "gdp_pc_real_growth_pct",
    "FM.LBL.BMNY.ZG": "broad_money_growth_pct",
    "NE.CON.GOVT.ZS": "gov_consumption_pct_gdp",
    "GC.XPN.TOTL.GD.ZS": "gov_expense_pct_gdp",
    "NY.GNS.ICTR.ZS": "gross_savings_pct_gdp",
    "NE.CON.PRVT.KD.ZG": "private_consumption_growth_pct",
    "SL.IND.EMPL.ZS": "industry_employment_share_pct",
}
COUNTRIES = ["GBR", "CAN", "AUS", "NZL", "USA"]
WELFARE_ANGLO = ["GBR", "CAN", "AUS", "NZL"]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_vintage(indicator: str) -> Path:
    candidates = sorted(VINTAGES.glob(f"{indicator}@*.parquet"))
    if not candidates:
        raise FileNotFoundError(f"no vintage for {indicator}")
    return candidates[-1]


def build(run_utc: datetime | None = None, root: Path | None = None) -> dict:
    run_utc = run_utc or datetime.now(tz=timezone.utc)
    root = root or ROOT
    stamp = run_utc.strftime("%Y-%m-%dT%H%M%SZ")

    inputs: list[dict] = []
    frames = []
    for indicator, column in INDICATORS.items():
        vintage = latest_vintage(indicator)
        frame = pd.read_parquet(vintage)[["country_iso3", "year", "value"]]
        frame = frame.rename(columns={"value": column})
        frames.append(frame.loc[frame["country_iso3"].isin(COUNTRIES)])
        inputs.append({
            "publisher": "world_bank_wdi",
            "series": indicator,
            "vintage_file": str(vintage.relative_to(root)),
            "sha256": sha256_path(vintage),
        })

    panel = frames[0]
    for frame in frames[1:]:
        panel = panel.merge(frame, on=["country_iso3", "year"], how="outer")
    panel = panel.loc[panel["year"].between(2000, 2024)].sort_values(["country_iso3", "year"])
    panel["welfare_anglo"] = panel["country_iso3"].isin(WELFARE_ANGLO)
    panel["stagnation_window"] = panel["year"].between(2019, 2024)
    panel["money_growth_above_5pct"] = panel["broad_money_growth_pct"] > 5.0

    output_path = root / "data" / "derived" / "anglo_public_private_stagnation_panel.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)

    manifest_dir = root / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"fetch_run_{stamp}_anglo_stagnation_panel.yaml"
    manifest_path.write_text(yaml.safe_dump({
        "run_utc": stamp,
        "pipeline": "anglo_public_private_stagnation_panel",
        "inputs": inputs,
        "artifacts": {
            "panel_parquet": str(output_path.relative_to(root)),
            "panel_sha256": sha256_path(output_path),
            "panel_rows": len(panel),
            "countries": COUNTRIES,
            "welfare_anglo": WELFARE_ANGLO,
        },
    }, sort_keys=False))
    return {
        "rows": len(panel),
        "panel": str(output_path.relative_to(root)),
        "manifest": str(manifest_path.relative_to(root)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = build()
    print(json.dumps(result) if args.json else result)
