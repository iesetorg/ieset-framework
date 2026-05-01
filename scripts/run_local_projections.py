#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = local_projections.

Implements Jordà local projections: at each horizon h = 0..H, regress
y_{t+h} on the treatment shock at t, with country + time FE and
country-clustered SEs. Reports the impulse response (LP coefficient
path) and the pooled cumulative effect over the post-shock window.

Verdict logic uses the cumulative coefficient: SUPPORTED if cumulative
sign matches claim AND p-value at h=H < 0.10; REFUTED if opposite;
PARTIAL otherwise.

Usage:
  python3 scripts/run_local_projections.py [<hid> | --all]
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
    is_stub_falsification_rule,    has_committed_verdict,
    ROOT, RUNS, load_spec, build_panel, infer_claim_direction, filter_sample,
    first_loaded_var, construct_treatment_from_text,
    should_persist_preflight_inconclusive,
    bump_bulk_run_count, print_bulk_run_summary, fit_fe_ols_fallback,
    prune_controls_for_overlap,
)


HORIZONS = list(range(0, 6))  # h=0..5


def list_specs() -> list[str]:
    with (ROOT / "engine/runnability.derived.yaml").open() as f:
        d = yaml.safe_load(f)
    return [h["hypothesis_id"] for h in d["hypotheses"]
            if h["estimator_template"] == "local_projections"]


def fit_lp(panel: pd.DataFrame, spec: dict, outcome: str, treatment: str) -> dict:
    var_blocks = spec.get("variables") or {}
    control_names = [c["name"] for c in (var_blocks.get("controls") or [])
                     if c.get("name") and c["name"] in panel.columns]
    sub, usable_controls, dropped_controls = prune_controls_for_overlap(
        panel,
        [outcome, treatment],
        control_names,
        min_obs=50,
    )
    if len(sub) < 50:
        return {"error": f"insufficient obs ({len(sub)}); LP needs >=50"}

    # For each horizon h, build y_{t+h} and regress on treatment_t
    coefficients = []
    try:
        rhs = [treatment] + usable_controls
        for h in HORIZONS:
            sub_h = sub.copy()
            sub_h[f"y_h{h}"] = sub_h.groupby("country_iso3")[outcome].shift(-h)
            sub_h = sub_h.dropna(subset=[f"y_h{h}", treatment])
            if len(sub_h) < 30:
                coefficients.append({"horizon": h, "error": f"insufficient at h={h}"})
                continue
            try:
                from linearmodels.panel import PanelOLS
                sub_idx = sub_h.set_index(["country_iso3", "year"])
                mod = PanelOLS(sub_idx[f"y_h{h}"], sub_idx[rhs],
                               entity_effects=True, time_effects=True,
                               drop_absorbed=True)
                res = mod.fit(cov_type="clustered", cluster_entity=True)
                coefficients.append({
                    "horizon": h,
                    "coefficient": float(res.params[treatment]),
                    "std_error": float(res.std_errors[treatment]),
                    "p_value": float(res.pvalues[treatment]),
                    "n_obs": int(res.nobs),
                })
            except Exception as exc:
                fallback = fit_fe_ols_fallback(
                    sub_h.reset_index(drop=True),
                    f"y_h{h}",
                    rhs,
                    treatment,
                    entity=True,
                    time=True,
                    cluster_spec="country",
                    method_label=f"LP fallback h={h} (linearmodels failed: {exc})",
                )
                if "error" in fallback:
                    coefficients.append({"horizon": h, "error": str(exc)})
                else:
                    coefficients.append({
                        "horizon": h,
                        "coefficient": fallback["coefficient"],
                        "std_error": fallback["std_error"],
                        "p_value": fallback["p_value"],
                        "n_obs": fallback["n_obs"],
                    })
        # Cumulative effect = sum of coefficients across horizons
        valid = [c for c in coefficients if "coefficient" in c]
        if not valid:
            return {"error": "no valid horizons"}
        cumul = sum(c["coefficient"] for c in valid)
        # Use h=H (last valid) p-value as the headline significance
        last = valid[-1]
        return {
            "shape": "local_projections",
            "horizons": coefficients,
            "cumulative_coefficient": float(cumul),
            "horizon_h_coefficient": last["coefficient"],
            "horizon_h_std_error": last["std_error"],
            "horizon_h_p_value": last["p_value"],
            "max_horizon": last["horizon"],
            "n_countries": int(sub["country_iso3"].nunique()),
            "method": "Jordà local projections (TWFE, country-clustered)",
            "dropped_controls_due_to_overlap": dropped_controls,
        }
    except Exception as exc:
        return {"error": f"LP failed: {exc}"}


def compute_verdict(est: dict, claim_dir: str) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]
    cumul = est["cumulative_coefficient"]
    p = est["horizon_h_p_value"]
    sign = "+" if cumul >= 0 else "-"
    mag = (f"cumulative_effect={cumul:+.4g}, h={est['max_horizon']}, "
           f"p_h={p:.3g}")
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
        "template": "local_projections",
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "estimate": est,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_local_projections.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))
    md = [
        f"# Result card — {hid}", "",
        f"**Verdict:** {v} — {reason}", "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}", "",
        "## Local-projections IRF",
    ]
    if "error" in est:
        md.append(f"- _Error:_ {est['error']}")
    else:
        md.append(f"- Method: {est.get('method')}")
        md.append(f"- Cumulative effect: **{est['cumulative_coefficient']:+.4g}**")
        md.append(f"- Final-horizon p-value: {est['horizon_h_p_value']:.3g}")
        md.append("")
        md.append("| h | β | SE | p | n |")
        md.append("|---|---|---|---|---|")
        for c in est.get("horizons") or []:
            if "coefficient" in c:
                md.append(f"| {c['horizon']} | {c['coefficient']:+.4g} | "
                          f"{c['std_error']:.3g} | {c['p_value']:.3g} | {c['n_obs']} |")
            else:
                md.append(f"| {c['horizon']} | _err_ | _err_ | _err_ | — |")
    md.append("")
    md.append("## Variables resolved")
    for v_ in status["variables_loaded"]:
        md.append(f"- `{v_['source']}` → {v_['name']} ({v_['role']}, n={v_['n_rows']})")
    md.append("")
    md.append(f"_Generated by `scripts/run_local_projections.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


def run_one(
    hid: str,
    force: bool = False,
    persist_preflight_inconclusive: bool = True,
) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if not found:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    # Integrity gate: refuse to grade against a stub falsification rule.
    # The auto-grader's verdicts are only meaningful against a dispositive
    # pre-registered threshold; running against the generic boilerplate
    # ("…when this stub is promoted from draft") would attach a fake-clean
    # verdict to a non-promoted spec. See post-mortem (commit bba6f644).
    if is_stub_falsification_rule(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "falsification rule not sharpened — auto-grader refuses to "
            "grade against the generic stub boilerplate. Promote the spec "
            "(replace falsification.rule with a dispositive threshold AND "
            "document the sharpening in methodology_note) before running."
        )
        persisted = should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        )
        if persisted:
            write_outputs(
                hid,
                spec,
                {"variables_loaded": [], "variables_missing": []},
                {"error": reason},
                verdict,
                reason,
            )
        suffix = " (stub rule, refused to grade)"
        if not persisted:
            suffix += " [artifact skipped]"
        return f"  ⚠ {hid}: {verdict}{suffix}"

    panel, status = build_panel(spec)
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    treatment_items = var_blocks.get("treatment") or []
    if not outcome_items or not treatment_items:
        v, r = "INCONCLUSIVE_DATA_PENDING", "no outcome or no treatment variable"
        if should_persist_preflight_inconclusive(r, persist_preflight_inconclusive):
            write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    panel_filt = filter_sample(panel, spec)
    o = first_loaded_var(outcome_items, panel_filt)
    t = first_loaded_var(treatment_items, panel_filt)
    if t is None:
        built = construct_treatment_from_text(spec, panel_filt)
        if built is not None:
            panel_filt, t = built
    if o is None or t is None:
        missing = []
        if o is None: missing += [item.get("source") for item in outcome_items]
        if t is None: missing += [item.get("source") for item in treatment_items]
        v, r = "INCONCLUSIVE_DATA_PENDING", f"variables not loaded: {missing}"
        if should_persist_preflight_inconclusive(r, persist_preflight_inconclusive):
            write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    est = fit_lp(panel_filt, spec, o, t)
    cd = infer_claim_direction(spec)
    v, r = compute_verdict(est, cd)
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
    ap.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts during bulk runs.",
    )
    args = ap.parse_args()
    persist_preflight = args.write_preflight_inconclusive or not args.all
    if args.all:
        ids = list_specs()
        counts: dict[str, int] = {}
        print(f"Running {len(ids)} local_projections specs…")
        for hid in ids:
            try:
                msg = (
                    run_one(
                        hid,
                        force=args.force,
                        persist_preflight_inconclusive=persist_preflight,
                    )
                )
                print(msg)
                bump_bulk_run_count(counts, msg)
            except Exception as e:
                print(f"  ✗ {hid}: crashed — {e}")
                counts["crashed"] = counts.get("crashed", 0) + 1
                traceback.print_exc()
        print_bulk_run_summary("local_projections", counts)
        return 0
    if not args.hypothesis_id:
        ap.error("Pass <hid> or --all")
    print(
        run_one(
            args.hypothesis_id,
            force=args.force,
            persist_preflight_inconclusive=persist_preflight,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
