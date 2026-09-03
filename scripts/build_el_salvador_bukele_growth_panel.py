#!/usr/bin/env python3
"""Build the El Salvador Bukele-era growth/security panel from pinned WDI vintages.

Annual series for SLV plus Latin American peers (for peer-contrast columns):
real GDP growth, GDP-per-capita growth, homicide rate, FDI inflows, personal
remittances, domestic credit to the private sector, and private consumption.
All inputs are existing on-disk world_bank_wdi vintages (latest of each).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages" / "world_bank_wdi"

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_real_growth_pct",
    "NY.GDP.PCAP.KD.ZG": "gdp_pc_real_growth_pct",
    "VC.IHR.PSRC.P5": "homicide_rate_per_100k",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_net_inflows_pct_gdp",
    "BX.TRF.PWKR.DT.GD.ZS": "remittances_pct_gdp",
    "FS.AST.PRVT.GD.ZS": "credit_to_private_pct_gdp",
    "NE.CON.PRVT.ZS": "private_consumption_pct_gdp",
    "SP.POP.1564.MA.ZS": "working_age_male_share_pct",
}
FOCUS = "SLV"
PEERS = ["MEX", "GTM", "HND", "NIC", "CRI", "PAN", "COL", "PER"]
BUKELE_REGIME_START = 2019


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
        frames.append(frame.loc[frame["country_iso3"].isin([FOCUS] + PEERS)])
        inputs.append({
            "publisher": "world_bank_wdi",
            "series": indicator,
            "vintage_file": str(vintage.relative_to(root)),
            "sha256": sha256_path(vintage),
        })

    panel = frames[0]
    for frame in frames[1:]:
        panel = panel.merge(frame, on=["country_iso3", "year"], how="outer")
    panel = panel.loc[panel["year"].between(2010, 2025)].sort_values(["country_iso3", "year"])

    peer_gdp = (
        panel.loc[panel["country_iso3"].isin(PEERS)]
        .groupby("year")["gdp_real_growth_pct"].mean()
        .rename("latam_peer_gdp_growth_pct")
    )
    panel = panel.merge(peer_gdp, on="year", how="left")
    panel["slv_growth_premium_vs_peers_pp"] = panel["gdp_real_growth_pct"] - panel["latam_peer_gdp_growth_pct"]
    panel["bukele_regime"] = (panel["country_iso3"] == FOCUS) & (panel["year"] >= BUKELE_REGIME_START)

    output_path = root / "data" / "derived" / "el_salvador_bukele_growth_panel.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)

    manifest_dir = root / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"fetch_run_{stamp}_el_salvador_bukele_panel.yaml"
    manifest_path.write_text(yaml.safe_dump({
        "run_utc": stamp,
        "pipeline": "el_salvador_bukele_growth_panel",
        "bukele_regime_from": BUKELE_REGIME_START,
        "inputs": inputs,
        "artifacts": {
            "panel_parquet": str(output_path.relative_to(root)),
            "panel_sha256": sha256_path(output_path),
            "panel_rows": len(panel),
            "focus": FOCUS,
            "peers": PEERS,
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
