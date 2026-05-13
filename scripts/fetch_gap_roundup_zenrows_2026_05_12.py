#!/usr/bin/env python3
"""Focused data-gap roundup using the robust HTTP/ZenRows path.

Reads a ZenRows key from stdin when requested, stores no secret, and writes a
manifest plus audit files. Jobs are deliberately chosen from current blocker
clusters: intergenerational mobility, migration/labour channels, minimum-wage
bite inputs, occupational licensing, IRENA LCOE, and wealth-tax manual panels.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers import REGISTRY
from data.fetchers._base import FetchResult, write_manifest


@dataclass(frozen=True)
class Job:
    publisher: str
    series_id: str
    cluster: str
    rationale: str
    kwargs: dict[str, Any] | None = None


JOBS = [
    Job(
        "oecd",
        "OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0",
        "intergenerational_mobility",
        "OECD education-finance channel for mobility decomposition",
        {"start_period": "2010", "end_period": "2024"},
    ),
    Job(
        "oecd",
        "OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0",
        "intergenerational_mobility",
        "OECD housing/segregation channel for mobility decomposition",
    ),
    Job(
        "oecd",
        "OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0",
        "migration_labour",
        "Immigrant employment rates by educational attainment",
    ),
    Job(
        "oecd",
        "OECD.ELS.IMD,DSD_MIG@DF_MIG_NUP_SEX,1.0",
        "migration_labour",
        "Immigrant employment/unemployment/participation rates by sex",
    ),
    Job(
        "oecd",
        "OECD.ELS.IMD,DSD_MIG_F@DF_MIG_POPF,1.0",
        "migration_labour",
        "Foreign-born population stocks",
    ),
    Job(
        "bls",
        "OEWS_state_p10_hourly_wage_panel",
        "minimum_wage",
        "State all-occupation hourly 10th percentile wage for bite ratios",
    ),
    Job(
        "bls",
        "OEWS_state_median_hourly_wage_panel",
        "minimum_wage",
        "State all-occupation hourly median wage for bite ratios",
    ),
    Job(
        "kleiner_krueger",
        "kk_state_licensing_share_workforce",
        "occupational_licensing",
        "State licensing share of workforce for licensing/mobility rebuild",
    ),
    Job(
        "kleiner_krueger",
        "kk_state_2015_share_pct",
        "occupational_licensing",
        "2015 state licensing cross-section for licensing/mobility rebuild",
    ),
    Job(
        "irena",
        "lcoe_solar_pv",
        "renewables_lcoe",
        "IRENA solar PV LCOE workbook/manual-drop parser",
    ),
    Job(
        "irena",
        "lcoe_wind_onshore",
        "renewables_lcoe",
        "IRENA onshore wind LCOE workbook/manual-drop parser",
    ),
    Job(
        "wealth_tax_manual",
        "revenue_forecast_realized",
        "wealth_tax",
        "Manual realized-vs-forecast wealth-tax panel",
    ),
]


def read_key(enabled: bool) -> None:
    if not enabled:
        return
    key = sys.stdin.readline().strip()
    if key:
        os.environ["ZENROWS_API_KEY"] = key


def run_job(job: Job) -> tuple[FetchResult | None, dict[str, Any]]:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if job.publisher not in REGISTRY:
        return None, {
            "publisher": job.publisher,
            "series_id": job.series_id,
            "cluster": job.cluster,
            "status": "missing_fetcher",
            "started_utc": started,
            "rationale": job.rationale,
            "error": f"known fetchers: {sorted(REGISTRY)}",
        }
    try:
        result = REGISTRY[job.publisher].fetch(job.series_id, **(job.kwargs or {}))
    except Exception as exc:  # noqa: BLE001
        text = str(exc)
        key = os.environ.get("ZENROWS_API_KEY")
        if key:
            text = text.replace(key, "<ZENROWS_API_KEY>")
        return None, {
            "publisher": job.publisher,
            "series_id": job.series_id,
            "cluster": job.cluster,
            "status": "failed",
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rationale": job.rationale,
            "error_type": type(exc).__name__,
            "error": text[:1600],
            "kwargs": job.kwargs or {},
        }
    return result, {
        "publisher": result.publisher,
        "series_id": result.series_id,
        "cluster": job.cluster,
        "status": "ok",
        "started_utc": started,
        "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rationale": job.rationale,
        "rows": result.rows,
        "period": [result.start_date, result.end_date],
        "frequency": result.frequency,
        "vintage": str(result.parquet_path.relative_to(ROOT)),
        "sha256": result.sha256,
        "source_url": result.source_url,
        "extra": result.extra,
        "kwargs": job.kwargs or {},
    }


def write_audit(records: list[dict[str, Any]], manifest_path: Path | None) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_json = ROOT / "engine" / "audits" / f"data_gap_roundup_zenrows_{stamp}.json"
    out_md = ROOT / "engine" / "audits" / f"data_gap_roundup_zenrows_{stamp}.md"
    ok = [r for r in records if r["status"] == "ok"]
    failed = [r for r in records if r["status"] != "ok"]
    by_cluster: dict[str, dict[str, int]] = {}
    for record in records:
        cluster = record["cluster"]
        bucket = by_cluster.setdefault(cluster, {"ok": 0, "failed": 0, "rows": 0})
        if record["status"] == "ok":
            bucket["ok"] += 1
            bucket["rows"] += int(record.get("rows") or 0)
        else:
            bucket["failed"] += 1

    payload = {
        "generated_utc": stamp,
        "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path else None,
        "counts": {
            "jobs": len(records),
            "ok": len(ok),
            "failed": len(failed),
            "rows": sum(int(r.get("rows") or 0) for r in ok),
            "by_cluster": by_cluster,
        },
        "records": records,
    }
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# ZenRows Data-Gap Roundup",
        "",
        f"- generated_utc: `{stamp}`",
        f"- manifest: `{payload['manifest']}`",
        f"- jobs: {len(records)}",
        f"- ok: {len(ok)}",
        f"- failed: {len(failed)}",
        f"- rows landed: {payload['counts']['rows']:,}",
        "",
        "## Cluster Summary",
        "",
        "| cluster | ok | failed | rows |",
        "| --- | ---: | ---: | ---: |",
    ]
    for cluster, counts in sorted(by_cluster.items()):
        lines.append(f"| `{cluster}` | {counts['ok']} | {counts['failed']} | {counts['rows']:,} |")
    lines.extend(["", "## Landed", ""])
    for record in ok:
        lines.append(
            f"- `{record['publisher']}:{record['series_id']}` - {record['rows']:,} rows, "
            f"{record['period'][0]} to {record['period'][1]} - {record['rationale']}"
        )
    if failed:
        lines.extend(["", "## Failed / Still Blocked", ""])
        for record in failed:
            lines.append(
                f"- `{record['publisher']}:{record['series_id']}` - "
                f"{record.get('error_type', record['status'])}: {record.get('error', '')[:300]}"
            )
    out_md.write_text("\n".join(lines) + "\n")
    print(f"audit_json: {out_json.relative_to(ROOT)}")
    print(f"audit_md:   {out_md.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read-zenrows-key-stdin", action="store_true")
    parser.add_argument("--match", help="Comma-separated publisher:series_id pairs to run")
    parser.add_argument("--cluster", help="Comma-separated clusters to run")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    read_key(args.read_zenrows_key_stdin)
    selected = JOBS
    if args.match:
        wanted = {x.strip() for x in args.match.split(",") if x.strip()}
        selected = [job for job in selected if f"{job.publisher}:{job.series_id}" in wanted]
    if args.cluster:
        clusters = {x.strip() for x in args.cluster.split(",") if x.strip()}
        selected = [job for job in selected if job.cluster in clusters]
    if args.limit is not None:
        selected = selected[: args.limit]

    results: list[FetchResult] = []
    records: list[dict[str, Any]] = []
    for i, job in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}] {job.publisher}:{job.series_id} ({job.cluster})", flush=True)
        result, record = run_job(job)
        records.append(record)
        if result is not None:
            results.append(result)
            print(f"  OK rows={result.rows} vintage={result.parquet_path.relative_to(ROOT)}", flush=True)
        else:
            print(f"  FAIL {record.get('error_type', record['status'])}: {record.get('error')}", flush=True)

    manifest_path = write_manifest(results) if results else None
    if manifest_path:
        print(f"manifest: {manifest_path.relative_to(ROOT)}")
    write_audit(records, manifest_path)
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
