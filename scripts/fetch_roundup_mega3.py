#!/usr/bin/env python3
"""Fetch the third IESET mega-roundup.

This wave targets specialist but high-legitimacy sources that broaden the
framework beyond generic macro panels: capital controls, refugee/migration,
crime, central-bank and national-stat-office panels, exchange-rate regimes,
asset prices, energy transition, and country case-study underlays.
"""
from __future__ import annotations

import argparse
import json
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
    rationale: str
    kwargs: dict[str, Any] | None = None


MEGA3: list[Job] = [
    # Capital controls, exchange-rate regimes, crisis and asset-price history.
    Job("chinn_ito", "kaopen_index_normalized", "Chinn-Ito capital account openness"),
    Job("chinn_ito", "kaopen_raw", "Chinn-Ito raw KAOPEN factor"),
    Job("chinn_ito", "kaopen_components", "Chinn-Ito AREAER restriction components"),
    Job("irr", "era_classification_monthly_1940_2019", "Ilzetzki-Reinhart-Rogoff exchange-rate regimes"),
    Job("irr", "unified_market_analysis_1946_2021", "IRR unified exchange-rate market analysis"),
    Job("irr", "anchor_currency_monthly_1946_2019", "IRR anchor currency classifications"),
    Job("shiller", "ie_data", "Shiller long-run equity, rates, and CAPE"),
    Job("shiller", "home_price_index", "Shiller long-run US home-price index"),
    Job("hanke", "hyperinflation_table", "Hanke-Krus hyperinflation episode table"),

    # Migration, displacement, crime, and state capacity.
    Job("unhcr", "population", "UNHCR population by country of asylum"),
    Job("unhcr", "population_origin", "UNHCR displacement by country of origin"),
    Job("unhcr", "asylum_decisions", "UNHCR asylum decisions"),
    Job("unhcr", "solutions", "UNHCR durable solutions"),
    Job("un_desa", "international_migrant_stock", "UN DESA international migrant stock seed panel"),
    Job("unodc", "intentional_homicide", "UNODC intentional homicide"),
    Job("unodc", "violent_crime", "UNODC violent and sexual crime"),
    Job("unodc", "corruption", "UNODC bribery/corruption statistics"),
    Job("unodc", "prisons", "UNODC prison population"),

    # Energy transition and productivity.
    Job("irena", "installed_capacity_renewable", "IRENA renewable installed capacity"),
    Job("irena", "installed_capacity_solar_pv", "IRENA solar PV installed capacity"),
    Job("irena", "installed_capacity_wind", "IRENA wind installed capacity"),
    Job("eu_klems", "tfp", "EU KLEMS country-level TFP"),
    Job("eu_klems", "tfp_industry", "EU KLEMS industry TFP"),
    Job("eu_klems", "unit_labour_cost", "EU KLEMS unit labour cost"),
    Job("eu_klems", "value_added_per_hour", "EU KLEMS labour productivity per hour"),
    Job("eu_klems", "value_added_per_worker", "EU KLEMS labour productivity per worker"),

    # US Census and poverty / housing / education underlays.
    Job("us_census", "ACS", "US Census ACS state income and population"),
    Job("us_census", "acs_education_attainment", "US Census ACS education attainment"),
    Job("us_census", "acs_school_enrollment", "US Census ACS school enrollment"),
    Job("us_census", "annual_state_population_estimates", "US Census state population estimates"),
    Job("us_census", "population", "US Census national population"),
    Job("us_census", "saipe", "US Census SAIPE state poverty/income"),
    Job("us_census", "spm_child_poverty_rate", "US Census child SPM poverty"),
    Job("us_census", "building_permits", "US Census building permits"),
    Job("us_census", "trade_in_goods", "US Census goods exports"),

    # National statistical offices and central banks for case-study robustness.
    Job("ons", "ABMI", "ONS UK real GDP"),
    Job("ons", "D7BT", "ONS UK CPI"),
    Job("ons", "MGSX", "ONS UK unemployment"),
    Job("ons", "KAB9", "ONS UK real average weekly earnings"),
    Job("ons", "IHXW", "ONS UK real GDP per head"),
    Job("ons", "LZVB", "ONS UK output per hour"),
    Job("ons", "LF24", "ONS UK employment rate"),
    Job("ons", "CDKO", "ONS UK house price index"),
    Job("boe", "LPMAUYM", "Bank of England M4 monetary stock"),
    Job("rba", "d03hist", "RBA monetary aggregates"),
    Job("rba", "f01hist", "RBA interest rates"),
    Job("rba", "g01hist", "RBA consumer price inflation"),
    Job("rba", "f11hist", "RBA exchange rates"),
    Job("destatis", "42153", "Destatis industrial production"),
    Job("destatis", "61111", "Destatis consumer price index"),
    Job("destatis", "81000", "Destatis GDP and components"),
    Job("destatis", "62121", "Destatis nominal and real earnings"),
    Job("destatis", "13231", "Destatis labour-force participation"),
    Job("scb", "population", "Statistics Sweden population"),
    Job("scb", "gdp", "Statistics Sweden GDP"),
    Job("scb", "cpi", "Statistics Sweden CPI"),
    Job("scb", "unemployment", "Statistics Sweden labour force"),
    Job("ssb", "GDP", "Statistics Norway GDP"),
    Job("ssb", "formuesskatt_base", "Statistics Norway wealth-tax base"),
    Job("ssb", "skatteinntekter", "Statistics Norway tax revenue"),
    Job("ssb", "utvandring", "Statistics Norway migration by citizenship"),
    Job("ine", "IPC_general", "INE Spain CPI"),
    Job("ine", "EPA_PARO", "INE Spain unemployment"),
    Job("ine", "EPA_OCUPADOS", "INE Spain employment"),
    Job("ine", "CNTR_PIB", "INE Spain GDP"),
    Job("ine", "ECV_pobreza", "INE Spain poverty rate"),
    Job("ipeadata", "IPCA", "IPEADATA Brazil CPI"),
    Job("ipeadata", "GDP", "IPEADATA Brazil GDP"),
    Job("ipeadata", "MIN_WAGE", "IPEADATA Brazil minimum wage"),
    Job("ipeadata", "UNEMPLOYMENT", "IPEADATA Brazil unemployment"),
    Job("ipeadata", "BOLSA_FAMILIA", "IPEADATA Bolsa Familia coverage"),
    Job("eia", "international_energy_statistics", "EIA Venezuela crude production seed"),
]


def run_job(job: Job) -> tuple[FetchResult | None, dict[str, Any]]:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if job.publisher not in REGISTRY:
        return None, {
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
            "publisher": job.publisher,
            "series_id": job.series_id,
            "status": "failed",
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rationale": job.rationale,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1200],
            "kwargs": job.kwargs or {},
        }
    return result, {
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


def write_audit(records: list[dict[str, Any]], manifest_path: Path | None) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_json = ROOT / "engine" / "audits" / f"data_roundup_mega3_{stamp}.json"
    out_md = ROOT / "engine" / "audits" / f"data_roundup_mega3_{stamp}.md"
    ok = [r for r in records if r["status"] == "ok"]
    failed = [r for r in records if r["status"] != "ok"]
    payload = {
        "generated_utc": stamp,
        "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path else None,
        "counts": {
            "jobs": len(records),
            "ok": len(ok),
            "failed": len(failed),
            "rows": sum(int(r.get("rows") or 0) for r in ok),
        },
        "records": records,
    }
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# IESET Mega Data Roundup 3",
        "",
        f"- generated_utc: `{stamp}`",
        f"- manifest: `{payload['manifest']}`",
        f"- jobs: {len(records)}",
        f"- ok: {len(ok)}",
        f"- failed: {len(failed)}",
        f"- rows landed: {payload['counts']['rows']:,}",
        "",
        "## Landed",
        "",
    ]
    for r in ok:
        lines.append(
            f"- `{r['publisher']}:{r['series_id']}` — {r['rows']:,} rows, "
            f"{r['period'][0]} to {r['period'][1]} — {r['rationale']}"
        )
    if failed:
        lines.extend(["", "## Failed / Needs Scrape Or Repair", ""])
        for r in failed:
            lines.append(
                f"- `{r['publisher']}:{r['series_id']}` — {r.get('error_type', r['status'])}: "
                f"{str(r.get('error', ''))[:240]}"
            )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"audit_json: {out_json.relative_to(ROOT)}")
    print(f"audit_md:   {out_md.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only", help="Comma-separated publisher ids to run")
    parser.add_argument("--skip", help="Comma-separated publisher:series_id pairs to skip")
    parser.add_argument("--match", help="Comma-separated publisher:series_id pairs to run")
    args = parser.parse_args()

    selected = MEGA3
    if args.match:
        wanted = {x.strip() for x in args.match.split(",") if x.strip()}
        selected = [job for job in selected if f"{job.publisher}:{job.series_id}" in wanted]
    if args.only:
        allowed = {x.strip() for x in args.only.split(",") if x.strip()}
        selected = [job for job in selected if job.publisher in allowed]
    if args.skip:
        skipped = {x.strip() for x in args.skip.split(",") if x.strip()}
        selected = [job for job in selected if f"{job.publisher}:{job.series_id}" not in skipped]
    if args.limit is not None:
        selected = selected[: args.limit]

    results: list[FetchResult] = []
    records: list[dict[str, Any]] = []
    for i, job in enumerate(selected, start=1):
        print(f"[{i}/{len(selected)}] {job.publisher}:{job.series_id} — {job.rationale}", flush=True)
        result, record = run_job(job)
        records.append(record)
        if result:
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
