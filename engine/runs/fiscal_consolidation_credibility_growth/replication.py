#!/usr/bin/env python3
"""Replication — Fiscal consolidation and growth via credibility premium.

Spec: Fiscal consolidation episodes that improve sovereign-credibility proxies
(WGI Government Effectiveness, rule of law) yield subsequent GDP pc growth premiums
relative to non-consolidating peers.

Design:
  1. Broad panel 1996-2019.
  2. WDI tax revenue (% of GDP) as fiscal proxy (GC.TAX.TOTL.GD.ZS).
  3. Identify large tax-revenue increases (consolidation) over 5-year windows.
  4. Compare post-consolidation growth to comparator median, split by
     WGI Government Effectiveness improvement.

Falsification:
  SUPPORTED if consolidators with GE improvement grow >= comparator median + 0.50 pp/yr.
  REFUTED if they grow <= comparator median.
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

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "fiscal_consolidation_credibility_growth"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD_START = 1996
PERIOD_END = 2019
WINDOW = 5
POST_WINDOW = 5
DIFF_THRESHOLD = 0.005


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
    tax_path = latest("world_bank_wdi", "GC.TAX.TOTL.GD.ZS")
    ge_path = latest("wgi", "GOV_WGI_GE.EST")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")
    manifest = {
        "wdi_tax": {"publisher": "world_bank_wdi", "series": "GC.TAX.TOTL.GD.ZS",
                    "vintage_file": str(tax_path.relative_to(REPO_ROOT)), "sha256": sha256(tax_path)},
        "wgi_ge": {"publisher": "wgi", "series": "GOV_WGI_GE.EST",
                   "vintage_file": str(ge_path.relative_to(REPO_ROOT)), "sha256": sha256(ge_path)},
        "wdi_gdppc_growth": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD.ZG",
                             "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
    }
    tax = load_long(tax_path, "tax")
    ge = load_long(ge_path, "ge")
    growth = load_long(gdppc_path, "gdppc_growth")
    growth["gdppc_growth"] = growth["gdppc_growth"] / 100.0

    # Detect consolidation episodes: top tercile of 5-year tax-revenue increases
    episodes = []
    for iso3, g in tax.groupby("country"):
        g = g.sort_values("year")
        for base_y in range(PERIOD_START, PERIOD_END - WINDOW - POST_WINDOW + 1):
            end_y = base_y + WINDOW
            base_row = g[g["year"] == base_y]
            end_row = g[g["year"] == end_y]
            if base_row.empty or end_row.empty: continue
            base_t = float(base_row["tax"].iloc[0])
            end_t = float(end_row["tax"].iloc[0])
            if pd.isna(base_t) or pd.isna(end_t) or base_t <= 0: continue
            change = end_t - base_t
            episodes.append({"country": iso3, "base_year": base_y, "end_year": end_y, "tax_change": change})
    ep_df = pd.DataFrame(episodes)
    if len(ep_df) < 20:
        verdict = "blocked_data_pending — insufficient consolidation episode observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    cut = ep_df["tax_change"].quantile(2/3)
    consolidators = ep_df[ep_df["tax_change"] >= cut].copy()

    # GE improvement during consolidation
    def ge_change(row):
        s = ge[(ge["country"] == row["country"]) & (ge["year"] >= row["base_year"]) & (ge["year"] <= row["end_year"])]
        if len(s) < 2: return np.nan
        return float(s["ge"].iloc[-1]) - float(s["ge"].iloc[0])
    consolidators["ge_change"] = consolidators.apply(ge_change, axis=1)

    # Post-consolidation growth
    def post_growth(row):
        s = growth[(growth["country"] == row["country"]) & (growth["year"] > row["end_year"]) & (growth["year"] <= row["end_year"] + POST_WINDOW)]
        if len(s) == 0: return np.nan
        return float(s["gdppc_growth"].mean())
    consolidators["post_growth"] = consolidators.apply(post_growth, axis=1)
    consolidators = consolidators[consolidators["post_growth"].notna()]
    if len(consolidators) < 5:
        verdict = "blocked_data_pending — insufficient post-consolidation growth data."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    # Split by GE improvement
    consolidators["ge_improved"] = consolidators["ge_change"] > 0
    improved = consolidators[consolidators["ge_improved"]]
    not_improved = consolidators[~consolidators["ge_improved"]]

    mean_improved = float(improved["post_growth"].mean()) if len(improved) else 0.0
    mean_not_improved = float(not_improved["post_growth"].mean()) if len(not_improved) else 0.0

    # Comparator median: all country-period growths not in consolidation episodes
    comp_growths = []
    for iso3 in growth["country"].unique():
        s = growth[growth["country"] == iso3]
        for y in range(PERIOD_START + WINDOW, PERIOD_END - POST_WINDOW + 1):
            # Skip if this country-year is a consolidator episode end
            if iso3 in consolidators["country"].values and y in consolidators["end_year"].values:
                continue
            ss = s[(s["year"] > y) & (s["year"] <= y + POST_WINDOW)]
            if len(ss) == 0: continue
            comp_growths.append(float(ss["gdppc_growth"].mean()))
    comp_growths = [g for g in comp_growths if not pd.isna(g)]
    comp_median = float(np.median(comp_growths)) if comp_growths else 0.0

    diff_improved = mean_improved - comp_median
    diff_not = mean_not_improved - comp_median

    if mean_improved >= comp_median + DIFF_THRESHOLD:
        verdict = f"supported — High-credibility consolidators {mean_improved*100:+.2f}%/yr vs comparator median {comp_median*100:+.2f}%/yr (diff {diff_improved*100:+.2f}pp, n={len(improved)})."
    elif mean_improved <= comp_median:
        verdict = f"refuted — High-credibility consolidators {mean_improved*100:+.2f}%/yr at or below comparator median {comp_median*100:+.2f}%/yr."
    else:
        verdict = f"partial — High-credibility consolidators {mean_improved*100:+.2f}%/yr vs median {comp_median*100:+.2f}%/yr (diff {diff_improved*100:+.2f}pp)."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_consolidators": int(len(consolidators)), "n_improved": int(len(improved)), "n_not_improved": int(len(not_improved)),
                    "mean_improved": mean_improved, "mean_not_improved": mean_not_improved, "comparator_median": comp_median,
                    "diff_improved": diff_improved, "diff_not_improved": diff_not},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wdi_tax: {manifest['wdi_tax']['vintage_file']}\n  wgi_ge: {manifest['wgi_ge']['vintage_file']}\n  wdi_growth: {manifest['wdi_gdppc_growth']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
