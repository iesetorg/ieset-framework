#!/usr/bin/env python3
"""High-row-count trusted-source gap wave for IESET.

This wave targets broad official panels that repeatedly appear as blockers in
hypothesis diagnostics: BIS credit/DSR/property panels, WDI Doing Business and
education/labour indicators, ILOSTAT labour indicators, OECD social/labour/
housing/pension flows, Eurostat EU macro/labour panels, and remaining BLS state
or county labour panels.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers import REGISTRY  # noqa: E402
from data.fetchers._base import FetchResult, write_manifest  # noqa: E402


@dataclass(frozen=True)
class Job:
    cluster: str
    publisher: str
    series_id: str
    rationale: str
    kwargs: dict[str, Any] | None = None


JOBS: list[Job] = [
    # BIS: credit-cycle, crisis, household debt, housing, and exchange-rate blockers.
    Job("bis_credit", "bis", "WS_CREDIT_GAP", "BIS credit-to-GDP gap; crisis and credit-boom hypotheses"),
    Job("bis_credit", "bis", "WS_TC", "BIS total credit to non-financial sector"),
    Job("bis_credit", "bis", "WS_DSR", "BIS debt-service ratios"),
    Job("bis_housing", "bis", "WS_SPP", "BIS selected residential property prices"),
    Job("bis_fx", "bis", "WS_EER", "BIS effective exchange rates"),

    # WDI: common all-country blockers from housing, legal/institutional, education, migration, informality.
    Job("wdi_business", "world_bank_wdi", "IC.REC.COST", "Resolving insolvency cost"),
    Job("wdi_business", "world_bank_wdi", "IC.REC.DURS", "Years to resolve insolvency"),
    Job("wdi_business", "world_bank_wdi", "IC.LGL.DURS", "Time to enforce contracts"),
    Job("wdi_business", "world_bank_wdi", "IC.CNST.PRMT", "Construction permits / permit burden"),
    Job("wdi_business", "world_bank_wdi", "IC.TAX.TOTL.CP.ZS", "Total tax and contribution rate"),
    Job("wdi_education_labour", "world_bank_wdi", "SE.SEC.CMPT.LO.ZS", "Lower-secondary completion"),
    Job("wdi_education_labour", "world_bank_wdi", "SL.TLF.ACTI.65UP.ZS", "65+ labour-force participation"),
    Job("wdi_education_labour", "world_bank_wdi", "SL.ISV.IFRM.ZS", "Informal employment share"),
    Job("wdi_migration", "world_bank_wdi", "SM.EMI.TERT.ZS", "Tertiary educated emigration rate"),
    Job("wdi_trade", "world_bank_wdi", "TX.VAL.AGRI.ZS.UN", "Agricultural raw materials exports share"),

    # ILOSTAT: broad labour outcomes that often substitute for missing OECD-only labour coverage.
    Job("ilo_labour", "ilostat", "unemployment_rate", "ILO unemployment rate"),
    Job("ilo_labour", "ilostat", "EAP_2WAP_SEX_AGE_RT", "ILO labour-force participation rate"),
    Job("ilo_labour", "ilostat", "EAR_4MTH_SEX_RT", "ILO earnings / wage index alias"),
    Job("ilo_labour", "ilostat", "EMP_TEMP_SEX_ECO_NB_E", "ILO employment by status/economic activity"),

    # OECD: exact source families appearing in diagnostics.
    Job("oecd_social", "oecd", "DSD_SOCX@DF_SOCX_AGG", "OECD social expenditure aggregates"),
    Job("oecd_social", "oecd", "DSD_SOCX@DF_SOCX_ALMP", "OECD active labour-market programme expenditure"),
    Job("oecd_labour", "oecd", "EPL_OV", "OECD employment-protection legislation"),
    Job("oecd_labour", "oecd", "DSD_LMS_low_education_unemployment_rate", "OECD low-education unemployment"),
    Job("oecd_pensions", "oecd", "DSD_PENSIONS@DF_PENSIONS_REPL_RATE", "OECD pension replacement rates"),
    Job("oecd_distribution", "oecd", "DSD_IDD@DF_CHILD_POV", "OECD child poverty"),
    Job("oecd_housing", "oecd", "HOUSE_PRICES", "OECD residential house prices"),
    Job("oecd_macro", "oecd", "HFCE", "OECD household final consumption expenditure"),
    Job("oecd_macro", "oecd", "GGEXP", "OECD government expenditure"),
    Job("oecd_productivity", "oecd", "DSD_PDB", "OECD productivity database"),

    # Eurostat: large EU panels for housing, labour, national accounts, productivity, electricity prices.
    Job("eurostat_macro", "eurostat", "nama_10_gdp", "Eurostat national accounts GDP"),
    Job("eurostat_macro", "eurostat", "nama_10_a10", "Eurostat sectoral national accounts"),
    Job("eurostat_labour", "eurostat", "une_rt_a", "Eurostat unemployment"),
    Job("eurostat_labour", "eurostat", "lfsa_egan", "Eurostat employment by activity"),
    Job("eurostat_distribution", "eurostat", "ilc_di12", "Eurostat income distribution"),
    Job("eurostat_migration", "eurostat", "migr_imm1ctz", "Eurostat immigration by citizenship"),
    Job("eurostat_energy", "eurostat", "nrg_pc_205", "Eurostat electricity prices"),

    # BLS: minimum-wage/employment underlays. QCEW county can be large.
    Job("bls_state_county", "bls", "LAU_state_unemployment_rate_panel", "BLS state unemployment rates"),
    Job("bls_state_county", "bls", "LAU_state_employment_population_ratio_panel", "BLS state employment-population ratios"),
    Job("bls_state_county", "bls", "QCEW_state_total_employment_panel", "BLS QCEW state total employment"),
    Job("bls_state_county", "bls", "QCEW_state_NAICS722_employment_panel", "BLS QCEW state food-service employment"),
    Job("bls_state_county", "bls", "QCEW_county_NAICS722_employment_panel", "BLS QCEW county food-service employment"),
]


def _read_key() -> None:
    key = getpass.getpass("ZenRows API key: ").strip()
    if key:
        os.environ["ZENROWS_API_KEY"] = key


def _clusters_arg(value: str) -> set[str]:
    return {part.strip() for part in value.split(",") if part.strip()}


def run_job(job: Job) -> tuple[FetchResult | None, dict[str, Any]]:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if job.publisher not in REGISTRY:
        return None, {
            "cluster": job.cluster,
            "publisher": job.publisher,
            "series_id": job.series_id,
            "status": "missing_fetcher",
            "started_utc": started,
            "rationale": job.rationale,
            "error": f"known fetchers: {sorted(REGISTRY)}",
        }
    try:
        result = REGISTRY[job.publisher].fetch(job.series_id, **(job.kwargs or {}))
    except Exception as exc:  # noqa: BLE001
        return None, {
            "cluster": job.cluster,
            "publisher": job.publisher,
            "series_id": job.series_id,
            "status": "failed",
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rationale": job.rationale,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1600],
            "kwargs": job.kwargs or {},
        }
    return result, {
        "cluster": job.cluster,
        "publisher": result.publisher,
        "series_id": result.series_id,
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
        "kwargs": job.kwargs or {},
    }


def write_audit(records: list[dict[str, Any]], results: list[FetchResult]) -> tuple[Path, Path, Path | None]:
    tag = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    audit_dir = ROOT / "engine" / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / f"data_gap_mega_wave_{tag}.json"
    md_path = audit_dir / f"data_gap_mega_wave_{tag}.md"
    manifest = write_manifest(results) if results else None
    payload = {
        "generated_utc": tag,
        "manifest": str(manifest.relative_to(ROOT)) if manifest else None,
        "jobs": len(records),
        "ok": sum(1 for r in records if r["status"] == "ok"),
        "failed": sum(1 for r in records if r["status"] == "failed"),
        "rows_landed": sum(int(r.get("rows") or 0) for r in records if r["status"] == "ok"),
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    by_cluster: dict[str, dict[str, int]] = {}
    for r in records:
        bucket = by_cluster.setdefault(r["cluster"], {"ok": 0, "failed": 0, "rows": 0})
        bucket[r["status"]] = bucket.get(r["status"], 0) + 1
        bucket["rows"] += int(r.get("rows") or 0)
    lines = [
        "# Data-Gap Mega Wave",
        "",
        f"- generated_utc: `{tag}`",
        f"- manifest: `{str(manifest.relative_to(ROOT)) if manifest else ''}`",
        f"- jobs: {payload['jobs']}",
        f"- ok: {payload['ok']}",
        f"- failed: {payload['failed']}",
        f"- rows landed: {payload['rows_landed']:,}",
        "",
        "## Cluster Summary",
        "",
        "| cluster | ok | failed | rows |",
        "| --- | ---: | ---: | ---: |",
    ]
    for cluster, bucket in sorted(by_cluster.items()):
        lines.append(f"| `{cluster}` | {bucket.get('ok', 0)} | {bucket.get('failed', 0)} | {bucket['rows']:,} |")
    lines.extend(["", "## Landed", ""])
    for r in records:
        if r["status"] == "ok":
            lines.append(
                f"- `{r['publisher']}:{r['series_id']}` - {int(r['rows']):,} rows, "
                f"{(r.get('period') or ['',''])[0]} to {(r.get('period') or ['',''])[1]} - {r['rationale']}"
            )
    failed = [r for r in records if r["status"] != "ok"]
    if failed:
        lines.extend(["", "## Failed / Still Blocked", ""])
        for r in failed:
            lines.append(
                f"- `{r['publisher']}:{r['series_id']}` - {r.get('error_type', r['status'])}: {r.get('error', '')}"
            )
    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--read-zenrows-key-stdin", action="store_true")
    parser.add_argument(
        "--cluster",
        default="all",
        help="Comma-separated clusters, or all. Available: " + ", ".join(sorted({j.cluster for j in JOBS})),
    )
    args = parser.parse_args()
    if args.read_zenrows_key_stdin:
        _read_key()
    wanted = None if args.cluster == "all" else _clusters_arg(args.cluster)
    jobs = [j for j in JOBS if wanted is None or j.cluster in wanted]
    records: list[dict[str, Any]] = []
    results: list[FetchResult] = []
    for i, job in enumerate(jobs, start=1):
        print(f"[{i}/{len(jobs)}] {job.publisher}:{job.series_id} ({job.cluster})", flush=True)
        result, record = run_job(job)
        records.append(record)
        if result is not None:
            results.append(result)
            print(f"  OK rows={result.rows:,} vintage={result.parquet_path.relative_to(ROOT)}", flush=True)
        else:
            print(f"  FAIL {record.get('error_type', record['status'])}: {record.get('error', '')[:240]}", flush=True)
    json_path, md_path, manifest = write_audit(records, results)
    print(f"manifest: {manifest.relative_to(ROOT) if manifest else ''}")
    print(f"audit_json: {json_path.relative_to(ROOT)}")
    print(f"audit_md:   {md_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
