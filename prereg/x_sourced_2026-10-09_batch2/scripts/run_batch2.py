"""Run the 11 batch-2 pre-registered tests (specs committed in b79b1fb1e before any fetch).
Usage (repo root): python prereg/x_sourced_2026-10-09_batch2/scripts/run_batch2.py
Inputs: latest vintages written by fetch_batch2.py under data/vintages (gitignored)."""
import glob, json, pathlib, datetime, numpy as np, pandas as pd, statsmodels.formula.api as smf
ROOT = pathlib.Path(__file__).resolve().parents[3]; OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
V = ROOT / "data/vintages"
def vint(pat): return sorted(glob.glob(str(V / pat)))[-1]
RES = {}
def rec(hid, verdict, headline, metrics, inputs):
    d = OUT / hid; d.mkdir(parents=True, exist_ok=True)
    r = dict(hypothesis_id=hid, verdict=verdict, headline=headline, metrics=metrics,
             inputs=[str(pathlib.Path(i).relative_to(ROOT)) for i in inputs],
             run_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    (d / "results.json").write_text(json.dumps(r, indent=1, default=float)); RES[hid] = r; print(f"[{verdict}] {hid}: {headline}")
def safe(f):
    try: f()
    except Exception as e:
        import traceback; traceback.print_exc(); print("ERROR", f.__name__, repr(e))
def fred(s):
    f = vint(f"fred/{s}@*.parquet"); d = pd.read_parquet(f); d["date"] = pd.to_datetime(d.date)
    return d.set_index("date").value.astype(float).dropna().sort_index(), f
def eu(code, **flt):
    for f in sorted(glob.glob(str(V / f"eurostat/{code}@2026-10-09T17*.parquet")), reverse=True):
        d = pd.read_parquet(f)
        if all((c in d and (d[c] == v).any()) for c, v in flt.items()):
            for c, v in flt.items(): d = d[d[c] == v]
            return d, f
    raise FileNotFoundError(code, flt)

def b1():
    s, f1 = fred("PSAVERT"); ahe, f2 = fred("CES0500000003"); cpi, f3 = fred("CPIAUCSL")
    latest = s.iloc[-1]; jan = s.loc["2025-01-01"]; d = latest - jan; lo = s.loc["2023-01-01":"2024-12-01"].min(); low = latest < lo
    last_lower = s[s <= latest].index.max() if (s.iloc[:-1] <= latest).any() else None
    last_lower = s.iloc[:-1][s.iloc[:-1] <= latest].index.max()
    rw = (ahe / cpi).dropna(); rw6 = (rw.iloc[-1] / rw.iloc[-7] - 1) * 100; rw12 = (rw.iloc[-1] / rw.iloc[-13] - 1) * 100
    v = "SUPPORTED" if (d <= -1.0 and low and rw6 < 0) else ("REFUTED" if d >= 0 else "PARTIAL")
    rec("us_personal_saving_rate_fell_since_jan_2025", v,
        f"Saving rate Jan-25 {jan:.1f}% -> {s.index[-1]:%b-%y} {latest:.1f}% ({d:+.1f}pp); 2023-24 low {lo:.1f}%; last time at or below this: {last_lower:%b-%y}. Real avg hourly earnings {rw.index[-1]:%b-%y}: {rw6:+.2f}% over 6m, {rw12:+.2f}% y/y",
        dict(jan25=jan, latest=latest, latest_month=str(s.index[-1].date()), change_pp=d, min_2023_2024=lo, lowest_since_2022=bool(low),
             last_month_at_or_below=str(last_lower.date()), real_ahe_6m_pct=rw6, real_ahe_12m_pct=rw12, real_ahe_month=str(rw.index[-1].date())), [f1, f2, f3])

def b2():
    s, f = fred("A229RX0"); a = s.groupby(s.index.year).mean()
    cagr = lambda x0, x1, yrs: ((x1 / x0) ** (1 / yrs) - 1) * 100
    t45 = cagr(a[2016], a[2020], 4); bid = cagr(a[2020], a[2024], 4)
    l12 = s.iloc[-12:]; mid = l12.index.mean(); gap = (mid - pd.Timestamp("2024-07-01")).days / 365.25; t47 = cagr(a[2024], l12.mean(), gap)
    p45 = cagr(s["2017-01-01"], s["2021-01-01"], 4); pb = cagr(s["2021-01-01"], s["2025-01-01"], 4)
    gp = (s.index[-1] - pd.Timestamp("2025-01-01")).days / 365.25; p47 = cagr(s["2025-01-01"], s.iloc[-1], gp)
    near = abs(t45 - 3.9) <= 1 and abs(bid + 1.2) <= 1 and abs(t47 - 3.1) <= 1
    order = t45 > bid and t47 > bid
    v = "SUPPORTED" if (bid < 0 and order and near) else ("REFUTED" if t47 <= bid else ("PARTIAL" if order else "PARTIAL"))
    rec("us_real_disposable_income_growth_by_presidential_term", v,
        f"Real disposable income per person, annual-average basis: Trump-1 {t45:+.1f}%/yr, Biden {bid:+.1f}%/yr, Trump-2 {t47:+.1f}%/yr (to {s.index[-1]:%b-%y}). Jan-to-Jan basis (claim's likely method): {p45:+.1f} / {pb:+.1f} / {p47:+.1f}%/yr",
        dict(t45_annavg=t45, biden_annavg=bid, t47_annavg=t47, t47_gap_years=gap, t45_jan=p45, biden_jan=pb, t47_jan=p47, latest_month=str(s.index[-1].date()),
             within_1pp_of_claim=bool(near), ordering_holds=bool(order)), [f])

def b3():
    inc, f1 = fred("MEHOINUSA672N"); fx = vint("us_census/hstpov2@*.xlsx")
    x = pd.read_excel(fx, header=None).iloc[8:77, [0, 3]]; x.columns = ["yr", "pct"]
    x["year"] = x.yr.astype(str).str[:4].astype(int); x["pct"] = x.pct.astype(float)
    x = x.iloc[::-1].drop_duplicates("year", keep="last").set_index("year").pct.sort_index()  # rows are newest-first; keep first-listed (post-redesign) row
    ly = x.index.max(); lp = x[ly]; prior_min = x.drop(ly).min(); B = lp < prior_min
    A = inc.iloc[-1] >= inc.max(); iy = inc.index[-1].year; prev_max = inc.iloc[:-1].max(); prev_year = inc.iloc[:-1].idxmax().year
    v = "SUPPORTED" if (A and B) else ("PARTIAL" if (A or B) else "REFUTED")
    rec("us_median_household_income_record_and_poverty_record_low_2025", v,
        f"Real median household income {iy}: ${inc.iloc[-1]:,.0f} ({'record' if A else 'not a record'}; previous high ${prev_max:,.0f} in {prev_year}). Official poverty {ly}: {lp:.1f}% vs previous low {prior_min:.1f}% ({int(x.drop(ly).idxmin())}) - {'record low' if B else 'not a record low'}",
        dict(income_latest=inc.iloc[-1], income_year=iy, income_prev_max=prev_max, income_prev_max_year=prev_year, income_record=bool(A),
             poverty_latest=lp, poverty_year=int(ly), poverty_prev_min=prior_min, poverty_prev_min_year=int(x.drop(ly).idxmin()), poverty_record_low=bool(B),
             poverty_2024=x.get(2024)), [f1, fx])

def b4():
    i, f1 = fred("FYOINT"); r, f2 = fred("FYFR"); i.index = i.index.year; r.index = r.index.year
    sh = (i / r * 100).dropna(); ly = sh.index.max(); s02 = sh[2002]; sl = sh[ly]
    v = "SUPPORTED" if (sl >= 22 and s02 <= 15) else ("REFUTED" if sl < 15 else "PARTIAL")
    pk = sh.loc[:2020].idxmax()
    rec("us_federal_interest_share_of_receipts_doubled_since_2002", v,
        f"Net interest / federal receipts: FY{ly} {sl:.1f}% (${i[ly]/1e6:.2f}T of ${r[ly]/1e6:.2f}T) vs FY2002 {s02:.1f}%; previous peak {sh.loc[:2020].max():.1f}% in FY{pk}",
        dict(latest_fy=int(ly), share_latest=sl, share_2002=s02, interest_latest_musd=i[ly], receipts_latest_musd=r[ly], prior_peak=sh.loc[:2020].max(), prior_peak_fy=int(pk),
             share_series_2015_on={int(k): round(v_, 2) for k, v_ in sh.loc[2015:].items()}), [f1, f2])

def b5():
    m, f1 = fred("MTSDS133FMS"); fy, f2 = fred("FYFSD")
    t12 = -m.iloc[-12:].sum(); lo, hi = m.index[-12], m.index[-1]
    v = "SUPPORTED" if 1.7e6 <= t12 <= 2.3e6 else ("REFUTED" if (t12 < 1.5e6 or t12 > 2.5e6) else "PARTIAL")
    rec("us_federal_deficit_about_2_trillion_2026", v,
        f"Federal deficit, 12 months {lo:%b-%y}..{hi:%b-%y}: ${t12/1e6:.2f}T; last full fiscal year in FRED (FY{fy.index[-1].year}): ${-fy.iloc[-1]/1e6:.2f}T",
        dict(t12_musd=t12, window=[str(lo.date()), str(hi.date())], fy_latest=int(fy.index[-1].year), fy_deficit_musd=-fy.iloc[-1]), [f1, f2])

def b6():
    d, f1 = eu("nrg_pc_205", geo_code="UK", currency="NAC", tax="X_VAT")
    def ann(band):
        x = d[d.nrg_cons == band].copy(); x["y"] = x.period.str[:4].astype(int); g = x.groupby("y").value
        return g.mean()[g.count() == 2]
    hd, f2 = eu("prc_hicp_aind", geo_code="UK"); h = hd.assign(y=hd.period.astype(int)).set_index("y").value
    gas, f3 = fred("PNGASEUUSDM"); fxr, f4 = fred("DEXUSUK")
    gbp = (gas / fxr.resample("MS").mean().reindex(gas.index)).dropna(); ga = gbp.groupby(gbp.index.year).mean()
    out = {}
    for band in ["MWH2000-19999", "MWH500-1999"]:
        p = ann(band); end = 2020 if 2020 in p.index else 2019
        real = (p[end] / h[end]) / (p[2010] / h[2010]) * 100 - 100; nom = (p[end] / p[2010] - 1) * 100
        out[band] = dict(end=end, real_pct=real, nominal_pct=nom, p2010=p[2010], pend=p[end], years=list(map(int, p.index)))
    m = out["MWH2000-19999"]; end = m["end"]; G = (ga[end] / ga[2010] - 1) * 100
    E = m["real_pct"]; v = "SUPPORTED" if (E >= 20 and G < 0) else ("REFUTED" if E <= 5 else "PARTIAL")
    rec("uk_industrial_electricity_real_price_rose_2010_2020_as_gas_fell", v,
        f"UK mid-size industrial power price (excl. VAT) 2010->{end}: {E:+.1f}% real ({m['nominal_pct']:+.1f}% nominal); smaller band {out['MWH500-1999']['real_pct']:+.1f}% real. European gas price in GBP 2010->{end}: {G:+.1f}%",
        dict(bands=out, gas_gbp_change_pct=G, gas_gbp_2010=ga[2010], gas_gbp_end=ga[end], hicp_2010=h[2010], hicp_end=h[end]), [f1, f2, f3, f4])

EU27 = "AT BE BG HR CY CZ DK EE FI FR DE EL HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split()
def b7():
    b, fb = eu("nrg_bal_peh", nrg_bal="GEP")
    b = b[b.geo_code.isin(EU27)].assign(y=lambda q: q.period.astype(int)).pivot_table(index=["geo_code", "y"], columns="siec", values="value")
    b["vre"] = (b.RA300.fillna(0) + b.get("RA410", 0).fillna(0) + b.RA420.fillna(0)) / b.TOTAL * 100
    res = {}; files = [fb]
    for tax in ["X_VAT", "I_TAX", "X_TAX"]:
        p, fp = eu("nrg_pc_205", tax=tax, currency="EUR", nrg_cons="MWH2000-19999"); files.append(fp)
        p = p[p.geo_code.isin(EU27)].assign(y=lambda q: q.period.str[:4].astype(int)).groupby(["geo_code", "y"]).value.mean()
        X = pd.concat([p.rename("price"), b.vre], axis=1).dropna().reset_index(); X = X[(X.y >= 2008) & (X.y <= 2024) & (X.price > 0)]
        X["lp"] = np.log(X.price)
        r = smf.ols("lp ~ vre + C(geo_code) + C(y)", X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(X.geo_code)[0]})
        res[tax] = dict(beta=r.params.vre, p=r.pvalues.vre, n=int(r.nobs), countries=int(X.geo_code.nunique()), pct_per_10pp=(np.exp(10 * r.params.vre) - 1) * 100)
        if tax == "X_VAT":
            de = X[X.geo_code == "DE"].set_index("y")
            res["DE"] = dict(corr=de.price.corr(de.vre), price_2010=de.price.get(2010), price_2024=de.price.get(2024), vre_2010=de.vre.get(2010), vre_2024=de.vre.get(2024),
                             price_2019=de.price.get(2019), vre_2019=de.vre.get(2019), n=len(de),
                             eu_median_price_2024=X[X.y == 2024].price.median(), de_rank_2024=int(X[X.y == 2024].price.rank(ascending=False)[X[(X.y == 2024)].geo_code == "DE"].iloc[0]),
                             n_2024=int((X.y == 2024).sum()))
    m = res["X_VAT"]; v = "SUPPORTED" if (m["beta"] > 0 and m["p"] < 0.05) else ("REFUTED" if (m["beta"] < 0 and m["p"] < 0.05) else "INCONCLUSIVE")
    de = res["DE"]
    rec("germany_eu_industrial_electricity_price_vs_wind_solar_share", v,
        f"EU27 2008-24, country+year FE: +10pp wind+solar share -> {m['pct_per_10pp']:+.1f}% industrial price excl. VAT (p={m['p']:.2f}, n={m['n']}); incl. all taxes {res['I_TAX']['pct_per_10pp']:+.1f}% (p={res['I_TAX']['p']:.2f}); excl. all taxes {res['X_TAX']['pct_per_10pp']:+.1f}% (p={res['X_TAX']['p']:.2f}). Germany 2010->2024: share {de['vre_2010']:.0f}%->{de['vre_2024']:.0f}%, price EUR{de['price_2010']:.3f}->{de['price_2024']:.3f}/kWh (rank {de['de_rank_2024']}/{de['n_2024']} in 2024)",
        res, files)

def b8():
    d, f = eu("sts_inpr_q", nace_r2="C"); d = d.pivot_table(index="period", columns="geo_code", values="value").dropna().sort_index()
    y18 = d[d.index.str.startswith("2018")].mean(); l4 = d.iloc[-4:].mean(); ch = (l4 / y18 - 1) * 100
    v = "SUPPORTED" if (ch.DE <= -8 and ch.CH >= 5) else ("REFUTED" if ch.DE >= ch.CH else "PARTIAL")
    rec("germany_vs_switzerland_industrial_production_since_2018", v,
        f"Manufacturing output, last 4 quarters ({d.index[-4]}..{d.index[-1]}) vs 2018 average: Germany {ch.DE:+.1f}%, Switzerland {ch.CH:+.1f}%",
        dict(de_change=ch.DE, ch_change=ch.CH, window=[d.index[-4], d.index[-1]], de_2018=y18.DE, ch_2018=y18.CH, de_l4=l4.DE, ch_l4=l4.CH), [f])

def b9():
    f = vint("eia_v2/electricity_retail-sales_monthly_sectorid-RES_stateid-AL-US@*.parquet"); d = pd.read_parquet(f)
    d = d.assign(date=pd.to_datetime(d.period), price=d.price.astype(float)).pivot_table(index="date", columns="stateid", values="price").dropna().sort_index()
    l, p = d.iloc[-12:], d.iloc[-24:-12]; g = (l.mean() / p.mean() - 1) * 100
    cpi, fc = fred("CPIAUCSL"); ci = (cpi.reindex(l.index).mean() / cpi.reindex(p.index).mean() - 1) * 100
    v = "SUPPORTED" if (g.AL >= g.US and g.AL > ci) else ("REFUTED" if (g.AL < g.US and l.mean().AL < l.mean().US) else "PARTIAL")
    rec("alabama_residential_electricity_prices_rising_faster_than_us", v,
        f"Residential power price, 12 months to {d.index[-1]:%b-%y} vs prior 12: Alabama {g.AL:+.1f}% (avg {l.mean().AL:.2f}c/kWh), US {g.US:+.1f}% (avg {l.mean().US:.2f}c/kWh); CPI {ci:+.1f}%",
        dict(g_al=g.AL, g_us=g.US, cpi=ci, al_level=l.mean().AL, us_level=l.mean().US, latest=str(d.index[-1].date()), cpi_window_complete=bool(cpi.reindex(l.index).notna().all())), [f, fc])

def b10():
    m, f1 = fred("MORTGAGE30US"); mm = m.resample("MS").mean(); full = mm[mm.index < pd.Timestamp(m.index[-1].year, m.index[-1].month, 1)] if m.index[-1].day < 25 else mm
    lm = full.index[-1]; rate = full.iloc[-1]; mean71 = m.mean(); A = rate <= mean71; share_above = (mm > rate).mean() * 100
    fs = vint("shiller/home_price_index@*.parquet"); s = pd.read_parquet(fs).set_index("year").real_home_price_index
    ratio = s.iloc[-1] / s.mean(); B = ratio >= 1.7
    v = "SUPPORTED" if (A and B) else ("PARTIAL" if (A or B) else "REFUTED")
    rec("us_mortgage_rates_normal_but_real_home_prices_far_above_average", v,
        f"30y mortgage {lm:%b-%y} {rate:.2f}% vs 1971-2026 average {mean71:.2f}% ({share_above:.0f}% of months were higher); latest weekly {m.iloc[-1]:.2f}% ({m.index[-1]:%d-%b}). Shiller real home prices {int(s.index[-1])}: {100*(ratio-1):+.0f}% vs 1890-{int(s.index[-1])} average",
        dict(rate_month=str(lm.date()), rate=rate, latest_weekly=m.iloc[-1], latest_week=str(m.index[-1].date()), mean_since_1971=mean71, median_since_1971=m.median(), share_months_higher=share_above,
             mean_2010_2019=m.loc["2010":"2019"].mean(), shiller_latest_year=int(s.index[-1]), shiller_ratio=ratio, rate_normal=bool(A), prices_high=bool(B)), [f1, fs])

OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
def b11():
    f = vint("imf_weo_sdmx/WEO__NGDPRPC@*.parquet"); d = pd.read_parquet(f); d["year"] = d.year.astype(int)
    d = d[d.country_iso3.isin(OECD) & d.year.isin([2014, 2024])].pivot_table(index="country_iso3", columns="year", values="value")
    fb = []
    miss = [c for c in OECD if c not in d.index or d.loc[c].isna().any()]
    if miss:
        fr = vint("imf_weo_sdmx/WEO__NGDP_R@*.parquet"); fl = vint("imf_weo_sdmx/WEO__LP@*.parquet"); fb = [fr, fl]
        R = pd.read_parquet(fr); L = pd.read_parquet(fl)
        for c in miss:
            r_ = R[R.country_iso3 == c].assign(year=lambda q: q.year.astype(int)).set_index("year").value
            l_ = L[L.country_iso3 == c].assign(year=lambda q: q.year.astype(int)).set_index("year").value
            d.loc[c, 2014] = r_[2014] / l_[2014]; d.loc[c, 2024] = r_[2024] / l_[2024]
    g = (d[2024] / d[2014] - 1) * 100; rk = int(g.rank(ascending=False)["CAN"]); n = len(g)
    v = "SUPPORTED" if (g.CAN <= 5 and rk >= 36) else ("REFUTED" if (g.CAN > 8 or rk <= 30) else "PARTIAL")
    bottom = g.sort_values().head(5).round(1).to_dict()
    rec("canada_real_gdp_per_capita_2014_2024_third_worst_oecd", v,
        f"Real GDP per person 2014->2024 (IMF WEO): Canada {g.CAN:+.1f}% total, rank {rk}/{n} in the OECD; OECD median {g.median():+.1f}%; bottom five {bottom}",
        dict(g_can=g.CAN, rank=rk, n=n, median=g.median(), bottom5=bottom, fallback_countries=miss, all=g.round(2).to_dict()), [f] + fb)

for f in [b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11]: safe(f)
(OUT / "summary.json").write_text(json.dumps(RES, indent=1, default=float))
