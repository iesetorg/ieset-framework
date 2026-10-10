#!/usr/bin/env python3
"""Frozen 64-cell Internet-uptake to Eurostat citizenship labour calibration.

--preflight reads Eurostat dimensions and keys only. Selected Eurostat values
and null masks are first opened by --run/--verify after two separate commits.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,subprocess
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import t as student_t
import yaml

ROOT=Path(__file__).resolve().parents[1]
FAMILY='wdi_internet_eurostat_citizen_labour_2026_10_10'
RUNNER='scripts/run_wdi_internet_eurostat_citizen_labour_2026.py'
PREREG='engine/audits/wdi_internet_eurostat_citizen_labour_prereg_2026-10-10.md'
ROSTER='data/pinned_evidence/wdi_internet_eurostat_citizen_labour_2026_key_roster.csv'
ROSTER_SHA='ed255398f42704075825c4e76db3dab2003ef2cfe6c12a8c24086c380b368758'
LOCK='data/pinned_evidence/wdi_internet_eurostat_citizen_labour_2026.manifest.json'
SUMMARY='engine/audits/wdi_internet_eurostat_citizen_labour_results_2026-10-10.md'
STEEL='hypotheses/steelman/wdi_internet_eurostat_citizen_labour_family_2026.md'
SOURCES={
 'internet':{'publisher':'world_bank_wdi','series_id':'IT.NET.USER.ZS','path':'data/vintages/world_bank_wdi/IT.NET.USER.ZS@2026-05-05T203400Z.parquet','sha256':'c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8','manifest':'data/manifests/fetch_run_2026-05-05T210519Z.yaml','manifest_sha256':'5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112'},
 'activity':{'publisher':'eurostat','series_id':'lfsa_argan','path':'data/vintages/eurostat/lfsa_argan@2026-04-30T130700Z.parquet','sha256':'0ed2c40356794d48779dff7fc951e022cfb7994b1d7be5249f16fed12627dec9','manifest':'data/manifests/fetch_run_2026-04-30T130723Z.yaml','manifest_sha256':'cdb19507131f6659ca87ec4aa96784f031627a8bab939dc9ec9390752778aa16'},
 'employment':{'publisher':'eurostat','series_id':'lfsa_ergan','path':'data/vintages/eurostat/lfsa_ergan@2026-04-30T130634Z.parquet','sha256':'e0129dac7799748fad79571d6b736cf9afb55d290fe4c6b8f95457af8e1eee68','manifest':'data/manifests/fetch_run_2026-04-30T130700Z.yaml','manifest_sha256':'63fb4149706f480f087beeab88cfd049b870d26ca689edbdd2f227c039a158dd'},
}
GEO=dict(zip('AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL NO PL PT RO SE SI SK TR UK CH'.split(),'AUT BEL BGR CYP CZE DEU DNK EST GRC ESP FIN FRA HRV HUN IRL ITA LTU LUX LVA MLT NLD NOR POL PRT ROU SWE SVN SVK TUR GBR CHE'.split()))
CASES={}
for outcome in ('activity','employment'):
 for citizen in ('NAT','FOR'):
  for sex in ('F','M'):
   for low in range(20,60,5):
    key=f'{outcome}_{citizen.lower()}_{sex.lower()}_{low}_{low+4}'
    CASES[key]={'id':f'wdi_internet_eurostat_{key}_forward_2026','outcome':outcome,'citizen':citizen,'sex':sex,'age':f'Y{low}-{low+4}','age_label':f'{low}–{low+4}','sex_label':'women' if sex=='F' else 'men','citizen_label':'national citizens' if citizen=='NAT' else 'foreign citizens'}
assert len(CASES)==64
FAMILY_SIZE=64;ALPHA=0.01;P_MAX=ALPHA/FAMILY_SIZE;BETA_MIN=0.02;MATERIAL_X=2.0;MAX_X=20.0
MIN_YEARS=5;MIN_DISTINCT_YEARS=12
FLOORS={'NAT':dict(min_valid_rows=350,min_valid_countries=26,min_material_rows=200,min_material_countries=25),
        'FOR':dict(min_valid_rows=200,min_valid_countries=16,min_material_rows=100,min_material_countries=15)}
MAX_TOP1=0.30;MAX_COUNTRY=0.20;MAX_YEAR=0.20
CORRECTION={'disposition':'descriptive_calibration_only','family_id':FAMILY,'family_size':FAMILY_SIZE,'family_alpha':ALPHA,'bonferroni_p_max':P_MAX,'causal_credit':0,'policy_score_eligible':False,'policy_score_credit':0,'school_score_eligible':False,'school_score_credit':0,'featured_eligible':False}
LIMITATIONS=[
 'The 64 cells are disjoint within a labour measure by citizenship, sex and age, but activity and employment overlap and all cells share macro shocks; they are not independent replications.',
 'Internet use measures national uptake, not randomized access, policy, or the Internet use of the selected demographic cell.',
 'Annual LFS employment and activity rates are repeated cross sections, not individual job transitions; migration and naturalisation change citizenship-cell composition.',
 'The pinned Eurostat Parquet omitted quality/break flags. The pre-2020 outcome window avoids the 2021 redesign but may retain older country-specific breaks or unreliable foreign-citizen cells.',
 'World Bank metadata identifies the International Telecommunication Union as the underlying Internet-use source. Public data rights require separate review.',
 'The 64-test Bonferroni correction is local to this prospective family; it does not correct prior IESET archive-wide selection.',
 'No result has causal, policy, school, position, or featured credit.',
]

def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
 return h.hexdigest()

def git(*args:str)->bytes:return subprocess.check_output(['git',*args],cwd=ROOT)

def first_addition(rel:str)->str:
 revisions=git('log','--diff-filter=A','--format=%H','HEAD','--',rel).decode().splitlines()
 if not revisions:raise RuntimeError(f'missing first-addition commit: {rel}')
 return revisions[-1]

def committed_unchanged(rel:str,rev:str)->None:
 path=ROOT/rel
 if not path.is_file() or path.read_bytes()!=git('show',f'{rev}:{rel}') or git('status','--porcelain','--',rel).strip():
  raise RuntimeError(f'frozen file changed or uncommitted: {rel}')

def spec_rel(case:dict[str,Any])->str:return f'hypotheses/labour/{case["id"]}.yaml'
def run_rel(case:dict[str,Any])->str:return f'engine/runs/{case["id"]}'

def load_roster()->dict[str,list[tuple[str,int]]]:
 path=ROOT/ROSTER;raw=path.read_bytes()
 if sha256(path)!=ROSTER_SHA or not raw.startswith(b'case_id,country_iso3,year\n'):raise RuntimeError('roster SHA/header mismatch')
 records=list(csv.DictReader(io.StringIO(raw.decode())))
 observed=[(r['case_id'],r['country_iso3'],int(r['year'])) for r in records]
 if len(observed)!=22826 or observed!=sorted(set(observed)) or {x[0] for x in observed}!=set(CASES):raise RuntimeError('roster order, uniqueness or family mismatch')
 result={key:[] for key in CASES}
 for key,country,year in observed:
  if country not in GEO.values() or not 2005<=year<=2018:raise RuntimeError('roster geography/year out of range')
  result[key].append((country,year))
 return result

def threshold(case:dict[str,Any],rows:list[tuple[str,int]],net:dict[tuple[str,int],float])->dict[str,Any]:
 material=[(c,y) for c,y in rows if abs(net[c,y-1]-net[c,y-2])>=MATERIAL_X]
 return {'family_id':FAMILY,'family_size':FAMILY_SIZE,'family_alpha':ALPHA,'p_max_two_sided_bonferroni':P_MAX,
  'positive_beta_min_rate_pp_per_internet_pp':BETA_MIN,'material_internet_change_min_abs_pp':MATERIAL_X,'max_abs_internet_change_pp':MAX_X,
  'anchor_years':[2005,2018],'expected_key_rows':len(rows),'expected_key_countries':len({c for c,y in rows}),
  'expected_key_years':len({y for c,y in rows}),'expected_material_key_rows':len(material),'expected_material_key_countries':len({c for c,y in material}),
  'roster_sha256':ROSTER_SHA,**FLOORS[case['citizen']],'min_distinct_years':MIN_DISTINCT_YEARS,'min_complete_years_per_country':MIN_YEARS,
  'max_top_1pct_partialled_internet_share':MAX_TOP1,'max_country_partialled_internet_share':MAX_COUNTRY,'max_year_partialled_internet_share':MAX_YEAR,
  'source_files':{role:{k:v for k,v in source.items() if k in ('path','sha256','manifest','manifest_sha256')} for role,source in SOURCES.items()},
  'causal_credit':0,'policy_score_eligible':False,'policy_score_credit':0,'school_score_eligible':False,'school_score_credit':0,'featured_eligible':False}

def registration_commit(roster:dict[str,list[tuple[str,int]]],net:dict[tuple[str,int],float])->str:
 frozen=[PREREG,RUNNER,ROSTER,STEEL]+[spec_rel(c) for c in CASES.values()]
 revisions={first_addition(rel) for rel in frozen}
 if len(revisions)!=1:raise RuntimeError('registration files lack one shared first-addition commit')
 rev=revisions.pop()
 for rel in frozen:committed_unchanged(rel,rev)
 if git('ls-tree','-r','--name-only',rev,'--',LOCK).strip() or any(git('ls-tree','-r','--name-only',rev,'--',run_rel(c)).strip() for c in CASES.values()):
  raise RuntimeError('registration commit already contained source lock or outcomes')
 for key,case in CASES.items():
  spec=yaml.safe_load((ROOT/spec_rel(case)).read_text())
  if (spec.get('hypothesis_id')!=case['id'] or spec.get('status')!='pre_registered' or spec.get('topic')!='labour'
      or spec.get('evidence_type')!='associational' or spec.get('claim_direction')!='+' or spec.get('steelman')!=STEEL
      or spec.get('covers_claims')!=[] or spec.get('linked_hypotheses')!=[] or spec.get('linked_conditions')!=[]
      or spec['sample'].get('countries')!=sorted({c for c,y in roster[key]}) or spec['sample'].get('period')!=[2005,2019]
      or spec['falsification'].get('threshold')!=threshold(case,roster[key],net)
      or spec['variables']['treatment'][0].get('source')!='world_bank_wdi:IT.NET.USER.ZS'
      or spec['variables']['outcome'][0].get('source')!=f'eurostat:{SOURCES[case["outcome"]]["series_id"]}'
      or spec['estimator'].get('fixed_effects')!=['country','year'] or spec['estimator'].get('clustering')!='country'):
   raise RuntimeError(f'registered spec changed: {key}')
 return rev

def check_sources()->dict[str,dict[str,Any]]:
 result={}
 for role,src in SOURCES.items():
  raw=ROOT/src['path'];manifest_path=ROOT/src['manifest']
  if not raw.is_file() or sha256(raw)!=src['sha256'] or not manifest_path.is_file() or sha256(manifest_path)!=src['manifest_sha256']:
   raise RuntimeError(f'{role} source/manifest SHA mismatch or missing')
  doc=yaml.safe_load(manifest_path.read_text());hits=[e for e in doc.get('entries',[]) if e.get('publisher')==src['publisher'] and e.get('series_id')==src['series_id'] and e.get('parquet_path')==src['path'] and e.get('sha256')==src['sha256']]
  if len(hits)!=1:raise RuntimeError(f'{role} source not in pinned manifest')
  e=hits[0];result[role]={**src,'source_url':e.get('source_url'),'methodology_url':e.get('methodology_url'),'license_label':e.get('license'),'fetch_utc':e.get('fetch_utc'),'rows':e.get('rows')}
 return result

def internet_values()->dict[tuple[str,int],float]:
 """Only WDI treatment/control values and statuses; no Eurostat outcome values."""
 path=ROOT/SOURCES['internet']['path']
 df=pd.read_parquet(path,columns=['country_iso3','year','value','obs_status'])
 df=df.loc[df.country_iso3.isin(GEO.values()) & df.obs_status.fillna('').isin(['','A'])].copy()
 if df.duplicated(['country_iso3','year']).any():raise RuntimeError('duplicate WDI country-year')
 df['value']=pd.to_numeric(df.value,errors='coerce')
 df=df.loc[np.isfinite(df.value)&df.value.between(0,100)]
 return {(str(c),int(y)):float(v) for c,y,v in df[['country_iso3','year','value']].itertuples(index=False,name=None)}

def outcome_keys()->dict[str,set[tuple[str,int]]]:
 """Only exact Eurostat dimensions and keys; never value, null mask, or flag."""
 result={}
 for outcome in ('activity','employment'):
  src=SOURCES[outcome];cols=['freq','unit','sex','age','citizen','geo_code','period']
  df=pd.read_parquet(ROOT/src['path'],columns=cols)
  if len(df)!=(459530 if outcome=='activity' else 525365):raise RuntimeError('Eurostat source row count changed')
  df=df.loc[df.freq.eq('A')&df.unit.eq('PC')&df.sex.isin(['F','M'])&df.citizen.isin(['NAT','FOR'])&df.geo_code.isin(GEO)].copy()
  if df.duplicated(['sex','age','citizen','geo_code','period']).any():raise RuntimeError(f'duplicate {outcome} exact key')
  for key,case in CASES.items():
   if case['outcome']!=outcome:continue
   sel=df.loc[df.sex.eq(case['sex'])&df.age.eq(case['age'])&df.citizen.eq(case['citizen'])]
   result[key]={(GEO[str(g)],int(y)) for g,y in sel[['geo_code','period']].itertuples(index=False,name=None)}
 return result

def candidate_rows(keys:set[tuple[str,int]],net:dict[tuple[str,int],float])->list[tuple[str,int]]:
 pool={(c,y) for c,y in keys if 2005<=y<=2018 and (c,y+1) in keys and (c,y-1) in net and (c,y-2) in net and abs(net[c,y-1]-net[c,y-2])<=MAX_X}
 counts=Counter(c for c,y in pool)
 return sorted((c,y) for c,y in pool if counts[c]>=MIN_YEARS)

def concentration(panel:pd.DataFrame,residual:np.ndarray)->dict[str,float]:
 squares=np.square(np.asarray(residual,dtype=float));total=float(squares.sum())
 if not math.isfinite(total) or total<=0:raise ValueError('no residualized Internet variation')
 top=max(1,math.ceil(.01*len(squares)));by=panel[['country_iso3','year']].copy();by['sq']=squares
 return {'top_1pct_rows':float(np.sort(squares)[-top:].sum()/total),'largest_country':float(by.groupby('country_iso3').sq.sum().max()/total),'largest_year':float(by.groupby('year').sq.sum().max()/total)}

def key_preflight(roster:dict[str,list[tuple[str,int]]],net:dict[tuple[str,int],float])->dict[str,Any]:
 keys=outcome_keys();summary={}
 for key,case in CASES.items():
  rows=roster[key]
  if candidate_rows(keys[key],net)!=rows:raise RuntimeError(f'Eurostat key-only roster mismatch: {key}')
  panel=pd.DataFrame([{'country_iso3':c,'year':y,'x':net[c,y-1]-net[c,y-2],'x0':net[c,y-2]} for c,y in rows])
  material=panel.x.abs().ge(MATERIAL_X)
  residual=smf.ols('x ~ x0 + C(country_iso3) + C(year)',data=panel).fit().resid.to_numpy()
  summary[key]={'key_pairs':len(rows),'key_countries':int(panel.country_iso3.nunique()),'key_years':int(panel.year.nunique()),'material_exposure_pairs':int(material.sum()),'material_exposure_countries':int(panel.loc[material,'country_iso3'].nunique()),'treatment_only_partialled_variance_shares':concentration(panel,residual)}
 return {'family_id':FAMILY,'family_size':FAMILY_SIZE,'roster_sha256':ROSTER_SHA,'outcome_values_read':False,'outcome_null_masks_read':False,'outcome_statuses_read':False,'cells':summary}

def lock_payload(rev:str,sources:dict[str,Any],preflight:dict[str,Any])->dict[str,Any]:
 return {'family_id':FAMILY,'preregistration_commit':rev,'source_records':sources,'key_roster':{'path':ROSTER,'sha256':ROSTER_SHA},'key_preflight':preflight,'outcome_value_or_null_access_before_lock':False,'treatment_values_inspected_before_registration':True,'whole_fetch_manifests_copied':False}

def write_source_lock()->None:
 roster=load_roster();net=internet_values();rev=registration_commit(roster,net);sources=check_sources();preflight=key_preflight(roster,net)
 path=ROOT/LOCK
 if path.exists():raise FileExistsError(LOCK)
 path.write_text(json.dumps(lock_payload(rev,sources,preflight),indent=2,sort_keys=True)+'\n')
 print(f'wrote {LOCK}; commit separately before selected Eurostat outcomes')

def check_source_lock(rev:str,sources:dict[str,Any],preflight:dict[str,Any])->str:
 path=ROOT/LOCK
 if json.loads(path.read_text())!=lock_payload(rev,sources,preflight):raise RuntimeError('source-lock payload differs from source hashes or preflight')
 commit=first_addition(LOCK)
 if commit==rev or subprocess.run(['git','merge-base','--is-ancestor',rev,commit],cwd=ROOT).returncode:raise RuntimeError('source lock does not follow registration')
 committed_unchanged(LOCK,commit)
 if any(git('ls-tree','-r','--name-only',commit,'--',run_rel(c)).strip() for c in CASES.values()):raise RuntimeError('source-lock commit contains measured results')
 return commit

def finite_rate(value:Any)->float|None:
 try:v=float(value)
 except (ValueError,TypeError,OverflowError):return None
 return v if math.isfinite(v) and 0<=v<=100 else None

def measured_panels(roster:dict[str,list[tuple[str,int]]],net:dict[tuple[str,int],float])->dict[str,tuple[pd.DataFrame,dict[str,Any]]]:
 """First selected Eurostat numeric/null access; caller has verified two commits."""
 result={}
 for outcome in ('activity','employment'):
  src=SOURCES[outcome];cols=['freq','unit','sex','age','citizen','geo_code','period','value']
  df=pd.read_parquet(ROOT/src['path'],columns=cols)
  df=df.loc[df.freq.eq('A')&df.unit.eq('PC')&df.sex.isin(['F','M'])&df.citizen.isin(['NAT','FOR'])&df.geo_code.isin(GEO)]
  for key,case in CASES.items():
   if case['outcome']!=outcome:continue
   sel=df.loc[df.sex.eq(case['sex'])&df.age.eq(case['age'])&df.citizen.eq(case['citizen'])]
   vals={(GEO[str(g)],int(y)):finite_rate(v) for g,y,v in sel[['geo_code','period','value']].itertuples(index=False,name=None)}
   data=[];invalid=0
   for c,y in roster[key]:
    before=vals.get((c,y));after=vals.get((c,y+1))
    if before is None or after is None:invalid+=1;continue
    data.append({'country_iso3':c,'year':y,'x':net[c,y-1]-net[c,y-2],'x0':net[c,y-2],'rate_change':after-before})
   panel=pd.DataFrame(data,columns=['country_iso3','year','x','x0','rate_change'])
   before_filter=len(panel);counts=panel.country_iso3.value_counts()
   panel=panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
   material=panel.x.abs().ge(MATERIAL_X)
   gate={'roster_rows':len(roster[key]),'dropped_missing_or_invalid_rate_pairs':invalid,'complete_pairs_before_country_floor':before_filter,
    'valid_rows':len(panel),'valid_countries':int(panel.country_iso3.nunique()),'distinct_years':int(panel.year.nunique()),
    'material_exposure_rows':int(material.sum()),'material_exposure_countries':int(panel.loc[material,'country_iso3'].nunique()),
    'source_cell_flags_retained':False,'outcome_values_read_after_lock':True}
   result[key]=(panel,gate)
 return result

def estimate(case:dict[str,Any],panel:pd.DataFrame,gate:dict[str,Any])->dict[str,Any]:
 floor=FLOORS[case['citizen']]
 if (gate['valid_rows']<floor['min_valid_rows'] or gate['valid_countries']<floor['min_valid_countries']
     or gate['material_exposure_rows']<floor['min_material_rows'] or gate['material_exposure_countries']<floor['min_material_countries']
     or gate['distinct_years']<MIN_DISTINCT_YEARS):
  return {'gate':gate,'verdict':'INCONCLUSIVE','reason':'frozen complete-case, country, year, or material-exposure floor failed','primary':None}
 residual=smf.ols('x ~ x0 + C(country_iso3) + C(year)',data=panel).fit().resid.to_numpy()
 try:shares=concentration(panel,residual)
 except ValueError:return {'gate':gate,'verdict':'INCONCLUSIVE','reason':'no residualized exposure variation','primary':None}
 gate['partialled_internet_variance_shares']=shares
 if shares['top_1pct_rows']>MAX_TOP1 or shares['largest_country']>MAX_COUNTRY or shares['largest_year']>MAX_YEAR:
  return {'gate':gate,'verdict':'INCONCLUSIVE','reason':'frozen partialled-treatment concentration gate failed','primary':None}
 model=smf.ols('rate_change ~ x + x0 + C(country_iso3) + C(year)',data=panel)
 if model.exog.shape[0]!=len(panel) or np.linalg.matrix_rank(model.exog)!=model.exog.shape[1]:
  return {'gate':gate,'verdict':'INCONCLUSIVE','reason':'fixed-effect model rank deficient','primary':None}
 groups=int(panel.country_iso3.nunique())
 fit=model.fit(cov_type='cluster',cov_kwds={'groups':panel.country_iso3,'use_correction':True,'df_correction':True},use_t=True)
 beta,se=float(fit.params['x']),float(fit.bse['x'])
 if not math.isfinite(beta) or not math.isfinite(se) or se<=0:
  return {'gate':gate,'verdict':'INCONCLUSIVE','reason':'nonfinite or nonpositive clustered uncertainty','primary':None}
 p=float(2*student_t.sf(abs(beta/se),groups-1));critical=float(student_t.ppf(1-P_MAX/2,groups-1))
 if not math.isfinite(p) or not math.isfinite(critical):
  return {'gate':gate,'verdict':'INCONCLUSIVE','reason':'nonfinite country-cluster t inference','primary':None}
 primary={'coefficient':beta,'std_error':se,'p_value_two_sided':p,'confidence_level':1-P_MAX,
  'confidence_interval':[beta-critical*se,beta+critical*se],'n_rows':len(panel),'n_countries':groups,'df_inference':groups-1,
  'model_rank':int(fit.model.rank),'method':'country/year FE OLS with baseline Internet use; country-cluster CR1; Student t(G-1)'}
 if beta>=BETA_MIN and p<=P_MAX:verdict,reason='SUPPORTED','positive association clears frozen magnitude and 64-test cutoff'
 elif beta<=-BETA_MIN and p<=P_MAX:verdict,reason='REFUTED','opposite association clears frozen magnitude and 64-test cutoff'
 else:verdict,reason='PARTIAL','estimable association does not clear both frozen directional gates'
 return {'gate':gate,'verdict':verdict,'reason':reason,'primary':primary}

def artifact_payload(key:str,case:dict[str,Any],result:dict[str,Any],rev:str,lock_commit:str,stamp:str)->dict[str,Any]:
 hid=case['id'];verdict=result['verdict'];gate=result['gate'];primary=result['primary']
 diagnostics={'hypothesis_id':hid,'family_id':FAMILY,'family_size':FAMILY_SIZE,'verdict':verdict,'verdict_label':verdict,'verdict_reason':result['reason'],
  'run_utc':stamp,'runner':RUNNER,'preregistration_commit':rev,'source_lock_commit':lock_commit,'source_lock':LOCK,
  'template':'panel_fe','preflight':gate,'primary':primary,'p_max_two_sided_bonferroni':P_MAX,'positive_beta_min_rate_pp_per_internet_pp':BETA_MIN,
  'data_status':{'variables_missing':[],'input_vintages':list(SOURCES.values())},'limitations':LIMITATIONS,'correction':CORRECTION}
 manifest={'hypothesis_id':hid,'run_utc':stamp,'runner':RUNNER,'preregistration_commit':rev,'source_lock_commit':lock_commit,
  'source_lock':LOCK,'status':verdict,'vintages':list(SOURCES.values()),'derived_panel':gate,'correction':CORRECTION}
 packet={'packet_version':1,'generated_utc':stamp,'hypothesis':{'id':hid,'path':spec_rel(case),'topic':'labour'},
  'preregistration':{'spec_commit':rev,'source_lock_commit':lock_commit,'family_id':FAMILY,'family_size':FAMILY_SIZE,
   'key_roster':ROSTER,'key_roster_sha256':ROSTER_SHA,'steelman':STEEL},
  'reproduction':{'runner':RUNNER,'run_dir':run_rel(case),'command':f'python3 {RUNNER} --verify'},
  'verdict':{'raw':verdict,'bucket':verdict.lower() if verdict!='INCONCLUSIVE' else 'archive','reason':result['reason']},
  'data':{'inputs':SOURCES,'sample':gate},'results':{'primary':primary},'limitations':LIMITATIONS,'correction':CORRECTION}
 card=f'# Result card: {hid}\n\nVerdict: **{verdict}**. {result["reason"]}.\n\nFrozen preregistration `{rev}`; source-lock commit `{lock_commit}`.\n\n'
 card+=f'Eurostat {case["outcome"]} rate: {case["citizen_label"]}, {case["sex_label"]}, ages {case["age_label"]}. Key-only roster {gate["roster_rows"]} country-years; valid {gate["valid_rows"]} / {gate["valid_countries"]} countries; material Internet-gain pairs {gate["material_exposure_rows"]} / {gate["material_exposure_countries"]} countries.\n'
 if primary is not None:card+=f'\nPrimary beta={primary["coefficient"]:+.6g} rate percentage-point change per one percentage point prior Internet-use gain, country-cluster SE={primary["std_error"]:.6g}, two-sided p={primary["p_value_two_sided"]:.6g}, {100*(1-P_MAX):.4f}% CI={primary["confidence_interval"]}.\n'
 card+=f'\nFamily correction: 64 registered tests, Bonferroni family alpha 0.01, individual two-sided p ≤ {P_MAX}; |beta| ≥ {BETA_MIN} also required. Activity and employment outcomes share people and shocks. Descriptive only; no causal, policy, school, position, or featured credit. Source flags were not retained.\n'
 wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\nroot = Path(__file__).resolve().parents[3]\n"+f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
 chart={'hypothesis_id':hid,'family_id':FAMILY,'verdict':verdict,'primary':primary}
 coef=[{'term':'prior_internet_use_gain_pp',**primary}] if primary is not None else []
 return {'diagnostics':diagnostics,'manifest':manifest,'packet':packet,'card':card,'wrapper':wrapper,'chart':chart,'coefficients':coef}

def summary_text(results:dict[str,dict[str,Any]],rev:str,lock_commit:str)->str:
 lines=['# WDI Internet uptake × Eurostat citizenship labour: 64-cell results','',f'Preregistration `{rev}`; source lock `{lock_commit}`.',
  f'All 64 prespecified activity/employment × citizenship × sex × age cells share one Bonferroni family: alpha 0.01, each two-sided p ≤ {P_MAX}.','',
  '| Cell | Verdict | Valid pairs / countries | Material pairs / countries | Beta | Two-sided p |','| --- | --- | ---: | ---: | ---: | ---: |']
 for key,case in CASES.items():
  result=results[key];gate=result['gate'];primary=result['primary'];beta=f'{primary["coefficient"]:+.6g}' if primary else 'not estimated';p=f'{primary["p_value_two_sided"]:.6g}' if primary else 'not estimated'
  lines.append(f'| {key} | **{result["verdict"]}** | {gate["valid_rows"]} / {gate["valid_countries"]} | {gate["material_exposure_rows"]} / {gate["material_exposure_countries"]} | {beta} | {p} |')
 counts=Counter(r['verdict'] for r in results.values())
 lines+=['',f'Verdicts: {dict(sorted(counts.items()))}.','',
  'Beta is next-year activity/employment rate change in percentage points per one percentage point prior national Internet-use gain, conditional on baseline Internet use and country/year fixed effects.',
  'The two labour margins overlap, all cells share exposure and shocks, and citizenship/age rates are repeated cross sections. Neither cell count nor local Bonferroni correction establishes independent replication or covers adaptive IESET archive search. Source flags were not retained. No causal, policy, school, position, or featured credit.','']
 return '\n'.join(lines)

def write_artifacts(results:dict[str,dict[str,Any]],rev:str,lock_commit:str)->None:
 if (ROOT/SUMMARY).exists() or any((ROOT/run_rel(c)).exists() for c in CASES.values()):raise FileExistsError('result artifacts already exist')
 stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
 cols=['term','coefficient','std_error','p_value_two_sided','confidence_level','confidence_interval','n_rows','n_countries','df_inference','model_rank','method']
 for key,case in CASES.items():
  payload=artifact_payload(key,case,results[key],rev,lock_commit,stamp);folder=ROOT/run_rel(case);folder.mkdir(parents=True)
  (folder/'hypothesis.yaml').write_bytes((ROOT/spec_rel(case)).read_bytes())
  (folder/'diagnostics.json').write_text(json.dumps(payload['diagnostics'],indent=2)+'\n')
  (folder/'manifest.yaml').write_text(yaml.safe_dump(payload['manifest'],sort_keys=False))
  (folder/'evidence_packet.yaml').write_text(yaml.safe_dump(payload['packet'],sort_keys=False))
  (folder/'result_card.md').write_text(payload['card']);(folder/'replication.py').write_text(payload['wrapper'])
  (folder/'chart_data.json').write_text(json.dumps(payload['chart'],indent=2)+'\n')
  pd.DataFrame(payload['coefficients'],columns=cols).to_parquet(folder/'coefficients.parquet',index=False)
 (ROOT/SUMMARY).write_text(summary_text(results,rev,lock_commit))

def equal_close(actual:Any,expected:Any,label:str)->None:
 if isinstance(expected,dict):
  if not isinstance(actual,dict) or set(actual)!=set(expected):raise AssertionError(f'{label} fields differ')
  for k,v in expected.items():equal_close(actual[k],v,f'{label}.{k}')
 elif isinstance(expected,list):
  if isinstance(actual,np.ndarray):actual=actual.tolist()
  if not isinstance(actual,list) or len(actual)!=len(expected):raise AssertionError(f'{label} list differs')
  for n,v in enumerate(expected):equal_close(actual[n],v,f'{label}[{n}]')
 elif isinstance(expected,float):
  if not math.isfinite(float(actual)) or not math.isclose(float(actual),expected,rel_tol=1e-9,abs_tol=1e-11):raise AssertionError(f'{label} numeric mismatch')
 elif actual!=expected:raise AssertionError(f'{label} value mismatch')

def verify_artifacts(results:dict[str,dict[str,Any]],rev:str,lock_commit:str)->None:
 for key,case in CASES.items():
  folder=ROOT/run_rel(case);saved=json.loads((folder/'diagnostics.json').read_text())
  payload=artifact_payload(key,case,results[key],rev,lock_commit,saved['run_utc'])
  equal_close(saved,payload['diagnostics'],f'{key}.diagnostics')
  equal_close(yaml.safe_load((folder/'manifest.yaml').read_text()),payload['manifest'],f'{key}.manifest')
  equal_close(yaml.safe_load((folder/'evidence_packet.yaml').read_text()),payload['packet'],f'{key}.packet')
  equal_close(json.loads((folder/'chart_data.json').read_text()),payload['chart'],f'{key}.chart')
  if ((folder/'hypothesis.yaml').read_bytes()!=(ROOT/spec_rel(case)).read_bytes() or (folder/'result_card.md').read_text()!=payload['card'] or (folder/'replication.py').read_text()!=payload['wrapper']):raise AssertionError(f'{key} text artifact mismatch')
  equal_close(pd.read_parquet(folder/'coefficients.parquet').to_dict(orient='records'),payload['coefficients'],f'{key}.coefficients')
 if (ROOT/SUMMARY).read_text()!=summary_text(results,rev,lock_commit):raise AssertionError('family summary mismatch')

def main()->int:
 parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);actions=parser.add_mutually_exclusive_group(required=True)
 for action in ('check-sources','preflight','write-source-lock','run','verify'):actions.add_argument(f'--{action}',action='store_true')
 args=parser.parse_args();sources=check_sources()
 if args.check_sources:print('three source SHA pins match; selected Eurostat outcomes unopened');return 0
 roster=load_roster();net=internet_values()
 if args.preflight:print(json.dumps(key_preflight(roster,net),indent=2,sort_keys=True));return 0
 if args.write_source_lock:write_source_lock();return 0
 rev=registration_commit(roster,net);preflight=key_preflight(roster,net);lock_commit=check_source_lock(rev,sources,preflight)
 panels=measured_panels(roster,net);results={key:estimate(CASES[key],*panels[key]) for key in CASES}
 if args.run:
  write_artifacts(results,rev,lock_commit)
  print(json.dumps({'family_id':FAMILY,'verdicts':dict(sorted(Counter(r['verdict'] for r in results.values()).items())),'registration':rev,'source_lock_commit':lock_commit},indent=2));return 0
 verify_artifacts(results,rev,lock_commit)
 print('verified exact replay',FAMILY,dict(sorted(Counter(r['verdict'] for r in results.values()).items())));return 0
if __name__=='__main__':raise SystemExit(main())
