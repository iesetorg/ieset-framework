#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = event_study.

Two shapes are handled:

  single_country_its
      sample.countries has 1 entry (or the spec resolves to a treatment
      country plus controls). The runner fits a linear pre-period trend
      to the outcome, projects it forward, and computes the post-period
      actual-vs-counterfactual gap.

  multi_country_twfe
      sample.countries has many entries with a binary post-treatment
      treatment variable (or a country-specific event year inferable from
      the spec text). Fits a two-way-FE OLS with the post-treatment
      dummy and reports the pooled effect.

The event year is discovered, in order, from:
  1. estimator.event_year (explicit in the spec)
  2. variables.treatment[0].event_year (alternative location)
  3. The first 4-digit year inside sample.period found in the claim text
     or falsification.test text.

Verdicts:
  SUPPORTED                  — direction matches claim AND effect clears
                               threshold (or, absent threshold, |Δ| > 5%
                               in log-units / 0.5 in raw units).
  REFUTED                    — direction opposite the claim AND effect is
                               > threshold magnitude.
  PARTIAL                    — direction matches but magnitude below
                               threshold, OR direction can't be inferred.
  INCONCLUSIVE_DATA_PENDING  — outcome data not on disk for the relevant
                               country / period.

Usage:
    python3 scripts/run_event_study.py <hypothesis_id>
    python3 scripts/run_event_study.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
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
from run_descriptive import extract_threshold


# ---------------------------------------------------------------------------
# Event year discovery
# ---------------------------------------------------------------------------


def find_event_year(spec: dict) -> int | None:
    """Pull an event year out of the spec — explicit fields first, then text."""
    est = spec.get("estimator") or {}
    if isinstance(est, dict) and est.get("event_year"):
        try:
            return int(est["event_year"])
        except (TypeError, ValueError):
            pass

    var_blocks = spec.get("variables") or {}
    for item in (var_blocks.get("treatment") or []):
        if item.get("event_year"):
            try:
                return int(item["event_year"])
            except (TypeError, ValueError):
                pass

    # Fallback: first 4-digit year inside sample.period that appears in the
    # claim or falsification.test text.
    text = ((spec.get("claim") or "") + " " +
            (spec.get("falsification") or {}).get("test", "") + " " +
            (spec.get("notes") or ""))
    period = (spec.get("sample") or {}).get("period") or [None, None]
    if period and len(period) == 2 and all(p is not None for p in period):
        for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", text):
            y = int(m.group(0))
            if period[0] < y < period[1]:
                return y
    return None


# ---------------------------------------------------------------------------
# Single-country interrupted time series
# ---------------------------------------------------------------------------


def fit_its(panel: pd.DataFrame, outcome: str, country: str,
            event_year: int, period: list[int]) -> dict:
    sub = panel[panel["country_iso3"] == country].dropna(subset=[outcome])
    if period and period[0] is not None:
        sub = sub[sub["year"] >= int(period[0])]
    if period and period[1] is not None:
        sub = sub[sub["year"] <= int(period[1])]
    sub = sub.sort_values("year")

    pre = sub[sub["year"] < event_year]
    post = sub[sub["year"] >= event_year]
    if len(pre) < 4 or len(post) < 3:
        return {"error": f"insufficient pre/post obs (pre={len(pre)}, post={len(post)})"}

    # Fit linear trend on pre-period, project forward.
    pre_x = pre["year"].astype(float).values
    pre_y = pre[outcome].astype(float).values
    a, b = np.polyfit(pre_x, pre_y, 1)  # y = a*year + b

    post_x = post["year"].astype(float).values
    post_y = post[outcome].astype(float).values
    counterfactual = a * post_x + b
    gap = post_y - counterfactual

    pre_resid = pre_y - (a * pre_x + b)
    pre_sd = float(np.std(pre_resid, ddof=1)) if len(pre) > 1 else 0.0
    end_year = int(post_x[-1])
    end_gap = float(gap[-1])
    mean_gap = float(np.mean(gap))
    z_end = end_gap / pre_sd if pre_sd > 0 else None
    z_mean = mean_gap / pre_sd if pre_sd > 0 else None

    return {
        "shape": "single_country_its",
        "country": country,
        "event_year": int(event_year),
        "n_pre": int(len(pre)),
        "n_post": int(len(post)),
        "pre_trend_slope": float(a),
        "pre_trend_intercept": float(b),
        "pre_residual_sd": pre_sd,
        "end_year": end_year,
        "end_year_actual": float(post_y[-1]),
        "end_year_counterfactual": float(counterfactual[-1]),
        "end_year_gap": end_gap,
        "mean_post_gap": mean_gap,
        "z_end": z_end,
        "z_mean": z_mean,
        "post_period_years": [int(post_x[0]), end_year],
    }


# ---------------------------------------------------------------------------
# Multi-country TWFE event study (pooled post coefficient)
# ---------------------------------------------------------------------------


def construct_treatment_from_text(spec: dict,
                                  panel: pd.DataFrame) -> tuple[pd.DataFrame, str] | None:
    """Build a post-event binary treatment column from a `constructed:` source.

    Handles strings like:
        'constructed: event date = 1997-05-06 (Brown grants BoE independence)'
        'constructed: binary = 1 for GBR from 1997-05'
        'constructed: post-1971 fiat regime'

    Returns the panel (with a new column) and the column name, or None if
    no constructable pattern was found.
    """
    var_blocks = spec.get("variables") or {}
    treatment_items = var_blocks.get("treatment") or []
    if not treatment_items:
        return None
    first = treatment_items[0]
    source = (first.get("source") or "")
    name = first.get("name") or "constructed_treatment"
    if not source.lower().lstrip().startswith("constructed:"):
        return None

    # Parse the year. Try date pattern first (1997-05-06), then bare year.
    text = source.lower()
    year = None
    m = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if m:
        year = int(m.group(1))
    if year is None:
        return None

    # Parse the target ISO3 country.
    # 1. 'binary = 1 for GBR from 1997-05' on this treatment item
    # 2. fall through any OTHER treatment item's source for the same pattern
    # 3. fall through the sample's first country (event-study convention:
    #    treated unit listed first)
    iso3 = None
    sources_to_scan = [source] + [
        (t.get("source") or "") for t in treatment_items[1:]
    ]
    for src in sources_to_scan:
        cm = re.search(r"\bfor\s+([A-Z]{3})\b", src)
        if cm:
            iso3 = cm.group(1)
            break
    if iso3 is None:
        sample = (spec.get("sample") or {})
        countries = sample.get("countries") or []
        if countries:
            iso3 = countries[0]

    df = panel.copy()
    if iso3 is not None:
        df[name] = ((df["country_iso3"] == iso3) & (df["year"] >= year)).astype(int)
    else:
        df[name] = (df["year"] >= year).astype(int)
    return df, name


def fit_twfe_event(panel: pd.DataFrame, spec: dict, outcome: str,
                   treatment: str | None) -> dict:
    """Pooled post-treatment OLS with country + year FE."""
    var_blocks = spec.get("variables") or {}
    control_names = [c["name"] for c in (var_blocks.get("controls") or [])
                     if c.get("name") and c["name"] in panel.columns]

    if treatment is None or treatment not in panel.columns:
        # Try to construct it from a `constructed:` source string.
        built = construct_treatment_from_text(spec, panel)
        if built is not None:
            panel, treatment = built
            control_names = [c["name"] for c in (var_blocks.get("controls") or [])
                             if c.get("name") and c["name"] in panel.columns]
        else:
            return {"error": "no treatment variable resolved"}
    needed = [outcome, treatment] + control_names
    sub = panel[["country_iso3", "year"] + needed].dropna()
    if len(sub) < 30:
        return {"error": f"insufficient obs ({len(sub)})"}

    try:
        from linearmodels.panel import PanelOLS
        sub = sub.set_index(["country_iso3", "year"])
        rhs = [treatment] + control_names
        mod = PanelOLS(sub[outcome], sub[rhs], entity_effects=True,
                       time_effects=True, drop_absorbed=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        return {
            "shape": "multi_country_twfe",
            "coefficient": float(res.params[treatment]),
            "std_error": float(res.std_errors[treatment]),
            "p_value": float(res.pvalues[treatment]),
            "n_obs": int(res.nobs),
            "n_countries": int(sub.index.get_level_values(0).nunique()),
            "r_squared_within": float(res.rsquared_within or 0),
            "method": "linearmodels.PanelOLS (TWFE, country-clustered)",
        }
    except Exception as exc:
        return {"error": f"twfe failed: {exc}"}


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def event_study_verdict(comp: dict, claim_dir: str, threshold: dict,
                        outcome_is_log: bool) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    shape = comp["shape"]

    if shape == "single_country_its":
        gap = comp.get("mean_post_gap")
        z = comp.get("z_mean")
        sign = "+" if gap >= 0 else "-"
        # "Big" effect: |z| > 1.5 (about 87% prediction interval) or |gap| > 0.05 in log.
        big_z = (z is not None and abs(z) > 1.5)
        big_gap = (outcome_is_log and abs(gap) > 0.05)
        big = big_z or big_gap
        mag = (f"mean_gap={gap:+.4g}, z={z:+.2g}" if z is not None
               else f"mean_gap={gap:+.4g}")
        threshold_met = None
        if "percent" in threshold:
            t = threshold["percent"] / 100.0
            threshold_met = (outcome_is_log and abs(gap) > t)
        elif "fold" in threshold:
            t = float(threshold["fold"])
            threshold_met = abs(gap) > np.log(t) if outcome_is_log else abs(gap) > t
        if claim_dir == "?":
            return "PARTIAL", f"shape=ITS, {mag}; claim direction ambiguous"
        if sign == claim_dir:
            if threshold_met is True or (threshold_met is None and big):
                return "SUPPORTED", f"shape=ITS, sign matches claim {claim_dir}, {mag}"
            return "PARTIAL", f"shape=ITS, sign matches claim {claim_dir} but magnitude small ({mag})"
        if threshold_met is True or big:
            return "REFUTED", f"shape=ITS, sign {sign} OPPOSITE claim {claim_dir}, {mag}"
        return "PARTIAL", f"shape=ITS, opposite sign but small ({mag})"

    if shape == "multi_country_twfe":
        coef = comp["coefficient"]
        p = comp["p_value"]
        sign = "+" if coef >= 0 else "-"
        mag = f"coef={coef:+.4g}, p={p:.3g}"
        if claim_dir == "?":
            return ("PARTIAL", f"shape=TWFE, {mag}; claim direction ambiguous")
        if p < 0.10:
            if sign == claim_dir:
                return "SUPPORTED", f"shape=TWFE, sign matches claim {claim_dir}, {mag}"
            return "REFUTED", f"shape=TWFE, sign {sign} OPPOSITE claim {claim_dir}, {mag}"
        return "PARTIAL", f"shape=TWFE, {mag} (above α=0.10)"

    return "INCONCLUSIVE_DATA_PENDING", f"unknown shape {shape}"


# ---------------------------------------------------------------------------
# Output (mirrors run_panel_fe / run_descriptive)
# ---------------------------------------------------------------------------


def write_outputs(hid: str, spec: dict, status: dict, comp: dict,
                  threshold: dict, verdict: str, reason: str,
                  event_year: int | None) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    diag = {
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "event_study",
        "claim_direction_inferred": infer_claim_direction(spec),
        "event_year": event_year,
        "threshold_extracted": threshold,
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "comparison": comp,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_event_study.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))

    md = [
        f"# Result card — {hid}",
        "",
        f"**Verdict:** {verdict} — {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test','').strip()}",
        f"- **Event year:** {event_year if event_year else '(not extracted)'}",
        "",
        "## Estimate",
    ]
    if "error" in comp:
        md.append(f"- _Error:_ {comp['error']}")
    else:
        for k, v in comp.items():
            md.append(f"- **{k}:** {v}")
    md.append("")
    md.append("## Variables resolved")
    if status["variables_loaded"]:
        for v in status["variables_loaded"]:
            md.append(f"- `{v['source']}` → {v['name']} ({v['role']}, "
                      f"publisher={v['publisher']}, n={v['n_rows']})")
    if status["variables_missing"]:
        md.append("\n### Variables missing data")
        for v in status["variables_missing"]:
            md.append(f"- `{v['source']}` ({v['role']}, name={v['name']})")
    md.append("")
    md.append(f"_Generated by `scripts/run_event_study.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def list_event_study_specs() -> list[str]:
    derived = ROOT / "engine" / "runnability.derived.yaml"
    with derived.open() as f:
        d = yaml.safe_load(f)
    return [h["hypothesis_id"] for h in d["hypotheses"]
            if h["estimator_template"] == "event_study"]


def run_one(hid: str, force: bool = False) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if found is None:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    panel, status = build_panel(spec)
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    if not outcome_items:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = "no outcome variable in spec"
        write_outputs(hid, spec, status, {"error": reason}, {}, verdict, reason, None)
        return f"  ⚠ {hid}: {verdict}"
    outcome_name = outcome_items[0]["name"]
    outcome_kind = (outcome_items[0].get("transformation") or "level").lower()
    outcome_is_log = "log" in outcome_kind

    if outcome_name not in panel.columns:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        missing = [v["source"] for v in status["variables_missing"]
                   if v["role"] == "outcome"]
        reason = f"outcome '{outcome_name}' not loaded; missing: {missing}"
        write_outputs(hid, spec, status, {"error": reason}, {}, verdict, reason, None)
        return f"  ⚠ {hid}: {verdict}"

    event_year = find_event_year(spec)
    threshold = extract_threshold(
        (spec.get("claim") or "") + " " +
        (spec.get("falsification") or {}).get("test", "")
    )

    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    period = sample.get("period") or [None, None]
    panel_filt = filter_sample(panel, spec)

    if len(countries) == 1:
        if event_year is None:
            comp = {"error": "couldn't infer event_year"}
        else:
            comp = fit_its(panel_filt, outcome_name, countries[0], event_year, period)
    else:
        treatment_items = var_blocks.get("treatment") or []
        treatment = treatment_items[0]["name"] if treatment_items else None
        comp = fit_twfe_event(panel_filt, spec, outcome_name, treatment)

    claim_dir = infer_claim_direction(spec)
    verdict, reason = event_study_verdict(comp, claim_dir, threshold, outcome_is_log)
    write_outputs(hid, spec, status, comp, threshold, verdict, reason, event_year)

    icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
            "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
    return f"  {icon} {hid}: {verdict} — {reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing committed verdicts.")
    args = parser.parse_args()
    if args.all:
        ids = list_event_study_specs()
        print(f"Running {len(ids)} event_study specs…")
        for hid in ids:
            try:
                print(run_one(hid, force=args.force))
            except Exception as exc:
                print(f"  ✗ {hid}: runner crashed — {exc}")
                traceback.print_exc()
        return 0
    if not args.hypothesis_id:
        parser.error("Pass <hypothesis_id> or --all.")
    print(run_one(args.hypothesis_id, force=args.force))
    return 0


if __name__ == "__main__":
    sys.exit(main())
