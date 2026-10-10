#!/usr/bin/env python3
"""Frozen BIS nominal-depreciation to HICP consumer-group inflation descriptive family.

Blind preflight reads BIS nominal EER values and selected Eurostat COICOP/country/
year keys only. HICP values and nulls first open after separate registration and
source-lock commits. One omnibus claim has 20 fixed component estimates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "bis_neer_eurostat_goods_hicp_2026_10_10"
RUNNER = "scripts/run_bis_neer_eurostat_goods_hicp_2026.py"
PREREG = "engine/audits/bis_neer_eurostat_goods_hicp_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/bis_neer_eurostat_goods_hicp_2026_key_roster.csv"
ROSTER_SHA = "9548cf5bedc596a978c471ef3b1d69c6338b4a2caffe255507def0ed26e8faa6"
LOCK = "data/pinned_evidence/bis_neer_eurostat_goods_hicp_2026.manifest.json"
SUMMARY = "engine/audits/bis_neer_eurostat_goods_hicp_results_2026-10-10.md"
HYPOTHESIS_ID = "bis_neer_hicp_multicategory_pass_through_2026"
SPEC = f"hypotheses/monetary/{HYPOTHESIS_ID}.yaml"
STEELMAN = f"hypotheses/steelman/{HYPOTHESIS_ID}.md"
RUN_DIR = f"engine/runs/{HYPOTHESIS_ID}"
SOURCES = {
    "neer": {"publisher": "bis", "series_id": "WS_EER",
        "path": "data/vintages/bis/WS_EER@2026-07-23T151604Z.parquet",
        "sha256": "57bbce3e22fc428c8cd8ddee8a998d273b5240a816af89e532b81d41ade35170",
        "manifest": "data/manifests/fetch_run_2026-07-23T151632Z.yaml",
        "manifest_sha256": "1768f0d7c38c93f1ad4df591b0b1634b3460faa964f6267874b8798b7b8dbb81"},
    "hicp": {"publisher": "eurostat", "series_id": "prc_hicp_aind",
        "path": "data/vintages/eurostat/prc_hicp_aind@2026-04-30T115920Z.parquet",
        "sha256": "be97a646f95e04c481c583bcde08817aaf6fc315cb7b5f1b628c735cf6a2aec4",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
}
GEO_TO_BIS = {
    "AT":"AT","BE":"BE","BG":"BG","CY":"CY","CZ":"CZ","DE":"DE","DK":"DK",
    "EE":"EE","EL":"GR","ES":"ES","FI":"FI","FR":"FR","HR":"HR","HU":"HU",
    "IE":"IE","IS":"IS","IT":"IT","LT":"LT","LU":"LU","LV":"LV","MT":"MT",
    "NL":"NL","NO":"NO","PL":"PL","PT":"PT","RO":"RO","SE":"SE","SI":"SI","SK":"SK",
}
GEO_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","CY":"CYP","CZ":"CZE","DE":"DEU",
    "DK":"DNK","EE":"EST","EL":"GRC","ES":"ESP","FI":"FIN","FR":"FRA",
    "HR":"HRV","HU":"HUN","IE":"IRL","IS":"ISL","IT":"ITA","LT":"LTU",
    "LU":"LUX","LV":"LVA","MT":"MLT","NL":"NLD","NO":"NOR","PL":"POL",
    "PT":"PRT","RO":"ROU","SE":"SWE","SI":"SVN","SK":"SVK",
}
# Every selected ECOICOP group is a different three-digit sibling. No parent
# category or special aggregate enters this fixed family.
CASES = {
    "CP011": {"slug":"food", "label":"food", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP012": {"slug":"nonalcoholic_beverages", "label":"non-alcoholic beverages", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP021": {"slug":"alcoholic_beverages", "label":"alcoholic beverages", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP022": {"slug":"tobacco", "label":"tobacco", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP031": {"slug":"clothing", "label":"clothing", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP032": {"slug":"footwear", "label":"footwear", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP045": {"slug":"household_energy", "label":"electricity, gas and other fuels", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP051": {"slug":"furniture", "label":"furniture and furnishings, carpets and other floor coverings", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP052": {"slug":"household_textiles", "label":"household textiles", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP053": {"slug":"household_appliances", "label":"household appliances", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP054": {"slug":"tableware_utensils", "label":"glassware, tableware and household utensils", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP055": {"slug":"home_garden_tools", "label":"tools and equipment for house and garden", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP061": {"slug":"medical_products", "label":"medical products, appliances and equipment", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP071": {"slug":"vehicle_purchases", "label":"purchase of vehicles", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP072": {"slug":"vehicle_operation", "label":"operation of personal transport equipment", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP091": {"slug":"audiovisual_equipment", "label":"audio-visual, photographic and information processing equipment", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP092": {"slug":"recreation_durables", "label":"other major durables for recreation and culture", "key_rows":450, "key_countries":27, "material_rows":193, "material_countries":27},
    "CP093": {"slug":"recreation_goods", "label":"other recreational items and equipment, gardens and pets", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP095": {"slug":"books_stationery", "label":"newspapers, books and stationery", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
    "CP123": {"slug":"personal_effects", "label":"personal effects n.e.c.", "key_rows":489, "key_countries":29, "material_rows":206, "material_countries":29},
}
FIRST_T, LAST_T, MIN_YEARS = 2002, 2018, 10
MAX_ABS_DEPRECIATION, MATERIAL_DEPRECIATION = 15.0, 2.0
MIN_VALID_ROWS, MIN_VALID_COUNTRIES = 400, 24
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 150, 22
MAX_TOP_ONE_PERCENT, MAX_TOP_COUNTRY = 0.30, 0.25
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_ABS_BETA, MIN_LOO_BETA = 0.04, 0.02
MIN_ESTIMABLE_CATEGORIES, MIN_DIRECTIONAL_CATEGORIES = 16, 5
CORRECTION = {"disposition":"descriptive_calibration_only", "family_id":FAMILY,
    "family_size":len(CASES), "family_alpha":FAMILY_ALPHA,
    "bonferroni_p_max":P_MAX, "public_hypothesis_count":1,
    "component_estimates":len(CASES), "causal_credit":0,
    "policy_score_eligible":False, "policy_score_credit":0,
    "school_score_eligible":False, "school_score_credit":0, "featured_eligible":False}
LIMITATIONS = [
    "BIS broad nominal effective exchange rates use manufacturing-trade weights; the selected HICP baskets have different import shares and some include regulated or locally supplied items.",
    "Euro-area members share a currency, so national BIS EER changes are correlated despite different trade weights. Country and year fixed effects and two-way clustering do not identify an exchange-rate shock.",
    "Some selected groups include locally delivered services and regulated prices; they are distinct spending groups, not pure imported-goods baskets.",
    "The pinned Eurostat annual HICP Parquet retains no cell flags. Finite values are used without claiming break screening, method continuity, or independent price collection.",
    "Eurostat annual-average HICP change compares average monthly indices in year t+1 with the prior year's average; it is not December-to-December inflation.",
    "A one-year lag establishes ordering, not causality. Import costs, energy and food commodity prices, excise taxes, domestic demand, monetary response, and pricing-to-market can confound the relation.",
    "The 20 COICOP groups do not nest each other, but their prices share shocks and source methodology. Bonferroni correction is local to this fixed family; archive-wide selection is not corrected.",
    "No causal, policy, school-score, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel() -> str:
    return SPEC


def steelman_rel() -> str:
    return STEELMAN


def run_rel() -> str:
    return RUN_DIR


def threshold() -> dict[str,Any]:
    return {"family_id":FAMILY,"family_size":len(CASES),"family_alpha":FAMILY_ALPHA,
        "public_hypothesis_count":1,"component_estimates":len(CASES),
        "p_max_two_sided_bonferroni":P_MAX,"expected_beta_sign":"+",
        "meaningful_beta_min_abs":MIN_ABS_BETA,"min_loo_beta_abs":MIN_LOO_BETA,
        "min_estimable_categories":MIN_ESTIMABLE_CATEGORIES,
        "min_directional_categories":MIN_DIRECTIONAL_CATEGORIES,
        "min_valid_rows_per_category":MIN_VALID_ROWS,
        "min_valid_countries_per_category":MIN_VALID_COUNTRIES,
        "min_material_change_rows_per_category":MIN_MATERIAL_ROWS,
        "min_material_change_countries_per_category":MIN_MATERIAL_COUNTRIES,
        "material_depreciation_min_abs":MATERIAL_DEPRECIATION,
        "max_abs_depreciation":MAX_ABS_DEPRECIATION,
        "min_complete_years_per_country":MIN_YEARS,
        "max_top_one_percent_residual_x_share":MAX_TOP_ONE_PERCENT,
        "max_top_country_residual_x_share":MAX_TOP_COUNTRY,
        "selected_coicop":list(CASES),"selected_hicp_unit":"RCH_A_AVG",
        "expected_key_rows_by_code":{code:case["key_rows"] for code,case in CASES.items()},
        "expected_key_countries_by_code":{code:case["key_countries"] for code,case in CASES.items()},
        "expected_material_key_rows_by_code":{code:case["material_rows"] for code,case in CASES.items()},
        "roster_sha256":ROSTER_SHA,
        "source_files":{role:{field:source[field] for field in
            ("path","sha256","manifest","manifest_sha256")}
            for role,source in SOURCES.items()},
        "causal_credit":0,"policy_score_eligible":False,"policy_score_credit":0,
        "school_score_eligible":False,"school_score_credit":0,"featured_eligible":False}

def load_roster() -> dict[str, list[tuple[str, int]]]:
    path=ROOT/ROSTER
    raw=path.read_bytes()
    if sha256(path)!=ROSTER_SHA or not raw.startswith(b"coicop,geo_code,treatment_year\n"):
        raise RuntimeError("key-only roster header/hash mismatch")
    records=list(csv.DictReader(io.StringIO(raw.decode())))
    observed=[(row["coicop"],row["geo_code"],int(row["treatment_year"])) for row in records]
    if observed!=sorted(set(observed)) or len(observed)!=9741:
        raise RuntimeError("key-only roster order, uniqueness, or size changed")
    result={code:[] for code in CASES}
    for code,geo,year in observed:
        if code not in result or geo not in GEO_TO_BIS or not FIRST_T<=year<=LAST_T:
            raise RuntimeError("unexpected category, geography, or year")
        result[code].append((geo,year))
    for code,case in CASES.items():
        if len(result[code])!=case["key_rows"] or len({g for g,_ in result[code]})!=case["key_countries"]:
            raise RuntimeError(f"key-only envelope changed: {code}")
    return result


def validate_specs() -> None:
    roster=load_roster()
    if len(CASES)!=20 or len(set(case["slug"] for case in CASES.values()))!=20:
        raise RuntimeError("component family denominator or category identity changed")
    spec=yaml.safe_load((ROOT/SPEC).read_text())
    countries=sorted({GEO_TO_ISO3[geo] for rows in roster.values() for geo,_ in rows})
    if (spec.get("hypothesis_id")!=HYPOTHESIS_ID
            or spec.get("status")!="pre_registered"
            or spec.get("evidence_type")!="associational"
            or spec.get("claim_direction")!="+"
            or spec.get("steelman")!=STEELMAN
            or spec.get("covers_claims")!=[] or spec.get("linked_hypotheses")!=[]
            or spec.get("linked_conditions")!=[]
            or spec["sample"].get("countries")!=countries
            or spec["sample"].get("period")!=[FIRST_T,LAST_T+1]
            or spec["falsification"].get("threshold")!=threshold()):
        raise RuntimeError("frozen omnibus spec differs from runner and roster")


def registration_commit() -> str:
    files=[RUNNER,PREREG,ROSTER,SPEC,STEELMAN]
    revisions={first_addition(relative) for relative in files}
    if len(revisions)!=1:
        raise RuntimeError("five omnibus registration files lack one shared first-addition commit")
    revision=revisions.pop()
    for relative in files: committed_unchanged(relative,revision)
    if git("ls-tree","-r","--name-only",revision,"--",RUN_DIR).strip():
        raise RuntimeError("registration commit already contained measured result")
    validate_specs()
    return revision

def check_sources() -> dict[str, dict[str, Any]]:
    selected = {}
    for role, source in SOURCES.items():
        raw = ROOT / source["path"]
        manifest_path = ROOT / source["manifest"]
        if not raw.is_file() or sha256(raw) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned source: {role}")
        if not manifest_path.is_file() or sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest_path.read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("publisher") == source["publisher"]
            and entry.get("series_id") == source["series_id"]
            and entry.get("parquet_path") == source["path"]
            and entry.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest lacks exact source entry: {role}")
        selected[role] = {**source, "source_url": matches[0].get("source_url"),
            "methodology_url": matches[0].get("methodology_url"),
            "license": matches[0].get("license"), "fetch_utc": matches[0].get("fetch_utc")}
    return selected


def exposure() -> dict[tuple[str,int],float]:
    # BIS numeric treatment, including its missingness, may be screened blindly.
    cols=["FREQ","EER_TYPE","EER_BASKET","REF_AREA","period","value","OBS_STATUS"]
    raw=pd.read_parquet(ROOT/SOURCES["neer"]["path"],columns=cols)
    raw=raw.loc[raw.FREQ.eq("M") & raw.EER_TYPE.eq("N") & raw.EER_BASKET.eq("B")
        & raw.REF_AREA.isin(GEO_TO_BIS.values())].copy()
    raw["year"]=raw.period.str[:4].astype(int)
    raw=raw.loc[raw.year.between(FIRST_T-1,LAST_T)]
    if raw.duplicated(["REF_AREA","period"]).any():
        raise RuntimeError("duplicate exact BIS monthly nominal-broad EER key")
    raw["value"]=pd.to_numeric(raw.value,errors="coerce")
    raw=raw.loc[raw.OBS_STATUS.eq("A") & raw.value.notna() & raw.value.gt(0)]
    annual=raw.groupby(["REF_AREA","year"]).agg(months=("period","nunique"),
        mean=("value","mean"))
    annual=annual.loc[annual.months.eq(12)]["mean"].to_dict()
    result={}
    for geo,bis in GEO_TO_BIS.items():
        for year in range(FIRST_T,LAST_T+1):
            if (bis,year-1) not in annual or (bis,year) not in annual: continue
            value=100*math.log(float(annual[bis,year-1])/float(annual[bis,year]))
            if math.isfinite(value) and abs(value)<=MAX_ABS_DEPRECIATION:
                result[geo,year]=value
    return result


def outcome_keys() -> dict[str,set[tuple[str,int]]]:
    # Strictly categorical keys. HICP value/null column stays sealed.
    raw=pd.read_parquet(ROOT/SOURCES["hicp"]["path"],
        columns=["freq","unit","coicop","geo_code","period"])
    raw=raw.loc[raw.freq.eq("A") & raw.unit.eq("RCH_A_AVG")
        & raw.coicop.isin(CASES) & raw.geo_code.isin(GEO_TO_BIS)].copy()
    raw["year"]=pd.to_numeric(raw.period,errors="raise").astype(int)
    if raw.duplicated(["coicop","geo_code","year"]).any():
        raise RuntimeError("duplicate selected HICP category-country-year key")
    return {code:set(raw.loc[raw.coicop.eq(code),["geo_code","year"]]
        .itertuples(index=False,name=None)) for code in CASES}


def expected_roster() -> dict[str,list[tuple[str,int]]]:
    x=exposure(); keys=outcome_keys(); result={}
    for code in CASES:
        rows=[(geo,year) for geo,year in x if (geo,year+1) in keys[code]]
        counts=pd.Series([geo for geo,_ in rows]).value_counts()
        result[code]=sorted((geo,year) for geo,year in rows if counts[geo]>=MIN_YEARS)
    return result


def preflight() -> dict[str,Any]:
    roster=load_roster()
    if expected_roster()!=roster:
        raise RuntimeError("frozen roster differs from BIS exposure and HICP keys")
    x=exposure(); by_category={}
    for code,rows in roster.items():
        material=[(geo,year) for geo,year in rows if abs(x[geo,year])>=MATERIAL_DEPRECIATION]
        case=CASES[code]
        if len(material)!=case["material_rows"] or len({g for g,_ in material})!=case["material_countries"]:
            raise RuntimeError(f"material BIS envelope changed: {code}")
        by_category[code]={"key_rows":len(rows),"key_countries":len({g for g,_ in rows}),
            "material_exposure_rows":len(material),
            "material_exposure_countries":len({g for g,_ in material})}
    return {"family_size":len(CASES),"by_category":by_category,
        "outcome_values_opened":False,"outcome_null_masks_opened":False,
        "note":"HICP category/country/year keys are upper bounds; no selected HICP value or completeness mask was screened."}

def lock_payload(registration: str, selected: dict[str, dict[str, Any]],
                 blind: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
        "sources": selected, "key_only_preflight": blind,
        "statement": "Exact source pins were locked after preregistration and before selected Eurostat HICP values/nulls were opened."}


def write_source_lock() -> None:
    registration = registration_commit()
    selected = check_sources()
    blind = preflight()
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, selected, blind), indent=2, sort_keys=True) + "\n")


def check_source_lock(registration: str, selected: dict[str, dict[str, Any]],
                      blind: dict[str, Any]) -> str:
    revision = first_addition(LOCK)
    if revision == registration:
        raise RuntimeError("source lock was not committed separately")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT)
    committed_unchanged(LOCK, revision)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, selected, blind):
        raise RuntimeError("committed source lock differs from frozen pins")
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise RuntimeError("source-lock commit already contained measured result")
    return revision


def measured_hicp_values() -> dict[str,dict[tuple[str,int],float|None]]:
    # First selected HICP numeric/null access, only after both chronology commits.
    raw=pd.read_parquet(ROOT/SOURCES["hicp"]["path"],
        columns=["freq","unit","coicop","geo_code","period","value"])
    raw=raw.loc[raw.freq.eq("A") & raw.unit.eq("RCH_A_AVG")
        & raw.coicop.isin(CASES) & raw.geo_code.isin(GEO_TO_BIS)].copy()
    raw["year"]=pd.to_numeric(raw.period,errors="raise").astype(int)
    if raw.duplicated(["coicop","geo_code","year"]).any():
        raise RuntimeError("duplicate selected HICP outcome cell")
    raw["value"]=pd.to_numeric(raw.value,errors="coerce")
    result={}
    for code in CASES:
        selected=raw.loc[raw.coicop.eq(code),["geo_code","year","value"]]
        result[code]={(geo,int(year)):float(value) if pd.notna(value) else None
            for geo,year,value in selected.itertuples(index=False,name=None)}
    return result


def measured_panels(roster:dict[str,list[tuple[str,int]]]) -> dict[str,tuple[pd.DataFrame,dict[str,Any]]]:
    values=measured_hicp_values(); x=exposure(); result={}
    for code,rows in roster.items():
        panel_rows=[]; invalid=0
        for geo,year in rows:
            y=values[code].get((geo,year+1))
            if y is None or not math.isfinite(y):
                invalid+=1; continue
            panel_rows.append({"geo_code":geo,"year":year,"x":x[geo,year],"y":y})
        panel=pd.DataFrame(panel_rows,columns=["geo_code","year","x","y"])
        counts=panel.geo_code.value_counts()
        panel=panel.loc[panel.geo_code.map(counts).ge(MIN_YEARS)].copy()
        panel=panel.sort_values(["geo_code","year"]).reset_index(drop=True)
        material=panel.x.abs().ge(MATERIAL_DEPRECIATION)
        gate={"key_only_rows":len(rows),"missing_or_nonfinite_hicp_cells":invalid,
            "valid_rows":len(panel),"valid_countries":int(panel.geo_code.nunique()),
            "valid_years":int(panel.year.nunique()),
            "material_change_rows":int(material.sum()),
            "material_change_countries":int(panel.loc[material,"geo_code"].nunique()),
            "min_complete_years_per_country":MIN_YEARS,
            "outcome_values_read_after_lock":True,"source_cell_flags_available":False}
        result[code]=(panel,gate)
    return result


def estimate(panel:pd.DataFrame,gate:dict[str,Any]) -> dict[str,Any]:
    if (gate["valid_rows"]<MIN_VALID_ROWS or gate["valid_countries"]<MIN_VALID_COUNTRIES
            or gate["material_change_rows"]<MIN_MATERIAL_ROWS
            or gate["material_change_countries"]<MIN_MATERIAL_COUNTRIES):
        return {"verdict":"INCONCLUSIVE","reason":"frozen complete-case or material-depreciation floor failed",
            "gate":gate,"primary":None}
    residual_model=smf.ols("x ~ C(geo_code)+C(year)",data=panel)
    if np.linalg.matrix_rank(residual_model.exog)!=residual_model.exog.shape[1]:
        return {"verdict":"INCONCLUSIVE","reason":"residual exposure design lacks full rank",
            "gate":gate,"primary":None}
    residual_sq=np.square(np.asarray(residual_model.fit().resid,dtype=float))
    total=float(residual_sq.sum())
    if not math.isfinite(total) or total<=0:
        return {"verdict":"INCONCLUSIVE","reason":"no finite residual EER variation",
            "gate":gate,"primary":None}
    top_n=max(1,math.ceil(.01*len(panel)))
    gate["top_one_percent_residual_x_share"]=float(sum(sorted(residual_sq,reverse=True)[:top_n])/total)
    gate["top_country_residual_x_share"]=float(panel.assign(residual_sq=residual_sq)
        .groupby("geo_code").residual_sq.sum().max()/total)
    if (gate["top_one_percent_residual_x_share"]>MAX_TOP_ONE_PERCENT
            or gate["top_country_residual_x_share"]>MAX_TOP_COUNTRY):
        return {"verdict":"INCONCLUSIVE","reason":"frozen residual-EER concentration gate failed",
            "gate":gate,"primary":None}
    model=smf.ols("y ~ x+C(geo_code)+C(year)",data=panel)
    if np.linalg.matrix_rank(model.exog)!=model.exog.shape[1]:
        return {"verdict":"INCONCLUSIVE","reason":"primary model lacks full rank",
            "gate":gate,"primary":None}
    fit=model.fit()
    idx=fit.model.exog_names.index("x")
    country_codes=pd.factorize(panel.geo_code,sort=True)[0]
    cov,_,_=cov_cluster_2groups(fit,country_codes,panel.year.to_numpy(),use_correction=True)
    variance=float(cov[idx,idx])
    beta=float(fit.params["x"])
    if not math.isfinite(beta) or not math.isfinite(variance) or variance<=0:
        return {"verdict":"INCONCLUSIVE","reason":"nonfinite or nonpositive two-way cluster uncertainty",
            "gate":gate,"primary":None}
    se=math.sqrt(variance)
    dof=min(gate["valid_countries"],gate["valid_years"])-1
    p=float(2*student_t.sf(abs(beta/se),dof))
    critical=float(student_t.ppf(1-P_MAX/2,dof))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"verdict":"INCONCLUSIVE","reason":"nonfinite Student t inference",
            "gate":gate,"primary":None}
    loo=[]
    for geo in sorted(panel.geo_code.unique()):
        subset=panel.loc[panel.geo_code.ne(geo)]
        loo.append(float(smf.ols("y ~ x+C(geo_code)+C(year)",data=subset).fit().params["x"]))
    if not all(math.isfinite(v) for v in loo):
        return {"verdict":"INCONCLUSIVE","reason":"nonfinite leave-one-country-out coefficient",
            "gate":gate,"primary":None}
    gate["loo_beta_min"]=min(loo);gate["loo_beta_max"]=max(loo)
    primary={"coefficient":beta,"std_error":se,"p_value_two_sided":p,
        "confidence_level":1-P_MAX,"confidence_interval":[beta-critical*se,beta+critical*se],
        "n_rows":len(panel),"n_countries":gate["valid_countries"],"n_years":gate["valid_years"],
        "df_inference":dof,"model_rank":int(fit.model.rank),
        "method":"country/year FE OLS; two-way country and treatment-year CR1; Student t(min(G,T)-1)"}
    if beta>=MIN_ABS_BETA and p<=P_MAX and min(loo)>=MIN_LOO_BETA:
        verdict,reason="SUPPORTED","positive lagged descriptive relation clears size, family-significance, and country-deletion gates"
    elif beta<=-MIN_ABS_BETA and p<=P_MAX and max(loo)<=-MIN_LOO_BETA:
        verdict,reason="REFUTED","opposite lagged descriptive relation clears size, family-significance, and country-deletion gates"
    else:
        verdict,reason="PARTIAL","estimable relation does not clear all frozen directional gates"
    return {"verdict":verdict,"reason":reason,"gate":gate,"primary":primary}

def aggregate_results(results:dict[str,dict[str,Any]]) -> dict[str,Any]:
    counts={status:sum(result["verdict"]==status for result in results.values())
        for status in ("SUPPORTED","REFUTED","PARTIAL","INCONCLUSIVE")}
    estimable=len(CASES)-counts["INCONCLUSIVE"]
    if estimable<MIN_ESTIMABLE_CATEGORIES:
        verdict,reason="INCONCLUSIVE","fewer than sixteen component categories passed frozen estimation gates"
    elif counts["SUPPORTED"]>=MIN_DIRECTIONAL_CATEGORIES and counts["REFUTED"]==0:
        verdict,reason="SUPPORTED","at least five disjoint groups clear family-adjusted positive pass-through gates without a qualified opposite group"
    elif counts["REFUTED"]>=MIN_DIRECTIONAL_CATEGORIES and counts["SUPPORTED"]==0:
        verdict,reason="REFUTED","at least five disjoint groups clear family-adjusted opposite-direction gates without a qualified positive group"
    else:
        verdict,reason="PARTIAL","the estimable 20-group family does not clear the frozen omnibus directional rule"
    return {"verdict":verdict,"reason":reason,"counts":counts,
        "estimable_categories":estimable,"components":results}


def payload(omnibus:dict[str,Any],registration:str,lock_commit:str,stamp:str) -> dict[str,Any]:
    verdict=omnibus["verdict"];counts=omnibus["counts"]
    primary={"qualifying_positive_categories":counts["SUPPORTED"],
        "qualifying_opposite_categories":counts["REFUTED"],
        "estimable_categories":omnibus["estimable_categories"],
        "minimum_estimable":MIN_ESTIMABLE_CATEGORIES,
        "minimum_same_direction":MIN_DIRECTIONAL_CATEGORIES,
        "component_p_max_two_sided_bonferroni":P_MAX,
        "component_meaningful_beta_min_abs":MIN_ABS_BETA,
        "component_min_loo_beta_abs":MIN_LOO_BETA}
    diagnostics={"hypothesis_id":HYPOTHESIS_ID,"family_id":FAMILY,"verdict":verdict,
        "verdict_label":verdict,"verdict_reason":omnibus["reason"],"run_utc":stamp,
        "runner":RUNNER,"preregistration_commit":registration,
        "source_lock_commit":lock_commit,"source_lock":LOCK,"template":"panel_fe",
        "preflight":{"component_count":len(CASES),"component_verdict_counts":counts},
        "primary":primary,"components":omnibus["components"],
        "data_status":{"variables_missing":[],"input_vintages":list(SOURCES.values())},
        "limitations":LIMITATIONS,"correction":CORRECTION}
    manifest={"hypothesis_id":HYPOTHESIS_ID,"run_utc":stamp,"runner":RUNNER,
        "preregistration_commit":registration,"source_lock_commit":lock_commit,
        "source_lock":LOCK,"status":verdict,"vintages":list(SOURCES.values()),
        "component_verdict_counts":counts,"correction":CORRECTION}
    packet={"packet_version":1,"generated_utc":stamp,
        "hypothesis":{"id":HYPOTHESIS_ID,"path":SPEC,"topic":"monetary"},
        "preregistration":{"spec_commit":registration,"source_lock_commit":lock_commit,
            "family_id":FAMILY,"family_size":len(CASES),"public_hypothesis_count":1,
            "key_roster":ROSTER,"key_roster_sha256":ROSTER_SHA,"steelman":STEELMAN},
        "reproduction":{"runner":RUNNER,"run_dir":RUN_DIR,
            "command":f"python3 {RUNNER} --verify"},
        "verdict":{"raw":verdict,"bucket":verdict.lower(),"reason":omnibus["reason"]},
        "data":{"inputs":SOURCES,"sample":primary,"selected_coicop":list(CASES)},
        "results":{"primary":primary,"components":omnibus["components"]},
        "limitations":LIMITATIONS,"correction":CORRECTION}
    card=(f"# Result card: {HYPOTHESIS_ID}\n\nVerdict: **{verdict}**. {omnibus['reason']}.\n\n"
        f"Preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
        f"Twenty prespecified disjoint HICP groups share one public omnibus hypothesis. "
        f"Estimable components: {omnibus['estimable_categories']}/20; qualified positive: "
        f"{counts['SUPPORTED']}; qualified opposite: {counts['REFUTED']}; other estimable: "
        f"{counts['PARTIAL']}.\n\n"
        f"Each component requires two-sided p≤{P_MAX:.8f}, |beta|≥{MIN_ABS_BETA:.3f}, "
        f"and same-direction country-deletion |beta|≥{MIN_LOO_BETA:.3f}. "
        "The omnibus requires five same-direction qualifying groups and no qualified opposite group. "
        "No category is a separate public hypothesis or graduation. Zero causal, policy, school, "
        "position, and featured credit.\n")
    wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart={"hypothesis_id":HYPOTHESIS_ID,"family_id":FAMILY,"verdict":verdict,
        "primary":primary,"components":{code:{"verdict":item["verdict"],"primary":item["primary"]}
            for code,item in omnibus["components"].items()}}
    coefficients=[{"term":code,**item["primary"]} for code,item in omnibus["components"].items()
        if item["primary"] is not None]
    return {"diagnostics":diagnostics,"manifest":manifest,"packet":packet,
        "card":card,"wrapper":wrapper,"chart":chart,"coefficients":coefficients}


def summary_text(omnibus:dict[str,Any],registration:str,lock_commit:str) -> str:
    counts=omnibus["counts"]
    lines=["# Nominal depreciation and next-year HICP consumer-group inflation: one omnibus test","",
        f"Preregistration `{registration}`; source lock `{lock_commit}`.",
        f"Omnibus verdict **{omnibus['verdict']}**: {omnibus['reason']}.",
        f"Estimable groups {omnibus['estimable_categories']}/20; qualified positive {counts['SUPPORTED']}; "
        f"qualified opposite {counts['REFUTED']}; partial components {counts['PARTIAL']}.",
        f"Family alpha 0.01 across 20 prespecified components; two-sided p≤{P_MAX:.8f} for each.","",
        "| COICOP group | Component result | Complete cells / countries | Material rows / countries | Beta | Two-sided p |",
        "| --- | --- | ---: | ---: | ---: | ---: |"]
    for code,case in CASES.items():
        result=omnibus["components"][code];gate=result["gate"];primary=result["primary"]
        beta=f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p=f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {code}: {case['label']} | {result['verdict']} | "
            f"{gate['valid_rows']} / {gate['valid_countries']} | "
            f"{gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |")
    lines+=["","These twenty rows are planned estimates of **one** preregistered claim, not twenty public hypotheses. "
        "Beta is next-year annual-average HICP inflation percentage points per +1 log-percentage-point "
        "BIS nominal broad EER depreciation at t. The pinned HICP vintage lacks cell flags. "
        "The lagged association does not identify exchange-rate pass-through causally. "
        "All causal, policy, school-score, position, and featured credit is zero.",""]
    return "\n".join(lines)

def normalize(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: fields differ")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length differs")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected,
                rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def write_artifacts(omnibus:dict[str,Any],registration:str,lock_commit:str) -> None:
    folder=ROOT/RUN_DIR
    if folder.exists() or (ROOT/SUMMARY).exists():
        raise FileExistsError("measured omnibus artifacts already exist")
    stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated=payload(omnibus,registration,lock_commit,stamp)
    folder.mkdir(parents=True)
    (folder/"hypothesis.yaml").write_bytes((ROOT/SPEC).read_bytes())
    (folder/"diagnostics.json").write_text(json.dumps(generated["diagnostics"],indent=2)+"\n")
    (folder/"manifest.yaml").write_text(yaml.safe_dump(generated["manifest"],sort_keys=False))
    (folder/"evidence_packet.yaml").write_text(yaml.safe_dump(generated["packet"],sort_keys=False))
    (folder/"result_card.md").write_text(generated["card"])
    (folder/"replication.py").write_text(generated["wrapper"])
    (folder/"chart_data.json").write_text(json.dumps(generated["chart"],indent=2)+"\n")
    pd.DataFrame(generated["coefficients"],columns=["term","coefficient","std_error",
        "p_value_two_sided","confidence_level","confidence_interval","n_rows",
        "n_countries","n_years","df_inference","model_rank","method"]).to_parquet(
            folder/"coefficients.parquet",index=False)
    (ROOT/SUMMARY).write_text(summary_text(omnibus,registration,lock_commit))


def verify_artifacts(omnibus:dict[str,Any],registration:str,lock_commit:str) -> None:
    folder=ROOT/RUN_DIR
    saved=json.loads((folder/"diagnostics.json").read_text())
    generated=payload(omnibus,registration,lock_commit,saved["run_utc"])
    equal_close(saved,generated["diagnostics"],"omnibus.diagnostics")
    equal_close(yaml.safe_load((folder/"manifest.yaml").read_text()),generated["manifest"],"omnibus.manifest")
    equal_close(yaml.safe_load((folder/"evidence_packet.yaml").read_text()),generated["packet"],"omnibus.packet")
    equal_close(json.loads((folder/"chart_data.json").read_text()),generated["chart"],"omnibus.chart")
    equal_close(pd.read_parquet(folder/"coefficients.parquet").to_dict(orient="records"),
        generated["coefficients"],"omnibus.coefficients")
    if ((folder/"hypothesis.yaml").read_bytes()!=(ROOT/SPEC).read_bytes()
            or (folder/"result_card.md").read_text()!=generated["card"]
            or (folder/"replication.py").read_text()!=generated["wrapper"]):
        raise AssertionError("omnibus text artifact differs from replay")
    if (ROOT/SUMMARY).read_text()!=summary_text(omnibus,registration,lock_commit):
        raise AssertionError("omnibus summary differs from replay")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "validate-specs", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    selected = check_sources()
    if args.check_sources:
        print("exact BIS and Eurostat source/manifest hashes match; HICP values unopened")
        return 0
    if args.validate_specs:
        validate_specs()
        print("one omnibus spec and 20 component categories agree with frozen runner and roster")
        return 0
    blind = preflight()
    if args.preflight:
        print(json.dumps(blind, indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    registration = registration_commit()
    lock_commit = check_source_lock(registration, selected, blind)
    panels = measured_panels(load_roster())
    results = {code: estimate(*panels[code]) for code in CASES}
    omnibus = aggregate_results(results)
    if args.run:
        write_artifacts(omnibus, registration, lock_commit)
        print(HYPOTHESIS_ID, omnibus["verdict"], omnibus["counts"])
        return 0
    verify_artifacts(omnibus, registration, lock_commit)
    print("verified exact replay", HYPOTHESIS_ID, omnibus["verdict"], omnibus["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
