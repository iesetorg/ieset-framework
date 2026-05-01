#!/usr/bin/env python3
"""Rerun inconclusive runs linked to a specific missing-data publisher.

This script scans persisted ``engine/runs/*/diagnostics.json`` artifacts,
selects inconclusive runs whose missing-variable diagnostics reference a
target publisher, and optionally reruns the subset whose missing series are
loadable now.

Usage:
  ./venv/bin/python scripts/rerun_missing_publisher_inconclusive.py world_bank_wdi
  ./venv/bin/python scripts/rerun_missing_publisher_inconclusive.py world_bank_wdi --apply
  ./venv/bin/python scripts/rerun_missing_publisher_inconclusive.py world_bank_wdi --apply --limit 25
  ./venv/bin/python scripts/rerun_missing_publisher_inconclusive.py world_bank_wdi --all-matching
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_descriptive
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
    "synth_did": run_synth_did,
    "synthetic_control": run_synth_did,
}


def verdict_text(doc: dict) -> str:
    return str(doc.get("verdict_label") or doc.get("verdict") or "").strip()


def is_inconclusive(doc: dict) -> bool:
    return verdict_text(doc).upper().startswith("INCONCLUSIVE")


def iter_missing_series(doc: dict, publisher: str):
    status = doc.get("data_status") or {}
    missing = status.get("variables_missing") if isinstance(status, dict) else []
    want = publisher.strip().lower()
    for entry in missing or []:
        source = str(entry.get("source") or "").strip()
        if not source:
            continue
        for clause in run_panel_fe.parse_source_clauses(source):
            pub, series = run_panel_fe.resolve_source_target(
                clause["publisher"],
                clause["series"],
            )
            if pub.lower() == want:
                yield f"{pub}:{series}"


def collect_candidates(
    publisher: str,
    *,
    require_loadable: bool,
) -> tuple[list[dict], Counter, Counter]:
    loadable_cache: dict[str, bool] = {}
    counts = Counter()
    by_series = Counter()
    candidates: list[dict] = []

    for path in glob.glob(RUNS_GLOB):
        doc = json.loads(Path(path).read_text())
        if not is_inconclusive(doc):
            continue
        hid = Path(path).parent.name
        template = str(doc.get("template") or "unknown")
        series = sorted(set(iter_missing_series(doc, publisher)))
        if not series:
            continue
        counts["matching_inconclusive"] += 1
        for token in series:
            by_series[token] += 1
        now_loadable = []
        for token in series:
            cached = loadable_cache.get(token)
            if cached is None:
                cached = run_panel_fe.load_variable(token) is not None
                loadable_cache[token] = cached
            if cached:
                now_loadable.append(token)
        if now_loadable:
            counts["loadable_now"] += 1
        else:
            counts["still_missing_now"] += 1
            if require_loadable:
                continue
        candidates.append(
            {
                "hypothesis_id": hid,
                "template": template,
                "series": series,
                "loadable_now": now_loadable,
            }
        )
    candidates.sort(key=lambda row: (row["template"], row["hypothesis_id"]))
    return candidates, counts, by_series


def print_audit(candidates: list[dict], counts: Counter, by_series: Counter, publisher: str) -> None:
    print(f"Publisher-linked inconclusive audit: {publisher}")
    print(f"  matching inconclusive runs: {counts['matching_inconclusive']}")
    print(f"  with at least one loadable series now: {counts['loadable_now']}")
    print(f"  still fully missing now: {counts['still_missing_now']}")
    print("")
    print("Top missing series in existing diagnostics:")
    for token, count in by_series.most_common(20):
        print(f"  {count:4d} {token}")
    print("")
    print(f"Rerun candidates: {len(candidates)}")
    for row in candidates[:50]:
        loadable = ", ".join(row["loadable_now"][:2]) if row["loadable_now"] else "none"
        print(f"  {row['template']:24s} {row['hypothesis_id']}  [{loadable}]")
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
    print(f"Rerunning {len(subset)} publisher-linked inconclusive run(s)...")
    for row in subset:
        hid = row["hypothesis_id"]
        template = row["template"]
        runner = RUNNER_BY_TEMPLATE.get(template)
        if runner is None:
            print(f"  ✗ {hid}: no runner for template={template}")
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
    run_panel_fe.print_bulk_run_summary("publisher-linked rerun", counts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("publisher", help="Publisher prefix to target, e.g. world_bank_wdi")
    parser.add_argument("--apply", action="store_true", help="Actually rerun the selected subset.")
    parser.add_argument("--limit", type=int, default=None, help="Cap reruns to the first N candidates.")
    parser.add_argument("--force", action="store_true", help="Pass --force through to the underlying runner.")
    parser.add_argument(
        "--all-matching",
        action="store_true",
        help="Rerun all matching inconclusives, even if the missing series are still unavailable now.",
    )
    parser.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts during reruns.",
    )
    args = parser.parse_args()

    candidates, counts, by_series = collect_candidates(
        args.publisher,
        require_loadable=not args.all_matching,
    )
    print_audit(candidates, counts, by_series, args.publisher)
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
