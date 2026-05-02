#!/usr/bin/env python3
"""Replication — Catch-up growth fades after middle-income threshold.

Spec: Developmentalist catch-up economies show faster growth before reaching
40 percent of US GDP per capita, but their growth premium shrinks or reverses
after crossing that threshold.

Design:
  1. Build PWT panel 1960-2019 (rgdpe per capita, constant 2017 USD).
  2. For each country-year, compute income_rel_us = GDPpc / US_GDPpc.
  3. Compute 5-year-forward annualised log growth.
  4. Compare mean growth for observations where income_rel_us < 0.40
     versus where income_rel_us >= 0.40.

Falsification:
  SUPPORTED if mean growth below_40 >= mean growth above_40 + 1.00 pp/yr
             AND the difference is significant at p < 0.05 (two-sided t-test).
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
import statsmodels.api as sm

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "catch_up_growth_fades_after_middle_income_threshold"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1960, 2019)
THRESHOLD_REL_US = 0.40
GROWTH_DIFF_THRESHOLD = 0.01  # 1 pp/yr


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
        "pwt_full": {
            "publisher": "pwt",
            "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pwt_path),
        },
    }

    t = pq.read_table(pwt_path).to_pandas()
    t = t[["country", "year", "rgdpe", "pop"]].copy()
    t = t.dropna(subset=["rgdpe", "pop"])
    t["year"] = t["year"].astype(int)
    t = t[(t["year"] >= PERIOD[0]) & (t["year"] <= PERIOD[1])]
    t["rgdpe_pc"] = t["rgdpe"] / t["pop"]
    t = t[t["rgdpe_pc"] > 0]

    # US GDP pc series
    us = t[t["country"] == "United States"][["year", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "us_rgdpe_pc"})
    panel = t.merge(us, on="year", how="inner")
    panel["rel_us"] = panel["rgdpe_pc"] / panel["us_rgdpe_pc"]
    panel["log_rgdpe_pc"] = np.log(panel["rgdpe_pc"])

    # 5-year-forward annualised growth
    panel = panel.sort_values(["country", "year"])
    panel["log_rgdpe_pc_t5"] = panel.groupby("country")["log_rgdpe_pc"].shift(-5)
    panel["growth_5yr_fwd"] = (panel["log_rgdpe_pc_t5"] - panel["log_rgdpe_pc"]) / 5.0
    panel = panel.dropna(subset=["growth_5yr_fwd"])

    # Below vs above threshold
    panel["below_40"] = panel["rel_us"] < THRESHOLD_REL_US
    below = panel[panel["below_40"]]
    above = panel[~panel["below_40"]]

    mean_below = float(below["growth_5yr_fwd"].mean()) if len(below) else 0.0
    mean_above = float(above["growth_5yr_fwd"].mean()) if len(above) else 0.0
    diff = mean_below - mean_above

    # T-test
    if len(below) > 1 and len(above) > 1:
        from scipy import stats
        tstat, pval = stats.ttest_ind(
            below["growth_5yr_fwd"].dropna().values,
            above["growth_5yr_fwd"].dropna().values,
            equal_var=False,
        )
        tstat = float(tstat)
        pval = float(pval)
    else:
        tstat = float("nan")
        pval = float("nan")

    # Verdict
    sig = pval < 0.05 if np.isfinite(pval) else False
    if mean_below >= mean_above + GROWTH_DIFF_THRESHOLD and sig:
        verdict = (
            f"supported — Below-{int(THRESHOLD_REL_US*100)}% growth {mean_below*100:+.2f}%/yr vs "
            f"above {mean_above*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
        )
    elif mean_below <= mean_above:
        verdict = (
            f"refuted — Below-threshold growth {mean_below*100:+.2f}%/yr not above "
            f"above-threshold {mean_above*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
        )
    else:
        verdict = (
            f"partial — Diff {diff*100:+.2f}pp below threshold ({GROWTH_DIFF_THRESHOLD*100:.0f}pp) "
            f"or not significant (p={pval:.3f})."
        )

    # Robustness: regression with spline
    panel["rel_us_clipped"] = panel["rel_us"].clip(upper=1.5)
    panel["spline_40"] = np.maximum(0, panel["rel_us"] - THRESHOLD_REL_US)
    X = sm.add_constant(panel[["rel_us", "spline_40"]])
    y = panel["growth_5yr_fwd"]
    reg = sm.OLS(y, X).fit(cov_type="HC3")
    spline_coef = float(reg.params["spline_40"])
    spline_p = float(reg.pvalues["spline_40"])

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_observations": int(len(panel)),
            "n_countries": int(panel["country"].nunique()),
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
        "vintages:\n"
        + "".join(f"  {k}: {v['vintage_file']}\n" for k, v in manifest.items())
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

PWT panel {PERIOD[0]}-{PERIOD[1]}. 5-year-forward annualised log GDP-per-capita growth
(RGDPE/pop). Split by income relative to US frontier in the base year of each growth
window (< {int(THRESHOLD_REL_US*100)}% vs ≥ {int(THRESHOLD_REL_US*100)}%).

## Threshold

SUPPORTED if mean growth below-threshold ≥ mean growth above-threshold + {GROWTH_DIFF_THRESHOLD*100:.0f}pp/yr
AND significant at p < 0.05. REFUTED if below-threshold growth ≤ above-threshold growth.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Country-year observations | {len(panel)} |
| Countries | {panel["country"].nunique()} |
| Below-{int(THRESHOLD_REL_US*100)}% observations | {len(below)} |
| Above-{int(THRESHOLD_REL_US*100)}% observations | {len(above)} |
| Mean growth below | {mean_below*100:+.2f}%/yr |
| Mean growth above | {mean_above*100:+.2f}%/yr |
| Difference | {diff*100:+.2f}pp/yr |
| t-statistic | {tstat:.2f} |
| p-value | {pval:.3f} |
| Spline at 40% coef | {spline_coef*100:+.2f}pp |
| Spline p-value | {spline_p:.3f} |

## Robustness

Linear spline regression: growth = β0 + β1·rel_us + β2·max(0, rel_us − 0.40).
β2 = {spline_coef*100:+.2f}pp (p={spline_p:.3f}). Positive β2 would mean growth is *higher* above the
threshold after controlling for level; negative β2 supports fading catch-up.

## Limitations

- Cross-country comparison, not within-country crossing of the threshold.
- 5-year-forward windows shrink sample at panel ends.
- Relative-to-US threshold conflates domestic growth with US slowdowns.
- No controls for initial human capital, institutions, or commodity cycles.

## Next robustness checks

- Use 10-year-forward growth windows.
- Control for country fixed effects (within-estimator).
- Test alternative thresholds (30%, 50% of US).
- Use Maddison instead of PWT for longer historical coverage.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
