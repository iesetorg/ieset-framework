#!/usr/bin/env python3
"""Fetch the second IESET mega-roundup.

Wave 1 pulled the core macro/governance spine. This wave targets broad
under-covered libraries: extra WDI health/finance/demography/sector variables,
UNDP HDI components, Heritage annual economic-freedom releases, UNCTAD trade
and FDI bulk panels, WID inequality bulk extracts, Eurostat EU detail, BLS US
state/county labour panels, and more OECD/ECB series.
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


WID_COUNTRIES = [
    "US", "GB", "DE", "FR", "IT", "ES", "NL", "SE", "NO", "DK", "FI",
    "IE", "CA", "AU", "NZ", "JP", "KR", "CN", "IN", "ID", "BR", "MX",
    "AR", "CL", "CO", "PE", "ZA", "NG", "EG", "TR", "PL", "CZ", "EE",
    "SG", "IL", "CH", "AT", "BE", "PT", "GR",
]


MEGA2: list[Job] = [
    # WDI: recurring missing controls and quality-of-life outcomes.
    Job("world_bank_wdi", "NE.EXP.GNFS.ZS", "exports share of GDP"),
    Job("world_bank_wdi", "NE.IMP.GNFS.ZS", "imports share of GDP"),
    Job("world_bank_wdi", "NE.GDI.FTOT.ZS", "gross fixed capital formation"),
    Job("world_bank_wdi", "TT.PRI.MRCH.XD.WD", "net barter terms of trade"),
    Job("world_bank_wdi", "DT.DOD.DECT.GN.ZS", "external debt share of GNI"),
    Job("world_bank_wdi", "FM.LBL.BMNY.GD.ZS", "broad money share of GDP"),
    Job("world_bank_wdi", "FM.LBL.BMNY.ZG", "broad money growth"),
    Job("world_bank_wdi", "GC.TAX.TOTL.GD.ZS", "tax revenue share"),
    Job("world_bank_wdi", "GC.REV.XGRT.GD.ZS", "government revenue excluding grants"),
    Job("world_bank_wdi", "GB.XPD.RSDV.GD.ZS", "research and development share"),
    Job("world_bank_wdi", "IP.PAT.RESD", "resident patent applications"),
    Job("world_bank_wdi", "IT.NET.USER.ZS", "internet users share"),
    Job("world_bank_wdi", "FX.OWN.TOTL.ZS", "financial account ownership"),
    Job("world_bank_wdi", "IC.BUS.NREG", "new business registrations"),
    Job("world_bank_wdi", "IC.REG.DURS", "business start-up time"),
    Job("world_bank_wdi", "SH.MED.PHYS.ZS", "physicians per 1,000 people"),
    Job("world_bank_wdi", "SH.XPD.CHEX.GD.ZS", "current health expenditure share"),
    Job("world_bank_wdi", "SH.XPD.OOPC.CH.ZS", "out-of-pocket health spending share"),
    Job("world_bank_wdi", "SH.STA.MMRT", "maternal mortality ratio"),
    Job("world_bank_wdi", "SH.DYN.NMRT", "neonatal mortality rate"),
    Job("world_bank_wdi", "SP.POP.1564.TO.ZS", "working-age population share"),
    Job("world_bank_wdi", "SP.POP.DPND.OL", "old-age dependency ratio"),
    Job("world_bank_wdi", "SP.URB.TOTL.IN.ZS", "urban population share"),
    Job("world_bank_wdi", "SL.AGR.EMPL.ZS", "agriculture employment share"),
    Job("world_bank_wdi", "SL.IND.EMPL.ZS", "industry employment share"),
    Job("world_bank_wdi", "SL.SRV.EMPL.ZS", "services employment share"),
    Job("world_bank_wdi", "NV.AGR.TOTL.ZS", "agriculture value-added share"),
    Job("world_bank_wdi", "NV.IND.TOTL.ZS", "industry value-added share"),
    Job("world_bank_wdi", "AG.LND.AGRI.ZS", "agricultural land share"),
    Job("world_bank_wdi", "AG.PRD.FOOD.XD", "food production index"),
    Job("world_bank_wdi", "EG.USE.ELEC.KH.PC", "electricity use per capita"),
    Job("world_bank_wdi", "EG.ELC.FOSL.ZS", "fossil electricity share"),
    Job("world_bank_wdi", "EG.ELC.RNEW.ZS", "renewable electricity share"),
    Job("world_bank_wdi", "EN.ATM.CO2E.PC", "CO2 emissions per capita"),
    Job("world_bank_wdi", "ST.INT.ARVL", "international tourist arrivals"),
    Job("world_bank_wdi", "SE.SEC.ENRR", "secondary enrolment"),
    Job("world_bank_wdi", "SE.PRM.CMPT.ZS", "primary completion"),
    Job("world_bank_wdi", "SE.XPD.TOTL.GD.ZS", "education spending share"),

    # Human development, institutions, inequality.
    Job("undp_hdi", "hdi", "UNDP Human Development Index"),
    Job("undp_hdi", "life_expectancy", "UNDP life expectancy component"),
    Job("undp_hdi", "mean_years_schooling", "UNDP mean schooling component"),
    Job("undp_hdi", "expected_years_schooling", "UNDP expected schooling component"),
    Job("undp_hdi", "gni_per_capita", "UNDP GNI per capita component"),
    *[Job("heritage_ief", f"ief_{year}", f"Heritage IEF release {year}") for year in range(2010, 2027)],
    Job("heritage_ief", "ief_panel", "Heritage annual panel from local releases"),
    Job(
        "wid",
        "wid_all",
        "WID targeted bulk extract for broad inequality variables",
        {"country_filter": WID_COUNTRIES},
    ),
    Job(
        "wid",
        "top-0-1-share-of-total-income",
        "WID top 0.1 percent income share",
        {"country_filter": WID_COUNTRIES},
    ),

    # Trade, investment, food, labour.
    Job("unctad", "US.FDI", "UNCTAD FDI inward flows"),
    Job("unctad", "US.FDIstock", "UNCTAD FDI inward stock"),
    Job("unctad", "US.TradeMerchTotal", "UNCTAD merchandise trade matrix"),
    Job("unctad", "US.TradeServ", "UNCTAD services trade"),
    Job("unctad", "US.GVCParticipation", "UNCTAD global value chain participation"),
    Job("faostat", "food_balance_sheets", "FAOSTAT food import dependence panel"),
    Job("bls", "LAU_state_unemployment_rate_panel", "BLS state unemployment rates"),
    Job("bls", "LAU_state_employment_population_ratio_panel", "BLS state employment-population ratios"),
    Job("bls", "QCEW_state_total_employment_panel", "BLS QCEW state total employment"),
    Job("bls", "QCEW_state_NAICS722_employment_panel", "BLS QCEW state food-service employment"),
    Job("bls", "QCEW_county_NAICS722_employment_panel", "BLS QCEW county food-service employment"),

    # Eurostat deep EU panel coverage.
    Job("eurostat", "nama_10_gdp", "Eurostat national accounts GDP"),
    Job("eurostat", "nama_10_a10", "Eurostat sectoral national accounts"),
    Job("eurostat", "nama_10_lp_ulc", "Eurostat labour productivity and unit labour costs"),
    Job("eurostat", "une_rt_a", "Eurostat annual unemployment"),
    Job("eurostat", "lfsa_egan", "Eurostat employment by activity"),
    Job("eurostat", "ilc_di12", "Eurostat income distribution"),
    Job("eurostat", "ilc_li02", "Eurostat at-risk-of-poverty threshold"),
    Job("eurostat", "demo_pjan", "Eurostat population by age/sex"),
    Job("eurostat", "migr_imm1ctz", "Eurostat immigration by citizenship"),
    Job("eurostat", "rd_e_gerdtot", "Eurostat R&D expenditure"),
    Job("eurostat", "nrg_pc_205", "Eurostat electricity prices"),

    # OECD/ECB additional macro, taxation, social, and financial market detail.
    Job("oecd", "DSD_KEI", "OECD key economic indicators"),
    Job("oecd", "DSD_TAX", "OECD taxation indicators"),
    Job("oecd", "DSD_SOCX@DF_SOCX_AGG", "OECD social expenditure aggregates"),
    Job("oecd", "DSD_PENSIONS@DF_PENSIONS_REPL_RATE", "OECD pension replacement rates"),
    Job("oecd", "HEALTH_STAT@DF_AMENABLE_MORT", "OECD amenable mortality"),
    Job("oecd", "HOUSE_PRICES", "OECD residential house prices"),
    Job("oecd", "HFCE", "OECD household final consumption expenditure"),
    Job("oecd", "GGEXP", "OECD government expenditure"),
    Job("ecb", "ICP", "ECB harmonised inflation euro area"),
    Job("ecb", "euribor", "ECB euribor money-market rate"),
    Job("ecb", "financial_markets_yields_10yr", "ECB euro-area 10-year yield"),
    Job("ecb", "BSI/M.U2.Y.V.M30.X.I.U2.2300.Z01.A", "ECB euro-area M3 annual growth"),
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
    out_json = ROOT / "engine" / "audits" / f"data_roundup_mega2_{stamp}.json"
    out_md = ROOT / "engine" / "audits" / f"data_roundup_mega2_{stamp}.md"
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
        "# IESET Mega Data Roundup 2",
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

    selected = MEGA2
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
