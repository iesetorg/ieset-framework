#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = synth_did or synthetic_control.

Implements a simple synthetic-control / synth-DiD via least-squares
weighting over the donor pool. For each treated country (first in
sample.countries; rest are donors), find non-negative weights summing
to 1 that minimise the pre-treatment outcome RMSE. Compute the post-
treatment gap (treated minus weighted-donor) and the placebo
distribution by re-running with each donor as treated.

Verdict:
  SUPPORTED if observed gap is large (|gap| > 0.5×pre-period SD) AND
    sign matches claim direction AND placebo p-value < 0.10.
  REFUTED if sign opposite claim AND gap large AND placebo p < 0.10.
  PARTIAL otherwise.
  INCONCLUSIVE_DATA_PENDING if outcome data missing.

Usage:
  python3 scripts/run_synth_did.py [<hid> | --all]
"""
from __future__ import annotations

import argparse, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_panel_fe import (
    has_committed_verdict,
    ROOT, RUNS, load_spec, build_panel, infer_claim_direction, filter_sample,
)
from run_event_study import find_event_year


def list_specs() -> list[str]:
    with (ROOT / "engine/runnability.derived.yaml").open() as f:
        d = yaml.safe_load(f)
    return [h["hypothesis_id"] for h in d["hypotheses"]
            if h["estimator_template"] in ("synth_did", "synthetic_control")]


def fit_synthetic(panel: pd.DataFrame, outcome: str, treated: str,
                  donors: list[str], event_year: int) -> dict:
    """Closed-form synthetic-control via non-negative least squares on
    pre-period outcomes. Falls back to equal-weight if NNLS fails."""
    sub = panel[panel["country_iso3"].isin([treated] + donors)].copy()
    sub = sub.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"no data for {outcome}"}

    # Wide panel: index=year, columns=country
    wide = sub.pivot_table(index="year", columns="country_iso3", values=outcome,
                           aggfunc="mean")
    pre = wide[wide.index < event_year]
    post = wide[wide.index >= event_year]
    if treated not in wide.columns:
        return {"error": f"{treated} not in panel"}
    pre_treated = pre[treated].dropna()
    pre_donors_full = pre[donors].dropna(how="all", axis=1)
    pre_donors = pre_donors_full.dropna(axis=1)  # Donors with full pre-period coverage
    common_years = pre_treated.index.intersection(pre_donors.index)
    if len(common_years) < 4 or pre_donors.shape[1] < 2:
        return {"error": f"insufficient pre-period coverage (years={len(common_years)}, donors={pre_donors.shape[1]})"}
    Y_pre = pre_treated.loc[common_years].values
    X_pre = pre_donors.loc[common_years].values

    # Solve min ||Y - Xw||² s.t. w >= 0, sum(w)=1 — naïve via SciPy NNLS
    try:
        from scipy.optimize import nnls
        w_raw, _ = nnls(X_pre, Y_pre)
        if w_raw.sum() == 0:
            w = np.ones(X_pre.shape[1]) / X_pre.shape[1]
        else:
            w = w_raw / w_raw.sum()
    except Exception:
        w = np.ones(X_pre.shape[1]) / X_pre.shape[1]
    donor_names = list(pre_donors.columns)
    weights = dict(zip(donor_names, w.round(4).tolist()))

    pre_synth = X_pre @ w
    pre_rmse = float(np.sqrt(np.mean((Y_pre - pre_synth) ** 2)))
    pre_sd = float(np.std(Y_pre, ddof=1)) if len(Y_pre) > 1 else 0.0

    post_treated = post[treated].dropna()
    if post_treated.empty:
        return {"error": "no post-period treated obs"}
    post_donors = post[donor_names].dropna(how="any")
    if post_donors.empty:
        return {"error": "no post-period donor obs"}
    common_post = post_treated.index.intersection(post_donors.index)
    if len(common_post) == 0:
        return {"error": "no overlapping post-period years across treated + donors"}
    Y_post = post_treated.loc[common_post].values
    X_post = post_donors.loc[common_post, donor_names].values
    post_synth = X_post @ w
    gap = Y_post - post_synth
    end_gap = float(gap[-1])
    mean_gap = float(np.mean(gap))

    # Placebo: re-run with each donor as "treated"; compare absolute mean-gap to placebo distribution
    placebos: list[float] = []
    for d_idx, d in enumerate(donor_names):
        try:
            other_donors = [x for x in donor_names if x != d]
            X_pre_d = pre_donors[other_donors].loc[common_years].values
            Y_pre_d = pre_donors[d].loc[common_years].values
            try:
                w_d, _ = nnls(X_pre_d, Y_pre_d)
                w_d = w_d / w_d.sum() if w_d.sum() > 0 else np.ones(len(other_donors)) / len(other_donors)
            except Exception:
                w_d = np.ones(len(other_donors)) / len(other_donors)
            X_post_d = post_donors[other_donors].loc[common_post].values
            Y_post_d = pre_donors[d].loc[common_post].values if d in pre_donors.columns else None
            if Y_post_d is None or len(Y_post_d) == 0 or np.any(np.isnan(Y_post_d)):
                continue
            placebo_gap = float(np.mean(Y_post_d - X_post_d @ w_d))
            placebos.append(placebo_gap)
        except Exception:
            continue

    # Permutation p: fraction of placebos with |placebo_gap| >= |observed_gap|
    p_value = (1 + sum(1 for pg in placebos if abs(pg) >= abs(mean_gap))) / (1 + len(placebos))

    return {
        "shape": "synth_did",
        "treated_country": treated,
        "event_year": int(event_year),
        "n_donors": len(donor_names),
        "donor_weights": weights,
        "pre_rmse": pre_rmse,
        "pre_period_sd": pre_sd,
        "mean_post_gap": mean_gap,
        "end_period_gap": end_gap,
        "post_period_years": [int(common_post[0]), int(common_post[-1])],
        "placebo_p_value": float(p_value),
        "n_placebos": len(placebos),
        "method": "synthetic-control via NNLS, permutation inference",
    }


def verdict(est: dict, claim_dir: str) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]
    gap = est["mean_post_gap"]
    p = est["placebo_p_value"]
    sd = est["pre_period_sd"]
    big = sd > 0 and abs(gap) > 0.5 * sd
    sign = "+" if gap >= 0 else "-"
    mag = (f"mean_gap={gap:+.4g}, |gap|/pre_sd={abs(gap)/sd:.2g}, p_perm={p:.3g}"
           if sd > 0 else f"mean_gap={gap:+.4g}, p_perm={p:.3g}")
    if claim_dir == "?":
        return "PARTIAL", f"{mag}; claim direction ambiguous"
    if big and p < 0.10:
        if sign == claim_dir:
            return "SUPPORTED", f"sign matches claim {claim_dir}, {mag}"
        return "REFUTED", f"sign {sign} OPPOSITE claim {claim_dir}, {mag}"
    return "PARTIAL", f"{mag} (gap below 0.5×pre_sd or placebo p≥0.10)"


def write_outputs(hid: str, spec: dict, status: dict, est: dict,
                  v: str, reason: str) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    diag = {
        "verdict": f"{v} — {reason}",
        "verdict_label": v,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "synth_did",
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "estimate": est,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_synth_did.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))
    md = [
        f"# Result card — {hid}", "",
        f"**Verdict:** {v} — {reason}", "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}", "",
        "## Synthetic-control estimate",
    ]
    if "error" in est:
        md.append(f"- _Error:_ {est['error']}")
    else:
        for k, v_ in est.items():
            if k == "donor_weights":
                md.append(f"- **donor_weights** (top): {dict(sorted(v_.items(), key=lambda x: -x[1])[:5])}")
            else:
                md.append(f"- **{k}:** {v_}")
    md.append("")
    md.append("## Variables resolved")
    for v_ in status["variables_loaded"]:
        md.append(f"- `{v_['source']}` → {v_['name']} ({v_['role']}, n={v_['n_rows']})")
    md.append("")
    md.append(f"_Generated by `scripts/run_synth_did.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


def run_one(hid: str, force: bool = False) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if not found:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    panel, status = build_panel(spec)
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    if not outcome_items:
        v, r = "INCONCLUSIVE_DATA_PENDING", "no outcome variable"
        write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    o = outcome_items[0]["name"]
    if o not in panel.columns:
        v, r = "INCONCLUSIVE_DATA_PENDING", f"outcome '{o}' not loaded"
        write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    if len(countries) < 3:
        v, r = "INCONCLUSIVE_DATA_PENDING", f"need >= 3 countries (1 treated + 2 donors), got {len(countries)}"
        write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    event_year = find_event_year(spec)
    if event_year is None:
        period = sample.get("period") or [None, None]
        if all(period) and len(period) == 2:
            event_year = (period[0] + period[1]) // 2
        else:
            v, r = "INCONCLUSIVE_DATA_PENDING", "couldn't infer event_year"
            write_outputs(hid, spec, status, {"error": r}, v, r)
            return f"  ⚠ {hid}: {v}"
    panel_filt = filter_sample(panel, spec)
    treated, *donors = countries
    est = fit_synthetic(panel_filt, o, treated, donors, event_year)
    cd = infer_claim_direction(spec)
    v, r = verdict(est, cd)
    write_outputs(hid, spec, status, est, v, r)
    icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
            "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(v, " ")
    return f"  {icon} {hid}: {v} — {r}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("hypothesis_id", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing committed verdicts.")
    args = ap.parse_args()
    if args.all:
        ids = list_specs()
        print(f"Running {len(ids)} synth_did/synthetic_control specs…")
        for hid in ids:
            try: print(run_one(hid, force=args.force))
            except Exception as e:
                print(f"  ✗ {hid}: crashed — {e}")
                traceback.print_exc()
        return 0
    if not args.hypothesis_id:
        ap.error("Pass <hid> or --all")
    print(run_one(args.hypothesis_id, force=args.force))
    return 0


if __name__ == "__main__":
    sys.exit(main())
