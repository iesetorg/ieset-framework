#!/usr/bin/env python3
"""Replication — Product market regulation and TFP growth, 30-year panel 1990-2019.

Spec: Lower product-market regulation predicts higher long-run TFP growth after
controlling for education, capital deepening, and initial income.

Design:
  1. Broad panel 1990-2019.
  2. PWT TFP (rtfpna) and human capital (hc), capital stock (rkna / pop).
  3. Market-regulation proxy: WGI Regulatory Quality (RQ.EST) — higher = less
     intrusive regulation, conceptually linked to lower PMR.
  4. TWFE: 5-year-forward TFP growth on RQ + log initial TFP + hc + log capital
     per worker + year and country FE.

Falsification:
  SUPPORTED if β_RQ > 0 and p < 0.05.
  REFUTED if β_RQ < 0 and p < 0.05.
  Otherwise PARTIAL.

Note: OECD PMR or Fraser EFW would be sharper proxies but are not available in
local vintages; WGI RQ is used with this limitation flagged.
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
HID = "product_market_regulation_tfp_30yr_panel"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1990, 2019)


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

    rq_path = latest("wgi", "GOV_WGI_RQ.EST")
    pwt_path = latest("pwt", "pwt_full")

    manifest = {
        "wgi_rq": {
            "publisher": "wgi", "series": "GOV_WGI_RQ.EST",
            "vintage_file": str(rq_path.relative_to(REPO_ROOT)), "sha256": sha256(rq_path),
        },
        "pwt": {
            "publisher": "pwt", "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path),
        },
    }

    rq = load_long(rq_path, "rq")
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rtfpna", "hc", "rkna", "pop", "rgdpe"]].copy()
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.dropna(subset=["rtfpna", "pop"])
    pwt["capital_per_worker"] = pwt["rkna"] / pwt["pop"]
    pwt["log_tfp"] = np.log(pwt["rtfpna"])
    pwt["log_cap_worker"] = np.log(pwt["capital_per_worker"])
    pwt["log_gdp_pc"] = np.log(pwt["rgdpe"] / pwt["pop"])

    panel = rq.merge(pwt, on=["country", "year"], how="inner")
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.dropna(subset=["rq", "log_tfp", "hc", "log_cap_worker"])
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    # 5-year-forward TFP growth
    panel["log_tfp_t5"] = panel.groupby("country")["log_tfp"].shift(-5)
    panel["tfp_growth_5yr"] = (panel["log_tfp_t5"] - panel["log_tfp"]) / 5.0
    panel = panel.dropna(subset=["tfp_growth_5yr"])

    if len(panel) < 100:
        verdict = "blocked_data_pending — insufficient panel observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_observations": int(len(panel))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # TWFE via within demeaning
    cols = ["tfp_growth_5yr", "rq", "log_tfp", "hc", "log_cap_worker", "log_gdp_pc"]
    d = panel[["country", "year"] + cols].copy()
    for col in cols:
        d[f"{col}_dm"] = d[col] - d.groupby("country")[col].transform("mean")
        d[f"{col}_dm"] = d[f"{col}_dm"] - d.groupby("year")[f"{col}_dm"].transform("mean")

    X_vars = [f"{c}_dm" for c in cols if c != "tfp_growth_5yr"]
    X = sm.add_constant(d[X_vars])
    y = d["tfp_growth_5yr_dm"]
    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask]
    y = y[mask]

    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": d.loc[mask, "country"]})

    rq_coef = float(res.params["rq_dm"])
    rq_se = float(res.bse["rq_dm"])
    rq_p = float(res.pvalues["rq_dm"])
    rq_ci_lo, rq_ci_hi = res.conf_int().loc["rq_dm"].tolist()
    n_obs = int(res.nobs)
    r2 = float(res.rsquared)

    if rq_coef > 0 and rq_p < 0.05:
        verdict = (
            f"supported — TWFE β_RQ={rq_coef:+.4f} (SE {rq_se:.4f}, p={rq_p:.3f}, n={n_obs}), "
            f"R²={r2:.3f}. Higher regulatory quality predicts stronger TFP growth controlling for "
            f"human capital and capital per worker."
        )
    elif rq_coef < 0 and rq_p < 0.05:
        verdict = (
            f"refuted — TWFE β_RQ={rq_coef:+.4f} (SE {rq_se:.4f}, p={rq_p:.3f}, n={n_obs}) "
            f"is negative and significant."
        )
    else:
        verdict = (
            f"partial — TWFE β_RQ={rq_coef:+.4f} (SE {rq_se:.4f}, p={rq_p:.3f}, n={n_obs}), "
            f"R²={r2:.3f}. Does not meet falsification threshold."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_observations": n_obs,
            "n_countries": int(panel["country"].nunique()),
            "rq_coef": rq_coef,
            "rq_se": rq_se,
            "rq_p": rq_p,
            "rq_ci_lo": rq_ci_lo,
            "rq_ci_hi": rq_ci_hi,
            "r2_within": r2,
        },
        "threshold": "β_RQ > 0 and p < 0.05",
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

Broad panel {PERIOD[0]}-{PERIOD[1]}. Outcome: 5-year-forward annualised log TFP growth
(PWT `rtfpna`). Treatment: WGI Regulatory Quality (`GOV_WGI_RQ.EST`) as proxy for
low product-market regulation / state interference. Controls: log initial TFP,
human capital (`hc`), log capital per worker, log GDP per capita. Estimator:
TWFE with country and year fixed effects, clustered SE by country.

## Threshold

SUPPORTED if β_RQ > 0 and p < 0.05.
REFUTED if β_RQ < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | {n_obs} |
| Countries | {panel["country"].nunique()} |
| β_RQ | {rq_coef:+.4f} |
| SE | {rq_se:.4f} |
| 95% CI | [{rq_ci_lo:+.4f}, {rq_ci_hi:+.4f}] |
| p-value | {rq_p:.3f} |
| R² within | {r2:.3f} |

## Limitations

- WGI Regulatory Quality is a governance perception index, not a direct
  product-market-regulation measure. OECD PMR or Fraser EFW would be sharper.
- PWT TFP is a residual and sensitive to measurement assumptions.
- TWFE with heterogeneous treatment effects may bias estimates.
- Human capital (`hc`) is based on years-of-schooling returns, not quality-adjusted.

## Next robustness checks

- Re-run with OECD-only sample.
- Use 10-year-forward TFP growth.
- Add country-specific time trends.
- Test alternative proxies (WGI Rule of Law, V-Dem liberal component).
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
