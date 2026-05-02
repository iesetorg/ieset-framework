#!/usr/bin/env python3
"""Replication — Trade openness and long-run income convergence, 1960-2019.

Spec: Trade openness predicts long-run GDP-per-capita convergence more strongly than
industrial-policy intensity.

Design:
  1. Broad panel 1960-2019.
  2. WDI trade openness (NE.TRD.GNFS.ZS, % of GDP).
  3. PWT RGDPE per capita for income and growth.
  4. TWFE: 5-year-forward log GDPpc growth on trade openness + controls.

Falsification:
  SUPPORTED if β_trade > 0 and p < 0.05.
  REFUTED if β_trade < 0 and p < 0.05.
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
HID = "trade_openness_long_run_income_convergence"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1960, 2019)


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

    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    pwt_path = latest("pwt", "pwt_full")

    manifest = {
        "wdi_trade": {
            "publisher": "world_bank_wdi", "series": "NE.TRD.GNFS.ZS",
            "vintage_file": str(trade_path.relative_to(REPO_ROOT)), "sha256": sha256(trade_path),
        },
        "pwt": {
            "publisher": "pwt", "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path),
        },
    }

    trade = load_long(trade_path, "trade_gdp")
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]
    pwt["log_gdppc"] = np.log(pwt["rgdpe_pc"])

    panel = trade.merge(pwt, on=["country", "year"], how="inner")
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.dropna(subset=["trade_gdp", "log_gdppc"])
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    # 5-year-forward growth
    panel["log_gdppc_t5"] = panel.groupby("country")["log_gdppc"].shift(-5)
    panel["growth_5yr"] = (panel["log_gdppc_t5"] - panel["log_gdppc"]) / 5.0
    panel = panel.dropna(subset=["growth_5yr"])

    if len(panel) < 100:
        verdict = "blocked_data_pending — insufficient panel observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_observations": int(len(panel))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # TWFE via within demeaning
    d = panel[["country", "year", "growth_5yr", "trade_gdp", "log_gdppc"]].copy()
    for col in ["growth_5yr", "trade_gdp", "log_gdppc"]:
        d[f"{col}_dm"] = d[col] - d.groupby("country")[col].transform("mean")
        d[f"{col}_dm"] = d[f"{col}_dm"] - d.groupby("year")[f"{col}_dm"].transform("mean")

    X = sm.add_constant(d[["trade_gdp_dm", "log_gdppc_dm"]])
    y = d["growth_5yr_dm"]
    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask]
    y = y[mask]

    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": d.loc[mask, "country"]})

    tr_coef = float(res.params["trade_gdp_dm"])
    tr_se = float(res.bse["trade_gdp_dm"])
    tr_p = float(res.pvalues["trade_gdp_dm"])
    tr_ci_lo, tr_ci_hi = res.conf_int().loc["trade_gdp_dm"].tolist()
    n_obs = int(res.nobs)
    r2 = float(res.rsquared)

    if tr_coef > 0 and tr_p < 0.05:
        verdict = (
            f"supported — TWFE β_trade={tr_coef:+.6f} (SE {tr_se:.6f}, p={tr_p:.3f}, n={n_obs}), "
            f"R²={r2:.3f}. Higher trade openness predicts stronger income growth."
        )
    elif tr_coef < 0 and tr_p < 0.05:
        verdict = (
            f"refuted — TWFE β_trade={tr_coef:+.6f} (SE {tr_se:.6f}, p={tr_p:.3f}, n={n_obs}) "
            f"is negative and significant."
        )
    else:
        verdict = (
            f"partial — TWFE β_trade={tr_coef:+.6f} (SE {tr_se:.6f}, p={tr_p:.3f}, n={n_obs}), "
            f"R²={r2:.3f}. Does not meet falsification threshold."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_observations": n_obs,
            "n_countries": int(panel["country"].nunique()),
            "trade_coef": tr_coef,
            "trade_se": tr_se,
            "trade_p": tr_p,
            "trade_ci_lo": tr_ci_lo,
            "trade_ci_hi": tr_ci_hi,
            "r2_within": r2,
        },
        "threshold": "β_trade > 0 and p < 0.05",
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

Broad panel {PERIOD[0]}-{PERIOD[1]}. Outcome: 5-year-forward annualised log GDP-per-capita
growth (PWT RGDPE). Treatment: WDI trade openness (`NE.TRD.GNFS.ZS`, % of GDP).
Controls: log initial GDP per capita. Estimator: TWFE (country + year fixed effects),
clustered SE by country.

## Threshold

SUPPORTED if β_trade > 0 and p < 0.05.
REFUTED if β_trade < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | {n_obs} |
| Countries | {panel["country"].nunique()} |
| β_trade | {tr_coef:+.6f} |
| SE | {tr_se:.6f} |
| 95% CI | [{tr_ci_lo:+.6f}, {tr_ci_hi:+.6f}] |
| p-value | {tr_p:.3f} |
| R² within | {r2:.3f} |

## Limitations

- Trade/GDP is a crude openness measure that includes re-exports and can be
  inflated for small, entrepôt economies.
- No direct industrial-policy intensity measure for the comparison claimed in
  the original hypothesis.
- Reverse causality: faster-growing countries may import more as a share of GDP.
- TWFE assumptions may be violated with heterogeneous treatment effects.

## Next robustness checks

- Use tariff-weighted openness or WITS trade data where available.
- Instrument with geographic trade-propensity (Frankel-Romer).
- Test with 10-year-forward growth windows.
- Control for institutional quality and human capital.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
