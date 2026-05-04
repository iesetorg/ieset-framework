#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = cointegration_vecm.

This runner implements a conservative country-by-country Johansen
cointegration screen for two long-run macro series. It is intentionally narrow:
it can only graduate a hypothesis when the spec has already sharpened the
falsification rule and enough country series are available to test the
registered pair.

Verdict logic for the current IESET natural-rate shape:
  SUPPORTED                 - no cointegration in >=80% of tested countries.
  REFUTED                   - cointegration in >=50% of tested countries.
  PARTIAL                   - enough data, but neither decisive threshold clears.
  INCONCLUSIVE_DATA_PENDING - stub rule, missing data, missing statsmodels, or
                              insufficient country/time coverage.

Usage:
  python3 scripts/run_cointegration_vecm.py <hypothesis_id>
  python3 scripts/run_cointegration_vecm.py --all
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_panel_fe import (
    ROOT,
    RUNS,
    bump_bulk_run_count,
    build_panel,
    filter_sample,
    first_loaded_var,
    has_committed_verdict,
    infer_claim_direction,
    is_stub_falsification_rule,
    load_spec,
    print_bulk_run_summary,
    should_persist_preflight_inconclusive,
)


MIN_OBS_PER_COUNTRY = 20
MIN_TESTED_COUNTRIES = 8
SUPPORTED_NO_COINTEGRATION_SHARE = 0.80
REFUTED_COINTEGRATION_SHARE = 0.50


def list_specs() -> list[str]:
    with (ROOT / "engine/runnability.derived.yaml").open() as f:
        data = yaml.safe_load(f)
    return [
        row["hypothesis_id"]
        for row in data["hypotheses"]
        if row["estimator_template"] == "cointegration_vecm"
    ]


def select_pair(spec: dict, panel: pd.DataFrame) -> tuple[str | None, str | None, list[str]]:
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    treatment_items = var_blocks.get("treatment") or []

    candidates: list[str] = []
    for item in outcome_items:
        name = item.get("name")
        if name and name in panel.columns and panel[name].notna().any():
            candidates.append(name)

    # Fallback for future VECM specs that register one outcome plus one
    # long-run state variable as the "treatment" block.
    if len(candidates) < 2:
        t = first_loaded_var(treatment_items, panel)
        if t and t not in candidates:
            candidates.append(t)

    return (
        candidates[0] if len(candidates) >= 1 else None,
        candidates[1] if len(candidates) >= 2 else None,
        candidates,
    )


def johansen_country_result(
    country: str,
    country_panel: pd.DataFrame,
    var_a: str,
    var_b: str,
) -> dict:
    data = (
        country_panel.sort_values("year")[[var_a, var_b]]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    if len(data) < MIN_OBS_PER_COUNTRY:
        return {
            "country_iso3": country,
            "tested": False,
            "error": f"insufficient observations ({len(data)})",
        }
    if data[var_a].nunique(dropna=True) < 5 or data[var_b].nunique(dropna=True) < 5:
        return {
            "country_iso3": country,
            "tested": False,
            "error": "low variation in one or both series",
        }

    try:
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
    except Exception as exc:
        return {
            "country_iso3": country,
            "tested": False,
            "error": f"statsmodels Johansen test unavailable: {exc}",
        }

    try:
        result = coint_johansen(data.astype(float), det_order=0, k_ar_diff=1)
    except Exception as exc:
        return {
            "country_iso3": country,
            "tested": False,
            "error": f"Johansen test failed: {exc}",
        }

    trace_rank0 = float(result.lr1[0])
    cv90 = float(result.cvt[0, 0])
    cv95 = float(result.cvt[0, 1])
    cv99 = float(result.cvt[0, 2])
    cointegrated_90 = bool(trace_rank0 > cv90)
    cointegrated_95 = bool(trace_rank0 > cv95)
    return {
        "country_iso3": country,
        "tested": True,
        "n_obs": int(len(data)),
        "trace_rank0": trace_rank0,
        "critical_value_90": cv90,
        "critical_value_95": cv95,
        "critical_value_99": cv99,
        "cointegrated_at_10pct": cointegrated_90,
        "cointegrated_at_5pct": cointegrated_95,
        "year_min": int(country_panel["year"].min()),
        "year_max": int(country_panel["year"].max()),
    }


def fit_cointegration_panel(panel: pd.DataFrame, spec: dict, var_a: str, var_b: str) -> dict:
    if panel.empty or var_a not in panel.columns or var_b not in panel.columns:
        return {"error": f"pair not available in panel: {var_a}, {var_b}"}

    tests = []
    for country, country_panel in panel.groupby("country_iso3"):
        tests.append(johansen_country_result(str(country), country_panel, var_a, var_b))

    tested = [row for row in tests if row.get("tested")]
    if len(tested) < MIN_TESTED_COUNTRIES:
        return {
            "error": (
                f"only {len(tested)} tested countries; "
                f"cointegration screen requires >= {MIN_TESTED_COUNTRIES}"
            ),
            "country_tests": tests,
            "variables": [var_a, var_b],
        }

    cointegrated = [row for row in tested if row["cointegrated_at_10pct"]]
    cointegrated_share = len(cointegrated) / len(tested)
    no_cointegration_share = 1.0 - cointegrated_share
    return {
        "shape": "country_johansen_cointegration_screen",
        "variables": [var_a, var_b],
        "method": "Johansen trace test, rank-0 rejection at 10pct critical value",
        "n_tested_countries": int(len(tested)),
        "n_cointegrated_10pct": int(len(cointegrated)),
        "cointegrated_share_10pct": float(cointegrated_share),
        "no_cointegration_share_10pct": float(no_cointegration_share),
        "supported_no_cointegration_share_threshold": SUPPORTED_NO_COINTEGRATION_SHARE,
        "refuted_cointegration_share_threshold": REFUTED_COINTEGRATION_SHARE,
        "country_tests": tests,
    }


def compute_verdict(est: dict) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]

    no_coint_share = est["no_cointegration_share_10pct"]
    coint_share = est["cointegrated_share_10pct"]
    n = est["n_tested_countries"]
    pair = ", ".join(est["variables"])
    summary = (
        f"{pair}: no-cointegration share={no_coint_share:.1%}, "
        f"cointegration share={coint_share:.1%}, tested countries={n}"
    )
    if no_coint_share >= SUPPORTED_NO_COINTEGRATION_SHARE:
        return "SUPPORTED", summary
    if coint_share >= REFUTED_COINTEGRATION_SHARE:
        return "REFUTED", summary
    return "PARTIAL", f"{summary}; neither decisive threshold clears"


def write_outputs(
    hid: str,
    spec: dict,
    status: dict,
    est: dict,
    verdict: str,
    reason: str,
) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "cointegration_vecm",
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": est,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_cointegration_vecm.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))

    md = [
        f"# Result card - {hid}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim', '').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule', '').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test', '').strip()}",
        "",
        "## Cointegration Screen",
    ]
    if "error" in est:
        md.append(f"- _Error:_ {est['error']}")
    else:
        md.append(f"- Method: {est['method']}")
        md.append(f"- Pair: `{est['variables'][0]}` and `{est['variables'][1]}`")
        md.append(f"- Tested countries: {est['n_tested_countries']}")
        md.append(f"- No-cointegration share: {est['no_cointegration_share_10pct']:.1%}")
        md.append(f"- Cointegration share: {est['cointegrated_share_10pct']:.1%}")
        md.append("")
        md.append("| Country | n | trace r=0 | cv90 | cointegrated at 10pct |")
        md.append("|---|---:|---:|---:|---|")
        for row in est.get("country_tests") or []:
            if row.get("tested"):
                md.append(
                    f"| {row['country_iso3']} | {row['n_obs']} | "
                    f"{row['trace_rank0']:.3g} | {row['critical_value_90']:.3g} | "
                    f"{row['cointegrated_at_10pct']} |"
                )
            else:
                md.append(f"| {row['country_iso3']} | - | - | - | {row.get('error')} |")

    md.append("")
    md.append("## Variables resolved")
    for item in status.get("variables_loaded") or []:
        md.append(
            f"- `{item['source']}` -> {item['name']} "
            f"({item['role']}, publisher={item['publisher']}, n={item['n_rows']})"
        )
    if status.get("variables_missing"):
        md.append("")
        md.append("### Variables missing data")
        for item in status["variables_missing"]:
            md.append(f"- `{item['source']}` ({item['role']}, name={item['name']})")
    md.append("")
    md.append(
        f"_Generated by `scripts/run_cointegration_vecm.py` at "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_"
    )
    (out_dir / "result_card.md").write_text("\n".join(md))


def run_one(
    hid: str,
    force: bool = False,
    persist_preflight_inconclusive: bool = True,
) -> str:
    if not force and has_committed_verdict(hid):
        return f"  * {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if not found:
        return f"  x {hid}: spec not found"
    _, spec = found

    if is_stub_falsification_rule(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "falsification rule not sharpened - auto-grader refuses to grade "
            "against generic stub boilerplate. Promote the spec with a "
            "dispositive threshold and methodology_note before running."
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
        return f"  ! {hid}: {verdict}{suffix}"

    panel, status = build_panel(spec)
    panel_filt = filter_sample(panel, spec)
    var_a, var_b, candidates = select_pair(spec, panel_filt)
    if var_a is None or var_b is None:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = f"fewer than two loaded cointegration variables: {candidates}"
        if should_persist_preflight_inconclusive(reason, persist_preflight_inconclusive):
            write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ! {hid}: {verdict} - {reason}"

    est = fit_cointegration_panel(panel_filt, spec, var_a, var_b)
    verdict, reason = compute_verdict(est)
    write_outputs(hid, spec, status, est, verdict, reason)
    return f"  * {hid}: {verdict} - {reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?", help="Run one hypothesis id.")
    parser.add_argument("--all", action="store_true", help="Run all cointegration_vecm specs.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts.",
    )
    args = parser.parse_args()

    if args.all:
        counts: dict[str, int] = {}
        for hid in list_specs():
            try:
                msg = run_one(
                    hid,
                    force=args.force,
                    persist_preflight_inconclusive=args.write_preflight_inconclusive,
                )
                print(msg)
                bump_bulk_run_count(counts, msg)
            except Exception:
                traceback.print_exc()
                counts["crashed"] = counts.get("crashed", 0) + 1
        print_bulk_run_summary("cointegration_vecm bulk run", counts)
        return 0

    if not args.hypothesis_id:
        parser.error("provide hypothesis_id or --all")
    print(
        run_one(
            args.hypothesis_id,
            force=args.force,
            persist_preflight_inconclusive=args.write_preflight_inconclusive,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
