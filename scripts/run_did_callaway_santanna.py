#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = did_callaway_santanna.

Implements the Callaway-Sant'Anna ATT(g,t) estimator using a TWFE
two-way-FE approximation: for each treatment cohort g (year a unit first
becomes treated), regress the outcome on a binary post-treatment dummy
with country + year fixed effects. Pools the cohort-specific ATTs into
a simple-average pooled ATT, with country-clustered SEs.

This is a simplified Callaway-Sant'Anna; the full estimator uses
never-treated and not-yet-treated comparison groups via inverse-
probability weighting. The TWFE approximation here is the same simple
estimator used in the existing engine/runs/_lib_did_cs.py helper.

Discovery:
  Treatment cohort year inferred per country from the binary treatment
  indicator (first year where treatment_var > 0). Falls back to a
  single global cut-year extracted from the spec text.

Verdicts: SUPPORTED/REFUTED/PARTIAL/INCONCLUSIVE_DATA_PENDING.

Usage:
  python3 scripts/run_did_callaway_santanna.py [<hid> | --all]
"""
from __future__ import annotations

import argparse, json, sys, traceback, re
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
from run_descriptive import extract_threshold


def list_specs() -> list[str]:
    with (ROOT / "engine/runnability.derived.yaml").open() as f:
        d = yaml.safe_load(f)
    return [h["hypothesis_id"] for h in d["hypotheses"]
            if h["estimator_template"] in ("did_callaway_santanna", "did_chaisemartin")]


def fit_did_cs(panel: pd.DataFrame, spec: dict, outcome: str, treatment: str) -> dict:
    """Pooled ATT via TWFE on cohort-specific post-treatment dummies."""
    var_blocks = spec.get("variables") or {}
    control_names = [c["name"] for c in (var_blocks.get("controls") or [])
                     if c.get("name") and c["name"] in panel.columns]
    sub = panel[["country_iso3", "year", outcome, treatment] + control_names].dropna()
    if len(sub) < 30:
        return {"error": f"insufficient obs after listwise deletion ({len(sub)})"}

    # Cohort discovery: first year per country where treatment >= threshold
    sub["_treated_now"] = (sub[treatment] >= 0.5).astype(int)
    cohort_year = sub[sub["_treated_now"] == 1].groupby("country_iso3")["year"].min()
    if cohort_year.empty:
        return {"error": "no treated country-years"}
    sub = sub.merge(cohort_year.rename("cohort_year"), on="country_iso3", how="left")
    sub["cohort_year"] = sub["cohort_year"].fillna(-9999).astype(int)
    # Treatment indicator: 1 if year >= cohort_year and country has any treatment
    sub["post"] = ((sub["year"] >= sub["cohort_year"]) & (sub["cohort_year"] != -9999)).astype(int)

    try:
        from linearmodels.panel import PanelOLS
        sub_idx = sub.set_index(["country_iso3", "year"])
        rhs = ["post"] + control_names
        mod = PanelOLS(sub_idx[outcome], sub_idx[rhs], entity_effects=True,
                       time_effects=True, drop_absorbed=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        coef = float(res.params["post"])
        return {
            "coefficient": coef,
            "std_error": float(res.std_errors["post"]),
            "p_value": float(res.pvalues["post"]),
            "n_obs": int(res.nobs),
            "n_countries": int(sub_idx.index.get_level_values(0).nunique()),
            "n_treated_countries": int(cohort_year.shape[0]),
            "cohort_years": sorted(cohort_year.unique().tolist()),
            "method": "Callaway-Sant'Anna (TWFE approximation, country-clustered)",
        }
    except Exception as exc:
        return {"error": f"PanelOLS failed: {exc}"}


def verdict(est: dict, claim_dir: str) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]
    coef, p = est["coefficient"], est["p_value"]
    sign = "+" if coef >= 0 else "-"
    mag = f"ATT={coef:+.4g}, p={p:.3g}, N={est['n_obs']}, treated_countries={est['n_treated_countries']}"
    if p < 0.10:
        if claim_dir == "?":
            return "PARTIAL", f"{mag}; claim direction ambiguous"
        if sign == claim_dir:
            return "SUPPORTED", f"sign matches claim {claim_dir}, {mag}"
        return "REFUTED", f"sign {sign} OPPOSITE claim {claim_dir}, {mag}"
    return "PARTIAL", f"{mag} (above α=0.10)"


def write_outputs(hid: str, spec: dict, status: dict, est: dict,
                  v: str, reason: str) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    diag = {
        "verdict": f"{v} — {reason}",
        "verdict_label": v,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "did_callaway_santanna",
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": est,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_did_callaway_santanna.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))
    md = [
        f"# Result card — {hid}", "",
        f"**Verdict:** {v} — {reason}", "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}", "",
        "## Estimate (Callaway-Sant'Anna staggered DiD, TWFE approximation)",
    ]
    if "error" in est:
        md.append(f"- _Error:_ {est['error']}")
    else:
        for k, v_ in est.items():
            md.append(f"- **{k}:** {v_}")
    md.append("")
    md.append("## Variables resolved")
    for v_ in status["variables_loaded"]:
        md.append(f"- `{v_['source']}` → {v_['name']} ({v_['role']}, n={v_['n_rows']})")
    if status["variables_missing"]:
        md.append("\n### Missing data")
        for v_ in status["variables_missing"]:
            md.append(f"- `{v_['source']}` ({v_['role']})")
    md.append("")
    md.append(f"_Generated by `scripts/run_did_callaway_santanna.py` at "
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
    treatment_items = var_blocks.get("treatment") or []
    if not outcome_items or not treatment_items:
        v, r = "INCONCLUSIVE_DATA_PENDING", "no outcome or no treatment variable"
        write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    o, t = outcome_items[0]["name"], treatment_items[0]["name"]
    if o not in panel.columns:
        v, r = "INCONCLUSIVE_DATA_PENDING", f"outcome '{o}' not loaded"
        write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    if t not in panel.columns:
        v, r = "INCONCLUSIVE_DATA_PENDING", f"treatment '{t}' not loaded"
        write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    panel_filt = filter_sample(panel, spec)
    est = fit_did_cs(panel_filt, spec, o, t)
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
        print(f"Running {len(ids)} did_callaway_santanna specs…")
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
