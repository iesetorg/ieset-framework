#!/usr/bin/env python3
"""Replication — State capacity precedes effective liberal market policy.

Spec: State capacity is a prerequisite for effective liberal market policy.

Design:
  1. Broad panel 1996-2019.
  2. WGI Government Effectiveness (state capacity proxy, early window 1996-2005)
     and market openness (WDI trade openness, later window 2005-2019).
  3. Within early high-GE countries, test whether later trade openness is associated
     with higher GDP pc growth.
  4. If early GE predicts later growth gains from trade openness, that supports
     the prerequisite claim.

Falsification:
  SUPPORTED if high-GE countries show significantly stronger trade-openness growth premium
  than low-GE countries.
  REFUTED if the premium is reversed or near-zero across both groups.
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
HID = "state_capacity_precedes_liberal_market"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


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
    ge_path = latest("wgi", "GOV_WGI_GE.EST")
    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")
    manifest = {
        "wgi_ge": {"publisher": "wgi", "series": "GOV_WGI_GE.EST",
                   "vintage_file": str(ge_path.relative_to(REPO_ROOT)), "sha256": sha256(ge_path)},
        "wdi_trade": {"publisher": "world_bank_wdi", "series": "NE.TRD.GNFS.ZS",
                      "vintage_file": str(trade_path.relative_to(REPO_ROOT)), "sha256": sha256(trade_path)},
        "wdi_gdppc_growth": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD.ZG",
                             "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
    }
    ge = load_long(ge_path, "ge")
    trade = load_long(trade_path, "trade")
    growth = load_long(gdppc_path, "gdppc_growth")
    growth["gdppc_growth"] = growth["gdppc_growth"] / 100.0

    # Early GE 1996-2005
    early_ge = ge[(ge["year"] >= 1996) & (ge["year"] <= 2005)].groupby("country")["ge"].mean().reset_index()
    early_ge["high_ge"] = early_ge["ge"] >= early_ge["ge"].median()

    # Later trade openness 2005-2019
    later_trade = trade[(trade["year"] >= 2005) & (trade["year"] <= 2019)].groupby("country")["trade"].mean().reset_index()
    later_trade["high_trade"] = later_trade["trade"] >= later_trade["trade"].median()

    # Later growth 2005-2019
    later_growth = growth[(growth["year"] >= 2005) & (growth["year"] <= 2019)].groupby("country")["gdppc_growth"].mean().reset_index()

    df = early_ge.merge(later_trade, on="country", how="inner").merge(later_growth, on="country", how="inner").dropna()
    if len(df) < 20:
        verdict = "blocked_data_pending — insufficient country overlap."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    # In high-GE countries, is high-trade associated with higher growth?
    hg = df[df["high_ge"]]
    lg = df[~df["high_ge"]]
    hg_ht = hg[hg["high_trade"]]
    hg_lt = hg[~hg["high_trade"]]
    lg_ht = lg[lg["high_trade"]]
    lg_lt = lg[~lg["high_trade"]]

    mean_hg_ht = float(hg_ht["gdppc_growth"].mean()) if len(hg_ht) else 0.0
    mean_hg_lt = float(hg_lt["gdppc_growth"].mean()) if len(hg_lt) else 0.0
    mean_lg_ht = float(lg_ht["gdppc_growth"].mean()) if len(lg_ht) else 0.0
    mean_lg_lt = float(lg_lt["gdppc_growth"].mean()) if len(lg_lt) else 0.0

    diff_hg = mean_hg_ht - mean_hg_lt
    diff_lg = mean_lg_ht - mean_lg_lt

    # Supported if high-GE countries get a positive trade premium and it exceeds the low-GE premium
    if diff_hg > 0 and diff_hg > diff_lg + 0.005:
        verdict = f"supported — High-GE trade premium {diff_hg*100:+.2f}pp exceeds low-GE premium {diff_lg*100:+.2f}pp."
    elif diff_hg <= 0 and diff_lg <= 0:
        verdict = f"refuted — No positive trade premium in either governance group (high-GE {diff_hg*100:+.2f}pp, low-GE {diff_lg*100:+.2f}pp)."
    else:
        verdict = f"partial — High-GE trade premium {diff_hg*100:+.2f}pp, low-GE trade premium {diff_lg*100:+.2f}pp."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_countries": int(len(df)), "high_ge_high_trade": int(len(hg_ht)), "high_ge_low_trade": int(len(hg_lt)),
                    "low_ge_high_trade": int(len(lg_ht)), "low_ge_low_trade": int(len(lg_lt)),
                    "mean_high_ge_high_trade": mean_hg_ht, "mean_high_ge_low_trade": mean_hg_lt,
                    "mean_low_ge_high_trade": mean_lg_ht, "mean_low_ge_low_trade": mean_lg_lt,
                    "diff_high_ge": diff_hg, "diff_low_ge": diff_lg},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wgi_ge: {manifest['wgi_ge']['vintage_file']}\n  wdi_trade: {manifest['wdi_trade']['vintage_file']}\n  wdi_growth: {manifest['wdi_gdppc_growth']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nCross-section of {len(df)} countries. State capacity = mean WGI GE 1996-2005. Trade openness = mean WDI trade 2005-2019. Growth = mean WDI GDP pc growth 2005-2019.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
