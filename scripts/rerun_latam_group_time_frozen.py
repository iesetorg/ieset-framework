#!/usr/bin/env python3
"""Exact group-time replays for two frozen LATAM staggered-adoption specs.

The old generic runner estimated a TWFE approximation with adoption years
misread from constructed vintages. This runner uses the dates declared in the
unchanged v1 specs, not-yet/never-treated controls, and every registered rule
component. Country-cluster uncertainty is a delete-one-country jackknife.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_panel_fe  # noqa: E402
import frozen_source_lock  # noqa: E402

CASES = {
    "latam_extra_fiscal_rule_adoption_panel_1999_2024": {
        "outcome": "gross_general_govt_debt_share_gdp",
        "treatment": "fiscal_rule_indicator",
        "adoption": {"BRA": 1999, "CHL": 2001, "COL": 2011, "PER": 1999, "URY": 2006},
        "source": "constructed: country-year binary, 1 from adoption-year onward (Chile 2001, Brazil 1999, Colombia 2011, Peru 1999, Uruguay 2006)",
        "secondary": "fiscal_balance_share_gdp",
    },
    "latam_extra_inflation_targeting_diff_in_diff_1999_2024": {
        "outcome": "cpi_inflation_yoy",
        "treatment": "inflation_targeting_indicator",
        "adoption": {"BRA": 1999, "CHL": 1999, "COL": 1999, "MEX": 2001, "PER": 2002,
                     "GTM": 2005, "URY": 2007, "PRY": 2011, "DOM": 2012, "CRI": 2018},
        "source": "constructed: country-year binary by adoption date (BRA/CHL/COL 1999, MEX 2001, PER 2002, GTM 2005, URY 2007, PRY 2011, DOM 2012, CRI 2018)",
        "secondary": "inflation_volatility",
    },
}
GROWTH = "log_gdp_pc_constant"
TOT = "terms_of_trade"
WGI = "wgi_government_effectiveness"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior(run_dir: Path) -> None:
    target = run_dir / "historical" / "2026-04-30_twfe_fallback"
    target.mkdir(parents=True, exist_ok=True)
    names = ("diagnostics.json", "result_card.md", "replication.py")
    for name in names:
        source, dest = run_dir / name, target / name
        if source.exists() and not dest.exists():
            shutil.copy2(source, dest)
    manifest = target / "sha256.json"
    if not manifest.exists():
        manifest.write_text(json.dumps(
            {name: sha256_file(target / name) for name in names if (target / name).exists()},
            indent=2, sort_keys=True,
        ) + "\n")


def prepare(hid: str) -> tuple[pd.DataFrame, dict, dict, dict]:
    case = CASES[hid]
    found = run_panel_fe.load_spec(hid)
    if not found:
        raise RuntimeError(f"missing frozen spec {hid}")
    spec_path, spec = found
    if spec.get("version") != 1 or (spec.get("estimator") or {}).get("template") != "did_callaway_santanna":
        raise RuntimeError("frozen v1 staggered-DiD contract changed")
    declared_source = spec["variables"]["treatment"][0]["source"]
    if declared_source != case["source"] or spec["variables"]["treatment"][0]["name"] != case["treatment"]:
        raise RuntimeError("declared treatment or adoption dates changed")
    if case["outcome"] != spec["variables"]["outcome"][0]["name"]:
        raise RuntimeError("registered primary outcome changed")
    panel, status = frozen_source_lock.checked_build_panel(hid, spec)
    panel = run_panel_fe.filter_sample(panel, spec).copy()
    if hid.startswith("latam_extra_inflation"):
        # The frozen sample explicitly excludes dollarised comparators and
        # Venezuela after 1999. Apply before any panel operation.
        panel = panel[~panel.country_iso3.isin(["ECU", "SLV", "PAN"])].copy()
        panel = panel[~(panel.country_iso3.eq("VEN") & panel.year.gt(1999))].copy()
    panel = panel.sort_values(["country_iso3", "year"])
    if panel.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate country-year after vintage join")
    panel[case["treatment"]] = [
        int(year >= case["adoption"].get(country, 9999))
        for country, year in zip(panel.country_iso3, panel.year)
    ]
    for row in status["variables_loaded"]:
        if row.get("name") == case["treatment"]:
            row["source"] = case["source"]
            row["runner_applied_exact_adoption_dates"] = True
    panel_digest = hashlib.sha256(panel.to_csv(
        index=False, float_format="%.17g", na_rep="NA",
    ).encode()).hexdigest()
    provenance = {
        "spec_path": str(spec_path.relative_to(ROOT)),
        "spec_sha256": sha256_file(spec_path),
        "input_panel_sha256": panel_digest,
        "prior_run": "historical/2026-04-30_twfe_fallback",
        **frozen_source_lock.provenance(hid),
    }
    return panel, spec, status, provenance


def group_time_cells(panel: pd.DataFrame, case: dict, excluded: str | None = None) -> list[dict]:
    adoption = case["adoption"]
    y = panel.pivot(index="country_iso3", columns="year", values=case["outcome"])
    tot = panel.pivot(index="country_iso3", columns="year", values=TOT)
    # WGI is biennial in early vintages. For a pretreatment covariate only,
    # carry the last observed score forward through g-1; never use a future
    # or post-adoption value to fill a baseline.
    wgi = panel.pivot(index="country_iso3", columns="year", values=WGI).ffill(axis=1)
    cells: list[dict] = []
    for g in sorted(set(adoption.values())):
        treated_names = [country for country, year in adoption.items() if year == g and country != excluded]
        if not treated_names or g - 1 not in y.columns:
            continue
        for t in range(g, int(panel.year.max()) + 1):
            if t not in y.columns:
                continue
            comparison_names = [
                country for country in y.index
                if country != excluded and adoption.get(country, 9999) > t
            ]
            if len(comparison_names) < 4:
                continue
            dy, dtot = y[t] - y[g - 1], tot[t] - tot[g - 1]
            working = pd.DataFrame({"dy": dy, "dtot": dtot, "wgi_pre": wgi[g - 1]}).dropna()
            treated = working.loc[working.index.intersection(treated_names)]
            comparison = working.loc[working.index.intersection(comparison_names)]
            if treated.empty or len(comparison) < 4:
                continue
            x_control = np.column_stack([
                np.ones(len(comparison)), comparison.dtot.to_numpy(),
                comparison.wgi_pre.to_numpy(),
            ])
            if np.linalg.matrix_rank(x_control) < 3:
                continue
            beta = np.linalg.lstsq(x_control, comparison.dy.to_numpy(), rcond=None)[0]
            x_treated = np.column_stack([
                np.ones(len(treated)), treated.dtot.to_numpy(), treated.wgi_pre.to_numpy(),
            ])
            residual = treated.dy.to_numpy() - x_treated @ beta
            cells.append({
                "cohort_year": g, "year": t, "att": float(np.mean(residual)),
                "n_treated": len(treated), "n_comparison": len(comparison),
                "treated_countries": sorted(treated.index.tolist()),
                "comparison_countries": sorted(comparison.index.tolist()),
            })
    return cells


def primary_estimate(panel: pd.DataFrame, case: dict) -> tuple[dict, list[dict]]:
    cells = group_time_cells(panel, case)
    expected = set(case["adoption"])
    covered = {c for cell in cells for c in cell["treated_countries"]}
    if not cells:
        return {"error": "no valid group-time comparison cells"}, cells
    weights = np.array([cell["n_treated"] for cell in cells], dtype=float)
    coefficient = float(np.average([cell["att"] for cell in cells], weights=weights))
    contributors = sorted({
        country for cell in cells
        for country in cell["treated_countries"] + cell["comparison_countries"]
    })
    used_country_years = {
        (country, year)
        for cell in cells
        for country in cell["treated_countries"] + cell["comparison_countries"]
        for year in (cell["cohort_year"] - 1, cell["year"])
    }
    leave_one = []
    for country in contributors:
        reduced = group_time_cells(panel, case, excluded=country)
        if not reduced:
            continue
        w = [cell["n_treated"] for cell in reduced]
        leave_one.append(float(np.average([cell["att"] for cell in reduced], weights=w)))
    if len(leave_one) < 6:
        standard_error, p_value, ci = None, None, [None, None]
    else:
        values = np.array(leave_one)
        n = len(values)
        standard_error = float(np.sqrt((n - 1) / n * np.square(values - values.mean()).sum()))
        degrees = n - 1
        p_value = float(2 * stats.t.sf(abs(coefficient / standard_error), df=degrees)) if standard_error > 0 else None
        critical = float(stats.t.ppf(0.975, df=degrees))
        ci = [coefficient - critical * standard_error, coefficient + critical * standard_error]
    return {
        "coefficient": coefficient, "std_error": standard_error,
        "p_value": p_value, "confidence_interval_95": ci,
        "n_group_time_cells": len(cells),
        "n_obs": len(used_country_years),
        "n_treated_country_periods": int(sum(weights)),
        "n_countries": len(contributors),
        "n_treated_countries_covered": len(covered),
        "treated_countries_missing": sorted(expected - covered),
        "cohort_years_covered": sorted({cell["cohort_year"] for cell in cells}),
        "method": "Callaway-Sant'Anna-style outcome-regression group-time ATT(g,t), conditional on terms-of-trade change and latest observed pretreatment WGI; not-yet/never-treated controls",
        "uncertainty": "delete-one-contributing-country jackknife, t reference; few-cohort limitation",
        "wgi_baseline_rule": "latest observed WGI at or before g-1; no post-adoption backfill",
    }, cells


def cumulative_growth(series: pd.Series, adoption: int) -> float | None:
    values = series.sort_index()
    years = [year for year in range(adoption + 1, 2025) if year not in (2020, 2021)]
    increments = [values.get(year, np.nan) - values.get(year - 1, np.nan) for year in years]
    if any(not np.isfinite(value) for value in increments):
        return None
    return float(sum(increments))


def growth_endpoint(panel: pd.DataFrame, case: dict, *, threshold: float) -> dict:
    x = panel.pivot(index="country_iso3", columns="year", values=GROWTH)
    never = sorted(set(x.index) - set(case["adoption"]))
    rows = []
    for country, year in case["adoption"].items():
        if country not in x.index:
            rows.append({"country": country, "status": "country missing"})
            continue
        treated = cumulative_growth(x.loc[country], year)
        control = [cumulative_growth(x.loc[c], year) for c in never]
        control = [value for value in control if value is not None]
        if treated is None or len(control) < 3:
            rows.append({"country": country, "status": "insufficient matched growth data"})
            continue
        rows.append({"country": country, "adoption_year": year,
                     "treated_log_growth": treated,
                     "never_treated_median_log_growth": float(np.median(control)),
                     "matched_gap": float(treated - np.median(control)),
                     "n_never_treated": len(control)})
    gaps = [row["matched_gap"] for row in rows if "matched_gap" in row]
    complete = len(gaps) == len(case["adoption"])
    value = float(np.median(gaps)) if gaps else None
    return {"country_rows": rows, "median_matched_gap": value,
            "threshold": threshold, "complete": complete,
            "passes": (value >= threshold) if complete and value is not None else None,
            "excluded_growth_years": [2020, 2021]}


def fiscal_dispersion(panel: pd.DataFrame, case: dict) -> dict:
    rows = []
    for country, year in case["adoption"].items():
        sub = panel[panel.country_iso3.eq(country)]
        before = sub[sub.year.lt(year)][case["secondary"]].dropna()
        after = sub[sub.year.ge(year)][case["secondary"]].dropna()
        row = {"country": country, "adoption_year": year,
               "pre_years": len(before), "post_years": len(after)}
        if len(before) >= 3 and len(after) >= 3:
            row.update(pre_sd=float(before.std(ddof=1)), post_sd=float(after.std(ddof=1)),
                       post_minus_pre=float(after.std(ddof=1) - before.std(ddof=1)))
        else:
            row["status"] = "insufficient observed pre/post fiscal-balance years"
        rows.append(row)
    deltas = [row["post_minus_pre"] for row in rows if "post_minus_pre" in row]
    complete = len(deltas) == len(case["adoption"])
    median = float(np.median(deltas)) if deltas else None
    return {"country_rows": rows, "median_post_minus_pre_sd": median,
            "complete": complete,
            "passes": (median < 0) if complete and median is not None else None}


def inflation_volatility(panel: pd.DataFrame, case: dict) -> dict:
    rows = []
    for country, year in case["adoption"].items():
        sub = panel[panel.country_iso3.eq(country)].sort_values("year").copy()
        sub["sd5"] = sub[case["outcome"]].rolling(5, min_periods=5).std(ddof=1)
        before = sub[sub.year.lt(year)].sd5.dropna()
        after = sub[sub.year.ge(year + 4)].sd5.dropna()
        row = {"country": country, "adoption_year": year,
               "pre_5yr_windows": len(before), "post_5yr_windows": len(after)}
        if len(before) >= 1 and len(after) >= 1:
            row.update(pre_mean_sd=float(before.mean()), post_mean_sd=float(after.mean()),
                       post_minus_pre=float(after.mean() - before.mean()))
        else:
            row["status"] = "no complete five-year window on one side of adoption"
        rows.append(row)
    deltas = [row["post_minus_pre"] for row in rows if "post_minus_pre" in row]
    complete = len(deltas) == len(case["adoption"])
    median = float(np.median(deltas)) if deltas else None
    return {"country_rows": rows, "median_post_minus_pre_sd": median,
            "complete": complete,
            "passes": (median < 0) if complete and median is not None else None}


def decision(hid: str, primary: dict, dispersion: dict, growth: dict) -> tuple[str, str, dict]:
    if "error" in primary or primary.get("p_value") is None:
        return "INCONCLUSIVE_DATA_PENDING", "registered primary ATT or uncertainty not estimable", {}
    # All pre-registered treated cohorts need an observed g-1 baseline before
    # the full-sample primary claim can be graded.
    if primary["treated_countries_missing"]:
        missing = ", ".join(primary["treated_countries_missing"])
        return "INCONCLUSIVE_DATA_PENDING", f"registered treated cohorts lack a pre-adoption primary outcome: {missing}", {
            "a_negative_att_p_below_0_10": None,
            "b_dispersion_declines": dispersion["passes"],
            "c_no_growth_penalty": growth["passes"],
        }
    a = primary["coefficient"] < 0 and primary["p_value"] < 0.10
    components = {
        "a_negative_att_p_below_0_10": a,
        "b_dispersion_declines": dispersion["passes"],
        "c_no_growth_penalty": growth["passes"],
    }
    if not a:
        return "REFUTED", "preregistered support conjunction failed because primary negative-ATT significance condition (a) failed; no opposite effect is established", components
    if any(value is False for value in components.values()):
        return "REFUTED", "preregistered support conjunction failed because a secondary condition failed; no opposite effect is established", components
    if any(value is None for value in components.values()):
        return "INCONCLUSIVE_DATA_PENDING", "a frozen secondary condition is unassessable", components
    return "SUPPORTED", "all three frozen conditions passed", components


def build(hid: str) -> tuple[dict, str]:
    case = CASES[hid]
    panel, spec, status, provenance = prepare(hid)
    primary, cells = primary_estimate(panel, case)
    dispersion = fiscal_dispersion(panel, case) if "fiscal_rule" in hid else inflation_volatility(panel, case)
    growth = growth_endpoint(panel, case, threshold=0.0 if "fiscal_rule" in hid else -0.05)
    verdict, reason, components = decision(hid, primary, dispersion, growth)
    if verdict == "REFUTED" and components.get("a_negative_att_p_below_0_10") is False:
        decision_scope = (
            "Frozen condition (a) alone is dispositive for this conjunctive claim. "
            "A null secondary condition remains unmeasured and is not treated as a pass or failure. "
            "This logical failure of the support rule does not show an opposite treatment effect."
        )
    elif verdict == "INCONCLUSIVE_DATA_PENDING":
        decision_scope = "The full registered treatment cohort cannot be graded from the local primary outcome."
    else:
        decision_scope = "All stated rule components were evaluated."
    diagnostics = {
        "hypothesis_id": hid, "template": "did_callaway_santanna",
        "verdict": f"{verdict} — {reason}", "verdict_label": verdict,
        "verdict_reason": reason,
        "runner": "scripts/rerun_latam_group_time_frozen.py",
        "falsification_rule_text": spec["falsification"]["rule"],
        "adoption_years_from_frozen_spec": case["adoption"],
        "estimate": primary,
        "group_time_cells": cells,
        "dispersion_endpoint": dispersion,
        "growth_endpoint": growth,
        "frozen_rule_components": components,
        "decision_scope": decision_scope,
        "evidence_tier_recommendation": "calibration" if verdict == "REFUTED" else "archive",
        "evidence_tier_reason": (
            "The primary condition fails the conjunction, but the early 1999 cohorts "
            "lack a pure five-year pre-adoption volatility window; few treated "
            "cohorts and jackknife uncertainty limit causal generalization."
            if verdict == "REFUTED" else
            "Missing registered pretreatment outcome prevents full-sample grading."
        ),
        "data_status": status,
        "provenance": provenance,
    }
    if "fiscal_rule" in hid:
        if "Mexico Pemex-and-budget 2006" not in spec["claim"] or "MEX" in case["adoption"]:
            raise RuntimeError("frozen fiscal claim/treatment discrepancy changed")
        diagnostics["frozen_spec_inconsistency"] = {
            "claim_names_mexico_adoption_year": 2006,
            "treatment_source_names_mexico": False,
            "mexico_used_as_never_treated_comparison": any(
                "MEX" in cell["comparison_countries"] for cell in cells
            ),
            "disposition": (
                "The frozen claim names Mexico as a 2006 adopter, but its treatment "
                "source and tags omit Mexico. This replay follows the registered "
                "treatment variable, so Mexico remains a comparison country. "
                "Resolve the conflict prospectively; keep this run archived."
            ),
        }
    card = "\n".join([
        f"# Result card — {hid}", "",
        f"**Verdict:** {diagnostics['verdict']}", "",
        "## Frozen rule", "",
        f"- (a) ATT < 0 at p < 0.10: **{components.get('a_negative_att_p_below_0_10')}**; ATT={primary.get('coefficient')}, p={primary.get('p_value')}",
        f"- (b) within-country {'fiscal-balance dispersion' if 'fiscal_rule' in hid else 'five-year inflation volatility'} declines: **{components.get('b_dispersion_declines')}**; median post-minus-pre={dispersion.get('median_post_minus_pre_sd')}",
        f"- (c) no cumulative-growth penalty: **{components.get('c_no_growth_penalty')}**; matched median log-growth gap={growth.get('median_matched_gap')} (threshold {growth['threshold']})", "",
        f"**Decision scope:** {decision_scope}",
        f"Design-grade recommendation: **{diagnostics['evidence_tier_recommendation']}** — {diagnostics['evidence_tier_reason']} Failure of necessary condition (a) is not evidence that the unmeasured secondary condition passed or failed, nor that treatment had an opposite effect.", "",
        "## Method and coverage", "",
        "Group-time ATT(g,t) compares each adoption cohort with countries not yet or never treated, from g-1 to t. Control-country outcome regression adjusts for terms-of-trade change and the latest observed WGI at or before g-1 (early WGI is biennial; no post-adoption backfill). The pooled ATT weights treated country-periods; uncertainty uses a delete-one-country jackknife. Common oil-price and US-rate movements are absorbed in each group-time comparison.",
        f"Group-time cells: {primary.get('n_group_time_cells')}; contributing countries: {primary.get('n_countries')}; registered treated countries without primary baseline: {', '.join(primary.get('treated_countries_missing', [])) or 'none'}.",
        "The previous TWFE fallback and its incorrectly inferred cohort years are preserved under `historical/`. COVID 2020–2021 is excluded only from the registered cumulative-growth endpoint.", "",
        f"Spec SHA-256: `{provenance['spec_sha256']}`", f"Input-panel SHA-256: `{provenance['input_panel_sha256']}`", "",
    ])
    if "fiscal_rule" in hid:
        card += (
            "\n**Frozen-spec inconsistency:** The claim names Mexico as a 2006 "
            "adopter, but the registered treatment source omits it; this replay "
            "treats Mexico as a comparison country. The run remains archived "
            "pending prospective resolution.\n"
        )
    return diagnostics, card


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", choices=sorted(CASES))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    diagnostics, card = build(args.hypothesis_id)
    manifest = frozen_source_lock.manifest_text(diagnostics)
    run_dir = ROOT / "engine" / "runs" / args.hypothesis_id
    if args.check:
        existing = json.loads((run_dir / "diagnostics.json").read_text())
        if (not frozen_source_lock.same_packet(diagnostics, existing)
                or not frozen_source_lock.same_result_card(card, (run_dir / "result_card.md").read_text())
                or (run_dir / "manifest.yaml").read_text() != manifest):
            print("FAIL: exact replay artifacts stale", file=sys.stderr)
            return 1
    else:
        snapshot_prior(run_dir)
        (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True, allow_nan=False) + "\n")
        (run_dir / "result_card.md").write_text(card)
        (run_dir / "manifest.yaml").write_text(manifest)
    print(f"{args.hypothesis_id}: {diagnostics['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
