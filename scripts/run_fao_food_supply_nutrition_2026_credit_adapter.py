#!/usr/bin/env python3
"""Output-only annotation of the frozen FAOSTAT nutrition result packets.

The initial eight results were committed in 2814f80bac542b6feb52e15e590315352302d66c. This adapter replays the
frozen preregistered fit unchanged, then adds explicit zero-credit and source-
quality metadata. It never changes a sample, coefficient, p value, gate or verdict.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
import yaml

import run_fao_food_supply_nutrition_2026 as base

ADAPTER = 'scripts/run_fao_food_supply_nutrition_2026_credit_adapter.py'
ORIGINAL_RESULT_COMMIT = '2814f80bac542b6feb52e15e590315352302d66c'
CORRECTION = {
 'disposition':'descriptive_calibration_only',
 'family_id':base.FAMILY,
 'school_score_eligible':False,
 'school_score_credit':0,
 'policy_score_eligible':False,
 'policy_score_credit':0,
 'causal_credit':0,
 'featured_eligible':False,
 'output_only_annotation':'Added after the frozen measured result commit. No numerical result, gate, sample or verdict changed.',
}

def annotate(original:dict[str,bytes], sample:dict, x:str, y:str) -> dict[str,bytes]:
 flags=sample['admitted_flag_counts']
 n=sample['complete_rows']
 if flags.get('exposure_E')!=n or flags.get('outcome_X')!=n or sum(v for k,v in flags.items() if k.startswith('exposure_'))!=n or sum(v for k,v in flags.items() if k.startswith('outcome_'))!=n:
  raise RuntimeError('unexpected FAOSTAT E/X flag composition; annotation requires separate review')
 source_quality={
  'exposure':{'flag':'E','description':'FAO estimated food-supply indicator','admitted_rows':n,'share':1.0},
  'outcome':{'flag':'X','description':'External organization nutrition estimate redistributed by FAO','admitted_rows':n,'share':1.0},
  'source_note':'Health endpoints are modeled or externally estimated; annual rows do not represent independent direct surveys.',
 }
 out=dict(original)
 diagnostic=json.loads(out['diagnostics.json'])
 original_primary=diagnostic['primary']; original_verdict=diagnostic['verdict'];original_preflight=diagnostic['preflight']
 diagnostic['correction']=CORRECTION
 diagnostic['source_quality']=source_quality
 diagnostic['evidence_tier_recommendation']='calibration'
 diagnostic['frozen_runner']=diagnostic['runner']
 diagnostic['runner']=ADAPTER
 assert diagnostic['primary']==original_primary and diagnostic['verdict']==original_verdict and diagnostic['preflight']==original_preflight
 out['diagnostics.json']=(json.dumps(diagnostic,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
 packet=yaml.safe_load(out['evidence_packet.yaml'])
 original_result=packet['result']
 packet['source_quality']=source_quality
 packet['correction']=CORRECTION
 packet['reproduction']['runner']=ADAPTER
 packet['reproduction']['command']=f'python3 {ADAPTER} --verify --source-root <pinned-cache-root>'
 assert packet['result']==original_result
 out['evidence_packet.yaml']=yaml.safe_dump(packet,sort_keys=False,allow_unicode=True).encode()
 manifest=yaml.safe_load(out['manifest.yaml'])
 manifest['source_quality']=source_quality
 manifest['correction']=CORRECTION
 manifest['runner']=ADAPTER
 out['manifest.yaml']=yaml.safe_dump(manifest,sort_keys=False,allow_unicode=True).encode()
 card=out['result_card.md'].decode()
 card+=f'\n**Source-quality and public-credit review:** all {n} admitted food-supply rows carry FAOSTAT `E` (estimated) and all {n} nutrition outcome rows carry `X` (external organization). These are modeled or external estimates, not independently observed diets and health outcomes. Public visibility, if the evidence audit grants it, is calibration only with zero school, causal, policy, position and featured credit.\n'
 out['result_card.md']=card.encode()
 replication=("#!/usr/bin/env python3\nimport os, subprocess, sys\nroot=os.environ.get('IESET_RAW_ROOT')\n"
              "if not root: raise SystemExit('set IESET_RAW_ROOT to the matching raw cache')\n"
              f"raise SystemExit(subprocess.call([sys.executable,'{ADAPTER}','--verify','--source-root',root]))\n")
 out['replication.py']=replication.encode()
 return out

def verify_first_measured_commit(directory:Path, original:dict[str,bytes]) -> None:
 """Ensure every replayed pre-annotation byte matches the archived first result."""
 for name, content in original.items():
  rel=(directory/name).relative_to(base.ROOT).as_posix()
  saved=subprocess.run(['git','show',f'{ORIGINAL_RESULT_COMMIT}:{rel}'],
                       cwd=base.ROOT,capture_output=True,check=False)
  if saved.returncode or saved.stdout!=content:
   raise RuntimeError('frozen replay differs from first measured commit: '+rel)

def run(source_root:Path, verify:bool) -> None:
 lock,mapping,roster,meta=base.custody(source_root)
 rows=base.source_rows(source_root/base.RAW,mapping,roster)
 counts=Counter(); summaries=[]; pending=[]
 for slug,x,y,sign,_,_ in base.CASES:
  frame,sample=base.make_frame(slug,x,y,roster[slug],rows,meta)
  verdict,reason,result=base.fit(frame,sample,sign)
  spec=yaml.safe_load((base.ROOT/base.spec_rel(slug)).read_text())
  original=base.artifacts(slug,x,y,sign,spec,lock,meta,sample,verdict,reason,result)
  amended=annotate(original,sample,x,y)
  directory=base.ROOT/base.run_rel(slug)
  verify_first_measured_commit(directory,original)
  for name,new_bytes in amended.items():
   path=directory/name
   if not path.is_file():raise RuntimeError('missing original packet: '+str(path))
   if verify:
    if path.read_bytes()!=new_bytes:raise RuntimeError('annotated exact replay mismatch: '+str(path))
   else:
    if path.read_bytes()!=original[name]:raise RuntimeError('pre-annotation result differs from first measured output: '+str(path))
    pending.append((path,new_bytes))
  counts[verdict]+=1
  summaries.append((slug,verdict,sample['complete_rows'],sample['countries'],reason))
 if (base.ROOT/base.SUMMARY).read_bytes()!=base.summary_bytes(summaries):
  raise RuntimeError('frozen family summary differs from original runner')
 if verify:
  print('Exact adapter replay passed: eight unchanged numerical results with E/X and zero-credit annotations')
 else:
  for path,new_bytes in pending:path.write_bytes(new_bytes)
  print('Annotated eight frozen packets; verdict counts',dict(counts))

def main() -> None:
 p=argparse.ArgumentParser(description=__doc__)
 m=p.add_mutually_exclusive_group(required=True)
 m.add_argument('--apply',action='store_true');m.add_argument('--verify',action='store_true')
 p.add_argument('--source-root',type=Path,required=True)
 a=p.parse_args();run(a.source_root,a.verify)

if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('ERROR:',exc,file=sys.stderr)
  raise
