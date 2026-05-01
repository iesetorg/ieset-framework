#!/usr/bin/env python3
"""Bulk backfill + rerun campaign for inconclusive hypotheses.

This script turns the persisted inconclusive corpus into an executable queue:

1. Scan ``engine/runs/*/diagnostics.json`` for missing source tokens.
2. Collapse them to unique publisher/series pairs with frequency counts.
3. Skip anything already materialized on disk.
4. Optionally fetch the top missing series for ready publishers.
5. Optionally rerun the newly preflight-ready inconclusive subset.

Usage:
  ./venv/bin/python scripts/run_inconclusive_campaign.py
  ./venv/bin/python scripts/run_inconclusive_campaign.py --apply --top 40 --rerun
  ./venv/bin/python scripts/run_inconclusive_campaign.py --apply --publishers owid,world_bank_wdi,imf_pcps
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))

import audit_inconclusive_load
import rerun_preflight_ready_inconclusive
import run_panel_fe
from data.fetchers import REGISTRY
from data.fetchers._base import FetchResult, utc_stamp, write_manifest

PUBLISHERS_YAML = ROOT / "data" / "fetchers" / "publishers.yaml"


@dataclass
class QueueItem:
    publisher: str
    series: str
    count: int


def load_publishers_doc() -> dict:
    if not PUBLISHERS_YAML.exists():
        return {}
    return yaml.safe_load(PUBLISHERS_YAML.read_text()) or {}


PUBLISHERS_DOC = load_publishers_doc()


def canonical_publisher(publisher: str) -> str:
    publisher = str(publisher).strip()
    pubs = (PUBLISHERS_DOC.get("publishers") or {})
    for pub_id, rec in pubs.items():
        if publisher == pub_id:
            return pub_id
        aliases = {str(a) for a in rec.get("aliases", []) or []}
        if publisher in aliases:
            return pub_id
    return publisher


def resolve_series_alias(publisher: str, series: str) -> str:
    publisher, resolved = run_panel_fe.resolve_source_target(
        canonical_publisher(publisher),
        str(series),
    )
    mod = REGISTRY.get(publisher)
    aliases = getattr(mod, "SERIES_ALIASES", None)
    if isinstance(aliases, dict):
        if resolved in aliases:
            return str(aliases[resolved])
        upper = str(resolved).upper()
        if upper in aliases:
            return str(aliases[upper])
    per_pub = getattr(run_panel_fe, "SERIES_ALIAS_BY_PUBLISHER", {})
    return per_pub.get(publisher, {}).get(str(resolved).upper(), str(resolved))


def auth_env_var(publisher: str) -> str | None:
    pubs = (PUBLISHERS_DOC.get("publishers") or {})
    rec = pubs.get(canonical_publisher(publisher)) or {}
    return rec.get("auth_env_var")


def is_manual_publisher(publisher: str) -> bool:
    pubs = (PUBLISHERS_DOC.get("publishers") or {})
    rec = pubs.get(canonical_publisher(publisher)) or {}
    endpoint = str(rec.get("endpoint") or "")
    return endpoint.startswith("manual://")


def support_status(publisher: str, series: str) -> str | None:
    publisher, series = run_panel_fe.resolve_source_target(
        canonical_publisher(publisher),
        str(series),
    )
    mod = REGISTRY.get(publisher)
    if mod is None:
        return "no ready fetcher registered"
    if is_manual_publisher(publisher):
        return "manual-drop publisher"
    env_name = auth_env_var(publisher)
    if env_name and not os.environ.get(env_name):
        return f"missing auth env var {env_name}"
    supported = getattr(mod, "SUPPORTED", None)
    if isinstance(supported, dict):
        resolved = resolve_series_alias(publisher, series)
        if resolved not in supported:
            return "unsupported series id for fetcher"
    return None


def series_materialized(publisher: str, series: str) -> bool:
    publisher = canonical_publisher(publisher)
    resolved_pub, resolved_series = run_panel_fe.resolve_source_target(publisher, str(series))
    candidates = {
        (publisher, str(series)),
        (resolved_pub, resolved_series),
        (resolved_pub, resolve_series_alias(resolved_pub, resolved_series)),
    }
    for candidate_pub, candidate_series in candidates:
        if run_panel_fe.latest_vintage(candidate_pub, candidate_series) is not None:
            return True
    return False


def build_missing_queue(*, publishers: set[str] | None = None) -> list[QueueItem]:
    by_series: Counter[tuple[str, str]] = Counter()
    runs_glob = ROOT / "engine" / "runs"
    for path in runs_glob.glob("*/diagnostics.json"):
        try:
            doc = json.loads(path.read_text())
        except Exception:
            continue
        if not audit_inconclusive_load.is_inconclusive(doc):
            continue
        for pub, series in audit_inconclusive_load.iter_missing_tokens(doc):
            pub = canonical_publisher(pub)
            if publishers and pub not in publishers:
                continue
            by_series[(pub, series)] += 1

    items = [
        QueueItem(publisher=pub, series=series, count=count)
        for (pub, series), count in by_series.items()
        if not series_materialized(pub, series)
    ]
    return sorted(items, key=lambda row: (-row.count, row.publisher, row.series))


def render_plan(
    queue: list[QueueItem],
    *,
    top: int,
    per_publisher: int | None,
    only_fetchable: bool,
) -> str:
    chosen = shortlist(queue, top=top, per_publisher=per_publisher, only_fetchable=only_fetchable)
    lines = [
        f"Missing-series queue: {len(queue)} unresolved unique publisher/series pairs",
        f"Planned fetch batch:  {len(chosen)} item(s)",
        "",
    ]
    blocked = Counter()
    for item in queue:
        reason = support_status(item.publisher, item.series)
        if reason:
            blocked[reason] += 1
    if blocked:
        lines.append("Blocked series in queue:")
        for reason, count in blocked.most_common():
            lines.append(f"  {reason:32s} {count:4d}")
        lines.append("")
    by_pub = Counter(item.publisher for item in chosen)
    lines.append("Batch by publisher:")
    for pub, count in by_pub.most_common():
        lines.append(f"  {pub:24s} {count:4d}")
    lines.append("")
    lines.append("Top queued series:")
    for item in chosen[:80]:
        lines.append(f"  {item.publisher}:{item.series}  (seen in {item.count} inconclusive run(s))")
    return "\n".join(lines)


def shortlist(
    queue: list[QueueItem],
    *,
    top: int,
    per_publisher: int | None,
    only_fetchable: bool,
) -> list[QueueItem]:
    if per_publisher is None:
        items = queue
        if only_fetchable:
            items = [item for item in queue if support_status(item.publisher, item.series) is None]
        return items[:top]
    taken: Counter[str] = Counter()
    out: list[QueueItem] = []
    for item in queue:
        if len(out) >= top:
            break
        if only_fetchable and support_status(item.publisher, item.series) is not None:
            continue
        if taken[item.publisher] >= per_publisher:
            continue
        out.append(item)
        taken[item.publisher] += 1
    return out


def fetch_queue(items: list[QueueItem]) -> tuple[list[FetchResult], list[dict]]:
    successes: list[FetchResult] = []
    failures: list[dict] = []
    for item in items:
        publisher, series = run_panel_fe.resolve_source_target(
            canonical_publisher(item.publisher),
            str(item.series),
        )
        mod = REGISTRY.get(publisher)
        if mod is None:
            failures.append({
                "publisher": publisher,
                "series": series,
                "count": item.count,
                "error": "no ready fetcher registered",
            })
            continue

        env_name = auth_env_var(publisher)
        if env_name and not os.environ.get(env_name):
            failures.append({
                "publisher": publisher,
                "series": series,
                "count": item.count,
                "error": f"missing auth env var {env_name}",
            })
            continue

        try:
            result = mod.fetch(series)
            successes.append(result)
            print(
                f"OK  {publisher}:{series} -> {result.rows} rows "
                f"({result.start_date} -> {result.end_date})"
            )
        except Exception as exc:
            failures.append({
                "publisher": publisher,
                "series": series,
                "count": item.count,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=2),
            })
            print(f"ERR {publisher}:{series} — {exc}")
    return successes, failures


def rerun_ready_subset(*, limit: int | None = None) -> None:
    candidates, counts = rerun_preflight_ready_inconclusive.collect_candidates()
    rerun_preflight_ready_inconclusive.print_audit(candidates, counts)
    rerun_preflight_ready_inconclusive.apply_reruns(
        candidates,
        limit=limit,
        force=False,
        write_preflight_inconclusive=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Fetch the shortlisted series instead of printing the plan only.")
    parser.add_argument("--top", type=int, default=40, help="Maximum number of unique series to queue.")
    parser.add_argument(
        "--per-publisher",
        type=int,
        default=12,
        help="Cap the queued series per publisher. Pass 0 to disable.",
    )
    parser.add_argument(
        "--publishers",
        default=None,
        help="Comma-separated allowlist of publishers (e.g. owid,world_bank_wdi,imf_pcps).",
    )
    parser.add_argument("--rerun", action="store_true", help="Rerun the preflight-ready inconclusive subset after fetching.")
    parser.add_argument(
        "--rerun-limit",
        type=int,
        default=None,
        help="Cap reruns to the first N currently preflight-ready hypotheses.",
    )
    parser.add_argument(
        "--include-blocked",
        action="store_true",
        help="Include manual/auth-missing/unsupported items in the shortlist instead of fetchable-only mode.",
    )
    args = parser.parse_args()

    pub_filter = None
    if args.publishers:
        pub_filter = {canonical_publisher(p.strip()) for p in args.publishers.split(",") if p.strip()}
    per_publisher = None if args.per_publisher == 0 else args.per_publisher

    only_fetchable = not args.include_blocked
    queue = build_missing_queue(publishers=pub_filter)
    print(render_plan(queue, top=args.top, per_publisher=per_publisher, only_fetchable=only_fetchable))

    if not args.apply:
        return 0

    batch = shortlist(queue, top=args.top, per_publisher=per_publisher, only_fetchable=only_fetchable)
    print("")
    print(f"Fetching {len(batch)} queued series...")
    successes, failures = fetch_queue(batch)
    if successes:
        manifest = write_manifest(successes, run_stamp=f"bootstrap_{utc_stamp()}")
        print("")
        print(f"Wrote manifest: {manifest.relative_to(ROOT)}")
    if failures:
        print("")
        print("Failures:")
        for row in failures[:80]:
            print(f"  {row['publisher']}:{row['series']} — {row['error']}")
        if len(failures) > 80:
            print(f"  ... {len(failures) - 80} more")

    if args.rerun:
        print("")
        rerun_ready_subset(limit=args.rerun_limit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
