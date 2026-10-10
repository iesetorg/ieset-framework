#!/usr/bin/env python3
"""Frozen two-test descriptive physician/maternal and education/fertility family."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

ROOT=Path(__file__).resolve().parents[1]
FAMILY='physician_education_followthrough_2026'
RUNNER='scripts/run_physician_education_family_2026.py'
PREREG='engine/audits/physician_education_family_prereg_2026-10-10.md'
SUMMARY='engine/audits/physician_education_family_results_2026-10-10.md'
ROSTER='data/pinned_evidence/physician_education_family_key_roster.csv'
ROSTER_SHA='8befd15bbffd25608f71ac534f5ccffcff876d1bc3aae0fc92ba2e2425756dc0'
LOCK='data/pinned_evidence/physician_education_family_2026.manifest.json'
MANIFESTS={
 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml':'e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e',
 'data/manifests/fetch_run_2026-05-05T210519Z.yaml':'5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112',
 'data/manifests/fetch_run_2026-04-30T130536Z.yaml':'ab56887949d3a51f3e3001ac1065c62538af1db4d4a722e39e29a774447f511b',
 'data/manifests/baseline_pull.yaml':'6a3666f79670d3e5bba88295bd113167c80032c67a9b51fe539cfd23853333c0',
}
SOURCES={
 'physician':{'publisher':'who_gho','series_id':'HWF_0001','manifest':'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml','path':'data/vintages/who_gho/HWF_0001@2026-04-30T114839Z.parquet','sha256':'fe1fff01e150281cc3b7413371377f5935afdc531a46a12c2886d11eeeed087f','rows':3693,'license':'CC-BY-NC-SA-3.0 IGO'},
 'maternal':{'publisher':'world_bank_wdi','series_id':'SH.STA.MMRT','manifest':'data/manifests/fetch_run_2026-05-05T210519Z.yaml','path':'data/vintages/world_bank_wdi/SH.STA.MMRT@2026-05-05T203546Z.parquet','sha256':'39e1fe35bd2dcd301842751cf4866cc8acb49685baf78576d8a7f1b1b37c4917','rows':17556,'license':'CC-BY-4.0'},
 'education':{'publisher':'world_bank_wdi','series_id':'SE.SEC.CUAT.UP.FE.ZS','manifest':None,'path':'data/vintages/world_bank_wdi/SE.SEC.CUAT.UP.FE.ZS@2026-05-03T054112Z.parquet','sha256':'55f50998acddb5029a0a18c6d0b6fce33b188f613d4c53cc287d1c2312f98fdd','rows':17556,'license':'CC-BY-4.0'},
 'fertility':{'publisher':'world_bank_wdi','series_id':'SP.DYN.TFRT.IN','manifest':'data/manifests/fetch_run_2026-04-30T130536Z.yaml','path':'data/vintages/world_bank_wdi/SP.DYN.TFRT.IN@2026-04-30T130516Z.parquet','sha256':'ff1eb90d4033e42ca63bb0de72c27f21044e55b69e44568d65321dd81cd8cfd1','rows':17556,'license':'CC-BY-4.0'},
}
STUDIES={
 'physician_maternal':{'id':'who_physician_density_maternal_mortality_forward_2026','topic':'healthcare','xrole':'physician','yrole':'maternal','nkeys':91,'min_complete':50,'material':2.0,'min_material':15,'spread':5.0,'top_one':0.20,'top_k':5,'top_k_max':0.65,'holdout':40,'beta':0.05,'xunit':'per +10 physicians per 10,000','yunit':'log maternal-mortality reduction'},
 'education_fertility':{'id':'wdi_female_upper_secondary_fertility_forward_2026','topic':'labour','xrole':'education','yrole':'fertility','nkeys':216,'min_complete':120,'material':10.0,'min_material':30,'spread':15.0,'top_one':0.15,'top_k':10,'top_k_max':0.55,'holdout':100,'beta':0.01,'xunit':'per +1 percentage point female upper-secondary attainment','yunit':'births-per-woman fertility reduction'},
}
FAMILY_ALPHA=0.01;FAMILY_SIZE=2;P_MAX=FAMILY_ALPHA/FAMILY_SIZE;MIN_SIGNS=4
CREDIT={'causal_credit':0,'policy_score_eligible':False,'policy_score_credit':0,'school_score_eligible':False,'school_score_credit':0,'featured_eligible':False}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def first_added(path):
 lines=git('log','--diff-filter=A','--format=%H','HEAD','--',path).decode().splitlines()
 if not lines:raise RuntimeError(f'no first-addition commit: {path}')
 return lines[-1]
def ancestor(a,b):return a!=b and subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def frozen(path,rev):
 p=ROOT/path
 if not p.is_file() or p.read_bytes()!=git('show',f'{rev}:{path}') or git('status','--porcelain','--',path).strip():raise RuntimeError(f'frozen-byte mismatch: {path}')
def spec_path(study):return f"hypotheses/{STUDIES[study]['topic']}/{STUDIES[study]['id']}.yaml"
def steelman_path(study):return f"hypotheses/steelman/{STUDIES[study]['id']}.md"
def run_dir(study):return f"engine/runs/{STUDIES[study]['id']}"
def roster():
 p=ROOT/ROSTER
 if sha(p)!=ROSTER_SHA:raise RuntimeError('roster hash mismatch')
 rows=list(csv.DictReader(p.open(newline='')))
 out={k:[r['country_iso3'] for r in rows if r['study_id']==k] for k in STUDIES}
 if len(rows)!=307:raise RuntimeError('roster row count mismatch')
 for k,codes in out.items():
  if len(codes)!=STUDIES[k]['nkeys'] or codes!=sorted(set(codes)):raise RuntimeError(f'roster shape mismatch: {k}')
 return out

def threshold(k):
 s=STUDIES[k]
 return {'family_id':FAMILY,'family_size':FAMILY_SIZE,'family_alpha':FAMILY_ALPHA,'bonferroni_p_max_two_sided':P_MAX,'meaningful_beta_min_abs':s['beta'],'min_complete_countries':s['min_complete'],'min_material_exposure_gain_countries':s['min_material'],'material_exposure_gain':s['material'],'min_exposure_p90_p10_spread':s['spread'],'max_top_country_residualized_exposure_share':s['top_one'],f"max_top_{s['top_k']}_residualized_exposure_share":s['top_k_max'],'min_leave_one_hash_fold_out_countries':s['holdout'],'min_concordant_holdouts_for_directional_verdict':MIN_SIGNS,'roster_sha256':ROSTER_SHA,'source_lock_path':LOCK,**CREDIT}

def registration_commit():
 paths=[RUNNER,PREREG,ROSTER]+[p for k in STUDIES for p in (spec_path(k),steelman_path(k))]
 revs={first_added(p) for p in paths}
 if len(revs)!=1:raise RuntimeError('family registration files must first appear in one commit')
 reg=revs.pop()
 for p in paths:frozen(p,reg)
 if git('ls-tree','-r','--name-only',reg,'--',LOCK,*[run_dir(k) for k in STUDIES]).strip():raise RuntimeError('source lock or run entered registration commit')
 codes=roster()
 for k in STUDIES:
  spec=yaml.safe_load((ROOT/spec_path(k)).read_text())
  if spec.get('hypothesis_id')!=STUDIES[k]['id'] or spec.get('status')!='pre_registered' or spec.get('evidence_type')!='descriptive' or spec.get('sample',{}).get('countries')!=codes[k] or spec.get('scope',{}).get('countries')!=codes[k] or spec.get('falsification',{}).get('threshold')!=threshold(k) or spec.get('covers_claims')!=[] or spec.get('linked_hypotheses')!=[]:raise RuntimeError(f'spec differs from frozen runner: {k}')
 return reg

def manifest_sources():
 for m,digest in MANIFESTS.items():
  if sha(ROOT/m)!=digest:raise RuntimeError(f'fetch/baseline manifest hash mismatch: {m}')
 out={}
 for role,s in SOURCES.items():
  if s['manifest'] is None:
   baseline=yaml.safe_load((ROOT/'data/manifests/baseline_pull.yaml').read_text())
   publishers=baseline.get('pulls',[]) if isinstance(baseline,dict) else baseline
   if not any(x.get('id')==s['series_id'] for item in publishers if isinstance(item,dict) for x in item.get('series',[])):
    raise RuntimeError('unmanifested education indicator absent from baseline pull declaration')
   out[role]={'publisher':s['publisher'],'series_id':s['series_id'],'parquet_path':s['path'],'sha256':s['sha256'],'rows':s['rows'],'license':s['license'],'source_url':f"https://api.worldbank.org/v2/country/all/indicator/{s['series_id']}?format=json",'methodology_url':f"https://databank.worldbank.org/metadataglossary/sustainable-development-goals-(sdgs)/series/{s['series_id']}",'vintage_manifest_status':'absent; baseline pull declaration only; exact raw bytes pinned'}
   continue
  entries=yaml.safe_load((ROOT/s['manifest']).read_text())['entries']
  matches=[e for e in entries if e.get('publisher')==s['publisher'] and e.get('series_id')==s['series_id'] and e.get('parquet_path')==s['path']]
  if len(matches)!=1:raise RuntimeError(f'manifest entry missing or duplicate: {role}')
  e=matches[0]
  if e.get('sha256')!=s['sha256'] or e.get('rows')!=s['rows'] or e.get('license')!=s['license']:raise RuntimeError(f'manifest mismatch: {role}')
  out[role]={x:e.get(x) for x in ('publisher','series_id','parquet_path','sha256','rows','license','fetch_utc','source_url','methodology_url')}
 return out

def lock_payload(reg):
 return {'schema':'ieset-physician-education-family-source-lock-v1','registration_commit':reg,'roster_sha256':ROSTER_SHA,'runner_sha256':hashlib.sha256(git('show',f'{reg}:{RUNNER}')).hexdigest(),'manifest_hashes':MANIFESTS,'sources':manifest_sources(),'family_id':FAMILY,'family_size':FAMILY_SIZE,'bonferroni_p_max':P_MAX}
def source_lock_commit(reg):
 old=[s['path'] for s in SOURCES.values() if git('ls-tree','-r','--name-only',reg,'--',s['path']).strip()]
 new=[s['path'] for s in SOURCES.values() if s['path'] not in old]
 revs={first_added(p) for p in [LOCK]+new}
 if len(revs)!=1:raise RuntimeError('lock and newly pinned raw files must enter one commit')
 lock=revs.pop()
 if not ancestor(reg,lock):raise RuntimeError('lock must strictly follow registration')
 for p in [LOCK]+new:frozen(p,lock)
 for p in old:
  frozen(p,reg)
  if git('log','--format=%H',f'{reg}..HEAD','--',p).strip():raise RuntimeError(f'earlier tracked raw source changed: {p}')
 if json.loads((ROOT/LOCK).read_text())!=lock_payload(reg):raise RuntimeError('source lock metadata mismatch')
 for role,s in SOURCES.items():
  if sha(ROOT/s['path'])!=s['sha256']:raise RuntimeError(f'raw hash mismatch: {role}')
 return lock

def valid_num(v):
 try:v=float(v)
 except (TypeError,ValueError):return None
 return v if math.isfinite(v) else None

def read_values(role):
 s=SOURCES[role]
 if role=='physician':
  d=pd.read_parquet(ROOT/s['path'],columns=['country_iso3','SpatialDimType','IndicatorCode','year','value'])
  if len(d)!=s['rows']:raise RuntimeError('physician row count changed')
  d=d[d.SpatialDimType.eq('COUNTRY')&d.IndicatorCode.eq('HWF_0001')&d.year.isin([2000,2010])]
  if d.duplicated(['country_iso3','year']).any():raise RuntimeError('duplicate physician key')
  return {(r.country_iso3,int(r.year)):valid_num(r.value) for r in d.itertuples(index=False)}
 d=pd.read_parquet(ROOT/s['path'],columns=['country_iso3','indicator_id','year','value','obs_status'])
 if len(d)!=s['rows'] or set(d.indicator_id.dropna().unique())!={s['series_id']}:raise RuntimeError(f'WDI source identity/row count changed: {role}')
 years=[2000,2010] if role=='education' else [2011,2019]
 d=d[d.year.isin(years)]
 if d.duplicated(['country_iso3','year']).any():
  d=d[d.country_iso3.notna()]
  if d.duplicated(['country_iso3','year']).any():raise RuntimeError(f'duplicate WDI source key: {role}')
 return {(r.country_iso3,int(r.year)):(valid_num(r.value) if pd.isna(r.obs_status) or str(r.obs_status).strip() in ('','A') else None) for r in d.itertuples(index=False)}

def frame(k,values,codes):
 rows=[];excluded={'missing_or_nonfinite_or_status':0,'out_of_range':0}
 xrole=STUDIES[k]['xrole'];yrole=STUDIES[k]['yrole']
 for c in codes:
  a,b=values[xrole].get((c,2000)),values[xrole].get((c,2010));y0,y1=values[yrole].get((c,2011)),values[yrole].get((c,2019))
  if any(v is None for v in (a,b,y0,y1)):
   excluded['missing_or_nonfinite_or_status']+=1;continue
  if k=='physician_maternal':
   okay=0<=a<=200 and 0<=b<=200 and 0<y0<=5000 and 0<y1<=5000
   x=(b-a)/10;y=math.log(y0)-math.log(y1);baseline_y=math.log(y0)
  else:
   okay=0<=a<=100 and 0<=b<=100 and 0<y0<=10 and 0<y1<=10
   x=b-a;y=y0-y1;baseline_y=y0
  if not okay:
   excluded['out_of_range']+=1;continue
  rows.append({'country_iso3':c,'exposure_gain_raw':b-a,'x':x,'y':y,'baseline_x':a,'baseline_y':baseline_y,'fold':int(hashlib.sha256(c.encode()).hexdigest()[:8],16)%5})
 return pd.DataFrame(rows),excluded

def fit(d,k):
 if len(d)<8:return None
 x=d.x.to_numpy(dtype=float);y=d.y.to_numpy(dtype=float)
 base=np.column_stack([np.ones(len(d)),d.baseline_x.to_numpy(dtype=float),d.baseline_y.to_numpy(dtype=float)])
 X=np.column_stack([base[:,0],x,base[:,1:]])
 if np.linalg.matrix_rank(X)!=X.shape[1]:return None
 f=sm.OLS(y,X).fit(cov_type='HC3',use_t=True)
 beta,se,p=map(float,(f.params[1],f.bse[1],f.pvalues[1]))
 residual=x-base@np.linalg.lstsq(base,x,rcond=None)[0];sq=residual**2;total=float(sq.sum())
 if not(math.isfinite(beta) and math.isfinite(se) and se>0 and math.isfinite(p) and total>1e-10):return None
 shares=np.sort(sq/total)[::-1];top_k=STUDIES[k]['top_k'];ci=f.conf_int(alpha=P_MAX)[1]
 return {'coefficient':beta,'standard_error_hc3':se,'p_two_sided':p,'df_resid':int(f.df_resid),'familywise_ci_99_5':[float(ci[0]),float(ci[1])],'top_country_residualized_exposure_share':float(shares[0]),f'top_{top_k}_residualized_exposure_share':float(shares[:top_k].sum())}

def analyze(k,values,codes):
 s=STUDIES[k];d,excluded=frame(k,values,codes);n=len(d);failed=[]
 if n<s['min_complete']:failed.append('min_complete_countries')
 material=int((d.exposure_gain_raw>=s['material']).sum()) if n else 0
 if material<s['min_material']:failed.append('min_material_exposure_gain_countries')
 spread=float(np.percentile(d.exposure_gain_raw,90)-np.percentile(d.exposure_gain_raw,10)) if n else None
 if spread is None or spread<s['spread']:failed.append('min_exposure_p90_p10_spread')
 est=fit(d,k)
 if est is None:failed.append('full_rank_positive_hc3_uncertainty_and_residual_exposure')
 else:
  if est['top_country_residualized_exposure_share']>s['top_one']:failed.append('max_top_country_residualized_exposure_share')
  if est[f"top_{s['top_k']}_residualized_exposure_share"]>s['top_k_max']:failed.append(f"max_top_{s['top_k']}_residualized_exposure_share")
 folds={}
 for i in range(5):
  sub=d[d.fold!=i] if n else d;model=fit(sub,k) if len(sub)>=s['holdout'] else None
  if len(sub)<s['holdout']:failed.append(f'min_holdout_countries_fold_{i}')
  elif model is None:failed.append(f'holdout_estimator_fold_{i}')
  folds[str(i)]={'countries':len(sub),'coefficient':model['coefficient'] if model else None}
 plus=sum(v['coefficient'] is not None and v['coefficient']>0 for v in folds.values());minus=sum(v['coefficient'] is not None and v['coefficient']<0 for v in folds.values())
 if failed:verdict='INCONCLUSIVE'
 elif est['coefficient']>=s['beta'] and est['p_two_sided']<=P_MAX and plus>=MIN_SIGNS:verdict='SUPPORTED'
 elif est['coefficient']<=-s['beta'] and est['p_two_sided']<=P_MAX and minus>=MIN_SIGNS:verdict='REFUTED'
 else:verdict='PARTIAL'
 return {'design_id':s['id'],'family_id':FAMILY,'family_size':FAMILY_SIZE,'bonferroni_p_max':P_MAX,'verdict':verdict,'analysis_scope':'descriptive_only','source_key_countries':s['nkeys'],'complete_countries':n,'excluded_reasons':excluded,'material_exposure_gain_countries':material,'exposure_gain_p90_p10_spread':spread,'estimate':est,'leave_one_hash_fold_out':folds,'positive_holdout_signs':plus,'negative_holdout_signs':minus,'failed_gates':sorted(set(failed)),'credit':{'causal':0,'policy':0,'school':0,'position':0,'featured':0}},d

def json_bytes(v):return (json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def yaml_bytes(v):return yaml.safe_dump(v,sort_keys=False,allow_unicode=True).encode()
def parquet_bytes(rows,columns):
 f=io.BytesIO();pd.DataFrame(rows,columns=columns).to_parquet(f,index=False,engine='pyarrow');return f.getvalue()
def result_artifacts(k,result,d,reg,lock):
 s=STUDIES[k];id=s['id'];est=result['estimate'] or {};verdict=result['verdict'];beta=est.get('coefficient');p=est.get('p_two_sided');failed=', '.join(result['failed_gates']) or 'none'
 title='Physician density and later maternal mortality' if k=='physician_maternal' else 'Female upper-secondary attainment and later fertility'
 caveat='WHO physician density may count active or registered doctors; WDI maternal mortality is modelled partly from fertility, birth attendants and GDP. Neither measures quality of obstetric care.' if k=='physician_maternal' else 'Female attainment is a cumulative age-25+ measure; total fertility is a period rate. Cohort composition, reproductive policy, income and social norms can move both.'
 card=f'''# {title}\n\n**{verdict}** — descriptive only; zero causal, policy, school, position and featured credit.\n\nComplete countries: {result['complete_countries']}/{s['nkeys']}. Material exposure gains: {result['material_exposure_gain_countries']}; p90−p10 exposure spread: {result['exposure_gain_p90_p10_spread']}. HC3 slope: {beta} {s['yunit']} {s['xunit']}; two-sided p: {p}; frozen family p cutoff: {P_MAX}. Failed gates: {failed}. Five fixed country-hash holdouts: +{result['positive_holdout_signs']}/5, −{result['negative_holdout_signs']}/5.\n\n{caveat} The two tests share a Bonferroni denominator of two even if either is inconclusive. Earlier physician-density/amenable-mortality and broad schooling/fertility work was visible; this local correction is not archive-wide.\n\nRegistration `{reg}` preceded source lock `{lock}`. Exact replay: `python3 -B {RUNNER} --verify`.\n'''
 manifest={'design_id':id,'family_id':FAMILY,'family_size':FAMILY_SIZE,'bonferroni_p_max':P_MAX,'evidence_type':'descriptive','verdict':verdict,'spec_commit':reg,'lock_commit':lock,'runner_sha256':sha(ROOT/RUNNER),'source_custody':{r:manifest_sources()[r] for r in (s['xrole'],s['yrole'])},'credit':result['credit'],'artifacts':['hypothesis.yaml','manifest.yaml','diagnostics.json','coefficients.parquet','metric_results.parquet','chart_data.json','result_card.md','replication.py','evidence_packet.yaml']}
 packet={'design_id':id,'family_id':FAMILY,'family_size':FAMILY_SIZE,'bonferroni_p_max':P_MAX,'verdict':verdict,'evidence_type':'descriptive','causal_claim':False,'policy_effect_credit':False,'source_hashes_verified':True,'strict_spec_lock_chronology_verified':True,'school_claim_links':[],'correction':{'disposition':'descriptive_calibration_only','family_id':FAMILY,'family_size':FAMILY_SIZE,'family_alpha':FAMILY_ALPHA,'bonferroni_p_max':P_MAX,**CREDIT},'interpretation':title+' association; no identified causal or policy effect.'}
 chart={'design_id':id,'sample_countries':len(d),'country_values_published':False,'exposure_gain_quantiles':{str(q):float(np.percentile(d.exposure_gain_raw,q)) for q in (10,25,50,75,90)} if len(d) else {},'outcome_change_quantiles':{str(q):float(np.percentile(d.y,q)) for q in (10,25,50,75,90)} if len(d) else {}}
 replication=f"#!/usr/bin/env python3\nimport subprocess,sys\nfrom pathlib import Path\nroot=Path(__file__).resolve().parents[3]\nraise SystemExit(subprocess.call([sys.executable,'-B',str(root/'{RUNNER}'),'--verify']))\n"
 rd=run_dir(k)
 return {f'{rd}/hypothesis.yaml':(ROOT/spec_path(k)).read_bytes(),f'{rd}/manifest.yaml':yaml_bytes(manifest),f'{rd}/diagnostics.json':json_bytes(result),f'{rd}/coefficients.parquet':parquet_bytes([{'term':'prior_exposure_gain','coefficient':beta,'standard_error_hc3':est.get('standard_error_hc3'),'p_two_sided':p,'verdict':verdict}],['term','coefficient','standard_error_hc3','p_two_sided','verdict']),f'{rd}/metric_results.parquet':parquet_bytes([{'metric':'later_outcome_improvement','value':beta,'p_value':p,'verdict':verdict,'complete_countries':result['complete_countries']}],['metric','value','p_value','verdict','complete_countries']),f'{rd}/chart_data.json':json_bytes(chart),f'{rd}/result_card.md':card.encode(),f'{rd}/replication.py':replication.encode(),f'{rd}/evidence_packet.yaml':yaml_bytes(packet)}

def family_summary(results,reg,lock):
 lines=['# Physician and education followthrough — locked two-test family','',f'Registration `{reg}` preceded source lock `{lock}` and results. Both tests remain in the Bonferroni denominator: family α={FAMILY_ALPHA}, n={FAMILY_SIZE}, two-sided p≤{P_MAX}. No selected values were opened before source lock.','', '| Test | Complete / key countries | HC3 beta | Two-sided p | Verdict | Failed gates |','| --- | ---: | ---: | ---: | --- | --- |']
 for k,s in STUDIES.items():
  r=results[k];e=r['estimate'] or {};lines.append(f"| {s['id']} | {r['complete_countries']}/{s['nkeys']} | {e.get('coefficient')} | {e.get('p_two_sided')} | {r['verdict']} | {', '.join(r['failed_gates']) or 'none'} |")
 lines+=['','The female educational-attainment raw vintage has no matching per-run fetch-manifest entry; the exact bytes, SHA-256 and baseline pull declaration are locked and this provenance limit is visible. No alternative vintage was substituted after results. Earlier archive physician-density/amenable-mortality and education/demography studies were visible; this family correction does not address archive-wide selection. Maternal mortality is modelled partly using fertility and socioeconomic inputs. No causal, policy, school, position or featured credit.','',f'Exact replay: `python3 -B {RUNNER} --verify`.','']
 return '\n'.join(lines).encode()
def reproduce(write):
 reg=registration_commit();lock=source_lock_commit(reg);codes=roster();values={role:read_values(role) for role in SOURCES};results={};expected={}
 for k in STUDIES:
  result,d=analyze(k,values,codes[k]);results[k]=result;expected.update(result_artifacts(k,result,d,reg,lock))
 expected[SUMMARY]=family_summary(results,reg,lock)
 for rel,payload in expected.items():
  p=ROOT/rel
  if write:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
  elif not p.is_file() or p.read_bytes()!=payload:raise RuntimeError(f'exact replay mismatch: {rel}')
 for k,r in results.items():print(k,r['verdict'],r['complete_countries'],r['estimate'],r['failed_gates'])
 print('family artifacts written' if write else 'exact replay passed')
def main():
 a=argparse.ArgumentParser();g=a.add_mutually_exclusive_group(required=True);g.add_argument('--make-lock',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--verify',action='store_true');args=a.parse_args()
 if args.make_lock:
  reg=registration_commit()
  for role,s in SOURCES.items():
   if sha(ROOT/s['path'])!=s['sha256']:raise RuntimeError(f'raw hash mismatch: {role}')
  p=ROOT/LOCK;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(json_bytes(lock_payload(reg)));print('family source lock written; commit before selected-value access')
 else:reproduce(args.run)
if __name__=='__main__':main()
