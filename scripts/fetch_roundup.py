#!/usr/bin/env python3
"""Fetch a high-leverage IESET data roundup.

This is intentionally a thin orchestrator over existing data.fetchers modules:
each successful fetch still writes a normal vintage parquet and the combined
manifest records the official source URL, license, hash, and row count.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
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


ROUNDUP: list[Job] = [
    # Core cross-country controls/outcomes used hundreds of times.
    Job("world_bank_wdi", "NY.GDP.PCAP.KD", "real income per person"),
    Job("world_bank_wdi", "NY.GDP.PCAP.PP.KD", "PPP real income per person"),
    Job("world_bank_wdi", "NY.GDP.PCAP.KD.ZG", "real income growth"),
    Job("world_bank_wdi", "NY.GDP.MKTP.KD", "real GDP level"),
    Job("world_bank_wdi", "NY.GDP.MKTP.KD.ZG", "real GDP growth"),
    Job("world_bank_wdi", "NE.TRD.GNFS.ZS", "trade openness"),
    Job("world_bank_wdi", "NE.GDI.TOTL.ZS", "investment share"),
    Job("world_bank_wdi", "NE.CON.GOVT.ZS", "government consumption share"),
    Job("world_bank_wdi", "NE.CON.PRVT.PC.KD", "private consumption per person"),
    Job("world_bank_wdi", "FS.AST.PRVT.GD.ZS", "private credit depth"),
    Job("world_bank_wdi", "FP.CPI.TOTL.ZG", "inflation"),
    Job("world_bank_wdi", "SL.UEM.TOTL.ZS", "unemployment"),
    Job("world_bank_wdi", "SL.EMP.TOTL.SP.ZS", "employment-to-population"),
    Job("world_bank_wdi", "SL.TLF.CACT.FE.ZS", "female labour-force participation"),
    Job("world_bank_wdi", "SP.POP.TOTL", "population"),
    Job("world_bank_wdi", "SP.POP.GROW", "population growth"),
    Job("world_bank_wdi", "SP.DYN.LE00.IN", "life expectancy"),
    Job("world_bank_wdi", "SH.DYN.MORT", "under-5 mortality"),
    Job("world_bank_wdi", "SI.POV.GINI", "income inequality"),
    Job("world_bank_wdi", "SI.POV.DDAY", "extreme poverty"),
    Job("world_bank_wdi", "NV.IND.MANF.ZS", "manufacturing share"),
    Job("world_bank_wdi", "NV.SRV.TOTL.ZS", "services share"),
    Job("world_bank_wdi", "TX.VAL.TECH.MF.ZS", "high-tech export share"),
    Job("world_bank_wdi", "SE.TER.ENRR", "tertiary enrolment"),
    Job("world_bank_wdi", "EG.ELC.ACCS.ZS", "electricity access"),
    Job("world_bank_wdi", "BX.KLT.DINV.WD.GD.ZS", "FDI inflows share"),
    Job("world_bank_wdi", "BN.CAB.XOKA.GD.ZS", "current account balance"),
    Job("world_bank_wdi", "GC.NLD.TOTL.GD.ZS", "fiscal balance"),
    Job("world_bank_wdi", "PA.NUS.FCRF", "official exchange rate"),

    # Governance and institutional controls.
    Job("wgi", "GOV_WGI_GE.EST", "government effectiveness"),
    Job("wgi", "GOV_WGI_RQ.EST", "regulatory quality"),
    Job("wgi", "GOV_WGI_RL.EST", "rule of law"),
    Job("wgi", "GOV_WGI_CC.EST", "control of corruption"),
    Job("wgi", "GOV_WGI_VA.EST", "voice and accountability"),
    Job("wgi", "GOV_WGI_PV.EST", "political stability"),

    # Growth accounting and long-run panels.
    Job("pwt", "pwt_full", "PWT full growth-accounting panel"),
    Job("pwt", "rtfpna", "TFP level"),
    Job("pwt", "rgdpe", "expenditure-side real GDP"),
    Job("pwt", "hc", "human-capital index"),
    Job("pwt", "labsh", "labour share"),
    Job("maddison", "mpd2020", "Maddison long-run GDP per capita"),
    Job("jst", "jst_macrohistory", "Jorda-Schularick-Taylor macrohistory"),

    # Inequality, tax, institutions, and social indicators through OWID bridges.
    Job("owid", "top-marginal-income-tax-rate", "top marginal income tax rates"),
    Job("owid", "top-1-share-of-total-income", "top 1 percent income share"),
    Job("owid", "top-10-share-of-total-income", "top 10 percent income share"),
    Job("owid", "top-1-share-of-total-wealth", "top 1 percent wealth share"),
    Job("owid", "economic-complexity-index", "economic complexity ranking"),
    Job("owid", "ti-corruption-perception-index", "Transparency CPI bridge"),
    Job("owid", "intergenerational-earnings-elasticity", "mobility outcome"),
    Job("owid", "happiness-cantril-ladder", "subjective wellbeing"),
    Job("owid", "co2-emissions-per-capita", "emissions per person"),

    # IMF macro/fiscal and commodity prices.
    Job("imf", "NGDP_RPCH", "IMF real GDP growth"),
    Job("imf", "NGDPDPC", "IMF current-USD GDP per person"),
    Job("imf", "GGXWDG_NGDP", "government debt"),
    Job("imf", "GGR_G01_GDP_PT", "government revenue"),
    Job("imf", "GGX_G01_GDP_PT", "government expenditure"),
    Job("imf", "GGXCNL_NGDP", "net lending/borrowing"),
    Job("imf", "PCPIPCH", "CPI inflation"),
    Job("imf", "BCA_NGDPD", "current account balance"),
    Job("imf_pcps", "POILBRE", "Brent oil price"),
    Job("imf_pcps", "PNGASEUUSDM", "European natural gas price"),
    Job("imf_pcps", "PCOPPUSDM", "copper price"),
    Job("imf_pcps", "PMAIZMT", "maize price"),
    Job("imf_pcps", "PWHEAMT", "wheat price"),

    # Labour, health, macro-finance, and sector panels.
    Job("ilostat", "unemployment_rate", "global unemployment panel"),
    Job("ilostat", "EAP_2WAP_SEX_AGE_RT", "labour-force participation"),
    Job("who_gho", "WHOSIS_000001", "WHO life expectancy"),
    Job("bis", "WS_SPP", "BIS residential property prices"),
    Job("bis", "WS_EER", "BIS effective exchange rates"),
    Job("bis", "WS_TC", "BIS credit to private non-financial sector"),
    Job("bis", "WS_DSR", "BIS debt-service ratios"),

    # OECD high-value chunks: income, labour, product markets, prices.
    Job("oecd", "DSD_IDD", "OECD income distribution database"),
    Job("oecd", "MWUSD", "OECD minimum wage bite / real minimum wage"),
    Job("oecd", "DSD_LMS_low_education_unemployment_rate", "OECD low-education unemployment"),
    Job("oecd", "TUD", "OECD trade-union density"),
    Job("oecd", "EPL_OV", "OECD employment protection legislation"),
    Job("oecd", "DSD_PRICES", "OECD prices"),
    Job("oecd", "DSD_PDB", "OECD productivity database"),
    Job("oecd_pmr", "PMR", "OECD product-market regulation"),

    # Big institutional datasets. These can be dependency-sensitive but are
    # worth trying because one success unlocks many institutional hypotheses.
    Job("vdem", "vdem_cy_full", "V-Dem full country-year democracy/institutional panel"),
    Job("vdem", "codebook", "V-Dem variable metadata"),
    Job("polity5", "polity5", "Polity5 regime authority scores"),
    Job("freedom_house", "fiw", "Freedom House political rights/civil liberties"),
    Job("sipri", "milex", "SIPRI military expenditure"),
    Job("ucdp", "ged", "UCDP georeferenced conflict events"),
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
    }


def write_audit(records: list[dict[str, Any]], manifest_path: Path | None) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_json = ROOT / "engine" / "audits" / f"data_roundup_{stamp}.json"
    out_md = ROOT / "engine" / "audits" / f"data_roundup_{stamp}.md"
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
        "# IESET Data Roundup",
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
    parser.add_argument(
        "--match",
        help="Comma-separated publisher:series_id pairs to run, e.g. oecd:DSD_IDD,bis:WS_TC",
    )
    args = parser.parse_args()

    selected = ROUNDUP
    if args.match:
        wanted = {x.strip() for x in args.match.split(",") if x.strip()}
        selected = [job for job in selected if f"{job.publisher}:{job.series_id}" in wanted]
    if args.only:
        allowed = {x.strip() for x in args.only.split(",") if x.strip()}
        selected = [job for job in selected if job.publisher in allowed]
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
