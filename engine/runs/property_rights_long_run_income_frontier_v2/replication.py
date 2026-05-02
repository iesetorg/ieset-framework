#!/usr/bin/env python3
"""Replication v2 — Property rights and long-run income at the frontier (robustness).

Methodology note: This v2 uses a cross-sectional regression of country-mean
annual growth 1996-2018 on country-mean WGI Rule of Law, instead of the TWFE
panel in v1. v1 returned PARTIAL (β_RL=+0.0048, p=0.277, n=2474).

Design:
  1. Broad cross-section 1996-2018.
  2. Country-mean WGI RL.EST vs country-mean annual log GDPpc growth (Maddison).
  3. OLS with HC3 standard errors.

Falsification:
  SUPPORTED if β_RL > 0 and p < 0.05.
  REFUTED if β_RL < 0 and p < 0.05.
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
HID = "property_rights_long_run_income_frontier_v2"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1996, 2018)


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

    rl_path = latest("wgi", "GOV_WGI_RL.EST")
    madd_path = latest("maddison", "gdppc")

    manifest = {
        "wgi_rl": {
            "publisher": "wgi", "series": "GOV_WGI_RL.EST",
            "vintage_file": str(rl_path.relative_to(REPO_ROOT)), "sha256": sha256(rl_path),
        },
        "maddison_gdppc": {
            "publisher": "maddison", "series": "gdppc",
            "vintage_file": str(madd_path.relative_to(REPO_ROOT)), "sha256": sha256(madd_path),
        },
    }

    rl = load_long(rl_path, "rl")
    madd = pq.read_table(madd_path).to_pandas()
    madd = madd[(madd["country_iso3"].notna()) & (madd["country_iso3"].str.len() == 3)]
    madd = madd[["country_iso3", "year", "gdppc"]].rename(columns={"country_iso3": "country"})
    madd["year"] = madd["year"].astype(int)
    madd = madd[(madd["gdppc"].notna()) & (madd["gdppc"] > 0)]

    panel = rl.merge(madd, on=["country", "year"], how="inner")
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.dropna(subset=["rl", "gdppc"])
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)
    panel["log_gdppc"] = np.log(panel["gdppc"])
    panel["growth_yoy"] = panel.groupby("country")["log_gdppc"].diff()

    # Country means
    means = panel.groupby("country").agg(
        rl_mean=("rl", "mean"),
        growth_mean=("growth_yoy", "mean"),
        log_gdp_initial=("log_gdppc", "first"),
    ).dropna()

    if len(means) < 15:
        verdict = "blocked_data_pending — insufficient countries for cross-section."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(means))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    X = sm.add_constant(means[["rl_mean", "log_gdp_initial"]])
    y = means["growth_mean"]
    res = sm.OLS(y, X).fit(cov_type="HC3")

    rl_coef = float(res.params["rl_mean"])
    rl_se = float(res.bse["rl_mean"])
    rl_p = float(res.pvalues["rl_mean"])
    rl_ci_lo, rl_ci_hi = res.conf_int().loc["rl_mean"].tolist()
    n_obs = int(res.nobs)
    r2 = float(res.rsquared)

    if rl_coef > 0 and rl_p < 0.05:
        verdict = f"supported — Cross-section β_RL={rl_coef:+.4f} (SE {rl_se:.4f}, p={rl_p:.3f}, n={n_obs}), R²={r2:.3f}."
    elif rl_coef < 0 and rl_p < 0.05:
        verdict = f"refuted — Cross-section β_RL={rl_coef:+.4f} (SE {rl_se:.4f}, p={rl_p:.3f}, n={n_obs}) negative and significant."
    else:
        verdict = f"partial — Cross-section β_RL={rl_coef:+.4f} (SE {rl_se:.4f}, p={rl_p:.3f}, n={n_obs}), R²={r2:.3f}."

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "methodology_note": "v2 robustness: cross-sectional country-mean regression 1996-2018 (v1 used TWFE panel with 5-year-forward growth).",
        "metrics": {
            "n_countries": n_obs,
            "rl_coef": rl_coef,
            "rl_se": rl_se,
            "rl_p": rl_p,
            "rl_ci_lo": rl_ci_lo,
            "rl_ci_hi": rl_ci_hi,
            "r2": r2,
        },
        "threshold": "β_RL > 0 and p < 0.05",
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
        "sha256": {k: v["sha256"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict.split(' — ')[0]}\n"
        f"reason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\n"
        "methodology_note: v2 robustness using cross-sectional country-means\n"
        "vintages:\n"
        + "".join(f"  {k}: {v['vintage_file']}\n" for k, v in manifest.items())
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Cross-section of {n_obs} countries, {PERIOD[0]}-{PERIOD[1]}. Outcome: mean annual
log GDP-per-capita growth (Maddison). Treatment: mean WGI Rule of Law.
Control: log initial GDP per capita. Estimator: OLS with HC3 SEs.

## Methodology Note

This is a v2 robustness check for `property_rights_long_run_income_frontier`.
v1 used TWFE panel with 5-year-forward growth and found PARTIAL (β=+0.0048, p=0.277).
v2 uses a country-mean cross-section to test whether the panel result is driven
by within-country vs between-country variation.

## Metrics

| Metric | Value |
|---|---|
| Countries | {n_obs} |
| β_RL | {rl_coef:+.4f} |
| SE | {rl_se:.4f} |
| 95% CI | [{rl_ci_lo:+.4f}, {rl_ci_hi:+.4f}] |
| p-value | {rl_p:.3f} |
| R² | {r2:.3f} |

## Interpretation

See v1 result card for primary interpretation. This v2 tests whether the
partial TWFE panel result reflects weak between-country association.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
