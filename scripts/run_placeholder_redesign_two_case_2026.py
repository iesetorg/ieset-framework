#!/usr/bin/env python3
"""Two blind, claim-specific replacements for Fraser/GDP-per-capita placeholders.

--build-roster and --preflight read treatment/shock values and outcome keys only.
Outcome values and null/status masks are opened only by --run or --verify after
separate registration and source-lock commits. Old placeholder IDs are untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "placeholder_claim_specific_replacement_2026_10_10"
RUNNER = "scripts/run_placeholder_redesign_two_case_2026.py"
PREREG = "engine/audits/placeholder_claim_specific_replacement_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/placeholder_claim_specific_replacement_2026_key_roster.csv"
ROSTER_SHA = "1b028afd632f1646503bcf5f0107a917eaddc5cba20e3d5b524bde5bfbe7f19f"
LOCK = "data/pinned_evidence/placeholder_claim_specific_replacement_2026.manifest.json"
SUMMARY = "engine/audits/placeholder_claim_specific_replacement_results_2026-10-10.md"
TESTS = "tests/test_placeholder_claim_specific_replacement_2026.py"
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / 2
CASE = {
    "tax": {
        "id": "oecd_cit_private_investment_forward_calibration_2026", "topic": "fiscal",
        "old_id": "corporate_tax_rate_investment_elasticity", "beta_term": "cut",
        "expected_sign": "+", "meaningful_beta": 0.5,
        "floor": {"min_valid_rows": 500, "min_valid_countries": 30,
                  "min_cut_rows": 50, "min_cut_countries": 20,
                  "min_stable_rows": 200, "min_years_per_country": 5,
                  "max_top_one_percent_partialled_x_share": 0.20,
                  "max_top_country_partialled_x_share": 0.12},
    },
    "epl": {
        "id": "oecd_epl_recession_employment_recovery_calibration_2026", "topic": "labour",
        "old_id": "labour_market_flexibility_employment_resilience", "beta_term": "epl",
        "expected_sign": "-", "meaningful_beta": 0.75,
        "floor": {"min_valid_rows": 60, "min_valid_countries": 30,
                  "min_countries_with_two_nonoverlapping_events": 20,
                  "min_2009_events": 20, "min_2020_events": 20,
                  "min_distinct_event_years": 3, "max_one_event_year_share": 0.50,
                  "min_epl_interquartile_gap": 0.50,
                  "max_top_one_percent_partialled_x_share": 0.25,
                  "max_top_country_partialled_x_share": 0.12},
    },
}
SOURCES = {
    "cit": {"publisher": "oecd", "series_id": "oecd_combined_corporate_income_tax_rate",
            "path": "data/vintages/oecd/oecd_combined_corporate_income_tax_rate@2026-07-23T153857Z.parquet",
            "sha256": "3e9c5987717087d04d5f82461fc1a3fb5e406ba646fb9f333f8c542e5f3f5ee1",
            "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
            "manifest_sha256": "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18"},
    "private": {"publisher": "world_bank_wdi", "series_id": "NE.GDI.FPRV.ZS",
                "path": "data/vintages/world_bank_wdi/NE.GDI.FPRV.ZS@2026-04-30T115003Z.parquet",
                "sha256": "84294f869d513ae4c70154630b31388a53b41c42bf849a006740c9324ebeba14",
                "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
                "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
    "epl": {"publisher": "oecd", "series_id": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
            "path": "data/vintages/oecd/OECD.ELS.EMP_DSD_EPL_OV_DF_EPL_OV_1.0@2026-07-23T154113Z.parquet",
            "sha256": "8a25f91e01153564e8db18723e69ed41298c339255a6ac41b67942dc86022fcd",
            "manifest": "data/manifests/fetch_run_2026-07-23T154936Z.yaml",
            "manifest_sha256": "c2215e0e796c4697d0596848a7498c7a369e5fb2e9baed660e25a8791ffa580d"},
    "gdp": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
            "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
            "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
            "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
            "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "employment": {"publisher": "oecd", "series_id": "DSD_LFS_DF_LFS_INDIC",
                   "path": "data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-07-23T151216Z.parquet",
                   "sha256": "ac58f9ea05eb07e0d4696a81334021120cd679f58847a2fb32dc70e06074e6ae",
                   "manifest": "data/manifests/fetch_run_2026-07-23T151302Z.yaml",
                   "manifest_sha256": "4952688fa8fbf62df91c20409bf4180b75977bc638bb33e2a00a267b3053b601"},
}
# Frozen names in the 1,355-row OECD EPL source. No inferred joins at run time.
EPL_ISO3 = dict(zip(
    "Albania|Argentina|Australia|Austria|Bahamas|Barbados|Belgium|Bolivia|Bosnia-Herzegovina|Brazil|Canada|Chile|China|Colombia|Costa Rica|Croatia|Czech Republic|Denmark|Dominican Republic|Ecuador|El Salvador|Estonia|Finland|Former Yugoslav Republic of Macedonia|France|Germany|Greece|Guatemala|Honduras|Hungary|Iceland|India|Indonesia|Ireland|Israel|Italy|Jamaica|Japan|Kazakhstan|Korea|Kosovo|Latvia|Lithuania|Luxembourg|Malaysia|Mexico|Montenegro|Netherlands|New Zealand|Nicaragua|Norway|Panama|Paraguay|Peru|Poland|Portugal|Russian Federation|Saudi Arabia|Serbia|Slovak Republic|Slovenia|South Africa|Spain|Sweden|Switzerland|Thailand|Tunisia|Türkiye|United Kingdom|United States|Uruguay|Venezuela".split("|"),
    "ALB ARG AUS AUT BHS BRB BEL BOL BIH BRA CAN CHL CHN COL CRI HRV CZE DNK DOM ECU SLV EST FIN MKD FRA DEU GRC GTM HND HUN ISL IND IDN IRL ISR ITA JAM JPN KAZ KOR XKX LVA LTU LUX MYS MEX MNE NLD NZL NIC NOR PAN PRY PER POL PRT RUS SAU SRB SVK SVN ZAF ESP SWE CHE THA TUN TUR GBR USA URY VEN".split()
))
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = {
    "tax": [
        "The OECD combined statutory corporate rate is not an effective marginal or average business tax rate.",
        "WDI NE.GDI.FPRV.ZS is private gross fixed capital formation as a share of GDP, not a capital-stock-per-worker measure; GDP-denominator movements matter.",
        "Two-year investment response is one component of the archived claim and cannot prove faster capital deepening or a stronger response in open economies.",
        "Tax changes can respond to investment shocks; fixed effects and temporal ordering do not identify a causal effect.",
    ],
    "epl": [
        "OECD EPR_V1 measures regular-worker dismissal protection, not every dimension of labour-market flexibility.",
        "OECD employment-to-population ratio, ages 20-64, is not a re-employment duration or cohort measure.",
        "Country event selection uses the deepest negative WDI real-GDP-growth year of each recession spell; 2009 and 2020 dominate the key-only roster.",
        "Cross-country EPL differences and recession severity may reflect omitted institutions and pandemic responses; this is not causal.",
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    lines = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not lines:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return lines[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen first-commit mismatch: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(key: str) -> str:
    case = CASE[key]
    return f"hypotheses/{case['topic']}/{case['id']}.yaml"


def steelman_rel(key: str) -> str:
    return f"hypotheses/steelman/{CASE[key]['id']}.md"


def run_rel(key: str) -> str:
    return f"engine/runs/{CASE[key]['id']}"


def threshold(key: str) -> dict[str, Any]:
    case = CASE[key]
    roles = ["cit", "private"] if key == "tax" else ["epl", "gdp", "employment"]
    return {"family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX,
            "expected_beta_sign": case["expected_sign"],
            "meaningful_beta_min_abs": case["meaningful_beta"],
            **case["floor"], "roster_sha256": ROSTER_SHA,
            "source_files": {role: {f: SOURCES[role][f] for f in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role in roles},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def check_sources() -> None:
    for role, item in SOURCES.items():
        p = ROOT / item["path"]
        m = ROOT / item["manifest"]
        if not p.is_file() or sha256(p) != item["sha256"]:
            raise RuntimeError(f"raw source SHA mismatch: {role}")
        if not m.is_file() or sha256(m) != item["manifest_sha256"]:
            raise RuntimeError(f"fetch manifest SHA mismatch: {role}")
        manifest = yaml.safe_load(m.read_text())
        entries = [e for e in manifest.get("entries", [])
                   if e.get("publisher") == item["publisher"]
                   and e.get("series_id") == item["series_id"]
                   and e.get("parquet_path") == item["path"]
                   and e.get("sha256") == item["sha256"]]
        if len(entries) != 1:
            raise RuntimeError(f"fetch manifest source entry mismatch: {role}")


def blank_status(x: Any) -> bool:
    return pd.isna(x) or str(x).strip() == ""


def source_keys() -> dict[str, list[tuple[str, int]]]:
    """Read only exposure values and outcome keys/dimensions, never outcome values/status."""
    cit = pd.read_parquet(ROOT / SOURCES["cit"]["path"], columns=["country_iso3", "year", "value"])
    if len(cit) != 3640 or cit.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("OECD CIT key contract changed")
    citval = {(str(c), int(y)): float(v) for c, y, v in cit.itertuples(index=False, name=None)
              if pd.notna(v) and np.isfinite(v) and 0 <= float(v) <= 100}
    priv = pd.read_parquet(ROOT / SOURCES["private"]["path"], columns=["country_iso3", "year"])
    priv = priv.loc[priv.country_iso3.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
    if priv.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("WDI private-investment key contract changed")
    pkeys = {(str(c), int(y)) for c, y in priv.itertuples(index=False, name=None)}
    tax = sorted(((c, y) for c, y in citval if 2001 <= y <= 2020
                  and (c, y-1) in citval and (c, y) in pkeys and (c, y+2) in pkeys),
                 key=lambda z: (z[1], z[0]))
    epl = pd.read_parquet(ROOT / SOURCES["epl"]["path"], columns=["country", "year", "indicator", "value"])
    if (len(epl) != 1355 or not epl.indicator.eq("EPR_V1").all()
            or epl.duplicated(["country", "year"]).any()
            or set(epl.country) != set(EPL_ISO3)):
        raise RuntimeError("OECD EPL dimension/key contract changed")
    eplval = {(EPL_ISO3[str(n)], int(y)): float(v) for n, y, _, v in epl.itertuples(index=False, name=None)
              if pd.notna(v) and np.isfinite(v) and 0 <= float(v) <= 6}
    gdp = pd.read_parquet(ROOT / SOURCES["gdp"]["path"],
                          columns=["country_iso3", "year", "value", "obs_status"])
    gdp = gdp.loc[gdp.country_iso3.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
    if gdp.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("WDI recession-exposure key contract changed")
    growth = {(str(c), int(y)): float(v) for c, y, v, status in gdp.itertuples(index=False, name=None)
              if pd.notna(v) and np.isfinite(v) and blank_status(status)}
    employment = pd.read_parquet(ROOT / SOURCES["employment"]["path"], columns=[
        "REF_AREA", "MEASURE", "UNIT_MEASURE", "SEX", "AGE", "LABOUR_FORCE_STATUS", "period"])
    selected = employment.loc[(employment.MEASURE == "EMP_RATIO")
                              & (employment.UNIT_MEASURE == "PT_POP_SUB")
                              & (employment.SEX == "_T")
                              & (employment.AGE == "Y20T64")
                              & (employment.LABOUR_FORCE_STATUS == "EMP")]
    if selected.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("OECD employment selected key contract changed")
    ekeys = {(str(c), int(y)) for c, y in selected[["REF_AREA", "period"]].itertuples(index=False, name=None)}
    recession: list[tuple[str, int]] = []
    for c in sorted({c for c, _ in growth}):
        negative = sorted((y, g) for (cc, y), g in growth.items()
                          if cc == c and 2000 <= y <= 2022 and g < 0)
        spells: list[list[tuple[int, float]]] = []
        group: list[tuple[int, float]] = []
        for y, g in negative:
            if group and y > group[-1][0] + 1:
                spells.append(group)
                group = []
            group.append((y, g))
        if group:
            spells.append(group)
        candidates: list[tuple[int, float]] = []
        for spell in spells:
            y, g = min(spell, key=lambda z: (z[1], z[0]))
            if (c, y-1) in eplval and (c, y) in ekeys and (c, y+2) in ekeys:
                candidates.append((y, g))
        kept: list[tuple[int, float]] = []
        for y, g in candidates:
            if kept and y - kept[-1][0] < 3:
                if (g, y) < (kept[-1][1], kept[-1][0]):
                    kept[-1] = (y, g)
            else:
                kept.append((y, g))
        recession += [(c, y) for y, _ in kept]
    recession.sort(key=lambda z: (z[1], z[0]))
    if len(tax) != 2810 or len(recession) != 89:
        raise RuntimeError(f"key-only envelope changed: tax={len(tax)}, epl={len(recession)}")
    return {"tax": tax, "epl": recession}


def roster_bytes(rows: dict[str, list[tuple[str, int]]]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["case_id", "country_iso3", "year"])
    for key in CASE:
        for c, y in rows[key]:
            writer.writerow([key, c, y])
    return out.getvalue().encode()


def key_preflight() -> dict[str, Any]:
    check_sources()
    rows = source_keys()
    actual = roster_bytes(rows)
    p = ROOT / ROSTER
    if not p.is_file() or p.read_bytes() != actual or sha256(p) != ROSTER_SHA:
        raise RuntimeError("frozen key-only roster mismatch")
    return {key: {"roster_rows": len(v), "roster_countries": len({c for c, _ in v}),
                  "roster_years": [min(y for _, y in v), max(y for _, y in v)],
                  "outcome_values_or_status_read": False} for key, v in rows.items()}


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER, TESTS]
    for key in CASE:
        frozen += [spec_rel(key), steelman_rel(key)]
    revs = {first_addition(x) for x in frozen}
    if len(revs) != 1:
        raise RuntimeError("registration files must share first-addition commit")
    rev = revs.pop()
    for x in frozen:
        committed_unchanged(x, rev)
    for key in CASE:
        spec = yaml.safe_load((ROOT / spec_rel(key)).read_text())
        if (spec["hypothesis_id"] != CASE[key]["id"] or spec["status"] != "pre_registered"
                or spec["steelman"] != steelman_rel(key)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec["falsification"]["threshold"] != threshold(key)):
            raise RuntimeError(f"registered spec mismatch: {key}")
        if git_output("ls-tree", "-r", "--name-only", rev, "--", run_rel(key)).strip():
            raise RuntimeError("measured run present in registration commit")
    return rev


def lock_payload(rev: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": rev,
            "source_files": SOURCES, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "blind_preflight": preflight, "correction": CORRECTION,
            "locked_utc": datetime.now(timezone.utc).isoformat()}


def source_lock_commit() -> tuple[str, dict[str, Any]]:
    rev = first_addition(LOCK)
    committed_unchanged(LOCK, rev)
    payload = json.loads((ROOT / LOCK).read_text())
    if (payload.get("family_id") != FAMILY
            or payload.get("preregistration_commit") != registration_commit()
            or payload.get("source_files") != SOURCES
            or payload.get("key_roster") != {"path": ROSTER, "sha256": ROSTER_SHA}
            or payload.get("blind_preflight") != key_preflight()
            or payload.get("correction") != CORRECTION):
        raise RuntimeError("source lock changed or does not match frozen registration")
    prereg_rev = payload["preregistration_commit"]
    if rev == prereg_rev:
        raise RuntimeError("source lock must be in a distinct later commit")
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", prereg_rev, rev],
                              cwd=ROOT, check=False, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    if ancestry.returncode != 0:
        raise RuntimeError("source-lock commit must descend from the preregistration commit")
    for key in CASE:
        if git_output("ls-tree", "-r", "--name-only", rev, "--", run_rel(key)).strip():
            raise RuntimeError("measured run present in source-lock commit")
    return rev, payload


def analysis_frame(key: str, roster: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    if key == "tax":
        cit = pd.read_parquet(ROOT / SOURCES["cit"]["path"], columns=["country_iso3", "year", "value"])
        c = {(str(country), int(y)): float(v) for country, y, v in cit.itertuples(index=False, name=None)
             if pd.notna(v) and np.isfinite(v) and 0 <= float(v) <= 100}
        private = pd.read_parquet(ROOT / SOURCES["private"]["path"],
                                  columns=["country_iso3", "year", "value", "obs_status"])
        private = private.loc[private.country_iso3.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
        if private.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError("duplicate private-investment country-year")
        y = {(str(country), int(year)): (v, status) for country, year, v, status
             in private.itertuples(index=False, name=None)}
        rows = []
        invalid = status_fail = 0
        for country, year in roster:
            d = c[(country, year)] - c[(country, year-1)]
            a, sa = y[(country, year)]
            b, sb = y[(country, year+2)]
            if not blank_status(sa) or not blank_status(sb):
                status_fail += 1
                continue
            if not all(pd.notna(x) and np.isfinite(x) and 0 <= float(x) <= 100 for x in [a, b]):
                invalid += 1
                continue
            rows.append({"country_iso3": country, "year": year, "outcome": float(b)-float(a),
                         "baseline": float(a), "cut": int(d <= -1), "hike": int(d >= 1),
                         "stable": int(abs(d) < 1), "tax_delta": d})
        frame = pd.DataFrame(rows, columns=["country_iso3", "year", "outcome", "baseline", "cut", "hike", "stable", "tax_delta"])
        if not frame.empty:
            counts = frame.country_iso3.value_counts()
            frame = frame.loc[frame.country_iso3.map(counts).ge(CASE[key]["floor"]["min_years_per_country"])].copy()
        frame = frame.sort_values(["year", "country_iso3"]).reset_index(drop=True)
        return frame, {"roster_rows": len(roster), "invalid_or_missing_outcome_pairs": invalid,
                       "nonblank_outcome_status_pairs": status_fail,
                       "after_min_years_country_floor": len(frame)}
    epl = pd.read_parquet(ROOT / SOURCES["epl"]["path"], columns=["country", "year", "value"])
    e = {(EPL_ISO3[str(n)], int(y)): float(v) for n, y, v in epl.itertuples(index=False, name=None)
         if pd.notna(v) and np.isfinite(v) and 0 <= float(v) <= 6}
    growth = pd.read_parquet(ROOT / SOURCES["gdp"]["path"],
                             columns=["country_iso3", "year", "value", "obs_status"])
    g = {(str(c), int(y)): float(v) for c, y, v, s in growth.itertuples(index=False, name=None)
         if pd.notna(v) and np.isfinite(v) and blank_status(s)}
    employment = pd.read_parquet(ROOT / SOURCES["employment"]["path"], columns=[
        "REF_AREA", "MEASURE", "UNIT_MEASURE", "SEX", "AGE", "LABOUR_FORCE_STATUS",
        "period", "value", "OBS_STATUS"])
    employment = employment.loc[(employment.MEASURE == "EMP_RATIO")
                                & (employment.UNIT_MEASURE == "PT_POP_SUB")
                                & (employment.SEX == "_T") & (employment.AGE == "Y20T64")
                                & (employment.LABOUR_FORCE_STATUS == "EMP")]
    if employment.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate selected employment country-year")
    y = {(str(c), int(year)): (v, status) for c, year, v, status
         in employment[["REF_AREA", "period", "value", "OBS_STATUS"]].itertuples(index=False, name=None)}
    rows = []
    invalid = status_fail = 0
    for country, year in roster:
        a, sa = y[(country, year)]
        b, sb = y[(country, year+2)]
        if str(sa).strip() != "A" or str(sb).strip() != "A":
            status_fail += 1
            continue
        if not all(pd.notna(x) and np.isfinite(x) and 0 <= float(x) <= 100 for x in [a, b]):
            invalid += 1
            continue
        rows.append({"country_iso3": country, "year": year,
                     "outcome": float(b)-float(a), "baseline": float(a),
                     "epl": e[(country, year-1)], "gdp_shock": g[(country, year)]})
    frame = pd.DataFrame(rows, columns=["country_iso3", "year", "outcome", "baseline", "epl", "gdp_shock"])
    frame = frame.sort_values(["year", "country_iso3"]).reset_index(drop=True)
    return frame, {"roster_rows": len(roster), "invalid_or_missing_outcome_pairs": invalid,
                   "non_actual_outcome_status_pairs": status_fail}


def pre_estimation_gate(key: str, frame: pd.DataFrame) -> dict[str, bool]:
    """Check complete-case and exposure floors before fitting any estimator."""
    floor = CASE[key]["floor"]
    if frame.empty:
        names = ("min_valid_rows", "min_valid_countries")
        names += (("min_cut_rows", "min_cut_countries", "min_stable_rows", "min_years_per_country")
                  if key == "tax" else
                  ("min_countries_with_two_nonoverlapping_events", "min_2009_events",
                   "min_2020_events", "min_distinct_event_years",
                   "max_one_event_year_share", "min_epl_interquartile_gap"))
        return {name: False for name in names}
    countries = frame.country_iso3.nunique()
    checks = {"min_valid_rows": len(frame) >= floor["min_valid_rows"],
              "min_valid_countries": countries >= floor["min_valid_countries"]}
    if key == "tax":
        checks.update({
            "min_cut_rows": int(frame.cut.sum()) >= floor["min_cut_rows"],
            "min_cut_countries": frame.loc[frame.cut.eq(1), "country_iso3"].nunique() >= floor["min_cut_countries"],
            "min_stable_rows": int(frame.stable.sum()) >= floor["min_stable_rows"],
            "min_years_per_country": int(frame.country_iso3.value_counts().min()) >= floor["min_years_per_country"],
        })
    else:
        cnt = frame.country_iso3.value_counts()
        checks.update({
            "min_countries_with_two_nonoverlapping_events": int((cnt >= 2).sum()) >= floor["min_countries_with_two_nonoverlapping_events"],
            "min_2009_events": int(frame.year.eq(2009).sum()) >= floor["min_2009_events"],
            "min_2020_events": int(frame.year.eq(2020).sum()) >= floor["min_2020_events"],
            "min_distinct_event_years": frame.year.nunique() >= floor["min_distinct_event_years"],
            "max_one_event_year_share": float(frame.year.value_counts(normalize=True).max()) <= floor["max_one_event_year_share"],
            "min_epl_interquartile_gap": float(frame.epl.quantile(.75)-frame.epl.quantile(.25)) >= floor["min_epl_interquartile_gap"],
        })
    return checks


def sample_gate(key: str, frame: pd.DataFrame, sample: dict[str, Any]) -> dict[str, bool]:
    checks = pre_estimation_gate(key, frame)
    floor = CASE[key]["floor"]
    for name in ("max_top_one_percent_partialled_x_share", "max_top_country_partialled_x_share"):
        checks[name] = (sample.get(name) is not None and sample[name] <= floor[name])
    return checks


def residual_concentration(model: Any, term: str, countries: pd.Series) -> dict[str, float | None]:
    names = model.model.exog_names
    idx = names.index(term)
    X = np.asarray(model.model.exog, dtype=float)
    x = X[:, idx]
    Z = np.delete(X, idx, axis=1)
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    weight = rx * rx
    total = float(weight.sum())
    if total <= 1e-12:
        return {"max_top_one_percent_partialled_x_share": None,
                "max_top_country_partialled_x_share": None}
    n_top = max(1, math.ceil(len(weight) * .01))
    by_country = pd.DataFrame({"country": countries.to_numpy(), "w": weight}).groupby("country").w.sum()
    return {"max_top_one_percent_partialled_x_share": float(np.sort(weight)[-n_top:].sum()/total),
            "max_top_country_partialled_x_share": float(by_country.max()/total)}


def estimate(key: str, frame: pd.DataFrame) -> tuple[dict[str, Any] | None, dict[str, float | None]]:
    if frame.empty:
        return None, {"max_top_one_percent_partialled_x_share": None,
                      "max_top_country_partialled_x_share": None}
    formula = ("outcome ~ cut + hike + baseline + C(country_iso3) + C(year)" if key == "tax"
               else "outcome ~ epl + baseline + gdp_shock + C(year)")
    model = smf.ols(formula, data=frame).fit()
    X = model.model.exog
    if np.linalg.matrix_rank(X) != X.shape[1]:
        return None, {"max_top_one_percent_partialled_x_share": None,
                      "max_top_country_partialled_x_share": None}
    countries = frame.country_iso3
    clustered = model.get_robustcov_results(cov_type="cluster", groups=countries,
                                             use_correction=True, df_correction=True,
                                             use_t=True)
    term = CASE[key]["beta_term"]
    ix = model.model.exog_names.index(term)
    beta = float(clustered.params[ix])
    se = float(clustered.bse[ix])
    groups = int(countries.nunique())
    df = groups - 1
    if not np.isfinite(beta) or not np.isfinite(se) or se <= 0 or groups < 2:
        return None, {"max_top_one_percent_partialled_x_share": None,
                      "max_top_country_partialled_x_share": None}
    p = float(2 * student_t.sf(abs(beta/se), df))
    ci = float(student_t.ppf(1-P_MAX/2, df)*se)
    return ({"coefficient": beta, "std_error": se, "p_value_two_sided": p,
            "confidence_level": 1-P_MAX, "confidence_interval": [beta-ci, beta+ci],
            "n_rows": int(len(frame)), "n_countries": groups, "df_inference": df,
            "model_rank": int(np.linalg.matrix_rank(X)),
            "method": "OLS; country-cluster CR1; Student t(G-1); fixed effects as registered"},
            residual_concentration(model, term, countries))


def classify_verdict(key: str, primary: dict[str, Any] | None, gates: dict[str, bool]) -> tuple[str, str]:
    if not all(gates.values()) or primary is None:
        return "INCONCLUSIVE", "frozen coverage, identification, influence, or estimator floor failed"
    beta = primary["coefficient"]
    p = primary["p_value_two_sided"]
    min_effect = CASE[key]["meaningful_beta"]
    expected = 1 if CASE[key]["expected_sign"] == "+" else -1
    if p <= P_MAX and expected*beta >= min_effect:
        return "SUPPORTED", "direction, familywise p, and practical-effect gates passed"
    if p <= P_MAX and expected*beta <= -min_effect:
        return "REFUTED", "opposite direction, familywise p, and practical-effect gates passed"
    return "PARTIAL", "estimable association did not clear a frozen directional gate"


def outcome(key: str, roster: list[tuple[str, int]], rev: str, lock_rev: str, run_utc: str) -> dict[str, Any]:
    frame, count = analysis_frame(key, roster)
    before_fit = pre_estimation_gate(key, frame)
    estimator_attempted = all(before_fit.values())
    if estimator_attempted:
        primary, concentration = estimate(key, frame)
    else:
        primary = None
        concentration = {"max_top_one_percent_partialled_x_share": None,
                         "max_top_country_partialled_x_share": None}
    sample = {**count, "valid_rows": len(frame),
              "estimator_attempted": estimator_attempted,
              "valid_countries": int(frame.country_iso3.nunique()) if not frame.empty else 0,
              "outcome_values_read_after_lock": True, **concentration}
    if not frame.empty:
        if key == "tax":
            sample.update({"cut_rows": int(frame.cut.sum()),
                           "cut_countries": int(frame.loc[frame.cut.eq(1), "country_iso3"].nunique()),
                           "stable_rows": int(frame.stable.sum()),
                           "hike_rows": int(frame.hike.sum())})
        else:
            cnt = frame.country_iso3.value_counts()
            sample.update({"countries_with_two_nonoverlapping_events": int((cnt >= 2).sum()),
                           "events_2009": int(frame.year.eq(2009).sum()),
                           "events_2020": int(frame.year.eq(2020).sum()),
                           "distinct_event_years": int(frame.year.nunique()),
                           "largest_event_year_share": float(frame.year.value_counts(normalize=True).max()),
                           "epl_interquartile_gap": float(frame.epl.quantile(.75)-frame.epl.quantile(.25))})
    gates = sample_gate(key, frame, sample)
    gates["full_rank_and_estimable_uncertainty"] = primary is not None
    verdict, reason = classify_verdict(key, primary, gates)
    return {"hypothesis_id": CASE[key]["id"], "replaces_placeholder_for": CASE[key]["old_id"],
            "family_id": FAMILY, "verdict": verdict, "verdict_label": verdict,
            "verdict_reason": reason, "run_utc": run_utc, "runner": RUNNER,
            "preregistration_commit": rev, "source_lock_commit": lock_rev,
            "source_lock": LOCK, "template": "panel_fe" if key == "tax" else "descriptive",
            "sample": sample, "gate_checks": gates, "primary": primary,
            "p_max_two_sided_bonferroni": P_MAX,
            "meaningful_beta_min_abs": CASE[key]["meaningful_beta"],
            "data_status": {"variables_missing": [], "input_vintages": [SOURCES[k] for k in
                            (["cit", "private"] if key == "tax" else ["epl", "gdp", "employment"])]},
            "limitations": LIMITATIONS[key] + [
                "Bonferroni correction covers these two prospectively registered calibrations only, not the historical IESET research search.",
                "The archived Fraser/GDP-per-capita placeholder remains archived; no score or causal credit is transferred."],
            "correction": CORRECTION}


def artifact_bytes(key: str, result: dict[str, Any]) -> dict[str, bytes]:
    case = CASE[key]
    spec = (ROOT / spec_rel(key)).read_bytes()
    stamp = result["run_utc"]
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": case["id"], "path": spec_rel(key), "topic": case["topic"]},
              "preregistration": {"spec_commit": result["preregistration_commit"],
                                  "source_lock_commit": result["source_lock_commit"],
                                  "family_id": FAMILY, "family_size": 2,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": steelman_rel(key)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(key),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                          "reason": result["verdict_reason"]},
              "data": {"inputs": {k: SOURCES[k] for k in
                      (["cit", "private"] if key == "tax" else ["epl", "gdp", "employment"])},
                       "sample": result["sample"]},
              "results": {"primary": result["primary"], "gate_checks": result["gate_checks"]},
              "limitations": result["limitations"], "correction": CORRECTION}
    card = (f"# {case['id']}\n\n**Verdict: {result['verdict']}** — {result['verdict_reason']}.\n\n"
            f"This is a descriptive calibration of one measurable component of archived "
            f"`{case['old_id']}`. The old placeholder is still archived.\n\n"
            f"Valid rows: {result['sample']['valid_rows']}; countries: {result['sample']['valid_countries']}.\n")
    if result["primary"]:
        p = result["primary"]
        card += (f"Primary coefficient: {p['coefficient']:+.6g}; country-cluster SE "
                 f"{p['std_error']:.6g}; two-sided p {p['p_value_two_sided']:.6g}; "
                 f"{100*(1-P_MAX):.1f}% family-adjusted interval "
                 f"[{p['confidence_interval'][0]:+.6g}, {p['confidence_interval'][1]:+.6g}].\n")
    card += ("\nNo causal, school, policy, or featured credit is assigned. "
             "See diagnostics and the frozen registration for coverage and limitations.\n")
    manifest = {"schema": "ieset-run-manifest-v1", "generated_utc": stamp,
                "hypothesis_id": case["id"], "runner": RUNNER,
                "preregistration_commit": result["preregistration_commit"],
                "source_lock_commit": result["source_lock_commit"],
                "inputs": packet["data"]["inputs"], "correction": CORRECTION}
    metrics = pd.DataFrame([{"hypothesis_id": case["id"], "verdict": result["verdict"],
                             "coefficient": None if result["primary"] is None else result["primary"]["coefficient"],
                             "std_error": None if result["primary"] is None else result["primary"]["std_error"],
                             "p_value": None if result["primary"] is None else result["primary"]["p_value_two_sided"],
                             "n_rows": result["sample"]["valid_rows"],
                             "n_countries": result["sample"]["valid_countries"]}])
    pq = io.BytesIO()
    metrics.to_parquet(pq, index=False)
    copy = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\n"
            f"root = Path(__file__).resolve().parents[3]\n"
            f"subprocess.run(['python3', '{RUNNER}', '--verify'], cwd=root, check=True)\n")
    return {"diagnostics.json": (json.dumps(result, indent=2, sort_keys=True)+"\n").encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "result_card.md": card.encode(), "hypothesis.yaml": spec,
            "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "replication.py": copy.encode(), "coefficients.parquet": pq.getvalue(),
            "chart_data.json": (json.dumps({"hypothesis_id": case["id"],
                                             "primary": result["primary"],
                                             "verdict": result["verdict"]}, sort_keys=True, indent=2)+"\n").encode()}


def summary_bytes(results: dict[str, dict[str, Any]]) -> bytes:
    lines = ["# Claim-specific placeholder replacement results — 2026-10-10", "",
             "Two prospectively registered descriptive tests with a local Bonferroni threshold p ≤ .005.",
             "The original 131-record Fraser/GDP-per-capita placeholder group remains archived.", ""]
    for key in CASE:
        r = results[key]
        lines += [f"- `{r['hypothesis_id']}`: **{r['verdict']}**; {r['sample']['valid_rows']} rows, "
                  f"{r['sample']['valid_countries']} countries; {r['verdict_reason']}."]
    lines += ["", "Neither result conveys causal, school, policy, or featured credit.", ""]
    return "\n".join(lines).encode()


def run_or_verify(verify: bool) -> None:
    lock_rev, lock = source_lock_commit()
    rev = lock["preregistration_commit"]
    rosters = source_keys()
    if roster_bytes(rosters) != (ROOT / ROSTER).read_bytes():
        raise RuntimeError("source keys differ from registered roster")
    if verify:
        if not all((ROOT / run_rel(k) / "diagnostics.json").is_file() for k in CASE):
            raise RuntimeError("missing measured run for verification")
        stamp = json.loads((ROOT / run_rel("tax") / "diagnostics.json").read_text())["run_utc"]
    else:
        if any((ROOT / run_rel(k)).exists() for k in CASE) or (ROOT / SUMMARY).exists():
            raise RuntimeError("measured run already exists; refusing overwrite")
        stamp = datetime.now(timezone.utc).isoformat()
    results = {key: outcome(key, rosters[key], rev, lock_rev, stamp) for key in CASE}
    for key in CASE:
        expected = artifact_bytes(key, results[key])
        dest = ROOT / run_rel(key)
        if verify:
            observed = {p.name for p in dest.iterdir() if p.is_file()}
            if observed != set(expected):
                raise RuntimeError(f"run artifact set mismatch: {key}")
            for name, raw in expected.items():
                if (dest / name).read_bytes() != raw:
                    raise RuntimeError(f"exact replay mismatch: {key}/{name}")
        else:
            dest.mkdir(parents=True)
            for name, raw in expected.items():
                (dest / name).write_bytes(raw)
    summary = summary_bytes(results)
    if verify:
        if (ROOT / SUMMARY).read_bytes() != summary:
            raise RuntimeError("exact replay mismatch: result summary")
        print("Exact replay passed: two run directories, sixteen artifacts, one summary")
    else:
        (ROOT / SUMMARY).write_bytes(summary)
        print(json.dumps({k: {"verdict": v["verdict"], "sample": v["sample"],
                              "primary": v["primary"]} for k, v in results.items()}, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    for flag in ("build-roster", "preflight", "lock", "run", "verify"):
        group.add_argument("--"+flag, action="store_true")
    args = p.parse_args()
    if args.build_roster:
        check_sources()
        rows = source_keys()
        pth = ROOT / ROSTER
        pth.parent.mkdir(parents=True, exist_ok=True)
        pth.write_bytes(roster_bytes(rows))
        print(json.dumps({"roster_sha256": sha256(pth),
                          "cases": {k: {"rows": len(v), "countries": len({c for c, _ in v})}
                                    for k, v in rows.items()}}, indent=2))
    elif args.preflight:
        print(json.dumps(key_preflight(), indent=2))
    elif args.lock:
        rev = registration_commit()
        preflight = key_preflight()
        pth = ROOT / LOCK
        if pth.exists():
            raise RuntimeError("source lock already exists")
        pth.write_text(json.dumps(lock_payload(rev, preflight), sort_keys=True, indent=2)+"\n")
        print(f"Source lock written after preregistration commit {rev}")
    elif args.run:
        run_or_verify(False)
    elif args.verify:
        run_or_verify(True)


if __name__ == "__main__":
    main()
