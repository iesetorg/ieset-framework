#!/usr/bin/env python3
"""Retry official-source data pulls prone to daily/public-file limits.

This script is intentionally narrow: it targets BLS LAU state panels and a
bounded-year-window QCEW state total employment panel. Each successful fetch
produces:
  - a new vintage parquet under data/vintages/bls/
  - a manifest entry under data/manifests/
  - an audit summary under engine/audits/

It is safe to re-run: existing vintages are preserved via timestamped filenames.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers import REGISTRY  # noqa: E402
from data.fetchers._base import FetchResult, write_manifest  # noqa: E402


@dataclass(frozen=True)
class Job:
    publisher: str
    series_id: str
    rationale: str
    kwargs: dict[str, Any] | None = None


def _utc_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _classify_error(exc: Exception) -> dict[str, str]:
    msg = str(exc)
    msg_lower = msg.lower()
    et = type(exc).__name__

    # Common offline/blocked environment markers.
    if "nodename nor servname provided, or not known" in msg_lower or "errno 8" in msg_lower:
        return {"blocker_category": "dns_resolution", "error_hint": "DNS resolver unavailable in runtime"}
    if "name or service not known" in msg_lower:
        return {"blocker_category": "dns_resolution", "error_hint": "DNS lookup failed"}
    if "network is unreachable" in msg_lower or "errno 101" in msg_lower:
        return {"blocker_category": "network_unreachable", "error_hint": "network unreachable"}
    if "timed out" in msg_lower or "timeout" in msg_lower:
        return {"blocker_category": "timeout", "error_hint": "request timed out"}

    # Rate limit-ish.
    if "429" in msg_lower or "too many requests" in msg_lower:
        return {"blocker_category": "rate_limited", "error_hint": "HTTP 429 / rate limited"}

    # BLS often blocks bot-like downloads with 403/Access Denied for some bulk files.
    if "403" in msg_lower or "access denied" in msg_lower or "forbidden" in msg_lower:
        return {"blocker_category": "blocked_403", "error_hint": "HTTP 403 / access denied"}

    return {"blocker_category": "unknown", "error_hint": f"{et}"}


def _expected_source_metadata(job: Job) -> dict[str, str | None]:
    if job.publisher != "bls":
        return {"expected_source_url": None, "expected_methodology_url": None}
    if job.series_id.startswith("LAU_state_"):
        return {
            "expected_source_url": "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            "expected_methodology_url": "https://www.bls.gov/lau/",
        }
    if job.series_id.startswith("QCEW_"):
        return {
            "expected_source_url": "https://data.bls.gov/cew/data/api/{year}/a/industry/10.csv",
            "expected_methodology_url": "https://www.bls.gov/cew/downloadable-data-files.htm",
        }
    return {"expected_source_url": None, "expected_methodology_url": None}


def _run_job(job: Job) -> tuple[FetchResult | None, dict[str, Any]]:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    expected = _expected_source_metadata(job)
    if job.publisher not in REGISTRY:
        return None, {
            "publisher": job.publisher,
            "series_id": job.series_id,
            "status": "missing_fetcher",
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rationale": job.rationale,
            "kwargs": job.kwargs or {},
            "error": f"known fetchers: {sorted(REGISTRY)}",
            **expected,
        }
    try:
        result = REGISTRY[job.publisher].fetch(job.series_id, **(job.kwargs or {}))
    except Exception as exc:  # noqa: BLE001
        classified = _classify_error(exc)
        return None, {
            "publisher": job.publisher,
            "series_id": job.series_id,
            "status": "failed",
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rationale": job.rationale,
            "kwargs": job.kwargs or {},
            "error_type": type(exc).__name__,
            "error": str(exc)[:2400],
            **classified,
            **expected,
        }
    return result, {
        "publisher": result.publisher,
        "series_id": result.series_id,
        "status": "ok",
        "started_utc": started,
        "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rationale": job.rationale,
        "kwargs": job.kwargs or {},
        "rows": result.rows,
        "period": [result.start_date, result.end_date],
        "frequency": result.frequency,
        "vintage": str(result.parquet_path.relative_to(ROOT)),
        "sha256": result.sha256,
        "source_url": result.source_url,
        "methodology_url": result.methodology_url,
        "expected_source_url": expected.get("expected_source_url"),
        "expected_methodology_url": expected.get("expected_methodology_url"),
        "extra": result.extra,
    }


def _write_audit(tag: str, records: list[dict[str, Any]], results: list[FetchResult]) -> tuple[Path, Path, Path | None]:
    audit_dir = ROOT / "engine" / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / f"daily_rate_limited_data_backfill_{tag}.json"
    md_path = audit_dir / f"daily_rate_limited_data_backfill_{tag}.md"
    # Always write a manifest, even for fully-failed runs, so automation
    # operators have a single place to look for "what ran" timestamps.
    manifest = write_manifest(results)
    payload = {
        "generated_utc": tag,
        "manifest": str(manifest.relative_to(ROOT)),
        "jobs": len(records),
        "ok": sum(1 for r in records if r["status"] == "ok"),
        "failed": sum(1 for r in records if r["status"] == "failed"),
        "rows_landed": sum(int(r.get("rows") or 0) for r in records if r["status"] == "ok"),
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Daily Rate-Limited Data Backfill",
        "",
        f"- generated_utc: `{tag}`",
        f"- manifest: `{str(manifest.relative_to(ROOT))}`",
        f"- ok: {payload['ok']}",
        f"- failed: {payload['failed']}",
        f"- rows landed: {payload['rows_landed']:,}",
        "",
        "## Landed",
        "",
    ]
    for r in records:
        if r["status"] == "ok":
            period = r.get("period") or ["", ""]
            lines.append(
                f"- `{r['publisher']}:{r['series_id']}` — {int(r.get('rows') or 0):,} rows, "
                f"{period[0]} to {period[1]} — {r.get('rationale', '')}"
            )
            if r.get("source_url"):
                lines.append(f"  - source_url: `{r['source_url']}`")
            if r.get("methodology_url"):
                lines.append(f"  - methodology_url: `{r['methodology_url']}`")
            if r.get("vintage"):
                lines.append(f"  - vintage: `{r['vintage']}`")
    failed = [r for r in records if r["status"] != "ok"]
    if failed:
        lines.extend(["", "## Failed / Still Blocked", ""])
        for r in failed:
            lines.append(f"- `{r['publisher']}:{r['series_id']}` — {r.get('error_type', r['status'])}: {r.get('error', '')}")
            if r.get("blocker_category"):
                lines.append(f"  - blocker_category: `{r.get('blocker_category')}`")
            if r.get("expected_source_url"):
                lines.append(f"  - expected_source_url: `{r.get('expected_source_url')}`")
            if r.get("expected_methodology_url"):
                lines.append(f"  - expected_methodology_url: `{r.get('expected_methodology_url')}`")

    lines.extend(["", "## Run Settings", ""])
    for key in (
        "BLS_API_KEY",
        "BLS_LAU_START_YEAR",
        "BLS_LAU_END_YEAR",
        "BLS_QCEW_START_YEAR",
        "BLS_QCEW_END_YEAR",
    ):
        val = os.environ.get(key)
        if key == "BLS_API_KEY":
            val = "set" if val else "unset"
        lines.append(f"- `{key}`: `{val}`")

    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lau-start-year", type=int, default=1990)
    parser.add_argument("--lau-end-year", type=int, default=2024)
    parser.add_argument("--qcew-start-year", type=int, default=2019)
    parser.add_argument("--qcew-end-year", type=int, default=2024)
    parser.add_argument("--skip-lau-unemployment", action="store_true")
    parser.add_argument("--skip-lau-epop", action="store_true")
    parser.add_argument("--skip-qcew", action="store_true")
    args = parser.parse_args()

    os.environ["BLS_LAU_START_YEAR"] = str(args.lau_start_year)
    os.environ["BLS_LAU_END_YEAR"] = str(args.lau_end_year)
    os.environ["BLS_QCEW_START_YEAR"] = str(args.qcew_start_year)
    os.environ["BLS_QCEW_END_YEAR"] = str(args.qcew_end_year)

    jobs: list[Job] = []
    if not args.skip_lau_epop:
        jobs.append(
            Job(
                "bls",
                "LAU_state_employment_population_ratio_panel",
                "BLS LAU state monthly employment-population ratio panel",
            )
        )
    if not args.skip_lau_unemployment:
        jobs.append(
            Job(
                "bls",
                "LAU_state_unemployment_rate_panel",
                "BLS LAU state monthly unemployment rate panel",
            )
        )
    if not args.skip_qcew:
        jobs.append(
            Job(
                "bls",
                "QCEW_state_total_employment_panel",
                "BLS QCEW state total employment panel (bounded year window)",
            )
        )

    tag = _utc_tag()
    records: list[dict[str, Any]] = []
    results: list[FetchResult] = []
    for job in jobs:
        result, record = _run_job(job)
        records.append(record)
        if result is not None:
            results.append(result)

    _write_audit(tag, records, results)
    ok = sum(1 for r in records if r["status"] == "ok")
    failed = sum(1 for r in records if r["status"] == "failed")
    print(f"ok={ok} failed={failed} tag={tag}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
