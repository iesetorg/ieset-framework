#!/usr/bin/env python3
"""Replication — Estonia market-reform post-Soviet growth, 1991-2007.

Spec:     hypotheses/growth/estonia_market_reform_post_soviet_growth_1991_2007.yaml
Method:   YAML names did_chaisemartin (did_multiplegt_dyn). The Stata package
          has no clean Python equivalent. The YAML allows fallback to
          synth_did. We implement classic synthetic control (Abadie-Diamond-
          Hainmueller 2010) with treated=EST and donor pool from the YAML
          comparator countries (Latvia, Lithuania, Poland, Hungary, Czech,
          Slovak, Slovenia). Pre-trend test: comparing pre-treatment fit to
          post-treatment gap. We also report a within-Baltic vs CIS DiD and
          a recovery-speed comparison (years to regain 1991 GDP-pc level).

Treatment: Estonia's "shock therapy" + currency board (1992) + flat tax
(1994). Treatment date = 1992 (the start of the radical-reform regime).
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
RUN_ID = "estonia_market_reform_post_soviet_growth_1991_2007"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

TREATED = "EST"
DONORS_FULL = ["LVA", "LTU", "POL", "HUN", "CZE", "SVK", "SVN"]   # task spec
CIS_PEERS = ["BLR", "UKR", "RUS"]                                  # YAML control
TREAT_YEAR = 1992
PERIOD = (1989, 2007)


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def latest(pub, series):
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_maddison():
    p = latest("maddison", "mpd2020")
    t = pq.read_table(p).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    t["year"] = t["year"].astype(int)
    t["gdppc"] = pd.to_numeric(t["gdppc"], errors="coerce")
    out = t[["country_iso3", "year", "gdppc"]].rename(columns={"country_iso3": "country"})
    return out, p


def synthetic_control(panel, treat_year=TREAT_YEAR, donors=DONORS_FULL):
    sub = panel[panel["country"].isin([TREATED] + donors)]
    wide = sub.pivot(index="year", columns="country", values="log_gdp_pc")
    pre_years = [y for y in wide.index if y < treat_year and y >= PERIOD[0]]
    post_years = [y for y in wide.index if y >= treat_year and y <= PERIOD[1]]
    if len(pre_years) < 2:
        return {"error": f"only {len(pre_years)} pre years (need ≥2)",
                "treat_year": treat_year}
    # Drop donors with any NaN in pre or post
    valid = [d for d in donors if wide.loc[pre_years + post_years, d].notna().all()]
    if not valid:
        return {"error": "no donors with full coverage"}
    pre = wide.loc[pre_years, [TREATED] + valid]
    post = wide.loc[post_years, [TREATED] + valid]
    treat_pre = pre[TREATED].values
    donor_pre = pre[valid].values

    def loss(w): return float(np.sum((treat_pre - donor_pre @ w) ** 2))
    n = len(valid)
    sol = minimize(loss, np.ones(n) / n, method="SLSQP",
                   bounds=[(0, 1)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}])
    w = sol.x
    synth_pre = donor_pre @ w
    synth_post = post[valid].values @ w
    treat_post = post[TREATED].values
    gap_post = treat_post - synth_post
    gap_pre = treat_pre - synth_pre
    return {
        "treat_year": treat_year,
        "donors": valid,
        "weights": {valid[i]: float(w[i]) for i in range(n)},
        "pre_fit_rmse_log": float(np.sqrt(np.mean(gap_pre ** 2))),
        "post_avg_gap_log": float(np.mean(gap_post)),
        "post_avg_gap_pct": float(np.expm1(np.mean(gap_post)) * 100),
        "post_gap_by_year": {int(y): float(g) for y, g in zip(post_years, gap_post)},
        "pre_gap_by_year": {int(y): float(g) for y, g in zip(pre_years, gap_pre)},
    }


def did_baltic_vs_cis(panel):
    """Two-way FE DiD: Baltics (treated) vs CIS (control), pre vs post 1992."""
    sub = panel[panel["country"].isin(["EST", "LVA", "LTU"] + CIS_PEERS)].copy()
    sub = sub[(sub["year"] >= PERIOD[0]) & (sub["year"] <= PERIOD[1])]
    sub = sub.dropna(subset=["log_gdp_pc"])
    sub["baltic"] = sub["country"].isin(["EST", "LVA", "LTU"]).astype(int)
    sub["post"] = (sub["year"] >= TREAT_YEAR).astype(int)
    sub["did"] = sub["baltic"] * sub["post"]
    from linearmodels.panel import PanelOLS
    sub = sub.set_index(["country", "year"])
    res = PanelOLS(sub["log_gdp_pc"], sub[["did", "post"]],
                   entity_effects=True, check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True)
    if "did" not in res.params.index:
        return {"error": "did absorbed"}
    return {
        "n": int(res.nobs),
        "beta_did": float(res.params["did"]),
        "se": float(res.std_errors["did"]),
        "ci_lo": float(res.conf_int().loc["did", "lower"]),
        "ci_hi": float(res.conf_int().loc["did", "upper"]),
        "p": float(res.pvalues["did"]),
        "interpretation": ("Baltics' relative gain in log GDP-pc post-1992 vs "
                           "CIS comparator pool"),
    }


def recovery_speed(panel):
    """Years for each country to regain 1991 GDP-pc level."""
    out = {}
    for c in [TREATED] + DONORS_FULL + CIS_PEERS:
        sub = panel[panel["country"] == c].set_index("year")["gdppc"].dropna()
        if 1991 not in sub.index:
            out[c] = {"baseline_1991": None, "year_recovered": None,
                      "level_2007_vs_1991_pct": None}
            continue
        b = sub.loc[1991]
        recov = None
        for y in range(1992, 2008):
            if y in sub.index and sub.loc[y] >= b:
                recov = int(y)
                break
        end_pct = (float(sub.loc[2007] / b - 1) * 100) if 2007 in sub.index else None
        out[c] = {"baseline_1991": float(b),
                  "year_recovered": recov,
                  "level_2007_vs_1991_pct": end_pct}
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    md, mpath = load_maddison()
    manifest = {"gdppc": {"publisher": "maddison", "series": "mpd2020",
                          "vintage_file": str(mpath.relative_to(REPO_ROOT)),
                          "sha256": sha256(mpath)}}

    # Filter & engineer
    panel = md[md["country"].isin([TREATED] + DONORS_FULL + CIS_PEERS)].copy()
    panel = panel[(panel["year"] >= 1985) & (panel["year"] <= PERIOD[1])]
    panel = panel.drop_duplicates(subset=["country", "year"]).reset_index(drop=True)
    panel["log_gdp_pc"] = np.log(panel["gdppc"])

    sc = synthetic_control(panel)
    did = did_baltic_vs_cis(panel)
    recov = recovery_speed(panel)

    # Pre-trend test: pre-fit RMSE / mean post-treat gap ratio.
    # YAML threshold:
    #   - EST recovers to 1991 level by 2000 AND exceeds it by ≥20% by 2007
    #   - Baltic mean cumulative growth 1995-2007 > CIS mean by ≥15 pp
    est_recov = recov.get("EST", {})
    est_recover_year = est_recov.get("year_recovered")
    est_2007_growth = est_recov.get("level_2007_vs_1991_pct")
    threshold_a = (est_recover_year is not None and est_recover_year <= 2000
                   and est_2007_growth is not None and est_2007_growth >= 20)

    # Cumulative growth 1995-2007: log(2007) - log(1995) per country
    def cumg(c):
        sub = panel[panel["country"] == c].set_index("year")["gdppc"]
        if 1995 in sub.index and 2007 in sub.index and pd.notna(sub.loc[1995]) and pd.notna(sub.loc[2007]):
            return float((np.log(sub.loc[2007]) - np.log(sub.loc[1995])) * 100)
        return None
    baltic_g = [cumg(c) for c in ["EST", "LVA", "LTU"] if cumg(c) is not None]
    cis_g = [cumg(c) for c in CIS_PEERS if cumg(c) is not None]
    baltic_mean = float(np.mean(baltic_g)) if baltic_g else None
    cis_mean = float(np.mean(cis_g)) if cis_g else None
    gap_pp = (baltic_mean - cis_mean) if baltic_mean is not None and cis_mean is not None else None
    threshold_b = gap_pp is not None and gap_pp >= 15.0

    all_pass = threshold_a and threshold_b
    if all_pass:
        verdict = (f"SUPPORTED — Estonia recovered 1991 level by {est_recover_year} "
                   f"and reached +{est_2007_growth:.0f}% by 2007. Baltic−CIS cumulative "
                   f"log-growth gap 1995-2007 = {gap_pp:.1f} pp.")
    elif threshold_a or threshold_b:
        verdict = (f"PARTIAL — recovery threshold pass={threshold_a} "
                   f"(year_recovered={est_recover_year}, 2007 vs 1991 = {est_2007_growth}); "
                   f"Baltic−CIS gap pass={threshold_b} (gap={gap_pp})")
    else:
        verdict = (f"REFUTED — Estonia recovery year={est_recover_year}, "
                   f"2007 vs 1991 = {est_2007_growth}%, Baltic−CIS gap={gap_pp} pp.")

    # Chart
    series_data = []
    colors = {"EST": "#E15759", "LVA": "#F28E2B", "LTU": "#EDC948",
              "POL": "#76B7B2", "HUN": "#59A14F", "CZE": "#9C755F",
              "SVK": "#B07AA1", "SVN": "#FF9DA7", "BLR": "#666",
              "UKR": "#888", "RUS": "#444"}
    for c in [TREATED] + DONORS_FULL + CIS_PEERS:
        sub = panel[(panel["country"] == c) & panel["log_gdp_pc"].notna()].sort_values("year")
        if sub.empty:
            continue
        series_data.append({
            "id": c, "label": c, "color": colors.get(c, "#666"),
            "treated": c == TREATED,
            "points": [{"x": int(r.year), "y": float(r.log_gdp_pc)} for r in sub.itertuples()],
        })

    chart = {
        "chart_id": f"{RUN_ID}/fig1",
        "title": f"Log GDP per capita — Estonia vs CEE/Baltic donors and CIS peers, {PERIOD[0]}-{PERIOD[1]}",
        "subtitle": (f"Synthetic-control post-1992 avg gap = "
                     f"{sc.get('post_avg_gap_pct', float('nan')):+.1f}%. "
                     f"DiD Baltic−CIS β = {did.get('beta_did', float('nan')):+.3f} "
                     f"(p={did.get('p', float('nan')):.3f})."),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log GDP per capita (Maddison 2020 intl $)", "type": "linear"},
        "series": series_data,
        "annotations": [{"type": "note",
                         "label": f"Treatment 1992 (Estonia currency board); flat tax 1994."}],
        "sources": [{"publisher_id": "maddison", "series_id": "mpd2020",
                     "vintage_file": str(mpath.relative_to(REPO_ROOT))}],
        "permalink": f"/h/{RUN_ID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    coef_rows = []
    if "beta_did" in did:
        coef_rows.append({"spec": "did_baltic_vs_cis", "term": "did",
                          "estimate": did["beta_did"], "se": did["se"],
                          "ci_lo": did["ci_lo"], "ci_hi": did["ci_hi"],
                          "p": did["p"], "n_obs": did["n"]})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict, "all_pass": all_pass,
        "synthetic_control": sc,
        "did_baltic_vs_cis": did,
        "recovery_speed": recov,
        "cumulative_growth_1995_2007_pp": {
            "baltic_mean": baltic_mean,
            "cis_mean": cis_mean,
            "gap_pp": gap_pp,
        },
        "falsification_components": {
            "estonia_recovery_threshold": threshold_a,
            "baltic_minus_cis_growth_ge_15pp": threshold_b,
        },
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator_template": "did_chaisemartin (fallback synthetic_control + DiD)",
        "vintages": manifest,
    }, sort_keys=False))

    lines = [
        f"# Result card — Estonia market reform post-Soviet growth 1991-2007",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Recovery speed",
        "",
        "| Country | 1991 level | Year recovered | 2007 vs 1991 (%) |",
        "|---|---:|---:|---:|",
    ]
    for c, r in recov.items():
        lines.append(f"| {c} | {r['baseline_1991']} | {r['year_recovered']} | "
                     f"{r['level_2007_vs_1991_pct']} |")
    lines += [
        "",
        "## Synthetic control (donors: " + ", ".join(sc.get("donors", [])) + ")",
        "",
        f"- Pre-fit RMSE (log): {sc.get('pre_fit_rmse_log', float('nan')):.4f}",
        f"- Post-1992 avg gap (log): {sc.get('post_avg_gap_log', float('nan')):+.4f} "
        f"({sc.get('post_avg_gap_pct', float('nan')):+.2f}%)",
        f"- Donor weights: {sc.get('weights', {})}",
        "",
        "## DiD: Baltics vs CIS, pre/post 1992 (entity FE, log GDP-pc)",
        "",
        f"- β_did = {did.get('beta_did', float('nan')):+.4f} (p={did.get('p', float('nan')):.3f})",
        f"- 95% CI: [{did.get('ci_lo', float('nan')):+.3f}, {did.get('ci_hi', float('nan')):+.3f}]",
        f"- n = {did.get('n', '?')}",
        "",
        f"## Cumulative growth 1995-2007",
        "",
        f"- Baltic mean: {baltic_mean} pp",
        f"- CIS mean: {cis_mean} pp",
        f"- **Gap (Baltic − CIS)**: {gap_pp} pp (threshold: ≥15 pp)",
        "",
        "## Provenance",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  EST recovered by: {est_recover_year}; 2007 vs 1991: {est_2007_growth}%")
    print(f"  Baltic−CIS gap 1995-2007: {gap_pp}")


if __name__ == "__main__":
    sys.exit(main())
