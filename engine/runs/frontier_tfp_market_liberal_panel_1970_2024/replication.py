#!/usr/bin/env python3
"""Replication — Frontier TFP and market liberalisation panel, 1970-2019.

Spec: Among OECD and high-income Asian economies, long-run TFP growth is higher where
product-market regulation and state ownership are lower.

Design:
  1. OECD + high-income Asian panel, 1970-2019.
  2. TFP from PWT (rtfpna).
  3. Market-liberal proxy: WGI Regulatory Quality (RQ.EST) — higher = better
     regulation, less state interference.
  4. TWFE panel: 5-year-forward TFP growth on RQ + log initial TFP + log GDPpc + FE.

Falsification:
  SUPPORTED if β_RQ > 0 and p < 0.05 in primary TWFE.
  REFUTED if β_RQ < 0 and p < 0.05.
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
HID = "frontier_tfp_market_liberal_panel_1970_2024"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1970, 2019)

# OECD + high-income Asian sample
COUNTRIES = [
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "CZE", "DEU", "DNK", "ESP",
    "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL", "ISR", "ITA",
    "JPN", "KOR", "LTU", "LUX", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "SVK", "SVN", "SWE", "TUR", "USA",
    "HKG", "SGP", "TWN",  # high-income Asian
]


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

    paths = {
        "wgi_rq": ("wgi", "GOV_WGI_RQ.EST"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths.items():
        p = latest(pub, series)
        manifest[v] = {"publisher": pub, "series": series,
                       "vintage_file": str(p.relative_to(REPO_ROOT)), "sha256": sha256(p)}
        frames.append(load_long(p, v))

    # PWT TFP and GDP
    pwt_path = latest("pwt", "pwt_full")
    manifest["pwt"] = {"publisher": "pwt", "series": "pwt_full",
                       "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path)}
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rtfpna", "rgdpe", "pop"]].copy()
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.dropna(subset=["rtfpna", "rgdpe", "pop"])
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]
    pwt["log_tfp"] = np.log(pwt["rtfpna"])
    pwt["log_gdp_pc"] = np.log(pwt["rgdpe_pc"])
    pwt = pwt[pwt["country"].isin(COUNTRIES)]
    pwt = pwt[(pwt["year"] >= PERIOD[0]) & (pwt["year"] <= PERIOD[1])]

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")

    panel = panel.merge(pwt, on=["country", "year"], how="inner")
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    # 5-year-forward TFP growth
    panel["log_tfp_t5"] = panel.groupby("country")["log_tfp"].shift(-5)
    panel["tfp_growth_5yr"] = (panel["log_tfp_t5"] - panel["log_tfp"]) / 5.0
    panel = panel.dropna(subset=["tfp_growth_5yr", "wgi_rq", "log_tfp", "log_gdp_pc"])

    if len(panel) < 50:
        verdict = "blocked_data_pending — insufficient panel observations after merges."
        diagnostics = {
            "hypothesis_id": HID, "verdict": verdict,
            "n_observations": int(len(panel)),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # TWFE via within demeaning
    d = panel[["country", "year", "tfp_growth_5yr", "wgi_rq", "log_tfp", "log_gdp_pc"]].copy()
    for col in ["tfp_growth_5yr", "wgi_rq", "log_tfp", "log_gdp_pc"]:
        d[f"{col}_dm"] = d[col] - d.groupby("country")[col].transform("mean")
        d[f"{col}_dm"] = d[f"{col}_dm"] - d.groupby("year")[f"{col}_dm"].transform("mean")

    X = sm.add_constant(d[["wgi_rq_dm", "log_tfp_dm", "log_gdp_pc_dm"]])
    y = d["tfp_growth_5yr_dm"]
    # Drop any perfectly collinear dummies / NaN
    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask]
    y = y[mask]

    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": d.loc[mask, "country"]})

    rq_coef = float(res.params["wgi_rq_dm"])
    rq_se = float(res.bse["wgi_rq_dm"])
    rq_p = float(res.pvalues["wgi_rq_dm"])
    rq_ci_lo, rq_ci_hi = res.conf_int().loc["wgi_rq_dm"].tolist()

    n_obs = int(res.nobs)
    r2 = float(res.rsquared)

    if rq_coef > 0 and rq_p < 0.05:
        verdict = (
            f"supported — TWFE β_RQ={rq_coef:+.4f} (SE {rq_se:.4f}, p={rq_p:.3f}, "
            f"n={n_obs}), R²_within={r2:.3f}. Higher regulatory quality predicts stronger TFP growth."
        )
    elif rq_coef < 0 and rq_p < 0.05:
        verdict = (
            f"refuted — TWFE β_RQ={rq_coef:+.4f} (SE {rq_se:.4f}, p={rq_p:.3f}, "
            f"n={n_obs}) is negative and significant."
        )
    else:
        verdict = (
            f"partial — TWFE β_RQ={rq_coef:+.4f} (SE {rq_se:.4f}, p={rq_p:.3f}, "
            f"n={n_obs}), R²_within={r2:.3f}. Does not meet falsification threshold."
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

OECD + high-income Asian panel {PERIOD[0]}-{PERIOD[1]}. Outcome: 5-year-forward
annualised log TFP growth (PWT `rtfpna`). Treatment: WGI Regulatory Quality
(`GOV_WGI_RQ.EST`) as proxy for market liberalisation / low state interference.
Controls: log initial TFP, log GDP per capita. Estimator: TWFE with country and
year fixed effects, clustered SE by country.

## Threshold

SUPPORTED if β_RQ > 0 and p < 0.05 in primary TWFE.
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

- WGI Regulatory Quality is a perception-based governance indicator, not a direct
  product-market-regulation or state-ownership measure.
- OECD PMR or Fraser EFW would be sharper proxies but are not available in local
  vintages.
- TWFE with staggered adoption and heterogeneous treatment effects may bias
  estimates (Goodman-Bacon 2021).
- 5-year-forward windows shrink sample at panel ends.

## Next robustness checks

- Re-run with 10-year-forward growth.
- Add country-specific time trends.
- Use alternative institution proxies (WGI Rule of Law, V-Dem liberal component).
- Restrict to post-1990 panel where WGI coverage is denser.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
