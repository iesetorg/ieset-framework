#!/usr/bin/env python3
"""Replication — Canadian GDP per capita stagnation post-2015.

Spec:     hypotheses/growth/canada_gdp_per_capita_stagnation_post_2015.yaml
Steelman: hypotheses/steelman/canada_gdp_per_capita_stagnation_post_2015.md

Within-country TWFE: CAN vs anglophone/resource/small-open donor pool 2000-2023.
Treatment indicator canada_post_2015. CAN is single treated country; use
donor-country dummies + time FE so the treatment indicator is identified
(same identification approach as the UK template).

Population-growth decomposition: report descriptive Δ in real GDP per capita
vs Δ in real aggregate GDP vs Δ in population, to flag the "denominator
absorbed output" interpretation explicitly per the YAML falsification rule.
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
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "engine" / "runs" / "canada_gdp_per_capita_stagnation_post_2015"

TREATED = "CAN"
DONORS = ["USA", "AUS", "NZL", "GBR", "NOR", "CHE"]
ALL = [TREATED] + DONORS
PERIOD = (2000, 2023)


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


def assemble():
    paths = {
        "gdp_pc_ppp":      ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "gdp_pc_kd":       ("world_bank_wdi", "NY.GDP.PCAP.KD"),
        "population":      ("world_bank_wdi", "SP.POP.TOTL"),
        "trade_openness":  ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "urbanisation":    ("world_bank_wdi", "SP.URB.TOTL.IN.ZS"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths.items():
        p = latest(pub, series)
        manifest[v] = {"publisher": pub, "series": series,
                       "vintage_file": str(p.relative_to(REPO_ROOT)),
                       "sha256": sha256(p)}
        frames.append(load_long(p, v))
    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(ALL)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["log_gdp_pc_kd"]  = np.log(panel["gdp_pc_kd"])
    panel["log_population"] = np.log(panel["population"])
    panel["canada_post_2015"] = ((panel["country"] == TREATED) & (panel["year"] >= 2015)).astype(int)
    panel["canada_post_2016"] = ((panel["country"] == TREATED) & (panel["year"] >= 2016)).astype(int)
    return panel, manifest


def fit(df, outcome, treatments, controls=None):
    """CAN is single treated country. Use donor-country dummies + time FE."""
    controls = controls or []
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
    for c in DONORS[1:]:
        d[f"donor_{c}"] = (d.index.get_level_values("country") == c).astype(float)
    donor_cols = [f"donor_{c}" for c in DONORS[1:]]
    X = d[donor_cols + treatments + controls]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=False, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in treatments:
        if t in res.params.index:
            out["coefs"][t] = {
                "estimate": float(res.params[t]),
                "se": float(res.std_errors[t]),
                "ci_lo": float(res.conf_int().loc[t, "lower"]),
                "ci_hi": float(res.conf_int().loc[t, "upper"]),
                "p": float(res.pvalues[t]),
                "t": float(res.tstats[t]),
            }
    return out


def synthetic_control_gap(df, outcome, treat_year=2015):
    sub = df[["country", "year", outcome]].dropna()
    wide = sub.pivot(index="year", columns="country", values=outcome)
    if TREATED not in wide.columns:
        return {"error": "treated missing"}
    pre = wide.loc[PERIOD[0]:treat_year - 1]
    post = wide.loc[treat_year:PERIOD[1]]
    if pre.shape[0] < 5:
        return {"error": "too few pre years"}
    from scipy.optimize import minimize
    can_pre = pre[TREATED].values
    donors_pre = pre[DONORS].values
    def loss(w): return np.sum((can_pre - donors_pre @ w) ** 2)
    n = len(DONORS)
    sol = minimize(loss, np.ones(n) / n, method="SLSQP",
                   bounds=[(0, 1)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}])
    w = sol.x
    synth_pre = donors_pre @ w
    synth_post = post[DONORS].values @ w
    can_post = post[TREATED].values
    post_years = list(post.index)
    gap = can_post - synth_post
    return {
        "donor_weights": {d: float(w[i]) for i, d in enumerate(DONORS)},
        "pre_fit_rmse": float(np.sqrt(np.mean((can_pre - synth_pre) ** 2))),
        "post_gap": {int(y): float(gap[i]) for i, y in enumerate(post_years)},
        "post_avg_gap": float(np.mean(gap)),
        "frac_negative": float(np.mean(gap < 0)),
    }


def population_decomposition(df):
    """Mechanical decomposition: Canada-vs-donor-pool average growth rates of
    real GDP, population, and real GDP per capita 2015-2023."""
    out = {}
    for label, group in [("canada", [TREATED]), ("donor_pool", DONORS)]:
        sub = df[df["country"].isin(group)]
        wide_pc = sub.pivot(index="year", columns="country", values="gdp_pc_ppp")
        wide_pop = sub.pivot(index="year", columns="country", values="population")
        # aggregate real gdp = pc * population
        wide_gdp = wide_pc * wide_pop
        # group totals (sum of populations, weighted-avg pc)
        agg_gdp = wide_gdp.sum(axis=1)
        agg_pop = wide_pop.sum(axis=1)
        agg_pc = agg_gdp / agg_pop
        if 2015 in agg_pc.index and 2023 in agg_pc.index:
            d_pc = float(np.log(agg_pc.loc[2023]) - np.log(agg_pc.loc[2015]))
            d_pop = float(np.log(agg_pop.loc[2023]) - np.log(agg_pop.loc[2015]))
            d_gdp = float(np.log(agg_gdp.loc[2023]) - np.log(agg_gdp.loc[2015]))
            out[label] = {
                "log_gdp_change_2015_2023": d_gdp,
                "log_pop_change_2015_2023": d_pop,
                "log_gdp_pc_change_2015_2023": d_pc,
                "gdp_change_pct": (np.exp(d_gdp) - 1) * 100,
                "pop_change_pct": (np.exp(d_pop) - 1) * 100,
                "gdp_pc_change_pct": (np.exp(d_pc) - 1) * 100,
            }
    if "canada" in out and "donor_pool" in out:
        c, d = out["canada"], out["donor_pool"]
        gap = c["log_gdp_pc_change_2015_2023"] - d["log_gdp_pc_change_2015_2023"]
        # numerator (real-gdp) gap
        num_gap = c["log_gdp_change_2015_2023"] - d["log_gdp_change_2015_2023"]
        # denominator (population) gap
        den_gap = c["log_pop_change_2015_2023"] - d["log_pop_change_2015_2023"]
        out["gap_decomposition"] = {
            "per_capita_log_gap_2015_2023": gap,
            "real_gdp_log_gap": num_gap,
            "population_log_gap": den_gap,
            "share_attributable_to_population_growth": (
                float(-den_gap / gap) if gap != 0 else None
            ),
            "share_attributable_to_real_gdp": (
                float(num_gap / gap) if gap != 0 else None
            ),
        }
    return out


def build_chart(df, primary, sc, manifest):
    colors = {"CAN": "#E15759", "USA": "#4E79A7", "AUS": "#EDC948", "NZL": "#F28E2B",
              "GBR": "#76B7B2", "NOR": "#59A14F", "CHE": "#9C755F"}
    series = []
    for c in ALL:
        sub = df[df["country"] == c][["year", "log_gdp_pc_ppp"]].dropna().sort_values("year")
        if sub.empty: continue
        series.append({
            "id": c, "label": c, "color": colors.get(c, "#666"),
            "treated": c == TREATED,
            "points": [{"x": int(r.year), "y": float(r.log_gdp_pc_ppp)} for r in sub.itertuples()],
        })
    b = primary["coefs"].get("canada_post_2015", {})
    return {
        "chart_id": "canada_gdp_per_capita_stagnation_post_2015/fig1",
        "title": "Log GDP per capita (PPP, constant) — Canada vs anglophone/resource/small-open donor pool, 2000-2023",
        "subtitle": (
            f"β_canada_post_2015 = {b.get('estimate', float('nan')):+.3f} "
            f"(p={b.get('p', float('nan')):.3f}). "
            f"SC post-2015 frac negative: {sc.get('frac_negative', 0):.0%}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log GDP per capita PPP (constant intl $)", "type": "linear"},
        "series": series,
        "annotations": [{"type": "note", "label": "Treatment 2015 (Trudeau Liberal election Nov 2015). Donor pool: USA/AUS/NZL/GBR/NOR/CHE."}],
        "sources": [{"publisher_id": v["publisher"], "series_id": v["series"],
                     "vintage_file": v["vintage_file"]} for v in manifest.values()],
        "permalink": "/h/canada_gdp_per_capita_stagnation_post_2015",
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    primary = fit(panel, "log_gdp_pc_ppp",
                  ["canada_post_2015"],
                  ["log_population", "trade_openness", "urbanisation"])
    robust_2016 = fit(panel, "log_gdp_pc_ppp",
                      ["canada_post_2016"],
                      ["log_population", "trade_openness", "urbanisation"])
    secondary_kd = fit(panel, "log_gdp_pc_kd",
                       ["canada_post_2015"],
                       ["log_population", "trade_openness", "urbanisation"])
    sc = synthetic_control_gap(panel, "log_gdp_pc_ppp", treat_year=2015)
    decomp = population_decomposition(panel)

    b = primary["coefs"].get("canada_post_2015", {})
    sign_ok = b.get("estimate", 0) < 0
    sig = b.get("p", 1.0) < 0.10
    sc_ok = (sc.get("frac_negative") or 0) >= 0.60
    primary_pass = sign_ok and sig
    all_pass = primary_pass and sc_ok

    # Population-decomposition guard from YAML: if real-gdp numerator growth
    # is at or above donor-pool average AND >100% of gap attributable to denominator,
    # record as supported on per-capita stagnation but NOT on productivity stagnation.
    pop_share = (decomp.get("gap_decomposition") or {}).get("share_attributable_to_population_growth")
    productivity_caveat = pop_share is not None and pop_share > 1.0

    if all_pass and not productivity_caveat:
        verdict = (
            f"SUPPORTED — Canada diverged negatively from donor pool post-2015 "
            f"(β={b.get('estimate', 0):+.3f}, p={b.get('p', 0):.3f}). "
            f"SC gap negative in {sc.get('frac_negative', 0):.0%} of post-2015 years."
        )
    elif all_pass and productivity_caveat:
        verdict = (
            f"PARTIAL — per-capita stagnation supported (β={b.get('estimate', 0):+.3f}, "
            f"p={b.get('p', 0):.3f}), but population-growth decomposition attributes "
            f"{pop_share:.0%} of the per-capita gap to faster Canadian population "
            f"growth; productivity-stagnation framing NOT supported on this evidence."
        )
    elif primary_pass and not sc_ok:
        verdict = (
            f"PARTIAL — TWFE supports stagnation (β={b.get('estimate', 0):+.3f}, "
            f"p={b.get('p', 0):.3f}) but SC gap negative in only "
            f"{sc.get('frac_negative', 0):.0%} of post-2015 years (<60% threshold)."
        )
    else:
        verdict = (
            f"REFUTED — TWFE β={b.get('estimate', 0):+.3f} p={b.get('p', 1.0):.3f}; "
            f"falsification rule fails."
        )

    (OUT_DIR / "chart_data.json").write_text(json.dumps(
        build_chart(panel, primary, sc, manifest), indent=2) + "\n")

    rows = []
    for spec_label, res in [("primary_twfe_2015", primary), ("robust_twfe_2016", robust_2016),
                            ("secondary_kd_2015", secondary_kd)]:
        for t, c in res.get("coefs", {}).items():
            rows.append({"spec": spec_label, "term": t, **c, "n_obs": res["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "all_pass": all_pass,
        "primary_twfe_2015": primary,
        "robust_twfe_2016": robust_2016,
        "secondary_kd_2015": secondary_kd,
        "synthetic_control": sc,
        "population_decomposition": decomp,
        "falsification_components": {
            "twfe_sign_negative": sign_ok,
            "twfe_p_lt_010": sig,
            "sc_frac_negative_ge_060": sc_ok,
            "productivity_caveat_pop_share_gt_100pct": productivity_caveat,
        },
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "canada_gdp_per_capita_stagnation_post_2015",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # Result card
    b16 = robust_2016["coefs"].get("canada_post_2016", {})
    bkd = secondary_kd["coefs"].get("canada_post_2015", {})
    can = decomp.get("canada", {})
    don = decomp.get("donor_pool", {})
    g = decomp.get("gap_decomposition", {})

    lines = [
        "# Result card — Canada GDP per capita stagnation post-2015",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Primary spec (TWFE, log GDP pc PPP, 2000-2023)",
        "",
        "| Term | Estimate | SE | 95% CI | p | t |",
        "|---|---:|---:|:---:|---:|---:|",
        f"| canada_post_2015 | {b.get('estimate', float('nan')):+.4f} | {b.get('se', float('nan')):.4f} | "
        f"[{b.get('ci_lo', float('nan')):+.3f}, {b.get('ci_hi', float('nan')):+.3f}] | "
        f"{b.get('p', float('nan')):.3f} | {b.get('t', float('nan')):+.2f} |",
        f"| (robust 2016 cutoff) canada_post_2016 | {b16.get('estimate', float('nan')):+.4f} | "
        f"{b16.get('se', float('nan')):.4f} | "
        f"[{b16.get('ci_lo', float('nan')):+.3f}, {b16.get('ci_hi', float('nan')):+.3f}] | "
        f"{b16.get('p', float('nan')):.3f} | {b16.get('t', float('nan')):+.2f} |",
        f"| (secondary KD-LCU) canada_post_2015 | {bkd.get('estimate', float('nan')):+.4f} | "
        f"{bkd.get('se', float('nan')):.4f} | "
        f"[{bkd.get('ci_lo', float('nan')):+.3f}, {bkd.get('ci_hi', float('nan')):+.3f}] | "
        f"{bkd.get('p', float('nan')):.3f} | {bkd.get('t', float('nan')):+.2f} |",
        "",
        f"n = {primary['n_obs']} country-years. Donor pool: {', '.join(DONORS)}.",
        "",
        "## Synthetic control",
        "",
        f"Donor weights: {sc.get('donor_weights', {})}",
        f"Pre-fit RMSE 2000-2014: {sc.get('pre_fit_rmse', float('nan')):.4f} log",
        f"Post-2015 avg gap (CAN − synthetic): {sc.get('post_avg_gap', float('nan')):+.3f} log",
        f"Fraction of post-2015 years CAN below synthetic: {sc.get('frac_negative', 0):.0%}",
        "",
        "## Population-growth decomposition (2015 → 2023)",
        "",
        "| Group | Δ real GDP (log) | Δ population (log) | Δ GDP per capita (log) |",
        "|---|---:|---:|---:|",
        f"| Canada | {can.get('log_gdp_change_2015_2023', float('nan')):+.3f} ({can.get('gdp_change_pct', float('nan')):+.1f}%) | "
        f"{can.get('log_pop_change_2015_2023', float('nan')):+.3f} ({can.get('pop_change_pct', float('nan')):+.1f}%) | "
        f"{can.get('log_gdp_pc_change_2015_2023', float('nan')):+.3f} ({can.get('gdp_pc_change_pct', float('nan')):+.1f}%) |",
        f"| Donor pool (avg) | {don.get('log_gdp_change_2015_2023', float('nan')):+.3f} ({don.get('gdp_change_pct', float('nan')):+.1f}%) | "
        f"{don.get('log_pop_change_2015_2023', float('nan')):+.3f} ({don.get('pop_change_pct', float('nan')):+.1f}%) | "
        f"{don.get('log_gdp_pc_change_2015_2023', float('nan')):+.3f} ({don.get('gdp_pc_change_pct', float('nan')):+.1f}%) |",
        f"| **Gap (CAN − donor)** | **{g.get('real_gdp_log_gap', float('nan')):+.3f}** | **{g.get('population_log_gap', float('nan')):+.3f}** | **{g.get('per_capita_log_gap_2015_2023', float('nan')):+.3f}** |",
        "",
    ]
    pop_share_v = g.get("share_attributable_to_population_growth")
    real_share_v = g.get("share_attributable_to_real_gdp")
    if pop_share_v is not None:
        lines += [
            f"**Decomposition headline:** Of the per-capita gap, "
            f"{pop_share_v:.0%} attributable to faster Canadian population growth "
            f"(denominator absorbing output) and {real_share_v:.0%} attributable to "
            f"slower real-GDP numerator growth.",
            "",
        ]
        if productivity_caveat:
            lines += [
                "**Productivity caveat:** Population-growth decomposition attributes >100% of the "
                "per-capita gap to denominator growth, meaning Canadian real-GDP numerator "
                "growth was at or above donor-pool average. The per-capita-stagnation framing "
                "is supported; the productivity-stagnation framing is NOT supported on this "
                "country-level evidence.",
                "",
            ]
    lines += [
        "## Interpretation",
        "",
        "Canadian GDP per capita (PPP) trajectory under the 2015-present policy mix is "
        "the question. The TWFE coefficient identifies the deviation from the donor-pool "
        "time-average; the synthetic-control coefficient is robustness; the population-"
        "growth decomposition is the falsification guard pre-registered in the YAML.",
        "",
        "## Steelman concerns",
        "",
        "1. Donor pool excludes EU energy-shock countries by design; alternative pool would change β.",
        "2. 2015 cutoff captures Trudeau era + global productivity slowdown + commodity-price cycle.",
        "3. Per-capita gap mechanically reflects rapid Canadian immigration absorbing output.",
        "4. Real-GDP numerator stagnation is the policy-relevant narrower claim and may differ from per-capita.",
        "",
        "## Provenance",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  canada_post_2015: β={b.get('estimate', float('nan')):+.4f} p={b.get('p', float('nan')):.3f}")
    print(f"  SC frac negative post-2015: {sc.get('frac_negative', 0):.0%}")
    print(f"  population-growth share of gap: {pop_share_v}")


if __name__ == "__main__":
    sys.exit(main())
