#!/usr/bin/env python3
"""Frozen eight-cell GFDD bank-resilience to future-crisis family.

Register and lock inspect exact source files, metadata and country/year keys
only. Selected numeric values, missingness and crisis flags are first read by
measure after the registration and all eight source locks are committed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pycountry
import statsmodels.formula.api as smf
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT=Path(__file__).resolve().parents[1]
FAMILY='gfdd_bank_resilience_future_crisis_2026_10_10'
RUNNER='scripts/run_gfdd_bank_resilience_crisis_2026.py'
PLAN='engine/audits/gfdd_bank_resilience_crisis_prereg_2026-10-10.md'
REPORT='engine/audits/gfdd_bank_resilience_crisis_results_2026-10-10.md'
ROSTER='data/pinned_evidence/gfdd_bank_resilience_crisis_2026_key_roster.csv'
ROSTER_SHA='d303224ca61e58debe69378870d7879d0e24df2777747cba004fb01990d0194e'
DATA_SOURCE=dict(path='data/vintages/gfdd/GFDDData@2026-05-02T201137Z.parquet',
    sha256='9afa3262a7de79ded1325797ef96153f56d5a842bd47d9d32979f7e45065d283',
    publisher='World Bank Global Financial Development Database',
    source_url='https://www.worldbank.org/en/publication/gfdr/data/global-financial-development-database',
    fetch_manifest=None)
META_SOURCE=dict(path='data/vintages/gfdd/GFDDSeries@2026-05-02T201137Z.parquet',
    sha256='3bc9958c85b97f9299f19587570f5bc6e474028a31285a3c38194d3eab424746',
    publisher='World Bank Global Financial Development Database',
    source_url='https://databank.worldbank.org/metadataglossary/global-financial-development/series%2Ccountry/viewall',
    fetch_manifest=None)
GDP_SOURCE=dict(path='data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet',
    sha256='0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f',
    publisher='world_bank_wdi',series_id='NY.GDP.PCAP.KD',
    source_url='https://data.worldbank.org/indicator/NY.GDP.PCAP.KD',
    manifest='data/manifests/fetch_run_2026-05-05T200056Z.yaml',
    manifest_sha256='a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945')
CRISIS='GFDD.OI.19'
CREDIT='GFDD.DI.14'
# Frozen a priori from GFDD Stability topic, plus one banking operating-efficiency indicator.
CELLS=(
    ('z_score','GFDD.SI.01','Bank Z-score',-1,100.0),
    ('nonperforming_loans','GFDD.SI.02','Bank nonperforming loans to gross loans',+1,100.0),
    ('capital_assets','GFDD.SI.03','Bank capital to total assets',-1,100.0),
    ('credit_deposits','GFDD.SI.04','Bank credit to bank deposits',+1,500.0),
    ('regulatory_capital','GFDD.SI.05','Bank regulatory capital to risk-weighted assets',-1,100.0),
    ('liquid_assets','GFDD.SI.06','Liquid assets to deposits and short-term funding',-1,300.0),
    ('loan_loss_provisions','GFDD.SI.07','Provisions to nonperforming loans',-1,500.0),
    ('cost_income','GFDD.EI.07','Bank cost to income ratio',+1,300.0),
)
ANCHORS=(2000,2005,2010)
KEY_COUNTRIES=212
KEY_ROWS_PER_CELL=636
ALPHA=0.05
MIN_ABS_BETA=0.03
MIN_ROWS=120
MIN_COUNTRIES=50
MIN_PER_ANCHOR=20
MIN_EVENTS=10
MIN_EVENT_COUNTRIES=8
MIN_NON_EVENTS=80
MIN_COMPLETE_ANCHORS=2
MIN_RESIDUAL_X_SD=0.20
MIN_RESIDUAL_Y_SD=0.05
MAX_TOP_ONE_PERCENT_SS=0.30
MAX_TOP_COUNTRY_SS=0.20
MIN_FOLD_ROWS=80
MIN_FOLD_COUNTRIES=35
MIN_SAME_SIGN_FOLDS=4
MAX_CREDIT_LEVEL=400.0
MAX_ABS_PRIOR_CREDIT_CHANGE=150.0
CREDIT_CORRECTION=dict(disposition='descriptive_calibration_only',causal_credit=0,
    policy_score_eligible=False,policy_score_credit=0,
    school_score_eligible=False,school_score_credit=0,featured_eligible=False)
LIMITS=[
    'The GFDD crisis dummy records years of Laeven–Valencia systemic banking crises; requiring five complete future years avoids treating missing years as non-events.',
    'Bank ratios are observational signals, not randomized prudential interventions; crisis risk, deleveraging and policy responses can affect measured ratios before the recorded onset.',
    'Seven indicators come from the GFDD Stability topic and cost-to-income from Efficiency; they share banking systems, countries and outcome, so eight cells form one correlated Holm family.',
    'The frozen 2000, 2005 and 2010 anchors end in 2015 and avoid the 2015 Bankscope-to-Orbis switch for some baseline predictors; source methods can still differ across countries.',
    'Country and anchor effects, baseline private-credit level/change and baseline real income do not isolate causal bank resilience or policy effects.',
    'The local GFDD parquet hashes and official World Bank metadata are pinned, but this older corpus has no tracked fetch manifest; raw source custody cannot be independently reconstructed from a manifest.',
    'Holm corrects this eight-cell family, not the entire previously visible IESET banking-crisis literature.',
    'No causal, policy, school, position or featured credit is assigned.',
]


def hid(cell: tuple) -> str:
    return f'gfdd_{cell[0]}_future_banking_crisis_2026'


def spec_rel(cell: tuple) -> str:
    return f'hypotheses/regulatory/{hid(cell)}.yaml'


def steel_rel(cell: tuple) -> str:
    return f'hypotheses/steelman/{hid(cell)}.md'


def lock_rel(cell: tuple) -> str:
    return f'data/pinned_evidence/{hid(cell)}.source.json'


def run_rel(cell: tuple) -> str:
    return f'engine/runs/{hid(cell)}'


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()


def js(value: Any) -> bytes:
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+'\n').encode()


def ya(value: Any) -> bytes:
    return yaml.safe_dump(value,sort_keys=False,allow_unicode=True,width=100).encode()


def git(*args: str) -> bytes:
    proc=subprocess.run(['git',*args],cwd=ROOT,capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace')}")
    return proc.stdout


def first_add(path: str) -> str:
    commits=git('log','--diff-filter=A','--reverse','--format=%H','HEAD','--',path).decode().splitlines()
    if len(commits)!=1:
        raise RuntimeError(f'expected one first-addition commit for {path}: {commits}')
    return commits[0]


def ancestor(older: str,newer: str) -> bool:
    return older!=newer and subprocess.run(['git','merge-base','--is-ancestor',older,newer],cwd=ROOT).returncode==0


def frozen(path: str,commit: str) -> None:
    if not (ROOT/path).is_file() or (ROOT/path).read_bytes()!=git('show',f'{commit}:{path}'):
        raise RuntimeError(f'frozen file changed: {path}')
    if git('status','--porcelain','--',path).strip():
        raise RuntimeError(f'uncommitted frozen file: {path}')


def source_paths(source_root: Path) -> dict[str,Path]:
    paths={}
    for role,record in [('gfdd',DATA_SOURCE),('meta',META_SOURCE),('gdp',GDP_SOURCE)]:
        path=source_root/record['path']
        if not path.is_file() or sha(path)!=record['sha256']:
            raise RuntimeError(f'missing/hash-mismatched pinned source: {role}')
        paths[role]=path
    manifest=ROOT/GDP_SOURCE['manifest']
    if not manifest.is_file() or sha(manifest)!=GDP_SOURCE['manifest_sha256']:
        raise RuntimeError('WDI GDP fetch manifest hash mismatch')
    entries=yaml.safe_load(manifest.read_text()).get('entries',[])
    matches=[row for row in entries if row.get('publisher')==GDP_SOURCE['publisher']
        and row.get('series_id')==GDP_SOURCE['series_id']
        and row.get('parquet_path')==GDP_SOURCE['path']
        and row.get('sha256')==GDP_SOURCE['sha256']]
    if len(matches)!=1:
        raise RuntimeError('WDI GDP manifest lacks exact source entry')
    gfdd_columns=set(pq.ParquetFile(paths['gfdd']).schema_arrow.names)
    required={'Country Code','Indicator Code'}|{str(y) for y in range(1995,2016)}
    if not required.issubset(gfdd_columns):
        raise RuntimeError('GFDD selected key/value schema missing')
    if not {'Series Code','Indicator Name','Topic','Source'}.issubset(pq.ParquetFile(paths['meta']).schema_arrow.names):
        raise RuntimeError('GFDD metadata schema missing')
    if not {'country_iso3','indicator_id','year','value','obs_status'}.issubset(pq.ParquetFile(paths['gdp']).schema_arrow.names):
        raise RuntimeError('WDI GDP schema missing')
    return paths


def key_roster(paths: dict[str,Path]) -> list[tuple[str,str,int]]:
    # Only categorical row identities and year-column names; no numeric cells or null masks.
    gfdd=pq.read_table(paths['gfdd'],columns=['Country Code','Indicator Code']).to_pandas()
    if gfdd.duplicated(['Country Code','Indicator Code']).any():
        raise RuntimeError('duplicate GFDD country/indicator keys')
    wanted={cell[1] for cell in CELLS}|{CRISIS,CREDIT}
    iso={c.alpha_3 for c in pycountry.countries}
    gfdd_keys={(str(c),str(i)) for c,i in zip(gfdd['Country Code'],gfdd['Indicator Code']) if c in iso}
    meta=pq.read_table(paths['meta'],columns=['Series Code','Indicator Name','Topic','Source']).to_pandas()
    if meta['Series Code'].duplicated().any() or not wanted.issubset(set(meta['Series Code'])):
        raise RuntimeError('GFDD series metadata key mismatch')
    for _,code,label,_,_ in CELLS:
        found=meta.loc[meta['Series Code']==code,'Indicator Name']
        if len(found)!=1 or not re.sub(r'[^a-z0-9]','',str(found.iloc[0]).lower()).startswith(re.sub(r'[^a-z0-9]','',label.lower())):
            raise RuntimeError(f'GFDD series label changed: {code}')
    gdp=pq.read_table(paths['gdp'],columns=['country_iso3','indicator_id','year']).to_pandas()
    gdp=gdp[(gdp.country_iso3.isin(iso))&(gdp.indicator_id==GDP_SOURCE['series_id'])]
    if gdp.duplicated(['country_iso3','year']).any():
        raise RuntimeError('duplicate national GDP country/year key')
    gdp_keys={(str(c),int(y)) for c,y in zip(gdp.country_iso3,gdp.year)}
    rows=[(code,cell[1],t) for cell in CELLS for code in sorted(iso) for t in ANCHORS
        if all((code,indicator) in gfdd_keys for indicator in (cell[1],CRISIS,CREDIT))
        and (code,t) in gdp_keys]
    rows.sort()
    for cell in CELLS:
        subset=[row for row in rows if row[1]==cell[1]]
        if len(subset)!=KEY_ROWS_PER_CELL or len({row[0] for row in subset})!=KEY_COUNTRIES:
            raise RuntimeError(f'key-only roster envelope changed for {cell[1]}: {len(subset)}')
    return rows


def roster_bytes(rows: list[tuple[str,str,int]]) -> bytes:
    out=io.StringIO(); writer=csv.writer(out,lineterminator='\n')
    writer.writerow(['country_iso3','gfdd_indicator','anchor_year'])
    writer.writerows(rows)
    return out.getvalue().encode()


def loaded_roster(paths: dict[str,Path]) -> list[tuple[str,str,int]]:
    path=ROOT/ROSTER
    if sha(path)!=ROSTER_SHA:
        raise RuntimeError('frozen key-only roster hash changed')
    rows=key_roster(paths)
    if path.read_bytes()!=roster_bytes(rows):
        raise RuntimeError('frozen key-only roster differs from source identities')
    return rows


def threshold(cell: tuple) -> dict[str,Any]:
    return dict(family_id=FAMILY,family_size=len(CELLS),family_alpha=ALPHA,
        holm_alpha=ALPHA,p_max_two_sided=ALPHA,
        expected_beta_sign='-' if cell[3]<0 else '+',
        meaningful_beta_min_abs=MIN_ABS_BETA,
        source_key_roster_path=ROSTER,source_key_roster_sha256=ROSTER_SHA,
        source_lock_path=lock_rel(cell),source_sha256=DATA_SOURCE['sha256'],
        secondary_source_sha256=GDP_SOURCE['sha256'],
        min_valid_rows=MIN_ROWS,min_valid_countries=MIN_COUNTRIES,
        min_rows_per_anchor=MIN_PER_ANCHOR,min_future_crisis_windows=MIN_EVENTS,
        min_future_crisis_countries=MIN_EVENT_COUNTRIES,min_noncrisis_windows=MIN_NON_EVENTS,
        min_complete_anchors_per_country=MIN_COMPLETE_ANCHORS,
        indicator_min=0.0,indicator_max=cell[4],credit_level_min=0.0,
        credit_level_max=MAX_CREDIT_LEVEL,
        max_abs_prior_credit_change_pp=MAX_ABS_PRIOR_CREDIT_CHANGE,
        min_residual_standardized_indicator_sd=MIN_RESIDUAL_X_SD,
        min_residual_crisis_sd=MIN_RESIDUAL_Y_SD,
        max_top_one_percent_indicator_ss_share=MAX_TOP_ONE_PERCENT_SS,
        max_top_country_indicator_ss_share=MAX_TOP_COUNTRY_SS,
        min_fold_rows=MIN_FOLD_ROWS,min_fold_countries=MIN_FOLD_COUNTRIES,
        min_same_sign_hash_folds=MIN_SAME_SIGN_FOLDS,
        causal_credit=0,policy_score_eligible=False,policy_score_credit=0,
        school_score_eligible=False,school_score_credit=0,featured_eligible=False)


def specification(cell: tuple,rows: list[tuple[str,str,int]]) -> dict[str,Any]:
    countries=sorted({row[0] for row in rows if row[1]==cell[1]})
    direction='lower' if cell[3]<0 else 'higher'
    sign='-' if cell[3]<0 else '+'
    return {'hypothesis_id':hid(cell),'version':1,'status':'pre_registered',
        'topic':'regulatory','claim_direction':sign,
        'claim':(f'Across frozen country windows anchored in 2000, 2005 and 2010, a higher '
            f'baseline {cell[2].lower()} predicts {direction} probability of a new '
            'systemic banking-crisis onset during t+1..t+5, conditional on prior private-credit/GDP '
            'level and five-year change, baseline real income, and country/anchor effects.'),
        'evidence_type':'associational',
        'methodology_note':('One cell of a prospective eight-signal GFDD bank-balance-sheet family. '
            'Before registration, only file hashes, official metadata, categorical indicator/country '
            'identities and year-column keys were inspected. Selected values, null masks, crisis flags, '
            'signs and estimates remain sealed until eight separate source-lock commits.'),
        'sample':{'countries':countries,'period':[2000,2015],'temporal_structure':'panel',
            'exclusion_rules':[
                'Use only the frozen key-only GFDD country/indicator/anchor roster at t=2000, 2005, 2010. Require exact GFDD source columns at predictor t, private-credit/GDP t−5/t and banking-crisis dummy t..t+5, plus WDI GDP per capita at t.',
                'After registration and all source locks, retain only at-risk windows with baseline crisis dummy exactly 0 and all five future crisis flags present and binary 0/1. A future onset is a 0-to-1 transition across the t through t+5 sequence; missing future flags never become non-events.',
                f'Predictor must be finite in [0,{cell[4]}]; private-credit/GDP endpoints finite in [0,{MAX_CREDIT_LEVEL}] and absolute five-year change <= {MAX_ABS_PRIOR_CREDIT_CHANGE}; real GDP per capita finite and positive. Keep countries with at least two complete anchors.',
                'No interpolation, missing-as-zero crisis recoding, winsorization, outcome-driven country selection, source substitution or post-result model, threshold or window change.'
            ]},
        'variables':{'treatment':[{'name':f'baseline_{cell[0]}_standardized',
            'source':f'gfdd:{cell[1]}','transformation':(
                f'GFDD {cell[2]} level at t, standardized by complete-case pooled mean and '
                f'population SD after the frozen [0,{cell[4]}] admissibility bound; +1 unit is +1 SD.'),
            'notes':'Country-level banking-system signal, not a policy intervention.'}],
            'outcome':[{'name':'systemic_banking_crisis_onset_next_five_years',
                'source':f'gfdd:{CRISIS}',
                'transformation':'Binary 0-to-1 transition from t through t+5, with all five future annual flags required and baseline t equal to 0.',
                'notes':'GFDD mirrors Laeven–Valencia systemic-crisis year coding; one or more later crisis spells in a window count once.'}],
            'controls':[{'name':'baseline_private_credit_gdp_share','source':f'gfdd:{CREDIT}',
                'transformation':'Percent of GDP at t.'},
                {'name':'prior_private_credit_gdp_change','source':f'gfdd:{CREDIT}',
                'transformation':'Credit/GDP percentage-point difference t minus t−5.'},
                {'name':'baseline_log_real_gdp_per_person','source':'world_bank_wdi:NY.GDP.PCAP.KD',
                'transformation':'Natural log constant-2015-dollar GDP per person at t.'}]},
        'estimator':{'template':'panel_fe','fixed_effects':['country','anchor_year'],
            'clustering':'country','notes':(
                'Equal country-window linear-probability OLS on one standardized bank indicator, '
                'baseline credit level/change, log real income, country and anchor-year fixed effects. '
                'Country-cluster CR1 uncertainty with two-sided Student t(G−1); eight-cell Holm correction. '
                'Five fixed country hash-fold omissions test sign stability. No causal estimate.')},
        'falsification':{'test':'gfdd_bank_resilience_crisis_2026_10_10',
            'rule':('INCONCLUSIVE if source chronology, complete at-risk outcome, rows/countries/anchor/event, '
                'variation, influence, rank, cluster-uncertainty or fold-coverage gates fail. '
                f'SUPPORTED iff coefficient has registered {sign} sign, at least 0.03 absolute crisis '
                'probability points per +1 predictor SD, Holm-adjusted two-sided p<=0.05 across all '
                'eight cells (inconclusive cells count p=1), and at least four of five fixed omitted-country '
                'folds share the registered sign. REFUTED iff the same requirements hold in the opposite '
                'direction. Otherwise PARTIAL.'),
            'threshold':threshold(cell)},
        'prior_confidence':0.5,
        'disclosure':('Eight correlated bank signals share outcome and many countries; Holm adjusts this '
            'family only. Existing IESET crisis predictors make archive-wide selection salient. Bank '
            'metrics and crisis dating are observational, and GFDD lacks a tracked fetch manifest. '
            'No causal, policy, school, position or featured credit.'),
        'steelman':steel_rel(cell),
        'scope':{'period':[2000,2015],'countries':countries,'outcome_dim':['financial_crisis'],
            'policy_family':['none'],'treatment_tags':[f'gfdd_{cell[0]}_baseline']},
        'covers_claims':[],'linked_hypotheses':[],'linked_conditions':[]}


def plan_text() -> str:
    lines=['# Prospective GFDD bank resilience → later systemic crisis', '',
        'This is one correlated eight-cell descriptive research family. Seven indicators are the complete frozen GFDD Stability topic SI.01–SI.07; the eighth is bank cost-to-income EI.07, an explicit operating-efficiency stress signal. Existing IESET credit-boom and macro-warning claims are separate; each cell conditions on the prior private-credit level and five-year change.', '',
        '## Key-only freeze', '',
        f'Each cell has {KEY_ROWS_PER_CELL} key rows across {KEY_COUNTRIES} ISO3 countries at 2000, 2005 and 2010. The wide GFDD data has a full country×indicator×year grid, so this roster is only an upper bound. Before this registration, only file hashes, schema/indicator metadata, country/series labels and year-column names were read. No selected numeric value, null mask, future crisis flag or estimate was opened.', '',
        'All eight hypotheses, steelmen, this plan, the runner and the 5,088-row roster are committed together. Each source lock is a later separate commit. The measured run must follow every lock and retain all eight cells, including design failures. The source hash, five-year windows, model, signs, bounds, complete-case floor, influence gates, five hash folds and Holm family size are fixed in the runner and specifications.', '',
        '## Outcome and inference', '',
        'At each anchor t, require the GFDD systemic-banking-crisis dummy to be 0 at baseline and present as 0/1 for every year t+1 through t+5; an onset is a 0-to-1 transition in that six-year sequence. The fixed floor is at least 10 onset windows across at least 8 countries per cell. Use country/anchor fixed-effect linear probability models with baseline private-credit level, prior five-year credit change and baseline real income. Country-cluster CR1 uncertainty, two-sided Student t(G−1), Holm alpha .05 across eight cells; unavailable or inconclusive cells enter Holm with p=1. Registered directional effect size is 0.03 probability points per +1 predictor SD, plus four-of-five fixed country-fold signs. Failed design gates are INCONCLUSIVE.', '',
        '## Custody and limits', '',
        'The pinned GFDDData and GFDDSeries parquet SHA-256 hashes are exact local locks and their metadata agrees with the official World Bank GFDD indicator glossary. This older local corpus has no tracked fetch manifest, so the precise original download transaction cannot be reconstructed. WDI GDP per capita has an exact tracked fetch manifest. No raw GFDD values are published. These are descriptive early-warning signals, not prudential-policy effects; no causal, policy, school, position or featured credit.', '',
        '| Cell | GFDD indicator | Registered sign |', '| --- | --- | --- |']
    lines += [f'| {name} | {code} {label} | {"negative" if sign<0 else "positive"} |' for name,code,label,sign,_ in CELLS]
    return '\n'.join(lines)+'\n'


def steel_text(cell: tuple) -> str:
    idea=('A stronger capital, liquidity or provisioning buffer plausibly absorbs losses before a systemic crisis.'
        if cell[3]<0 else 'A higher distressed-loan, credit-to-deposit or operating-cost ratio plausibly signals fragility before a systemic crisis.')
    return (f'# Steelman: {cell[2]} and later systemic banking crisis\n\n'
        f'**Registered ID:** `{hid(cell)}`. {idea} The registered sign is '
        f'{"negative" if cell[3]<0 else "positive"} for the next five-year crisis indicator. '
        'The signal is evaluated beyond prior credit depth and growth, baseline income, country and anchor effects.\n\n'
        'A countermechanism is plausible: stronger buffers may be built in anticipation of distress, while efficient or aggressive banks can earn high ratios before a crash. Accounting and country coverage differ across GFDD component sources. The linear-probability coefficient is descriptive, with eight-cell Holm correction and fixed influence, event-count and hash-fold gates. It cannot be interpreted as a causal effect of regulation or a policy recommendation.\n')


def write_registration(paths: dict[str,Path]) -> None:
    rows=key_roster(paths)
    if hashlib.sha256(roster_bytes(rows)).hexdigest()!=ROSTER_SHA:
        raise RuntimeError('key roster hash differs from frozen runner constant')
    files=[RUNNER,PLAN,ROSTER]+[p for cell in CELLS for p in (spec_rel(cell),steel_rel(cell))]
    if any((ROOT/p).exists() for p in files if p!=RUNNER):
        raise FileExistsError('registration artifact exists')
    schema=json.loads((ROOT/'schemas/hypothesis.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    for cell in CELLS:
        spec=specification(cell,rows)
        errors=list(Draft202012Validator(schema).iter_errors(spec))
        if errors:
            raise RuntimeError(f'{hid(cell)} schema: {[e.message for e in errors[:3]]}')
    for path in files:
        (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/PLAN).write_text(plan_text())
    (ROOT/ROSTER).write_bytes(roster_bytes(rows))
    for cell in CELLS:
        (ROOT/spec_rel(cell)).write_bytes(b'# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n'+ya(specification(cell,rows)))
        (ROOT/steel_rel(cell)).write_text(steel_text(cell))


def registration_commit(paths: dict[str,Path]) -> str:
    files=[RUNNER,PLAN,ROSTER]+[p for cell in CELLS for p in (spec_rel(cell),steel_rel(cell))]
    commits={first_add(p) for p in files}
    if len(commits)!=1:
        raise RuntimeError(f'family registration not in one first commit: {commits}')
    commit=commits.pop()
    for p in files: frozen(p,commit)
    if git('ls-tree','-r','--name-only',commit,'--',*[lock_rel(c) for c in CELLS],*[run_rel(c) for c in CELLS]).strip():
        raise RuntimeError('registration commit contained a source lock or result')
    rows=loaded_roster(paths)
    schema=json.loads(git('show',f'{commit}:schemas/hypothesis.schema.json'))
    Draft202012Validator.check_schema(schema)
    for cell in CELLS:
        spec=yaml.safe_load((ROOT/spec_rel(cell)).read_text())
        if spec!=specification(cell,rows) or not Draft202012Validator(schema).is_valid(spec):
            raise RuntimeError(f'frozen original registration invalid: {hid(cell)}')
    return commit


def lock_payload(cell: tuple,registration: str) -> dict[str,Any]:
    return dict(hypothesis_id=hid(cell),family_id=FAMILY,family_size=len(CELLS),
        registration_commit=registration,source_sha256=DATA_SOURCE['sha256'],
        metadata_sha256=META_SOURCE['sha256'],secondary_source_sha256=GDP_SOURCE['sha256'],
        key_roster_sha256=ROSTER_SHA,key_roster_path=ROSTER,
        sources=[DATA_SOURCE,META_SOURCE,GDP_SOURCE],
        selected_values_or_null_masks_read_before_locks=False,
        provenance_limit='GFDD local parquet files have SHA pins and official series metadata but no tracked fetch manifest.')


def write_lock(cell: tuple,registration: str) -> None:
    path=ROOT/lock_rel(cell)
    if path.exists(): raise FileExistsError(str(path))
    path.write_bytes(js(lock_payload(cell,registration)))


def lock_commits(registration: str) -> dict[str,str]:
    commits={}
    previous=registration
    for cell in CELLS:
        path=lock_rel(cell)
        commit=first_add(path)
        if not ancestor(previous,commit):
            raise RuntimeError(f'source locks must be separate ordered commits: {path}')
        names=git('diff-tree','--no-commit-id','--name-only','-r',commit).decode().splitlines()
        if names!=[path]:
            raise RuntimeError(f'source lock commit contains other files: {path}')
        frozen(path,commit)
        if json.loads((ROOT/path).read_text())!=lock_payload(cell,registration):
            raise RuntimeError(f'locked source metadata differs: {path}')
        if git('ls-tree','-r','--name-only',commit,'--',*[run_rel(c) for c in CELLS]).strip():
            raise RuntimeError('source lock already contains measured result')
        commits[hid(cell)]=commit
        previous=commit
    return commits


def selected_values(paths: dict[str,Path]) -> tuple[dict[tuple[str,str,int],float],dict[tuple[str,int],float]]:
    # The only selected numeric/null-mask access; caller has checked all committed locks.
    codes={c[1] for c in CELLS}|{CRISIS,CREDIT}
    yearcols={str(y) for t in ANCHORS for y in range(t-5,t+6)}
    frame=pq.read_table(paths['gfdd'],columns=['Country Code','Indicator Code']+sorted(yearcols)).to_pandas()
    frame=frame[frame['Indicator Code'].isin(codes)]
    if frame.duplicated(['Country Code','Indicator Code']).any():
        raise RuntimeError('duplicate selected GFDD series key')
    values={(str(row['Country Code']),str(row['Indicator Code']),int(year)):float(row[year])
        for _,row in frame.iterrows() for year in yearcols}
    gdp=pq.read_table(paths['gdp'],columns=['country_iso3','indicator_id','year','value','obs_status']).to_pandas()
    gdp=gdp[gdp.indicator_id==GDP_SOURCE['series_id']]
    if gdp.duplicated(['country_iso3','year']).any():
        # WDI aggregate rows with empty ISO key can duplicate; never use those.
        gdp=gdp[gdp.country_iso3.ne('')]
        if gdp.duplicated(['country_iso3','year']).any():
            raise RuntimeError('duplicate selected national GDP key')
    bad=gdp.obs_status.fillna('').astype(str).map(lambda x:x not in ('','A'))
    gdp.loc[bad,'value']=float('nan')
    income={(str(c),int(y)):float(v) for c,y,v in zip(gdp.country_iso3,gdp.year,gdp.value)}
    return values,income


def measured_panel(cell: tuple,roster: list[tuple[str,str,int]],
        values: dict[tuple[str,str,int],float],income: dict[tuple[str,int],float]) -> tuple[pd.DataFrame,dict[str,Any]]:
    rows=[]; dropped=Counter()
    for country,code,t in roster:
        if code!=cell[1]: continue
        x=values[(country,code,t)]
        credit0=values[(country,CREDIT,t-5)]
        credit1=values[(country,CREDIT,t)]
        base_crisis=values[(country,CRISIS,t)]
        future=[values[(country,CRISIS,y)] for y in range(t+1,t+6)]
        gdp=income.get((country,t),float('nan'))
        if not all(map(math.isfinite,[x,credit0,credit1,base_crisis,*future,gdp])):
            dropped['missing_or_nonfinite']+=1; continue
        if base_crisis!=0 or any(flag not in (0,1) for flag in future):
            dropped['not_at_risk_or_nonbinary_crisis']+=1; continue
        if not (0<=x<=cell[4]):
            dropped['indicator_range']+=1; continue
        if not (0<=credit0<=MAX_CREDIT_LEVEL and 0<=credit1<=MAX_CREDIT_LEVEL
                and abs(credit1-credit0)<=MAX_ABS_PRIOR_CREDIT_CHANGE):
            dropped['credit_range']+=1; continue
        if not gdp>0:
            dropped['gdp_range']+=1; continue
        flags=[base_crisis,*future]
        onset=any(a==0 and b==1 for a,b in zip(flags,flags[1:]))
        rows.append(dict(country_iso3=country,anchor_year=t,x_raw=x,y=int(onset),
            credit_level=credit1,prior_credit_change=credit1-credit0,log_income=math.log(gdp)))
    panel=pd.DataFrame(rows,columns=['country_iso3','anchor_year','x_raw','y',
        'credit_level','prior_credit_change','log_income'])
    counts=panel.country_iso3.value_counts()
    below=panel.country_iso3.map(counts).lt(MIN_COMPLETE_ANCHORS)
    dropped['country_below_two_anchors']+=int(below.sum())
    panel=panel.loc[~below].sort_values(['country_iso3','anchor_year']).reset_index(drop=True)
    events=panel[panel.y==1]
    gate=dict(key_roster_rows=KEY_ROWS_PER_CELL,key_roster_countries=KEY_COUNTRIES,
        complete_rows_before_country_floor=len(rows),valid_rows=len(panel),
        valid_countries=int(panel.country_iso3.nunique()),
        rows_per_anchor={str(t):int((panel.anchor_year==t).sum()) for t in ANCHORS},
        future_crisis_windows=len(events),future_crisis_countries=int(events.country_iso3.nunique()),
        noncrisis_windows=int((panel.y==0).sum()),dropped=dict(sorted(dropped.items())),
        selected_values_read_after_committed_locks=True)
    return panel,gate


def residual_formula(outcome: str) -> str:
    return f'{outcome} ~ credit_level + prior_credit_change + log_income + C(country_iso3) + C(anchor_year)'


def model_formula() -> str:
    return 'y ~ x + credit_level + prior_credit_change + log_income + C(country_iso3) + C(anchor_year)'


def estimate(panel: pd.DataFrame,gate: dict[str,Any]) -> dict[str,Any]:
    failures=[]
    if gate['valid_rows']<MIN_ROWS: failures.append('min_valid_rows')
    if gate['valid_countries']<MIN_COUNTRIES: failures.append('min_valid_countries')
    if min(gate['rows_per_anchor'].values())<MIN_PER_ANCHOR: failures.append('min_rows_per_anchor')
    if gate['future_crisis_windows']<MIN_EVENTS: failures.append('min_future_crisis_windows')
    if gate['future_crisis_countries']<MIN_EVENT_COUNTRIES: failures.append('min_future_crisis_countries')
    if gate['noncrisis_windows']<MIN_NON_EVENTS: failures.append('min_noncrisis_windows')
    if failures:
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    mean=float(panel.x_raw.mean());sd=float(panel.x_raw.std(ddof=0))
    if not math.isfinite(sd) or sd<=0:
        failures.append('nonzero_pooled_indicator_sd')
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    panel=panel.copy();panel['x']=(panel.x_raw-mean)/sd
    xmodel=smf.ols(residual_formula('x'),data=panel)
    ymodel=smf.ols(residual_formula('y'),data=panel)
    if (np.linalg.matrix_rank(xmodel.exog)!=xmodel.exog.shape[1]
            or np.linalg.matrix_rank(ymodel.exog)!=ymodel.exog.shape[1]):
        failures.append('residual_design_rank')
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    rx=np.asarray(xmodel.fit().resid,float);ry=np.asarray(ymodel.fit().resid,float)
    ss=rx**2;total=float(ss.sum());xsd=math.sqrt(total/len(rx)) if total>0 else 0.0
    ysd=float(np.sqrt(np.mean(ry**2)))
    top=max(1,math.ceil(.01*len(rx)))
    top_share=float(sum(sorted(ss,reverse=True)[:top])/total) if total>0 else 1.0
    country_share=float(panel.assign(ss=ss).groupby('country_iso3').ss.sum().max()/total) if total>0 else 1.0
    gate.update(indicator_pooled_mean=mean,indicator_pooled_sd=sd,
        residual_standardized_indicator_sd=xsd,residual_crisis_sd=ysd,
        top_one_percent_indicator_ss_share=top_share,top_country_indicator_ss_share=country_share)
    if xsd<MIN_RESIDUAL_X_SD: failures.append('min_residual_indicator_sd')
    if ysd<MIN_RESIDUAL_Y_SD: failures.append('min_residual_crisis_sd')
    if top_share>MAX_TOP_ONE_PERCENT_SS: failures.append('top_one_percent_indicator_concentration')
    if country_share>MAX_TOP_COUNTRY_SS: failures.append('top_country_indicator_concentration')
    if failures:
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    model=smf.ols(model_formula(),data=panel)
    if np.linalg.matrix_rank(model.exog)!=model.exog.shape[1]:
        failures.append('primary_design_rank')
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    groups=int(panel.country_iso3.nunique())
    fit=model.fit(cov_type='cluster',cov_kwds={'groups':panel.country_iso3,
        'use_correction':True,'df_correction':True},use_t=True)
    beta,se=float(fit.params['x']),float(fit.bse['x'])
    if not (math.isfinite(beta) and math.isfinite(se) and se>0):
        failures.append('finite_cluster_uncertainty')
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    p=float(2*student_t.sf(abs(beta/se),groups-1))
    critical=float(student_t.ppf(.995,groups-1))
    if not (math.isfinite(p) and math.isfinite(critical)):
        failures.append('finite_t_inference')
        return dict(sample=gate,primary=None,hash_folds=[],gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    primary=dict(beta=beta,country_cluster_se=se,p_two_sided=p,
        confidence_level=.99,confidence_interval=[beta-critical*se,beta+critical*se],
        n_rows=len(panel),n_countries=groups,df_inference=groups-1,
        model_rank=int(fit.model.rank),model_columns=int(model.exog.shape[1]),
        indicator_pooled_sd=sd,residual_standardized_indicator_sd=xsd,
        residual_crisis_sd=ysd,top_one_percent_indicator_ss_share=top_share,
        top_country_indicator_ss_share=country_share,
        method='equal-row country/anchor FE linear probability OLS with prior credit level/change and log income; country CR1 cluster t(G-1)')
    folds=[]
    for omit in range(5):
        subset=panel[panel.country_iso3.map(lambda c:int(hashlib.sha256(c.encode()).hexdigest(),16)%5!=omit)]
        if len(subset)<MIN_FOLD_ROWS or subset.country_iso3.nunique()<MIN_FOLD_COUNTRIES:
            failures.append(f'fold_{omit}_coverage');continue
        fold=smf.ols(model_formula(),data=subset)
        if np.linalg.matrix_rank(fold.exog)!=fold.exog.shape[1]:
            failures.append(f'fold_{omit}_rank');continue
        fb=float(fold.fit().params['x'])
        if not math.isfinite(fb):
            failures.append(f'fold_{omit}_finite');continue
        folds.append(dict(omitted_hash_fold=omit,rows=len(subset),
            countries=int(subset.country_iso3.nunique()),beta=fb))
    if failures:
        return dict(sample=gate,primary=primary,hash_folds=folds,gate_failures=failures,holm_adjusted_p=1.0,verdict='INCONCLUSIVE')
    return dict(sample=gate,primary=primary,hash_folds=folds,gate_failures=[],holm_adjusted_p=None,verdict='PENDING_FAMILY')


def holm(results: dict[str,dict[str,Any]]) -> None:
    ranked=sorted((r['primary']['p_two_sided'] if r['primary'] is not None and not r['gate_failures'] else 1.0,h)
        for h,r in results.items())
    running=0.0;adjusted={}
    for rank,(p,h) in enumerate(ranked):
        running=max(running,min(1.0,(len(CELLS)-rank)*p))
        adjusted[h]=running
    for cell in CELLS:
        r=results[hid(cell)]
        if r['gate_failures']:
            r['holm_adjusted_p']=1.0;r['verdict']='INCONCLUSIVE';continue
        r['holm_adjusted_p']=adjusted[hid(cell)]
        beta=r['primary']['beta'];folds=r['hash_folds']
        same=sum(f['beta']*cell[3]>0 for f in folds)
        opposite=sum(f['beta']*cell[3]<0 for f in folds)
        r['same_direction_folds']=same;r['opposite_direction_folds']=opposite
        if beta*cell[3]>=MIN_ABS_BETA and adjusted[hid(cell)]<=ALPHA and same>=MIN_SAME_SIGN_FOLDS:
            r['verdict']='SUPPORTED'
        elif beta*cell[3]<=-MIN_ABS_BETA and adjusted[hid(cell)]<=ALPHA and opposite>=MIN_SAME_SIGN_FOLDS:
            r['verdict']='REFUTED'
        else:r['verdict']='PARTIAL'


def artifacts(cell: tuple,result: dict[str,Any],registration: str,
        locked: str,stamp: str) -> dict[str,bytes]:
    id=hid(cell)
    diagnostic=dict(hypothesis_id=id,family_id=FAMILY,family_size=len(CELLS),
        registration_commit=registration,source_lock_commit=locked,
        source_sha256=DATA_SOURCE['sha256'],secondary_source_sha256=GDP_SOURCE['sha256'],
        source_key_roster_sha256=ROSTER_SHA,runner=RUNNER,run_utc=stamp,
        indicator_code=cell[1],registered_direction=cell[3],thresholds=threshold(cell),
        result=result,limitations=LIMITS,correction=CREDIT_CORRECTION)
    diag_bytes=js(diagnostic)
    source=dict(publisher='World Bank Global Financial Development Database plus WDI GDP per capita',
        source_sha256=DATA_SOURCE['sha256'],metadata_sha256=META_SOURCE['sha256'],
        secondary_source_sha256=GDP_SOURCE['sha256'],source_lock_commit=locked,
        source_lock_manifest=lock_rel(cell),key_roster_sha256=ROSTER_SHA,
        input_vintages=[{'path':r['path'],'sha256':r['sha256']} for r in (DATA_SOURCE,META_SOURCE,GDP_SOURCE)],
        gfdd_fetch_manifest='not available in tracked corpus',
        license='GFDD public World Bank download; underlying source rights vary; only derived summary published',
        contains_source_values=False)
    manifest=dict(hypothesis_id=id,status=result['verdict'],run_utc=stamp,runner=RUNNER,
        preregistration_commit=registration,source=source,family_id=FAMILY,
        family_size=len(CELLS),sample=result['sample'],correction=CREDIT_CORRECTION)
    packet=dict(packet_version=1,hypothesis={'id':id,'path':spec_rel(cell)},
        preregistration={'commit':registration,'steelman':steel_rel(cell),
            'source_plan':PLAN,'key_roster':ROSTER},source=source,
        family={'id':FAMILY,'size':len(CELLS),'members':[hid(c) for c in CELLS],
            'holm_alpha':ALPHA,'interpretation':'Eight correlated bank signals with one future-crisis outcome'},
        reproduction={'runner':RUNNER,
            'command':f'python3 {RUNNER} verify --source-root /path/to/IESET',
            'result_sha256':hashlib.sha256(diag_bytes).hexdigest()},
        result=result,limitations=LIMITS,correction=CREDIT_CORRECTION)
    primary=result['primary']
    card=(f'# Result card: {id}\n\nVerdict: **{result["verdict"]}**. '
        f'Registered signal {cell[1]} ({cell[2]}), sign {"negative" if cell[3]<0 else "positive"}.\n\n'
        f'Registration `{registration}`; source lock `{locked}`. '
        f'Complete at-risk windows {result["sample"]["valid_rows"]} in '
        f'{result["sample"]["valid_countries"]} countries, including '
        f'{result["sample"]["future_crisis_windows"]} future-crisis windows.\n')
    if result['gate_failures']:
        card+=f'\nFrozen gate failures: {", ".join(result["gate_failures"])}.\n'
    if primary:
        card+=(f'\nBeta={primary["beta"]:+.6g} crisis-probability points per +1 predictor SD; '
            f'country-cluster SE={primary["country_cluster_se"]:.6g}; '
            f'two-sided p={primary["p_two_sided"]:.6g}; '
            f'Holm p={result["holm_adjusted_p"]:.6g}; 99% CI={primary["confidence_interval"]}.\n')
    card+='\nDescriptive early-warning calibration only; zero causal, policy, school, position or featured credit.\n'
    wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root=Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
    return {'diagnostics.json':diag_bytes,'manifest.yaml':ya(manifest),
        'evidence_packet.yaml':ya(packet),'result_card.md':card.encode(),
        'replication.py':wrapper.encode(),'hypothesis.yaml':(ROOT/spec_rel(cell)).read_bytes(),
        'chart_data.json':js({'hypothesis_id':id,'family_id':FAMILY,
            'verdict':result['verdict'],'primary':primary})}


def report_text(results: dict[str,dict[str,Any]],registration: str,locks: dict[str,str]) -> str:
    lines=['# GFDD bank resilience and later systemic-crisis onset: frozen results','',
        f'Registration `{registration}`; eight distinct source locks, from `{next(iter(locks.values()))}` through `{list(locks.values())[-1]}`.','',
        '| Signal | Verdict | At-risk rows / countries | Events / countries | Beta per +1 SD | Raw p | Holm p | Gate failures |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for cell in CELLS:
        r=results[hid(cell)];p=r['primary'];g=r['sample']
        lines.append(f'| {cell[2]} | {r["verdict"]} | {g["valid_rows"]} / {g["valid_countries"]} | '
            f'{g["future_crisis_windows"]} / {g["future_crisis_countries"]} | '
            f'{p["beta"]:+.5g} | {p["p_two_sided"]:.5g} | {r["holm_adjusted_p"]:.5g} | '
            f'{", ".join(r["gate_failures"]) or "none"} |' if p else
            f'| {cell[2]} | {r["verdict"]} | {g["valid_rows"]} / {g["valid_countries"]} | '
            f'{g["future_crisis_windows"]} / {g["future_crisis_countries"]} | — | — | 1 | '
            f'{", ".join(r["gate_failures"]) or "none"} |')
    lines+=['','The eight indicators share outcome and countries; Holm adjusts the frozen family only. '
        'Baseline data are observational signals, not bank-regulation treatments. '
        'GFDD raw parquet hashes are pinned but no tracked GFDD fetch manifest exists. '
        'No causal, policy, school, position or featured credit.','']
    return '\n'.join(lines)


def equal_close(a: Any,b: Any,label: str) -> None:
    if isinstance(b,dict):
        if not isinstance(a,dict) or set(a)!=set(b):raise AssertionError(f'{label}: keys differ')
        for k,v in b.items():equal_close(a[k],v,f'{label}.{k}')
    elif isinstance(b,list):
        if not isinstance(a,list) or len(a)!=len(b):raise AssertionError(f'{label}: list length differs')
        for i,v in enumerate(b):equal_close(a[i],v,f'{label}[{i}]')
    elif isinstance(b,float):
        if not math.isfinite(float(a)) or not math.isclose(float(a),b,rel_tol=1e-9,abs_tol=1e-11):
            raise AssertionError(f'{label}: numeric mismatch')
    elif a!=b:raise AssertionError(f'{label}: value differs')


def write_results(results: dict[str,dict[str,Any]],registration: str,locks: dict[str,str]) -> None:
    if (ROOT/REPORT).exists() or any((ROOT/run_rel(c)).exists() for c in CELLS):
        raise FileExistsError('measured family artifact already exists')
    stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for cell in CELLS:
        folder=ROOT/run_rel(cell);folder.mkdir(parents=True)
        for name,content in artifacts(cell,results[hid(cell)],registration,locks[hid(cell)],stamp).items():
            (folder/name).write_bytes(content)
    (ROOT/REPORT).write_text(report_text(results,registration,locks))


def verify_results(results: dict[str,dict[str,Any]],registration: str,locks: dict[str,str]) -> None:
    for cell in CELLS:
        folder=ROOT/run_rel(cell)
        saved=json.loads((folder/'diagnostics.json').read_text())
        expected=artifacts(cell,results[hid(cell)],registration,locks[hid(cell)],saved['run_utc'])
        for name,content in expected.items():
            path=folder/name
            if name.endswith('.json'):
                equal_close(json.loads(path.read_text()),json.loads(content),f'{hid(cell)}:{name}')
            elif name.endswith('.yaml') and name!='hypothesis.yaml':
                equal_close(yaml.safe_load(path.read_text()),yaml.safe_load(content),f'{hid(cell)}:{name}')
            elif path.read_bytes()!=content:
                raise AssertionError(f'exact replay mismatch: {path}')
    if (ROOT/REPORT).read_text()!=report_text(results,registration,locks):
        raise AssertionError('family result report differs from exact replay')


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action',choices=['preflight','register','lock','measure','verify'])
    parser.add_argument('--source-root',type=Path,default=ROOT)
    parser.add_argument('--cell',choices=[c[0] for c in CELLS])
    args=parser.parse_args()
    paths=source_paths(args.source_root)
    if args.action=='preflight':
        rows=key_roster(paths)
        print(json.dumps({'family_size':len(CELLS),'key_only_rows':len(rows),
            'key_only_rows_per_cell':KEY_ROWS_PER_CELL,'key_only_countries_per_cell':KEY_COUNTRIES,
            'anchors':ANCHORS,'selected_values_opened':False},sort_keys=True))
        return 0
    if args.action=='register':
        write_registration(paths)
        print('wrote eight-cell registration from source keys only; commit before locks')
        return 0
    registration=registration_commit(paths)
    if args.action=='lock':
        if args.cell is None:raise ValueError('--cell required for each distinct lock')
        cell=next(c for c in CELLS if c[0]==args.cell)
        index=CELLS.index(cell)
        if index:
            prior=CELLS[index-1]
            if not (ROOT/lock_rel(prior)).exists() or not ancestor(registration,first_add(lock_rel(prior))):
                raise RuntimeError('prior family source lock must already be committed')
        write_lock(cell,registration)
        print(f'wrote source lock for {hid(cell)}; commit this lock alone')
        return 0
    locks=lock_commits(registration)
    roster=loaded_roster(paths)
    values,income=selected_values(paths)
    results={}
    for cell in CELLS:
        panel,gate=measured_panel(cell,roster,values,income)
        results[hid(cell)]=estimate(panel,gate)
    holm(results)
    if args.action=='measure':
        write_results(results,registration,locks)
        print(json.dumps({'family_id':FAMILY,'results':{h:{'verdict':r['verdict'],
            'rows':r['sample']['valid_rows'],'countries':r['sample']['valid_countries'],
            'events':r['sample']['future_crisis_windows'],'gate_failures':r['gate_failures'],
            'beta':r['primary']['beta'] if r['primary'] else None,
            'p':r['primary']['p_two_sided'] if r['primary'] else None,
            'holm_p':r['holm_adjusted_p']} for h,r in results.items()}},indent=2))
    else:
        verify_results(results,registration,locks)
        print('verified exact replay',FAMILY,{h:r['verdict'] for h,r in results.items()})
    return 0


if __name__=='__main__':
    raise SystemExit(main())
