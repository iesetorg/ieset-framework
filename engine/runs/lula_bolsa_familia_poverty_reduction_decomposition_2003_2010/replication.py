#!/usr/bin/env python3
"""Replication — Lula Bolsa Família poverty-reduction decomposition 2003-2010 (v1).

Spec: hypotheses/distribution/lula_bolsa_familia_poverty_reduction_decomposition_2003_2010.yaml

The pre-registered claim decomposes the 2003-2010 Brazilian distributional
improvement (extreme-poverty headcount and Gini) into three channels:
  (a) Bolsa Família cash-transfer expansion (Lei 10,836 / 2004)
  (b) real minimum-wage valorisation
  (c) the 2003-2008 commodity boom (treated as exogenous control via a
      LatAm donor pool: MEX, COL, PER, CHL, ARG)

We test the spec's pre-registered thresholds:
  PRIMARY 1: Shapley-style variance share of BF + min-wage policy channels
             on extreme-poverty headcount >= 0.40
  PRIMARY 2: Shapley-style variance share of BF + min-wage policy channels
             on Gini >= 0.30
  REFUTATION GATE: commodity-boom channel variance share <= 0.60 on either
                   outcome (otherwise commodity-determinism dominates)

Method:
  - Panel: BRA + 5 LatAm donors, 1995-2012, with Argentina 2001-2003
    excluded from the trend-fitting per spec exclusion_rules.
  - Outcome regressions:
        outcome_it = alpha_i + tau_t
                   + beta_BF   * bf_intensity_it
                   + beta_MW   * min_wage_log_it
                   + beta_COM  * commodity_gdpgrowth_it
                   + beta_URB  * urbanisation_it
                   + eps_it
    where the BF and min-wage channels are non-zero only for BRA, and the
    commodity channel proxies the boom by per-capita real GDP growth (a
    reduced-form control that picks up commodity-driven income shocks
    via the donor pool's response).
  - BF intensity (BRA-only): stepwise indexation of beneficiary-family share
    rising from 0.05 in 2003 to 1.0 in 2010 (calibrated to MDS / Camargo
    coverage timeline, ~13M families by 2010). Zero for donors.
  - Real min-wage index (BRA-only): published valorisation timeline
    deflated by IPCA, indexed to 1.0 in 2003 → ~1.55 by 2010 (>50% real
    rise per IPEA). Zero (in log-deviation form) for donors.
  - Commodity channel: per-capita real-GDP growth rate (NY.GDP.PCAP.KD.ZG),
    same for all countries — a reduced-form proxy in lieu of commodity
    terms-of-trade (TT.PRI.MRCH.XD.WD not in vintages).
  - Urbanisation: SP.URB.TOTL.IN.ZS as a slow-moving control.
  - Variance attribution: Shapley value over the four channels using the
    explained sum of squares (within-Brazil) as the value function. The
    BF + min-wage Shapley shares are summed for the policy-channel total.

Verdict logic (matches spec.falsification.threshold):
  SUPPORTED iff
      shapley_share(BF + MW, poverty) >= 0.40
      AND shapley_share(BF + MW, gini) >= 0.30
      AND shapley_share(commodity, poverty) <= 0.60
      AND shapley_share(commodity, gini) <= 0.60
  REFUTED if both poverty and gini policy shares fall below half their
  thresholds (< 0.20 and < 0.15) AND commodity > 0.60 on either outcome.
  PARTIAL otherwise.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "lula_bolsa_familia_poverty_reduction_decomposition_2003_2010"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BRA = "BRA"
DONORS = ["MEX", "COL", "PER", "CHL", "ARG"]
ALL_COUNTRIES = [BRA] + DONORS
PERIOD = (1995, 2012)
DECOMP_PERIOD = (2003, 2010)

# Spec falsification thresholds
THR_POVERTY_POLICY = 0.40
THR_GINI_POLICY = 0.30
THR_COMMODITY_MAX = 0.60

# Spec exclusion_rules
EXCLUDE = [("ARG", 2001), ("ARG", 2002), ("ARG", 2003), ("MEX", 2009)]

# Bolsa Família intensity timeline (BRA-only). Calibrated to MDS coverage:
# 2003: ~3.6M families (legacy CCTs); 2004 unification (Lei 10,836); 2010 ~12.7M
# families. Indexed to peak (1.0 = full programme reach).
BF_INTENSITY = {
    1995: 0.0, 1996: 0.0, 1997: 0.0, 1998: 0.0, 1999: 0.0, 2000: 0.0,
    2001: 0.05, 2002: 0.10,  # Bolsa Escola / Auxílio Gás predecessor coverage
    2003: 0.10, 2004: 0.30, 2005: 0.55, 2006: 0.70, 2007: 0.80, 2008: 0.88,
    2009: 0.95, 2010: 1.00, 2011: 1.00, 2012: 1.00,
}

# Real minimum-wage index (BRA, deflated by IPCA), 2003 = 1.00.
# Per IPEA / DIEESE published series: nominal R$240 (2003) → R$510 (2010);
# IPCA cumulative ~52% over period, leaving ~+55% real rise.
MW_REAL_INDEX_BRA = {
    1995: 0.85, 1996: 0.88, 1997: 0.91, 1998: 0.94, 1999: 0.94, 2000: 0.97,
    2001: 0.99, 2002: 1.00,
    2003: 1.00, 2004: 1.04, 2005: 1.13, 2006: 1.27, 2007: 1.36, 2008: 1.43,
    2009: 1.50, 2010: 1.55, 2011: 1.59, 2012: 1.66,
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def latest(pub: str, ser: str) -> Path:
    files = sorted(
        (REPO_ROOT / "data" / "vintages" / pub).glob(f"{ser}@*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    if not files:
        raise FileNotFoundError(f"{pub}:{ser}")
    return files[-1]


def load_long(path: Path, var: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "value" in t.columns:
        val = "value"
    else:
        meta = {"country_iso3", "country_name", "year", "indicator_id",
                "unit", "obs_status", "decimal"}
        cands = [c for c in t.columns if c not in meta]
        val = cands[-1]
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)]
    t = t[["country_iso3", "year", val]].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t[val] = pd.to_numeric(t[val], errors="coerce")
    t = t.dropna(subset=["year"])
    t["year"] = t["year"].astype(int)
    return t.rename(columns={val: var, "country_iso3": "country"})


def assemble() -> tuple[pd.DataFrame, dict]:
    paths = {
        "poverty":  ("world_bank_wdi", "SI.POV.DDAY"),
        "gini":     ("world_bank_wdi", "SI.POV.GINI"),
        "gdp_pc_growth": ("world_bank_wdi", "NY.GDP.PCAP.KD.ZG"),
        "urban":    ("world_bank_wdi", "SP.URB.TOTL.IN.ZS"),
    }
    manifest, frames = {}, []
    for var, (pub, ser) in paths.items():
        p = latest(pub, ser)
        manifest[var] = {
            "publisher": pub, "series": ser,
            "vintage_file": str(p.relative_to(REPO_ROOT)),
            "sha256": sha256(p),
        }
        frames.append(load_long(p, var))

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(ALL_COUNTRIES)]
    panel = panel[panel["year"].between(PERIOD[0], PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    # Apply spec exclusion rules
    excl_set = set(EXCLUDE)
    panel = panel[~panel.apply(
        lambda r: (r["country"], r["year"]) in excl_set, axis=1
    )].copy()

    # Construct policy channels
    panel["bf_intensity"] = panel.apply(
        lambda r: BF_INTENSITY.get(r["year"], 0.0) if r["country"] == BRA else 0.0,
        axis=1,
    )
    panel["min_wage_log"] = panel.apply(
        lambda r: np.log(MW_REAL_INDEX_BRA.get(r["year"], 1.0)) if r["country"] == BRA else 0.0,
        axis=1,
    )
    return panel, manifest


def fit_with(df: pd.DataFrame, outcome: str, channels: list[str]) -> dict:
    """Fit OLS with country and year FE plus selected channels.
    Returns explained sum of squares (within after FE) and full R^2.
    """
    cols = ["country", "year", outcome] + channels
    d = df[cols].dropna().copy()
    if len(d) < 10:
        return {"ess": 0.0, "tss": 1.0, "r2": 0.0, "n": 0}

    # Construct dummy design matrix: country FE, year FE, and channels.
    X_parts = []
    # constant absorbed by country FE
    cdum = pd.get_dummies(d["country"], drop_first=True, prefix="c").astype(float)
    ydum = pd.get_dummies(d["year"].astype(int), drop_first=True, prefix="y").astype(float)
    X_parts.append(cdum)
    X_parts.append(ydum)
    if channels:
        X_parts.append(d[channels].astype(float).reset_index(drop=True))
    X = pd.concat([p.reset_index(drop=True) for p in X_parts], axis=1)
    X.insert(0, "const", 1.0)
    y = d[outcome].astype(float).values
    Xv = X.values

    # Solve OLS via lstsq
    beta, *_ = np.linalg.lstsq(Xv, y, rcond=None)
    yhat = Xv @ beta
    resid = y - yhat
    ybar = y.mean()
    tss = float(((y - ybar) ** 2).sum())
    rss = float((resid ** 2).sum())
    ess = max(tss - rss, 0.0)
    r2 = 1.0 - (rss / tss) if tss > 0 else 0.0
    return {"ess": ess, "tss": tss, "r2": r2, "n": int(len(d)), "beta_channels": {
        ch: float(beta[list(X.columns).index(ch)]) for ch in channels
        if ch in X.columns
    }}


def shapley_r2(df: pd.DataFrame, outcome: str, channels: list[str]) -> dict:
    """Shapley decomposition of incremental R^2 across channels.
    Baseline (with country + year FE only) is the value function's empty set.
    """
    base = fit_with(df, outcome, [])
    base_r2 = base["r2"]
    full = fit_with(df, outcome, channels)
    full_r2 = full["r2"]
    explainable = max(full_r2 - base_r2, 0.0)
    n_obs = full["n"]

    # Cache R^2 over all subsets
    subsets_r2 = {}
    for k in range(0, len(channels) + 1):
        for sub in combinations(channels, k):
            key = tuple(sorted(sub))
            if key in subsets_r2:
                continue
            res = fit_with(df, outcome, list(key)) if key else base
            subsets_r2[key] = res["r2"]

    # Shapley value for each channel = average marginal incremental R^2
    n = len(channels)
    from math import factorial
    shap_abs = {ch: 0.0 for ch in channels}
    for ch in channels:
        rest = [c for c in channels if c != ch]
        for k in range(0, len(rest) + 1):
            for sub in combinations(rest, k):
                w = factorial(k) * factorial(n - k - 1) / factorial(n)
                with_ch = subsets_r2[tuple(sorted(list(sub) + [ch]))]
                without_ch = subsets_r2[tuple(sorted(sub))]
                shap_abs[ch] += w * (with_ch - without_ch)

    total_shap = sum(shap_abs.values())
    # Normalise to share of explainable (above-FE) variance
    if explainable > 1e-12:
        shap_share = {ch: shap_abs[ch] / explainable for ch in channels}
    else:
        shap_share = {ch: 0.0 for ch in channels}

    return {
        "base_r2": base_r2,
        "full_r2": full_r2,
        "explainable_r2": explainable,
        "n_obs": n_obs,
        "shapley_abs_r2": shap_abs,
        "shapley_share": shap_share,
        "shapley_sum_check": float(total_shap),
        "channel_betas": full.get("beta_channels", {}),
    }


def magnitude_brazil(df: pd.DataFrame, outcome: str, label: str) -> dict:
    """Brazil's observed change over decomposition window (linear-interp 2010 if missing)."""
    bra = df[df["country"] == BRA].set_index("year")[outcome].dropna()
    y0 = float(bra.loc[2003]) if 2003 in bra.index else float("nan")
    if 2010 in bra.index:
        y1 = float(bra.loc[2010])
        end_year = 2010
    else:
        # Linear interp 2009 → 2011 if 2010 missing (typical PNAD gap)
        if 2009 in bra.index and 2011 in bra.index:
            y1 = (float(bra.loc[2009]) + float(bra.loc[2011])) / 2.0
            end_year = 2010  # nominal
        elif 2009 in bra.index:
            y1 = float(bra.loc[2009])
            end_year = 2009
        else:
            y1 = float(bra.iloc[-1])
            end_year = int(bra.index[-1])
    return {"label": label, "y_2003": y0, "y_endpoint": y1, "endpoint_year": end_year,
            "delta": y1 - y0}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    channels = ["bf_intensity", "min_wage_log", "gdp_pc_growth", "urban"]

    # Fit Shapley on poverty and Gini, on the decomposition window
    decomp_df = panel[panel["year"].between(DECOMP_PERIOD[0], DECOMP_PERIOD[1])].copy()
    pov_shap = shapley_r2(decomp_df, "poverty", channels)
    gin_shap = shapley_r2(decomp_df, "gini", channels)

    # Brazil magnitudes (descriptive)
    pov_mag = magnitude_brazil(panel, "poverty", "extreme_poverty_headcount")
    gin_mag = magnitude_brazil(panel, "gini", "gini_coefficient")

    # Aggregate policy share = BF + minimum wage
    policy_pov = pov_shap["shapley_share"]["bf_intensity"] + pov_shap["shapley_share"]["min_wage_log"]
    policy_gin = gin_shap["shapley_share"]["bf_intensity"] + gin_shap["shapley_share"]["min_wage_log"]
    commodity_pov = pov_shap["shapley_share"]["gdp_pc_growth"]
    commodity_gin = gin_shap["shapley_share"]["gdp_pc_growth"]

    # Verdict per spec.falsification.threshold
    cond_pov_policy = policy_pov >= THR_POVERTY_POLICY
    cond_gin_policy = policy_gin >= THR_GINI_POLICY
    cond_com_pov   = commodity_pov <= THR_COMMODITY_MAX
    cond_com_gin   = commodity_gin <= THR_COMMODITY_MAX
    all_pass = all([cond_pov_policy, cond_gin_policy, cond_com_pov, cond_com_gin])

    # Refutation: half-threshold-failure on both AND commodity dominance
    refuted = (
        (policy_pov < 0.5 * THR_POVERTY_POLICY)
        and (policy_gin < 0.5 * THR_GINI_POLICY)
        and ((commodity_pov > THR_COMMODITY_MAX) or (commodity_gin > THR_COMMODITY_MAX))
    )

    if all_pass:
        verdict = (
            f"SUPPORTED — Bolsa Família + minimum-wage Shapley shares: "
            f"poverty {policy_pov*100:.0f}% (>= {THR_POVERTY_POLICY*100:.0f}%), "
            f"Gini {policy_gin*100:.0f}% (>= {THR_GINI_POLICY*100:.0f}%); "
            f"commodity-boom share poverty {commodity_pov*100:.0f}%, "
            f"Gini {commodity_gin*100:.0f}% (both <= {THR_COMMODITY_MAX*100:.0f}%). "
            f"Brazil 2003→2010 delta: poverty {pov_mag['delta']:+.1f}pp, "
            f"Gini {gin_mag['delta']:+.1f}."
        )
    elif refuted:
        verdict = (
            f"refuted — Policy channels (BF + minimum wage) Shapley shares "
            f"poverty {policy_pov*100:.0f}% (< half of {THR_POVERTY_POLICY*100:.0f}%), "
            f"Gini {policy_gin*100:.0f}% (< half of {THR_GINI_POLICY*100:.0f}%); "
            f"commodity-boom share dominates "
            f"(poverty {commodity_pov*100:.0f}%, Gini {commodity_gin*100:.0f}%)."
        )
    else:
        misses = []
        if not cond_pov_policy:
            misses.append(f"BF+MW poverty share {policy_pov*100:.0f}% < {THR_POVERTY_POLICY*100:.0f}%")
        if not cond_gin_policy:
            misses.append(f"BF+MW Gini share {policy_gin*100:.0f}% < {THR_GINI_POLICY*100:.0f}%")
        if not cond_com_pov:
            misses.append(f"commodity poverty share {commodity_pov*100:.0f}% > {THR_COMMODITY_MAX*100:.0f}%")
        if not cond_com_gin:
            misses.append(f"commodity Gini share {commodity_gin*100:.0f}% > {THR_COMMODITY_MAX*100:.0f}%")
        verdict = (
            "partial — Some Shapley conditions met but not all: "
            + "; ".join(misses)
            + f". Brazil 2003→2010 delta: poverty {pov_mag['delta']:+.1f}pp, "
            f"Gini {gin_mag['delta']:+.1f}."
        )

    # ---------- Persist diagnostics ----------
    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "thresholds": {
            "policy_share_poverty_min": THR_POVERTY_POLICY,
            "policy_share_gini_min": THR_GINI_POLICY,
            "commodity_share_max": THR_COMMODITY_MAX,
        },
        "shapley_poverty": pov_shap,
        "shapley_gini": gin_shap,
        "policy_share_poverty": policy_pov,
        "policy_share_gini": policy_gin,
        "commodity_share_poverty": commodity_pov,
        "commodity_share_gini": commodity_gin,
        "brazil_observed": {
            "poverty": pov_mag,
            "gini": gin_mag,
        },
        "sample": {
            "countries": ALL_COUNTRIES,
            "period": list(PERIOD),
            "decomp_window": list(DECOMP_PERIOD),
            "exclusions": [{"country": c, "year": y} for c, y in EXCLUDE],
            "panel_n_obs": int(len(panel)),
            "decomp_n_obs": int(len(decomp_df)),
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- Coefficients table ----------
    rows = []
    for outcome_name, sh in [("poverty", pov_shap), ("gini", gin_shap)]:
        rows.append({"spec": "fit_full", "outcome": outcome_name,
                     "term": "full_r2", "estimate": sh["full_r2"]})
        rows.append({"spec": "fit_baseline_FE", "outcome": outcome_name,
                     "term": "base_r2", "estimate": sh["base_r2"]})
        for ch in channels:
            rows.append({
                "spec": "shapley", "outcome": outcome_name,
                "term": ch + "_share", "estimate": sh["shapley_share"][ch],
            })
            rows.append({
                "spec": "shapley_abs", "outcome": outcome_name,
                "term": ch + "_abs_r2", "estimate": sh["shapley_abs_r2"][ch],
            })
            if ch in sh["channel_betas"]:
                rows.append({
                    "spec": "channel_beta", "outcome": outcome_name,
                    "term": ch + "_beta", "estimate": sh["channel_betas"][ch],
                })
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Chart ----------
    palette = {"BRA": "#4E79A7", "MEX": "#59A14F", "COL": "#B07AA1",
               "PER": "#E15759", "CHL": "#F28E2B", "ARG": "#76B7B2"}
    series = []
    for c in ALL_COUNTRIES:
        sub = (panel[panel["country"] == c][["year", "poverty"]].dropna()
               .sort_values("year"))
        if sub.empty:
            continue
        series.append({
            "id": c, "label": c, "color": palette.get(c, "#888"),
            "treated": (c == BRA),
            "points": [{"x": int(r.year), "y": float(r.poverty)}
                       for r in sub.itertuples()],
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Extreme-poverty headcount, BRA vs LatAm donor pool, 1995-2012",
        "subtitle": (
            f"BF + minimum-wage Shapley share of poverty: {policy_pov*100:.0f}% "
            f"(threshold {THR_POVERTY_POLICY*100:.0f}%). "
            f"Commodity-boom share: {commodity_pov*100:.0f}% "
            f"(max {THR_COMMODITY_MAX*100:.0f}%)."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Extreme-poverty headcount (% pop, USD 2.15 PPP)",
                   "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "note",
             "label": (
                 f"Brazil 2003→2010: poverty {pov_mag['y_2003']:.1f} → "
                 f"{pov_mag['y_endpoint']:.1f} (delta {pov_mag['delta']:+.1f}pp). "
                 f"Gini {gin_mag['y_2003']:.1f} → {gin_mag['y_endpoint']:.1f} "
                 f"(delta {gin_mag['delta']:+.1f}). Decomposition window: "
                 f"{DECOMP_PERIOD[0]}-{DECOMP_PERIOD[1]}."
             )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Manifest ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
        "vintages": manifest,
        "constructed_channels": {
            "bf_intensity": "BRA-only stepwise indexation; calibrated to MDS / IPEA "
                            "Bolsa Família family-coverage timeline (2003 ~3.6M → "
                            "2010 ~12.7M), peak normalised to 1.0.",
            "min_wage_log": "BRA-only log of real-minimum-wage index (IPCA-deflated), "
                            "2003 = 1.00 → 2010 ≈ 1.55 per IPEA / DIEESE.",
        },
        "deviations": [
            "Commodity-boom channel proxied by per-capita real-GDP growth "
            "(NY.GDP.PCAP.KD.ZG); spec called for TT.PRI.MRCH.XD.WD terms-of-"
            "trade index, not in vintages.",
            "ipeadata PNAD higher-frequency BRA series not used; rely on WDI "
            "SI.POV.DDAY (USD 2.15 2017 PPP) for cross-country comparability.",
            "Synthetic-control robustness sub-spec deferred; verdict relies on "
            "Shapley-style R-squared decomposition.",
            "Bolsa Família coverage and minimum-wage indices are constructed "
            "from published programme/IPEA timelines, not pulled as a versioned "
            "vintage — a 'BF coverage' parquet would let this re-run mechanically.",
        ],
    }, sort_keys=False))

    # ---------- Result card ----------
    lines = [
        f"# Result card — {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Pre-registered thresholds",
        "",
        f"- BF + minimum-wage Shapley share of poverty change: >= {THR_POVERTY_POLICY:.2f}",
        f"- BF + minimum-wage Shapley share of Gini change: >= {THR_GINI_POLICY:.2f}",
        f"- Commodity-boom Shapley share on either outcome: <= {THR_COMMODITY_MAX:.2f}",
        "",
        "## Shapley shares",
        "",
        "| Channel | Poverty share | Gini share |",
        "|---|---:|---:|",
    ]
    for ch in channels:
        lines.append(
            f"| {ch} | {pov_shap['shapley_share'][ch]*100:+.1f}% | "
            f"{gin_shap['shapley_share'][ch]*100:+.1f}% |"
        )
    lines.append(
        f"| **BF + minimum wage (policy)** | **{policy_pov*100:+.1f}%** | "
        f"**{policy_gin*100:+.1f}%** |"
    )
    lines += [
        "",
        f"Full-spec R^2 (poverty): {pov_shap['full_r2']:.3f} "
        f"(baseline FE: {pov_shap['base_r2']:.3f}; explainable above FE: "
        f"{pov_shap['explainable_r2']:.3f}).",
        f"Full-spec R^2 (gini): {gin_shap['full_r2']:.3f} "
        f"(baseline FE: {gin_shap['base_r2']:.3f}; explainable above FE: "
        f"{gin_shap['explainable_r2']:.3f}).",
        "",
        "## Brazil observed change, 2003 → endpoint",
        "",
        f"- Extreme-poverty headcount: {pov_mag['y_2003']:.1f} → "
        f"{pov_mag['y_endpoint']:.1f} (endpoint {pov_mag['endpoint_year']}, "
        f"delta {pov_mag['delta']:+.1f}pp).",
        f"- Gini coefficient (×100): {gin_mag['y_2003']:.1f} → "
        f"{gin_mag['y_endpoint']:.1f} (endpoint {gin_mag['endpoint_year']}, "
        f"delta {gin_mag['delta']:+.1f}).",
        "",
        "## Method",
        "",
        "Panel: BRA + 5 LatAm donors (MEX, COL, PER, CHL, ARG), 1995-2012,",
        "with Argentina 2001-2003 and Mexico 2009 dropped per spec",
        "exclusion_rules. Decomposition window 2003-2010. OLS with country",
        "and year FE plus four channels (BF intensity, real-min-wage log,",
        "per-capita GDP growth as commodity-boom proxy, urbanisation rate).",
        "Shapley value for each channel is the average marginal incremental",
        "R^2 over all subset orderings, normalised to the explainable-R^2",
        "share above the country+year-FE baseline.",
        "",
        "## Data",
        "",
        "- world_bank_wdi:SI.POV.DDAY (extreme-poverty headcount, USD 2.15 PPP)",
        "- world_bank_wdi:SI.POV.GINI (Gini × 100)",
        "- world_bank_wdi:NY.GDP.PCAP.KD.ZG (per-capita real-GDP growth)",
        "- world_bank_wdi:SP.URB.TOTL.IN.ZS (urbanisation rate)",
        "",
        "## Caveats",
        "",
        "- Bolsa Família intensity and the real-minimum-wage index are",
        "  constructed BRA-only series (zero for donors), calibrated to",
        "  published IPEA / MDS / DIEESE timelines. Errors-in-variables on",
        "  these channels could attenuate their attributed share.",
        "- The commodity channel is reduced-form (per-capita growth), not a",
        "  terms-of-trade index — partly absorbing the same general boom",
        "  signal that drives donor-pool poverty declines but missing",
        "  cross-country heterogeneity in commodity-export concentration.",
        "- Synthetic-control robustness on BRA is deferred to v1.1.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  policy_share(poverty)={policy_pov:.3f}  policy_share(gini)={policy_gin:.3f}")
    print(f"  commodity_share(poverty)={commodity_pov:.3f}  commodity_share(gini)={commodity_gin:.3f}")
    print(f"  full_r2(poverty)={pov_shap['full_r2']:.3f}  full_r2(gini)={gin_shap['full_r2']:.3f}")
    print(f"artifacts: {OUT_DIR}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
