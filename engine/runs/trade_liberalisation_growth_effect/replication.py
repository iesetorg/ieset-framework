#!/usr/bin/env python3
"""Replication — Trade liberalisation growth effect (Callaway-Sant'Anna staggered DiD).

Outcome: log real GDP per capita (level), event-study around treatment.
Treatment: country-specific liberalisation event year (Wacziarg-Welch coding).
"""
from __future__ import annotations

import hashlib, json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")
REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "trade_liberalisation_growth_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

# Wacziarg-Welch (2008) updated event years (subset with adequate data + simple coding)
EVENT_YEARS = {
    "CHN": 2001, "IND": 1991, "NZL": 1984, "VNM": 1986,
    "CHL": 1974, "POL": 1990, "CZE": 1993, "HUN": 1989,
    "KOR": 1988, "MEX": 1986, "IDN": 1994, "MYS": 1988,
    "THA": 1988, "PER": 1991, "COL": 1991, "BRA": 1991,
    "ARG": 1991, "TUR": 1989, "ZAF": 1991,
}
# Never-treated pool (or far-future) candidates — open economies / OECD pre-1980 or never-coded
CONTROLS = ["DEU", "FRA", "GBR", "USA", "JPN", "ITA", "ESP", "NLD",
            "BEL", "AUT", "SWE", "NOR", "DNK", "FIN", "CHE", "CAN", "AUS",
            "GHA", "KEN", "NGA", "EGY", "PAK", "BGD", "PHL", "LKA", "MAR", "TUN", "IRN"]
PERIOD = (1980, 2023)


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


def load_wdi(series, name):
    p = latest("world_bank_wdi", series)
    t = pq.read_table(p).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.rename(columns={"value": name, "country_iso3": "country"})
    return out, str(p.relative_to(REPO_ROOT)), sha256(p)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"hypothesis_id": RUN_ID, "estimator": "did_callaway_santanna", "inputs": {}}

    gdp, p1, h1 = load_wdi("NY.GDP.PCAP.KD", "gdp_pc")
    pop, p2, h2 = load_wdi("SP.POP.TOTL", "pop")
    manifest["inputs"]["gdp_pc"] = {"vintage": p1, "sha256": h1}
    manifest["inputs"]["pop"] = {"vintage": p2, "sha256": h2}

    df = gdp.merge(pop, on=["country", "year"], how="inner")
    df = df[df["country"].isin(list(EVENT_YEARS.keys()) + CONTROLS)]
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])]
    df["log_gdp_pc"] = np.log(df["gdp_pc"])

    # Treatment cohort: g = first treatment year (NaN for never-treated)
    df["cohort"] = df["country"].map(lambda c: EVENT_YEARS.get(c, np.nan))
    df = df.dropna(subset=["log_gdp_pc"]).reset_index(drop=True)

    # Drop hyperinflation country-years using CPI (simple guard)
    try:
        cpi, p3, h3 = load_wdi("FP.CPI.TOTL.ZG", "cpi_zg")
        df = df.merge(cpi, on=["country", "year"], how="left")
        df = df[(df["cpi_zg"].isna()) | (df["cpi_zg"] < 500)]
        manifest["inputs"]["cpi_zg"] = {"vintage": p3, "sha256": h3}
    except Exception as e:
        print("cpi guard skipped", e)

    # ---- Callaway-Sant'Anna via 'differences' library ----
    try:
        from differences import ATTgt
        panel = df[["country", "year", "log_gdp_pc", "cohort"]].copy()
        panel = panel.set_index(["country", "year"])
        att = ATTgt(data=panel, cohort_column="cohort")
        result = att.fit(formula="log_gdp_pc", control_group="not_yet_treated", progress_bar=False)
        # Aggregate
        overall = att.aggregate("simple")
        event = att.aggregate("event")
        cohort_agg = att.aggregate("cohort")
        def df_to_records(x):
            try:
                if hasattr(x, "reset_index"):
                    rec = x.reset_index().to_dict(orient="records")
                    # stringify any tuple keys / values
                    out = []
                    for r in rec:
                        out.append({str(k): (str(v) if isinstance(v, tuple) else v) for k, v in r.items()})
                    return out
                if hasattr(x, "to_dict"):
                    d = x.to_dict()
                    return {str(k): v for k, v in d.items()}
            except Exception:
                pass
            return str(x)
        results_overall = df_to_records(overall)
        results_event = df_to_records(event)
        results_cohort = df_to_records(cohort_agg)
        # Compute summary ATT + pre-trend from event aggregation
        try:
            ev_recs = results_event if isinstance(results_event, list) else []
            if ev_recs:
                cols = list(ev_recs[0].keys())
                # Find columns whose stringified form contains tokens
                def find(tokens):
                    for c in cols:
                        s = str(c).lower()
                        if all(t in s for t in tokens):
                            return c
                    return None
                et_col = find(["relative_period"]) or find(["event"]) or cols[0]
                att_col = find(["att"]) or cols[1]
                lower_col = find(["lower"])
                upper_col = find(["upper"])
                # post: 0..10
                def ev_val(r):
                    v = r.get(et_col)
                    try: return float(v)
                    except: return None
                post = [r for r in ev_recs if ev_val(r) is not None and 0 <= ev_val(r) <= 10]
                pre = [r for r in ev_recs if ev_val(r) is not None and -5 <= ev_val(r) <= -2]
                post_atts = [r[att_col] for r in post]
                pre_atts = [r[att_col] for r in pre]
                # pre-trend pass: all -5..-2 confidence bands include zero
                pre_pass = True
                for r in pre:
                    lo, hi = r.get(lower_col), r.get(upper_col)
                    if lo is not None and hi is not None and (lo > 0 or hi < 0):
                        pre_pass = False
                        break
                summary = {
                    "att_post_0_10_mean": float(np.mean(post_atts)) if post_atts else None,
                    "n_post_bins": len(post_atts),
                    "pre_trend_max_abs": float(max([abs(a) for a in pre_atts] or [0.0])),
                    "pre_trend_pass_zero_in_band": bool(pre_pass),
                    "event_window_used": "[-5, +10]",
                }
                # SimpleAggregation overall ATT
                if isinstance(results_overall, list) and results_overall:
                    sa_cols = list(results_overall[0].keys())
                    sa_att_col = next((c for c in sa_cols if "ATT" in str(c)), None)
                    if sa_att_col:
                        summary["overall_att_simple"] = float(results_overall[0][sa_att_col])
                results_overall = {"raw": results_overall, "summary": summary}
        except Exception as e:
            print("event-aggregation summary failed", e)
            import traceback; traceback.print_exc()
        cs_method = "differences.ATTgt"
    except Exception as e:
        print("differences ATTgt path failed:", e)
        # Fall back: manual two-way fixed effects event study
        results_overall, results_event, results_cohort = manual_event_study(df)
        cs_method = "manual_twfe_event_study"

    out = {
        "method": cs_method,
        "n_treated_countries": len(EVENT_YEARS),
        "n_control_countries": len([c for c in CONTROLS if c in df["country"].unique()]),
        "n_obs": int(len(df)),
        "period": list(PERIOD),
        "overall_att": results_overall,
        "event_study": results_event,
        "by_cohort": results_cohort,
    }

    (OUT_DIR / "diagnostics.json").write_text(json.dumps(out, indent=2, default=str))
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    write_result_card(out)
    print("done", RUN_ID)


def manual_event_study(df: pd.DataFrame):
    """Fallback: two-way FE event study with leads/lags, equal-weight cohort ATT."""
    from linearmodels.panel import PanelOLS
    d = df.copy()
    d["event_time"] = np.where(d["cohort"] > 0, d["year"] - d["cohort"], np.nan)
    # Bin event time to [-5, +10]
    d["et"] = d["event_time"].clip(-5, 10)
    # Build dummies (omit -1 as reference)
    dummies = pd.get_dummies(d["et"].fillna(-99), prefix="et").astype(float)
    if "et_-1.0" in dummies.columns:
        dummies = dummies.drop(columns=["et_-1.0"])
    if "et_-99.0" in dummies.columns:
        dummies = dummies.drop(columns=["et_-99.0"])
    dummies.index = d.index
    Y = d["log_gdp_pc"]
    X = dummies
    panel_df = pd.concat([d[["country", "year"]], Y, X], axis=1).dropna()
    panel_df = panel_df.set_index(["country", "year"])
    mod = PanelOLS(panel_df["log_gdp_pc"], panel_df.drop(columns=["log_gdp_pc"]),
                   entity_effects=True, time_effects=True)
    res = mod.fit(cov_type="clustered", cluster_entity=True)
    coefs = {k: float(v) for k, v in res.params.items()}
    ses = {k: float(v) for k, v in res.std_errors.items()}
    pvals = {k: float(v) for k, v in res.pvalues.items()}
    event_profile = {}
    for k, v in coefs.items():
        event_profile[k.replace("et_", "")] = {"coef": v, "se": ses.get(k), "p": pvals.get(k)}
    # ATT = avg of post (0..10) coefficients
    post = [v for k, v in coefs.items() if k.startswith("et_") and float(k.split("_")[1]) >= 0]
    overall = {"att": float(np.mean(post)) if post else None,
               "n_post_bins": len(post)}
    # Pre-trend: max abs of coefs at -5..-2
    pre = {k: v for k, v in coefs.items() if k.startswith("et_") and -5 <= float(k.split("_")[1]) <= -2}
    pre_max_abs = max([abs(v) for v in pre.values()] or [0.0])
    pre_min_p = min([pvals.get(k, 1.0) for k in pre.keys()] or [1.0])
    overall["pre_trend_max_abs"] = float(pre_max_abs)
    overall["pre_trend_min_p"] = float(pre_min_p)
    overall["pre_trend_pass"] = bool(pre_min_p > 0.10)
    return overall, event_profile, {}


def write_result_card(out: dict):
    overall = out.get("overall_att", {})
    event = out.get("event_study", {})
    md = []
    md.append(f"# Result card — {RUN_ID}")
    md.append("")
    md.append(f"**Estimator:** {out.get('method')}  ")
    md.append(f"**N obs:** {out.get('n_obs')}  ")
    md.append(f"**N treated cohorts:** {out.get('n_treated_countries')}  ")
    md.append(f"**N controls:** {out.get('n_control_countries')}  ")
    md.append(f"**Period:** {out.get('period')}")
    md.append("")
    md.append("## Overall ATT")
    md.append("```json")
    md.append(json.dumps(overall, indent=2, default=str))
    md.append("```")
    md.append("")
    md.append("## Event-study profile (-5 to +10 years)")
    md.append("```json")
    md.append(json.dumps(event, indent=2, default=str))
    md.append("```")
    md.append("")
    if isinstance(overall, dict) and "summary" in overall:
        overall = overall["summary"]
    md.append("## Pre-trend test")
    if isinstance(overall, dict) and "pre_trend_pass_zero_in_band" in overall:
        md.append(f"- Pre-trend max abs coef (-5..-2): {overall.get('pre_trend_max_abs'):.4f}")
        md.append(f"- Pre-trend pass (zero inside all pre-period CIs): **{overall.get('pre_trend_pass_zero_in_band')}**")
    elif isinstance(overall, dict) and "pre_trend_pass" in overall:
        md.append(f"- Pre-trend max abs coef (-5..-2): {overall.get('pre_trend_max_abs'):.4f}")
        md.append(f"- Pre-trend min p-value: {overall.get('pre_trend_min_p'):.3f}")
        md.append(f"- Pre-trend pass (min p > 0.10): **{overall.get('pre_trend_pass')}**")
    else:
        md.append("- Pre-trend test: see event_study coefficients at negative event times.")
    md.append("")
    md.append("## Verdict")
    if isinstance(overall, dict):
        att_val = overall.get("overall_att_simple") or overall.get("att_post_0_10_mean") or overall.get("att")
        passed = (att_val is not None) and (att_val > 0)
        pre_pass = overall.get("pre_trend_pass_zero_in_band", overall.get("pre_trend_pass", True))
        if passed and pre_pass:
            verdict = "SUPPORTED — ATT positive, pre-trends acceptable"
        elif passed and not pre_pass:
            verdict = "WEAKLY SUPPORTED — ATT positive but pre-trend fails (selection / shock confound likely)"
        else:
            verdict = "NOT SUPPORTED — ATT not positive"
        md.append(f"**{verdict}**")
        md.append(f"- Overall simple ATT (log points): {overall.get('overall_att_simple')}")
        md.append(f"- ATT post 0..10 mean (log points): {overall.get('att_post_0_10_mean')}")
    else:
        md.append("See diagnostics.json for full ATT(g,t) and aggregate decomposition.")
    md.append("")
    md.append("## Falsification rule")
    md.append("Per YAML: ATT(10y) > 0 at p<0.05 AND 3 of 4 canonical SC cases positive AND attenuation < 60% with institutional controls. This run executes the staggered-DiD piece only.")
    (OUT_DIR / "result_card.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
