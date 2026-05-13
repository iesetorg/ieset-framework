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


def _run_job(job: Job) -> tuple[FetchResult | None, dict[str, Any]]:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
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
        }
    try:
        result = REGISTRY[job.publisher].fetch(job.series_id, **(job.kwargs or {}))
    except Exception as exc:  # noqa: BLE001
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
