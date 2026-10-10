#!/usr/bin/env python3
"""Frozen five-cell Internet adoption and later ILO labour outcomes family.

Preflight, registration and locks inspect source hashes, manifests and keys only.
Numeric values and status/null masks are accessed only after five separate
committed source locks, and exact replay checks source and result custody.
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
FAMILY='ilo_internet_forward_labour_2026_10_10'
RUNNER='scripts/run_ilo_internet_labour_2026.py'
PLAN='engine/audits/ilo_internet_labour_prereg_2026-10-10.md'
REPORT='engine/audits/ilo_internet_labour_results_2026-10-10.md'
ROSTER='data/pinned_evidence/ilo_internet_labour_2026_key_roster.csv'
ROSTER_SHA='240209e929ef63138d1e182ac24f61b2d4ac474bb3950a48de65469e4aac182e'
BOOT='data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml'
JULY='data/manifests/fetch_run_2026-07-23T152624Z.yaml'
NET_MAN='data/manifests/fetch_run_2026-05-05T210519Z.yaml'
GDP_MAN='data/manifests/fetch_run_2026-05-05T200056Z.yaml'
MANIFEST_HASHES={BOOT:'e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e',JULY:'367fc796f8738908e3be217054f798e7684d29acee3d7304107136aecd05cdb6',NET_MAN:'5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112',GDP_MAN:'a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945'}
def rec(pub,code,file,hash,man,url):
 return dict(publisher=pub,series_id=code,path=f'data/vintages/{pub}/{file}',sha256=hash,manifest=man,source_url=url,license='CC BY 4.0')
SOURCES={
 'internet':rec('world_bank_wdi','IT.NET.USER.ZS','IT.NET.USER.ZS@2026-05-05T203400Z.parquet','c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8',NET_MAN,'https://data.worldbank.org/indicator/IT.NET.USER.ZS'),
 'income':rec('world_bank_wdi','NY.GDP.PCAP.KD','NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet','0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f',GDP_MAN,'https://data.worldbank.org/indicator/NY.GDP.PCAP.KD'),
 'une':rec('ilostat','UNE_2EAP_SEX_AGE_RT_A','UNE_2EAP_SEX_AGE_RT_A@2026-07-23T152620Z.parquet','dcc17617c0ef8f037fc414944d01aeab7a0a71370576b29ff416de18c5348990',JULY,'https://rplumber.ilo.org/data/indicator/?id=UNE_2EAP_SEX_AGE_RT_A&format=.csv'),
 'eap':rec('ilostat','EAP_2WAP_SEX_AGE_RT_A','EAP_2WAP_SEX_AGE_RT_A@2026-07-23T152621Z.parquet','17e1ed07bf963364d866304ff6384dbbfb8bc06d5ba30b42a474098c2c54e395',JULY,'https://rplumber.ilo.org/data/indicator/?id=EAP_2WAP_SEX_AGE_RT_A&format=.csv'),
 'poor':rec('ilostat','SDG_0111_SEX_AGE_RT_A','SDG_0111_SEX_AGE_RT_A@2026-04-30T114749Z.parquet','1d487136180283cc5f2082592bf2530d38a3b910f78c14fe8736a911f4ed6fa3',BOOT,'https://rplumber.ilo.org/data/indicator/?id=SDG_0111_SEX_AGE_RT_A&format=.csv'),
 'ear':rec('ilostat','EAR_EHRA_SEX_NB_A','EAR_EHRA_SEX_NB_A@2026-07-23T152623Z.parquet','b05db89172021502c9713373b69590e939d66c0e01c26303308ee163a1121c44',JULY,'https://rplumber.ilo.org/data/indicator/?id=EAR_EHRA_SEX_NB_A&format=.csv'),
}
SOURCE_SHA=hashlib.sha256('|'.join(SOURCES[k]['sha256'] for k in SOURCES).encode()).hexdigest()
# role, slug, outcome label, expected sign, meaningful absolute beta, beta unit
CELLS=(('une','unemployment','unemployment rate, age 15+','-',.35,'percentage points'),('eap','participation','labour-force participation rate, age 15+','+',.35,'percentage points'),('poor','working_poverty','working poverty rate among employed people, age 15+','-',.35,'percentage points'),('ear','female_hourly_earnings_ratio','female-to-male mean hourly earnings ratio','+',.015,'log points'),('eap','female_participation_gap','female minus male labour-force participation gap, age 15+','+',.35,'percentage points'))
YEARS=tuple(range(2005,2018));ALPHA=.05
MIN_ROWS={'une':500,'eap':500,'poor':400,'ear':150,'gap':500}
MIN_COUNTRIES={'une':50,'eap':50,'poor':40,'ear':18,'gap':50}
MIN_YEARS={'une':10,'eap':10,'poor':10,'ear':10,'gap':10}
MIN_ROWS_PER_COUNTRY=5
MIN_X_RESID_SD=.15;MIN_Y_RESID_SD={'une':.15,'eap':.15,'poor':.15,'ear':.005,'gap':.15}
MAX_TOP1=.30;MAX_COUNTRY=.18;MAX_YEAR=.35
MIN_FOLD_ROWS={'une':350,'eap':350,'poor':280,'ear':105,'gap':350}
MIN_FOLD_COUNTRIES={'une':35,'eap':35,'poor':28,'ear':13,'gap':35}
MIN_SAME_SIGN_FOLDS=4
CORRECTION=dict(disposition='descriptive_calibration_only',causal_credit=0,policy_score_eligible=False,policy_score_credit=0,school_score_eligible=False,school_score_credit=0,featured_eligible=False)
LIMITS=['The Internet uptake series and ILO labour outcomes are national descriptive statistics; common trends, income, education, institutions and labour demand can confound their association.','Unemployment and labour-force participation series are modelled ILO estimates and are correlated; working poverty is also an ILO modelled indicator. Wage data use national survey sources and have narrower coverage.','Source-code continuity is required within an outcome window, but a stable code does not rule out method breaks, revisions, earnings denominator changes or cross-country measurement differences.','Gender hourly earnings ratios compare female/male earnings in the same source, country and year, canceling local currency units; they are not adjusted pay gaps for comparable jobs.','The five outcomes share an Internet predictor and overlapping countries; Holm controls only this registered family, not the archive-wide selection history. No causal, policy, school, position or featured credit.']
def cellkey(c):return 'gap' if c[1]=='female_participation_gap' else c[0]
def hid(c):return f'ilo_internet_{c[1]}_forward_2026'
def spec_rel(c):return f'hypotheses/labour/{hid(c)}.yaml'
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
  need={'country_iso3','indicator_id','year','value','obs_status'} if r['publisher']=='world_bank_wdi' else {'country_iso3','source','indicator','sex','year','value','obs_status'}
  if role in ('une','eap','poor'):need.add('classif1')
  if not need.issubset(fields):raise RuntimeError(f'source schema changed: {role}')
  paths[role]=p
 for m,h in MANIFEST_HASHES.items():
  p=ROOT/m
  if not p.is_file() or sha(p)!=h:raise RuntimeError(f'manifest hash changed: {m}')
  entries=yaml.safe_load(p.read_text()).get('entries',[])
  for role,r in SOURCES.items():
   if r['manifest']!=m:continue
   match=[e for e in entries if e.get('publisher')==r['publisher'] and e.get('series_id')==r['series_id'] and e.get('parquet_path')==r['path'] and e.get('sha256')==r['sha256'] and str(e.get('license')).lower().replace('-','_') in ('cc_by_4.0','cc_by_4_0')]
   if len(match)!=1:raise RuntimeError(f'exact manifest entry missing: {role}')
 return paths

def key_roster(paths):
 iso={c.alpha_3 for c in pycountry.countries};keys={}
 for role,p in paths.items():
  if role in ('internet','income'):
   d=pq.read_table(p,columns=['country_iso3','indicator_id','year']).to_pandas()
   if set(d.indicator_id.dropna())!={SOURCES[role]['series_id']}:raise RuntimeError(f'indicator key mismatch: {role}')
   d=d[d.country_iso3.isin(iso)]
   if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate WDI national key: {role}')
   keys[role]={(str(x.country_iso3),int(x.year)) for x in d.itertuples()};continue
  cs=['country_iso3','source','indicator','sex','year']+(['classif1'] if role!='ear' else [])
  d=pq.read_table(p,columns=cs).to_pandas();d=d[d.country_iso3.isin(iso)]
  if set(d.indicator.dropna())!={SOURCES[role]['series_id'].removesuffix('_A')}:raise RuntimeError(f'ILO indicator key mismatch: {role}')
  if role in ('une','poor'):d=d[(d.sex=='SEX_T')&(d.classif1=='AGE_YTHADULT_YGE15')]
  elif role=='eap':d=d[(d.sex.isin(['SEX_T','SEX_F','SEX_M']))&(d.classif1=='AGE_YTHADULT_YGE15')]
  else:d=d[d.sex.isin(['SEX_F','SEX_M'])]
  if d.duplicated(['country_iso3','year','source','sex']).any():raise RuntimeError(f'duplicate ILO selector key: {role}')
  keys[role]={}
  for (country,year,source),z in d.groupby(['country_iso3','year','source'],dropna=False):
   sexes=set(z.sex)
   keys[role][(str(country),int(year),str(source))]=sexes
 rows=[]
 for c in CELLS:
  role=c[0];needed={'SEX_F','SEX_M'} if c[1] in ('female_participation_gap','female_hourly_earnings_ratio') else {'SEX_T'}
  for country in sorted(iso):
   sources={s for cc,y,s in keys[role] if cc==country}
   for t in YEARS:
    if not all((country,y) in keys['internet'] for y in (t-2,t)) or (country,t) not in keys['income']:continue
    valid=[s for s in sources if all(needed.issubset(keys[role].get((country,y,s),set())) for y in (t-2,t,t+2))]
    if len(valid)>1:raise RuntimeError(f'ambiguous source for {c[1]} {country} {t}: {valid}')
    if valid:rows.append((c[1],country,t,valid[0]))
 return sorted(rows)
def roster_bytes(rows):
 f=io.StringIO();w=csv.writer(f,lineterminator='\n');w.writerow(['cell','country_iso3','anchor_year','ilo_source']);w.writerows(rows);return f.getvalue().encode()
def loaded_roster(paths):
 rows=key_roster(paths);p=ROOT/ROSTER
 if sha(p)!=ROSTER_SHA or p.read_bytes()!=roster_bytes(rows):raise RuntimeError('frozen key roster differs')
 return rows

def threshold(c):
 k=cellkey(c)
 return dict(family_id=FAMILY,family_size=len(CELLS),family_alpha=ALPHA,holm_alpha=ALPHA,registered_beta_sign=c[3],meaningful_abs_beta=c[4],beta_unit=c[5]+' per +10 percentage-point prior Internet uptake',source_key_roster_path=ROSTER,source_key_roster_sha256=ROSTER_SHA,source_lock_path=lock_rel(c),family_source_sha256=SOURCE_SHA,min_valid_rows=MIN_ROWS[k],min_valid_countries=MIN_COUNTRIES[k],min_years=MIN_YEARS[k],min_rows_per_country=MIN_ROWS_PER_COUNTRY,min_residual_exposure_sd=MIN_X_RESID_SD,min_residual_outcome_sd=MIN_Y_RESID_SD[k],max_top_one_percent_exposure_ss_share=MAX_TOP1,max_top_country_exposure_ss_share=MAX_COUNTRY,max_top_year_exposure_ss_share=MAX_YEAR,max_top_one_percent_outcome_ss_share=MAX_TOP1,max_top_country_outcome_ss_share=MAX_COUNTRY,max_top_year_outcome_ss_share=MAX_YEAR,min_fold_rows=MIN_FOLD_ROWS[k],min_fold_countries=MIN_FOLD_COUNTRIES[k],min_same_sign_hash_folds=MIN_SAME_SIGN_FOLDS,causal_credit=0,policy_score_eligible=False,policy_score_credit=0,school_score_eligible=False,school_score_credit=0,featured_eligible=False)
def specification(c,rows):
 role,slug,label,sign,delta,unit=c;countries=sorted({r[1] for r in rows if r[0]==slug})
 outcome_source=f'ilostat:{SOURCES[role]["series_id"]}'
 outcome_transform={'female_hourly_earnings_ratio':'log of female mean hourly earnings divided by male mean hourly earnings, both positive local-currency levels from identical ILO country-year-source keys','female_participation_gap':'female minus male participation percentages (percentage points), both same ILO country-year-source keys'}.get(slug,'ILO total-sex age-15+ percentage rate')
 future='Natural log ratio at t+2 minus natural log ratio at t.' if role=='ear' else 'Percentage-point change in selected outcome from t to t+2.'
 return {'hypothesis_id':hid(c),'version':1,'status':'pre_registered','topic':'labour','claim_direction':sign,
  'claim':f'Among fixed national 2005–2017 anchor years, a larger t−2 to t increase in the share of people using the Internet predicts a {"lower" if sign=="-" else "higher"} subsequent t to t+2 change in {label}, conditional on its earlier change and level, baseline real income, country and anchor-year effects.',
  'evidence_type':'associational','methodology_note':'One of five distinct labour endpoints in a single prospective descriptive WDI Internet × ILOSTAT family. Source keys, exact source identity and hashes only were inspected before registration. Selected numeric values and status/null masks remain sealed through five separate committed source locks.',
  'sample':{'countries':countries,'period':[2003,2019],'temporal_structure':'panel','exclusion_rules':[
   'Use only the frozen cell-specific national country, anchor-year and exact ILO source-key roster. Require the identical ILO source code at t−2, t and t+2 and both female and male codes at each time for derived gender outcomes.',
   'Require finite WDI Internet percentages at t−2 and t within [0,100], positive finite WDI real GDP per person at t, and finite ILO outcomes at t−2, t and t+2.',
   'ILO rates must be in [0,100]; hourly female and male earnings must both be positive in the same source/year/local currency. Retain countries with at least five complete anchor years. No imputation, winsorization, source substitution or missing-as-zero recoding.'
  ]},
  'variables':{'treatment':[{'name':'prior_two_year_internet_uptake','source':'world_bank_wdi:IT.NET.USER.ZS','transformation':'(Internet use percent at t minus percent at t−2) divided by 10; +1 exposure unit is +10 percentage points.','notes':'National diffusion measure, not a policy intervention or exogenous treatment.'}],
   'outcome':[{'name':'future_'+slug+'_change','source':outcome_source,'transformation':outcome_transform+'; '+future,'notes':label}],
   'controls':[{'name':'prior_two_year_outcome_change','source':outcome_source,'transformation':'Same selected outcome change t−2→t in headline units.'},{'name':'baseline_outcome_level','source':outcome_source,'transformation':'Selected outcome level at t, in percentage points or log ratio.'},{'name':'baseline_log_real_income','source':'world_bank_wdi:NY.GDP.PCAP.KD','transformation':'Natural log of positive real GDP per person at t.'}]},
  'estimator':{'template':'panel_fe','fixed_effects':['country','anchor_year'],'clustering':'country_and_anchor_year','notes':'Equal country-year OLS on prior Internet uptake /10, prior same-outcome change, baseline outcome, log real GDP per person, country and anchor-year effects. Two-way country/year CR1 cluster covariance; two-sided Student t with min(country clusters,year clusters)-1 degrees of freedom. Holm over all five cells, with failed cells assigned p=1. Five fixed country-hash omission folds assess direction.'},
  'falsification':{'test':FAMILY,'rule':f'INCONCLUSIVE if exact sources, sample, residual variation/concentration, rank, two-way cluster uncertainty or fold coverage fails. SUPPORTED iff beta has registered sign and magnitude ≥{delta} {unit} per +10 Internet percentage points, Holm-adjusted two-sided p≤0.05, and at least four of five hash-fold slopes have that sign. REFUTED iff the reverse beta meets the same magnitude, Holm and fold requirements. Otherwise PARTIAL.','threshold':threshold(c)},
  'prior_confidence':.5,'disclosure':'Internet adoption correlates with development, education, labour demand and institutional change. Modelled ILO rates and national survey earnings have comparability limits. Temporal order and controls cannot establish effects. Five outcomes share one predictor; zero causal, policy, school, position and featured credit.',
  'steelman':steel_rel(c),'scope':{'period':[2003,2019],'countries':countries,'outcome_dim':['employment_labour'],'policy_family':['none'],'treatment_tags':['internet_use_diffusion','digital_adoption']},'covers_claims':[],'linked_hypotheses':[],'linked_conditions':[]}

def plan_text(rows):
 counts={c[1]:(sum(r[0]==c[1] for r in rows),len({r[1] for r in rows if r[0]==c[1]})) for c in CELLS}
 lines=['# Internet diffusion and later labour outcomes — prospective registration','',
  'The five-cell family asks whether earlier national Internet-use growth predicts later changes in unemployment, total labour-force participation, working poverty, the female/male mean hourly earnings ratio, and the female-minus-male participation gap. The first, second, third and fifth are percentage rates or gaps; the earnings ratio is a within-country/year/source local-currency ratio. The outcomes have distinct labour meanings but share the same exposure and overlapping ILO sources. Prior Internet→business registrations, services employment share, high-tech exports and patenting are different directed questions, not independent confirmation. This selected family is descriptive.','',
  '## Value-blind source-key freeze','',
  f'Anchor years t are 2005–2017, so outcomes end in 2019 before COVID. The roster has {len(rows):,} cell-specific structural country-year-source keys. Each ILO cell requires one identical source code at t−2, t and t+2; gender cells require both sexes within the same source/year. WDI files are broad country×year grids even where numeric values are null, so the counts below are upper bounds. Before this registration no selected numeric value, status/null mask, outcome change, sign or estimate was opened. This plan, five specs and steelmen, runner and key roster form one first-add commit. Five separate one-file source-lock commits must follow before any selected value access.','',
  '| Later labour outcome | Structural windows / countries | Registered sign | Meaningful beta per +10 Internet points |','| --- | ---: | --- | ---: |']
 lines += [f'| {c[2]} | {counts[c[1]][0]} / {counts[c[1]][1]} | {c[3]} | {c[4]} {c[5]} |' for c in CELLS]
 lines+=['','## Frozen measurement and failure gates','',
  'Exposure is (Internet-use percent at t minus percent at t−2)/10. Future response is selected ILO outcome change t→t+2; control its own t−2→t change and level at t plus log real GDP per person at t. Add country and anchor-year effects, two-way country/year clustered CR1 uncertainty, two-sided t with min(country,year clusters)−1 degrees of freedom, 99% descriptive intervals. Keep countries with at least five complete anchors. Require Internet and rate values in [0,100], positive wages, and positive real income. The female/male wage ratio is logged before differencing; female-minus-male participation remains a percentage-point gap. Exact ILO source continuity is required within each outcome window.','',
  'Coverage gates are cell-specific because annual national earnings surveys are much sparser than modelled ILO rate panels, but they are frozen before values: unemployment/total participation/gender participation gap ≥500 rows, ≥50 countries, ≥10 years; working poverty ≥400/40/10; hourly earnings ratio ≥150/18/10. The complete-case residual exposure SD must be ≥0.15 units (10 Internet points); residual outcome SD ≥0.15 percentage points for rates/gap, ≥0.005 log points for wages. For both residualized exposure and outcome, top 1% rows may contribute at most 30% squared variation, one country at most 18%, one year at most 35%. Five SHA256(country) mod 5 omission folds need ≥350 rows/35 countries for broad rate and gap cells, ≥280/28 for poverty and ≥105/13 for earnings; four of five slopes must match the registered direction. Rank or two-way cluster uncertainty failure is INCONCLUSIVE. Holm α=0.05 includes all five cells and assigns p=1 to failures. Material opposite sign with Holm and fold support is REFUTED; method-valid but threshold-missing is PARTIAL. No post-result substitution.','',
  '## Sources, rights and limits','',
  'All six raw parquets and four tracked fetch manifests are SHA-256 pinned. The two World Bank WDI sources and all four ILOSTAT sources are CC BY 4.0 in their exact fetch manifests. ILO unemployment and labour-force participation sources here use XA modelled source codes; working poverty is a modelled SDG rate; hourly earnings are national source observations in local currency. Only derived results are tracked, not raw source values. Source definitions: https://data.worldbank.org/indicator/IT.NET.USER.ZS ; https://ilostat.ilo.org/data/ ; https://ilostat.ilo.org/topics/working%20poverty/ ; https://ilostat.ilo.org/methods/concepts-and-definitions/description-wages-and-working-time-statistics/ .','',
  'Internet diffusion, income, education and labour-market change can share causes. The wage ratio is unadjusted for occupation or hours composition, and source continuity does not eliminate methodology changes. Thirteen years are thin for year-cluster inference. Holm is local to this family, not correction across all IESET exploration. All causal, policy, school, position and featured credit remains zero.','']
 return '\n'.join(lines)
def steel_text(c):
 sign='decrease' if c[3]=='-' else 'increase'
 return f'# Steelman: earlier Internet adoption and later {c[2]}\n\nExpanded Internet access could change search, matching, information and economic opportunity. The registered descriptive direction is a later {sign} in {c[2]} of at least {c[4]} {c[5]} per preceding +10 percentage-point Internet increase. The comparison controls its own prior change and level, real GDP per person, country and year effects.\n\nThe alternative is that schooling, structural change, income growth, institutions and labour demand drive both adoption and later labour data. ILO modelled estimates may share extrapolation structure; national wage surveys have uneven coverage and unadjusted composition. Internet access could also displace jobs, increase search-based measured unemployment, or leave poverty and gender gaps unchanged. Opposite material association refutes this registered prediction; weak, sparse or unstable evidence remains partial or inconclusive. No causal or policy inference follows.\n'
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
def lock_payload(c,reg):return dict(hypothesis_id=hid(c),family_id=FAMILY,family_size=len(CELLS),registration_commit=reg,source_sha256=SOURCE_SHA,key_roster_sha256=ROSTER_SHA,key_roster_path=ROSTER,source_records=SOURCES,manifest_sha256=MANIFEST_HASHES,selected_values_or_status_masks_read_before_locks=False,provenance_limit='ILO modelled rate estimates and national-source wage observations differ; Internet adoption is a descriptive exposure, not an intervention.')
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
 # First numeric or status/null-mask access; the caller has verified all five committed source locks.
 iso={c.alpha_3 for c in pycountry.countries};wdi={};ilo={};status_counts={}
 for role,p in paths.items():
  if role in ('internet','income'):
   d=pq.read_table(p,columns=['country_iso3','indicator_id','year','value','obs_status']).to_pandas();d=d[d.country_iso3.isin(iso)]
   if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate WDI measured key: {role}')
   wdi[role]={}
   for row in d.itertuples():
    try:v=float(row.value)
    except (TypeError,ValueError):v=float('nan')
    wdi[role][(str(row.country_iso3),int(row.year))]=v
   status_counts[role]=dict(sorted(Counter(d.obs_status.fillna('').astype(str)).items()))
  else:
   cols=['country_iso3','source','indicator','sex','year','value','obs_status']+(['classif1'] if role!='ear' else [])
   d=pq.read_table(p,columns=cols).to_pandas();d=d[d.country_iso3.isin(iso)]
   if role in ('une','poor'):d=d[(d.sex=='SEX_T')&(d.classif1=='AGE_YTHADULT_YGE15')]
   elif role=='eap':d=d[(d.sex.isin(['SEX_T','SEX_F','SEX_M']))&(d.classif1=='AGE_YTHADULT_YGE15')]
   else:d=d[d.sex.isin(['SEX_F','SEX_M'])]
   if d.duplicated(['country_iso3','year','source','sex']).any():raise RuntimeError(f'duplicate ILO measured selector key: {role}')
   ilo[role]={}
   for row in d.itertuples():
    try:v=float(row.value)
    except (TypeError,ValueError):v=float('nan')
    ilo[role][(str(row.country_iso3),int(row.year),str(row.source),str(row.sex))]=v
   status_counts[role]=dict(sorted(Counter(d.obs_status.fillna('').astype(str)).items()))
 return wdi,ilo,status_counts

def outcome(c,ilo,country,year,source):
 role,slug=c[:2];d=ilo[role]
 def v(sex):return d.get((country,year,source,sex),float('nan'))
 if slug=='female_hourly_earnings_ratio':
  f,m=v('SEX_F'),v('SEX_M')
  return math.log(f/m) if all(math.isfinite(q) and q>0 for q in (f,m)) else float('nan')
 if slug=='female_participation_gap':
  f,m=v('SEX_F'),v('SEX_M')
  return f-m if all(math.isfinite(q) and 0<=q<=100 for q in (f,m)) else float('nan')
 z=v('SEX_T')
 return z if math.isfinite(z) and 0<=z<=100 else float('nan')
def panel(c,roster,wdi,ilo):
 eligible=[r for r in roster if r[0]==c[1]];rows=[];drop=Counter()
 for _,country,t,source in eligible:
  net0=wdi['internet'].get((country,t-2),float('nan'));net1=wdi['internet'].get((country,t),float('nan'))
  inc=wdi['income'].get((country,t),float('nan'))
  if not all(math.isfinite(v) and 0<=v<=100 for v in (net0,net1)):drop['internet_missing_nonfinite_or_range']+=1;continue
  if not math.isfinite(inc) or inc<=0:drop['real_income_missing_nonpositive']+=1;continue
  z=[outcome(c,ilo,country,y,source) for y in (t-2,t,t+2)]
  if not all(math.isfinite(v) for v in z):drop['ilo_outcome_missing_nonfinite_or_range']+=1;continue
  rows.append(dict(country_iso3=country,anchor_year=t,ilo_source=source,x=(net1-net0)/10,y=z[2]-z[1],prior=z[1]-z[0],baseline=z[1],log_income=math.log(inc)))
 p=pd.DataFrame(rows,columns=['country_iso3','anchor_year','ilo_source','x','y','prior','baseline','log_income'])
 if len(p):
  cnt=p.country_iso3.value_counts();small=p.country_iso3.map(cnt).lt(MIN_ROWS_PER_COUNTRY)
  drop['country_below_five_complete_years']+=int(small.sum())
  p=p.loc[~small].sort_values(['country_iso3','anchor_year']).reset_index(drop=True)
 gate=dict(key_roster_rows=len(eligible),key_roster_countries=len({r[1] for r in eligible}),valid_rows_before_country_floor=len(rows),valid_rows=len(p),valid_countries=int(p.country_iso3.nunique()),valid_years=int(p.anchor_year.nunique()),rows_per_year={str(t):int((p.anchor_year==t).sum()) for t in YEARS},dropped=dict(sorted(drop.items())),selected_values_read_after_committed_locks=True)
 return p,gate
def rhs():return 'x + prior + baseline + log_income + C(country_iso3) + C(anchor_year)'
def reduced_rhs():return 'prior + baseline + log_income + C(country_iso3) + C(anchor_year)'
def concentration(p,resid):
 ss=np.asarray(resid,float)**2;total=float(ss.sum());top=max(1,math.ceil(.01*len(ss)))
 if not math.isfinite(total) or total<=0:return dict(residual_sd=0.,top_one_percent_ss_share=1.,top_country_ss_share=1.,top_year_ss_share=1.)
 return dict(residual_sd=math.sqrt(total/len(ss)),top_one_percent_ss_share=float(sum(sorted(ss,reverse=True)[:top])/total),top_country_ss_share=float(p.assign(ss=ss).groupby('country_iso3').ss.sum().max()/total),top_year_ss_share=float(p.assign(ss=ss).groupby('anchor_year').ss.sum().max()/total))
def estimate(c,p,gate):
 k=cellkey(c);fail=[]
 if gate['valid_rows']<MIN_ROWS[k]:fail.append('min_valid_rows')
 if gate['valid_countries']<MIN_COUNTRIES[k]:fail.append('min_valid_countries')
 if gate['valid_years']<MIN_YEARS[k]:fail.append('min_valid_years')
 if fail:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 xm=smf.ols('x ~ '+reduced_rhs(),data=p);ym=smf.ols('y ~ '+reduced_rhs(),data=p)
 xf=xm.fit();yf=ym.fit()
 if xf.model.rank!=xf.model.exog.shape[1] or yf.model.rank!=yf.model.exog.shape[1]:
  return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['residual_design_rank'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 xc=concentration(p,xf.resid);yc=concentration(p,yf.resid)
 gate.update(residual_exposure=xc,residual_outcome=yc)
 if xc['residual_sd']<MIN_X_RESID_SD:fail.append('min_residual_exposure_sd')
 if yc['residual_sd']<MIN_Y_RESID_SD[k]:fail.append('min_residual_outcome_sd')
 for name,v in [('exposure',xc),('outcome',yc)]:
  if v['top_one_percent_ss_share']>MAX_TOP1:fail.append('top_one_percent_'+name+'_concentration')
  if v['top_country_ss_share']>MAX_COUNTRY:fail.append('top_country_'+name+'_concentration')
  if v['top_year_ss_share']>MAX_YEAR:fail.append('top_year_'+name+'_concentration')
 if fail:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=fail,holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 m=smf.ols('y ~ '+rhs(),data=p);fit0=m.fit()
 if fit0.model.rank!=fit0.model.exog.shape[1]:return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['primary_design_rank'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 country_codes=pd.Categorical(p.country_iso3).codes;year_codes=pd.Categorical(p.anchor_year).codes
 fit=m.fit(cov_type='cluster',cov_kwds={'groups':np.column_stack([country_codes,year_codes]),'use_correction':True,'df_correction':True},use_t=False)
 beta,se=float(fit.params['x']),float(fit.bse['x']);df=min(gate['valid_countries'],gate['valid_years'])-1
 if not(math.isfinite(beta) and math.isfinite(se) and se>0):return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['finite_two_way_cluster_uncertainty'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 pv=float(2*student_t.sf(abs(beta/se),df));crit=float(student_t.ppf(.995,df))
 if not(math.isfinite(pv) and math.isfinite(crit)):return dict(sample=gate,primary=None,hash_folds=[],gate_failures=['finite_t_inference'],holm_adjusted_p=1.,verdict='INCONCLUSIVE')
 primary=dict(beta=beta,two_way_cluster_se=se,p_two_sided=pv,confidence_level=.99,confidence_interval=[beta-crit*se,beta+crit*se],n_rows=len(p),n_countries=gate['valid_countries'],n_years=gate['valid_years'],df_inference=df,model_rank=int(fit.model.rank),model_columns=int(m.exog.shape[1]),residual_exposure=xc,residual_outcome=yc,method='country/year FE OLS with baseline and prior outcome trend; two-way country/year CR1 cluster t(min(G,T)-1)')
 folds=[]
 for omit in range(5):
  q=p[p.country_iso3.map(lambda s:int(hashlib.sha256(s.encode()).hexdigest(),16)%5!=omit)]
  if len(q)<MIN_FOLD_ROWS[k] or q.country_iso3.nunique()<MIN_FOLD_COUNTRIES[k]:fail.append(f'fold_{omit}_coverage');continue
  f=smf.ols('y ~ '+rhs(),data=q);ff=f.fit()
  if ff.model.rank!=ff.model.exog.shape[1]:fail.append(f'fold_{omit}_rank');continue
  b=float(ff.params['x'])
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
  direction=1 if c[3]=='+' else -1
  if direction*beta>=c[4] and adj[hid(c)]<=ALPHA and (pos if direction==1 else neg)>=MIN_SAME_SIGN_FOLDS:r['verdict']='SUPPORTED'
  elif direction*beta<=-c[4] and adj[hid(c)]<=ALPHA and (neg if direction==1 else pos)>=MIN_SAME_SIGN_FOLDS:r['verdict']='REFUTED'
  else:r['verdict']='PARTIAL'
def artifacts(c,result,reg,lock,stamp):
 id=hid(c)
 diag=dict(hypothesis_id=id,family_id=FAMILY,family_size=len(CELLS),registration_commit=reg,source_lock_commit=lock,source_sha256=SOURCE_SHA,source_key_roster_sha256=ROSTER_SHA,runner=RUNNER,run_utc=stamp,predictor_series=['world_bank_wdi:IT.NET.USER.ZS'],outcome_series=SOURCES[c[0]]['series_id'],registered_direction=c[3],thresholds=threshold(c),result=result,limitations=LIMITS,correction=CORRECTION)
 db=js(diag)
 source=dict(publisher='World Bank World Development Indicators and ILOSTAT',source_sha256=SOURCE_SHA,source_lock_commit=lock,source_lock_manifest=lock_rel(c),key_roster_sha256=ROSTER_SHA,input_vintages=[{'path':v['path'],'sha256':v['sha256']} for v in SOURCES.values()],license='CC BY 4.0; derived summaries only',contains_source_values=False)
 manifest=dict(hypothesis_id=id,status=result['verdict'],run_utc=stamp,runner=RUNNER,preregistration_commit=reg,source=source,family_id=FAMILY,family_size=len(CELLS),sample=result['sample'],correction=CORRECTION)
 packet=dict(packet_version=1,hypothesis={'id':id,'path':spec_rel(c)},preregistration={'commit':reg,'steelman':steel_rel(c),'source_plan':PLAN,'key_roster':ROSTER},source=source,family={'id':FAMILY,'size':len(CELLS),'members':[hid(x) for x in CELLS],'holm_alpha':ALPHA,'interpretation':'Five correlated future labour outcomes after earlier national Internet-use growth'},reproduction={'runner':RUNNER,'command':f'python3 {RUNNER} verify --source-root /path/to/IESET','result_sha256':hashlib.sha256(db).hexdigest()},result=result,limitations=LIMITS,correction=CORRECTION)
 card=f'# Result card: {id}\n\nVerdict: **{result["verdict"]}**. Earlier Internet-use growth; later {c[2]}.\n\nRegistration `{reg}`; source lock `{lock}`. Complete country-years: {result["sample"]["valid_rows"]} in {result["sample"]["valid_countries"]} countries and {result["sample"]["valid_years"]} anchor years.\n'
 if result['gate_failures']:card+=f'\nFrozen gate failures: {", ".join(result["gate_failures"])}.\n'
 if result['primary']:
  q=result['primary'];card+=f'\nBeta={q["beta"]:+.6g} {c[5]} per +10 Internet percentage points; two-way cluster SE={q["two_way_cluster_se"]:.6g}; two-sided p={q["p_two_sided"]:.6g}; Holm p={result["holm_adjusted_p"]:.6g}; 99% CI={q["confidence_interval"]}.\n'
 card+='\nDescriptive prospective calibration only; zero causal, policy, school, position or featured credit.\n'
 wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"+"root=Path(__file__).resolve().parents[3]\n"+f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
 return {'diagnostics.json':db,'manifest.yaml':ya(manifest),'evidence_packet.yaml':ya(packet),'result_card.md':card.encode(),'replication.py':wrapper.encode(),'hypothesis.yaml':(ROOT/spec_rel(c)).read_bytes(),'chart_data.json':js({'hypothesis_id':id,'family_id':FAMILY,'verdict':result['verdict'],'primary':result['primary']})}
def report_text(results,reg,locks):
 lines=['# Internet uptake and later ILO labour outcomes: frozen family results','',f'Registration `{reg}`; five separate source locks from `{next(iter(locks.values()))}` through `{list(locks.values())[-1]}`.','','| Future labour outcome | Verdict | Rows / countries / years | Beta per +10 Internet points | Raw p | Holm p | Gate failures |','| --- | --- | ---: | ---: | ---: | ---: | --- |']
 for c in CELLS:
  r=results[hid(c)];q=r['primary'];g=r['sample'];line=f'| {c[2]} | {r["verdict"]} | {g["valid_rows"]} / {g["valid_countries"]} / {g["valid_years"]} | '
  line+=(f'{q["beta"]:+.5g} | {q["p_two_sided"]:.5g} | {r["holm_adjusted_p"]:.5g} | ' if q else '— | — | 1 | ')
  line+=f'{", ".join(r["gate_failures"]) or "none"} |';lines.append(line)
 lines+=['','All five selected outcomes remain in the Holm denominator, including INCONCLUSIVE outcomes. Source-code continuity and prior-outcome controls do not establish a causal effect. ILO modelled estimates and national earnings surveys have different comparability limits. The family was selected after other Internet questions in the archive and is not independent confirmation. No causal, policy, position, school or featured credit.','']
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
 parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);parser.add_argument('action',choices=['preflight','register','lock','measure','verify']);parser.add_argument('--source-root',type=Path,default=ROOT);parser.add_argument('--cell',choices=[c[1] for c in CELLS]);args=parser.parse_args()
 paths=source_paths(args.source_root)
 if args.action=='preflight':
  rows=key_roster(paths);counts={c[1]:{'rows':sum(r[0]==c[1] for r in rows),'countries':len({r[1] for r in rows if r[0]==c[1]})} for c in CELLS}
  print(json.dumps({'family_size':len(CELLS),'source_key_rows':len(rows),'source_key_roster_sha256':hashlib.sha256(roster_bytes(rows)).hexdigest(),'per_cell':counts,'years':[min(YEARS),max(YEARS)],'selected_values_or_status_masks_opened':False},sort_keys=True));return 0
 if args.action=='register':write_registration(paths);print('wrote five-cell key-only registration; commit before locks');return 0
 reg=registration_commit(paths)
 if args.action=='lock':
  if args.cell is None:raise ValueError('--cell required')
  c=next(c for c in CELLS if c[1]==args.cell);i=CELLS.index(c)
  if i and not (ROOT/lock_rel(CELLS[i-1])).exists():raise RuntimeError('prior lock must be committed')
  if i and not ancestor(reg,first_add(lock_rel(CELLS[i-1]))):raise RuntimeError('prior lock must be committed')
  write_lock(c,reg);print(f'wrote lock for {hid(c)}; commit this file alone');return 0
 locks=lock_commits(reg);roster=loaded_roster(paths);wdi,ilo,status_counts=selected_values(paths)
 results={}
 for c in CELLS:
  p,g=panel(c,roster,wdi,ilo);results[hid(c)]=estimate(c,p,g)
 holm(results)
 if args.action=='measure':
  write_results(results,reg,locks)
  print(json.dumps({h:{'verdict':r['verdict'],'rows':r['sample']['valid_rows'],'countries':r['sample']['valid_countries'],'years':r['sample']['valid_years'],'gate_failures':r['gate_failures'],'beta':r['primary']['beta'] if r['primary'] else None,'p':r['primary']['p_two_sided'] if r['primary'] else None,'holm_p':r['holm_adjusted_p']} for h,r in results.items()},indent=2))
 else:verify_results(results,reg,locks);print('verified exact replay',FAMILY,{h:r['verdict'] for h,r in results.items()})
 return 0
if __name__=='__main__':raise SystemExit(main())
