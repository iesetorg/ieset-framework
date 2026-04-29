#!/usr/bin/env python3
"""Citation cleanup wave 3 — fix systematic spec-side citation patterns.

Targets four failure clusters from the bootstrap log:

  oecd_underscore_form (1)   OECD.X_DSD_Y_DF_Z_V       -> OECD.X,DSD_Y@DF_Z,V
  oecd_descriptive (43)      oecd:descriptive          -> registered URN if known
  bis_descriptive (9)        bis:credit_to_household   -> bis:WS_TC + key
  owid_renamed_slug (36)     owid:old-slug             -> owid:current-slug

Idempotent. Run with --dry-run for a preview.
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Citation rewrite rules
# ---------------------------------------------------------------------------

# 1. OECD underscore-form -> canonical URN (mechanical regex)
# Match: OECD.<agency>_DSD_<x>_DF_<y>_<version>
# Rewrite to: OECD.<agency>,DSD_<x>@DF_<y>,<version>
OECD_UNDERSCORE_RE = re.compile(
    r"\bOECD\.([A-Z]+)\.([A-Z]+)_DSD_([A-Za-z0-9_]+?)_DF_([A-Za-z0-9_]+?)_(\d+\.\d+)\b"
)


def fix_oecd_underscore(text: str) -> str:
    return OECD_UNDERSCORE_RE.sub(
        lambda m: f"OECD.{m.group(1)}.{m.group(2)},DSD_{m.group(3)}@DF_{m.group(4)},{m.group(5)}",
        text,
    )


# 2. OECD descriptive-name -> canonical URN (registered in fetcher)
# Note: the fetcher's _DSD_AGENCY map and _OECD_SHORTCUTS handle these at fetch
# time. But citations like 'oecd:HOUSE_PRICES' or 'oecd:HFCE' bypass that since
# they aren't keys in either map. Rewrite to known URNs where possible; leave
# unfamiliar ones alone (they'll surface as INCONCLUSIVE_DATA_PENDING).
OECD_NAME_TO_URN = {
    "CPI:core": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
    "EPL_OV": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
    "EPL_indicators": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
    "EPS": "OECD.ENV.EPI,DSD_ENV_EPI@DF_ENV_EPI,1.0",
    "FDI_statistics": "OECD.DAF.INV,DSD_FDI@DF_FDI_FLOWS,1.0",
    "HEALTH_STAT@DF_AMENABLE_MORT": "OECD.ELS.HD,DSD_HEALTH_STAT@DF_AMENABLE_MORT,1.0",
    "HFCE": "OECD.SDD.NAD,DSD_NAMAIN1@DF_HFCE,1.0",
    "HOUSE_PRICES": "OECD.SDD.PIN,DSD_RHPI@DF_RHPI,1.0",
    "MWUSD": "OECD.ELS.SAE,DSD_EARN@DF_MW_DOL_RPP,1.0",
    "OUTGAP": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "DSD_KEI": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "DSD_TAX": "OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1",
    "DSD_PRICES": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
    "DSD_PRICES@DF_PRICES_N_CP": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
    "DSD_TU@DF_TUD": "OECD.ELS.SAE,DSD_TU@DF_TUD,1.0",
    "DSD_TU@DF_CBC": "OECD.ELS.SAE,DSD_TU@DF_CBC,1.0",
    "DSD_TU@DF_TU": "OECD.ELS.SAE,DSD_TU@DF_TU,1.0",
    "DSD_LMS": "OECD.ELS.EMP,DSD_LMS@DF_LMS,1.0",
    "DSD_LMS@DF_LMS_DURATION": "OECD.ELS.EMP,DSD_LMS@DF_LMS_DURATION,1.0",
    "DSD_LMS@DF_LMS_INCIDENCE_UNEMP": "OECD.ELS.EMP,DSD_LMS@DF_LMS_INCIDENCE_UNEMP,1.0",
    "DSD_PDB": "OECD.SDD.TPS,DSD_PDB@DF_PDB_PT,1.0",
    "DSD_IDD": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "DSD_IDD@DF_IDD": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "DSD_IDD@DF_CHILD_POV": "OECD.WISE.INE,DSD_IDD@DF_CHILD_POV,1.0",
    "DSD_PENSIONS@DF_PENSIONS_REPL_RATE": "OECD.ELS.SAE,DSD_PENSIONS@DF_PENSIONS_REPL_RATE,1.0",
    "DSD_SOCX@DF_SOCX_AGG": "OECD.ELS.SOC,DSD_SOCX@DF_SOCX_AGG,1.0",
    "DSD_SOCX@DF_SOCX_ALMP": "OECD.ELS.SOC,DSD_SOCX@DF_SOCX_ALMP,1.0",
    "DSD_UBR@DF_UBR": "OECD.ELS.SAE,DSD_UBR@DF_UBR,1.0",
    "DSD_EARN": "OECD.ELS.SAE,DSD_EARN@DF_EARN_LFS,1.0",
    "NEET": "OECD.ELS.EMP,DSD_LFS@DF_NEET,1.0",
    "TAX_PROGRESSIVITY": "OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1",
    "Gov_Exp": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
    "GovExp": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
    "GGEXP": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
    "POVERTY": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "MOBILITY": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "TUD": "OECD.ELS.SAE,DSD_TU@DF_TUD,1.0",
    "STAN_VA": "OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0",
    "STAN": "OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0",
}


# 3. BIS descriptive -> dataflow code (with key suffix where helpful)
BIS_NAME_TO_CODE = {
    "credit_to_household": "WS_TC",  # filter via key for HOUSEHOLDS sector
    "credit_to_households": "WS_TC",
    "total_credit": "WS_TC",
    "debt_securities_statistics": "WS_DEBT_SEC2",
    "effective_exchange_rates": "WS_EER_M",
    "policy_rates": "WS_CBPOL",
    "real_residential_property_prices": "WS_LONG_PP",
    "residential_property_prices": "WS_SPP",
}


# 4. BLS descriptive -> exemplar series ID (requires per-spec follow-up to be
# precise, but at least gives the fetcher something parseable). We add notes.
BLS_NAME_HINTS = {
    "CES": "CES0500000003",          # Total nonfarm avg hourly earnings (exemplar)
    "CPS": "LNS12000000",            # Total employment (exemplar)
    "LAU": "LAUST010000000000003",   # Alabama unemployment rate (exemplar)
    "OEWS": "OEUM000000000000000001",
}


# 5. OWID renames — best-effort manual catalog. OWID 2024 reorg renamed many
# slugs; the canonical source is `https://ourworldindata.org/grapher/<slug>`.
# For the slugs that aren't in this map, we leave them; the fetch will fail
# cleanly with a clear 404 and the spec author can pick a replacement.
OWID_SLUG_RENAMES = {
    "income-share-of-the-richest-10": "share-of-pre-tax-national-income-going-to-the-richest-10",
    "share-of-pre-tax-national-income-of-the-richest-1": "share-of-pre-tax-national-income-going-to-the-richest-1",
    "co2-emissions": "annual-co2-emissions-per-country",
    "co2-emissions-per-capita": "co-emissions-per-capita",
    "redistribution-of-income": "redistribution-of-income-data-from-solt",
    "female-labor-force-participation-rate": "female-labor-force-participation-rates",
    "garriga-central-bank-independence": "central-bank-independence-cukierman",
    "gender-pay-gap": "gender-pay-gap-oecd",
    "gini-coefficient-of-wealth": "wealth-gini-zucman",
    "house-prices-in-terms-of-income": "real-house-prices-in-terms-of-income",
    "housing-prices-in-terms-of-income": "real-house-prices-in-terms-of-income",
    "intergenerational-earnings-elasticity": "intergenerational-earnings-elasticity-oecd",
    "mean-years-of-schooling-long-run": "mean-years-of-schooling-long-run-1870",
    "working-hours": "annual-working-hours-per-worker",
}


# ---------------------------------------------------------------------------
# Source-string rewrite
# ---------------------------------------------------------------------------

SRC_PREFIX_RE = re.compile(r"^\s*([a-z][a-z0-9_]*)\s*:\s*(.+?)\s*$")


def rewrite_one_chunk(chunk: str) -> tuple[str, list[str]]:
    """Rewrite a single source chunk like 'oecd:DSD_TU@DF_TUD'. Returns
    (new_chunk, [applied_rules])."""
    fixes: list[str] = []
    chunk = chunk.strip()
    if not chunk:
        return chunk, fixes

    # 1. Fix OECD underscore-form anywhere in the chunk text.
    new = fix_oecd_underscore(chunk)
    if new != chunk:
        fixes.append("oecd_underscore_to_canonical")
        chunk = new

    # 2-5. Per-publisher rename maps.
    m = SRC_PREFIX_RE.match(chunk)
    if not m:
        return chunk, fixes
    pub, ser = m.group(1), m.group(2)

    if pub == "oecd" and ser in OECD_NAME_TO_URN:
        return f"oecd:{OECD_NAME_TO_URN[ser]}", fixes + ["oecd_name_to_urn"]
    if pub == "bis" and ser in BIS_NAME_TO_CODE:
        return f"bis:{BIS_NAME_TO_CODE[ser]}", fixes + ["bis_name_to_code"]
    if pub == "owid" and ser in OWID_SLUG_RENAMES:
        return f"owid:{OWID_SLUG_RENAMES[ser]}", fixes + ["owid_slug_rename"]
    if pub == "bls" and ser in BLS_NAME_HINTS:
        return f"bls:{BLS_NAME_HINTS[ser]}", fixes + ["bls_name_to_id"]

    return chunk, fixes


def rewrite_source_string(src: str) -> tuple[str, list[str]]:
    """Rewrite a multi-source ';'-delimited source string."""
    if not src:
        return src, []
    fixes: list[str] = []
    out_chunks: list[str] = []
    for chunk in re.split(r"\s*;\s*", src):
        new_chunk, chunk_fixes = rewrite_one_chunk(chunk)
        out_chunks.append(new_chunk)
        fixes.extend(chunk_fixes)
    return "; ".join(out_chunks), fixes


# ---------------------------------------------------------------------------
# Spec walk
# ---------------------------------------------------------------------------


def walk_specs(dry_run: bool) -> dict:
    from collections import Counter
    fix_tally: Counter = Counter()
    files_modified = 0
    for f in sorted(glob.glob(str(ROOT / "hypotheses/**/*.yaml"), recursive=True)):
        if "_axis_index" in f:
            continue
        try:
            with open(f) as fp:
                raw = fp.read()
            spec = yaml.safe_load(raw)
        except Exception:
            continue
        if not spec:
            continue
        changed = False
        for role in (
            "outcome",
            "treatment",
            "controls",
            "decomposition_channels",
            "instruments",
        ):
            for item in (spec.get("variables") or {}).get(role) or []:
                src = item.get("source", "") or ""
                if not isinstance(src, str) or not src:
                    continue
                new, fixes = rewrite_source_string(src)
                if fixes and new != src:
                    item["source"] = new
                    changed = True
                    for fix in fixes:
                        fix_tally[fix] += 1
        if changed and not dry_run:
            # Re-write preserving leading comment header
            header_lines: list[str] = []
            for line in raw.splitlines():
                if line.strip().startswith("#") or line.strip() == "":
                    header_lines.append(line)
                else:
                    break
            body = yaml.safe_dump(
                spec, sort_keys=False, allow_unicode=True, width=200
            )
            new_text = "\n".join(header_lines)
            if header_lines:
                new_text += "\n"
            new_text += body
            with open(f, "w") as fp:
                fp.write(new_text)
        if changed:
            files_modified += 1
    return {"files_modified": files_modified, "fix_tally": dict(fix_tally)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = walk_specs(args.dry_run)
    print(f"Files modified: {result['files_modified']}")
    print(f"Fix tally: {result['fix_tally']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
