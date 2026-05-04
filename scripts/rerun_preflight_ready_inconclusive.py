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
        return "preflight_ready" if (o is not None and t is not None) else "preflight_blocked"

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
        return "preflight_ready" if (o is not None and t is not None) else "preflight_blocked"

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
        return "preflight_ready"

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
        return "preflight_ready"

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
