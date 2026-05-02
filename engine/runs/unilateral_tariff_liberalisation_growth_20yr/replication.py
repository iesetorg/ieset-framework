#!/usr/bin/env python3
"""Replication — Unilateral tariff liberalisation and 20-year growth.

Spec: Countries undertaking unilateral tariff liberalisation experience stronger
20-year productivity and consumption growth than protected peers.

Design:
  1. Broad panel 1980-2019.
  2. WDI applied tariff rate (TM.TAX.MRCH.WM.AR.ZS) + PWT GDP pc.
  3. Identify large tariff-cut episodes (top tercile of 10-year tariff reduction).
  4. Compare post-episode GDP pc growth to comparator median.

Falsification:
  SUPPORTED if mean post-episode growth >= comparator median + 0.50 pp/yr.
  REFUTED if mean post-episode growth <= comparator median.
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
HID = "unilateral_tariff_liberalisation_growth_20yr"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1980
END_YEAR = 2019
EPISODE_WINDOW = 10
GROWTH_WINDOW = 10
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
    tariff_path = latest("world_bank_wdi", "TM.TAX.MRCH.WM.AR.ZS")
    pwt_path = latest("pwt", "pwt_full")
    manifest = {
        "wdi_tariff": {"publisher": "world_bank_wdi", "series": "TM.TAX.MRCH.WM.AR.ZS",
                       "vintage_file": str(tariff_path.relative_to(REPO_ROOT)), "sha256": sha256(tariff_path)},
        "pwt": {"publisher": "pwt", "series": "pwt_full",
                "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path)},
    }
    tariff = load_long(tariff_path, "tariff")
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]
    pwt["log_gdppc"] = np.log(pwt["rgdpe_pc"])

    # Detect tariff-cut episodes: largest 10-year drop in tariff, base year 1980-2000
    episodes = []
    for iso3, g in tariff.groupby("country"):
        g = g.sort_values("year")
        for base_y in range(BASE_YEAR, 2001):
            end_y = base_y + EPISODE_WINDOW
            base_row = g[g["year"] == base_y]
            end_row = g[g["year"] == end_y]
            if base_row.empty or end_row.empty: continue
            base_t = float(base_row["tariff"].iloc[0])
            end_t = float(end_row["tariff"].iloc[0])
            if pd.isna(base_t) or pd.isna(end_t) or base_t <= 0: continue
            drop = base_t - end_t
            episodes.append({"country": iso3, "base_year": base_y, "end_year": end_y, "tariff_drop": drop, "base_tariff": base_t})
    ep_df = pd.DataFrame(episodes)
    if len(ep_df) < 20:
        verdict = "blocked_data_pending — insufficient tariff episode observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return
    # Top tercile of drops
    cut = ep_df["tariff_drop"].quantile(2/3)
    reformers = ep_df[ep_df["tariff_drop"] >= cut].copy()
    # Compute post-episode growth (next 10 years)
    def _growth(row):
        sub = pwt[(pwt["country"] == row["country"]) & (pwt["year"] >= row["end_year"]) & (pwt["year"] <= row["end_year"] + GROWTH_WINDOW)].sort_values("year")
        if len(sub) < 2: return None
        first = sub.iloc[0]
        last = sub.iloc[-1]
        if first["rgdpe_pc"] <= 0 or last["rgdpe_pc"] <= 0: return None
        years = int(last["year"]) - int(first["year"])
        if years <= 0: return None
        return (np.log(last["rgdpe_pc"]) - np.log(first["rgdpe_pc"])) / years
    reformers["post_growth"] = reformers.apply(_growth, axis=1)
    reformers = reformers[reformers["post_growth"].notna()]
    if len(reformers) < 5:
        verdict = "blocked_data_pending — insufficient post-episode growth data."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return
    mean_reform = float(reformers["post_growth"].mean())
    # Comparator: all country-decade growth observations not in reformer episodes
    comp_growths = []
    for iso3 in pwt["country"].unique():
        sub = pwt[pwt["country"] == iso3].sort_values("year")
        for y in range(1990, END_YEAR - GROWTH_WINDOW + 1):
            # Skip if this country-year is a reformer episode start
            if iso3 in reformers["country"].values and y in reformers["end_year"].values:
                continue
            s = sub[(sub["year"] >= y) & (sub["year"] <= y + GROWTH_WINDOW)]
            if len(s) < 2: continue
            first = s.iloc[0]
            last = s.iloc[-1]
            if first["rgdpe_pc"] <= 0 or last["rgdpe_pc"] <= 0: continue
            yrs = int(last["year"]) - int(first["year"])
            if yrs <= 0: continue
            g = (np.log(last["rgdpe_pc"]) - np.log(first["rgdpe_pc"])) / yrs
            comp_growths.append(g)
    comp_median = float(np.median(comp_growths)) if comp_growths else 0.0
    diff = mean_reform - comp_median
    if mean_reform >= comp_median + DIFF_THRESHOLD:
        verdict = f"supported — Reformer post-episode growth {mean_reform*100:+.2f}%/yr vs comparator median {comp_median*100:+.2f}%/yr (diff {diff*100:+.2f}pp, n={len(reformers)})."
    elif mean_reform <= comp_median:
        verdict = f"refuted — Reformer growth {mean_reform*100:+.2f}%/yr at or below comparator median {comp_median*100:+.2f}%/yr."
    else:
        verdict = f"partial — Reformer growth {mean_reform*100:+.2f}%/yr vs median {comp_median*100:+.2f}%/yr (diff {diff*100:+.2f}pp)."
    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_reformers": int(len(reformers)), "mean_reformer_growth": mean_reform, "comparator_median": comp_median, "diff": diff, "tariff_drop_cutoff": cut},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wdi_tariff: {manifest['wdi_tariff']['vintage_file']}\n  pwt: {manifest['pwt']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
