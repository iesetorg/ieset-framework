#!/usr/bin/env python3
"""Frozen four-cell Eurostat regional R&D forward descriptive family."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from linearmodels.panel import PanelOLS
import yaml

ROOT=Path(__file__).resolve().parents[1]
FAMILY='eurostat_regional_rd_forward_2026_10_10'
REG='37cbc6d5339e8a9ac888c2c17213c4147608c7d4'
LOCK_COMMIT='393f291faa3881b5dc98225c80a839d0f3d8d9d4'
LOCK_REL=f'prereg/locks/{FAMILY}.json'
RUNNER_REL='scripts/run_eurostat_regional_rd_forward_2026.py'
AUDIT_REL='engine/audits/eurostat_regional_rd_forward_prereg_2026-10-10.md'
ARTIFACTS=('hypothesis.yaml','manifest.yaml','diagnostics.json','coefficients.parquet','chart_data.json','result_card.md','replication.py','evidence_packet.yaml','metric_results.parquet')


def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()


def git(*args:str)->str:
 return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def first_add(rel:str)->str:
 xs=git('log','--diff-filter=A','--format=%H','--',rel).splitlines()
 if not xs:raise ValueError('Missing first-add commit: '+rel)
 return xs[-1]


def frozen(rel:str,commit:str):
 now=(ROOT/rel).read_bytes()
 old=subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)
 head=subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT)
 if now!=old or now!=head:raise ValueError('Frozen artifact changed: '+rel)


def case_spec_path(case:str)->str:
 topic='growth' if 'gva' in case else 'labour'
 return f'hypotheses/{topic}/{case}.yaml'


def n2(z):return isinstance(z,str) and len(z)==4 and z[:2].isalpha() and 'Z' not in z and z[:2] not in {'EA','EU'}


def selected_key_lines(role:str,d:dict)->list[str]:
 keys=[]
 if role=='rd':
  for s,u,z,t in zip(d['sectperf'],d['unit'],d['geo_code'],d['period']):
   if s in {'BES','GOV'} and u=='PC_GDP' and n2(z) and 2000<=int(t)<=2023:keys.append(f'{s},{z},{t}')
 elif role=='gva':
  for u,s,z,t in zip(d['unit'],d['nace_r2'],d['geo_code'],d['period']):
   if u in {'CP_MEUR','PYP_MEUR'} and s=='TOTAL' and n2(z) and 2000<=int(t)<=2024:keys.append(f'{u},{z},{t}')
 else:
  for ed,sex,age,u,z,t in zip(d['isced11'],d['sex'],d['age'],d['unit'],d['geo_code'],d['period']):
   if ed=='TOTAL' and sex=='T' and age=='Y15-74' and u=='PC' and n2(z) and 2000<=int(t)<=2024:keys.append(f'{z},{t}')
 if len(keys)!=len(set(keys)):raise ValueError('Duplicate selected source keys: '+role)
 return sorted(keys)


def verify_custody(source_root:Path)->tuple[dict,dict,dict]:
 if subprocess.run(['git','merge-base','--is-ancestor',REG,LOCK_COMMIT],cwd=ROOT).returncode:raise ValueError('Registration is not ancestor of source lock')
 if subprocess.run(['git','merge-base','--is-ancestor',LOCK_COMMIT,'HEAD'],cwd=ROOT).returncode:raise ValueError('Source lock is not ancestor of result')
 frozen(LOCK_REL,LOCK_COMMIT)
 if first_add(LOCK_REL)!=LOCK_COMMIT:raise ValueError('Source-lock first-add chronology failed')
 lock=json.loads((ROOT/LOCK_REL).read_text())
 if lock['registration_commit']!=REG or lock['family_id']!=FAMILY or lock['family_size']!=4 or lock['selected_values_read_before_source_lock'] is not False:raise ValueError('Family lock malformed')
 roster_rel=lock['roster']['path']
 frozen(roster_rel,REG)
 if sha(ROOT/roster_rel)!=lock['roster']['sha256']:raise ValueError('Roster SHA mismatch')
 if sha(ROOT/lock['fetch_manifest']['path'])!=lock['fetch_manifest']['sha256']:raise ValueError('Fetch manifest SHA mismatch')
 cases=lock['hypothesis_ids']
 if len(cases)!=4 or cases!=sorted(cases):raise ValueError('Four-member denominator mismatch')
 specs={}
 for case in cases:
  rel=case_spec_path(case); frozen(rel,REG)
  if first_add(rel)!=REG:raise ValueError('Registration first-add chronology failed: '+case)
  s=yaml.safe_load((ROOT/rel).read_text()); t=s['falsification']['threshold']
  if s['status']!='pre_registered' or s['hypothesis_id']!=case or t['family_id']!=FAMILY or t['family_size']!=4 or t['source_key_roster_sha256']!=lock['roster']['sha256'] or t['source_lock_path']!=LOCK_REL:raise ValueError('Frozen spec mismatch: '+case)
  for role,ref in lock['source_files'].items():
   if t['source_files'][role]['path']!=ref['path'] or t['source_files'][role]['sha256']!=ref['sha256']:raise ValueError('Frozen source ref mismatch: '+case)
  specs[case]=s
 with (ROOT/roster_rel).open() as f: roster=list(csv.DictReader(f))
 by_case={case:[] for case in cases}
 for row in roster:
  case=row['case_id']; z=row['geo_code']; t=int(row['exposure_year'])
  if case not in by_case or row['country_code']!=z[:2] or not n2(z) or not 2001<=t<=2023:raise ValueError('Invalid roster row')
  by_case[case].append((z,t))
 for case,pairs in by_case.items():
  t=specs[case]['falsification']['threshold']
  if len(pairs)!=t['source_key_count'] or len(pairs)!=len(set(pairs)):raise ValueError('Case roster mismatch: '+case)
 for role,ref in lock['source_files'].items():
  p=source_root/ref['path']
  if not p.is_file() or sha(p)!=ref['sha256']:raise ValueError('Raw source missing or changed: '+role)
  parquet=pq.ParquetFile(p)
  if parquet.schema_arrow.names!=ref['schema_names'] or parquet.metadata.num_rows!=ref['raw_rows']:raise ValueError('Raw schema/row change: '+role)
  cols={k:[c for c in ref['schema_names'] if c!='value'] for k in lock['source_files']}[role]
  keys=selected_key_lines(role,pq.read_table(p,columns=cols).to_pydict())
  digest=hashlib.sha256(('\n'.join(keys)+'\n').encode()).hexdigest()
  if len(keys)!=ref['selected_key_count'] or digest!=ref['selected_key_sha256']:raise ValueError('Selected key SHA mismatch: '+role)
 return lock,specs,by_case


def finite(v):
 try:r=float(v)
 except (ValueError,TypeError):return None
 return r if math.isfinite(r) else None


def load_values(source_root:Path,lock:dict)->dict:
 """Called only after committed registration and source custody verification."""
 out={}
 for role,ref in lock['source_files'].items():
  cols=[*([c for c in ref['schema_names'] if c!='value']),'value']
  d=pq.read_table(source_root/ref['path'],columns=cols).to_pydict(); vals={}
  if role=='rd':
   itr=zip(d['sectperf'],d['unit'],d['geo_code'],d['period'],d['value'])
   for s,u,z,t,v in itr:
    if s in {'BES','GOV'} and u=='PC_GDP' and n2(z) and 2000<=int(t)<=2023:vals[(s,z,int(t))]=v
  elif role=='gva':
   itr=zip(d['unit'],d['nace_r2'],d['geo_code'],d['period'],d['value'])
   for u,s,z,t,v in itr:
    if u in {'CP_MEUR','PYP_MEUR'} and s=='TOTAL' and n2(z) and 2000<=int(t)<=2024:vals[(u,z,int(t))]=v
  else:
   itr=zip(d['isced11'],d['sex'],d['age'],d['unit'],d['geo_code'],d['period'],d['value'])
   for ed,sex,age,u,z,t,v in itr:
    if ed=='TOTAL' and sex=='T' and age=='Y15-74' and u=='PC' and n2(z) and 2000<=int(t)<=2024:vals[(z,int(t))]=v
  if len(vals)!=ref['selected_key_count']:raise ValueError('Selected value map/key mismatch: '+role)
  out[role]=vals
 return out


def panel_for(case:str,pairs:list[tuple[str,int]],values:dict,t:dict)->tuple[pd.DataFrame,dict]:
 sector=t['sector'];outcome=t['outcome'];rows=[]; dropped=Counter()
 for z,year in pairs:
  r0=finite(values['rd'].get((sector,z,year-1)));r1=finite(values['rd'].get((sector,z,year)))
  if r0 is None or r1 is None or min(r0,r1)<0 or max(r0,r1)>t['max_rd_share_pct_gdp'] or abs(r1-r0)>t['max_abs_rd_change_pp']:
   dropped['rd_missing_or_invalid']+=1;continue
  x=r1-r0
  if outcome=='gva':
   cp0=finite(values['gva'].get(('CP_MEUR',z,year-1)));cp1=finite(values['gva'].get(('CP_MEUR',z,year)))
   pyp1=finite(values['gva'].get(('PYP_MEUR',z,year)));pyp2=finite(values['gva'].get(('PYP_MEUR',z,year+1)))
   if any(v is None or v<=0 for v in [cp0,cp1,pyp1,pyp2]):dropped['gva_missing_or_invalid']+=1;continue
   prior=100*(pyp1/cp0-1); future=100*(pyp2/cp1-1)
   if max(abs(prior),abs(future))>t['max_abs_real_gva_growth_pp']:dropped['gva_growth_out_of_range']+=1;continue
  else:
   u0=finite(values['unemployment'].get((z,year-1)));u1=finite(values['unemployment'].get((z,year)));u2=finite(values['unemployment'].get((z,year+1)))
   if any(v is None or not 0<=v<=t['max_unemployment_rate_pct'] for v in [u0,u1,u2]):dropped['unemployment_missing_or_invalid']+=1;continue
   prior=u1;future=u2-u1
   if max(abs(u1-u0),abs(future))>t['max_abs_unemployment_change_pp']:dropped['unemployment_change_out_of_range']+=1;continue
  rows.append({'geo_code':z,'country_code':z[:2],'year':year,'x':x,'baseline_rd':r0,'prior_y':prior,'y':future})
 frame=pd.DataFrame(rows)
 if not frame.empty:
  counts=frame.groupby('geo_code').size()
  keep=set(counts[counts>=t['min_complete_years_per_region']].index)
  dropped['region_below_complete_year_floor']=int((~frame.geo_code.isin(keep)).sum())
  frame=frame[frame.geo_code.isin(keep)].sort_values(['geo_code','year']).reset_index(drop=True)
 diag={'source_key_rows':len(pairs),'complete_before_region_floor':len(rows),'complete_rows':len(frame),'regions':int(frame.geo_code.nunique()) if not frame.empty else 0,'countries':int(frame.country_code.nunique()) if not frame.empty else 0,'dropped':dict(dropped),'material_abs_exposure_rows':int((frame.x.abs()>=t['material_abs_rd_change_pp']).sum()) if not frame.empty else 0,'material_abs_exposure_regions':int(frame.loc[frame.x.abs()>=t['material_abs_rd_change_pp'],'geo_code'].nunique()) if not frame.empty else 0,'exposure_p90_p10_pp':float(np.quantile(frame.x,.9)-np.quantile(frame.x,.1)) if not frame.empty else 0.0}
 return frame,diag


def fit(frame:pd.DataFrame):
 d=frame.copy();d['country_year']=d['country_code']+'_'+d['year'].astype(str)
 d=d.set_index(['geo_code','year'])
 # Country-by-year effects absorb common national-year shifts; region effects absorb fixed regional levels.
 model=PanelOLS(d['y'],d[['x','baseline_rd','prior_y']],entity_effects=True,other_effects=d[['country_year']],drop_absorbed=True,check_rank=True)
 res=model.fit(cov_type='clustered',cluster_entity=True,debiased=True)
 if 'x' not in res.params or 'x' not in res.std_errors:raise ValueError('Exposure absorbed')
 beta=float(res.params['x']);se=float(res.std_errors['x']);p=float(res.pvalues['x'])
 if not all(math.isfinite(q) for q in [beta,se,p]) or se<=0:raise ValueError('Invalid cluster estimate')
 # Residualized exposure uses exactly the outcome model's controls and fixed effects.
 rmodel=PanelOLS(d['x'],d[['baseline_rd','prior_y']],entity_effects=True,other_effects=d[['country_year']],drop_absorbed=True,check_rank=True)
 rfit=rmodel.fit(cov_type='unadjusted')
 resid=rfit.resids.to_numpy().reshape(-1)
 base=d.reset_index();base['rx2']=resid*resid
 total=float(base.rx2.sum())
 if not math.isfinite(total) or total<=1e-12:raise ValueError('Residual exposure degenerate')
 region=base.groupby('geo_code').rx2.sum().sort_values(ascending=False)
 country=base.groupby('country_code').rx2.sum().sort_values(ascending=False)
 info={'beta':beta,'cluster_region_se':se,'p_two_sided':p,'df_resid':int(res.df_resid),'model_rows':int(res.nobs),'residual_exposure_sd_pp':float(np.std(resid,ddof=1)),'max_region_exposure_ss_share':float(region.iloc[0]/total),'max_country_exposure_ss_share':float(country.iloc[0]/total),'top_five_region_exposure_ss_share':float(region.iloc[:5].sum()/total),'top_three_exposure_countries':list(country.index[:3]),'method':'region and country-by-year FE; region-cluster covariance'}
 return info


def classify(frame:pd.DataFrame,diag:dict,t:dict)->tuple[dict,str]:
 gates=[]
 if diag['complete_rows']<t['min_complete_rows']:gates.append('complete_rows')
 if diag['regions']<t['min_regions']:gates.append('regions')
 if diag['countries']<t['min_countries']:gates.append('countries')
 if diag['material_abs_exposure_rows']<t['min_material_exposure_rows']:gates.append('material_exposure_rows')
 if diag['material_abs_exposure_regions']<t['min_material_exposure_regions']:gates.append('material_exposure_regions')
 if diag['exposure_p90_p10_pp']<t['min_exposure_p90_p10_pp']:gates.append('exposure_spread')
 if gates:diag['gate_failures']=gates;return {},'INCONCLUSIVE'
 try:estimate=fit(frame)
 except Exception as exc:diag['gate_failures']=['estimator:'+type(exc).__name__+':'+str(exc)];return {},'INCONCLUSIVE'
 if estimate['residual_exposure_sd_pp']<t['min_residual_exposure_sd_pp']:gates.append('residual_exposure_sd')
 for key in ['max_region_exposure_ss_share','max_country_exposure_ss_share','top_five_region_exposure_ss_share']:
  limit_key='max_top_five_region_exposure_ss_share' if key=='top_five_region_exposure_ss_share' else key
  if estimate[key]>t[limit_key]:gates.append(key)
 holdouts=[]
 for country in estimate['top_three_exposure_countries']:
  sub=frame[frame.country_code!=country]
  h={'omitted_country':country,'rows':len(sub),'regions':int(sub.geo_code.nunique())}
  if len(sub)<t['min_country_holdout_rows'] or h['regions']<t['min_country_holdout_regions']:
   h['failed']='sample_floor';gates.append('country_holdout_sample:'+country)
  else:
   try:h['beta']=fit(sub)['beta']
   except Exception as exc:h['failed']=type(exc).__name__+':'+str(exc);gates.append('country_holdout_fit:'+country)
  holdouts.append(h)
 estimate['country_holdouts']=holdouts
 diag['gate_failures']=gates
 if gates:return estimate,'INCONCLUSIVE'
 material=t['min_abs_beta_gva_growth_pp_per_rd_pp'] if t['outcome']=='gva' else t['min_abs_beta_unemployment_change_pp_per_rd_pp']
 direction=t['registered_direction'];beta=estimate['beta'];p=estimate['p_two_sided'];stable=all(h.get('beta',0)*beta>0 for h in holdouts)
 if p<=t['bonferroni_alpha'] and abs(beta)>=material and stable:
  return estimate, 'SUPPORTED' if beta*direction>0 else 'REFUTED'
 return estimate,'PARTIAL'


def json_write(p:Path,v):p.write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')


def parquet_write(p:Path,cols:dict,schema:pa.Schema):
 pq.write_table(pa.Table.from_pydict(cols,schema=schema),p,compression='snappy',version='2.6',write_statistics=False)


def emit(target:Path,case:str,spec:dict,lock:dict,diag:dict,estimate:dict,verdict:str):
 target.mkdir(parents=True,exist_ok=False)
 spec_rel=case_spec_path(case);t=spec['falsification']['threshold']
 (target/'hypothesis.yaml').write_bytes((ROOT/spec_rel).read_bytes())
 correction={'disposition':'descriptive_calibration_only','causal_credit':0,'policy_score_eligible':False,'policy_score_credit':0,'school_score_eligible':False,'school_score_credit':0,'position_score_credit':0,'featured_eligible':False}
 source={'publisher':'Eurostat','dataflows':['rd_e_gerdreg','nama_10r_3gva','lfst_r_lfu3rt'],'source_lock_commit':LOCK_COMMIT,'source_lock_manifest':LOCK_REL,'fetch_manifest':lock['fetch_manifest']['path'],'source_hashes':{r:x['sha256'] for r,x in lock['source_files'].items()},'key_roster_sha256':lock['roster']['sha256'],'contains_source_values':False}
 family={'id':FAMILY,'size':4,'members':lock['hypothesis_ids'],'bonferroni_alpha':t['bonferroni_alpha'],'interpretation':'Four correlated region-year tests; no independent replication or policy-effect credit.'}
 manifest={'hypothesis_id':case,'run_date':'2026-10-10','status':verdict,'runner':RUNNER_REL,'preregistration_commit':REG,'source':source,'family':family,'correction':correction}
 (target/'manifest.yaml').write_text(yaml.safe_dump(manifest,sort_keys=False,allow_unicode=True))
 diagnostic={'hypothesis_id':case,'family_id':FAMILY,'family_size':4,'registration_commit':REG,'source_lock_commit':LOCK_COMMIT,'thresholds':t,'sample':diag,'primary':estimate,'verdict':verdict,'correction':correction,'limitations':['Eurostat NUTS codes can cross boundary revisions; code continuity alone is not proof of unchanged territory.','Business and government R&D shares have a regional-GDP denominator; reverse causality, firm selection, EU funds and spillovers remain.','Region-years are dependent within regions and national years; fixed effects and region clustering do not identify a causal or policy effect.','Four-cell Bonferroni adjustment covers only this frozen family, not all IESET exploration.','Zero causal, policy, school, position and featured credit.']}
 json_write(target/'diagnostics.json',diagnostic)
 has='beta' in estimate
 parquet_write(target/'coefficients.parquet',{'term':['annual_rd_share_change_pp'] if has else [],'coefficient':[estimate['beta']] if has else [],'standard_error':[estimate['cluster_region_se']] if has else [],'p_value':[estimate['p_two_sided']] if has else []},pa.schema([('term',pa.string()),('coefficient',pa.float64()),('standard_error',pa.float64()),('p_value',pa.float64())]))
 json_write(target/'chart_data.json',{'display_series':[],'note':'No selected Eurostat source values or geography-level fitted data are republished.'})
 lines=[f'# {case}','','**Verdict: '+verdict+' — descriptive calibration only.**','',f"Frozen key rows: {diag['source_key_rows']:,}; complete rows: {diag['complete_rows']:,}; regions: {diag['regions']}; countries: {diag['countries']}.",f"Material exposure rows: {diag['material_abs_exposure_rows']}; regions: {diag['material_abs_exposure_regions']}; signed exposure p90–p10: {diag['exposure_p90_p10_pp']:.6g} percentage points."]
 if has:lines += [f"Estimated slope: {estimate['beta']:.6g} outcome percentage points per +1 percentage point R&D-share change; region-cluster SE {estimate['cluster_region_se']:.6g}; two-sided p={estimate['p_two_sided']:.6g}."]
 else:lines+=['No coefficient was released because a frozen gate failed.']
 if diag.get('gate_failures'):lines+=['Gate failures: '+', '.join(diag['gate_failures'])+'.']
 lines+=['','The four cells share sources, geography and years. No causal R&D effect, policy effect, school or position finding is established. NUTS boundary and source-vintage caveats remain.','']
 (target/'result_card.md').write_text('\n'.join(lines))
 (target/'replication.py').write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess,sys\nroot=Path(__file__).resolve().parents[3]\nsubprocess.run([sys.executable,str(root/'scripts/run_eurostat_regional_rd_forward_2026.py'),'--verify',*sys.argv[1:]],check=True)\n")
 packet={'packet_version':1,'hypothesis':{'id':case,'path':spec_rel},'preregistration':{'commit':REG,'steelman':spec['steelman'],'source_plan':AUDIT_REL,'key_roster':lock['roster']['path']},'source':source,'family':family,'reproduction':{'runner':RUNNER_REL,'command':'python3 '+RUNNER_REL+' --verify --source-root <retained IESET source checkout>','result_sha256':sha(target/'diagnostics.json')},'result':{'sample':diag,'primary':estimate,'gate_failures':diag.get('gate_failures',[]),'verdict':verdict},'limitations':diagnostic['limitations'],'correction':correction}
 (target/'evidence_packet.yaml').write_text(yaml.safe_dump(packet,sort_keys=False,allow_unicode=True))
 parquet_write(target/'metric_results.parquet',{'verdict':[verdict],'complete_rows':[diag['complete_rows']],'regions':[diag['regions']],'countries':[diag['countries']]},pa.schema([('verdict',pa.string()),('complete_rows',pa.int64()),('regions',pa.int64()),('countries',pa.int64())]))
 if set(p.name for p in target.iterdir())!=set(ARTIFACTS):raise ValueError('Run artifact roster mismatch')


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 group=ap.add_mutually_exclusive_group(required=True);group.add_argument('--run',action='store_true');group.add_argument('--verify',action='store_true')
 ap.add_argument('--source-root',required=True,type=Path);args=ap.parse_args()
 lock,specs,by_case=verify_custody(args.source_root)
 values=load_values(args.source_root,lock)
 results={}
 for case in lock['hypothesis_ids']:
  spec=specs[case];t=spec['falsification']['threshold'];panel,diag=panel_for(case,by_case[case],values,t)
  estimate,verdict=classify(panel,diag,t)
  results[case]=(diag,estimate,verdict)
 with tempfile.TemporaryDirectory(prefix='ieset_regional_rd_') as tmp:
  base=Path(tmp)
  for case in lock['hypothesis_ids']:
   diag,estimate,verdict=results[case];generated=base/case
   emit(generated,case,specs[case],lock,diag,estimate,verdict)
   target=ROOT/'engine/runs'/case
   if args.verify:
    if not target.is_dir():raise ValueError('Run directory absent: '+case)
    for art in ARTIFACTS:
     if sha(generated/art)!=sha(target/art):raise ValueError('Exact replay mismatch: '+case+'/'+art)
    print(case,'exact replay matched',len(ARTIFACTS),'artifacts; verdict',verdict,flush=True)
   else:
    if target.exists():raise ValueError('Run directory already exists: '+case)
    shutil.copytree(generated,target)
    print(case,verdict,'complete',diag['complete_rows'],'regions',diag['regions'],'gates',diag.get('gate_failures',[]),flush=True)

if __name__=='__main__':main()
