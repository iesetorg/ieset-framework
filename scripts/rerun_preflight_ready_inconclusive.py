#!/usr/bin/env python3
"""Audit and optionally rerun inconclusive runs that are preflight-ready now.

This script looks for existing ``engine/runs/*/diagnostics.json`` entries
whose verdict is inconclusive, re-evaluates whether the corresponding spec
would pass today's loader/spec-shape preflight, and optionally reruns only
that subset through the appropriate generic runner.

Usage:
  ./venv/bin/python scripts/rerun_preflight_ready_inconclusive.py
  ./venv/bin/python scripts/rerun_preflight_ready_inconclusive.py --apply
  ./venv/bin/python scripts/rerun_preflight_ready_inconclusive.py --apply --limit 25
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_descriptive
import run_cointegration_vecm
import run_did_callaway_santanna
import run_event_study
import run_local_projections
import run_panel_fe
import run_synth_did


RUNS_GLOB = str(ROOT / "engine" / "runs" / "*" / "diagnostics.json")
RUNNER_BY_TEMPLATE = {
    "panel_fe": run_panel_fe,
    "panel_fe_decomposition": run_panel_fe,
    "descriptive": run_descriptive,
    "event_study": run_event_study,
    "did_callaway_santanna": run_did_callaway_santanna,
    "did_chaisemartin": run_did_callaway_santanna,
    "local_projections": run_local_projections,
    "cointegration_vecm": run_cointegration_vecm,
    "synth_did": run_synth_did,
    "synthetic_control": run_synth_did,
}


def verdict_text(doc: dict) -> str:
    return str(doc.get("verdict_label") or doc.get("verdict") or "").strip()


def is_inconclusive(doc: dict) -> bool:
    return verdict_text(doc).upper().startswith("INCONCLUSIVE")


def control_names(spec: dict, panel) -> list[str]:
    var_blocks = spec.get("variables") or {}
    return [
        c["name"]
        for c in (var_blocks.get("controls") or [])
        if c.get("name") and c["name"] in panel.columns
    ]


def panel_min_obs(spec: dict) -> int:
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    single_country_time_series = (
        str(sample.get("temporal_structure") or "").lower() == "time_series"
        and len(countries) <= 1
    )
    return 12 if single_country_time_series else 30


def has_fe_treatment_variation(frame, spec: dict, treatment: str) -> bool:
    fe_spec = (spec.get("estimator") or {}).get("fixed_effects", []) or []
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    single_country_time_series = (
        str(sample.get("temporal_structure") or "").lower() == "time_series"
        and len(countries) <= 1
    )
    entity = "country" in [str(x).lower() for x in fe_spec]
    time = "year" in [str(x).lower() for x in fe_spec]
    if not entity and not time and not single_country_time_series:
        entity, time = True, True
    if entity:
        within_entity = frame.groupby("country_iso3")[treatment].nunique(dropna=True)
        if not within_entity.empty and bool((within_entity <= 1).all()):
            return False
    if time:
        within_time = frame.groupby("year")[treatment].nunique(dropna=True)
        if not within_time.empty and bool((within_time <= 1).all()):
            return False
    return True


def panel_fe_estimand_ready(panel, spec: dict, outcome: str, treatment: str) -> bool:
    min_obs = panel_min_obs(spec)
    sub, usable_controls, _dropped = run_panel_fe.prune_controls_for_overlap(
        panel,
        [outcome, treatment],
        control_names(spec, panel),
        min_obs=min_obs,
    )
    if len(sub) < min_obs:
        return False
    if has_fe_treatment_variation(sub, spec, treatment):
        return True
    no_controls = panel[["country_iso3", "year", outcome, treatment]].dropna()
    return len(no_controls) >= min_obs and has_fe_treatment_variation(
        no_controls,
        spec,
        treatment,
    )


def did_estimand_ready(panel, spec: dict, outcome: str, treatment: str) -> bool:
    sub, _usable_controls, _dropped = run_panel_fe.prune_controls_for_overlap(
        panel,
        [outcome, treatment],
        control_names(spec, panel),
        min_obs=30,
    )
    if len(sub) < 30:
        return False
    treated = (sub[treatment] >= 0.5)
    return bool(treated.any() and (~treated).any())


def local_projection_estimand_ready(panel, spec: dict, outcome: str, treatment: str) -> bool:
    sub, _usable_controls, _dropped = run_panel_fe.prune_controls_for_overlap(
        panel,
        [outcome, treatment],
        control_names(spec, panel),
        min_obs=50,
    )
    return len(sub) >= 50


def pre_post_ready(panel, outcome: str, country: str, cut_year: int, period: list[int]) -> bool:
    sub = panel[panel["country_iso3"] == country].dropna(subset=[outcome])
    if period and period[0] is not None:
        sub = sub[sub["year"] >= int(period[0])]
    if period and period[1] is not None:
        sub = sub[sub["year"] <= int(period[1])]
    pre = sub[sub["year"] < cut_year]
    post = sub[sub["year"] >= cut_year]
    return len(pre) >= 3 and len(post) >= 3


def event_study_ready(panel, spec: dict, outcome: str, treatment: str | None) -> bool:
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    period = sample.get("period") or [None, None]
    if len(countries) == 1:
        event_year = run_event_study.find_event_year(spec)
        if event_year is None:
            return False
        sub = panel[panel["country_iso3"] == countries[0]].dropna(subset=[outcome])
        if period and period[0] is not None:
            sub = sub[sub["year"] >= int(period[0])]
        if period and period[1] is not None:
            sub = sub[sub["year"] <= int(period[1])]
        pre = sub[sub["year"] < event_year]
        post = sub[sub["year"] >= event_year]
        return len(pre) >= 4 and len(post) >= 3
    if treatment is None or treatment not in panel.columns:
        built = run_panel_fe.construct_treatment_from_text(spec, panel)
        if built is not None:
            panel, treatment = built
        else:
            return False
    sub, _usable_controls, _dropped = run_panel_fe.prune_controls_for_overlap(
        panel,
        [outcome, treatment],
        control_names(spec, panel),
        min_obs=30,
    )
    return len(sub) >= 30


def synth_did_ready(panel, spec: dict, outcome: str) -> bool:
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    if len(countries) < 3:
        return False
    event_year = run_event_study.find_event_year(spec)
    if event_year is None:
        period = sample.get("period") or [None, None]
        if not (all(period) and len(period) == 2):
            return False
        event_year = (int(period[0]) + int(period[1])) // 2
    treated, donors = countries[0], countries[1:]
    sub = panel[panel["country_iso3"].isin([treated] + donors)].dropna(subset=[outcome])
    if sub.empty:
        return False
    wide = sub.pivot_table(index="year", columns="country_iso3", values=outcome, aggfunc="mean")
    if treated not in wide.columns:
        return False
    pre = wide[wide.index < event_year]
    post = wide[wide.index >= event_year]
    available_donors = [d for d in donors if d in pre.columns]
    if len(available_donors) < 2:
        return False
    pre_treated = pre[treated].dropna()
    pre_donors = pre[available_donors].dropna(how="all", axis=1).dropna(axis=1)
    common_years = pre_treated.index.intersection(pre_donors.index)
    if len(common_years) < 4 or pre_donors.shape[1] < 2:
        return False
    post_treated = post[treated].dropna()
    if post_treated.empty:
        return False
    donor_names = list(pre_donors.columns)
    post_donors = post[donor_names].dropna(how="any")
    if post_donors.empty:
        return False
    return len(post_treated.index.intersection(post_donors.index)) > 0


def classify_preflight_state(hid: str, template: str) -> str:
    found = run_panel_fe.load_spec(hid)
    if not found:
        return "spec_missing"
    _, spec = found
    if run_panel_fe.is_stub_falsification_rule(spec):
        return "stub_rule"

    panel, _status = run_panel_fe.build_panel(spec)
    panel_filt = run_panel_fe.filter_sample(panel, spec)
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    treatment_items = var_blocks.get("treatment") or []
    decomposition_items = var_blocks.get("decomposition_channels") or []

    if template == "panel_fe_decomposition":
        if not outcome_items or not decomposition_items:
            return "missing_spec_vars"
        o = run_panel_fe.first_loaded_var(outcome_items, panel_filt)
        t = run_panel_fe.first_loaded_var(decomposition_items, panel_filt)
        return (
            "preflight_ready"
            if (o is not None and t is not None and panel_fe_estimand_ready(panel_filt, spec, o, t))
            else "preflight_blocked"
        )

    if template in ("panel_fe", "did_callaway_santanna", "did_chaisemartin", "local_projections"):
        if not outcome_items:
            return "missing_spec_vars"
        o = run_panel_fe.first_loaded_var(outcome_items, panel_filt)
        t = run_panel_fe.first_loaded_var(treatment_items, panel_filt)
        if t is None and not treatment_items and template == "panel_fe":
            built = run_panel_fe.construct_treatment_from_estimator_notes(spec, panel_filt)
            if built is not None:
                _, t = built
        if not treatment_items and template != "panel_fe":
            return "missing_spec_vars"
        if o is None or t is None:
            return "preflight_blocked"
        if template == "panel_fe":
            ready = panel_fe_estimand_ready(panel_filt, spec, o, t)
        elif template in ("did_callaway_santanna", "did_chaisemartin"):
            ready = did_estimand_ready(panel_filt, spec, o, t)
        else:
            ready = local_projection_estimand_ready(panel_filt, spec, o, t)
        return "preflight_ready" if ready else "preflight_blocked"

    if template == "descriptive":
        if not outcome_items:
            return "missing_spec_vars"
        o = run_panel_fe.first_loaded_var(outcome_items, panel_filt)
        if o is None:
            return "preflight_blocked"
        sample = spec.get("sample") or {}
        countries = sample.get("countries") or []
        period = sample.get("period") or [None, None]
        if len(countries) == 1:
            cut = run_descriptive.find_cut_year(spec)
            if cut is None:
                cut = (period[0] + period[1]) // 2 if len(period) == 2 and all(period) else None
            if cut is None:
                return "preflight_blocked"
            if not pre_post_ready(panel_filt, o, countries[0], cut, period):
                return "preflight_blocked"
        elif not countries:
            return "preflight_blocked"
        return "preflight_ready"

    if template == "event_study":
        if not outcome_items:
            return "missing_spec_vars"
        o = run_panel_fe.first_loaded_var(outcome_items, panel_filt)
        if o is None:
            return "preflight_blocked"
        sample = spec.get("sample") or {}
        countries = sample.get("countries") or []
        if len(countries) == 1 and run_event_study.find_event_year(spec) is None:
            return "preflight_blocked"
        treatment_items = var_blocks.get("treatment") or []
        t = run_panel_fe.first_loaded_var(treatment_items, panel_filt)
        return "preflight_ready" if event_study_ready(panel_filt, spec, o, t) else "preflight_blocked"

    if template in ("synth_did", "synthetic_control"):
        if not outcome_items:
            return "missing_spec_vars"
        o = run_panel_fe.first_loaded_var(outcome_items, panel_filt)
        if o is None:
            return "preflight_blocked"
        sample = spec.get("sample") or {}
        countries = sample.get("countries") or []
        if len(countries) < 3:
            return "preflight_blocked"
        if run_event_study.find_event_year(spec) is None:
            period = sample.get("period") or [None, None]
            if not (all(period) and len(period) == 2):
                return "preflight_blocked"
        return "preflight_ready" if synth_did_ready(panel_filt, spec, o) else "preflight_blocked"

    if template == "cointegration_vecm":
        loaded = [
            item.get("name")
            for item in outcome_items
            if item.get("name")
            and item.get("name") in panel_filt.columns
            and panel_filt[item.get("name")].notna().any()
        ]
        return "preflight_ready" if len(loaded) >= 2 else "preflight_blocked"

    return "unknown_template"


def collect_candidates() -> tuple[list[dict], Counter]:
    counts = Counter()
    candidates: list[dict] = []
    for path in glob.glob(RUNS_GLOB):
        doc = json.loads(Path(path).read_text())
        if not is_inconclusive(doc):
            continue
        hid = Path(path).parent.name
        template = str(doc.get("template") or "unknown")
        state = classify_preflight_state(hid, template)
        counts[state] += 1
        if state == "preflight_ready":
            candidates.append({"hypothesis_id": hid, "template": template})
    return sorted(candidates, key=lambda row: (row["template"], row["hypothesis_id"])), counts


def print_audit(candidates: list[dict], counts: Counter) -> None:
    print("Current inconclusive preflight state:")
    for key, value in counts.most_common():
        print(f"  {key:20s} {value:4d}")
    print("")
    print(f"Preflight-ready rerun candidates: {len(candidates)}")
    for row in candidates[:50]:
        print(f"  {row['template']:24s} {row['hypothesis_id']}")
    if len(candidates) > 50:
        print(f"  ... {len(candidates) - 50} more")


def apply_reruns(
    candidates: list[dict],
    *,
    limit: int | None,
    force: bool,
    write_preflight_inconclusive: bool,
) -> None:
    counts: dict[str, int] = {}
    subset = candidates[:limit] if limit is not None else candidates
    print("")
    print(f"Rerunning {len(subset)} preflight-ready inconclusive run(s)...")
    for row in subset:
        hid = row["hypothesis_id"]
        template = row["template"]
        runner = RUNNER_BY_TEMPLATE.get(template)
        if runner is None:
            msg = f"  ✗ {hid}: no runner for template={template}"
            print(msg)
            counts["crashed"] = counts.get("crashed", 0) + 1
            continue
        try:
            msg = runner.run_one(
                hid,
                force=force,
                persist_preflight_inconclusive=write_preflight_inconclusive,
            )
            print(msg)
            run_panel_fe.bump_bulk_run_count(counts, msg)
        except Exception as exc:
            print(f"  ✗ {hid}: runner crashed — {exc}")
            counts["crashed"] = counts.get("crashed", 0) + 1
    run_panel_fe.print_bulk_run_summary("preflight-ready rerun", counts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually rerun the preflight-ready subset.")
    parser.add_argument("--limit", type=int, default=None, help="Cap reruns to the first N candidates.")
    parser.add_argument("--force", action="store_true", help="Pass --force through to the underlying runner.")
    parser.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts during reruns.",
    )
    args = parser.parse_args()

    candidates, counts = collect_candidates()
    print_audit(candidates, counts)
    if args.apply:
        apply_reruns(
            candidates,
            limit=args.limit,
            force=args.force,
            write_preflight_inconclusive=args.write_preflight_inconclusive,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
