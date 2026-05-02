#!/usr/bin/env python3
"""Replication — Poland market transition and 30-year income growth, 1991-2019.

Spec: Poland's sustained market transition predicts stronger long-run income growth
than CEE countries with weaker competition and slower privatisation.

Design:
  1. Poland + CEE comparator set.
  2. PWT RGDPE per capita 1991-2019.
  3. Endpoint slope comparison relative to Germany.

Falsification:
  SUPPORTED if Poland slope >= comparator median + 0.50 pp/yr.
  REFUTED if Poland slope <= comparator median.
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
HID = "poland_market_transition_30yr_growth"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1991
END_YEAR = 2019
DIFF_THRESHOLD = 0.005

TARGET = "POL"
FRONTIER = "DEU"
COMPARATORS = ["CZE", "SVK", "HUN", "SVN", "HRV", "BGR", "ROU", "EST", "LVA", "LTU"]


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pwt_path = latest("pwt", "pwt_full")
    manifest = {
        "pwt": {"publisher": "pwt", "series": "pwt_full",
                "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path)},
    }
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt[(pwt["year"] >= BASE_YEAR) & (pwt["year"] <= END_YEAR)]
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]
    frontier = pwt[pwt["country_iso3"] == FRONTIER][["year", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "frontier_rgdpe_pc"})
    panel = pwt.merge(frontier, on="year", how="inner")
    panel["log_rel_frontier"] = np.log(panel["rgdpe_pc"] / panel["frontier_rgdpe_pc"])
    countries = [TARGET] + COMPARATORS
    rows = []
    for iso3 in countries:
        sub = panel[panel["country_iso3"] == iso3].sort_values("year")
        if len(sub) < 2: continue
        base = sub[sub["year"] == BASE_YEAR]
        end = sub[sub["year"] == END_YEAR]
        if base.empty or end.empty: continue
        slope = (float(end["log_rel_frontier"].iloc[0]) - float(base["log_rel_frontier"].iloc[0])) / (END_YEAR - BASE_YEAR)
        rows.append({"country_iso3": iso3, "convergence_slope": slope, "is_poland": iso3 == TARGET})
    results = pd.DataFrame(rows)
    if len(results) < 5:
        verdict = "blocked_data_pending — insufficient comparator coverage."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(results))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return
    pol = results[results["is_poland"]]
    comp = results[~results["is_poland"]]
    pol_slope = float(pol["convergence_slope"].iloc[0]) if len(pol) else float("nan")
    comp_median = float(comp["convergence_slope"].median())
    diff = pol_slope - comp_median
    if pol_slope >= comp_median + DIFF_THRESHOLD:
        verdict = f"supported — Poland slope {pol_slope*100:+.2f}pp/yr vs median {comp_median*100:+.2f}pp/yr (diff {diff*100:+.2f}pp)."
    elif pol_slope <= comp_median:
        verdict = f"refuted — Poland slope {pol_slope*100:+.2f}pp/yr at or below median {comp_median*100:+.2f}pp/yr."
    else:
        verdict = f"partial — Poland slope {pol_slope*100:+.2f}pp/yr vs median {comp_median*100:+.2f}pp/yr (diff {diff*100:+.2f}pp)."
    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_comparators": int(len(comp)), "poland_slope": pol_slope, "comparator_median": comp_median, "diff": diff},
        "countries": rows, "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  pwt: {manifest['pwt']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nPoland vs {len(comp)} CEE comparators, endpoint slope {BASE_YEAR}-{END_YEAR}.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
