#!/usr/bin/env python3
"""Frozen four-cell IMF Brent-shock by fuel-export exposure family.

Preflight, registration and locks read source identities, hashes, schemas and
country/year/month keys only. Numeric values and null masks are opened solely
after registration and four separate source-lock commits.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,subprocess
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pycountry
import statsmodels.formula.api as smf
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT=Path(__file__).resolve().parents[1]
FAMILY='imf_brent_fuel_export_forward_macro_2026_10_10'
RUNNER='scripts/run_imf_brent_export_transmission_2026.py'
PLAN='engine/audits/imf_brent_export_transmission_prereg_2026-10-10.md'
REPORT='engine/audits/imf_brent_export_transmission_results_2026-10-10.md'
ROSTER='data/pinned_evidence/imf_brent_export_transmission_2026_key_roster.csv'
ROSTER_SHA='5652568f0a0a9cf0c2b919abeeb0916f4325b5579403fedae31c9cd15dcc38d1'
BOOT='data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml'
GDP_MAN='data/manifests/fetch_run_2026-05-05T200056Z.yaml'
INV_MAN='data/manifests/fetch_run_2026-05-05T203305Z.yaml'
MANIFEST_HASHES={BOOT:'e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e',GDP_MAN:'a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945',INV_MAN:'53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0'}
def rec(pub,code,file,hash,man,url,license):
 return dict(publisher=pub,series_id=code,path=f'data/vintages/{pub}/{file}',sha256=hash,manifest=man,source_url=url,license=license)
SOURCES={
 'oil':rec('imf_pcps','POILBRE','POILBRE@2026-05-05T195409Z.parquet','d1f0753d78837b6be853f43672c138981582b1d524fe47152a413ddefa6dbc4c',GDP_MAN,'https://www.imf.org/en/research/commodity-prices','IMF standard permissions; attribution required'),
 'fuel':rec('world_bank_wdi','TX.VAL.FUEL.ZS.UN','TX.VAL.FUEL.ZS.UN@2026-04-30T115204Z.parquet','a4c2d9e1aef424666d6becae2a4f913925e32b2223491d87b6f3943e546ec20e',BOOT,'https://data.worldbank.org/indicator/TX.VAL.FUEL.ZS.UN','CC BY 4.0'),
 'ca':rec('world_bank_wdi','BN.CAB.XOKA.GD.ZS','BN.CAB.XOKA.GD.ZS@2026-05-05T195123Z.parquet','977f10a40e15becc1f1f7abdee7e3f8a99ab7c39ffdc6e3994d5a993efa4f168',GDP_MAN,'https://data.worldbank.org/indicator/BN.CAB.XOKA.GD.ZS','CC BY 4.0'),
 'invest':rec('world_bank_wdi','NE.GDI.FTOT.ZS','NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet','fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21',INV_MAN,'https://data.worldbank.org/indicator/NE.GDI.FTOT.ZS','CC BY 4.0'),
 'income':rec('world_bank_wdi','NY.GDP.PCAP.KD','NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet','0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f',GDP_MAN,'https://data.worldbank.org/indicator/NY.GDP.PCAP.KD','CC BY 4.0'),
 'cons':rec('world_bank_wdi','NE.CON.PRVT.PC.KD','NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet','e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe',GDP_MAN,'https://data.worldbank.org/indicator/NE.CON.PRVT.PC.KD','CC BY 4.0'),
}
SOURCE_SHA=hashlib.sha256('|'.join(SOURCES[k]['sha256'] for k in SOURCES).encode()).hexdigest()
CELLS=(('ca','current_account','Current-account balance, percent of GDP',.5,'percentage points'),('invest','fixed_investment','Gross fixed capital formation, percent of GDP',.4,'percentage points'),('income','real_income_pc','Real GDP per person',.015,'log points'),('cons','real_consumption_pc','Real household consumption per person',.015,'log points'))
YEARS=tuple(range(2005,2018));BASE_YEARS=tuple(range(2000,2005));ALPHA=.05
MIN_ROWS=500;MIN_COUNTRIES=50;MIN_YEARS=10;MIN_ROWS_PER_COUNTRY=5
MIN_EXPORTER_COUNTRIES=15;MIN_EXPORTER_ROWS=80;EXPORTER_SHARE=30.
MIN_RESIDUAL_X_SD=.15;MIN_RESIDUAL_Y={'ca':.25,'invest':.25,'income':.005,'cons':.005}
MAX_TOP1_X=.30;MAX_TOP_COUNTRY_X=.18;MAX_TOP_YEAR_X=.35
MAX_TOP1_Y=.30;MAX_TOP_COUNTRY_Y=.18;MAX_TOP_YEAR_Y=.35
MIN_FOLD_ROWS=350;MIN_FOLD_COUNTRIES=35;MIN_SAME_SIGN_FOLDS=4
CORRECTION=dict(disposition='descriptive_calibration_only',causal_credit=0,policy_score_eligible=False,policy_score_credit=0,school_score_eligible=False,school_score_credit=0,featured_eligible=False)
LIMITS=[
 'IMF PCPS Brent is a common global price, not a country-specific export price or exogenous country treatment; timing and fixed effects do not establish effects.',
 'WDI fuel exports are a share of merchandise exports, not GDP or net fuel exports; countries may also import fuel, and fixed 2000-2004 shares do not capture later trade changes.',
 'The outcomes are national-accounts or balance-of-payments aggregates with revisions and potential country-method breaks; real mean consumption has no distributional interpretation.',
 'All four cells share one oil series, baseline exposure and many countries; Holm controls only this selected family, not the broader IESET search.',
 'Country/year effects and baseline outcome trends do not eliminate global demand, exchange-rate, domestic production, financial, and fiscal confounding.',
 'Only derived results are tracked; raw IMF/World Bank values are not redistributed. All causal, policy, school, position and featured credit is zero.'
]
def hid(c):return f'imf_brent_fuel_export_{c[1]}_forward_2026'
def spec_rel(c):return f'hypotheses/commodity_shocks/{hid(c)}.yaml'
def steel_rel(c):return f'hypotheses/steelman/{hid(c)}.md'
def lock_rel(c):return f'data/pinned_evidence/{hid(c)}.source.json'
def run_rel(c):return f'engine/runs/{hid(c)}'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def js(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def ya(x):return yaml.safe_dump(x,sort_keys=False,allow_unicode=True,width=110).encode()
def git(*args):
 p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True)
 if p.returncode:raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode(errors='replace')}")
 return p.stdout
def first_add(path):
 cs=git('log','--diff-filter=A','--reverse','--format=%H','HEAD','--',path).decode().splitlines()
 if len(cs)!=1:raise RuntimeError(f'expected one first-add commit for {path}: {cs}')
 return cs[0]
def ancestor(a,b):return a!=b and subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT).returncode==0
def frozen(path,commit):
 if not (ROOT/path).is_file() or (ROOT/path).read_bytes()!=git('show',f'{commit}:{path}'):raise RuntimeError(f'frozen artifact changed: {path}')
 if git('status','--porcelain','--',path).strip():raise RuntimeError(f'uncommitted frozen artifact: {path}')
def source_paths(source_root):
 paths={}
 for role,r in SOURCES.items():
  p=source_root/r['path']
  if not p.is_file() or sha(p)!=r['sha256']:raise RuntimeError(f'missing/hash-mismatched source: {role}')
  fields=set(pq.ParquetFile(p).schema_arrow.names)
  need={'region','period','value'} if role=='oil' else {'country_iso3','indicator_id','year','value','obs_status'}
  if not need.issubset(fields):raise RuntimeError(f'source schema changed: {role}')
  paths[role]=p
 for m,h in MANIFEST_HASHES.items():
  p=ROOT/m
  if not p.is_file() or sha(p)!=h:raise RuntimeError(f'manifest hash changed: {m}')
  entries=yaml.safe_load(p.read_text()).get('entries',[])
  for role,r in SOURCES.items():
   if r['manifest']!=m:continue
   match=[e for e in entries if e.get('publisher')==r['publisher'] and e.get('series_id')==r['series_id'] and e.get('parquet_path')==r['path'] and e.get('sha256')==r['sha256']]
   if len(match)!=1:raise RuntimeError(f'exact manifest entry missing: {role}')
 return paths

def key_roster(paths):
 iso={c.alpha_3 for c in pycountry.countries};keys={}
 oil=pq.read_table(paths['oil'],columns=['region','period']).to_pandas()
 if set(oil.region.dropna())!={'W00'}:raise RuntimeError('unexpected PCPS regional key')
 months=set(oil.period.astype(str))
 for t in YEARS:
  for y in (t-1,t):
   if any(f'{y}M{m}' not in months for m in range(1,13)):raise RuntimeError(f'Brent month keys missing: {y}')
 for role,p in paths.items():
  if role=='oil':continue
  d=pq.read_table(p,columns=['country_iso3','indicator_id','year']).to_pandas()
  if set(d.indicator_id.dropna())!={SOURCES[role]['series_id']}:raise RuntimeError(f'indicator key mismatch: {role}')
  d=d[d.country_iso3.isin(iso)]
  if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate national key: {role}')
  keys[role]={(str(c),int(y)) for c,y in zip(d.country_iso3,d.year)}
 rows=[]
 for c in CELLS:
  role=c[0]
  for country in sorted(iso):
   if sum((country,y) in keys['fuel'] for y in BASE_YEARS)<3:continue
   for t in YEARS:
    if all((country,y) in keys[role] for y in (t-2,t,t+2)) and (country,t) in keys['income']:
     rows.append((country,t,SOURCES[role]['series_id']))
 return sorted(rows)
def roster_bytes(rows):
 f=io.StringIO();w=csv.writer(f,lineterminator='\n');w.writerow(['country_iso3','shock_year','outcome_series']);w.writerows(rows);return f.getvalue().encode()
def loaded_roster(paths):
 rows=key_roster(paths);p=ROOT/ROSTER
 if sha(p)!=ROSTER_SHA or p.read_bytes()!=roster_bytes(rows):raise RuntimeError('frozen key roster differs')
 return rows

def threshold(c):
 return dict(family_id=FAMILY,family_size=4,family_alpha=ALPHA,holm_alpha=ALPHA,registered_beta_sign='+',meaningful_abs_beta=c[3],beta_unit=c[4]+' per +1 pooled SD oil-shock-by-baseline-fuel-share',source_key_roster_path=ROSTER,source_key_roster_sha256=ROSTER_SHA,source_lock_path=lock_rel(c),family_source_sha256=SOURCE_SHA,min_valid_rows=MIN_ROWS,min_valid_countries=MIN_COUNTRIES,min_years=MIN_YEARS,min_rows_per_country=MIN_ROWS_PER_COUNTRY,min_exporter_countries=MIN_EXPORTER_COUNTRIES,min_exporter_rows=MIN_EXPORTER_ROWS,exporter_baseline_fuel_share_pct=EXPORTER_SHARE,min_residual_standardized_exposure_sd=MIN_RESIDUAL_X_SD,min_residual_outcome_sd=MIN_RESIDUAL_Y[c[0]],max_top_one_percent_exposure_ss_share=MAX_TOP1_X,max_top_country_exposure_ss_share=MAX_TOP_COUNTRY_X,max_top_year_exposure_ss_share=MAX_TOP_YEAR_X,max_top_one_percent_outcome_ss_share=MAX_TOP1_Y,max_top_country_outcome_ss_share=MAX_TOP_COUNTRY_Y,max_top_year_outcome_ss_share=MAX_TOP_YEAR_Y,min_fold_rows=MIN_FOLD_ROWS,min_fold_countries=MIN_FOLD_COUNTRIES,min_same_sign_hash_folds=MIN_SAME_SIGN_FOLDS,causal_credit=0,policy_score_eligible=False,policy_score_credit=0,school_score_eligible=False,school_score_credit=0,featured_eligible=False)

def specification(c,rows):
 role,slug,label,delta,unit=c;countries=sorted({r[0] for r in rows if r[2]==SOURCES[role]['series_id']})
 trans=('Exact t to t+2 change in percentage-point level, requiring values within the frozen bound.' if role in ('ca','invest') else 'Natural log of positive exact t+2 level divided by positive exact t level.')
 return {'hypothesis_id':hid(c),'version':1,'status':'pre_registered','topic':'growth','claim_direction':'+',
  'claim':f'Among the fixed national 2005-2017 shock-year roster, a larger IMF Brent annual-price increase in year t interacted with a higher fixed 2000-2004 fuel share of merchandise exports predicts a larger subsequent t to t+2 increase in {label.lower()}, conditional on baseline level and prior two-year change, baseline real income, country and shock-year effects.',
  'evidence_type':'associational','methodology_note':'One of four distinct macro-response endpoints in a single prospective, descriptive IMF PCPS × WDI fuel-export-exposure family. Source keys and hashes only were inspected before registration; selected values and null masks remain sealed through four separate source-lock commits.',
  'sample':{'countries':countries,'period':[2000,2019],'temporal_structure':'panel','exclusion_rules':[
   'Use only the frozen structural country, shock-year and outcome-key roster; require at least three finite, status-clean fuel-export shares in 2000-2004 and take their fixed arithmetic mean, bounded [0,100].',
   'For shock years 2005-2017 require exactly twelve positive finite monthly IMF Brent prices in each of t-1 and t; annual arithmetic means form log(price_t/price_t-1). No missing month is imputed.',
   'For each cell require finite status-clean outcome at t-2, t and t+2 and real GDP per person at t. Current-account values must lie in [-100,100] percent GDP; fixed-investment values in [0,100] percent GDP; real income and real private consumption levels must be positive.',
   'Retain country panels with at least five complete rows. Never alter source, endpoint, country, lag, controls or threshold after selected values; no winsorization or missing-as-zero recoding.'
  ]},
  'variables':{'treatment':[{'name':'standardized_brent_shock_times_preperiod_fuel_export_share','source':'imf_pcps:POILBRE; world_bank_wdi:TX.VAL.FUEL.ZS.UN','transformation':'Log annual mean Brent price change t-1→t multiplied by fixed 2000-2004 mean fuel exports as a fraction of merchandise exports, then standardized by complete-case pooled population SD.','notes':'The interaction is an exposure proxy, not a country-specific oil export price or measured policy intervention.'}],
   'outcome':[{'name':'future_two_year_'+slug+'_change','source':f'world_bank_wdi:{SOURCES[role]["series_id"]}','transformation':trans,'notes':label}],
   'controls':[{'name':'prior_two_year_outcome_change','source':f'world_bank_wdi:{SOURCES[role]["series_id"]}','transformation':'Same outcome change t-2→t in its headline units.'},{'name':'baseline_outcome_level','source':f'world_bank_wdi:{SOURCES[role]["series_id"]}','transformation':'Level at t, logged for real income or private consumption.'},{'name':'baseline_log_real_income','source':'world_bank_wdi:NY.GDP.PCAP.KD','transformation':'Natural log positive real GDP per person at t; duplicates baseline outcome and is omitted when income is the outcome.'}]},
  'estimator':{'template':'panel_fe','fixed_effects':['country','shock_year'],'clustering':'country_and_shock_year','notes':'Equal country-year OLS on pooled-SD interaction exposure, prior outcome change, baseline outcome and log real income (income outcome omits duplicate log-income control), country and shock-year effects. Two-way country/year CR1 cluster covariance; two-sided Student t with min(country clusters,year clusters)-1 degrees of freedom; Holm over all four cells. Five fixed country-hash omission folds assess directional stability.'},
  'falsification':{'test':'imf_brent_fuel_export_forward_macro_2026_10_10','rule':f'INCONCLUSIVE if exact sources, sample, exporter spread, residual variation/concentration, rank, two-way cluster uncertainty or fold coverage fails. SUPPORTED iff positive beta >= {delta} {unit} per +1 interaction SD, Holm-adjusted two-sided p<=0.05, and at least four of five hash-fold slopes are positive. REFUTED iff beta <= -{delta}, same p and at least four negative folds. Otherwise PARTIAL.','threshold':threshold(c)},
  'prior_confidence':.5,'disclosure':'Global Brent shocks and fixed fuel-export orientation can be jointly related to global demand and country institutions; fuel imports are omitted, as are later export-mix changes. Country/year effects and timing do not identify an oil-price or policy effect. Four outcomes share source and sample; zero causal, policy, school, position or featured credit.',
  'steelman':steel_rel(c),'scope':{'period':[2000,2019],'countries':countries,'outcome_dim':[{'ca':'capital_flows','invest':'industrial_capability','income':'gdp_growth','cons':'private_consumption'}[role]],'policy_family':['none'],'treatment_tags':['brent_price_shock','baseline_fuel_export_orientation']},'covers_claims':[],'linked_hypotheses':[],'linked_conditions':[]}

def plan_text(rows):
 counts={c[1]:(sum(r[2]==SOURCES[c[0]]['series_id'] for r in rows),len({r[0] for r in rows if r[2]==SOURCES[c[0]]['series_id']})) for c in CELLS}
 lines=['# IMF Brent shocks, fixed fuel-export orientation and later macro responses — prospective registration','',
  'The single four-cell family asks whether countries whose merchandise exports were more fuel oriented in 2000-2004 have larger later macro responses to a common Brent price increase. The four distinct responses are current-account balance, fixed-investment share, real GDP per person and real private consumption per person. The IMF PCPS monthly Brent price and WDI merchandise fuel-export share measure an interaction proxy, not country-specific net oil trade or a policy. Prior IMF inflation→macro, WDI resource-rent→sector-growth and energy-price→industrial outcomes are different directed questions and are not independent confirmations.','',
  '## Value-blind source-key freeze','',
  f'Shock years are 2005–2017; baseline fuel-export-share keys are 2000–2004; response endpoints end by 2019. The roster has {len(rows):,} cell-specific structural keys. WDI files contain broad country×year grids even where values are null, so key counts are upper bounds only. Before this registration no selected numeric value or null mask, shock, baseline share, outcome change, sign or estimate was opened. This plan, four specs and steelmen, runner and key roster are one first-add commit. Four separate one-file source-lock commits must follow before any selected value access.','',
  '| Outcome | Source-key rows / countries | Registered sign | Meaningful beta per +1 interaction SD |','| --- | ---: | --- | --- |']
 lines += [f'| {c[2]} | {counts[c[1]][0]} / {counts[c[1]][1]} | positive | {c[3]} {c[4]} |' for c in CELLS]
 lines+=['','## Frozen measurement and failures','',
  'Fixed exposure is the 2000–2004 arithmetic mean of at least three valid national fuel-export shares [0,100], divided by 100, multiplied by log of annual-average Brent price in shock year t over t−1. Exactly twelve positive finite monthly prices are required for each annual average. Standardize the interaction using the pooled complete-case population SD separately per endpoint; +1 beta unit is +1 SD. Outcome is t→t+2 change in percentage points for current-account and investment shares, or log growth for income and private consumption. Control the same outcome’s t−2→t change, baseline level, baseline log real GDP per person except where it duplicates the income outcome, plus country and shock-year effects. Keep countries with at least five complete rows. Two-way country/year clustered CR1 SE; two-sided t with min(country,year clusters)−1 df; 99% descriptive intervals.','',
  f'Each endpoint requires at least {MIN_ROWS} rows, {MIN_COUNTRIES} countries and {MIN_YEARS} shock years; at least {MIN_EXPORTER_COUNTRIES} countries and {MIN_EXPORTER_ROWS} rows must have baseline fuel share ≥{EXPORTER_SHARE:g}%. Residualized standardized exposure SD ≥{MIN_RESIDUAL_X_SD}; residualized outcome SD ≥0.25 percentage points for current-account and investment changes or ≥0.005 log points for real income and consumption growth. Top 1% row shares of squared residual exposure and outcome ≤{MAX_TOP1_X}/{MAX_TOP1_Y}; maximum country shares ≤{MAX_TOP_COUNTRY_X}/{MAX_TOP_COUNTRY_Y}; maximum shock-year shares ≤{MAX_TOP_YEAR_X}/{MAX_TOP_YEAR_Y}. Five SHA256(country) mod 5 omissions require ≥{MIN_FOLD_ROWS} rows and ≥{MIN_FOLD_COUNTRIES} countries each; four of five same-sign slopes. Rank or two-way cluster uncertainty failure is INCONCLUSIVE. Holm α={ALPHA} includes all four cells, with invalid cells p=1. Opposite signed material and Holm-significant result is REFUTED; method-valid but threshold-missing is PARTIAL. No post-result substitutions.','',
  '## Source custody, rights, limitations','',
  'All six raw source parquets and their exact tracked fetch-manifest entries are SHA-256 pinned. The IMF source manifest identifies POILBRE as Dated Brent, light blend, USD per barrel, monthly global W00; it records IMF attribution-required permissions. IMF published data terms permit attributed derived use and warn that some statistical products include third-party inputs. WDI records CC BY 4.0. This packet retains only derived diagnostics, not raw series rows. Source definitions: https://www.imf.org/en/research/commodity-prices ; https://www.imf.org/en/about/copyright-and-terms ; https://data.worldbank.org/indicator/TX.VAL.FUEL.ZS.UN .',
  'The interaction does not measure import dependence or country-specific export receipts. Global demand, domestic extraction, exchange rates, fiscal policy and revisions can drive both exposure and outcomes. Two-way clustering helps with shared years but only thirteen shock years exist; no causal, policy, school, position or featured credit can follow. Holm is local to the selected family, not archive-wide correction.','']
 return '\n'.join(lines)
def steel_text(c):
 return f'# Steelman: Brent shock, fixed fuel-export orientation and later {c[2].lower()}\n\nA country that exported a greater fraction of merchandise as fuel before the shock period could receive larger export receipts after Brent rises. That might raise subsequent {c[2].lower()} over the following two years. The registered target is a positive descriptive slope of at least {c[3]} {c[4]} per +1 pooled SD of the interaction, after own baseline and prior trend, baseline income, and country/year effects.\n\nThe strong alternative is that Brent is a global demand signal and fuel-export shares omit import bills, extraction quantity, contract pricing and services trade. A higher price can appreciate currencies, suppress non-oil sectors, or trigger countercyclical saving rather than spending. Two-year forward changes may reverse an immediate boom. Measurement revisions, simultaneous commodity shocks, and shared source errors remain. An opposite material association refutes this specific predictive direction; weak, fragile or sparse results remain partial or inconclusive. No causal or policy claim follows.\n'

def write_registration(paths):
 rows=key_roster(paths);rb=roster_bytes(rows)
 if hashlib.sha256(rb).hexdigest()!=ROSTER_SHA:raise RuntimeError('roster hash must be frozen in runner before register')
 files=[RUNNER,PLAN,ROSTER]+[p for c in CELLS for p in (spec_rel(c),steel_rel(c))]
 if any((ROOT/p).exists() for p in files if p!=RUNNER):raise FileExistsError('registration artifact exists')
 schema=json.loads((ROOT/'schemas/hypothesis.schema.json').read_text());Draft202012Validator.check_schema(schema)
 for c in CELLS:
  errors=list(Draft202012Validator(schema).iter_errors(specification(c,rows)))
  if errors:raise RuntimeError(f'{hid(c)} schema: {[e.message for e in errors[:3]]}')
 for p in files:(ROOT/p).parent.mkdir(parents=True,exist_ok=True)
 (ROOT/PLAN).write_text(plan_text(rows));(ROOT/ROSTER).write_bytes(rb)
 for c in CELLS:
  (ROOT/spec_rel(c)).write_bytes(b'# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n'+ya(specification(c,rows)))
  (ROOT/steel_rel(c)).write_text(steel_text(c))

def registration_commit(paths):
 files=[RUNNER,PLAN,ROSTER]+[p for c in CELLS for p in (spec_rel(c),steel_rel(c))]
 cs={first_add(p) for p in files}
 if len(cs)!=1:raise RuntimeError(f'registration not in one first commit: {cs}')
 reg=cs.pop()
 for p in files:frozen(p,reg)
 if git('ls-tree','-r','--name-only',reg,'--',*[lock_rel(c) for c in CELLS],*[run_rel(c) for c in CELLS]).strip():raise RuntimeError('registration contains lock/result')
 rows=loaded_roster(paths);schema=json.loads(git('show',f'{reg}:schemas/hypothesis.schema.json'))
 for c in CELLS:
  spec=yaml.safe_load((ROOT/spec_rel(c)).read_text())
  if spec!=specification(c,rows) or not Draft202012Validator(schema).is_valid(spec):raise RuntimeError(f'registered spec changed/invalid: {hid(c)}')
 return reg

def lock_payload(c,reg):return dict(hypothesis_id=hid(c),family_id=FAMILY,family_size=4,registration_commit=reg,source_sha256=SOURCE_SHA,key_roster_sha256=ROSTER_SHA,key_roster_path=ROSTER,source_records=SOURCES,manifest_sha256=MANIFEST_HASHES,selected_values_or_null_masks_read_before_locks=False,provenance_limit='IMF source is one global Brent price series; WDI country exposure is a fuel share of merchandise exports, not net fuel trade.')
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
 # First numeric and null-mask access. This caller must have verified all four committed source locks.
 oil=pq.read_table(paths['oil'],columns=['region','period','value']).to_pandas()
 oil=oil[oil.region=='W00'];om={str(k):float(v) for k,v in zip(oil.period,oil.value)}
 shocks={};bad_years=[]
 for t in YEARS:
  annual=[]
  for y in (t-1,t):
   z=[om.get(f'{y}M{m}',float('nan')) for m in range(1,13)]
   annual.append(sum(z)/12 if len(z)==12 and all(math.isfinite(v) and v>0 for v in z) else float('nan'))
  shocks[t]=math.log(annual[1]/annual[0]) if all(math.isfinite(v) and v>0 for v in annual) else float('nan')
  if not math.isfinite(shocks[t]):bad_years.append(t)
 iso={c.alpha_3 for c in pycountry.countries};values={}
 for role,p in paths.items():
  if role=='oil':continue
  d=pq.read_table(p,columns=['country_iso3','indicator_id','year','value','obs_status']).to_pandas()
  d=d[d.country_iso3.isin(iso)]
  if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate national measured key: {role}')
  status=d.obs_status.fillna('').astype(str).map(lambda s:s not in ('','A'))
  d.loc[status,'value']=float('nan')
  values[role]={(str(c),int(y)):float(v) for c,y,v in zip(d.country_iso3,d.year,d.value)}
 return shocks,values,bad_years

def panel(c,roster,shocks,values,bad_years):
 role=c[0];rows=[];drop=Counter();eligible=[(country,t) for country,t,s in roster if s==SOURCES[role]['series_id']]
 shares={}
 for country in {country for country,t in eligible}:
  z=[values['fuel'].get((country,y),float('nan')) for y in BASE_YEARS]
  z=[v for v in z if math.isfinite(v) and 0<=v<=100]
  shares[country]=sum(z)/len(z) if len(z)>=3 else float('nan')
 for country,t in sorted(eligible):
  fuel=shares[country];shock=shocks[t]
  if not math.isfinite(fuel):drop['baseline_fuel_share_missing_or_out_of_range']+=1;continue
  if not math.isfinite(shock):drop['oil_month_missing_or_nonpositive']+=1;continue
  z=[values[role].get((country,y),float('nan')) for y in (t-2,t,t+2)]
  inc=values['income'].get((country,t),float('nan'))
  if not all(math.isfinite(v) for v in [*z,inc]):drop['outcome_or_income_missing_or_nonfinite']+=1;continue
  if inc<=0:drop['nonpositive_real_income']+=1;continue
  if role=='ca' and not all(-100<=v<=100 for v in z):drop['current_account_range']+=1;continue
  if role=='invest' and not all(0<=v<=100 for v in z):drop['investment_range']+=1;continue
  if role in ('income','cons') and not all(v>0 for v in z):drop['nonpositive_real_outcome']+=1;continue
  base=math.log(z[1]) if role in ('income','cons') else z[1]
  prior=math.log(z[1]/z[0]) if role in ('income','cons') else z[1]-z[0]
  future=math.log(z[2]/z[1]) if role in ('income','cons') else z[2]-z[1]
  rows.append(dict(country_iso3=country,shock_year=t,x_raw=shock*fuel/100,fuel_share=fuel,y=future,prior=prior,baseline=base,log_income=math.log(inc)))
 p=pd.DataFrame(rows,columns=['country_iso3','shock_year','x_raw','fuel_share','y','prior','baseline','log_income'])
 cnt=p.country_iso3.value_counts();small=p.country_iso3.map(cnt).lt(MIN_ROWS_PER_COUNTRY)
 drop['country_below_five_complete_years']+=int(small.sum())
 p=p.loc[~small].sort_values(['country_iso3','shock_year']).reset_index(drop=True)
 gate=dict(key_roster_rows=len(eligible),key_roster_countries=len({country for country,t in eligible}),valid_rows_before_country_floor=len(rows),valid_rows=len(p),valid_countries=int(p.country_iso3.nunique()),valid_years=int(p.shock_year.nunique()),exporter_countries=int(p.loc[p.fuel_share>=EXPORTER_SHARE,'country_iso3'].nunique()),exporter_rows=int((p.fuel_share>=EXPORTER_SHARE).sum()),rows_per_year={str(t):int((p.shock_year==t).sum()) for t in YEARS},oil_invalid_years=bad_years,dropped=dict(sorted(drop.items())),selected_values_read_after_committed_locks=True)
 return p,gate

def rhs(c):return 'x + prior + baseline' + ('' if c[0]=='income' else ' + log_income') + ' + C(country_iso3) + C(shock_year)'
def reduced_rhs(c):return 'prior + baseline' + ('' if c[0]=='income' else ' + log_income') + ' + C(country_iso3) + C(shock_year)'
def concentration(p,resid):
 ss=np.asarray(resid,float)**2;total=float(ss.sum());top=max(1,math.ceil(.01*len(ss)))
 if not math.isfinite(total) or total<=0:return dict(residual_sd=0.,top_one_percent_ss_share=1.,top_country_ss_share=1.,top_year_ss_share=1.)
 return dict(residual_sd=math.sqrt(total/len(ss)),top_one_percent_ss_share=float(sum(sorted(ss,reverse=True)[:top])/total),top_country_ss_share=float(p.assign(ss=ss).groupby('country_iso3').ss.sum().max()/total),top_year_ss_share=float(p.assign(ss=ss).groupby('shock_year').ss.sum().max()/total))
def estimate(c,p,gate):
 fail=[]
 if gate['valid_rows']<MIN_ROWS:fail.append('min_valid_rows')
 if gate['valid_countries']<MIN_COUNTRIES:fail.append('min_valid_countries')
 if gate['valid_years']<MIN_YEARS:fail.append('min_valid_years')
 if gate['exporter_countries']<MIN_EXPORTER_COUNTRIES:fail.append('min_exporter_countries')
 if gate['exporter_rows']<MIN_EXPORTER_ROWS:fail.append('min_exporter_rows')
 if fail:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 mean=float(p.x_raw.mean());sd=float(p.x_raw.std(ddof=0))
 if not math.isfinite(sd) or sd<=0:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['nonzero_pooled_exposure_sd'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 p=p.copy();p['x']=(p.x_raw-mean)/sd
 xm=smf.ols('x ~ '+reduced_rhs(c),data=p);ym=smf.ols('y ~ '+reduced_rhs(c),data=p)
 if np.linalg.matrix_rank(xm.exog)!=xm.exog.shape[1] or np.linalg.matrix_rank(ym.exog)!=ym.exog.shape[1]:
  return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['residual_design_rank'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 xc=concentration(p,xm.fit().resid);yc=concentration(p,ym.fit().resid)
 gate.update(exposure_pooled_mean=mean,exposure_pooled_sd=sd,residual_exposure=xc,residual_outcome=yc)
 if xc['residual_sd']<MIN_RESIDUAL_X_SD:fail.append('min_residual_exposure_sd')
 if yc['residual_sd']<MIN_RESIDUAL_Y[c[0]]:fail.append('min_residual_outcome_sd')
 for a,info,t1,tc,ty in [('exposure',xc,MAX_TOP1_X,MAX_TOP_COUNTRY_X,MAX_TOP_YEAR_X),('outcome',yc,MAX_TOP1_Y,MAX_TOP_COUNTRY_Y,MAX_TOP_YEAR_Y)]:
  if info['top_one_percent_ss_share']>t1:fail.append('top_one_percent_'+a+'_concentration')
  if info['top_country_ss_share']>tc:fail.append('top_country_'+a+'_concentration')
  if info['top_year_ss_share']>ty:fail.append('top_year_'+a+'_concentration')
 if fail:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 m=smf.ols('y ~ '+rhs(c),data=p)
 if np.linalg.matrix_rank(m.exog)!=m.exog.shape[1]:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['primary_design_rank'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 country_codes=pd.Categorical(p.country_iso3).codes;year_codes=pd.Categorical(p.shock_year).codes
 fit=m.fit(cov_type='cluster',cov_kwds={'groups':np.column_stack([country_codes,year_codes]),'use_correction':True,'df_correction':True},use_t=False)
 beta,se=float(fit.params['x']),float(fit.bse['x']);df=min(gate['valid_countries'],gate['valid_years'])-1
 if not(math.isfinite(beta) and math.isfinite(se) and se>0):return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['finite_two_way_cluster_uncertainty'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 pv=float(2*student_t.sf(abs(beta/se),df));crit=float(student_t.ppf(.995,df))
 if not(math.isfinite(pv) and math.isfinite(crit)):return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['finite_t_inference'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 primary=dict(beta=beta,two_way_cluster_se=se,p_two_sided=pv,confidence_level=.99,confidence_interval=[beta-crit*se,beta+crit*se],n_rows=len(p),n_countries=gate['valid_countries'],n_years=gate['valid_years'],df_inference=df,model_rank=int(fit.model.rank),model_columns=int(m.exog.shape[1]),exposure_pooled_sd=sd,residual_exposure=xc,residual_outcome=yc,method='country/year FE OLS with baseline and prior outcome trend; two-way country/year CR1 cluster t(min(G,T)-1)')
 folds=[]
 for omit in range(5):
  q=p[p.country_iso3.map(lambda s:int(hashlib.sha256(s.encode()).hexdigest(),16)%5!=omit)]
  if len(q)<MIN_FOLD_ROWS or q.country_iso3.nunique()<MIN_FOLD_COUNTRIES:fail.append(f'fold_{omit}_coverage');continue
  f=smf.ols('y ~ '+rhs(c),data=q)
  if np.linalg.matrix_rank(f.exog)!=f.exog.shape[1]:fail.append(f'fold_{omit}_rank');continue
  b=float(f.fit().params['x'])
  if not math.isfinite(b):fail.append(f'fold_{omit}_finite');continue
  folds.append(dict(omitted_hash_fold=omit,rows=len(q),countries=int(q.country_iso3.nunique()),beta=b))
 if fail:return dict(sample=gate,primary=primary,hash_folds=folds,gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 return dict(sample=gate,primary=primary,hash_folds=folds,gate_failures=[],holm_adjusted_p=None,verdict='PENDING_FAMILY')

def holm(results):
 ranked=sorted((r['primary']['p_two_sided'] if r['primary'] is not None and not r['gate_failures'] else 1.,h) for h,r in results.items());running=0.;adj={}
 for i,(p,h) in enumerate(ranked):running=max(running,min(1.,(len(CELLS)-i)*p));adj[h]=running
 for c in CELLS:
  r=results[hid(c)]
  if r['gate_failures']:r['holm_adjusted_p']=1.;r['verdict']='INCONCLUSIVE';continue
  r['holm_adjusted_p']=adj[hid(c)];beta=r['primary']['beta'];pos=sum(f['beta']>0 for f in r['hash_folds']);neg=sum(f['beta']<0 for f in r['hash_folds'])
  r['positive_folds']=pos;r['negative_folds']=neg
  if beta>=c[3] and adj[hid(c)]<=ALPHA and pos>=MIN_SAME_SIGN_FOLDS:r['verdict']='SUPPORTED'
  elif beta<=-c[3] and adj[hid(c)]<=ALPHA and neg>=MIN_SAME_SIGN_FOLDS:r['verdict']='REFUTED'
  else:r['verdict']='PARTIAL'

def artifacts(c,result,reg,lock,stamp):
 id=hid(c);diag=dict(hypothesis_id=id,family_id=FAMILY,family_size=4,registration_commit=reg,source_lock_commit=lock,source_sha256=SOURCE_SHA,source_key_roster_sha256=ROSTER_SHA,runner=RUNNER,run_utc=stamp,predictor_series=['imf_pcps:POILBRE','world_bank_wdi:TX.VAL.FUEL.ZS.UN'],outcome_series=SOURCES[c[0]]['series_id'],registered_direction='+',thresholds=threshold(c),result=result,limitations=LIMITS,correction=CORRECTION)
 db=js(diag);source=dict(publisher='IMF Primary Commodity Prices and World Bank World Development Indicators',source_sha256=SOURCE_SHA,source_lock_commit=lock,source_lock_manifest=lock_rel(c),key_roster_sha256=ROSTER_SHA,input_vintages=[{'path':v['path'],'sha256':v['sha256']} for v in SOURCES.values()],license='IMF attributed data use; WDI CC BY 4.0; derived summaries only',contains_source_values=False)
 manifest=dict(hypothesis_id=id,status=result['verdict'],run_utc=stamp,runner=RUNNER,preregistration_commit=reg,source=source,family_id=FAMILY,family_size=4,sample=result['sample'],correction=CORRECTION)
 packet=dict(packet_version=1,hypothesis={'id':id,'path':spec_rel(c)},preregistration={'commit':reg,'steelman':steel_rel(c),'source_plan':PLAN,'key_roster':ROSTER},source=source,family={'id':FAMILY,'size':4,'members':[hid(x) for x in CELLS],'holm_alpha':ALPHA,'interpretation':'One global Brent shock interacted with fixed baseline fuel-export orientation; four correlated future macro endpoints'},reproduction={'runner':RUNNER,'command':f'python3 {RUNNER} verify --source-root /path/to/IESET','result_sha256':hashlib.sha256(db).hexdigest()},result=result,limitations=LIMITS,correction=CORRECTION)
 card=f'# Result card: {id}\n\nVerdict: **{result["verdict"]}**. Predictor: Brent shock × fixed baseline fuel-export share; outcome: {c[2]}.\n\nRegistration `{reg}`; source lock `{lock}`. Complete country-years: {result["sample"]["valid_rows"]} in {result["sample"]["valid_countries"]} countries and {result["sample"]["valid_years"]} shock years.\n'
 if result['gate_failures']:card+=f'\nFrozen gate failures: {", ".join(result["gate_failures"])}.\n'
 if result['primary']:
  q=result['primary'];card+=f'\nBeta={q["beta"]:+.6g} {c[4]} per +1 exposure SD; two-way cluster SE={q["two_way_cluster_se"]:.6g}; two-sided p={q["p_two_sided"]:.6g}; Holm p={result["holm_adjusted_p"]:.6g}; 99% CI={q["confidence_interval"]}.\n'
 card+='\nDescriptive prospective calibration only; zero causal, policy, school, position or featured credit.\n'
 wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"+"root=Path(__file__).resolve().parents[3]\n"+f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
 return {'diagnostics.json':db,'manifest.yaml':ya(manifest),'evidence_packet.yaml':ya(packet),'result_card.md':card.encode(),'replication.py':wrapper.encode(),'hypothesis.yaml':(ROOT/spec_rel(c)).read_bytes(),'chart_data.json':js({'hypothesis_id':id,'family_id':FAMILY,'verdict':result['verdict'],'primary':result['primary']})}
def report_text(results,reg,locks):
 lines=['# IMF Brent shock × fuel-export orientation: frozen future macro results','',f'Registration `{reg}`; four separate source locks from `{next(iter(locks.values()))}` through `{list(locks.values())[-1]}`.','','| Future outcome | Verdict | Rows / countries / years | Beta per +1 exposure SD | Raw p | Holm p | Gate failures |','| --- | --- | ---: | ---: | ---: | ---: | --- |']
 for c in CELLS:
  r=results[hid(c)];q=r['primary'];g=r['sample'];line=f'| {c[2]} | {r["verdict"]} | {g["valid_rows"]} / {g["valid_countries"]} / {g["valid_years"]} | '
  line+=(f'{q["beta"]:+.5g} | {q["p_two_sided"]:.5g} | {r["holm_adjusted_p"]:.5g} | ' if q else '— | — | 1 | ')
  line+=f'{", ".join(r["gate_failures"]) or "none"} |';lines.append(line)
 lines+=['','The four outcomes share the same common oil price shock and baseline country fuel-export orientation. Holm adjusts the four registered tests, not the broader archive-selection history. Two-way country/year uncertainty still has only thirteen years. Fuel export share omits fuel imports and is not net-oil exposure. No causal, policy, position, school or featured credit.','']
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
 if (ROOT/REPORT).exists() or any((ROOT/run_rel(c)).exists() for c in CELLS):raise FileExistsError('result already exists')
 stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
 for c in CELLS:
  folder=ROOT/run_rel(c);folder.mkdir(parents=True)
  for name,data in artifacts(c,results[hid(c)],reg,locks[hid(c)],stamp).items():(folder/name).write_bytes(data)
 (ROOT/REPORT).write_text(report_text(results,reg,locks))
def verify_results(results,reg,locks):
 for c in CELLS:
  folder=ROOT/run_rel(c);saved=json.loads((folder/'diagnostics.json').read_text());expected=artifacts(c,results[hid(c)],reg,locks[hid(c)],saved['run_utc'])
  for name,data in expected.items():
   p=folder/name
   if name.endswith('.json'):equal_close(json.loads(p.read_text()),json.loads(data),f'{hid(c)}:{name}')
   elif name.endswith('.yaml') and name!='hypothesis.yaml':equal_close(yaml.safe_load(p.read_text()),yaml.safe_load(data),f'{hid(c)}:{name}')
   elif p.read_bytes()!=data:raise AssertionError(f'exact replay mismatch: {p}')
 if (ROOT/REPORT).read_text()!=report_text(results,reg,locks):raise AssertionError('family report differs from replay')
def main():
 parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);parser.add_argument('action',choices=['preflight','register','lock','measure','verify']);parser.add_argument('--source-root',type=Path,default=ROOT);parser.add_argument('--cell',choices=[c[0] for c in CELLS]);args=parser.parse_args()
 paths=source_paths(args.source_root)
 if args.action=='preflight':
  rows=key_roster(paths);counts={c[0]:{'rows':sum(r[2]==SOURCES[c[0]]['series_id'] for r in rows),'countries':len({r[0] for r in rows if r[2]==SOURCES[c[0]]['series_id']})} for c in CELLS}
  print(json.dumps({'family_size':4,'source_key_rows':len(rows),'source_key_roster_sha256':hashlib.sha256(roster_bytes(rows)).hexdigest(),'per_cell':counts,'years':[min(YEARS),max(YEARS)],'selected_values_or_null_masks_opened':False},sort_keys=True));return 0
 if args.action=='register':write_registration(paths);print('wrote four-cell key-only registration; commit before locks');return 0
 reg=registration_commit(paths)
 if args.action=='lock':
  if args.cell is None:raise ValueError('--cell required')
  c=next(c for c in CELLS if c[0]==args.cell);i=CELLS.index(c)
  if i and not (ROOT/lock_rel(CELLS[i-1])).exists():raise RuntimeError('prior lock must be committed')
  if i and not ancestor(reg,first_add(lock_rel(CELLS[i-1]))):raise RuntimeError('prior lock must be committed')
  write_lock(c,reg);print(f'wrote lock for {hid(c)}; commit this file alone');return 0
 locks=lock_commits(reg);roster=loaded_roster(paths);shocks,values,bad_years=selected_values(paths)
 results={}
 for c in CELLS:
  p,g=panel(c,roster,shocks,values,bad_years);results[hid(c)]=estimate(c,p,g)
 holm(results)
 if args.action=='measure':
  write_results(results,reg,locks)
  print(json.dumps({h:{'verdict':r['verdict'],'rows':r['sample']['valid_rows'],'countries':r['sample']['valid_countries'],'years':r['sample']['valid_years'],'gate_failures':r['gate_failures'],'beta':r['primary']['beta'] if r['primary'] else None,'p':r['primary']['p_two_sided'] if r['primary'] else None,'holm_p':r['holm_adjusted_p']} for h,r in results.items()},indent=2))
 else:verify_results(results,reg,locks);print('verified exact replay',FAMILY,{h:r['verdict'] for h,r in results.items()})
 return 0
if __name__=='__main__':raise SystemExit(main())
