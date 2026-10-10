#!/usr/bin/env python3
"""Frozen eight-cell WDI resource-rent to later sector-growth family.

Preflight, registration and locks read exact source hashes, manifests, schemas and
country/year identities only. Selected values and null masks are first read by
measure, after registration and all eight source locks are committed.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,subprocess
from collections import Counter
from datetime import datetime,timezone
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
FAMILY='wdi_resource_rents_future_sector_growth_2026_10_10'
RUNNER='scripts/run_wdi_resource_rents_sector_growth_2026.py'
PLAN='engine/audits/wdi_resource_rents_sector_growth_prereg_2026-10-10.md'
REPORT='engine/audits/wdi_resource_rents_sector_growth_results_2026-10-10.md'
ROSTER='data/pinned_evidence/wdi_resource_rents_sector_growth_2026_key_roster.csv'
ROSTER_SHA='2e82530b40d9383e8444eed52e57b7143841a0766471bf8352b0a8ad54738309'
BOOT='data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml'
GAS_MAN='data/manifests/fetch_run_2026-04-30T144015Z.yaml'
GDP_MAN='data/manifests/fetch_run_2026-05-05T200056Z.yaml'
MANIFEST_HASHES={BOOT:'e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e',
    GAS_MAN:'f3dd70400d87c379eedfb9727462307f2c972646666168883113bd9a38588572',
    GDP_MAN:'a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945'}
def record(code,file,hash,manifest):
    return dict(series_id=code,path=f'data/vintages/world_bank_wdi/{file}',sha256=hash,
        publisher='world_bank_wdi',manifest=manifest,
        source_url=f'https://data.worldbank.org/indicator/{code}',license='CC BY 4.0')
SOURCES={
 'total':record('NY.GDP.TOTL.RT.ZS','NY.GDP.TOTL.RT.ZS@2026-04-30T115056Z.parquet','db6778300a832f2f90f3855b5583293007ca9b5c7760e52904ba0da493b7ccd2',BOOT),
 'oil':record('NY.GDP.PETR.RT.ZS','NY.GDP.PETR.RT.ZS@2026-04-30T115050Z.parquet','15d64d3d8c333989208fd524b13ce58103d0a79ba38aa83a36e030014d2aaa3e',BOOT),
 'gas':record('NY.GDP.NGAS.RT.ZS','NY.GDP.NGAS.RT.ZS@2026-04-30T143734Z.parquet','7518375757dbc58355e3fff0026216d4ad471a48782a5cdef13c2402bdc0d2e6',GAS_MAN),
 'mineral':record('NY.GDP.MINR.RT.ZS','NY.GDP.MINR.RT.ZS@2026-04-30T115036Z.parquet','db8a50980b94565820a21e955d3ddb2c26e0e54f6eef74467e06ba0c3e4a0b64',BOOT),
 'manufacturing':record('NV.IND.MANF.KD','NV.IND.MANF.KD@2026-04-30T115022Z.parquet','fc4f4fcf319edbb0fba84ee91ec3e7780b84328a72abd36330feda40dbfad0b9',BOOT),
 'services':record('NV.SRV.TOTL.KD','NV.SRV.TOTL.KD@2026-04-30T151128Z.parquet','d6209478a5f209eecd9cb6ea8440f34ec6cfcc8efa4f4846e8f7fa69e2fa9330',None),
 'income':record('NY.GDP.PCAP.KD','NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet','0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f',GDP_MAN),
}
FAMILY_SOURCE_SHA=hashlib.sha256('|'.join(SOURCES[k]['sha256'] for k in SOURCES).encode()).hexdigest()
RENTS=(('total','Total natural resource rents'),('oil','Oil rents'),('gas','Natural gas rents'),('mineral','Mineral rents'))
SECTORS=(('manufacturing','Real manufacturing value added',-1),('services','Real services value added',+1))
CELLS=tuple((rent,sector,label,slabel,sign) for rent,label in RENTS for sector,slabel,sign in SECTORS)
ANCHORS=(1995,2000,2005,2010)
KEY_COUNTRIES=215
KEY_ROWS_PER_CELL=860
ALPHA=.05
MIN_ABS_BETA=.03 # log points of cumulative five-year sector growth per +1 pooled SD rent
MIN_ROWS=160
MIN_COUNTRIES=60
MIN_PER_ANCHOR=30
MIN_COMPLETE_ANCHORS=2
MIN_RESIDUAL_X_SD=.15
MIN_RESIDUAL_Y_SD=.04
MAX_TOP_ONE_PERCENT_X_SS=.35
MAX_TOP_COUNTRY_X_SS=.25
MAX_TOP_ONE_PERCENT_Y_SS=.35
MAX_TOP_COUNTRY_Y_SS=.25
MIN_FOLD_ROWS=110
MIN_FOLD_COUNTRIES=40
MIN_SAME_SIGN_FOLDS=4
MAX_RENT=100.0
CORRECTION=dict(disposition='descriptive_calibration_only',causal_credit=0,
    policy_score_eligible=False,policy_score_credit=0,school_score_eligible=False,
    school_score_credit=0,featured_eligible=False)
LIMITS=[
 'Resource rents are modeled World Bank estimates of commodity value less extraction cost divided by current GDP; they are not randomized treatment or a fiscal-revenue measure.',
 'Total rent includes oil, gas, minerals, coal and forest rents; the four predictors are correlated and belong to one eight-cell Holm family.',
 'Real sector value added is a national-accounts series in constant 2015 US dollars; cross-country level comparability and methodological breaks can affect growth measures.',
 'Country/anchor effects, baseline income, sector scale and prior sector growth cannot remove commodity-price, investment, exchange-rate or institutional confounding.',
 'The local services-value-added parquet has an exact SHA pin but no tracked fetch manifest; its original download transaction is not independently reconstructed.',
 'The frozen 1995–2010 anchors yield nonoverlapping 1995–2000, 2000–2005, 2005–2010 and 2010–2015 follow-up intervals; no pandemic period is included.',
 'No causal, school, policy, position or featured credit is assigned; Holm corrects this family, not every earlier IESET resource question.'
]

def hid(cell):return f'wdi_{cell[0]}_rent_{cell[1]}_growth_2026'
def spec_rel(cell):return f'hypotheses/resource_rents/{hid(cell)}.yaml'
def steel_rel(cell):return f'hypotheses/steelman/{hid(cell)}.md'
def lock_rel(cell):return f'data/pinned_evidence/{hid(cell)}.source.json'
def run_rel(cell):return f'engine/runs/{hid(cell)}'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def js(v):return (json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def ya(v):return yaml.safe_dump(v,sort_keys=False,allow_unicode=True,width=100).encode()
def git(*args):
 p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True)
 if p.returncode:raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode(errors='replace')}")
 return p.stdout
def first_add(path):
 commits=git('log','--diff-filter=A','--reverse','--format=%H','HEAD','--',path).decode().splitlines()
 if len(commits)!=1:raise RuntimeError(f'expected one first-addition commit for {path}: {commits}')
 return commits[0]
def ancestor(a,b):return a!=b and subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT).returncode==0
def frozen(path,commit):
 if not (ROOT/path).is_file() or (ROOT/path).read_bytes()!=git('show',f'{commit}:{path}'):
  raise RuntimeError(f'frozen file changed: {path}')
 if git('status','--porcelain','--',path).strip():raise RuntimeError(f'uncommitted frozen file: {path}')

def source_paths(source_root):
 paths={}
 for role,record in SOURCES.items():
  p=source_root/record['path']
  if not p.is_file() or sha(p)!=record['sha256']:raise RuntimeError(f'missing/hash-mismatched pinned source: {role}')
  paths[role]=p
  fields=set(pq.ParquetFile(p).schema_arrow.names)
  if not {'country_iso3','indicator_id','year','value','obs_status'}.issubset(fields):raise RuntimeError(f'source schema missing: {role}')
 for m,h in MANIFEST_HASHES.items():
  p=ROOT/m
  if not p.is_file() or sha(p)!=h:raise RuntimeError(f'tracked WDI fetch manifest hash changed: {m}')
  entries=yaml.safe_load(p.read_text()).get('entries',[])
  for role,rec in SOURCES.items():
   if rec['manifest']!=m:continue
   matches=[e for e in entries if e.get('publisher')==rec['publisher'] and e.get('series_id')==rec['series_id'] and e.get('parquet_path')==rec['path'] and e.get('sha256')==rec['sha256']]
   if len(matches)!=1:raise RuntimeError(f'WDI manifest lacks exact source entry: {role}')
 return paths

def key_roster(paths):
 iso={c.alpha_3 for c in pycountry.countries};keys={}
 for role,p in paths.items():
  d=pq.read_table(p,columns=['country_iso3','indicator_id','year']).to_pandas()
  if set(d.indicator_id.dropna())!={SOURCES[role]['series_id']}:raise RuntimeError(f'wrong indicator identity: {role}')
  d=d[d.country_iso3.isin(iso)]
  if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate national source key: {role}')
  keys[role]={(str(c),int(y)) for c,y in zip(d.country_iso3,d.year)}
 rows=[]
 for cell in CELLS:
  rent,sector=cell[:2]
  for c in sorted(iso):
   for t in ANCHORS:
    if ((c,t) in keys[rent] and (c,t) in keys['income'] and
        all((c,y) in keys['manufacturing'] and (c,y) in keys['services'] for y in (t-5,t,t+5))):
     rows.append((c,SOURCES[rent]['series_id'],SOURCES[sector]['series_id'],t))
 rows.sort()
 for cell in CELLS:
  sub=[x for x in rows if x[1]==SOURCES[cell[0]]['series_id'] and x[2]==SOURCES[cell[1]]['series_id']]
  if len(sub)!=KEY_ROWS_PER_CELL or len({x[0] for x in sub})!=KEY_COUNTRIES:raise RuntimeError(f'key roster envelope changed: {hid(cell)} {len(sub)}')
 return rows

def roster_bytes(rows):
 f=io.StringIO();w=csv.writer(f,lineterminator='\n');w.writerow(['country_iso3','rent_series','outcome_series','anchor_year']);w.writerows(rows)
 return f.getvalue().encode()
def loaded_roster(paths):
 p=ROOT/ROSTER;rows=key_roster(paths)
 if sha(p)!=ROSTER_SHA or p.read_bytes()!=roster_bytes(rows):raise RuntimeError('frozen source-key roster changed')
 return rows

def threshold(cell):
 return dict(family_id=FAMILY,family_size=8,family_alpha=ALPHA,holm_alpha=ALPHA,
  registered_beta_sign='-' if cell[4]<0 else '+',meaningful_abs_beta_log_points_per_sd=MIN_ABS_BETA,
  source_key_roster_path=ROSTER,source_key_roster_sha256=ROSTER_SHA,source_lock_path=lock_rel(cell),
  family_source_sha256=FAMILY_SOURCE_SHA,min_valid_rows=MIN_ROWS,min_valid_countries=MIN_COUNTRIES,
  min_rows_per_anchor=MIN_PER_ANCHOR,min_complete_anchors_per_country=MIN_COMPLETE_ANCHORS,
  rent_percent_gdp_min=0,rent_percent_gdp_max=MAX_RENT,min_residual_standardized_rent_sd=MIN_RESIDUAL_X_SD,
  min_residual_sector_growth_sd=MIN_RESIDUAL_Y_SD,max_top_one_percent_rent_ss_share=MAX_TOP_ONE_PERCENT_X_SS,
  max_top_country_rent_ss_share=MAX_TOP_COUNTRY_X_SS,max_top_one_percent_growth_ss_share=MAX_TOP_ONE_PERCENT_Y_SS,
  max_top_country_growth_ss_share=MAX_TOP_COUNTRY_Y_SS,min_fold_rows=MIN_FOLD_ROWS,
  min_fold_countries=MIN_FOLD_COUNTRIES,min_same_sign_hash_folds=MIN_SAME_SIGN_FOLDS,
  causal_credit=0,policy_score_eligible=False,policy_score_credit=0,school_score_eligible=False,
  school_score_credit=0,featured_eligible=False)

def specification(cell,rows):
 rent,sector,rlabel,slabel,sign=cell;countries=sorted({x[0] for x in rows if x[1]==SOURCES[rent]['series_id'] and x[2]==SOURCES[sector]['series_id']})
 direction='lower' if sign<0 else 'higher'
 return {'hypothesis_id':hid(cell),'version':1,'status':'pre_registered','topic':'resource_rents',
  'claim_direction':'-' if sign<0 else '+',
  'claim':f'Across fixed country windows in 1995, 2000, 2005 and 2010, higher baseline {rlabel.lower()} (% GDP) predicts {direction} cumulative real {sector} value-added growth in the next five years, conditional on prior five-year sector growth, baseline sector scale and real income, and country/anchor effects.',
  'evidence_type':'associational',
  'methodology_note':'One of eight prospective World Bank WDI resource-rent/sector cells. Only source hashes, official series definitions, country/year keys and schemas were inspected before registration. Selected values, null masks and estimates remain sealed until eight separate source-lock commits.',
  'sample':{'countries':countries,'period':[1990,2015],'temporal_structure':'panel','exclusion_rules':[
   'Use the frozen key-only roster of ISO3 national country/indicator/anchor identities. At each anchor t, require exact rent series at t, WDI GDP per person at t, and both real sector value-added series at t−5, t and t+5; this paired-sector requirement is identical across the two outcome cells for each rent.',
   f'After all source locks, retain complete finite rows with rent in [0,{MAX_RENT}] percent GDP, real income and both real sector levels strictly positive. Require countries to have at least {MIN_COMPLETE_ANCHORS} complete anchors. No interpolation or missing-as-zero recoding.',
   'The outcome is log real sector value added at t+5 minus log level at t; controls include the same sector’s prior t−5 to t log growth, log real sector level at t, log real GDP per person at t, country and anchor fixed effects. All anchor follow-ups are nonoverlapping and end by 2015.',
   'No outcome-driven country selection, winsorization, source substitution, post-result model/window/threshold change or policy interpretation.'
  ]},
  'variables':{'treatment':[{'name':f'baseline_{rent}_rent_standardized','source':f'world_bank_wdi:{SOURCES[rent]["series_id"]}',
    'transformation':'Level in percent GDP at anchor t, standardized using the pooled complete-case population SD; +1 unit is +1 SD.',
    'notes':'Modeled natural-resource rent, not fiscal revenue or a policy intervention.'}],
   'outcome':[{'name':f'future_five_year_real_{sector}_value_added_growth','source':f'world_bank_wdi:{SOURCES[sector]["series_id"]}',
    'transformation':'Natural log of positive real sector value added at t+5 divided by positive real sector value added at t.',
    'notes':'Constant 2015 US-dollar national-accounts sector value added.'}],
   'controls':[{'name':'prior_sector_growth','source':f'world_bank_wdi:{SOURCES[sector]["series_id"]}',
      'transformation':'Log sector value added at t divided by t−5.'},
      {'name':'baseline_log_sector_scale','source':f'world_bank_wdi:{SOURCES[sector]["series_id"]}',
      'transformation':'Natural log positive real sector value added at t.'},
      {'name':'baseline_log_real_income','source':f'world_bank_wdi:{SOURCES["income"]["series_id"]}',
      'transformation':'Natural log positive real GDP per person at t.'}]},
  'estimator':{'template':'panel_fe','fixed_effects':['country','anchor_year'],'clustering':'country',
   'notes':'Equal country-window OLS of five-year log sector growth on standardized rent, prior sector growth, baseline log sector scale and log income, country and anchor fixed effects. Country CR1 clustered uncertainty, two-sided Student t(G−1), Holm correction across all eight cells. Five fixed country hash-fold omissions assess sign stability. Descriptive only.'},
  'falsification':{'test':'wdi_resource_rents_sector_growth_2026_10_10',
   'rule':f'INCONCLUSIVE if source chronology or complete-case row, country, anchor, variation, influence, rank, cluster-uncertainty or fold-coverage gate fails. SUPPORTED iff beta has registered {"negative" if sign<0 else "positive"} sign, absolute beta >=0.03 log points of five-year growth per +1 rent SD, Holm-adjusted two-sided p<=0.05 across all eight cells (inconclusive p=1), and at least four of five omission folds share that sign. REFUTED iff these same criteria hold in the opposite direction. Otherwise PARTIAL.',
   'threshold':threshold(cell)},
  'prior_confidence':.5,
  'disclosure':'Four correlated rent measures and two sector outcomes form one eight-cell Holm family. Resource rents are modeled and expressed as GDP shares, so commodity prices and a common GDP denominator may confound levels. The services source lacks a tracked fetch manifest but has an exact local SHA pin. This is observational and receives no causal, policy, school, position or featured credit.',
  'steelman':steel_rel(cell),
  'scope':{'period':[1990,2015],'countries':countries,'outcome_dim':['industrial_capability' if sector=='manufacturing' else 'gdp_growth'],'policy_family':['none'],
   'treatment_tags':[f'wdi_{rent}_resource_rent']},
  'covers_claims':[],'linked_hypotheses':[],'linked_conditions':[]}

def plan_text():
 lines=['# Prospective World Bank natural-resource rents and later sector growth','',
  'This is one correlated eight-cell descriptive family: four modeled rent indicators (total, oil, natural gas, minerals) each paired with real manufacturing and real services value-added growth. The registered Dutch-disease pattern is lower later manufacturing growth but higher later services growth. Opposite outcomes can refute each cell. A total-rent indicator includes the component rents, so these are not independent confirmations. Existing UAE/Norway resource case studies do not evaluate this exact broad country-panel pair of prospective outcomes.','',
  '## Key-only freeze','',
  f'Each cell has {KEY_ROWS_PER_CELL} source-key rows across {KEY_COUNTRIES} ISO3 national codes at anchors 1995, 2000, 2005 and 2010; {KEY_ROWS_PER_CELL*len(CELLS):,} rows across eight cells. WDI files include full country×year grids even where values are missing, so this is only an upper bound. Before this registration, no selected numeric value, null mask, sign or estimate was opened. All eight specs, steelmen, this plan, the runner and key roster are committed together. Eight one-file source-lock commits must precede one measured family result commit.','',
  '## Frozen model and gates','',
  f'At t, require rent in [0,{MAX_RENT}] percent GDP, positive real GDP per person and positive real value-added levels for both sectors at t−5, t and t+5. Retain countries with at least {MIN_COMPLETE_ANCHORS} complete anchors. Analyze paired-sector samples for each rent. Outcome is log sector growth t→t+5, with own prior t−5→t growth, baseline log sector scale, baseline log real income, country and anchor fixed effects. Country CR1 cluster t(G−1) inference; 99% interval; five country hash-fold omissions. A meaningful effect is 0.03 log points of cumulative five-year growth per +1 pooled SD rent, approximately 3% growth. Frozen floors: 160 rows, 60 countries, 30 rows each anchor, residual rent SD 0.15, residual growth SD 0.04, top 1% rent/growth residual squared-share <=0.35, top country <=0.25, folds >=110 rows/40 countries, 4/5 sign stability. All eight cells, including inconclusive p=1, enter Holm alpha .05. Failed gates remain INCONCLUSIVE.','',
  '## Sources, rights and limits','',
  'All seven WDI source parquet bytes are SHA-256 pinned; six have exact tracked fetch entries and the real services-value-added source has only a local SHA pin, so its original fetch transaction cannot be independently reconstructed. The World Bank series glossary defines rents as modeled commodity value minus extraction cost, divided by current GDP, and licenses WDI as CC BY 4.0. This packet cites World Bank and distributes only derived summaries, not raw values. Sector growth can reflect global prices, demand, exchange rates, investment and national-accounts breaks. These are descriptive signals with no causal, policy, school, position or featured credit.','',
  '| Rent source | Outcome | Registered sign |','| --- | --- | --- |']
 lines += [f'| {SOURCES[c[0]]["series_id"]} {c[2]} | {SOURCES[c[1]]["series_id"]} {c[3]} | {"negative" if c[4]<0 else "positive"} |' for c in CELLS]
 lines += ['','Primary definitions: https://databank.worldbank.org/metadataglossary/world-development-indicators/series/NY.GDP.TOTL.RT.ZS ; https://data.worldbank.org/indicator/NV.IND.MANF.KD ; https://data.worldbank.org/indicator/NV.SRV.TOTL.KD .','']
 return '\n'.join(lines)

def steel_text(c):
 rent,sector,rlabel,slabel,sign=c
 mechanism=('A commodity boom can appreciate the real exchange rate and redirect labor or capital away from tradable manufacturing.' if sign<0 else 'Rent windfalls can raise local demand for nontradable services and finance service-sector investment.')
 return (f'# Steelman: {rlabel} and later {sector} growth\n\n**Registered ID:** `{hid(c)}`. {mechanism} The registered five-year coefficient sign is {"negative" if sign<0 else "positive"} after prior sector growth, baseline sector scale and income, country and anchor effects.\n\nCountermechanisms are plausible: rent-funded infrastructure may increase manufacturing, while Dutch-disease pressures, volatile prices or state capture can dampen services. The rent estimates include a current-GDP denominator and the two sector series are national accounts with potential breaks. The four rent measures overlap, and eight cells share a Holm correction. This is a descriptive prospective test, not a causal estimate or policy recommendation.\n')

def write_registration(paths):
 rows=key_roster(paths)
 if hashlib.sha256(roster_bytes(rows)).hexdigest()!=ROSTER_SHA:raise RuntimeError('key roster hash differs from runner freeze')
 files=[RUNNER,PLAN,ROSTER]+[p for c in CELLS for p in (spec_rel(c),steel_rel(c))]
 if any((ROOT/p).exists() for p in files if p!=RUNNER):raise FileExistsError('registration artifact exists')
 schema=json.loads((ROOT/'schemas/hypothesis.schema.json').read_text());Draft202012Validator.check_schema(schema)
 for c in CELLS:
  errors=list(Draft202012Validator(schema).iter_errors(specification(c,rows)))
  if errors:raise RuntimeError(f'{hid(c)} schema: {[e.message for e in errors[:3]]}')
 for p in files:(ROOT/p).parent.mkdir(parents=True,exist_ok=True)
 (ROOT/PLAN).write_text(plan_text());(ROOT/ROSTER).write_bytes(roster_bytes(rows))
 for c in CELLS:
  (ROOT/spec_rel(c)).write_bytes(b'# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n'+ya(specification(c,rows)))
  (ROOT/steel_rel(c)).write_text(steel_text(c))

def registration_commit(paths):
 files=[RUNNER,PLAN,ROSTER]+[p for c in CELLS for p in (spec_rel(c),steel_rel(c))]
 commits={first_add(p) for p in files}
 if len(commits)!=1:raise RuntimeError(f'family registration not in one first commit: {commits}')
 commit=commits.pop()
 for p in files:frozen(p,commit)
 if git('ls-tree','-r','--name-only',commit,'--',*[lock_rel(c) for c in CELLS],*[run_rel(c) for c in CELLS]).strip():raise RuntimeError('registration contains lock or result')
 rows=loaded_roster(paths);schema=json.loads(git('show',f'{commit}:schemas/hypothesis.schema.json'))
 for c in CELLS:
  spec=yaml.safe_load((ROOT/spec_rel(c)).read_text())
  if spec!=specification(c,rows) or not Draft202012Validator(schema).is_valid(spec):raise RuntimeError(f'original registration invalid: {hid(c)}')
 return commit

def lock_payload(c,reg):
 return dict(hypothesis_id=hid(c),family_id=FAMILY,family_size=8,registration_commit=reg,
  source_sha256=FAMILY_SOURCE_SHA,key_roster_sha256=ROSTER_SHA,key_roster_path=ROSTER,
  source_records=SOURCES,manifest_sha256=MANIFEST_HASHES,
  selected_values_or_null_masks_read_before_locks=False,
  provenance_limit='Real services value-added local parquet has an exact SHA pin but no tracked fetch manifest.')
def write_lock(c,reg):
 p=ROOT/lock_rel(c)
 if p.exists():raise FileExistsError(str(p))
 p.write_bytes(js(lock_payload(c,reg)))
def lock_commits(reg):
 out={};prior=reg
 for c in CELLS:
  p=lock_rel(c);commit=first_add(p)
  if not ancestor(prior,commit):raise RuntimeError(f'locks must be separate ordered commits: {p}')
  names=git('diff-tree','--no-commit-id','--name-only','-r',commit).decode().splitlines()
  if names!=[p]:raise RuntimeError(f'lock commit contains other paths: {p}')
  frozen(p,commit)
  if json.loads((ROOT/p).read_text())!=lock_payload(c,reg):raise RuntimeError(f'lock differs: {p}')
  if git('ls-tree','-r','--name-only',commit,'--',*[run_rel(x) for x in CELLS]).strip():raise RuntimeError('result predates all locks')
  out[hid(c)]=commit;prior=commit
 return out

def selected_values(paths):
 # First numeric/null-mask read. Caller has verified all eight committed locks.
 iso={c.alpha_3 for c in pycountry.countries};out={}
 for role,p in paths.items():
  d=pq.read_table(p,columns=['country_iso3','indicator_id','year','value','obs_status']).to_pandas()
  d=d[d.country_iso3.isin(iso)]
  if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate selected national values: {role}')
  bad=d.obs_status.fillna('').astype(str).map(lambda x:x not in ('','A'))
  d.loc[bad,'value']=float('nan')
  out[role]={(str(c),int(y)):float(v) for c,y,v in zip(d.country_iso3,d.year,d.value)}
 return out

def measured_panel(rent,roster,values):
 rows=[];drop=Counter()
 rent_code=SOURCES[rent]['series_id']
 anchors={(c,t) for c,r,o,t in roster if r==rent_code and o==SOURCES['manufacturing']['series_id']}
 for country,t in sorted(anchors):
  x=values[rent][(country,t)];inc=values['income'][(country,t)]
  m=[values['manufacturing'][(country,y)] for y in (t-5,t,t+5)]
  s=[values['services'][(country,y)] for y in (t-5,t,t+5)]
  if not all(map(math.isfinite,[x,inc,*m,*s])):drop['missing_or_nonfinite']+=1;continue
  if not (0<=x<=MAX_RENT):drop['rent_range']+=1;continue
  if not all(z>0 for z in [inc,*m,*s]):drop['nonpositive_sector_or_income']+=1;continue
  rows.append(dict(country_iso3=country,anchor_year=t,x_raw=x,log_income=math.log(inc),
   log_manufacturing=math.log(m[1]),prior_manufacturing=math.log(m[1]/m[0]),growth_manufacturing=math.log(m[2]/m[1]),
   log_services=math.log(s[1]),prior_services=math.log(s[1]/s[0]),growth_services=math.log(s[2]/s[1])))
 panel=pd.DataFrame(rows,columns=['country_iso3','anchor_year','x_raw','log_income','log_manufacturing','prior_manufacturing','growth_manufacturing','log_services','prior_services','growth_services'])
 counts=panel.country_iso3.value_counts();below=panel.country_iso3.map(counts).lt(MIN_COMPLETE_ANCHORS)
 drop['country_below_two_anchors']+=int(below.sum())
 panel=panel.loc[~below].sort_values(['country_iso3','anchor_year']).reset_index(drop=True)
 gate=dict(key_roster_rows=KEY_ROWS_PER_CELL,key_roster_countries=KEY_COUNTRIES,
  complete_rows_before_country_floor=len(rows),valid_rows=len(panel),valid_countries=int(panel.country_iso3.nunique()),
  rows_per_anchor={str(t):int((panel.anchor_year==t).sum()) for t in ANCHORS},dropped=dict(sorted(drop.items())),
  selected_values_read_after_committed_locks=True)
 return panel,gate

def residual_formula(outcome):return f'{outcome} ~ prior + log_sector + log_income + C(country_iso3) + C(anchor_year)'
def model_formula():return 'y ~ x + prior + log_sector + log_income + C(country_iso3) + C(anchor_year)'
def estimate(paired,basegate,sector):
 p=paired.copy();p['y']=p[f'growth_{sector}'];p['prior']=p[f'prior_{sector}'];p['log_sector']=p[f'log_{sector}']
 gate=dict(basegate);fail=[]
 if gate['valid_rows']<MIN_ROWS:fail.append('min_valid_rows')
 if gate['valid_countries']<MIN_COUNTRIES:fail.append('min_valid_countries')
 if min(gate['rows_per_anchor'].values())<MIN_PER_ANCHOR:fail.append('min_rows_per_anchor')
 if fail:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 mean=float(p.x_raw.mean());sd=float(p.x_raw.std(ddof=0))
 if not math.isfinite(sd) or sd<=0:
  fail.append('nonzero_pooled_rent_sd');return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 p['x']=(p.x_raw-mean)/sd
 xm=smf.ols(residual_formula('x'),data=p);ym=smf.ols(residual_formula('y'),data=p)
 if np.linalg.matrix_rank(xm.exog)!=xm.exog.shape[1] or np.linalg.matrix_rank(ym.exog)!=ym.exog.shape[1]:
  fail.append('residual_design_rank');return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 rx=np.asarray(xm.fit().resid,float);ry=np.asarray(ym.fit().resid,float)
 sx=rx**2;sy=ry**2;tx=float(sx.sum());ty=float(sy.sum())
 xsd=math.sqrt(tx/len(rx)) if tx>0 else 0.;ysd=math.sqrt(ty/len(ry)) if ty>0 else 0.
 top=max(1,math.ceil(.01*len(p)))
 x_top=float(sum(sorted(sx,reverse=True)[:top])/tx) if tx>0 else 1.
 y_top=float(sum(sorted(sy,reverse=True)[:top])/ty) if ty>0 else 1.
 x_country=float(p.assign(ss=sx).groupby('country_iso3').ss.sum().max()/tx) if tx>0 else 1.
 y_country=float(p.assign(ss=sy).groupby('country_iso3').ss.sum().max()/ty) if ty>0 else 1.
 gate.update(rent_pooled_mean=mean,rent_pooled_sd=sd,residual_standardized_rent_sd=xsd,residual_sector_growth_sd=ysd,
  top_one_percent_rent_ss_share=x_top,top_country_rent_ss_share=x_country,
  top_one_percent_growth_ss_share=y_top,top_country_growth_ss_share=y_country)
 if xsd<MIN_RESIDUAL_X_SD:fail.append('min_residual_rent_sd')
 if ysd<MIN_RESIDUAL_Y_SD:fail.append('min_residual_growth_sd')
 if x_top>MAX_TOP_ONE_PERCENT_X_SS:fail.append('top_one_percent_rent_concentration')
 if x_country>MAX_TOP_COUNTRY_X_SS:fail.append('top_country_rent_concentration')
 if y_top>MAX_TOP_ONE_PERCENT_Y_SS:fail.append('top_one_percent_growth_concentration')
 if y_country>MAX_TOP_COUNTRY_Y_SS:fail.append('top_country_growth_concentration')
 if fail:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 model=smf.ols(model_formula(),data=p)
 if np.linalg.matrix_rank(model.exog)!=model.exog.shape[1]:
  fail.append('primary_design_rank');return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 groups=int(p.country_iso3.nunique());fit=model.fit(cov_type='cluster',cov_kwds={'groups':p.country_iso3,'use_correction':True,'df_correction':True},use_t=True)
 beta,se=float(fit.params['x']),float(fit.bse['x'])
 if not(math.isfinite(beta) and math.isfinite(se) and se>0):
  fail.append('finite_cluster_uncertainty');return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 pv=float(2*student_t.sf(abs(beta/se),groups-1));critical=float(student_t.ppf(.995,groups-1))
 if not(math.isfinite(pv) and math.isfinite(critical)):
  fail.append('finite_t_inference');return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 primary=dict(beta=beta,country_cluster_se=se,p_two_sided=pv,confidence_level=.99,
  confidence_interval=[beta-critical*se,beta+critical*se],n_rows=len(p),n_countries=groups,df_inference=groups-1,
  model_rank=int(fit.model.rank),model_columns=int(model.exog.shape[1]),rent_pooled_sd=sd,
  residual_standardized_rent_sd=xsd,residual_sector_growth_sd=ysd,
  top_one_percent_rent_ss_share=x_top,top_country_rent_ss_share=x_country,
  top_one_percent_growth_ss_share=y_top,top_country_growth_ss_share=y_country,
  method='equal-row country/anchor FE OLS of five-year log sector growth with prior growth, baseline sector scale and log income; country CR1 cluster t(G-1)')
 folds=[]
 for omit in range(5):
  q=p[p.country_iso3.map(lambda c:int(hashlib.sha256(c.encode()).hexdigest(),16)%5!=omit)]
  if len(q)<MIN_FOLD_ROWS or q.country_iso3.nunique()<MIN_FOLD_COUNTRIES:fail.append(f'fold_{omit}_coverage');continue
  f=smf.ols(model_formula(),data=q)
  if np.linalg.matrix_rank(f.exog)!=f.exog.shape[1]:fail.append(f'fold_{omit}_rank');continue
  fb=float(f.fit().params['x'])
  if not math.isfinite(fb):fail.append(f'fold_{omit}_finite');continue
  folds.append(dict(omitted_hash_fold=omit,rows=len(q),countries=int(q.country_iso3.nunique()),beta=fb))
 if fail:return dict(sample=gate,primary=primary,hash_folds=folds,gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 return dict(sample=gate,primary=primary,hash_folds=folds,gate_failures=[],holm_adjusted_p=None,verdict='PENDING_FAMILY')

def holm(results):
 ranked=sorted((r['primary']['p_two_sided'] if r['primary'] is not None and not r['gate_failures'] else 1.,h) for h,r in results.items())
 running=0.;adj={}
 for i,(p,h) in enumerate(ranked):running=max(running,min(1.,(len(CELLS)-i)*p));adj[h]=running
 for c in CELLS:
  r=results[hid(c)]
  if r['gate_failures']:r['holm_adjusted_p']=1.;r['verdict']='INCONCLUSIVE';continue
  r['holm_adjusted_p']=adj[hid(c)];beta=r['primary']['beta'];same=sum(f['beta']*c[4]>0 for f in r['hash_folds']);opp=sum(f['beta']*c[4]<0 for f in r['hash_folds'])
  r['same_direction_folds']=same;r['opposite_direction_folds']=opp
  if beta*c[4]>=MIN_ABS_BETA and adj[hid(c)]<=ALPHA and same>=MIN_SAME_SIGN_FOLDS:r['verdict']='SUPPORTED'
  elif beta*c[4]<=-MIN_ABS_BETA and adj[hid(c)]<=ALPHA and opp>=MIN_SAME_SIGN_FOLDS:r['verdict']='REFUTED'
  else:r['verdict']='PARTIAL'

def artifacts(c,result,reg,lock,stamp):
 id=hid(c);diag=dict(hypothesis_id=id,family_id=FAMILY,family_size=8,registration_commit=reg,
  source_lock_commit=lock,source_sha256=FAMILY_SOURCE_SHA,source_key_roster_sha256=ROSTER_SHA,
  runner=RUNNER,run_utc=stamp,predictor_series=SOURCES[c[0]]['series_id'],outcome_series=SOURCES[c[1]]['series_id'],
  registered_direction=c[4],thresholds=threshold(c),result=result,limitations=LIMITS,correction=CORRECTION)
 db=js(diag);source=dict(publisher='World Bank World Development Indicators',source_sha256=FAMILY_SOURCE_SHA,
  source_lock_commit=lock,source_lock_manifest=lock_rel(c),key_roster_sha256=ROSTER_SHA,
  input_vintages=[{'path':v['path'],'sha256':v['sha256']} for v in SOURCES.values()],
  services_fetch_manifest='not available in tracked corpus',license='CC BY 4.0; World Bank attribution; derived summaries only',contains_source_values=False)
 manifest=dict(hypothesis_id=id,status=result['verdict'],run_utc=stamp,runner=RUNNER,
  preregistration_commit=reg,source=source,family_id=FAMILY,family_size=8,sample=result['sample'],correction=CORRECTION)
 packet=dict(packet_version=1,hypothesis={'id':id,'path':spec_rel(c)},
  preregistration={'commit':reg,'steelman':steel_rel(c),'source_plan':PLAN,'key_roster':ROSTER},
  source=source,family={'id':FAMILY,'size':8,'members':[hid(x) for x in CELLS],'holm_alpha':ALPHA,
   'interpretation':'Four correlated natural-resource rent predictors with two future real-sector growth outcomes'},
  reproduction={'runner':RUNNER,'command':f'python3 {RUNNER} verify --source-root /path/to/IESET',
   'result_sha256':hashlib.sha256(db).hexdigest()},result=result,limitations=LIMITS,correction=CORRECTION)
 card=(f'# Result card: {id}\n\nVerdict: **{result["verdict"]}**. Predictor {SOURCES[c[0]]["series_id"]}; outcome {SOURCES[c[1]]["series_id"]}; registered sign {"negative" if c[4]<0 else "positive"}.\n\nRegistration `{reg}`; source lock `{lock}`. Complete country windows {result["sample"]["valid_rows"]} in {result["sample"]["valid_countries"]} countries.\n')
 if result['gate_failures']:card+=f'\nFrozen gate failures: {", ".join(result["gate_failures"])}.\n'
 if result['primary']:
  q=result['primary'];card+=f'\nBeta={q["beta"]:+.6g} five-year log-growth points per +1 rent SD; country-cluster SE={q["country_cluster_se"]:.6g}; two-sided p={q["p_two_sided"]:.6g}; Holm p={result["holm_adjusted_p"]:.6g}; 99% CI={q["confidence_interval"]}.\n'
 card+='\nDescriptive prospective calibration only; zero causal, policy, school, position or featured credit.\n'
 wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
  "root=Path(__file__).resolve().parents[3]\n"
  f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
 return {'diagnostics.json':db,'manifest.yaml':ya(manifest),'evidence_packet.yaml':ya(packet),
  'result_card.md':card.encode(),'replication.py':wrapper.encode(),
  'hypothesis.yaml':(ROOT/spec_rel(c)).read_bytes(),
  'chart_data.json':js({'hypothesis_id':id,'family_id':FAMILY,'verdict':result['verdict'],'primary':result['primary']})}

def report_text(results,reg,locks):
 lines=['# WDI natural-resource rents and later real sector growth: frozen results','',
  f'Registration `{reg}`; eight distinct source locks, from `{next(iter(locks.values()))}` through `{list(locks.values())[-1]}`.','',
  '| Rent | Later sector | Verdict | Rows / countries | Beta per +1 rent SD | Raw p | Holm p | Gate failures |',
  '| --- | --- | --- | ---: | ---: | ---: | ---: | --- |']
 for c in CELLS:
  r=results[hid(c)];p=r['primary'];g=r['sample'];line=f'| {c[2]} | {c[1]} | {r["verdict"]} | {g["valid_rows"]} / {g["valid_countries"]} | '
  line+=(f'{p["beta"]:+.5g} | {p["p_two_sided"]:.5g} | {r["holm_adjusted_p"]:.5g} | ' if p else '— | — | 1 | ')
  line+=f'{", ".join(r["gate_failures"]) or "none"} |';lines.append(line)
 lines+=['','The four rent indicators overlap and the two sector outcomes share countries; Holm adjusts all eight registered cells. Rents are modeled shares of GDP, not policy interventions. The services source has an exact SHA pin but no tracked fetch manifest. No causal, school, policy, position or featured credit.','']
 return '\n'.join(lines)

def equal_close(a,b,label):
 if isinstance(b,dict):
  if not isinstance(a,dict) or set(a)!=set(b):raise AssertionError(f'{label}: keys differ')
  for k,v in b.items():equal_close(a[k],v,f'{label}.{k}')
 elif isinstance(b,list):
  if not isinstance(a,list) or len(a)!=len(b):raise AssertionError(f'{label}: list length differs')
  for i,v in enumerate(b):equal_close(a[i],v,f'{label}[{i}]')
 elif isinstance(b,float):
  if not math.isfinite(float(a)) or not math.isclose(float(a),b,rel_tol=1e-9,abs_tol=1e-11):raise AssertionError(f'{label}: numeric mismatch')
 elif a!=b:raise AssertionError(f'{label}: value differs')
def write_results(results,reg,locks):
 if (ROOT/REPORT).exists() or any((ROOT/run_rel(c)).exists() for c in CELLS):raise FileExistsError('measured result already exists')
 stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
 for c in CELLS:
  folder=ROOT/run_rel(c);folder.mkdir(parents=True)
  for name,content in artifacts(c,results[hid(c)],reg,locks[hid(c)],stamp).items():(folder/name).write_bytes(content)
 (ROOT/REPORT).write_text(report_text(results,reg,locks))
def verify_results(results,reg,locks):
 for c in CELLS:
  folder=ROOT/run_rel(c);saved=json.loads((folder/'diagnostics.json').read_text())
  expected=artifacts(c,results[hid(c)],reg,locks[hid(c)],saved['run_utc'])
  for name,content in expected.items():
   p=folder/name
   if name.endswith('.json'):equal_close(json.loads(p.read_text()),json.loads(content),f'{hid(c)}:{name}')
   elif name.endswith('.yaml') and name!='hypothesis.yaml':equal_close(yaml.safe_load(p.read_text()),yaml.safe_load(content),f'{hid(c)}:{name}')
   elif p.read_bytes()!=content:raise AssertionError(f'exact replay mismatch: {p}')
 if (ROOT/REPORT).read_text()!=report_text(results,reg,locks):raise AssertionError('family result report differs from replay')
def main():
 parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);parser.add_argument('action',choices=['preflight','register','lock','measure','verify']);parser.add_argument('--source-root',type=Path,default=ROOT);parser.add_argument('--cell',choices=[f'{c[0]}_{c[1]}' for c in CELLS]);args=parser.parse_args()
 paths=source_paths(args.source_root)
 if args.action=='preflight':
  rows=key_roster(paths);print(json.dumps({'family_size':len(CELLS),'key_only_rows':len(rows),'rows_per_cell':KEY_ROWS_PER_CELL,'countries_per_cell':KEY_COUNTRIES,'anchors':ANCHORS,'selected_values_opened':False},sort_keys=True));return 0
 if args.action=='register':write_registration(paths);print('wrote eight-cell key-only registration; commit before locks');return 0
 reg=registration_commit(paths)
 if args.action=='lock':
  if args.cell is None:raise ValueError('--cell required')
  c=next(c for c in CELLS if f'{c[0]}_{c[1]}'==args.cell);i=CELLS.index(c)
  if i and not (ROOT/lock_rel(CELLS[i-1])).exists():raise RuntimeError('prior lock must be committed')
  if i and not ancestor(reg,first_add(lock_rel(CELLS[i-1]))):raise RuntimeError('prior lock must be committed')
  write_lock(c,reg);print(f'wrote source lock for {hid(c)}; commit lock alone');return 0
 locks=lock_commits(reg);roster=loaded_roster(paths);values=selected_values(paths)
 results={}
 for rent,_ in RENTS:
  panel,gate=measured_panel(rent,roster,values)
  for c in (c for c in CELLS if c[0]==rent):results[hid(c)]=estimate(panel,gate,c[1])
 holm(results)
 if args.action=='measure':
  write_results(results,reg,locks)
  print(json.dumps({h:{'verdict':r['verdict'],'rows':r['sample']['valid_rows'],'countries':r['sample']['valid_countries'],'gate_failures':r['gate_failures'],'beta':r['primary']['beta'] if r['primary'] else None,'p':r['primary']['p_two_sided'] if r['primary'] else None,'holm_p':r['holm_adjusted_p']} for h,r in results.items()},indent=2))
 else:verify_results(results,reg,locks);print('verified exact replay',FAMILY,{h:r['verdict'] for h,r in results.items()})
 return 0
if __name__=='__main__':raise SystemExit(main())
