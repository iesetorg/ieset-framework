#!/usr/bin/env python3
"""Pull every no-auth series in data/manifests/baseline_pull.yaml.

Skips auth-gated publishers (FRED) unless the relevant env var is set.
Continues past individual fetch failures; reports all failures at the end.
Writes one aggregated manifest at data/manifests/bootstrap_<utc>.yaml.

Exit codes:
    0 — every requested series fetched successfully
    1 — at least one fetch failed
    2 — no entries attempted (publishers.yaml empty / baseline_pull.yaml missing)
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers import REGISTRY
from data.fetchers._base import FetchResult, utc_stamp, write_manifest

BASELINE_FILE = ROOT / "data" / "manifests" / "baseline_pull.yaml"


@dataclass
class PullOutcome:
    publisher: str
    series_id: str
    ok: bool
    rows: int = 0
    period: str = ""
    error: str = ""


def auth_check(publisher: str, requires_auth: bool) -> str | None:
    """Return None if auth OK; return a human-readable skip reason otherwise."""
    if not requires_auth:
        return None
    env_var_by_publisher = {"fred": "FRED_API_KEY"}
    env_var = env_var_by_publisher.get(publisher)
    if env_var and not os.environ.get(env_var):
        return f"skipped — {env_var} not set"
    return None


def main() -> int:
    if not BASELINE_FILE.exists():
        print(f"ERROR: {BASELINE_FILE.relative_to(ROOT)} missing", file=sys.stderr)
        return 2

    doc = yaml.safe_load(BASELINE_FILE.read_text())
    pulls = doc.get("pulls") or []
    if not pulls:
        print("ERROR: baseline_pull.yaml has no pulls", file=sys.stderr)
        return 2

    results: list[FetchResult] = []
    outcomes: list[PullOutcome] = []
    skipped: list[tuple[str, str]] = []  # (publisher, reason)

    run_start = time.monotonic()

    # Build a flat list of (publisher, series_id, kwargs) tuples for the worker pool.
    # Honour skip_reason and registry presence up-front.
    work: list[tuple[str, str, dict, object]] = []
    for entry in pulls:
        publisher = entry["publisher"]
        requires_auth = bool(entry.get("requires_auth", False))
        skip_reason = auth_check(publisher, requires_auth)
        if skip_reason:
            skipped.append((publisher, skip_reason))
            continue
        mod = REGISTRY.get(publisher)
        if mod is None:
            skipped.append((publisher, "not in REGISTRY (status != ready in publishers.yaml)"))
            continue
        for series in entry.get("series") or []:
            work.append((publisher, series["id"], series.get("kwargs") or {}, mod))

    # Parallelise across publishers — each fetch is mostly I/O so a thread pool
    # gives a 4-6× speedup. Many fetchers self-throttle internally.
    import concurrent.futures as _cf

    PARALLEL_WORKERS = int(os.environ.get("BOOTSTRAP_WORKERS", "6"))

    def _do_one(work_item: tuple[str, str, dict, object]) -> tuple[str, str, FetchResult | None, str | None, float]:
        publisher, series_id, kwargs, mod = work_item
        t0 = time.monotonic()
        try:
            r = mod.fetch(series_id, **kwargs)
            return publisher, series_id, r, None, time.monotonic() - t0
        except Exception as e:
            return publisher, series_id, None, f"{type(e).__name__}: {e}", time.monotonic() - t0

    print(f"bootstrap: {len(work)} series across {len(set(w[0] for w in work))} publishers, "
          f"{PARALLEL_WORKERS} parallel workers", flush=True)

    with _cf.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
        for publisher, series_id, r, err, dt in ex.map(_do_one, work):
            if r is None:
                outcomes.append(PullOutcome(publisher, series_id, ok=False, error=err or ""))
                print(f"FAIL  {publisher:<20}  {series_id[:50]:<50}  {(err or '')[:120]}", flush=True)
                continue
            results.append(r)
            outcomes.append(PullOutcome(
                publisher=publisher, series_id=series_id, ok=True,
                rows=r.rows, period=f"{r.start_date}→{r.end_date}",
            ))
            print(f"OK    {publisher:<20}  {series_id[:50]:<50}  rows={r.rows:>8}  "
                  f"period={r.start_date}→{r.end_date}  {dt:4.1f}s", flush=True)

    # Write a single aggregated manifest
    manifest_stamp = utc_stamp()
    if results:
        manifest_path = write_manifest(results, run_stamp=f"bootstrap_{manifest_stamp}")
    else:
        manifest_path = None

    # Summary
    total_elapsed = time.monotonic() - run_start
    n_ok = sum(1 for o in outcomes if o.ok)
    n_fail = sum(1 for o in outcomes if not o.ok)
    total_rows = sum(o.rows for o in outcomes if o.ok)

    print()
    print("=" * 78)
    print(f"Bootstrap complete: {n_ok} ok / {n_fail} fail  ({total_rows:,} rows total, {total_elapsed:.1f}s)")
    if skipped:
        print(f"Skipped publishers ({len(skipped)}):")
        for pub, reason in skipped:
            print(f"  - {pub}: {reason}")
    if n_fail:
        print(f"Failures ({n_fail}):")
        for o in outcomes:
            if not o.ok:
                print(f"  - {o.publisher}:{o.series_id} — {o.error}")
    if manifest_path:
        print(f"Manifest: {manifest_path.relative_to(ROOT)}")

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
