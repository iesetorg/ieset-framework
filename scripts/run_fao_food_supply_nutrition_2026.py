#!/usr/bin/env python3
"""Frozen FAOSTAT food-supply/nutrition country-panel family.

Commit registration and this runner, then commit the exact raw ZIP source lock.
Only --run/--verify read selected Value or row Flag fields after custody passes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import scipy.linalg
from scipy.stats import t as student_t
import yaml

ROOT = Path(__file__).resolve().parents[1]
FAMILY = 'fao_food_supply_nutrition_2026_10_10'
RUNNER = 'scripts/run_fao_food_supply_nutrition_2026.py'
PREREG = 'engine/audits/fao_food_supply_nutrition_prereg_2026-10-10.md'
ROSTER = 'data/pinned_evidence/fao_food_supply_nutrition_2026_key_roster.csv'
ROSTER_SHA = '5c631d0c187d7f714c179c5fe8d81bee745947f800e2df7515168a50f2cc8963'
CROSSWALK = 'data/pinned_evidence/fao_food_supply_nutrition_2026_m49_iso3.csv'
CROSSWALK_SHA = 'a7761fc28d856b7af94eca2aace8cec1fa26d42f23e56cf25b77b621d1f29dda'
LOCK = 'data/pinned_evidence/fao_food_supply_nutrition_2026.source.json'
SUMMARY = 'engine/audits/fao_food_supply_nutrition_results_2026-10-10.md'
RAW = 'data/vintages/faostat/food_security@2026-05-02T212150Z.zip'
RAW_SHA = '725f3592b383fd1a6896981c29c6db9ed85cb34f1687afed3cf4f86c7fef4de4'
ANCHORS = (2001, 2006, 2011, 2016)
P_MAX = 0.00125
MEANINGFUL_BETA = 0.25
MIN_ROWS = 300
MIN_COUNTRIES = 80
MIN_ANCHORS = 3
MIN_MATERIAL_COUNTRIES = 20
MAX_COUNTRY_SHARE = 0.20
MAX_ANCHOR_SHARE = 0.45
ALLOWED_FLAGS = {'A','E','X'}
ITEMS = {
 'energy': ('21010','Average dietary energy supply adequacy (percent) (3-year average)','%',10,5,300),
 'protein': ('21013','Average protein supply (g/cap/day) (3-year average)','g/cap/d',10,5,250),
 'animal_protein': ('21014','Average supply of protein of animal origin (g/cap/day) (3-year average)','g/cap/d',5,3,200),
 'staple_share': ('21012','Share of dietary energy supply derived from cereals, roots and tubers (percent) (3-year average)','%',10,5,100),
 'fat': ('21061','Average fat supply (g/cap/day) (3-year average)','g/cap/d',10,5,250),
 'anemia': ('21043','Prevalence of anemia among women of reproductive age (15-49 years) (percent)','%',None,None,100),
 'low_birthweight': ('21049','Prevalence of low birthweight (percent)','%',None,None,100),
 'stunting': ('21025','Percentage of children under 5 years of age who are stunted (modelled estimates) (percent)','%',None,None,100),
 'overweight': ('21041','Percentage of children under 5 years of age who are overweight (modelled estimates) (percent)','%',None,None,100),
}
CASES = [
 ('energy_stunting','energy','stunting','-',554,139),
 ('energy_low_birthweight','energy','low_birthweight','-',542,136),
 ('protein_stunting','protein','stunting','-',568,147),
 ('protein_low_birthweight','protein','low_birthweight','-',566,145),
 ('animal_protein_anemia','animal_protein','anemia','-',672,173),
 ('animal_protein_low_birthweight','animal_protein','low_birthweight','-',566,145),
 ('staple_share_anemia','staple_share','anemia','+',672,173),
 ('fat_overweight','fat','overweight','+',576,149),
]
LIMITATIONS = [
 'National food availability is not individual intake and may not reach disadvantaged households.',
 'FAO child outcomes are modeled UNICEF/WHO/World Bank estimates; women’s anemia is a WHO estimate. Values and trend revisions are not independent direct survey observations at each year.',
 'Income, infections, water, sanitation, care, health services, demographic change, reverse trends and unmeasured shocks confound the association.',
 'The eight cases share predictors, endpoints and a single FAOSTAT vintage. They are correlated local calibrations, not eight independent experiments; the family correction does not adjust selection across IESET.',
 'No causal, policy-effect, position, school-score or featured credit is permitted.',
]

def sha(path: Path) -> str:
 h = hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
 return h.hexdigest()

def git(*args: str) -> bytes:
 p = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
 if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace').strip())
 return p.stdout

def first_addition(rel: str) -> str:
 out=git('log','--diff-filter=A','--reverse','--format=%H','HEAD','--',rel).decode().splitlines()
 if len(out)!=1: raise RuntimeError('missing or ambiguous first addition: '+rel)
 return out[0]

def unchanged(rel: str, commit: str) -> None:
 if (ROOT/rel).read_bytes()!=git('show',commit+':'+rel): raise RuntimeError('frozen bytes changed: '+rel)
 if git('status','--porcelain','--',rel).strip(): raise RuntimeError('uncommitted frozen path: '+rel)

def spec_rel(slug: str) -> str:
 return 'hypotheses/healthcare/fao_food_supply_'+slug+'_2026.yaml'

def steel_rel(slug: str) -> str:
 return 'hypotheses/steelman/fao_food_supply_'+slug+'_2026.md'

def run_rel(slug: str) -> str:
 return 'engine/runs/fao_food_supply_'+slug+'_2026'

def custody(source_root: Path) -> tuple[dict,dict,dict[str,list[tuple[str,int]]],dict[str,str]]:
 regs=[PREREG,ROSTER,CROSSWALK,RUNNER]
 for slug,*_ in CASES: regs += [spec_rel(slug),steel_rel(slug)]
 commits={first_addition(rel) for rel in regs}
 if len(commits)!=1: raise RuntimeError('registration files not committed together')
 reg=commits.pop()
 for rel in regs: unchanged(rel,reg)
 lock_commit=first_addition(LOCK)
 if lock_commit==reg: raise RuntimeError('source lock must be a separate later commit')
 git('merge-base','--is-ancestor',reg,lock_commit)
 unchanged(LOCK,lock_commit)
 if sha(ROOT/ROSTER)!=ROSTER_SHA or sha(ROOT/CROSSWALK)!=CROSSWALK_SHA: raise RuntimeError('frozen roster or geography checksum mismatch')
 lock=json.loads((ROOT/LOCK).read_text())
 expected={'family_id':FAMILY,'source_path':RAW,'source_sha256':RAW_SHA,'key_roster_sha256':ROSTER_SHA,'m49_crosswalk_sha256':CROSSWALK_SHA,'license':'CC BY 4.0 with FAO statistical database terms'}
 for k,v in expected.items():
  if lock.get(k)!=v: raise RuntimeError('source lock contract mismatch: '+k)
 raw=source_root/RAW
 if not raw.is_file() or sha(raw)!=RAW_SHA: raise RuntimeError('missing or changed hash-pinned FAOSTAT raw ZIP')
 mapping={}
 for row in csv.DictReader(io.StringIO((ROOT/CROSSWALK).read_text())):
  if row['m49'] in mapping: raise RuntimeError('duplicate M49 crosswalk')
  mapping[row['m49']]=row['country_iso3']
 roster={slug:[] for slug,*_ in CASES}
 allrows=[]
 for row in csv.DictReader(io.StringIO((ROOT/ROSTER).read_text())):
  case,iso,anchor=row['case'],row['country_iso3'],int(row['anchor'])
  if case not in roster or anchor not in ANCHORS or len(iso)!=3: raise RuntimeError('invalid roster key')
  roster[case].append((iso,anchor));allrows.append((case,iso,anchor))
 if allrows!=sorted(set(allrows)): raise RuntimeError('roster duplicated or unsorted')
 specs={}
 for slug,x,y,sign,n,c in CASES:
  spec=yaml.safe_load((ROOT/spec_rel(slug)).read_text())
  th=spec['falsification']['threshold']
  if (spec['hypothesis_id']!='fao_food_supply_'+slug+'_2026' or spec['claim_direction']!=sign or
      th['family_id']!=FAMILY or th['family_size']!=8 or th['family_alpha']!=0.01 or
      th['p_max_two_sided_bonferroni']!=P_MAX or th['meaningful_beta_min_abs']!=MEANINGFUL_BETA or
      th['expected_key_rows']!=n or th['expected_key_countries']!=c or
      th['key_roster_sha256']!=ROSTER_SHA or th['m49_crosswalk_sha256']!=CROSSWALK_SHA or
      th['exposure_unit_scale']!=ITEMS[x][3] or th['material_within_country_range_raw_units']!=ITEMS[x][4] or
      th['expected_beta_sign']!=sign or len(roster[slug])!=n or len({iso for iso,_ in roster[slug]})!=c or
      th['source_lock_path']!=LOCK): raise RuntimeError('spec or roster differs from family contract: '+slug)
  specs[slug]=spec
 return lock,mapping,roster,{'registration_commit':reg,'source_lock_commit':lock_commit}

def source_rows(raw: Path,mapping: dict[str,str],roster:dict[str,list[tuple[str,int]]]) -> dict[tuple[str,str,int],tuple[str,str]]:
 allowed_years={name:({a for a in ANCHORS} if meta[3] else {a+4 for a in ANCHORS}) for name,meta in ITEMS.items()}
 by_code={meta[0]:name for name,meta in ITEMS.items()}
 rows={};keys={name:set() for name in ITEMS}
 with zipfile.ZipFile(raw) as z:
  names=[n for n in z.namelist() if n.endswith('All_Data_(Normalized).csv')]
  if len(names)!=1: raise RuntimeError('source ZIP normalized CSV ambiguity')
  with z.open(names[0]) as binary:
   reader=csv.DictReader(io.TextIOWrapper(binary,encoding='utf-8-sig',newline=''))
   required={'Area Code (M49)','Item Code','Item','Element','Year','Unit','Value','Flag'}
   if not required.issubset(set(reader.fieldnames or [])): raise RuntimeError('source CSV schema mismatch')
   for row in reader:
    name=by_code.get(row['Item Code'])
    if name is None or row['Element']!='Value':continue
    meta=ITEMS[name]
    label=row['Year']
    if meta[3]:
     if len(label)!=9 or label[4]!='-' or not label[:4].isdigit() or not label[5:].isdigit() or int(label[5:])!=int(label[:4])+2: continue
     year=int(label[:4])+1
    else:
     if not label.isdigit():continue
     year=int(label)
    if year not in allowed_years[name]:continue
    m49=row['Area Code (M49)'].strip("' ")
    try:m49=f'{int(m49):03d}'
    except ValueError:continue
    iso=mapping.get(m49)
    if not iso:continue
    if row['Item']!=meta[1] or row['Unit']!=meta[2]: raise RuntimeError('item label/unit mismatch: '+name)
    key=(name,iso,year)
    if key in rows:raise RuntimeError('duplicate raw item/country/year key: '+str(key))
    rows[key]=(row['Value'],row['Flag'])
    keys[name].add((iso,year))
 for slug,x,y,_,_,_ in CASES:
  pairs={(iso,a) for iso,a in keys[x] if a in ANCHORS and (iso,a+4) in keys[y]}
  counts=Counter(iso for iso,_ in pairs)
  frozen=sorted(p for p in pairs if counts[p[0]]>=2)
  if frozen!=roster[slug]:raise RuntimeError('raw ZIP keys do not reproduce frozen parquet-key roster: '+slug)
 return rows

def parse_cell(row: tuple[str,str],max_value:float) -> tuple[float|None,str]:
 value,flag=row
 if flag not in ALLOWED_FLAGS:return None,'inadmissible_flag_'+(flag or 'blank')
 try:v=float(value)
 except (ValueError,TypeError):return None,'nonnumeric_or_missing'
 if not math.isfinite(v) or v<0 or v>max_value:return None,'nonfinite_or_out_of_bounds'
 return v,flag

def make_frame(slug:str,x:str,y:str,roster:list[tuple[str,int]],rows:dict,meta:dict) -> tuple[pd.DataFrame,dict]:
 data=[];dropped=Counter();flags=Counter()
 for iso,a in roster:
  xx=rows.get((x,iso,a));yy=rows.get((y,iso,a+4))
  if xx is None or yy is None:raise RuntimeError('frozen source key missing')
  xv,xf=parse_cell(xx,ITEMS[x][5]);yv,yf=parse_cell(yy,ITEMS[y][5])
  if xv is None:dropped['exposure_'+xf]+=1;continue
  if yv is None:dropped['outcome_'+yf]+=1;continue
  data.append({'country_iso3':iso,'anchor':a,'x_raw':xv,'x':xv/ITEMS[x][3],'response':yv})
  flags['exposure_'+xf]+=1;flags['outcome_'+yf]+=1
 before=len(data)
 counts=Counter(row['country_iso3'] for row in data)
 frame=pd.DataFrame([row for row in data if counts[row['country_iso3']]>=2],columns=['country_iso3','anchor','x_raw','x','response'])
 material=0
 if not frame.empty:
  material=int(sum((g['x_raw'].max()-g['x_raw'].min())>=ITEMS[x][4] for _,g in frame.groupby('country_iso3')))
 sample={'key_rows':len(roster),'key_countries':len({c for c,_ in roster}),
         'complete_before_country_floor':before,'complete_rows':len(frame),
         'countries':int(frame['country_iso3'].nunique()) if not frame.empty else 0,
         'anchors':int(frame['anchor'].nunique()) if not frame.empty else 0,
         'material_countries':material,'material_range_raw_units':ITEMS[x][4],
         'excluded_source_rows_by_reason':dict(sorted(dropped.items())),
         'admitted_flag_counts':dict(sorted(flags.items()))}
 return frame,sample

def fit(frame:pd.DataFrame,sample:dict,sign:str) -> tuple[str,str,dict]:
 failures=[]
 if sample['complete_rows']<MIN_ROWS or sample['countries']<MIN_COUNTRIES:failures.append('complete_case_floor')
 if sample['anchors']<MIN_ANCHORS:failures.append('anchor_floor')
 if sample['material_countries']<MIN_MATERIAL_COUNTRIES:failures.append('material_country_floor')
 if failures:return 'INCONCLUSIVE',', '.join(failures),{'gates_failed':failures}
 nuisance=patsy.dmatrix('1 + C(country_iso3) + C(anchor)',frame,return_type='dataframe').to_numpy(dtype=float)
 x=frame['x'].to_numpy(dtype=float);y=frame['response'].to_numpy(dtype=float)
 n,k0=nuisance.shape
 q,r=scipy.linalg.qr(nuisance,mode='economic',check_finite=False)
 diag=np.abs(np.diag(r));tol=np.finfo(float).eps*max(n,k0)*float(diag.max())
 if np.any(diag<=tol) or n<=k0+1:return 'INCONCLUSIVE','full-rank gate failed',{'gates_failed':['full_rank']}
 xr=x-q@(q.T@x);yr=y-q@(q.T@y);xss=float(xr@xr)
 if not math.isfinite(xss) or xss<=(np.finfo(float).eps*max(n,k0+1)*max(1,float(np.linalg.norm(x))))**2:
  return 'INCONCLUSIVE','focal exposure rank gate failed',{'gates_failed':['focal_rank']}
 by_country=defaultdict(float);by_anchor=defaultdict(float)
 for c,a,sq in zip(frame['country_iso3'],frame['anchor'],xr*xr):by_country[c]+=float(sq);by_anchor[int(a)]+=float(sq)
 cshare=max(by_country.values())/xss;ashare=max(by_anchor.values())/xss
 sample['top_country_residualized_exposure_share']=cshare;sample['top_anchor_residualized_exposure_share']=ashare
 if cshare>MAX_COUNTRY_SHARE or ashare>MAX_ANCHOR_SHARE:
  return 'INCONCLUSIVE','residualized exposure concentration cap failed',{'gates_failed':['residual_concentration'],'top_country_share':cshare,'top_anchor_share':ashare}
 beta=float(xr@yr/xss);err=yr-beta*xr
 scores=defaultdict(float)
 for c,score in zip(frame['country_iso3'],xr*err):scores[c]+=float(score)
 g=sample['countries'];k=k0+1
 variance=(g/(g-1))*((n-1)/(n-k))*math.fsum(s*s for s in scores.values())/(xss*xss)
 se=math.sqrt(variance) if math.isfinite(variance) and variance>=0 else float('nan')
 if not math.isfinite(beta) or not math.isfinite(se) or se<=0:
  return 'INCONCLUSIVE','cluster uncertainty gate failed',{'gates_failed':['cluster_uncertainty']}
 p=float(2*student_t.sf(abs(beta/se),g-1));crit=float(student_t.ppf(1-P_MAX/2,g-1))
 result={'coefficient':beta,'std_error':se,'p_value_two_sided':p,'confidence_level':1-P_MAX,
         'confidence_interval':[beta-crit*se,beta+crit*se],
         'n_rows':n,'n_countries':g,'df_inference':g-1,'design_rank':k,
         'top_country_residualized_exposure_share':cshare,'top_anchor_residualized_exposure_share':ashare,
         'method':'country/anchor fixed-effect OLS; country CR1; two-sided Student t(G-1)'}
 directional=beta if sign=='+' else -beta
 if directional>=MEANINGFUL_BETA and p<=P_MAX:return 'SUPPORTED','predicted sign, magnitude and eight-test cutoff pass',result
 if directional<=-MEANINGFUL_BETA and p<=P_MAX:return 'REFUTED','opposite sign, magnitude and eight-test cutoff pass',result
 return 'PARTIAL','estimable association does not meet both frozen directional gates',result

def artifacts(slug:str,x:str,y:str,sign:str,spec:dict,lock:dict,meta:dict,sample:dict,verdict:str,reason:str,result:dict) -> dict[str,bytes]:
 ident=spec['hypothesis_id'];specpath=spec_rel(slug)
 inputs={'faostat_food_security':{'publisher':'FAO','series_id':'Suite of Food Security Indicators','path':RAW,'sha256':RAW_SHA,'catalog_url':lock['catalog_url'],'license':lock['license']}}
 packet={'packet_version':1,'hypothesis':{'id':ident,'path':specpath,'topic':'healthcare'},
  'preregistration':{'spec_commit':meta['registration_commit'],'source_lock_commit':meta['source_lock_commit'],'key_roster':ROSTER,'key_roster_sha256':ROSTER_SHA},
  'family':{'id':FAMILY,'size':8,'members':sorted('fao_food_supply_'+s+'_2026' for s,*_ in CASES)},
  'source':{'inputs':inputs,'m49_crosswalk':CROSSWALK,'m49_crosswalk_sha256':CROSSWALK_SHA},
  'result':{'verdict':verdict,'reason':reason,'gate_failures':result.get('gates_failed',[]),'sample':sample,'primary':result},
  'reproduction':{'runner':RUNNER,'command':f'python3 {RUNNER} --verify --source-root <pinned-cache-root>'},
  'limitations':LIMITATIONS,'credit':{'causal':0,'policy_effect':0,'school':0,'position':0,'featured':0}}
 diagnostic={'hypothesis_id':ident,'family_id':FAMILY,'verdict':verdict,'verdict_label':verdict,'verdict_reason':reason,
  'runner':RUNNER,'preregistration_commit':meta['registration_commit'],'source_lock_commit':meta['source_lock_commit'],
  'source_lock':LOCK,'source_sha256':RAW_SHA,'template':'panel_fe','preflight':sample,'primary':result,
  'p_max_two_sided_bonferroni':P_MAX,'meaningful_beta_min_abs':MEANINGFUL_BETA,
  'data_status':{'variables_missing':[],'input_vintages':[inputs['faostat_food_security']]},'limitations':LIMITATIONS}
 manifest={'hypothesis_id':ident,'status':verdict,'runner':RUNNER,'preregistration_commit':meta['registration_commit'],
  'source_lock_commit':meta['source_lock_commit'],'source_lock':LOCK,'vintages':[inputs['faostat_food_security']],
  'derived_panel':sample,'family_correction':{'size':8,'alpha':0.01,'p_max':P_MAX}}
 if verdict=='INCONCLUSIVE':finding=f'**INCONCLUSIVE.** {reason}. No coefficient or directional claim is graded.'
 else:finding=(f'**{verdict}.** Frozen ecological beta {result["coefficient"]:+.5f} outcome percentage points per one registered exposure unit '
               f'(country CR1 SE {result["std_error"]:.5f}; two-sided p={result["p_value_two_sided"]:.5g}; '
               f'{result["n_rows"]} country-waves, {result["n_countries"]} countries). {reason}.')
 card=(f'# FAOSTAT food supply: {x} and later {y}\n\n{finding}\n\n'
       f'Four 3-year supply windows centered in 2001, 2006, 2011 and 2016 precede annual outcomes by four midpoint years. '
       f'Exposure unit is {ITEMS[x][3]} {ITEMS[x][2]}; outcome unit is percentage points. '
       f'FAOSTAT source flags A/E/X were admitted and counted in diagnostics. '\
       f'This is one of eight correlated national ecological calibrations under a shared 0.01/8 cutoff. '
       f'Food availability is not individual intake; endpoints are modeled or externally estimated; unmeasured confounding remains. '
       f'No causal, policy, position, school or featured credit. Exact replay needs the hash-pinned raw ZIP.\n')
 replication=("#!/usr/bin/env python3\nimport os, subprocess, sys\nroot=os.environ.get('IESET_RAW_ROOT')\n"
              "if not root: raise SystemExit('set IESET_RAW_ROOT to the matching raw cache')\n"
              f"raise SystemExit(subprocess.call([sys.executable,'{RUNNER}','--verify','--source-root',root]))\n")
 return {'manifest.yaml':yaml.safe_dump(manifest,sort_keys=False,allow_unicode=True).encode(),
         'evidence_packet.yaml':yaml.safe_dump(packet,sort_keys=False,allow_unicode=True).encode(),
         'diagnostics.json':(json.dumps(diagnostic,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode(),
         'result_card.md':card.encode(),'hypothesis.yaml':(ROOT/specpath).read_bytes(),'replication.py':replication.encode()}

def summary_bytes(summaries:list[tuple]) -> bytes:
 lines=['# FAOSTAT food-supply/nutrition family — measured results','',
  'Eight frozen pathway cells remain in the Bonferroni denominator, including inconclusive cases. Source provenance and gate chronology are in the preregistration, source lock and run packets.','',
  '| Pathway | Verdict | Complete rows | Countries | Gate reason |','| --- | --- | ---: | ---: | --- |']
 for slug,verdict,n,c,reason in summaries:lines.append(f'| `{slug}` | {verdict} | {n} | {c} | {reason} |')
 lines+=['','All results are national ecological associations; supply is not individual intake and endpoints are modeled/external estimates. These eight outcomes and exposures are correlated. The local 0.01/8 threshold does not correct selection across the full IESET corpus. Zero causal, policy-effect, position, school-score and featured credit.','']
 return '\n'.join(lines).encode()

def run(source_root:Path,verify:bool) -> None:
 lock,mapping,roster,meta=custody(source_root)
 rows=source_rows(source_root/RAW,mapping,roster)
 summaries=[]
 for index,(slug,x,y,sign,_,_) in enumerate(CASES,1):
  frame,sample=make_frame(slug,x,y,roster[slug],rows,meta)
  verdict,reason,result=fit(frame,sample,sign)
  spec=yaml.safe_load((ROOT/spec_rel(slug)).read_text())
  produced=artifacts(slug,x,y,sign,spec,lock,meta,sample,verdict,reason,result)
  directory=ROOT/run_rel(slug)
  if verify:
   mismatches=[name for name,b in produced.items() if not (directory/name).is_file() or (directory/name).read_bytes()!=b]
   if mismatches:raise RuntimeError('exact replay mismatch '+slug+': '+', '.join(mismatches))
  else:
   directory.mkdir(parents=True,exist_ok=False)
   for name,b in produced.items():(directory/name).write_bytes(b)
  summaries.append((slug,verdict,sample['complete_rows'],sample['countries'],reason))
  print(f'{index}/8 {slug}: {verdict}; {sample["complete_rows"]} rows, {sample["countries"]} countries',flush=True)
 summary=summary_bytes(summaries)
 if verify:
  if (ROOT/SUMMARY).read_bytes()!=summary:raise RuntimeError('family summary exact replay mismatch')
  print('Exact replay passed for 8/8 packets and family summary')
 else:
  if (ROOT/SUMMARY).exists():raise RuntimeError('family summary already exists')
  (ROOT/SUMMARY).write_bytes(summary)
  print('Verdicts',dict(Counter(v for _,v,*_ in summaries)))

def self_test() -> None:
 groups=['AAA','BBB','CCC','DDD','EEE']
 synthetic=pd.DataFrame([{'country_iso3':c,'anchor':a,'x_raw':10+i*7+(a-2001)*0.3+(i%2)*(a-2001)*0.2,
                         'x':(10+i*7+(a-2001)*0.3+(i%2)*(a-2001)*0.2)/10,
                         'response':30-i+(a-2001)*0.1+(i%3)*(a-2001)*0.05}
                         for i,c in enumerate(groups) for a in ANCHORS])
 sample={'complete_rows':len(synthetic),'countries':len(groups),'anchors':len(ANCHORS),'material_countries':5}
 verdict,reason,result=fit(synthetic,sample,'-')
 if verdict!='INCONCLUSIVE' or 'complete_case_floor' not in result.get('gates_failed',[]):
  raise RuntimeError('synthetic floor test failed')
 print('Synthetic minimum-sample gate passed')

def main() -> None:
 parser=argparse.ArgumentParser(description=__doc__)
 mode=parser.add_mutually_exclusive_group(required=True)
 mode.add_argument('--self-test',action='store_true');mode.add_argument('--check-custody',action='store_true')
 mode.add_argument('--run',action='store_true');mode.add_argument('--verify',action='store_true')
 parser.add_argument('--source-root',type=Path)
 args=parser.parse_args()
 if args.self_test:self_test();return
 if args.source_root is None:parser.error('--source-root is required for this mode')
 if args.check_custody:
  _,_,roster,meta=custody(args.source_root)
  print(f'Committed registration {meta["registration_commit"]}, later source lock {meta["source_lock_commit"]}, and {sum(map(len,roster.values()))} key rows passed; selected values unopened')
 else:run(args.source_root,args.verify)

if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('ERROR:',exc,file=sys.stderr)
  raise
