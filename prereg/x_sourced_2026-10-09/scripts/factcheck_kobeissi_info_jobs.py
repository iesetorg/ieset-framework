"""Fact-check (not pre-registered): 'US Information-sector employment lowest since 2014' (KobeissiLetter 2107617937142014334)."""
import glob, json, pathlib, datetime, pandas as pd
W=pathlib.Path.home()/"IESET-worktrees/corpus-hypotheses-2026-10-09"; OUT=pathlib.Path.home()/"IESET-x-build/runs/factcheck_kobeissi_information_jobs_lowest_since_2014"
fs=sorted(glob.glob(str(W/"data/vintages/bls/CES5000000001@2026-10-09T1322[5-9]*.parquet"))+glob.glob(str(W/"data/vintages/bls/CES5000000001@2026-10-09T13230*.parquet")))
d=pd.concat([pd.read_parquet(f) for f in fs]); d=d[d.period.str.startswith('M')&(d.period!='M13')]
d['date']=pd.to_datetime(d.year.astype(str)+'-'+d.period.str[1:]+'-01'); s=d.drop_duplicates('date',keep='last').set_index('date').value.astype(float).sort_index()
lm=s.index[-1]; last=s.iloc[-1]
lower=s[(s<=last)&(s.index<lm)]; pand=(s.index>='2020-03-01')&(s.index<='2021-12-01')
lower_ex=s[(s<=last)&(s.index<lm)&~pand]
res=dict(series="CES5000000001 (Information, SA, thousands)", latest_month=str(lm.date()), latest=last, prev_month=s.iloc[-2],
  last_month_at_or_below_latest=str(lower.index[-1].date()), its_value=lower.iloc[-1],
  last_month_at_or_below_ex_pandemic=str(lower_ex.index[-1].date()), its_value_ex=lower_ex.iloc[-1],
  peak=str(s.idxmax().date()), peak_value=s.max(), drop_from_peak_pct=(last/s.max()-1)*100, change_since_jan25=last-s['2025-01-01'],
  verdict="PARTIAL", note="Literally false (pandemic months 2020-21 were lower, last at/below Dec-2020); true excluding the pandemic: lowest since "+lower_ex.index[-1].strftime('%b %Y')+". Sep-26 is preliminary.",
  inputs=[str(pathlib.Path(f).relative_to(W)) for f in fs], run_utc=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), preregistered=False)
(OUT/"results.json").write_text(json.dumps(res,indent=1,default=float)); print(json.dumps(res,indent=1,default=float))
