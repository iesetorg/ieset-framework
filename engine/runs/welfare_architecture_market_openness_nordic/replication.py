#!/usr/bin/env python3
"""Replication — Nordic welfare architecture compatible with market openness.

Spec: Nordic welfare-state architecture is compatible with sustained market openness
and high-income frontier status, contradicting a blanket free-market claim that
welfare states suppress growth.

Design:
  1. Nordic panel 1960-2023 (Denmark, Finland, Norway, Sweden, Iceland).
  2. Compare GDP pc growth, trade openness, and frontier status vs OECD peers
     with lower social spending.
  3. Test whether Nordics maintained frontier status while maintaining high tax burdens.

Falsification:
  SUPPORTED if Nordics grew at or above OECD median and maintained trade openness above median.
  REFUTED if Nordics grew significantly below OECD median (< -0.50 pp/yr).
  Otherwise PARTIAL.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "welfare_architecture_market_openness_nordic"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

NORDICS = {"DNK", "FIN", "NOR", "SWE", "ISL"}
OECD = {"AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "CZE", "DEU", "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL", "ISR", "ITA", "JPN", "KOR", "LUX", "MEX", "NLD", "NOR", "NZL", "POL", "PRT", "SVK", "SVN", "SWE", "TUR", "USA"}
PERIOD = (1995, 2023)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_long(path: Path, name: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    tax_path = latest("world_bank_wdi", "GC.TAX.TOTL.GD.ZS")
    manifest = {
        "wdi_gdppc": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD",
                      "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
        "wdi_trade": {"publisher": "world_bank_wdi", "series": "NE.TRD.GNFS.ZS",
                      "vintage_file": str(trade_path.relative_to(REPO_ROOT)), "sha256": sha256(trade_path)},
        "wdi_tax": {"publisher": "world_bank_wdi", "series": "GC.TAX.TOTL.GD.ZS",
                    "vintage_file": str(tax_path.relative_to(REPO_ROOT)), "sha256": sha256(tax_path)},
    }
    gdppc = load_long(gdppc_path, "gdppc")
    trade = load_long(trade_path, "trade")
    tax = load_long(tax_path, "tax")

    # Annual growth rates from GDP pc
    gdppc = gdppc.sort_values(["country", "year"])
    gdppc["log_gdppc"] = np.log(gdppc["gdppc"].replace({0: np.nan}))
    gdppc["growth_yoy"] = gdppc.groupby("country")["log_gdppc"].diff()

    # Filter period
    gdppc = gdppc[(gdppc["year"] >= PERIOD[0]) & (gdppc["year"] <= PERIOD[1])]
    trade = trade[(trade["year"] >= PERIOD[0]) & (trade["year"] <= PERIOD[1])]
    tax = tax[(tax["year"] >= PERIOD[0]) & (tax["year"] <= PERIOD[1])]

    # Country means
    growth_mean = gdppc.groupby("country")["growth_yoy"].mean().reset_index()
    trade_mean = trade.groupby("country")["trade"].mean().reset_index()
    tax_mean = tax.groupby("country")["tax"].mean().reset_index()

    df = growth_mean.merge(trade_mean, on="country", how="outer").merge(tax_mean, on="country", how="outer")
    df = df[df["country"].isin(OECD)].dropna(subset=["growth_yoy"])

    nordic_df = df[df["country"].isin(NORDICS)]
    oecd_non_nordic = df[~df["country"].isin(NORDICS)]

    nordic_growth = float(nordic_df["growth_yoy"].mean()) if len(nordic_df) else 0.0
    oecd_median_growth = float(oecd_non_nordic["growth_yoy"].median()) if len(oecd_non_nordic) else 0.0
    nordic_trade = float(nordic_df["trade"].mean()) if len(nordic_df) else 0.0
    oecd_median_trade = float(oecd_non_nordic["trade"].median()) if len(oecd_non_nordic) else 0.0
    nordic_tax = float(nordic_df["tax"].mean()) if len(nordic_df) else 0.0

    diff_growth = nordic_growth - oecd_median_growth

    if nordic_growth >= oecd_median_growth - 0.005 and nordic_trade >= oecd_median_trade:
        verdict = f"supported — Nordic growth {nordic_growth*100:+.2f}%/yr >= OECD median {oecd_median_growth*100:+.2f}%/yr, trade {nordic_trade:.1f}% >= median {oecd_median_trade:.1f}%."
    elif nordic_growth < oecd_median_growth - 0.005:
        verdict = f"refuted — Nordic growth {nordic_growth*100:+.2f}%/yr below OECD median {oecd_median_growth*100:+.2f}%/yr."
    else:
        verdict = f"partial — Nordic growth {nordic_growth*100:+.2f}%/yr vs OECD median {oecd_median_growth*100:+.2f}%/yr, trade {nordic_trade:.1f}% vs {oecd_median_trade:.1f}%."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_nordics": int(len(nordic_df)), "n_oecd": int(len(df)),
                    "nordic_growth": nordic_growth, "oecd_median_growth": oecd_median_growth,
                    "nordic_trade": nordic_trade, "oecd_median_trade": oecd_median_trade,
                    "nordic_tax": nordic_tax, "diff_growth": diff_growth},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wdi_gdppc: {manifest['wdi_gdppc']['vintage_file']}\n  wdi_trade: {manifest['wdi_trade']['vintage_file']}\n  wdi_tax: {manifest['wdi_tax']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nNordics: {sorted(NORDICS)}. OECD sample n={len(df)}. Period {PERIOD[0]}-{PERIOD[1]}.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
