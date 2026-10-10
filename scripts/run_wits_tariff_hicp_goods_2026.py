#!/usr/bin/env python3
"""Frozen weighted-tariff-decline to next-year goods-HICP omnibus calibration.

Blind preflight reads only WITS exposure values and Eurostat category/country/year
keys. Selected HICP values and null masks first open after a separate committed
source lock. Six correlated goods groups support only one public hypothesis.
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
FAMILY = "wits_tariff_eurostat_goods_hicp_2026_10_10"
ID = "wits_tariff_decline_goods_hicp_forward_2026"
RUNNER = "scripts/run_wits_tariff_hicp_goods_2026.py"
PLAN = "engine/audits/wits_tariff_hicp_goods_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wits_tariff_hicp_key_roster_2026.csv"
ROSTER_SHA = "0c10404ea09b28c5017430c9232eda81dc7713f175fde54708493f124609fbe8"
LOCK = "data/pinned_evidence/wits_tariff_hicp_goods_2026.manifest.json"
SUMMARY = "engine/audits/wits_tariff_hicp_goods_result_2026-10-10.md"
SPEC = f"hypotheses/trade/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
RUN_DIR = f"engine/runs/{ID}"
SOURCES = {
    "tariff": {"publisher":"wits", "series_id":"weighted_mean_applied_tariff",
        "path":"data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet",
        "sha256":"73520e0da6a44048e51a64671c97369aadf160130937f351f90375fb86b0e010",
        "manifest":"data/manifests/fetch_run_2026-07-23T151550Z.yaml",
        "manifest_sha256":"96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5"},
    "hicp": {"publisher":"eurostat", "series_id":"prc_hicp_aind",
        "path":"data/vintages/eurostat/prc_hicp_aind@2026-04-30T115920Z.parquet",
        "sha256":"be97a646f95e04c481c583bcde08817aaf6fc315cb7b5f1b628c735cf6a2aec4",
        "manifest":"data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256":"e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
}
GEO_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","CY":"CYP","CZ":"CZE","DE":"DEU",
    "DK":"DNK","EE":"EST","EL":"GRC","ES":"ESP","FI":"FIN","FR":"FRA",
    "HR":"HRV","HU":"HUN","IE":"IRL","IS":"ISL","IT":"ITA","LT":"LTU",
    "LU":"LUX","LV":"LVA","MT":"MLT","NL":"NLD","NO":"NOR","PL":"POL",
    "PT":"PRT","RO":"ROU","SE":"SWE","SI":"SVN","SK":"SVK",
    "CH":"CHE","TR":"TUR","UK":"GBR","RS":"SRB","MK":"MKD","AL":"ALB","ME":"MNE",
}
# Six non-nested three-digit spending groups predominantly made of tradable goods.
# This is a conceptual basket selection, NOT measured group-specific import shares.
CASES = {
    "CP031":"clothing", "CP032":"footwear", "CP052":"household textiles",
    "CP053":"household appliances", "CP071":"vehicle purchases",
    "CP091":"audio-visual and information-processing equipment",
}
FIRST_T, LAST_T, MIN_YEARS = 1998, 2018, 5
MAX_ABS_DECLINE, MATERIAL_ABS_DECLINE = 6.0, 1.0
MIN_VALID_ROWS, MIN_VALID_COUNTRIES = 400, 28
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 50, 25
MAX_TOP_ONE_PERCENT, MAX_TOP_COUNTRY = .30, .25
FAMILY_ALPHA, P_MAX = .01, .01 / len(CASES)
MIN_ABS_BETA, MIN_LOO_BETA = .10, .05
MIN_ESTIMABLE, MIN_DIRECTIONAL = 5, 2
CORRECTION = {"disposition":"descriptive_calibration_only", "family_id":FAMILY,
    "family_size":len(CASES), "family_alpha":FAMILY_ALPHA,
    "bonferroni_p_max":P_MAX, "public_hypothesis_count":1,
    "component_estimates":len(CASES), "causal_credit":0,
    "policy_score_eligible":False,"policy_score_credit":0,
    "school_score_eligible":False,"school_score_credit":0,"featured_eligible":False}
LIMITATIONS = [
    "The WITS series is an import-weighted applied merchandise tariff across all products, not a category-specific tariff, policy event, or exogenous reform. A change can reflect import composition and data revision.",
    "The six Eurostat COICOP groups are distinct goods-heavy spending groups, but their actual import shares were not measured. They share the same tariff panel, macro shocks, HICP methodology, and national price regimes; they count as one omnibus claim.",
    "Euro-area members share an external tariff; remaining country variation may reflect import weights rather than national tariff policy. Exchange rates, commodity costs, VAT, distribution margins, demand, and accession can confound the association.",
    "A three-year tariff change and next-year annual-average HICP inflation establish ordering but cannot identify when costs passed through. The annual-average rate is not December-to-December inflation.",
    "The pinned HICP Parquet lacks retained cell flags; finite values are not claimed break-screened or method-continuous. The pinned prc_hicp_aind table was later superseded by an ECOICOP 2 table.",
    "The six-test Bonferroni correction is local; prior IESET tariff and HICP archive exploration is not corrected. No causal, policy-effect, school-score, position, or featured credit is permitted.",
]


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def git(*args:str)->bytes:
    return subprocess.check_output(['git',*args],cwd=ROOT)


def first_addition(path:str)->str:
    commits=git('log','--diff-filter=A','--format=%H','HEAD','--',path).decode().splitlines()
    if not commits:raise RuntimeError(f'no committed first addition: {path}')
    return commits[-1]


def committed_unchanged(path:str,commit:str)->None:
    if (ROOT/path).read_bytes()!=git('show',f'{commit}:{path}'):
        raise RuntimeError(f'frozen registration file modified: {path}')
    if git('status','--porcelain','--',path).strip():
        raise RuntimeError(f'uncommitted frozen file: {path}')


def threshold()->dict[str,Any]:
    return {"family_id":FAMILY,"family_size":len(CASES),"family_alpha":FAMILY_ALPHA,
        "public_hypothesis_count":1,"component_estimates":len(CASES),
        "p_max_two_sided_bonferroni":P_MAX,"expected_beta_sign":"-",
        "meaningful_beta_min_abs":MIN_ABS_BETA,"min_loo_beta_abs":MIN_LOO_BETA,
        "min_estimable_categories":MIN_ESTIMABLE,"min_directional_categories":MIN_DIRECTIONAL,
        "min_valid_rows_per_category":MIN_VALID_ROWS,
        "min_valid_countries_per_category":MIN_VALID_COUNTRIES,
        "min_material_change_rows_per_category":MIN_MATERIAL_ROWS,
        "min_material_change_countries_per_category":MIN_MATERIAL_COUNTRIES,
        "material_tariff_change_min_abs":MATERIAL_ABS_DECLINE,
        "max_abs_three_year_tariff_change":MAX_ABS_DECLINE,
        "min_complete_years_per_country":MIN_YEARS,
        "max_top_one_percent_residual_x_share":MAX_TOP_ONE_PERCENT,
        "max_top_country_residual_x_share":MAX_TOP_COUNTRY,
        "selected_coicop":list(CASES),"selected_hicp_unit":"RCH_A_AVG",
        "expected_key_rows_by_code":{c:514 for c in CASES},
        "expected_key_countries_by_code":{c:33 for c in CASES},
        "expected_material_key_rows_by_code":{c:71 for c in CASES},
        "expected_material_key_countries_by_code":{c:30 for c in CASES},
        "roster_sha256":ROSTER_SHA,
        "source_files":{role:{k:source[k] for k in ('path','sha256','manifest','manifest_sha256')}
            for role,source in SOURCES.items()},
        "causal_credit":0,"policy_score_eligible":False,"policy_score_credit":0,
        "school_score_eligible":False,"school_score_credit":0,"featured_eligible":False}


def load_roster()->dict[str,list[tuple[str,int]]]:
    path=ROOT/ROSTER
    raw=path.read_bytes()
    if sha(path)!=ROSTER_SHA or not raw.startswith(b'coicop,geo_code,treatment_year\n'):
        raise RuntimeError('key-only roster header/hash mismatch')
    rows=[(r['coicop'],r['geo_code'],int(r['treatment_year']))
        for r in csv.DictReader(io.StringIO(raw.decode()))]
    if rows!=sorted(set(rows)) or len(rows)!=3084:raise RuntimeError('roster order or size mismatch')
    out={c:[] for c in CASES}
    for c,g,t in rows:
        if c not in CASES or g not in GEO_TO_ISO3 or not FIRST_T<=t<=LAST_T:
            raise RuntimeError('unexpected frozen key')
        out[c].append((g,t))
    for c in CASES:
        if len(out[c])!=514 or len({g for g,_ in out[c]})!=33:
            raise RuntimeError(f'frozen key envelope differs: {c}')
    return out


def validate_specs()->None:
    spec=yaml.safe_load((ROOT/SPEC).read_text())
    countries=sorted({GEO_TO_ISO3[g] for rows in load_roster().values() for g,_ in rows})
    if (spec.get('hypothesis_id')!=ID or spec.get('status')!='pre_registered'
        or spec.get('evidence_type')!='associational'
        or spec.get('claim_direction')!='-'
        or spec.get('steelman')!=STEELMAN
        or spec.get('covers_claims')!=[] or spec.get('linked_hypotheses')!=[]
        or spec.get('linked_conditions')!=[]
        or spec['sample'].get('countries')!=countries
        or spec['sample'].get('period')!=[FIRST_T,LAST_T+1]
        or spec['falsification'].get('threshold')!=threshold()):
        raise RuntimeError('spec differs from frozen runner and key roster')


def check_sources()->dict[str,dict[str,Any]]:
    out={}
    for role,source in SOURCES.items():
        path=ROOT/source['path'];manifest=ROOT/source['manifest']
        if not path.is_file() or sha(path)!=source['sha256']:
            raise RuntimeError(f'pinned source absent or changed: {role}')
        if not manifest.is_file() or sha(manifest)!=source['manifest_sha256']:
            raise RuntimeError(f'fetch manifest absent or changed: {role}')
        entries=yaml.safe_load(manifest.read_text()).get('entries',[])
        matches=[e for e in entries if e.get('publisher')==source['publisher']
            and e.get('series_id')==source['series_id']
            and e.get('parquet_path')==source['path'] and e.get('sha256')==source['sha256']]
        if len(matches)!=1:raise RuntimeError(f'fetch manifest lacks exact source: {role}')
        out[role]={**source,**{k:matches[0].get(k) for k in
            ('source_url','methodology_url','license','fetch_utc')}}
    return out


def exposure()->dict[tuple[str,int],float]:
    # Only treatment values and their missingness may be opened before registration.
    cols=['country_iso3','indicator_id','series_id','year','value','obs_status']
    raw=pd.read_parquet(ROOT/SOURCES['tariff']['path'],columns=cols)
    raw=raw.loc[raw.indicator_id.eq('TM.TAX.MRCH.WM.AR.ZS')
        & raw.series_id.eq('weighted_mean_applied_tariff')
        & raw.country_iso3.isin(GEO_TO_ISO3.values())].copy()
    raw['year']=pd.to_numeric(raw.year,errors='raise').astype(int)
    if raw.duplicated(['country_iso3','year']).any():
        raise RuntimeError('duplicate selected tariff country-year key')
    raw['value']=pd.to_numeric(raw.value,errors='coerce')
    raw=raw.loc[raw.obs_status.eq('') & raw.value.map(math.isfinite) & raw.value.ge(0)]
    annual={(r.country_iso3,int(r.year)):float(r.value) for r in raw.itertuples()}
    out={}
    for g,iso in GEO_TO_ISO3.items():
        for t in range(FIRST_T,LAST_T+1):
            if (iso,t-3) in annual and (iso,t) in annual:
                d=annual[iso,t-3]-annual[iso,t]
                if math.isfinite(d) and abs(d)<=MAX_ABS_DECLINE:out[g,t]=d
    return out


def outcome_keys()->dict[str,set[tuple[str,int]]]:
    # Categorical fields only: no selected HICP value/null column access.
    cols=['freq','unit','coicop','geo_code','period']
    raw=pd.read_parquet(ROOT/SOURCES['hicp']['path'],columns=cols)
    raw=raw.loc[raw.freq.eq('A') & raw.unit.eq('RCH_A_AVG')
        & raw.coicop.isin(CASES) & raw.geo_code.isin(GEO_TO_ISO3)].copy()
    raw['year']=pd.to_numeric(raw.period,errors='raise').astype(int)
    if raw.duplicated(['coicop','geo_code','year']).any():
        raise RuntimeError('duplicate selected HICP categorical key')
    return {c:set(raw.loc[raw.coicop.eq(c),['geo_code','year']]
        .itertuples(index=False,name=None)) for c in CASES}


def expected_roster()->dict[str,list[tuple[str,int]]]:
    x=exposure();keys=outcome_keys();out={}
    for c in CASES:
        rows=[(g,t) for g,t in x if (g,t+1) in keys[c]]
        counts=pd.Series([g for g,_ in rows]).value_counts()
        out[c]=sorted((g,t) for g,t in rows if counts[g]>=MIN_YEARS)
    return out


def preflight()->dict[str,Any]:
    roster=load_roster()
    if expected_roster()!=roster:raise RuntimeError('frozen roster differs from source keys and tariff values')
    x=exposure();out={}
    for c,rows in roster.items():
        material=[(g,t) for g,t in rows if abs(x[g,t])>=MATERIAL_ABS_DECLINE]
        if len(material)!=71 or len({g for g,_ in material})!=30:
            raise RuntimeError(f'blind material exposure envelope differs: {c}')
        out[c]={"key_rows":len(rows),"key_countries":len({g for g,_ in rows}),
            "material_tariff_change_rows":len(material),
            "material_tariff_change_countries":len({g for g,_ in material})}
    return {"family_size":len(CASES),"by_category":out,"outcome_values_opened":False,
        "outcome_null_masks_opened":False,
        "note":"Key-only HICP roster is an upper bound; no HICP values, nulls, or fits were screened."}


def registration_commit()->str:
    files=[RUNNER,PLAN,ROSTER,SPEC,STEELMAN]
    commits={first_addition(f) for f in files}
    if len(commits)!=1:raise RuntimeError('registration files lack shared first-addition commit')
    rev=commits.pop()
    for f in files:committed_unchanged(f,rev)
    if git('ls-tree','-r','--name-only',rev,'--',RUN_DIR).strip():
        raise RuntimeError('registration commit included measured result')
    validate_specs()
    return rev


def lock_payload(reg:str,selected:dict,blind:dict)->dict:
    return {"family_id":FAMILY,"preregistration_commit":reg,"sources":selected,
        "key_only_preflight":blind,
        "statement":"Source pins committed after preregistration and before selected HICP values or nulls were opened."}


def write_lock()->None:
    reg=registration_commit();selected=check_sources();blind=preflight()
    path=ROOT/LOCK
    if path.exists():raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(reg,selected,blind),indent=2,sort_keys=True)+'\n')


def check_lock(reg:str,selected:dict,blind:dict)->str:
    rev=first_addition(LOCK)
    if rev==reg:raise RuntimeError('source lock must be committed separately')
    subprocess.check_call(['git','merge-base','--is-ancestor',reg,rev],cwd=ROOT)
    committed_unchanged(LOCK,rev)
    if json.loads((ROOT/LOCK).read_text())!=lock_payload(reg,selected,blind):
        raise RuntimeError('source lock differs from frozen pins')
    if git('ls-tree','-r','--name-only',rev,'--',RUN_DIR).strip():
        raise RuntimeError('source-lock commit included measured result')
    return rev


def measured_hicp()->dict[str,dict[tuple[str,int],float|None]]:
    # First selected HICP numeric/null access; caller has validated both commits.
    cols=['freq','unit','coicop','geo_code','period','value']
    raw=pd.read_parquet(ROOT/SOURCES['hicp']['path'],columns=cols)
    raw=raw.loc[raw.freq.eq('A') & raw.unit.eq('RCH_A_AVG')
        & raw.coicop.isin(CASES) & raw.geo_code.isin(GEO_TO_ISO3)].copy()
    raw['year']=pd.to_numeric(raw.period,errors='raise').astype(int)
    if raw.duplicated(['coicop','geo_code','year']).any():
        raise RuntimeError('duplicate measured HICP cell')
    raw['value']=pd.to_numeric(raw.value,errors='coerce')
    return {c:{(g,int(y)):float(v) if pd.notna(v) else None for g,y,v in
        raw.loc[raw.coicop.eq(c),['geo_code','year','value']].itertuples(index=False,name=None)}
        for c in CASES}


def measured_panels(roster:dict)->dict[str,tuple[pd.DataFrame,dict]]:
    y=measured_hicp();x=exposure();out={}
    for c,rows in roster.items():
        panel=[];invalid=0
        for g,t in rows:
            value=y[c].get((g,t+1))
            if value is None or not math.isfinite(value):invalid+=1;continue
            panel.append({'geo_code':g,'year':t,'x':x[g,t],'y':value})
        frame=pd.DataFrame(panel,columns=['geo_code','year','x','y'])
        counts=frame.geo_code.value_counts()
        frame=frame.loc[frame.geo_code.map(counts).ge(MIN_YEARS)].copy()
        frame=frame.sort_values(['geo_code','year']).reset_index(drop=True)
        material=frame.x.abs().ge(MATERIAL_ABS_DECLINE)
        gate={"key_only_rows":len(rows),"missing_or_nonfinite_hicp_cells":invalid,
            "valid_rows":len(frame),"valid_countries":int(frame.geo_code.nunique()),
            "valid_years":int(frame.year.nunique()),
            "material_change_rows":int(material.sum()),
            "material_change_countries":int(frame.loc[material,'geo_code'].nunique()),
            "min_complete_years_per_country":MIN_YEARS,
            "outcome_values_read_after_lock":True,"source_cell_flags_available":False}
        out[c]=(frame,gate)
    return out


def estimate(frame:pd.DataFrame,gate:dict)->dict:
    def inconclusive(reason:str)->dict:
        return {"verdict":"INCONCLUSIVE","reason":reason,"gate":gate,"primary":None}
    if (gate['valid_rows']<MIN_VALID_ROWS or gate['valid_countries']<MIN_VALID_COUNTRIES
        or gate['material_change_rows']<MIN_MATERIAL_ROWS
        or gate['material_change_countries']<MIN_MATERIAL_COUNTRIES):
        return inconclusive('frozen complete-case or material-tariff-change floor failed')
    rm=smf.ols('x ~ C(geo_code)+C(year)',data=frame)
    if np.linalg.matrix_rank(rm.exog)!=rm.exog.shape[1]:
        return inconclusive('residual tariff design lacks full rank')
    sq=np.square(np.asarray(rm.fit().resid,dtype=float));total=float(sq.sum())
    if not math.isfinite(total) or total<=0:return inconclusive('no finite residual tariff variation')
    gate['top_one_percent_residual_x_share']=float(sum(sorted(sq,reverse=True)[:max(1,math.ceil(.01*len(frame)))])/total)
    gate['top_country_residual_x_share']=float(frame.assign(sq=sq).groupby('geo_code').sq.sum().max()/total)
    if (gate['top_one_percent_residual_x_share']>MAX_TOP_ONE_PERCENT
        or gate['top_country_residual_x_share']>MAX_TOP_COUNTRY):
        return inconclusive('frozen residual-tariff influence gate failed')
    model=smf.ols('y ~ x+C(geo_code)+C(year)',data=frame)
    if np.linalg.matrix_rank(model.exog)!=model.exog.shape[1]:
        return inconclusive('primary model lacks full rank')
    fit=model.fit();idx=fit.model.exog_names.index('x')
    codes=pd.factorize(frame.geo_code,sort=True)[0]
    cov,_,_=cov_cluster_2groups(fit,codes,frame.year.to_numpy(),use_correction=True)
    variance=float(cov[idx,idx]);beta=float(fit.params['x'])
    if not math.isfinite(beta) or not math.isfinite(variance) or variance<=0:
        return inconclusive('nonfinite or nonpositive two-way cluster uncertainty')
    se=math.sqrt(variance);dof=min(gate['valid_countries'],gate['valid_years'])-1
    p=float(2*student_t.sf(abs(beta/se),dof))
    critical=float(student_t.ppf(1-P_MAX/2,dof))
    if not math.isfinite(p) or not math.isfinite(critical):
        return inconclusive('nonfinite Student t inference')
    loo=[float(smf.ols('y ~ x+C(geo_code)+C(year)',data=frame.loc[frame.geo_code.ne(g)])
        .fit().params['x']) for g in sorted(frame.geo_code.unique())]
    if not all(math.isfinite(v) for v in loo):
        return inconclusive('nonfinite country-deletion coefficient')
    gate['loo_beta_min']=min(loo);gate['loo_beta_max']=max(loo)
    primary={"coefficient":beta,"std_error":se,"p_value_two_sided":p,
        "confidence_level":1-P_MAX,"confidence_interval":[beta-critical*se,beta+critical*se],
        "n_rows":len(frame),"n_countries":gate['valid_countries'],"n_years":gate['valid_years'],
        "df_inference":dof,"model_rank":int(fit.model.rank),
        "method":"country/year FE OLS; two-way country and treatment-year CR1; Student t(min(G,T)-1)"}
    if beta<=-MIN_ABS_BETA and p<=P_MAX and max(loo)<=-MIN_LOO_BETA:
        verdict,reason='SUPPORTED','lower later HICP inflation clears size, family-p, and country-deletion gates'
    elif beta>=MIN_ABS_BETA and p<=P_MAX and min(loo)>=MIN_LOO_BETA:
        verdict,reason='REFUTED','higher later HICP inflation clears opposite-direction gates'
    else:verdict,reason='PARTIAL','estimable component does not clear all directional gates'
    return {"verdict":verdict,"reason":reason,"gate":gate,"primary":primary}


def omnibus(results:dict[str,dict])->dict:
    counts={v:sum(r['verdict']==v for r in results.values())
        for v in ('SUPPORTED','REFUTED','PARTIAL','INCONCLUSIVE')}
    estimable=len(CASES)-counts['INCONCLUSIVE']
    if estimable<MIN_ESTIMABLE:
        verdict,reason='INCONCLUSIVE','fewer than five goods groups passed frozen estimation gates'
    elif counts['SUPPORTED']>=MIN_DIRECTIONAL and counts['REFUTED']==0:
        verdict,reason='SUPPORTED','at least two groups cleared corrected lower-inflation gates and none cleared the opposite gate'
    elif counts['REFUTED']>=MIN_DIRECTIONAL and counts['SUPPORTED']==0:
        verdict,reason='REFUTED','at least two groups cleared corrected opposite-direction gates and none cleared the lower-inflation gate'
    else:verdict,reason='PARTIAL','estimable six-group family did not clear the frozen omnibus directional rule'
    return {"verdict":verdict,"reason":reason,"counts":counts,
        "estimable_categories":estimable,"components":results}


def payload(result:dict,reg:str,lock:str,stamp:str)->dict:
    verdict=result['verdict'];counts=result['counts']
    primary={"qualified_lower_inflation_groups":counts['SUPPORTED'],
        "qualified_opposite_groups":counts['REFUTED'],
        "estimable_groups":result['estimable_categories'],
        "minimum_estimable_groups":MIN_ESTIMABLE,"minimum_directional_groups":MIN_DIRECTIONAL,
        "family_p_max_two_sided_bonferroni":P_MAX,
        "material_tariff_decline_rule":"absolute three-year change >= 1 percentage point"}
    diagnostics={"hypothesis_id":ID,"family_id":FAMILY,"verdict":verdict,
        "verdict_label":verdict,"verdict_reason":result['reason'],"run_utc":stamp,
        "runner":RUNNER,"preregistration_commit":reg,"source_lock_commit":lock,
        "source_lock":LOCK,"template":"panel_fe",
        "preflight":{"component_count":len(CASES),"component_verdict_counts":counts},
        "primary":primary,"components":result['components'],
        "data_status":{"variables_missing":[],"input_vintages":list(SOURCES.values())},
        "limitations":LIMITATIONS,"correction":CORRECTION}
    manifest={"hypothesis_id":ID,"run_utc":stamp,"runner":RUNNER,
        "preregistration_commit":reg,"source_lock_commit":lock,
        "source_lock":LOCK,"status":verdict,"vintages":list(SOURCES.values()),
        "component_verdict_counts":counts,"correction":CORRECTION}
    packet={"packet_version":1,"generated_utc":stamp,
        "hypothesis":{"id":ID,"path":SPEC,"topic":"trade"},
        "preregistration":{"spec_commit":reg,"source_lock_commit":lock,
            "family_id":FAMILY,"family_size":len(CASES),"public_hypothesis_count":1,
            "key_roster":ROSTER,"key_roster_sha256":ROSTER_SHA,"steelman":STEELMAN},
        "reproduction":{"runner":RUNNER,"run_dir":RUN_DIR,
            "command":f"python3 {RUNNER} --verify"},
        "verdict":{"raw":verdict,"bucket":verdict.lower(),"reason":result['reason']},
        "data":{"inputs":SOURCES,"sample":primary,"selected_coicop":list(CASES)},
        "results":{"primary":primary,"components":result['components']},
        "limitations":LIMITATIONS,"correction":CORRECTION}
    card=(f"# Result card: {ID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Preregistration: `{reg}`; source lock: `{lock}`.\n\n"
        f"Six selected non-nested HICP goods groups form one public omnibus hypothesis. "
        f"Estimable {result['estimable_categories']}/6; qualified lower-inflation "
        f"{counts['SUPPORTED']}; qualified opposite {counts['REFUTED']}. "
        f"Each component needs two-sided p <= {P_MAX:.8f}, absolute beta >= {MIN_ABS_BETA:.3f}, "
        f"and matching country-deletion absolute beta >= {MIN_LOO_BETA:.3f}. "
        "No component is a separate public hypothesis; no causal, policy-effect, school, position, or featured credit.\n")
    wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root=Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'--verify'],cwd=root))\n")
    chart={"hypothesis_id":ID,"family_id":FAMILY,"verdict":verdict,
        "primary":primary,"components":{c:{"verdict":r['verdict'],"primary":r['primary']}
            for c,r in result['components'].items()}}
    coefficients=[{"term":c,**r['primary']} for c,r in result['components'].items()
        if r['primary'] is not None]
    return {"diagnostics":diagnostics,"manifest":manifest,"packet":packet,
        "card":card,"wrapper":wrapper,"chart":chart,"coefficients":coefficients}


def summary_text(result:dict,reg:str,lock:str)->str:
    counts=result['counts']
    lines=["# Import-weighted tariff declines and next-year goods HICP: one omnibus test","",
        f"Registration `{reg}`; source lock `{lock}`.",
        f"Omnibus **{result['verdict']}**: {result['reason']}.",
        f"Estimable groups {result['estimable_categories']}/6; qualifying lower-inflation {counts['SUPPORTED']}; "
        f"opposite {counts['REFUTED']}; partial {counts['PARTIAL']}.",
        f"Six-test family alpha 0.01; two-sided component p <= {P_MAX:.8f}.","",
        "| Goods group | Component | Complete cells / countries | Material rows / countries | Beta | Two-sided p |",
        "| --- | --- | ---: | ---: | ---: | ---: |"]
    for c,label in CASES.items():
        r=result['components'][c];g=r['gate'];p=r['primary']
        beta=f"{p['coefficient']:+.6g}" if p else 'not estimated'
        pv=f"{p['p_value_two_sided']:.6g}" if p else 'not estimated'
        lines.append(f"| {c}: {label} | {r['verdict']} | {g['valid_rows']} / {g['valid_countries']} | "
            f"{g['material_change_rows']} / {g['material_change_countries']} | {beta} | {pv} |")
    lines.extend(["","The six component estimates support only one preregistered descriptive claim. "
        "Beta is next-year annual-average goods HICP inflation percentage points per +1 percentage-point "
        "decline in the import-weighted all-merchandise applied tariff across t-3 to t. "
        "The tariff is not a category-specific policy treatment, and the observed relation cannot establish causal pass-through. "
        "The HICP file lacks retained cell flags. All causal, policy, school, position, and featured credit is zero.",""])
    return '\n'.join(lines)


def normalize(v:Any)->Any:
    if isinstance(v,np.ndarray):return [normalize(x) for x in v.tolist()]
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
    if isinstance(v,list):return [normalize(x) for x in v]
    return v


def equal_close(actual:Any,expected:Any,label:str)->None:
    actual=normalize(actual)
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or set(actual)!=set(expected):
            raise AssertionError(f'{label}: fields differ')
        for k,v in expected.items():equal_close(actual[k],v,f'{label}.{k}')
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected):
            raise AssertionError(f'{label}: list length differs')
        for i,v in enumerate(expected):equal_close(actual[i],v,f'{label}[{i}]')
    elif isinstance(expected,float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual),expected,rel_tol=1e-9,abs_tol=1e-11):
            raise AssertionError(f'{label}: numeric mismatch')
    elif actual!=expected:raise AssertionError(f'{label}: value mismatch')


def write_artifacts(result:dict,reg:str,lock:str)->None:
    folder=ROOT/RUN_DIR
    if folder.exists() or (ROOT/SUMMARY).exists():raise FileExistsError('measured artifacts already exist')
    stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    out=payload(result,reg,lock,stamp);folder.mkdir(parents=True)
    (folder/'hypothesis.yaml').write_bytes((ROOT/SPEC).read_bytes())
    (folder/'diagnostics.json').write_text(json.dumps(out['diagnostics'],indent=2)+'\n')
    (folder/'manifest.yaml').write_text(yaml.safe_dump(out['manifest'],sort_keys=False))
    (folder/'evidence_packet.yaml').write_text(yaml.safe_dump(out['packet'],sort_keys=False))
    (folder/'result_card.md').write_text(out['card'])
    (folder/'replication.py').write_text(out['wrapper'])
    (folder/'chart_data.json').write_text(json.dumps(out['chart'],indent=2)+'\n')
    pd.DataFrame(out['coefficients'],columns=['term','coefficient','std_error',
        'p_value_two_sided','confidence_level','confidence_interval','n_rows',
        'n_countries','n_years','df_inference','model_rank','method']).to_parquet(
            folder/'coefficients.parquet',index=False)
    (ROOT/SUMMARY).write_text(summary_text(result,reg,lock))


def verify_artifacts(result:dict,reg:str,lock:str)->None:
    folder=ROOT/RUN_DIR;saved=json.loads((folder/'diagnostics.json').read_text())
    out=payload(result,reg,lock,saved['run_utc'])
    equal_close(saved,out['diagnostics'],'diagnostics')
    equal_close(yaml.safe_load((folder/'manifest.yaml').read_text()),out['manifest'],'manifest')
    equal_close(yaml.safe_load((folder/'evidence_packet.yaml').read_text()),out['packet'],'packet')
    equal_close(json.loads((folder/'chart_data.json').read_text()),out['chart'],'chart')
    equal_close(pd.read_parquet(folder/'coefficients.parquet').to_dict(orient='records'),out['coefficients'],'coefficients')
    for name,expected in [('hypothesis.yaml',(ROOT/SPEC).read_bytes()),
        ('result_card.md',out['card'].encode()),('replication.py',out['wrapper'].encode())]:
        if (folder/name).read_bytes()!=expected:raise AssertionError(f'{name} replay mismatch')
    if (ROOT/SUMMARY).read_text()!=summary_text(result,reg,lock):
        raise AssertionError('summary replay mismatch')


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);actions=parser.add_mutually_exclusive_group(required=True)
    for name in ('check-sources','validate-specs','preflight','write-source-lock','run','verify'):
        actions.add_argument('--'+name,action='store_true')
    args=parser.parse_args();selected=check_sources()
    if args.check_sources:
        print('exact WITS and Eurostat source hashes and manifests match; HICP values unopened');return 0
    if args.validate_specs:
        validate_specs();print('one omnibus spec, six planned groups, and frozen roster agree');return 0
    blind=preflight()
    if args.preflight:print(json.dumps(blind,indent=2,sort_keys=True));return 0
    if args.write_source_lock:
        write_lock();print(f'wrote {LOCK}; commit separately before --run');return 0
    reg=registration_commit();lock=check_lock(reg,selected,blind)
    panels=measured_panels(load_roster())
    result=omnibus({c:estimate(*panels[c]) for c in CASES})
    if args.run:
        write_artifacts(result,reg,lock)
        print(f'{ID}: {result["verdict"]}; {result["estimable_categories"]}/6 estimable')
    else:
        verify_artifacts(result,reg,lock)
        print(f'exact replay verified: {ID}: {result["verdict"]}')
    return 0

if __name__=='__main__':raise SystemExit(main())
