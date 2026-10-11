import glob, json, pathlib, datetime, numpy as np, pandas as pd, statsmodels.formula.api as smf
REPO=pathlib.Path(__file__).resolve().parents[3]; OUT=pathlib.Path(__file__).resolve().parents[1]/"runs"  # repo-relative (was ~/IESET + ~/IESET-x-build at original run)
def vint(pat): return sorted(glob.glob(str(REPO/"data/vintages"/pat)))[-1]
RES={}
def rec(hid, verdict, headline, metrics, inputs):
    d=OUT/hid; d.mkdir(parents=True, exist_ok=True)
    r=dict(hypothesis_id=hid, verdict=verdict, headline=headline, metrics=metrics, inputs=[str(pathlib.Path(i).relative_to(REPO)) for i in inputs],
           run_utc=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
    (d/"results.json").write_text(json.dumps(r, indent=1, default=float)); RES[hid]=r; print(f"[{verdict}] {hid}: {headline}")
def safe(f):
    try: f()
    except Exception as e: print("ERROR", f.__name__, repr(e))

def bls(s):
    f=max(glob.glob(str(REPO/f"data/vintages/bls/{s}@2026-10-09*.parquet")), key=lambda x:(len(pd.read_parquet(x)),x)); d=pd.read_parquet(f); d=d[d.period.str.startswith("M")&(d.period!="M13")]
    d["date"]=pd.to_datetime(d.year.astype(str)+"-"+d.period.str[1:]+"-01"); return d.set_index("date").value.astype(float).sort_index(), f

def h1():
    f=vint("indec_ipc/all@*.parquet"); d=pd.read_parquet(f).pivot(index="date",columns="component",values="mom_pct")
    w=d.loc["2025-01-01":"2026-08-01"]; gap=(w.headline-w.core).mean(); reg=(w.regulated-w.core).mean()
    v="SUPPORTED" if gap>=0.10 else ("REFUTED" if gap<=0 else "PARTIAL")
    rec("argentina_core_vs_headline_inflation_2025_2026", v, f"Jan25-Aug26 mean m/m: headline {w.headline.mean():.2f}%, core {w.core.mean():.2f}%, gap {gap:+.2f}pp; regulated-core {reg:+.2f}pp",
        dict(n=len(w),mean_headline=w.headline.mean(),mean_core=w.core.mean(),mean_regulated=w.regulated.mean(),mean_seasonal=w.seasonal.mean(),gap=gap,reg_minus_core=reg,
             last3=w.tail(3)[["headline","core","regulated"]].round(2).reset_index().astype(str).values.tolist()),[f])
def h2():
    f=vint("indec/148.3_INIVELNAL_DICI_M_26@2026-10-09*.parquet"); s=pd.read_parquet(f).set_index("date").value; m=s.pct_change()*100
    dec=m.loc["2023-12-01"]; last=m.iloc[-1]; m12=m.iloc[-12:].mean(); yoy=(s.iloc[-1]/s.iloc[-13]-1)*100
    v="SUPPORTED" if dec>=20 and last<=2.5 and m12<=3 else ("REFUTED" if last>4 else "PARTIAL")
    rec("argentina_monthly_cpi_25pct_to_under_2pct_2023_2026", v, f"Dec-23 m/m {dec:.1f}% -> {m.index[-1]:%b-%y} {last:.1f}%; last-12m mean {m12:.2f}%/mo; y/y {yoy:.1f}%",
        dict(dec23=dec,latest=last,latest_month=str(m.index[-1].date()),mean12=m12,yoy=yoy,min_since_2024=m.loc["2024":].min()),[f])
def yoy_mean(s,start): return (s.pct_change(12)*100).loc[start:].mean()
def h3():
    sea,f1=bls("SMU53426607072200001"); us,f2=bls("CEU7072200001")
    end=min(sea.index[-1],us.index[-1]); a=yoy_mean(sea[:end],"2025-01-01"); b=yoy_mean(us[:end],"2025-01-01")
    v="SUPPORTED" if (a<=b-1.0 and a<0) else ("REFUTED" if a>=b else "PARTIAL")
    rec("seattle_minimum_wage_restaurant_employment_2025_2026", v, f"Jan25-{end:%b%y} mean y/y food-service jobs: Seattle MSA {a:+.2f}% vs US {b:+.2f}% (latest Seattle {sea[end]:.1f}k vs {sea[end-pd.DateOffset(years=1)]:.1f}k yr ago)",
        dict(seattle_mean_yoy=a,us_mean_yoy=b,end=str(end.date()),seattle_latest=sea[end],us_latest=us[end]),[f1,f2])
def h4():
    ca,f1=bls("SMU06000007072200001"); us,f2=bls("CEU7072200001"); end=min(ca.index[-1],us.index[-1])
    # same-calendar-month base to net seasonality: base = Mar-2024 vs same month comparison via y/y chain
    same=end-pd.DateOffset(years=(end.year-2024)); base=pd.Timestamp("2024-03-01")
    ci=ca[end]/ca[base]*100; ui=us[end]/us[base]*100
    ci2=ca[end]/ca[pd.Timestamp(f"2023-{end.month:02d}-01")]*100; ui2=us[end]/us[pd.Timestamp(f"2023-{end.month:02d}-01")]*100
    g=ci-ui; v="SUPPORTED" if g<=-1.5 else ("REFUTED" if g>=0 else "PARTIAL")
    rec("california_fast_food_20_wage_restaurant_employment", v, f"Food-service jobs Mar-24 -> {end:%b-%y}: CA {ci-100:+.2f}% vs US {ui-100:+.2f}% (gap {g:+.2f}pp); same-month {end:%b}23->{end:%b%y}: CA {ci2-100:+.2f}% vs US {ui2-100:+.2f}%",
        dict(ca_idx=ci,us_idx=ui,gap=g,ca_vs_same_month_2023=ci2,us_vs_same_month_2023=ui2,end=str(end.date())),[f1,f2])
def h5():
    m,f=bls("CES3000000001"); ch=m.iloc[-1]-m.loc["2025-01-01"]; ytd=m.iloc[-1]-m.loc["2025-12-01"]
    v="SUPPORTED" if ch<=-20 else ("REFUTED" if ch>=20 else "PARTIAL")
    rec("us_manufacturing_jobs_change_since_jan_2025", v, f"Manufacturing jobs Jan-25 {m.loc['2025-01-01']:.0f}k -> {m.index[-1]:%b-%y} {m.iloc[-1]:.0f}k ({ch:+.0f}k; since Dec-25 {ytd:+.0f}k; prelim)",
        dict(jan25=m.loc["2025-01-01"],latest=m.iloc[-1],latest_month=str(m.index[-1].date()),change=ch,change_since_dec25=ytd,max_month_gain_2026=m.diff().loc["2026"].max()),[f])
def h6():
    fs={k:vint(f"smard/{k}_DE_month@*.parquet") for k in ["price_de_lu","wind_onshore","wind_offshore","solar","load"]}
    d=pd.concat({k:pd.read_parquet(f).set_index("date").value for k,f in fs.items()},axis=1).dropna()
    d["vre"]=(d.wind_onshore+d.wind_offshore+d.solar)/d.load*100; d["yr"]=d.index.year; d["mo"]=d.index.month
    r=smf.ols("price_de_lu ~ vre + C(yr) + C(mo)",d).fit(cov_type="HC3"); b,p=r.params.vre,r.pvalues.vre
    v="SUPPORTED" if (b<0 and p<0.05) else ("REFUTED" if (b>0 and p<0.05) else "INCONCLUSIVE")
    rec("germany_wind_solar_share_lowers_wholesale_price", v, f"+10pp wind+solar share of load -> {10*b:+.1f} EUR/MWh day-ahead (p={p:.3g}, n={int(r.nobs)}, yr+month FE)",
        dict(beta_per_pp=b,p=p,n=int(r.nobs),r2=r.rsquared,vre_mean_2019=d.loc['2019','vre'].mean(),vre_mean_2025=d.loc['2025','vre'].mean(),price_2019=d.loc['2019','price_de_lu'].mean(),price_2025=d.loc['2025','price_de_lu'].mean()),list(fs.values()))
def h7():
    fg=vint("eia_v2/electricity_electric-power-operational-data_annual*.parquet"); fp=vint("eia_v2/electricity_retail-sales_annual*.parquet")
    g=pd.read_parquet(fg); g["period"]=g.period.astype(int); g=g.pivot_table(index=["location","period"],columns="fueltypeid",values="generation").fillna(0)
    g["vre"]=(g.SUN+g.WND)/g.ALL*100; g["gas"]=g.NG/g.ALL*100
    p=pd.read_parquet(fp); p=p[p.sectorid=="RES"]; p["period"]=p.period.astype(int); p=p.set_index(["stateid","period"]).price.astype(float)
    states=[s for s in g.index.get_level_values(0).unique() if len(s)==2 and s!="US" and (s,2010) in p.index and (s,2025) in p.index]
    rows=[dict(st=s,dp=p[(s,2025)]-p[(s,2010)],p10=p[(s,2010)],dv=g.loc[(s,2025),"vre"]-g.loc[(s,2010),"vre"],dg=g.loc[(s,2025),"gas"]-g.loc[(s,2010),"gas"]) for s in states if (s,2025) in g.index and (s,2010) in g.index]
    X=pd.DataFrame(rows); r=smf.ols("dp ~ dv + dg + p10",X).fit(cov_type="HC3"); r2=smf.ols("dp ~ dv + dg + p10",X[~X.st.isin(["AK","HI"])]).fit(cov_type="HC3")
    b,pv=r.params.dv,r.pvalues.dv; v="SUPPORTED" if (b>0 and pv<0.05) else ("REFUTED" if (b<0 and pv<0.05) else "INCONCLUSIVE")
    top=X.nlargest(5,"dv")[["st","dv","dp"]].round(2).values.tolist()
    rec("us_state_wind_solar_share_vs_residential_price_2010_2025", v, f"Each +10pp wind+solar share 2010-25 -> {10*b:+.2f} c/kWh residential price change (p={pv:.2f}, n={len(X)}); ex-AK/HI {10*r2.params.dv:+.2f} (p={r2.pvalues.dv:.2f}); simple corr {X.dv.corr(X.dp):+.2f}",
        dict(beta_per_pp=b,p=pv,n=len(X),beta_exAKHI=r2.params.dv,p_exAKHI=r2.pvalues.dv,corr=X.dv.corr(X.dp),top5_vre_growth=top,median_dp=X.dp.median()),[fg,fp])
def h8():
    f=vint("uscbp/nationwide_encounters_state@*.parquet"); d=pd.read_parquet(f); d=d[d.land_border_region=="Southwest Land Border"]
    fy26=d[d.fiscal_year==2026]; months=set(fy26.month); a=fy26.encounter_count.sum(); b=d[(d.fiscal_year==2023)&d.month.isin(months)].encounter_count.sum()
    m=d.groupby("date").encounter_count.sum().sort_index(); ratio=a/b
    v="SUPPORTED" if ratio<=0.10 else ("REFUTED" if ratio>=0.5 else "PARTIAL")
    rec("us_southwest_border_encounters_collapse_fy2026", v, f"SW border encounters FY26 YTD ({len(months)} mo) {a:,.0f} vs FY23 same months {b:,.0f}: {100*(ratio-1):.1f}% (latest month {m.index[-1]:%b-%y}: {m.iloc[-1]:,.0f})",
        dict(fy26=a,fy23_same=b,ratio=ratio,n_months=len(months),latest_month=str(m.index[-1].date()),latest=m.iloc[-1],peak=m.max(),peak_month=str(m.idxmax().date())),[f])
def h9():
    f=vint("atlanta_fed_wgt/wgt_Average_Wage_Quartile@*.parquet"); d=pd.read_parquet(f).pivot(index="date",columns="group",values="median_wage_growth_pct")
    gap=d["Lowest quartile of wage distribution"]-d["Highest quartile of wage distribution"]
    pre=gap.loc["2023-01-01":"2024-06-01"].mean(); post=gap.loc["2025-02-01":].mean(); dl=post-pre
    q1pre=d["Lowest quartile of wage distribution"].loc["2023-01-01":"2024-06-01"].mean(); q1post=d["Lowest quartile of wage distribution"].loc["2025-02-01":].mean()
    v="SUPPORTED" if dl>=0.5 else ("REFUTED" if dl<=-0.5 else "INCONCLUSIVE")
    rec("border_closure_raises_low_wage_growth_2025_2026", v, f"Bottom-minus-top quartile wage growth gap: {pre:+.2f}pp (Jan23-Jun24) -> {post:+.2f}pp (Feb25-{gap.index[-1]:%b%y}); change {dl:+.2f}pp. Bottom quartile {q1pre:.1f}% -> {q1post:.1f}%",
        dict(gap_pre=pre,gap_post=post,delta=dl,q1_pre=q1pre,q1_post=q1post,latest=str(gap.index[-1].date()),gap_latest=gap.iloc[-1]),[f])
def h10():
    fi=vint("imf_weo_sdmx/WEO__NID_NGDP@*.parquet"); fg=vint("imf_weo_sdmx/WEO__NGDP_RPCH@*.parquet"); C=["SLV","GTM","HND","NIC","CRI","PAN","DOM"]
    I=pd.read_parquet(fi); G=pd.read_parquet(fg)
    sel=lambda D:D[D.country_iso3.isin(C)&D.year.astype(int).between(2019,2025)].groupby("country_iso3").value.mean()
    i,g=sel(I),sel(G); rank=int(i.rank(ascending=False)["SLV"]); med=g.drop("SLV").median()
    v="SUPPORTED" if (rank==len(i) and g["SLV"]<med) else ("REFUTED" if (rank<=3 and g["SLV"]>med) else "PARTIAL")
    rec("el_salvador_investment_and_growth_vs_central_america_2019_2025", v, f"2019-25 avg investment/GDP: SLV {i['SLV']:.1f}% (rank {rank}/{len(i)}; peers {i.drop('SLV').min():.1f}-{i.drop('SLV').max():.1f}%); avg real growth SLV {g['SLV']:.2f}% vs peer median {med:.2f}%",
        dict(invest=i.round(2).to_dict(),growth=g.round(2).to_dict(),slv_rank=rank,peer_median_growth=med),[fi,fg])
def h11():
    fg=vint("imf_weo_sdmx/WEO__NGDP_RPCH@*.parquet"); fu=vint("imf_weo_sdmx/WEO__LUR@*.parquet")
    g=pd.read_parquet(fg); g=g[g.country_iso3=="SWE"].set_index(g[g.country_iso3=="SWE"].year.astype(int)).value
    u=pd.read_parquet(fu); u=u[u.country_iso3=="SWE"].set_index(u[u.country_iso3=="SWE"].year.astype(int)).value
    neg=all(g[y]<0 for y in (1991,1992,1993)); pk=u.loc[1990:1998].max()
    v="SUPPORTED" if (neg and pk>=11) else ("PARTIAL" if (neg or pk>=11) else "REFUTED")
    rec("sweden_1990s_crisis_three_year_contraction_12pct_unemployment", v, f"Sweden real GDP 1991/92/93: {g[1991]:+.1f}%/{g[1992]:+.1f}%/{g[1993]:+.1f}%; peak unemployment {pk:.1f}% ({int(u.loc[1990:1998].idxmax())}) vs 1990 {u[1990]:.1f}%",
        dict(g91=g[1991],g92=g[1992],g93=g[1993],lur_peak=pk,lur_1990=u[1990],cum_91_93=((1+g[1991]/100)*(1+g[1992]/100)*(1+g[1993]/100)-1)*100),[fg,fu])
for f in [h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11]: safe(f)
(OUT/"summary.json").write_text(json.dumps(RES,indent=1,default=float))
