#!/usr/bin/env python3
"""Replication — NZ Rogernomics 1984 productivity effect.

Spec:     hypotheses/growth/nz_rogernomics_productivity_effect.yaml v1
Method:   Synthetic control (Abadie-Diamond-Hainmueller 2010) with
          treated = NZL, treatment year = 1984 (Lange-Douglas reforms),
          donor pool = {AUS, IRL, FIN, DNK, SWE, NOR, GBR, CAN}.

PRIMARY (dispositive): mean synthetic-control gap on log TFP (PWT
                       rtfpna) over 1995-2005 must be >= +0.05
                       (5 log-points / ~5%) for SUPPORTED. <= 0 for
                       REFUTED. Between 0 and 5% = PARTIAL.

INFORMATIVE: same gap on log real GDP per capita (PWT rgdpna / pop).
             Reported but does NOT gate the verdict — the headline
             claim is about productivity (TFP), not income.

METHOD_VALID: at least 4 donors with full coverage 1970-2005, AND
              pre-fit RMSE on log TFP <= 0.05. Method failure →
              inconclusive (per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2).
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
import yaml
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "nz_rogernomics_productivity_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

TREATED = "NZL"
DONORS = ["AUS", "IRL", "FIN", "DNK", "SWE", "NOR", "GBR", "CAN"]
TREAT_YEAR = 1984
PERIOD = (1970, 2005)
POST_WINDOW = (1995, 2005)  # decade-after window where the claim must show

PRIMARY_GAP_THRESHOLD = 0.05      # 5 log-points on TFP
PREFIT_RMSE_GATE = 0.05           # method-valid gate
MIN_DONORS = 4                    # method-valid gate


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_pwt(series: str) -> pd.DataFrame:
    p = latest("pwt", series)
    t = pq.read_table(p).to_pandas()
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.dropna(subset=["year", "value"])
    t["year"] = t["year"].astype(int)
    return t[["country_iso3", "year", "value"]].rename(
        columns={"country_iso3": "country", "value": series}
    ), p


def synthetic_control(panel: pd.DataFrame, outcome_col: str,
                      treat_year: int = TREAT_YEAR,
                      donors: list[str] = DONORS) -> dict:
    """Classic ADH synthetic control on `outcome_col`. Returns dict with
    weights, pre-fit RMSE, post gaps year-by-year and the post-window mean
    gap."""
    sub = panel[panel["country"].isin([TREATED] + donors)]
    wide = sub.pivot(index="year", columns="country", values=outcome_col)
    pre_years = [y for y in wide.index if PERIOD[0] <= y < treat_year]
    post_years = [y for y in wide.index if treat_year <= y <= PERIOD[1]]
    if len(pre_years) < 4:
        return {"error": f"only {len(pre_years)} pre years (need >=4)"}
    # Donors with complete pre + post coverage
    valid = []
    for d in donors:
        if d not in wide.columns:
            continue
        if wide.loc[pre_years + post_years, d].notna().all():
            valid.append(d)
    if len(valid) < MIN_DONORS:
        return {
            "error": f"only {len(valid)} donors with full coverage (need >={MIN_DONORS})",
            "valid_donors": valid,
        }
    if TREATED not in wide.columns or wide.loc[pre_years + post_years, TREATED].isna().any():
        return {"error": f"{TREATED} has missing data in window {PERIOD[0]}-{PERIOD[1]}"}

    pre = wide.loc[pre_years, [TREATED] + valid]
    post = wide.loc[post_years, [TREATED] + valid]
    treat_pre = pre[TREATED].values
    donor_pre = pre[valid].values

    def loss(w: np.ndarray) -> float:
        return float(np.sum((treat_pre - donor_pre @ w) ** 2))

    n = len(valid)
    sol = minimize(
        loss,
        np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
    )
    w = sol.x
    synth_pre = donor_pre @ w
    synth_post = post[valid].values @ w
    treat_post = post[TREATED].values
    gap_pre = treat_pre - synth_pre
    gap_post = treat_post - synth_post

    post_window_idx = [i for i, y in enumerate(post_years) if POST_WINDOW[0] <= y <= POST_WINDOW[1]]
    post_window_gap_mean = float(np.mean(gap_post[post_window_idx])) if post_window_idx else float("nan")

    return {
        "treat_year": int(treat_year),
        "donors": valid,
        "weights": {valid[i]: float(w[i]) for i in range(n)},
        "pre_fit_rmse": float(np.sqrt(np.mean(gap_pre ** 2))),
        "post_avg_gap": float(np.mean(gap_post)),
        "post_window_mean_gap": post_window_gap_mean,
        "post_window": list(POST_WINDOW),
        "gap_by_year_pre": {int(y): float(g) for y, g in zip(pre_years, gap_pre)},
        "gap_by_year_post": {int(y): float(g) for y, g in zip(post_years, gap_post)},
        "treated_path": {int(y): float(v) for y, v in zip(wide.index, wide[TREATED]) if pd.notna(v)},
        "synth_path": {**{int(y): float(s) for y, s in zip(pre_years, synth_pre)},
                       **{int(y): float(s) for y, s in zip(post_years, synth_post)}},
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rtfp_df, rtfp_path = load_pwt("rtfpna")
    rgdp_df, rgdp_path = load_pwt("rgdpna")
    pop_df, pop_path = load_pwt("pop")

    manifest = {
        "tfp": {"publisher": "pwt", "series": "rtfpna",
                "vintage_file": str(rtfp_path.relative_to(REPO_ROOT)),
                "sha256": sha256(rtfp_path)},
        "real_gdp_national_accounts": {"publisher": "pwt", "series": "rgdpna",
                                       "vintage_file": str(rgdp_path.relative_to(REPO_ROOT)),
                                       "sha256": sha256(rgdp_path)},
        "population": {"publisher": "pwt", "series": "pop",
                       "vintage_file": str(pop_path.relative_to(REPO_ROOT)),
                       "sha256": sha256(pop_path)},
    }

    # Build the analytical panel
    keep = [TREATED] + DONORS
    rtfp = rtfp_df[rtfp_df["country"].isin(keep) & rtfp_df["year"].between(*PERIOD)].copy()
    rgdp = rgdp_df[rgdp_df["country"].isin(keep) & rgdp_df["year"].between(*PERIOD)].copy()
    pop  = pop_df[pop_df["country"].isin(keep) & pop_df["year"].between(*PERIOD)].copy()

    # Merge GDP per capita
    gpc = rgdp.merge(pop, on=["country", "year"], how="inner")
    gpc["gdp_pc"] = gpc["rgdpna"] / gpc["pop"]
    gpc["log_gdp_pc"] = np.log(gpc["gdp_pc"])

    rtfp["log_tfp"] = np.log(rtfp["rtfpna"])

    # PRIMARY: synthetic control on log TFP
    tfp_panel = rtfp[["country", "year", "log_tfp"]]
    sc_tfp = synthetic_control(tfp_panel, "log_tfp")

    # INFORMATIVE: synthetic control on log GDP per capita
    gpc_panel = gpc[["country", "year", "log_gdp_pc"]]
    sc_gdp = synthetic_control(gpc_panel, "log_gdp_pc")

    # Method-valid gates
    method_errors = []
    if "error" in sc_tfp:
        method_errors.append(f"TFP synth: {sc_tfp['error']}")
    else:
        if len(sc_tfp["donors"]) < MIN_DONORS:
            method_errors.append(f"TFP donors {len(sc_tfp['donors'])} < {MIN_DONORS}")
        if sc_tfp["pre_fit_rmse"] > PREFIT_RMSE_GATE:
            method_errors.append(
                f"TFP pre-fit RMSE {sc_tfp['pre_fit_rmse']:.4f} > {PREFIT_RMSE_GATE}")

    if method_errors:
        verdict = (
            "inconclusive — method-validity gate failed: "
            + "; ".join(method_errors)
            + ". No primary verdict emitted."
        )
        primary_pass = False
        primary_partial = False
        primary_refuted = False
        post_window_gap_tfp = sc_tfp.get("post_window_mean_gap", float("nan"))
        post_window_gap_gdp = sc_gdp.get("post_window_mean_gap", float("nan")) if "error" not in sc_gdp else float("nan")
    else:
        post_window_gap_tfp = sc_tfp["post_window_mean_gap"]
        post_window_gap_gdp = sc_gdp["post_window_mean_gap"] if "error" not in sc_gdp else float("nan")

        primary_pass = post_window_gap_tfp >= PRIMARY_GAP_THRESHOLD
        primary_refuted = post_window_gap_tfp <= 0
        primary_partial = (not primary_pass) and (not primary_refuted)

        gdp_str = (
            f"; informative log GDP-pc gap = {post_window_gap_gdp*100:+.2f}%"
            if not np.isnan(post_window_gap_gdp) else ""
        )
        if primary_pass:
            verdict = (
                f"SUPPORTED — NZ synthetic-control log-TFP gap mean over "
                f"{POST_WINDOW[0]}-{POST_WINDOW[1]} = {post_window_gap_tfp*100:+.2f}% "
                f"(threshold +5%){gdp_str}. Pre-fit RMSE = {sc_tfp['pre_fit_rmse']:.4f}."
            )
        elif primary_refuted:
            verdict = (
                f"refuted — NZ synthetic-control log-TFP gap mean over "
                f"{POST_WINDOW[0]}-{POST_WINDOW[1]} = {post_window_gap_tfp*100:+.2f}% "
                f"(<= 0){gdp_str}. Productivity acceleration claim not supported by the data: "
                f"NZ TFP sits at or below its synthetic counterfactual built from "
                f"{len(sc_tfp['donors'])} donor advanced economies."
            )
        else:
            verdict = (
                f"partial — NZ synthetic-control log-TFP gap mean over "
                f"{POST_WINDOW[0]}-{POST_WINDOW[1]} = {post_window_gap_tfp*100:+.2f}% "
                f"(positive but below +5% threshold){gdp_str}."
            )

    # Diagnostics
    diagnostics = {
        "verdict": verdict,
        "primary_pass": primary_pass,
        "primary_partial": primary_partial,
        "primary_refuted": primary_refuted,
        "primary_gap_threshold": PRIMARY_GAP_THRESHOLD,
        "method_errors": method_errors,
        "post_window": list(POST_WINDOW),
        "post_window_mean_gap_log_tfp": float(post_window_gap_tfp) if not (
            isinstance(post_window_gap_tfp, float) and np.isnan(post_window_gap_tfp)
        ) else None,
        "post_window_mean_gap_log_gdp_pc": float(post_window_gap_gdp) if not (
            isinstance(post_window_gap_gdp, float) and np.isnan(post_window_gap_gdp)
        ) else None,
        "synthetic_control_log_tfp": sc_tfp,
        "synthetic_control_log_gdp_pc": sc_gdp,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # Coefficients table
    coef_rows = []
    if "error" not in sc_tfp:
        coef_rows.append({
            "spec": "synth_control_log_tfp",
            "term": "post_window_mean_gap",
            "estimate": sc_tfp["post_window_mean_gap"],
            "pre_fit_rmse": sc_tfp["pre_fit_rmse"],
            "n_donors": len(sc_tfp["donors"]),
        })
    if "error" not in sc_gdp:
        coef_rows.append({
            "spec": "synth_control_log_gdp_pc",
            "term": "post_window_mean_gap",
            "estimate": sc_gdp["post_window_mean_gap"],
            "pre_fit_rmse": sc_gdp["pre_fit_rmse"],
            "n_donors": len(sc_gdp["donors"]),
        })
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # Chart: TFP trajectory NZ vs synthetic + donors
    palette = ["#E15759", "#1f1f1f", "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B",
               "#76B7B2", "#EDC948", "#B6992D", "#9C755F"]
    series = []
    if "error" not in sc_tfp:
        # NZ actual
        nzl_path = sc_tfp["treated_path"]
        series.append({
            "id": "NZL", "label": "NZL (actual)", "color": palette[0],
            "treated": True,
            "points": [{"x": int(y), "y": float(v)} for y, v in sorted(nzl_path.items())],
        })
        # Synthetic NZ
        synth_path = sc_tfp["synth_path"]
        series.append({
            "id": "SYNTH_NZL", "label": "Synthetic NZ (donor-weighted)",
            "color": palette[1], "treated": False,
            "points": [{"x": int(y), "y": float(v)} for y, v in sorted(synth_path.items())],
        })
        # Donors
        donor_panel = tfp_panel[tfp_panel["country"].isin(sc_tfp["donors"])]
        for i, d in enumerate(sc_tfp["donors"]):
            sub = donor_panel[donor_panel["country"] == d].sort_values("year")
            if sub.empty:
                continue
            series.append({
                "id": d, "label": d, "color": palette[(i + 2) % len(palette)],
                "treated": False,
                "points": [{"x": int(r.year), "y": float(r.log_tfp)} for r in sub.itertuples()],
            })

    chart = {
        "kind": "result",
        "chart_id": f"{RUN_ID}/fig1",
        "title": "Log TFP — NZ vs synthetic counterfactual and advanced-economy donors, 1970-2005",
        "subtitle": (
            f"Synthetic-control mean log-TFP gap "
            f"{POST_WINDOW[0]}-{POST_WINDOW[1]}: "
            f"{post_window_gap_tfp*100:+.2f}% (threshold for SUPPORTED: +5%); "
            f"informative log GDP-pc gap: "
            f"{post_window_gap_gdp*100:+.2f}%."
            if not np.isnan(post_window_gap_tfp) else
            "Method-valid gate failed; no synthetic gap reported."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log TFP (PWT rtfpna)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": TREAT_YEAR,
             "label": f"Lange-Douglas Rogernomics ({TREAT_YEAR})"},
            {"type": "note",
             "label": (
                 f"Donor pool: {', '.join(sc_tfp.get('donors', DONORS))}. "
                 f"Pre-fit RMSE = {sc_tfp.get('pre_fit_rmse', float('nan')):.4f}."
             )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{RUN_ID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    # Manifest
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator_template": "synth_did (implemented as classic ADH synthetic control)",
        "vintages": manifest,
    }, sort_keys=False))

    # Result card
    weights_str = (
        ", ".join(f"{k}={v:.2f}" for k, v in sc_tfp["weights"].items())
        if "error" not in sc_tfp else "n/a (method failure)"
    )
    lines = [
        f"# Result card — NZ Rogernomics 1984 productivity effect",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Treated unit: **{TREATED}**, treatment year **{TREAT_YEAR}** (Lange-Douglas reforms).",
        f"- Donor pool: {', '.join(DONORS)}.",
        f"- Outcome (PRIMARY, dispositive): log TFP (PWT rtfpna).",
        f"- Outcome (INFORMATIVE, non-gating): log real GDP per capita (PWT rgdpna / pop).",
        f"- Post-treatment evaluation window: {POST_WINDOW[0]}-{POST_WINDOW[1]}.",
        "",
        "## PRIMARY result",
        "",
        f"- Mean synthetic-control gap on log TFP, "
        f"{POST_WINDOW[0]}-{POST_WINDOW[1]}: "
        f"**{post_window_gap_tfp*100:+.2f}%** "
        f"(SUPPORTED threshold: ≥ +5%; REFUTED threshold: ≤ 0%).",
        f"- Pre-treatment fit RMSE on log TFP: "
        f"**{sc_tfp.get('pre_fit_rmse', float('nan')):.4f}** "
        f"(method-valid gate: ≤ 0.05).",
        f"- Donors with full 1970-2005 coverage: "
        f"**{len(sc_tfp.get('donors', []))}** "
        f"(method-valid gate: ≥ {MIN_DONORS}).",
        f"- Donor weights: {weights_str}.",
        "",
        "## INFORMATIVE result (real-income channel)",
        "",
        f"- Mean synthetic-control gap on log real GDP per capita, "
        f"{POST_WINDOW[0]}-{POST_WINDOW[1]}: "
        f"**{post_window_gap_gdp*100:+.2f}%** (does not gate the verdict).",
        "",
        "## Method",
        "",
        "Classic Abadie-Diamond-Hainmueller (2010) synthetic-control "
        "estimator, donor weights chosen by SLSQP over the unit simplex "
        "to minimise pre-treatment squared loss. The spec calls for "
        "synth_did; the simpler ADH estimator is what the framework "
        "currently implements consistently across runs (see "
        "`engine/runs/estonia_market_reform_post_soviet_growth_1991_2007/`).",
        "",
        "Method-validity gates (per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2): "
        "pre-fit RMSE ≤ 0.05 and donor coverage ≥ 4. A failure on either "
        "gate emits `inconclusive`, never `refuted`.",
        "",
        "## Data",
        "",
        f"- pwt:rtfpna (TFP at constant national prices)",
        f"- pwt:rgdpna (real GDP at constant national prices)",
        f"- pwt:pop (population)",
        "",
        "Vintages pinned in `manifest.yaml`. Reproduce with `python3 replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    if "error" not in sc_tfp:
        print(f"  TFP gap mean {POST_WINDOW[0]}-{POST_WINDOW[1]}: {post_window_gap_tfp*100:+.2f}%")
        print(f"  GDP-pc gap mean: {post_window_gap_gdp*100:+.2f}%")
        print(f"  pre-fit RMSE: {sc_tfp['pre_fit_rmse']:.4f}; donors: {sc_tfp['donors']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
