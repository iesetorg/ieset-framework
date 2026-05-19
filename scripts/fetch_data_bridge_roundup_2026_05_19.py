#!/usr/bin/env python3
"""Targeted data-bridge roundup for the remaining runnability blockers.

Clusters covered:
  - OECD SDMX aliases / fiscal-output-labour/productivity bridge
  - BOJ / ECB / FRED monetary bridge
  - WITS / UN Comtrade / UNCTAD trade bridge
  - WIPO innovation bridge
  - IEA / IRENA energy bridge

Reads ZenRows from stdin when requested, stores no secret, writes a manifest and
an audit. This script records failures as first-class audit rows rather than
stopping the whole wave.
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
    # OECD alias / SDMX bridge.
    Job("oecd_bridge", "oecd", "OutputGap", "OECD KEI output-gap family used across fiscal/monetary controls"),
    Job("oecd_bridge", "oecd", "DSD_PDB", "OECD Productivity Database for productivity/wage/labour-share channels"),
    Job("oecd_bridge", "oecd", "DSD_LFS_DF_LFS_INDIC", "OECD labour-force indicators / harmonised unemployment aliases"),
    Job("oecd_bridge", "oecd", "DSD_EARN", "OECD earnings / real-wage aliases"),
    Job("oecd_bridge", "oecd", "DSD_SOCX@DF_SOCX_ALMP", "OECD ALMP social expenditure bridge"),
    Job("oecd_bridge", "oecd", "FDI_statistics", "OECD FDI statistics for investment-opening tests"),
    Job("oecd_bridge", "oecd", "DSD_PENSIONS@DF_PENSIONS_REPL_RATE", "OECD pension replacement-rate bridge"),
    Job("oecd_bridge", "oecd", "HFCE", "OECD household consumption national accounts"),
    Job("oecd_bridge", "oecd", "GGEXP", "OECD government expenditure national accounts"),

    # Monetary bridge.
    Job("monetary_bridge", "ecb", "FM.B.U2.EUR.4F.KR.MRR_FR.LEV", "ECB deposit facility / policy-rate alias"),
    Job("monetary_bridge", "ecb", "financial_markets_yields_2yr", "ECB 2y yield curve for forward-guidance tests"),
    Job("monetary_bridge", "ecb", "financial_markets_yields_5yr", "ECB 5y yield curve for forward-guidance tests"),
    Job("monetary_bridge", "ecb", "financial_markets_yields_10yr", "ECB 10y yield curve and fiscal credibility controls"),
    Job("monetary_bridge", "ecb", "financial_markets_money_market_OIS", "ECB OIS / money-market channel"),
    Job("monetary_bridge", "boj", "money_stock_m2", "BoJ money stock M2, Japan monetary bridge"),
    Job("monetary_bridge", "boj", "monetary_base", "BoJ monetary base, QE and monetarist bridge"),
    Job("monetary_bridge", "boj", "policy_rate", "BoJ policy-rate / call-rate bridge"),
    Job("monetary_bridge", "boj", "bond_yields_10y", "BoJ/JGB 10y rate bridge"),
    Job("monetary_bridge", "boj", "bond_yields_30y", "BoJ/JGB 30y rate bridge"),
    Job("monetary_bridge", "fred", "BOGMBASE_JPN", "FRED mirror for Japan monetary base if API key is present"),
    Job("monetary_bridge", "fred", "IRLTLT30JPM156N", "FRED OECD mirror for Japan 30-year long rate if present"),

    # WITS / Comtrade / UNCTAD bridge.
    Job("trade_bridge", "wits", "import_value", "WITS imports-to-world panel", {"start_year": 1988, "end_year": 2023}),
    Job("trade_bridge", "wits", "export_value_constant_usd", "WITS/WDI merchandise-export value panel for import-substitution tests"),
    Job("trade_bridge", "wits", "weighted_mean_applied_tariff", "WITS AHS weighted-average applied tariff", {"start_year": 1988, "end_year": 2023}),
    Job("trade_bridge", "wits", "tariff_average", "WITS tariff-average alias", {"start_year": 1988, "end_year": 2023}),
    Job("trade_bridge", "wits", "product_concentration", "WITS product/export concentration panel", {"start_year": 1988, "end_year": 2023}),
    Job("trade_bridge", "wits", "high_tech_exports", "High-tech exports mirror for industrial-upgrading specs"),
    Job("trade_bridge", "wits", "unique_hs6_products", "WITS exported HS6 product-count panel", {"start_year": 1988, "end_year": 2023}),
    Job("trade_bridge", "wits", "product_lines", "WITS imported HS6 product-count panel", {"start_year": 1988, "end_year": 2023}),
    Job("trade_bridge", "unctad", "US.FDI", "UNCTAD FDI flow panel"),
    Job("trade_bridge", "unctad", "US.GVCParticipation", "UNCTAD GVC participation panel"),
    Job("trade_bridge", "un_comtrade", "HS72_HS76_HS25_HS31", "UN Comtrade CBAM HS2 value basket", {"start_year": 2015, "end_year": 2024}),
    Job("trade_bridge", "un_comtrade", "HS72_HS76_HS25_HS31_volume", "UN Comtrade CBAM HS2 volume/weight basket", {"start_year": 2015, "end_year": 2024}),
    Job("trade_bridge", "un_comtrade", "export_value_by_sector", "UN Comtrade HS2 export-value panel", {"start_year": 2015, "end_year": 2024}),

    # WIPO / innovation bridge.
    Job("innovation_bridge", "wipo", "patent_applications", "WIPO resident + non-resident patent applications"),
    Job("innovation_bridge", "wipo", "patent_applications_resident", "WIPO resident patent applications"),
    Job("innovation_bridge", "wipo", "patent_applications_non_resident", "WIPO non-resident patent applications"),
    Job("innovation_bridge", "wipo", "ip_statistics_data_center", "WIPO IP statistics data-center country-year patent mirror"),

    # Energy bridge.
    Job("energy_bridge", "iea", "fossil_subsidies_estimate", "IEA fossil-fuel subsidies tracker"),
    Job("energy_bridge", "iea", "co2_emissions_from_fuel_combustion", "IEA CO2 from fuel-combustion highlights"),
    Job("energy_bridge", "iea", "industrial_electricity_price", "IEA industrial electricity prices"),
    Job("energy_bridge", "iea", "electricity_statistics", "IEA electricity-statistics public product"),
    Job("energy_bridge", "iea", "electricity_balance", "IEA electricity balance"),
    Job("energy_bridge", "iea", "nuclear_capacity_factor", "IEA nuclear capacity/generation bridge"),
    Job("energy_bridge", "irena", "lcoe_solar_pv", "IRENA solar PV LCOE"),
    Job("energy_bridge", "irena", "lcoe_wind_onshore", "IRENA onshore wind LCOE"),
]


def _read_zenrows(enabled: bool) -> None:
    if not enabled:
        return
    key = sys.stdin.readline().strip()
    if key:
        os.environ["ZENROWS_API_KEY"] = key


def _redact(text: object) -> str:
    out = str(text)
    for env_name in ("ZENROWS_API_KEY", "FRED_API_KEY", "UN_COMTRADE_KEY"):
        key = os.environ.get(env_name)
        if key:
            out = out.replace(key, f"<{env_name}>")
    return out


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
            "kwargs": job.kwargs or {},
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
            "error": _redact(exc)[:2000],
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
        "methodology_url": result.methodology_url,
        "extra": result.extra,
        "kwargs": job.kwargs or {},
    }


def write_audit(records: list[dict[str, Any]], manifest: Path | None) -> tuple[Path, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_json = ROOT / "engine" / "audits" / f"data_bridge_roundup_2026-05-19_{stamp}.json"
    out_md = ROOT / "engine" / "audits" / f"data_bridge_roundup_2026-05-19_{stamp}.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    ok = [r for r in records if r["status"] == "ok"]
    failed = [r for r in records if r["status"] != "ok"]
    by_cluster: dict[str, dict[str, int]] = {}
    for record in records:
        bucket = by_cluster.setdefault(record["cluster"], {"ok": 0, "failed": 0, "rows": 0})
        if record["status"] == "ok":
            bucket["ok"] += 1
            bucket["rows"] += int(record.get("rows") or 0)
        else:
            bucket["failed"] += 1
    payload = {
        "generated_utc": stamp,
        "manifest": str(manifest.relative_to(ROOT)) if manifest else None,
        "counts": {
            "jobs": len(records),
            "ok": len(ok),
            "failed": len(failed),
            "rows_landed": sum(int(r.get("rows") or 0) for r in ok),
            "by_cluster": by_cluster,
        },
        "records": records,
    }
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Data-Bridge Roundup — 2026-05-19",
        "",
        f"- generated_utc: `{stamp}`",
        f"- manifest: `{payload['manifest']}`",
        f"- jobs: {len(records)}",
        f"- ok: {len(ok)}",
        f"- failed: {len(failed)}",
        f"- rows landed: {payload['counts']['rows_landed']:,}",
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
        period = record.get("period") or ["", ""]
        lines.append(
            f"- `{record['publisher']}:{record['series_id']}` — {int(record['rows']):,} rows, "
            f"{period[0]} to {period[1]} — {record['rationale']}"
        )
    if failed:
        lines.extend(["", "## Failed / Still Blocked", ""])
        for record in failed:
            lines.append(
                f"- `{record['publisher']}:{record['series_id']}` — "
                f"{record.get('error_type', record['status'])}: {record.get('error', '')[:500]}"
            )
    out_md.write_text("\n".join(lines) + "\n")
    return out_json, out_md


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read-zenrows-key-stdin", action="store_true")
    parser.add_argument("--cluster", help="Comma-separated cluster names to run")
    parser.add_argument("--match", help="Comma-separated publisher:series pairs to run")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    _read_zenrows(args.read_zenrows_key_stdin)

    selected = JOBS
    if args.cluster:
        wanted = {part.strip() for part in args.cluster.split(",") if part.strip()}
        selected = [job for job in selected if job.cluster in wanted]
    if args.match:
        wanted_pairs = {part.strip() for part in args.match.split(",") if part.strip()}
        selected = [job for job in selected if f"{job.publisher}:{job.series_id}" in wanted_pairs]
    if args.limit is not None:
        selected = selected[: args.limit]

    records: list[dict[str, Any]] = []
    results: list[FetchResult] = []
    for index, job in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {job.publisher}:{job.series_id} ({job.cluster})", flush=True)
        result, record = run_job(job)
        records.append(record)
        if result is None:
            print(f"  FAIL {record.get('error_type', record['status'])}: {record.get('error', '')[:240]}", flush=True)
        else:
            results.append(result)
            print(f"  OK rows={result.rows:,} vintage={result.parquet_path.relative_to(ROOT)}", flush=True)

    manifest = write_manifest(results) if results else None
    audit_json, audit_md = write_audit(records, manifest)
    print(f"manifest: {manifest.relative_to(ROOT) if manifest else ''}")
    print(f"audit_json: {audit_json.relative_to(ROOT)}")
    print(f"audit_md:   {audit_md.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
