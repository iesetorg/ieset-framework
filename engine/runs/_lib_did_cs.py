"""Shared utilities for Callaway-Sant'Anna staggered DiD replications."""
from __future__ import annotations

import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def df_to_records(x):
    try:
        if hasattr(x, "reset_index"):
            rec = x.reset_index().to_dict(orient="records")
            return [{str(k): (str(v) if isinstance(v, tuple) else v) for k, v in r.items()} for r in rec]
        if hasattr(x, "to_dict"):
            return {str(k): v for k, v in x.to_dict().items()}
    except Exception:
        pass
    return str(x)


def cs_did(panel: pd.DataFrame, outcome_col: str, cohort_col: str = "cohort",
           control_group: str = "not_yet_treated", entity_col: str = "country",
           time_col: str = "year"):
    """Run Callaway-Sant'Anna DiD via differences library.

    Returns (overall_records, event_records, cohort_records, summary).
    Pre-trend pass: zero inside CIs for relative_period in [-5,-2].
    """
    from differences import ATTgt
    p = panel[[entity_col, time_col, outcome_col, cohort_col]].copy()
    p = p.dropna(subset=[outcome_col]).reset_index(drop=True)
    # cohort = NaN for never-treated
    p[cohort_col] = p[cohort_col].where(p[cohort_col].notna() & (p[cohort_col] != 0), np.nan)
    p = p.set_index([entity_col, time_col])
    att = ATTgt(data=p, cohort_column=cohort_col)
    att.fit(formula=outcome_col, control_group=control_group, progress_bar=False)
    overall = df_to_records(att.aggregate("simple"))
    event = df_to_records(att.aggregate("event"))
    cohort_agg = df_to_records(att.aggregate("cohort"))

    def find_col(cols, *tokens):
        for c in cols:
            s = str(c).lower()
            if all(t in s for t in tokens):
                return c
        return None

    summary = {}
    if isinstance(event, list) and event:
        cols = list(event[0].keys())
        et_col = find_col(cols, "relative_period") or cols[0]
        att_col = find_col(cols, "att") or cols[1]
        lower_col = find_col(cols, "lower")
        upper_col = find_col(cols, "upper")

        def evt(r):
            try:
                return float(r.get(et_col))
            except Exception:
                return None

        post = [r for r in event if evt(r) is not None and 0 <= evt(r) <= 10]
        pre = [r for r in event if evt(r) is not None and -5 <= evt(r) <= -2]
        post_atts = [float(r[att_col]) for r in post]
        pre_pass = True
        for r in pre:
            lo, hi = r.get(lower_col), r.get(upper_col)
            if lo is not None and hi is not None and (lo > 0 or hi < 0):
                pre_pass = False
                break
        summary["att_post_0_10_mean"] = float(np.mean(post_atts)) if post_atts else None
        summary["n_post_bins"] = len(post_atts)
        summary["pre_trend_max_abs"] = float(max([abs(float(r[att_col])) for r in pre] or [0.0]))
        summary["pre_trend_pass_zero_in_band"] = bool(pre_pass)
        summary["event_window_used"] = "[-5, +10]"
    if isinstance(overall, list) and overall:
        sa_cols = list(overall[0].keys())
        sa_att = next((c for c in sa_cols if "ATT" in str(c) and "lower" not in str(c) and "upper" not in str(c) and "std_error" not in str(c)), None)
        if sa_att:
            summary["overall_att_simple"] = float(overall[0][sa_att])
    return overall, event, cohort_agg, summary


def write_result_card(out_path: Path, run_id: str, out: dict, falsification_rule: str = ""):
    overall = out.get("overall_att", {})
    event = out.get("event_study", {})
    md = []
    md.append(f"# Result card — {run_id}")
    md.append("")
    md.append(f"**Estimator:** {out.get('method')}  ")
    md.append(f"**N obs:** {out.get('n_obs')}  ")
    md.append(f"**N treated:** {out.get('n_treated_countries')}  ")
    md.append(f"**N controls:** {out.get('n_control_countries')}  ")
    md.append(f"**Period:** {out.get('period')}  ")
    md.append(f"**Outcome:** {out.get('outcome')}")
    md.append("")
    summary = overall.get("summary") if isinstance(overall, dict) and "summary" in overall else overall
    md.append("## Overall ATT (Callaway-Sant'Anna SimpleAggregation)")
    if isinstance(summary, dict):
        if "overall_att_simple" in summary:
            md.append(f"- **ATT (simple): {summary['overall_att_simple']:.4f}** log points")
        if "att_post_0_10_mean" in summary and summary["att_post_0_10_mean"] is not None:
            md.append(f"- ATT (post 0..10 mean): {summary['att_post_0_10_mean']:.4f}")
        md.append("")
    md.append("## Event-study profile")
    md.append("Full event-time records in diagnostics.json. Selected rows:")
    md.append("")
    if isinstance(event, list):
        cols = list(event[0].keys()) if event else []
        et_col = next((c for c in cols if "relative_period" in str(c)), cols[0] if cols else None)
        att_col = next((c for c in cols if "ATT" in str(c) and "std" not in str(c) and "lower" not in str(c) and "upper" not in str(c)), None)
        lo_col = next((c for c in cols if "lower" in str(c)), None)
        hi_col = next((c for c in cols if "upper" in str(c)), None)
        md.append("| event time | ATT | 95% lower | 95% upper |")
        md.append("|---:|---:|---:|---:|")
        for r in event:
            try:
                t = float(r.get(et_col))
            except Exception:
                continue
            if -5 <= t <= 10:
                md.append(f"| {int(t)} | {r.get(att_col):.4f} | {r.get(lo_col):.4f} | {r.get(hi_col):.4f} |")
    md.append("")
    md.append("## Pre-trend test")
    if isinstance(summary, dict) and "pre_trend_pass_zero_in_band" in summary:
        md.append(f"- Max abs ATT in pre-window (-5..-2): {summary.get('pre_trend_max_abs'):.4f}")
        md.append(f"- Pre-trend pass (zero inside all pre-period 95% CIs): **{summary.get('pre_trend_pass_zero_in_band')}**")
    md.append("")
    md.append("## Verdict")
    att_val = (summary or {}).get("overall_att_simple") if isinstance(summary, dict) else None
    pre_pass = (summary or {}).get("pre_trend_pass_zero_in_band", True) if isinstance(summary, dict) else True
    expected_sign = out.get("expected_sign", "positive")
    sign_ok = att_val is not None and ((expected_sign == "positive" and att_val > 0) or
                                       (expected_sign == "negative" and att_val < 0))
    if sign_ok and pre_pass:
        verdict = f"SUPPORTED — ATT in expected direction ({expected_sign}); pre-trends acceptable"
    elif sign_ok and not pre_pass:
        verdict = f"WEAKLY SUPPORTED — ATT in expected direction but pre-trend fails; weaken claim"
    elif att_val is None:
        verdict = "INCONCLUSIVE — could not compute ATT"
    else:
        verdict = f"NOT SUPPORTED — ATT not in expected direction (expected {expected_sign}, got {att_val:.4f})"
    md.append(f"**{verdict}**")
    md.append("")
    md.append("## Falsification rule (from YAML)")
    md.append(falsification_rule.strip())
    md.append("")
    out_path.write_text("\n".join(md))
