#!/usr/bin/env python3
"""Replication v2 — Catch-up growth fades after middle-income threshold (robustness).

Methodology note: This v2 uses Maddison GDP-per-capita (longer historical coverage)
and 10-year-forward growth windows instead of PWT RGDPE and 5-year windows. It is a
robustness check for the v1 replication which returned PARTIAL with a +0.38pp diff.

Design:
  1. Maddison panel 1960-2018.
  2. 10-year-forward annualised log growth.
  3. Compare mean growth for observations where income_rel_us < 0.40 vs >= 0.40.

Falsification:
  SUPPORTED if mean growth below_40 >= mean growth above_40 + 1.00 pp/yr
             AND p < 0.05.
  REFUTED if mean growth below_40 <= mean growth above_40.
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
HID = "catch_up_growth_fades_after_middle_income_threshold_v2"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1960, 2018)
THRESHOLD_REL_US = 0.40
GROWTH_DIFF_THRESHOLD = 0.01


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

    madd_path = latest("maddison", "gdppc")
    manifest = {
        "maddison_gdppc": {
            "publisher": "maddison", "series": "gdppc",
            "vintage_file": str(madd_path.relative_to(REPO_ROOT)), "sha256": sha256(madd_path),
        },
    }

    madd = pq.read_table(madd_path).to_pandas()
    madd = madd[(madd["country_iso3"].notna()) & (madd["country_iso3"].str.len() == 3)]
    madd = madd[["country_iso3", "year", "gdppc"]].copy()
    madd["year"] = madd["year"].astype(int)
    madd = madd[(madd["year"] >= PERIOD[0]) & (madd["year"] <= PERIOD[1])]
    madd = madd[(madd["gdppc"].notna()) & (madd["gdppc"] > 0)]

    # US GDP pc
    us = madd[madd["country_iso3"] == "USA"][["year", "gdppc"]].rename(columns={"gdppc": "us_gdppc"})
    panel = madd.merge(us, on="year", how="inner")
    panel["rel_us"] = panel["gdppc"] / panel["us_gdppc"]
    panel["log_gdppc"] = np.log(panel["gdppc"])
    panel = panel.sort_values(["country_iso3", "year"])

    # 10-year-forward growth
    panel["log_gdppc_t10"] = panel.groupby("country_iso3")["log_gdppc"].shift(-10)
    panel["growth_10yr"] = (panel["log_gdppc_t10"] - panel["log_gdppc"]) / 10.0
    panel = panel.dropna(subset=["growth_10yr"])

    panel["below_40"] = panel["rel_us"] < THRESHOLD_REL_US
    below = panel[panel["below_40"]]
    above = panel[~panel["below_40"]]

    mean_below = float(below["growth_10yr"].mean()) if len(below) else 0.0
    mean_above = float(above["growth_10yr"].mean()) if len(above) else 0.0
    diff = mean_below - mean_above

    if len(below) > 1 and len(above) > 1:
        tstat, pval = stats.ttest_ind(below["growth_10yr"].dropna().values, above["growth_10yr"].dropna().values, equal_var=False)
        tstat = float(tstat)
        pval = float(pval)
    else:
        tstat = float("nan")
        pval = float("nan")

    sig = pval < 0.05 if np.isfinite(pval) else False
    if mean_below >= mean_above + GROWTH_DIFF_THRESHOLD and sig:
        verdict = f"supported — Below-threshold growth {mean_below*100:+.2f}%/yr vs above {mean_above*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
    elif mean_below <= mean_above:
        verdict = f"refuted — Below-threshold growth {mean_below*100:+.2f}%/yr not above above-threshold {mean_above*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
    else:
        verdict = f"partial — Diff {diff*100:+.2f}pp below threshold ({GROWTH_DIFF_THRESHOLD*100:.0f}pp) or not significant (p={pval:.3f})."

    # Spline regression
    panel["spline_40"] = np.maximum(0, panel["rel_us"] - THRESHOLD_REL_US)
    import statsmodels.api as sm
    X = sm.add_constant(panel[["rel_us", "spline_40"]])
    y = panel["growth_10yr"]
    reg = sm.OLS(y, X).fit(cov_type="HC3")
    spline_coef = float(reg.params["spline_40"])
    spline_p = float(reg.pvalues["spline_40"])

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "methodology_note": "v2 robustness: Maddison GDPpc + 10-year-forward growth (v1 used PWT RGDPE + 5-year).",
        "metrics": {
            "n_observations": int(len(panel)),
            "n_countries": int(panel["country_iso3"].nunique()),
            "n_below_40": int(len(below)),
            "n_above_40": int(len(above)),
            "mean_growth_below_40": mean_below,
            "mean_growth_above_40": mean_above,
            "growth_diff": diff,
            "t_stat": tstat,
            "p_value": pval,
            "spline_40_coef": spline_coef,
            "spline_40_p": spline_p,
        },
        "threshold": f"mean_below >= mean_above + {GROWTH_DIFF_THRESHOLD*100:.0f}pp and p < 0.05",
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
        "sha256": {k: v["sha256"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict.split(' — ')[0]}\n"
        f"reason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\n"
        "methodology_note: v2 robustness using Maddison + 10-year windows\n"
        "vintages:\n"
        + "".join(f"  {k}: {v['vintage_file']}\n" for k, v in manifest.items())
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Maddison panel {PERIOD[0]}-{PERIOD[1]}. 10-year-forward annualised log GDP-per-capita growth.
Split by income relative to US frontier (< {int(THRESHOLD_REL_US*100)}% vs ≥ {int(THRESHOLD_REL_US*100)}%).

## Methodology Note

This is a v2 robustness check for `catch_up_growth_fades_after_middle_income_threshold`.
v1 used PWT RGDPE + 5-year-forward growth and found PARTIAL (+0.38pp diff, p<0.001).
v2 uses Maddison (longer coverage, different PPP base) + 10-year windows to test
sensitivity to data source and growth horizon.

## Metrics

| Metric | Value |
|---|---|
| Observations | {len(panel)} |
| Countries | {panel["country_iso3"].nunique()} |
| Mean growth below | {mean_below*100:+.2f}%/yr |
| Mean growth above | {mean_above*100:+.2f}%/yr |
| Difference | {diff*100:+.2f}pp/yr |
| p-value | {pval:.3f} |
| Spline coef | {spline_coef*100:+.2f}pp |

## Interpretation

See v1 result card for primary interpretation. This v2 tests whether the
partial verdict is sensitive to data source (Maddison vs PWT) and growth
horizon (10-year vs 5-year).
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
