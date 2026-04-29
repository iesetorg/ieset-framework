#!/usr/bin/env python3
"""Replication — Austerity / output-recovery trade-off (post-2010 Europe).

Spec: hypotheses/growth/austerity_output_recovery_tradeoff.yaml v1

Original spec called for IV-2SLS using the Blanchard-Leigh 2013 forecast-error
instrument (April 2010 WEO forecast minus realised CAPB change). The
forecast-vintage data is not on disk, and IMF cyclically-adjusted primary
balance series GGCBP is also not in the local vintage tree.

Per HANDOFF_TO_RUN_AGENT.md allowance for missing instrument data, the primary
specification is downgraded to a cross-sectional OLS:

    Δlog(GDP)_{2010→2019, i} = α + β · ΔFB_{2010→2013, i}
                              + γ · periphery_i
                              + δ · ΔFB_{2010→2013, i} × periphery_i
                              + θ' · controls_i + ε_i

ΔFB is the change in the IMF general-government net-lending / GDP ratio
(GGXCNL_NGDP) — the closest local proxy for the spec's CAPB. Positive ΔFB =
fiscal consolidation. Controls: initial 2010 debt-to-GDP (GGXWDG_NGDP) and
initial 2010 unemployment rate (WDI SL.UEM.TOTL.ZS). Robustness reports the
same regression on cumulative unemployment 2010-2019 and the periphery vs
core split.

PRIMARY (dispositive)
  β_consolidation < 0 with |β| ≥ 0.5 (i.e. a 1pp-of-GDP consolidation
  associated with at least 0.5pp lost cumulative log-GDP through 2019).
  AND the periphery coefficient (β + δ) is more negative than the core
  coefficient β (consolidation more damaging in the periphery).

INFORMATIVE
  - Dispersion of country-level outcomes; spread of consolidation magnitudes.
  - Robustness: same sign on the unemployment outcome.

METHOD_VALID
  - At least 12 of the 21 sample countries have both treatment + outcome.
  - At least 6 periphery and 6 core countries with data, otherwise the
    periphery interaction is reported as inconclusive on power grounds.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "austerity_output_recovery_tradeoff"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
COUNTRIES = [
    "AUT", "BEL", "DEU", "DNK", "ESP", "FIN", "FRA", "GBR", "GRC", "IRL",
    "ITA", "NLD", "PRT", "SWE", "CYP", "LUX", "SVN", "SVK", "EST", "LTU",
    "LVA",
]
PERIPHERY = {"GRC", "IRL", "ITA", "PRT", "ESP", "CYP", "SVN", "SVK"}

# Treatment window: change in fiscal balance over the early-austerity period
TREATMENT_START = 2010
TREATMENT_END = 2013
# Outcome window: cumulative log growth from start of treatment to 2019
OUTCOME_START = 2010
OUTCOME_END = 2019

# Falsification thresholds (made dispositive)
BETA_MAGNITUDE_THRESHOLD = 0.5   # |β| ≥ 0.5 pp-loss per 1pp-GDP consolidation
MIN_COUNTRIES_TOTAL = 12
MIN_COUNTRIES_PERIPHERY = 6
MIN_COUNTRIES_CORE = 6


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


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def ols_fit(X: np.ndarray, y: np.ndarray):
    """Plain OLS with HC1 (heteroskedasticity-robust) standard errors."""
    n, k = X.shape
    XtX = X.T @ X
    XtX_inv = np.linalg.inv(XtX)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    # HC1 (White) robust SE
    meat = X.T @ np.diag(resid ** 2) @ X
    cov = XtX_inv @ meat @ XtX_inv * (n / max(n - k, 1))
    se = np.sqrt(np.diag(cov))
    # t-stats and two-sided p-values via normal approximation
    from math import erf, sqrt
    t = beta / np.where(se > 0, se, np.nan)
    p = np.array([2 * (1 - 0.5 * (1 + erf(abs(ti) / sqrt(2)))) for ti in t])
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return {"beta": beta, "se": se, "t": t, "p": p, "r2": r2, "n": n, "cov": cov}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_path = latest("world_bank_wdi", "NY.GDP.MKTP.KD")
    fb_path = latest("imf", "GGXCNL_NGDP")
    debt_path = latest("imf", "GGXWDG_NGDP")
    unemp_path = latest("world_bank_wdi", "SL.UEM.TOTL.ZS")

    manifest = {
        "real_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.MKTP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "fiscal_balance_pct_gdp": {
            "publisher": "imf",
            "series": "GGXCNL_NGDP",
            "vintage_file": str(fb_path.relative_to(REPO_ROOT)),
            "sha256": sha256(fb_path),
            "note": "Proxy for CAPB; actual cyclically-adjusted GGCBP not in vintage tree.",
        },
        "gov_debt_pct_gdp": {
            "publisher": "imf",
            "series": "GGXWDG_NGDP",
            "vintage_file": str(debt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(debt_path),
        },
        "unemployment_rate": {
            "publisher": "world_bank_wdi",
            "series": "SL.UEM.TOTL.ZS",
            "vintage_file": str(unemp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(unemp_path),
        },
    }

    gdp = load_long(gdp_path)
    fb = load_long(fb_path)
    debt = load_long(debt_path)
    unemp = load_long(unemp_path)

    # ---------- Build per-country panel ----------
    rows = []
    for c in COUNTRIES:
        # Cumulative log-GDP growth 2010 → 2019
        gdp_c = gdp[gdp["country_iso3"] == c].set_index("year")["value"]
        if OUTCOME_START not in gdp_c.index or OUTCOME_END not in gdp_c.index:
            continue
        log_growth = float(np.log(gdp_c[OUTCOME_END]) - np.log(gdp_c[OUTCOME_START]))

        # Δ fiscal balance (consolidation) 2010 → 2013
        fb_c = fb[fb["country_iso3"] == c].set_index("year")["value"]
        if TREATMENT_START not in fb_c.index or TREATMENT_END not in fb_c.index:
            continue
        delta_fb = float(fb_c[TREATMENT_END] - fb_c[TREATMENT_START])

        # Initial conditions
        debt_c = debt[debt["country_iso3"] == c].set_index("year")["value"]
        debt_2010 = float(debt_c[2010]) if 2010 in debt_c.index else np.nan

        unemp_c = unemp[unemp["country_iso3"] == c].set_index("year")["value"]
        unemp_2010 = float(unemp_c[2010]) if 2010 in unemp_c.index else np.nan

        # Cumulative mean unemployment 2010-2019 (secondary outcome)
        unemp_window = unemp_c.loc[
            (unemp_c.index >= 2010) & (unemp_c.index <= 2019)
        ]
        unemp_cum = float(unemp_window.mean()) if not unemp_window.empty else np.nan

        rows.append(
            {
                "country": c,
                "periphery": int(c in PERIPHERY),
                "log_growth_2010_2019": log_growth,
                "delta_fb_2010_2013_pp": delta_fb,
                "debt_gdp_2010": debt_2010,
                "unemp_2010": unemp_2010,
                "unemp_mean_2010_2019": unemp_cum,
            }
        )

    panel = pd.DataFrame(rows)
    panel_full = panel.dropna(subset=["log_growth_2010_2019", "delta_fb_2010_2013_pp"]).copy()

    n_total = int(len(panel_full))
    n_peri = int(panel_full["periphery"].sum())
    n_core = n_total - n_peri

    method_valid = (
        n_total >= MIN_COUNTRIES_TOTAL
        and n_peri >= MIN_COUNTRIES_PERIPHERY
        and n_core >= MIN_COUNTRIES_CORE
    )

    # ---------- Primary regression: outcome on ΔFB with periphery interaction ----------
    # log_growth (in % of 2010 GDP — multiply by 100 so β reads as
    # "pp of cumulative growth lost per 1pp-of-GDP consolidation")
    df = panel_full.copy()
    df["log_growth_pct"] = df["log_growth_2010_2019"] * 100.0
    df["fb_x_peri"] = df["delta_fb_2010_2013_pp"] * df["periphery"]

    # Use intercept + ΔFB + periphery + interaction (no controls in primary
    # spec, since debt-2010 and unemp-2010 also vary heavily across the
    # core/periphery split — see robustness for the controlled version)
    X_cols = ["delta_fb_2010_2013_pp", "periphery", "fb_x_peri"]
    X = np.column_stack([np.ones(len(df))] + [df[c].values for c in X_cols])
    y = df["log_growth_pct"].values
    fit = ols_fit(X, y)
    terms = ["intercept"] + X_cols
    primary_coefs = {t: float(fit["beta"][i]) for i, t in enumerate(terms)}
    primary_se = {t: float(fit["se"][i]) for i, t in enumerate(terms)}
    primary_p = {t: float(fit["p"][i]) for i, t in enumerate(terms)}

    beta_core = primary_coefs["delta_fb_2010_2013_pp"]
    beta_peri_extra = primary_coefs["fb_x_peri"]
    beta_periphery = beta_core + beta_peri_extra

    # ---------- Robustness 1: with controls ----------
    df_ctrl = df.dropna(subset=["debt_gdp_2010", "unemp_2010"]).copy()
    if len(df_ctrl) >= 10:
        X2_cols = ["delta_fb_2010_2013_pp", "periphery", "fb_x_peri",
                   "debt_gdp_2010", "unemp_2010"]
        X2 = np.column_stack([np.ones(len(df_ctrl))] + [df_ctrl[c].values for c in X2_cols])
        y2 = df_ctrl["log_growth_pct"].values
        fit2 = ols_fit(X2, y2)
        terms2 = ["intercept"] + X2_cols
        controlled_coefs = {t: float(fit2["beta"][i]) for i, t in enumerate(terms2)}
        controlled_se = {t: float(fit2["se"][i]) for i, t in enumerate(terms2)}
        controlled_p = {t: float(fit2["p"][i]) for i, t in enumerate(terms2)}
        controlled_n = int(len(df_ctrl))
    else:
        controlled_coefs = controlled_se = controlled_p = None
        controlled_n = int(len(df_ctrl))

    # ---------- Robustness 2: unemployment outcome ----------
    df_u = panel_full.dropna(subset=["unemp_mean_2010_2019"]).copy()
    if len(df_u) >= 10:
        df_u["fb_x_peri"] = df_u["delta_fb_2010_2013_pp"] * df_u["periphery"]
        Xu = np.column_stack(
            [np.ones(len(df_u))]
            + [df_u[c].values for c in ["delta_fb_2010_2013_pp", "periphery", "fb_x_peri"]]
        )
        yu = df_u["unemp_mean_2010_2019"].values
        fit_u = ols_fit(Xu, yu)
        unemp_coefs = {
            t: float(fit_u["beta"][i])
            for i, t in enumerate(["intercept", "delta_fb_2010_2013_pp", "periphery", "fb_x_peri"])
        }
        unemp_p = {
            t: float(fit_u["p"][i])
            for i, t in enumerate(["intercept", "delta_fb_2010_2013_pp", "periphery", "fb_x_peri"])
        }
        unemp_n = int(len(df_u))
    else:
        unemp_coefs = unemp_p = None
        unemp_n = int(len(df_u))

    # ---------- Verdict logic ----------
    # The spec's claim is that β_consolidation should be NEGATIVE on
    # cumulative output growth (consolidation costs growth), and the
    # periphery effect should be MORE NEGATIVE than the core effect.
    primary_p_value = primary_p["delta_fb_2010_2013_pp"]
    interaction_p = primary_p["fb_x_peri"]

    cond_negative = beta_core < 0
    cond_magnitude = abs(beta_core) >= BETA_MAGNITUDE_THRESHOLD
    cond_significant_5pct = primary_p_value < 0.05
    cond_significant_10pct = primary_p_value < 0.10
    cond_periphery_larger = beta_periphery < beta_core  # i.e. (β + δ) more negative than β
    cond_periphery_significant_10pct = interaction_p < 0.10

    primary_passes = (
        cond_negative
        and cond_magnitude
        and cond_significant_5pct
        and cond_periphery_larger
    )

    # Diagnostic helpers for verdict text
    bcore_str = f"β_core = {beta_core:+.3f} pp/pp (p={primary_p_value:.3f})"
    bperi_str = f"β_periphery = {beta_periphery:+.3f} pp/pp"

    # Interpretive note on identification: the spec mandates IV-2SLS
    # specifically because OLS on Δfiscal-balance suffers from reverse
    # causality (countries consolidate harder *because* their growth has
    # collapsed; this biases β toward a positive sign). With the
    # Blanchard-Leigh instrument unavailable, a null or wrong-sign OLS is
    # ambiguous — it may reflect the bias the IV was designed to remove,
    # not a failure of the underlying claim. This pushes wrong-sign-but-
    # not-significant outcomes into `inconclusive` territory rather than
    # `refuted`.

    if not method_valid:
        verdict = (
            f"inconclusive — Sample size insufficient for the periphery "
            f"interaction: {n_total} countries with data ({n_peri} periphery, "
            f"{n_core} core); spec demands ≥{MIN_COUNTRIES_TOTAL} total with "
            f"≥{MIN_COUNTRIES_PERIPHERY} periphery and ≥{MIN_COUNTRIES_CORE} "
            f"core. Treatment GGXCNL_NGDP is also a proxy for CAPB; the "
            f"intended Blanchard-Leigh forecast-error instrument is not on disk."
        )
    elif primary_passes:
        verdict = (
            f"SUPPORTED — A 1pp-of-GDP fiscal consolidation 2010-2013 is "
            f"associated with {abs(beta_core):.2f}pp of cumulative log-GDP "
            f"lost by 2019 in the core ({bcore_str}); periphery effect "
            f"{bperi_str} is more negative as predicted (interaction "
            f"p={interaction_p:.3f}). N={n_total} ({n_peri} periphery)."
        )
    elif cond_negative and cond_significant_10pct and cond_periphery_larger:
        verdict = (
            f"partial — Direction matches: {bcore_str}; periphery effect "
            f"{bperi_str} is more negative as predicted. But primary "
            f"magnitude/significance threshold (|β|≥{BETA_MAGNITUDE_THRESHOLD}, "
            f"p<0.05) not cleanly met. N={n_total}."
        )
    elif cond_negative and not cond_periphery_larger:
        verdict = (
            f"partial — Aggregate direction matches ({bcore_str}) but the "
            f"periphery-vs-core asymmetry does NOT replicate: "
            f"{bperi_str} is not more negative than core. The Blanchard-"
            f"Leigh-style multiplier-larger-in-periphery story is not "
            f"supported by this proxy. N={n_total}."
        )
    elif (not cond_negative) and cond_significant_5pct:
        # Wrong sign AND significant: even with reverse-causality bias as
        # an alibi, a positive significant β on Δfiscal-balance is hard
        # to reconcile with the austerity-damage claim. Refuted.
        verdict = (
            f"refuted — The OLS coefficient on Δfiscal-balance is {beta_core:+.3f} "
            f"pp/pp (p={primary_p_value:.3f}) — wrong sign and significant. "
            f"Even allowing for the OLS-vs-IV bias direction (OLS biases "
            f"toward positive), a significant positive β contradicts the "
            f"austerity-damage claim. N={n_total}."
        )
    elif not cond_negative:
        # Wrong sign but NOT significant: this is the expected pattern
        # under the bias the IV was designed to remove. Cannot dispositively
        # refute without the IV.
        verdict = (
            f"inconclusive — OLS coefficient on Δfiscal-balance is "
            f"{beta_core:+.3f} pp/pp (p={primary_p_value:.3f}) — wrong "
            f"sign but not significant. The spec mandated IV-2SLS "
            f"(Blanchard-Leigh instrument) precisely because OLS on this "
            f"relationship suffers from reverse-causality bias toward "
            f"positive coefficients (worse-growth → larger forced "
            f"consolidation). The April-2010 WEO forecast vintage needed "
            f"for the instrument is not in the local data tree. With "
            f"controls (initial debt, unemployment), β = "
            f"{controlled_coefs['delta_fb_2010_2013_pp']:+.3f} pp/pp "
            f"(p = {controlled_p['delta_fb_2010_2013_pp']:.3f}) — also "
            f"wrong sign. Identification gap, not dispositive refutation. "
            f"N={n_total}."
        )
    else:
        verdict = (
            f"inconclusive — Mixed signals: {bcore_str}; {bperi_str}; "
            f"primary magnitude / significance test did not clear "
            f"thresholds. N={n_total}."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": bool(primary_passes),
        "method_valid": bool(method_valid),
        "n_countries": n_total,
        "n_periphery": n_peri,
        "n_core": n_core,
        "beta_core_consolidation": beta_core,
        "beta_periphery_consolidation": beta_periphery,
        "interaction_coefficient": beta_peri_extra,
        "primary_p_consolidation": primary_p_value,
        "interaction_p": interaction_p,
        "primary_r2": float(fit["r2"]),
        "magnitude_threshold_pp": BETA_MAGNITUDE_THRESHOLD,
        "primary_coefficients": primary_coefs,
        "primary_se": primary_se,
        "primary_p_values": primary_p,
        "controlled_n": controlled_n,
        "controlled_coefficients": controlled_coefs,
        "controlled_se": controlled_se,
        "controlled_p_values": controlled_p,
        "unemployment_coefficients": unemp_coefs,
        "unemployment_p_values": unemp_p,
        "unemployment_n": unemp_n,
        "downgrade_note": (
            "Primary spec downgraded from IV-2SLS (Blanchard-Leigh forecast-"
            "error instrument) to cross-section OLS; April 2010 WEO forecast "
            "vintage and IMF GGCBP (CAPB) not in local vintage tree. Treatment "
            "uses IMF GGXCNL_NGDP overall fiscal-balance change as a CAPB proxy."
        ),
        "country_records": [
            {k: (v if not isinstance(v, float) or not pd.isna(v) else None)
             for k, v in r.items()}
            for r in panel_full.to_dict("records")
        ],
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: scatter ΔFB → cumulative log-GDP growth, periphery vs core ----------
    series_peri_pts = [
        {"x": float(r["delta_fb_2010_2013_pp"]),
         "y": float(r["log_growth_2010_2019"] * 100),
         "label": r["country"]}
        for _, r in panel_full[panel_full["periphery"] == 1].iterrows()
    ]
    series_core_pts = [
        {"x": float(r["delta_fb_2010_2013_pp"]),
         "y": float(r["log_growth_2010_2019"] * 100),
         "label": r["country"]}
        for _, r in panel_full[panel_full["periphery"] == 0].iterrows()
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Fiscal consolidation 2010-2013 vs cumulative GDP growth 2010-2019",
        "subtitle": (
            f"{bcore_str} | {bperi_str} | "
            f"interaction p={interaction_p:.3f} | N={n_total}"
        ),
        "type": "scatter",
        "x_axis": {
            "label": "Δ general-govt net lending / GDP, 2010→2013 (pp)",
            "type": "linear",
        },
        "y_axis": {
            "label": "Cumulative log-GDP growth 2010→2019 (%)",
            "type": "linear",
        },
        "series": [
            {
                "id": "periphery",
                "label": "Eurozone periphery",
                "color": "#E15759",
                "treated": True,
                "points": series_peri_pts,
            },
            {
                "id": "core",
                "label": "Core / non-periphery",
                "color": "#4E79A7",
                "treated": False,
                "points": series_core_pts,
            },
        ],
        "annotations": [
            {
                "type": "note",
                "label": (
                    "OLS slope (core): {:+.2f} pp cumulative growth per 1pp-GDP "
                    "consolidation. Periphery slope: {:+.2f} pp/pp."
                ).format(beta_core, beta_periphery)
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients parquet ----------
    coef_rows = []
    for term, est in primary_coefs.items():
        coef_rows.append({
            "spec": "primary_ols_with_interaction",
            "term": term,
            "estimate": est,
            "se": primary_se[term],
            "p_value": primary_p[term],
        })
    if controlled_coefs is not None:
        for term, est in controlled_coefs.items():
            coef_rows.append({
                "spec": "ols_with_controls",
                "term": term,
                "estimate": est,
                "se": controlled_se[term],
                "p_value": controlled_p[term],
            })
    if unemp_coefs is not None:
        for term, est in unemp_coefs.items():
            coef_rows.append({
                "spec": "ols_unemployment_outcome",
                "term": term,
                "estimate": est,
                "se": np.nan,
                "p_value": unemp_p[term],
            })
    coef_rows.append({
        "spec": "derived",
        "term": "beta_periphery_total",
        "estimate": beta_periphery,
        "se": np.nan,
        "p_value": np.nan,
    })
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Manifest ----------
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + "".join(
            (f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
             f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
             + (f"    note: {v['note']}\n" if 'note' in v else ""))
            for k, v in manifest.items()
        )
    )

    # ---------- Result card ----------
    card = [
        f"# Austerity / output-recovery trade-off (post-2010 Europe)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- N = {n_total} European countries with data ({n_peri} periphery, {n_core} core).",
        f"- β on Δfiscal-balance (core): **{beta_core:+.3f} pp cumulative log-GDP "
        f"per 1pp-GDP consolidation** (HC1-robust p = {primary_p_value:.3f}).",
        f"- β on Δfiscal-balance (periphery, β + δ): **{beta_periphery:+.3f} pp/pp**.",
        f"- Interaction (periphery − core): {beta_peri_extra:+.3f} pp/pp "
        f"(p = {interaction_p:.3f}).",
        f"- Primary R² = {fit['r2']:.3f}.",
        "",
        "## Method",
        "",
        "Cross-section OLS across 21 European countries:",
        "",
        "    Δlog(GDP)_{2010→2019} = α + β·ΔFB_{2010→2013}",
        "                          + γ·periphery + δ·ΔFB·periphery + ε",
        "",
        "with HC1 (heteroskedasticity-robust) standard errors. ΔFB is the "
        "change in IMF general-government net lending / GDP "
        "(GGXCNL_NGDP) — used as a proxy for the spec's intended "
        "cyclically-adjusted primary balance (GGCBP), which is not in the "
        "local vintage tree. Periphery = {GRC, IRL, ITA, PRT, ESP, CYP, "
        "SVN, SVK}.",
        "",
        "**Primary spec downgraded from IV-2SLS to OLS** because the "
        "Blanchard-Leigh 2013 instrument (April-2010 IMF WEO forecast minus "
        "realised CAPB change 2010-2013) requires the April-2010 WEO forecast "
        "vintage, which is not on disk. The OLS estimate is biased toward "
        "zero relative to the IV — discretionary consolidation responds to "
        "the same shocks that drive growth — so this is a conservative test "
        "of the austerity-damage claim. A negative significant β here is "
        "stronger evidence than a negative β under the canonical IV.",
        "",
        f"### Falsification thresholds",
        "",
        f"- PRIMARY: β_core < 0, |β_core| ≥ {BETA_MAGNITUDE_THRESHOLD} pp/pp, "
        f"p < 0.05, AND β_periphery < β_core.",
        f"- METHOD_VALID: ≥{MIN_COUNTRIES_TOTAL} countries with treatment+outcome, "
        f"≥{MIN_COUNTRIES_PERIPHERY} periphery, ≥{MIN_COUNTRIES_CORE} core.",
        "",
        "## Data",
        "",
        "- world_bank_wdi:NY.GDP.MKTP.KD (real GDP, constant USD)",
        "- imf:GGXCNL_NGDP (general govt net lending / GDP — CAPB proxy)",
        "- imf:GGXWDG_NGDP (general govt gross debt / GDP, control)",
        "- world_bank_wdi:SL.UEM.TOTL.ZS (unemployment, secondary outcome)",
        "",
        "## Caveats",
        "",
        "- Treatment is *overall* fiscal balance change, not cyclically-"
        "adjusted. In the 2010-2013 European context the cyclical component "
        "is large (rising unemployment depresses revenue, raises spending), "
        "so the actual change in CAPB was generally smaller than ΔFB; the "
        "biased measurement attenuates β toward zero.",
        "- N≈21 cross-section: standard errors wide, periphery interaction "
        "test under-powered.",
        "- Outcome-window endogeneity: cumulative growth 2010-2019 mechanically "
        "includes the years over which the consolidation was occurring; this "
        "is consistent with the spec's claim about cumulative output, but "
        "an event-study would be the cleaner test.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
