#!/usr/bin/env python3
"""Replication — Property rights and long-run income at the frontier, 1996-2018.

Spec: Property-rights protection predicts 40-year income growth more strongly than
state investment share.

Design:
  1. Broad panel 1996-2018 (WGI coverage window).
  2. WGI Rule of Law (RL.EST) as property-rights proxy.
  3. Maddison GDP-per-capita for income.
  4. TWFE: 5-year-forward log GDPpc growth on RL + controls.

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
HID = "property_rights_long_run_income_frontier"
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

    panel = rl.merge(madd, on=["country", "year"], how="inner")
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.dropna(subset=["rl", "gdppc"])
    panel["log_gdppc"] = np.log(panel["gdppc"])
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
    d = panel[["country", "year", "growth_5yr", "rl", "log_gdppc"]].copy()
    for col in ["growth_5yr", "rl", "log_gdppc"]:
        d[f"{col}_dm"] = d[col] - d.groupby("country")[col].transform("mean")
        d[f"{col}_dm"] = d[f"{col}_dm"] - d.groupby("year")[f"{col}_dm"].transform("mean")

    X = sm.add_constant(d[["rl_dm", "log_gdppc_dm"]])
    y = d["growth_5yr_dm"]
    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask]
    y = y[mask]

    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": d.loc[mask, "country"]})

    rl_coef = float(res.params["rl_dm"])
    rl_se = float(res.bse["rl_dm"])
    rl_p = float(res.pvalues["rl_dm"])
    rl_ci_lo, rl_ci_hi = res.conf_int().loc["rl_dm"].tolist()
    n_obs = int(res.nobs)
    r2 = float(res.rsquared)

    if rl_coef > 0 and rl_p < 0.05:
        verdict = (
            f"supported — TWFE β_RL={rl_coef:+.4f} (SE {rl_se:.4f}, p={rl_p:.3f}, n={n_obs}), "
            f"R²={r2:.3f}. Stronger rule of law predicts higher income growth."
        )
    elif rl_coef < 0 and rl_p < 0.05:
        verdict = (
            f"refuted — TWFE β_RL={rl_coef:+.4f} (SE {rl_se:.4f}, p={rl_p:.3f}, n={n_obs}) "
            f"is negative and significant."
        )
    else:
        verdict = (
            f"partial — TWFE β_RL={rl_coef:+.4f} (SE {rl_se:.4f}, p={rl_p:.3f}, n={n_obs}), "
            f"R²={r2:.3f}. Does not meet falsification threshold."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_observations": n_obs,
            "n_countries": int(panel["country"].nunique()),
            "rl_coef": rl_coef,
            "rl_se": rl_se,
            "rl_p": rl_p,
            "rl_ci_lo": rl_ci_lo,
            "rl_ci_hi": rl_ci_hi,
            "r2_within": r2,
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
        "vintages:\n"
        + "".join(f"  {k}: {v['vintage_file']}\n" for k, v in manifest.items())
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Broad panel {PERIOD[0]}-{PERIOD[1]}. Outcome: 5-year-forward annualised log GDP-per-capita
growth (Maddison). Treatment: WGI Rule of Law (`GOV_WGI_RL.EST`) as property-rights proxy.
Controls: log initial GDP per capita. Estimator: TWFE (country + year fixed effects),
clustered SE by country.

## Threshold

SUPPORTED if β_RL > 0 and p < 0.05.
REFUTED if β_RL < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | {n_obs} |
| Countries | {panel["country"].nunique()} |
| β_RL | {rl_coef:+.4f} |
| SE | {rl_se:.4f} |
| 95% CI | [{rl_ci_lo:+.4f}, {rl_ci_hi:+.4f}] |
| p-value | {rl_p:.3f} |
| R² within | {r2:.3f} |

## Limitations

- WGI Rule of Law is perception-based and includes dimensions beyond narrow
  property-rights security (e.g., contract enforcement, judicial independence).
- No direct control for state investment share as specified in the original hypothesis.
- 5-year-forward windows shrink sample at panel ends.
- TWFE with heterogeneous effects may be biased.

## Next robustness checks

- Control for WGI Government Effectiveness (state-capacity proxy).
- Use PWT instead of Maddison for GDP pc.
- Test with 10-year-forward growth windows.
- Add human-capital controls where available.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
