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
    is_stub_falsification_rule,    has_committed_verdict,
    ROOT, RUNS, VINTAGES, load_spec, build_panel, infer_claim_direction, filter_sample,
    first_loaded_var, construct_treatment_from_text,
    should_persist_preflight_inconclusive,
    bump_bulk_run_count, print_bulk_run_summary, fit_fe_ols_fallback,
    prune_controls_for_overlap,
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
    sub, usable_controls, dropped_controls = prune_controls_for_overlap(
        panel,
        [outcome, treatment],
        control_names,
        min_obs=30,
    )
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
    sub_plain = sub.copy()

    try:
        from linearmodels.panel import PanelOLS
        sub_idx = sub.set_index(["country_iso3", "year"])
        rhs = ["post"] + usable_controls
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
            "dropped_controls_due_to_overlap": dropped_controls,
        }
    except Exception as exc:
        fallback = fit_fe_ols_fallback(
            sub_plain,
            outcome,
            ["post"] + usable_controls,
            "post",
            entity=True,
            time=True,
            cluster_spec="country",
            method_label=f"Callaway-Sant'Anna TWFE fallback (linearmodels failed: {exc})",
        )
        if "error" in fallback:
            return fallback
        fallback["n_treated_countries"] = int(cohort_year.shape[0])
        fallback["cohort_years"] = sorted(cohort_year.unique().tolist())
        fallback["dropped_controls_due_to_overlap"] = dropped_controls
        return fallback


def compute_verdict(est: dict, claim_dir: str) -> tuple[str, str]:
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
                  v: str, reason: str, extra_diag: dict | None = None,
                  extra_sections: list[tuple[str, list[str]]] | None = None) -> None:
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
    if extra_diag:
        diag.update(extra_diag)
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
    for title, lines in extra_sections or []:
        md.append("")
        md.append(f"## {title}")
        md.extend(lines)
    md.append("")
    md.append(f"_Generated by `scripts/run_did_callaway_santanna.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


MINIMUM_WAGE_DATA_GATES = {
    "minimum_wage_employment_effect_us_states": {
        "required": [
            {
                "role": "outcome",
                "name": "teen_employment_to_population_ratio",
                "publisher": "bls",
                "series": "LAU_state_teen_employment_population_ratio_panel",
                "repair": (
                    "BLS/CPS-LAU state panel for ages 16-19, keyed by state and year, "
                    "covering 1990-2024 with at least 40 states and 20 years per state."
                ),
            },
            {
                "role": "treatment",
                "name": "state_minimum_wage_log_level",
                "publisher": "usdol",
                "series": "state_minimum_wage_history",
                "repair": (
                    "USDOL state statutory minimum-wage history, keyed by state and year, "
                    "with federal-floor fallback and at least 30 states with binding state changes."
                ),
            },
        ],
        "secondary": [
            "bls:CES_state_NAICS722_employment_panel for state accommodation/food-services employment.",
            "bls:QCEW_county_NAICS722_employment_panel plus manual:vaghul_zipperer_county_minimum_wage for the border-pair robustness.",
            "bls:LAU_state_unemployment_rate_panel and fred:state_real_gdp_panel for controls.",
        ],
        "incompatible_local": [
            "fred:LNS12300012 is national teen E/P, not a state panel.",
            "fred:STTMINWGCA is California's minimum wage exemplar, not the USDOL all-state history.",
            "fred:NYNGSP is New York GSP exemplar, not an all-state GDP panel.",
            "bls:CES* vintages currently on disk are national/current-window CES series, not state NAICS-722 panels.",
        ],
        "runner_limitation": (
            "The generic DID runner currently normalizes vintages to country_iso3/year. "
            "A clean state-level verdict needs either a subnational unit_id path in this runner "
            "or a pre-derived state-year panel that the runner can treat as the estimation unit."
        ),
    },
    "minimum_wage_above_median_employment_teen_effects": {
        "required": [
            {
                "role": "outcome",
                "name": "teen_employment_to_population_ratio_high_bite",
                "publisher": "bls",
                "series": "LAU_state_teen_employment_population_ratio_panel",
                "repair": (
                    "US state/city teen employment-to-population panel for high-bite cases, "
                    "keyed by subnational unit and year."
                ),
            },
            {
                "role": "outcome",
                "name": "wage_at_10th_percentile",
                "publisher": "bls",
                "series": "OEWS_state_p10_hourly_wage_panel",
                "repair": (
                    "BLS OEWS state p10 hourly wage panel, paired with median wages so the "
                    "first-order wage effect and bite ratio can be tested honestly."
                ),
            },
            {
                "role": "treatment",
                "name": "minimum_wage_bite_ratio",
                "publisher": "derived",
                "series": "minimum_wage_bite_ratio_subnational_panel",
                "repair": (
                    "Constructed statutory minimum / local age-specific median wage panel for "
                    "Seattle, NYC fast-food, California, UK NLW regions, and German Mindestlohn cases."
                ),
            },
        ],
        "secondary": [
            "ons:ASHE_regional_p10_hourly_wage_panel and uk_low_pay_commission:NLW_history for UK regions.",
            "destatis:VSE_kreis_p10_hourly_wage_panel and destatis:german_minimum_wage_history for German Kreise.",
            "oecd:regional_neet_15_24_panel or national-statistical regional NEET panels for third-order persistence.",
            "Subnational sector composition and adult unemployment controls keyed to the same unit-year frame.",
        ],
        "incompatible_local": [
            "world_bank_wdi:NY.GDP.MKTP.KD is only a national GDP control proxy; it cannot identify high-bite subregional treatment.",
            "The current BLS vintages are national LNS/CES/CUUR extracts and do not include LAU/OEWS/QCEW subnational panels.",
            "No ONS ASHE/APS/BRES or Destatis Mikrozensus/VSE subregional wage-employment vintages are on disk.",
        ],
        "runner_limitation": (
            "The five-case high-bite design is subnational and multi-country. The runner needs "
            "unit_id-level panel support before these fetched sources can be estimated without "
            "collapsing the design to country-year aggregates."
        ),
    },
    "minimum_wage_disemployment_at_high_bite_ratios": {
        "required": [
            {
                "role": "outcome",
                "name": "teen_employment_to_population",
                "publisher": "bls",
                "series": "LAU_state_teen_employment_population_ratio_panel",
                "repair": (
                    "BLS/CPS-LAU state teen employment-to-population panel, keyed by "
                    "state and year. The national FRED LNS12300012 series is useful "
                    "context but cannot identify high-bite state cohorts."
                ),
            },
            {
                "role": "treatment",
                "name": "state_minimum_wage",
                "publisher": "usdol",
                "series": "state_minimum_wage_history",
                "repair": (
                    "USDOL all-state statutory minimum-wage history with federal-floor "
                    "fallback and binding-change flags."
                ),
            },
            {
                "role": "treatment",
                "name": "minimum_to_median_wage_ratio",
                "publisher": "bls",
                "series": "OES_state_median_hourly_wage_panel",
                "repair": (
                    "BLS OES/OEWS state median hourly wage panel to construct the local "
                    "minimum-to-median bite ratio used for high-bite stratification."
                ),
            },
        ],
        "secondary": [
            "bls:QCEW_county_NAICS722_employment_panel for border-pair and low-wage-sector robustness.",
            "oecd:MWUSD_minimum_to_median_wage_ratio for cross-country descriptive context only.",
            "oecd:DSD_LMS_low_education_unemployment_rate for non-US robustness after native OECD keying is wired.",
        ],
        "incompatible_local": [
            "fred:LNS12300012 is national teen E/P, not the state panel required by the preregistered DiD.",
            "fred:STTMINWGCA is a California exemplar, not all-state statutory treatment timing.",
            "OECD MWUSD can contextualize bite ratios but cannot replace the state-year cohort design.",
        ],
        "runner_limitation": (
            "The high-bite design requires state/unit cohort timing and local bite ratios. "
            "Do not run the generic country-year path until unit_id support or a validated "
            "state-year derived panel is present."
        ),
    },
    "federal_minimum_wage_employment_meta": {
        "required": [
            {
                "role": "outcome",
                "name": "state_total_employment_qcew",
                "publisher": "bls",
                "series": "QCEW_state_total_employment_panel",
                "repair": (
                    "BLS QCEW state-quarter or state-year employment counts, keyed by "
                    "state and period, for the meta-style aggregation of state evidence."
                ),
            },
            {
                "role": "treatment",
                "name": "state_minimum_wage",
                "publisher": "usdol",
                "series": "state_minimum_wage_history",
                "repair": (
                    "USDOL all-state statutory minimum-wage history with binding "
                    "increase timing; federal-only FRED series is not sufficient for "
                    "state cohort identification."
                ),
            },
            {
                "role": "treatment",
                "name": "minimum_to_median_wage_ratio",
                "publisher": "derived",
                "series": "minimum_wage_bite_ratio_subnational_panel",
                "repair": (
                    "State/local minimum-to-median wage bite panel needed to evaluate "
                    "whether Sanders-style federal bite ratios extrapolate beyond the "
                    "historical state evidence."
                ),
            },
        ],
        "secondary": [
            "bls:QCEW_state_NAICS72_employment_panel for low-wage-sector employment robustness.",
            "bls:LAU_state_unemployment_rate_panel and state population/GDP controls keyed to the same state-period frame.",
            "CBO scenario assumptions should be recorded as metadata, not treated as outcome data.",
        ],
        "incompatible_local": [
            "fred:FEDMINNFRWG is federal level history, not state cohort treatment timing.",
            "fred:STTMINWGCA is a single-state exemplar, not an all-state statutory history.",
            "Current BLS CES/OEWS single-series pulls are not QCEW state employment panels.",
        ],
        "runner_limitation": (
            "The federal-floor meta test is an extrapolation from state-level evidence. "
            "It needs state/unit panel support and bite-ratio diagnostics before any "
            "employment-effect verdict can be credible."
        ),
    },
}


def _latest_exact_vintage(publisher: str, series: str) -> Path | None:
    pub_dir = VINTAGES / publisher
    if not pub_dir.exists():
        return None
    candidates = list(pub_dir.glob(f"{series}@*.parquet"))
    candidates.extend(pub_dir.glob(f"{series}.parquet"))
    nested = pub_dir / series
    if nested.exists():
        candidates.extend(nested.glob("*.parquet"))
    return max(candidates, key=lambda p: p.name) if candidates else None


def minimum_wage_data_gate(hid: str) -> tuple[dict, dict, str, str, dict, list[tuple[str, list[str]]]] | None:
    gate = MINIMUM_WAGE_DATA_GATES.get(hid)
    if gate is None:
        return None

    loaded = []
    missing = []
    missing_exact = []
    required_exact = []
    for item in gate["required"]:
        source = f"{item['publisher']}:{item['series']}"
        required_exact.append(source)
        path = _latest_exact_vintage(item["publisher"], item["series"])
        if path is None:
            missing.append({"role": item["role"], "name": item["name"], "source": source})
            missing_exact.append(source)
            continue
        try:
            n_rows = int(len(pd.read_parquet(path)))
        except Exception:
            n_rows = 0
        loaded.append(
            {
                "role": item["role"],
                "name": item["name"],
                "source": source,
                "publisher": item["publisher"],
                "n_rows": n_rows,
            }
        )

    if not missing:
        return None

    status = {"variables_loaded": loaded, "variables_missing": missing}
    reason = "minimum-wage data gate failed; missing state/subnational outcome/treatment panels"
    est = {"error": reason}
    extra_diag = {
        "method_valid": False,
        "data_gap": True,
        "minimum_wage_data_gate": True,
        "required_exact_vintages": required_exact,
        "missing_exact_vintages": missing_exact,
        "incompatible_local_vintages": gate["incompatible_local"],
        "secondary_or_verdict_completeness_sources_needed": gate["secondary"],
        "runner_limitation": gate["runner_limitation"],
        "data_repair_note": [
            f"{item['publisher']}:{item['series']} — {item['repair']}"
            for item in gate["required"]
        ],
    }
    extra_sections = [
        (
            "Data repair note",
            [
                "- The preregistered minimum-wage design is state/subnational; national or single-state exemplar series are not compatible evidence.",
                *[
                    f"- Required: `{item['publisher']}:{item['series']}` — {item['repair']}"
                    for item in gate["required"]
                ],
                *[f"- Also needed for full verdict completeness: {src}" for src in gate["secondary"]],
                *[f"- Not used as compatible evidence: {src}" for src in gate["incompatible_local"]],
                f"- Runner limitation: {gate['runner_limitation']}",
            ],
        )
    ]
    return status, est, "INCONCLUSIVE_DATA_PENDING", reason, extra_diag, extra_sections


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
    # Data gates are non-grading integrity guards. Run them before the generic
    # stub-rule refusal so known proxy-prone designs preserve a precise repair
    # bill of materials instead of falling through to national/single-state
    # exemplars in future bulk waves.
    gated = minimum_wage_data_gate(hid)
    if gated is not None:
        status, est, verdict, reason, extra_diag, extra_sections = gated
        extra_diag["pre_registration_stub_rule"] = is_stub_falsification_rule(spec)
        persisted = should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        )
        if persisted:
            write_outputs(
                hid,
                spec,
                status,
                est,
                verdict,
                reason,
                extra_diag=extra_diag,
                extra_sections=extra_sections,
            )
        suffix = " (minimum-wage state/subnational data gate)"
        if not persisted:
            suffix += " [artifact skipped]"
        return f"  ⚠ {hid}: {verdict}{suffix}"

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
    if o is None:
        v, r = "INCONCLUSIVE_DATA_PENDING", "no outcome variable loaded"
        if should_persist_preflight_inconclusive(r, persist_preflight_inconclusive):
            write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    if t is None:
        built = construct_treatment_from_text(spec, panel_filt)
        if built is not None:
            panel_filt, t = built
    if t is None:
        v, r = "INCONCLUSIVE_DATA_PENDING", "no treatment variable loaded"
        if should_persist_preflight_inconclusive(r, persist_preflight_inconclusive):
            write_outputs(hid, spec, status, {"error": r}, v, r)
        return f"  ⚠ {hid}: {v}"
    est = fit_did_cs(panel_filt, spec, o, t)
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
        print(f"Running {len(ids)} did_callaway_santanna specs…")
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
        print_bulk_run_summary("did_callaway_santanna", counts)
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
