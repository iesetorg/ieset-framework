"""Batch 2 (2026-10-09): generate X-sourced pre-registered specs + steelmen, then freeze SHA256 ledger.
Run from repo root:  python prereg/x_sourced_2026-10-09_batch2/scripts/make_specs.py
No data is fetched or read by this script."""
import json, yaml, pathlib, hashlib, datetime, jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]
BATCH = pathlib.Path(__file__).resolve().parents[1]
schema = json.load(open(ROOT / "schemas/hypothesis.schema.json"))
DISC = ("Drafted 2026-10-09 from a high-engagement X post (source URL in source_provenance). The figures quoted in the post "
        "were seen before drafting. No IESET data for this test was fetched or inspected before this spec was frozen in "
        "prereg/x_sourced_2026-10-09_batch2/PREREG_LEDGER.json and committed to git; the run directory is added in a later commit. "
        "Thresholds chosen by the drafting agent and not reviewed by a second analyst.")
CONF = "Author holds no positions related to this claim. Engine house prior is market-liberal; disclosed."
H = []
def h(hid, topic, claim, ev, countries, period, ts, outcomes, est, rule, test, threshold, prior, dims, policy, tweets, direction, steel, notes=""):
    H.append((dict(hypothesis_id=hid, version=1, status="pre_registered", topic=topic, claim=claim, claim_direction=direction,
      evidence_type=ev, sample=dict(countries=countries, period=period, temporal_structure=ts),
      variables=dict(outcome=outcomes), estimator=dict(template=est),
      falsification=dict(rule=rule, test=test, threshold=threshold), prior_confidence=prior,
      disclosure=DISC, conflict_disclosure=CONF, steelman=f"hypotheses/steelman/{hid}.md",
      scope=dict(period=period, countries=countries, outcome_dim=dims, policy_family=policy),
      source_provenance={"archive_refs": tweets, "mined_at": "2026-10-09", "mined_by_model": "IESET research agent (X search)"},
      notes=notes or "X-sourced batch 2 (2026-10-09). Runner: prereg/x_sourced_2026-10-09_batch2/scripts/run_batch2.py"), steel))
V = lambda n, s, t="level": dict(name=n, source=s, transformation=t)

h("us_personal_saving_rate_fell_since_jan_2025", "fiscal",
  "Since January 2025 the US personal saving rate has fallen from about 5.7% to about 4.1%, the lowest since 2022, while real wages have been falling: households are drawing down savings to keep up with prices.",
  "descriptive", ["USA"], [2022, 2026], "time_series",
  [V("personal_saving_rate", "fred:PSAVERT", "percent, SAAR, monthly"), V("avg_hourly_earnings", "fred:CES0500000003", "deflated by fred:CPIAUCSL")],
  "descriptive",
  "Let d = PSAVERT(latest) - PSAVERT(2025-01). Let low = PSAVERT(latest) < min(PSAVERT 2023-01..2024-12). Let rw = real AHE (CES0500000003/CPIAUCSL) latest common month vs 6 months earlier. SUPPORTED if d <= -1.0pp AND low AND rw < 0. REFUTED if d >= 0. PARTIAL otherwise. Current vintage as fetched on run date.",
  "endpoint_change_checklist", "d<=-1.0 & latest<min(2023-24) & real_AHE_6m<0", 0.6, ["employment_labour"], ["fiscal_policy", "trade_policy"],
  ["https://x.com/SteveRattner/status/2107916376459579534"], "-",
  "Saving-rate levels are heavily revised at annual NIPA updates, and a falling saving rate can reflect rising asset wealth (wealth effect) rather than distress. Real average hourly earnings is a composition-sensitive series. The post attributes the fall to tariffs and war; this test checks only the facts, not the cause.")

h("us_real_disposable_income_growth_by_presidential_term", "distribution",
  "Real after-tax (disposable) household income per person grew about 3.9%/yr in Trump's first term, fell about 1.2%/yr under Biden, and has grown about 3.1%/yr in Trump's second term.",
  "descriptive", ["USA"], [2016, 2026], "time_series",
  [V("real_dpi_per_capita", "fred:A229RX0", "chained 2017 USD, monthly SAAR")],
  "descriptive",
  "Primary (annual averages, less sensitive to stimulus-month endpoints): T45 = CAGR 2016avg->2020avg; Biden = CAGR 2020avg->2024avg; T47 = growth from 2024avg to mean of latest 12 months, annualised over the gap between period midpoints. SUPPORTED if Biden < 0 AND T45 > Biden AND T47 > Biden AND each of T45, Biden, T47 is within +/-1.0pp of the claimed 3.9, -1.2, 3.1. PARTIAL if T45 > Biden AND T47 > Biden but another condition fails. REFUTED if T47 <= Biden. Secondary (reported, not decisive): point-to-point Jan-to-Jan annualised growth (Jan17->Jan21, Jan21->Jan25, Jan25->latest).",
  "term_cagr_comparison", "biden<0 & t45>biden & t47>biden & |each-claimed|<=1.0", 0.4, ["poverty_inequality"], ["fiscal_policy"],
  ["https://x.com/KanekoaTheGreat/status/2106462742848967105"], "?",
  "Term averages are dominated by things presidents do not control: the 2020-21 pandemic transfers inflate the Biden starting point and 2020 levels; the 2021-22 inflation surge was global. The comparison is descriptive and says nothing about policy causation.")

h("us_median_household_income_record_and_poverty_record_low_2025", "distribution",
  "US real median household income is at a record high and the official poverty rate (10.2%) is the lowest on record.",
  "descriptive", ["USA"], [1959, 2025], "time_series",
  [V("real_median_household_income", "fred:MEHOINUSA672N", "2025 CPI-U-RS dollars, annual"),
   V("official_poverty_rate", "us_census:hstpov2", "percent of all people, official measure, CPS ASEC Historical Table 2")],
  "descriptive",
  "A = latest-year MEHOINUSA672N is the maximum of the whole series. B = latest-year official poverty rate (all people) is strictly the lowest since 1959 (ties count as not strictly lowest; report). SUPPORTED if A and B. PARTIAL if exactly one. REFUTED if neither. Informative: latest poverty rate vs claimed 10.2%. Census table-break years (2013, 2017 redesigns) use the post-redesign row.",
  "record_checklist", "income_latest==max & poverty_latest==min", 0.55, ["poverty_inequality"], ["fiscal_policy"],
  ["https://x.com/KanekoaTheGreat/status/2106462742848967105"], "?",
  "Record highs in real median income are common in any growing economy and say little about the K-shape (distribution), which the speaker is disputing. The official poverty measure ignores taxes and transfers; the supplemental measure can move differently.")

h("us_federal_interest_share_of_receipts_doubled_since_2002", "fiscal",
  "Interest on the US national debt now takes about 25% of federal tax revenue, up from about 12% in 2002.",
  "descriptive", ["USA"], [2002, 2026], "time_series",
  [V("federal_interest_outlays_fy", "fred:FYOINT", "USD millions, fiscal year (net interest)"), V("federal_receipts_fy", "fred:FYFR", "USD millions, fiscal year")],
  "descriptive",
  "Share = FYOINT/FYFR. SUPPORTED if latest FY share >= 22% AND FY2002 share <= 15%. REFUTED if latest FY share < 15%. PARTIAL otherwise. Note: FYOINT is net interest; the post's $1.3T figure is gross interest including intragovernmental trust-fund interest, which this test does not use.",
  "ratio_endpoints", "share_latest>=0.22 & share_2002<=0.15", 0.5, ["fiscal_policy", "taxation"], ["fiscal_policy"],
  ["https://x.com/WallStreetMav/status/2106176639357116743", "https://x.com/WallStreetMav/status/2105859881337004187"], "+",
  "Interest share of revenue is a cyclical measure: it was depressed in 2002-2021 by unusually low rates, and the 1980s-90s saw comparable shares. A higher share is a fiscal-space constraint, not by itself evidence of an unsustainable path.")

h("us_federal_deficit_about_2_trillion_2026", "fiscal",
  "The US federal deficit is running at roughly $2 trillion a year.",
  "descriptive", ["USA"], [2025, 2026], "time_series",
  [V("monthly_surplus_deficit", "fred:MTSDS133FMS", "USD millions, monthly, Monthly Treasury Statement")],
  "descriptive",
  "T12 = sum of MTSDS133FMS over the latest 12 available months (deficit as a positive number). SUPPORTED if 1.7T <= T12 <= 2.3T. REFUTED if T12 < 1.5T or T12 > 2.5T. PARTIAL otherwise. Informative: latest complete fiscal year (fred:FYFSD).",
  "rolling_sum_band", "1.7e6<=T12<=2.3e6 (USD m)", 0.6, ["fiscal_policy", "taxation"], ["fiscal_policy"],
  ["https://x.com/ThomasSowell/status/2107622181223956964"], "?",
  "Monthly deficits are lumpy (timing shifts of benefit payments, tariff refunds); a 12-month window can differ from the fiscal-year figure. Roughly $2T is a loose claim, so the band is wide.")

h("uk_industrial_electricity_real_price_rose_2010_2020_as_gas_fell", "energy",
  "UK industrial electricity prices rose by about 30% in real terms between 2010 and 2020 while the wholesale price of gas fell, so the rise cannot be blamed on overseas conflicts or fuel costs.",
  "descriptive", ["GBR"], [2010, 2020], "time_series",
  [V("uk_industrial_electricity_price", "eurostat:nrg_pc_205", "GBP/kWh, band MWH2000-19999, excl. VAT and recoverable taxes, annual mean of semesters"),
   V("uk_hicp", "eurostat:prc_hicp_aind", "CP00 annual average index, deflator"),
   V("eu_gas_price", "fred:PNGASEUUSDM", "USD/MMBtu, converted to GBP with fred:DEXUSUK, annual mean")],
  "descriptive",
  "E = real (HICP-deflated) change in UK band-ID industrial price from 2010 to the last UK year available in 2019-2020 (use 2020 if present, else 2019; report which). G = change in GBP gas price 2010 to the same end year. SUPPORTED if E >= +20% AND G < 0. REFUTED if E <= +5%. PARTIAL otherwise. Robustness (reported): band IC (MWH500-1999).",
  "endpoint_change_checklist", "E>=0.20 & G<0", 0.65, ["energy"], ["energy_policy"],
  ["https://x.com/s8mb/status/2106485478820028524"], "+",
  "Policy costs (carbon price floor from 2013, renewables obligation, network charges) are the likely drivers, but some network investment would have happened anyway. Large energy-intensive users received exemptions, so band-ID prices may overstate or understate what heavy industry paid. Eurostat UK data stop after Brexit.")

h("germany_eu_industrial_electricity_price_vs_wind_solar_share", "energy",
  "Higher wind+solar shares raise industrial (not wholesale) electricity prices: across EU countries, years with a higher wind+solar share of generation have higher non-household electricity prices, with Germany the headline case.",
  "associational", ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"],
  [2008, 2024], "panel",
  [V("industrial_electricity_price", "eurostat:nrg_pc_205", "EUR/kWh, band MWH2000-19999, excl. VAT and recoverable taxes, annual mean of semesters, log"),
   V("wind_solar_share", "eurostat:nrg_bal_peh", "(wind + solar PV + solar thermal) / total gross electricity production, percent")],
  "panel_fe",
  "OLS log(price) ~ wind_solar_share + country FE + year FE, SE clustered by country, EU27 2008-2024 annual. SUPPORTED (renewables raise industrial prices) if beta > 0 AND p < 0.05. REFUTED if beta < 0 AND p < 0.05. INCONCLUSIVE otherwise. Secondary (reported, not decisive): same model for prices incl. all taxes (I_TAX) and excl. all taxes (X_TAX); Germany-only time series (n~17) descriptive correlation and 2010->2024 change in price vs share.",
  "panel_fe_beta_sign", "beta>0 & p<0.05", 0.45, ["energy", "industrial_capability"], ["energy_policy"],
  ["https://x.com/dlacalle_IA/status/2106401506521907314", "https://x.com/s8mb/status/2106485478820028524"], "+",
  "Within-country variation in share is mostly a smooth trend absorbed partly by year effects; levies that fund renewables (EEG surcharge, abolished 2022) and network expansion are the channel, but gas prices and carbon prices move the same years. Industrial users often get levy exemptions, which weakens the link. Associational only.",
  notes="User-requested test (industrial, not wholesale). dlacalle_IA post has ~108 likes (below the 200-like bar; included on user request); s8mb post is context. Runner: prereg/x_sourced_2026-10-09_batch2/scripts/run_batch2.py")

h("germany_vs_switzerland_industrial_production_since_2018", "growth",
  "Swiss industry thrives while German industrial production implodes: since 2018 Swiss manufacturing output has grown while Germany's has fallen sharply.",
  "descriptive", ["DEU", "CHE"], [2018, 2026], "time_series",
  [V("manufacturing_production_index", "eurostat:sts_inpr_q", "NACE C, volume index 2021=100, seasonally and calendar adjusted, quarterly")],
  "descriptive",
  "Change = mean of latest 4 common quarters vs 2018 mean. SUPPORTED if DEU change <= -8% AND CHE change >= +5%. REFUTED if DEU change >= CHE change. PARTIAL otherwise. Fallback if CHE missing from Eurostat: oecd production index (same rule, disclosed).",
  "two_country_change", "deu<=-0.08 & che>=0.05", 0.7, ["industrial_capability"], ["industrial_policy", "energy_policy"],
  ["https://x.com/MichaelAArouet/status/2107798442399449514"], "?",
  "Swiss manufacturing output is dominated by pharmaceuticals, which have boomed globally; German output is concentrated in energy-intensive chemicals and autos hit by the 2022 gas shock and Chinese EV competition. The post's explanation (work ethic, hours) is not tested here.")

h("alabama_residential_electricity_prices_rising_faster_than_us", "energy",
  "Alabamians face high and rising electricity prices (attributed to the data-centre build-out).",
  "descriptive", ["USA"], [2024, 2026], "time_series",
  [V("al_residential_price", "eia_v2:electricity/retail-sales", "AL, RES, cents/kWh, monthly"), V("us_residential_price", "eia_v2:electricity/retail-sales", "US, RES, cents/kWh, monthly"), V("cpi", "fred:CPIAUCSL", "y/y")],
  "descriptive",
  "gAL, gUS = percent change in mean residential price over the latest 12 months vs the prior 12 months. SUPPORTED if gAL >= gUS AND gAL > CPI inflation over the same window. REFUTED if gAL < gUS AND the AL 12-month mean level is below the US level. PARTIAL otherwise. Data-centre attribution not tested.",
  "relative_growth", "gAL>=gUS & gAL>cpi", 0.4, ["energy"], ["energy_policy"],
  ["https://x.com/DougJones/status/2107196564414636099"], "+",
  "Alabama prices are set by a regulated utility (Alabama Power) with periodic rate cases, so 12-month changes can be lumpy; residential bills also reflect high per-capita usage, so bills can be high even where per-kWh prices are not. Annual EIA state data were fetched earlier on 2026-10-09 for a batch-1 test but Alabama monthly figures were not examined.")

h("us_mortgage_rates_normal_but_real_home_prices_far_above_average", "housing",
  "US mortgage rates near 7% are within the normal historical range, while real home prices are about 90% above their long-term average since 1890.",
  "descriptive", ["USA"], [1890, 2026], "time_series",
  [V("mortgage_rate_30y", "fred:MORTGAGE30US", "weekly, percent; monthly mean"), V("real_home_price_index", "shiller:home_price_index", "Shiller Fig3-1 real home price index, annual/monthly")],
  "descriptive",
  "A = latest-month mean MORTGAGE30US <= mean of all MORTGAGE30US since 1971-04. B = latest Shiller real home price index >= 1.70 x its mean over 1890..latest. SUPPORTED if A and B. PARTIAL if exactly one. REFUTED if neither. Informative: share of months since 1971 with a rate above latest.",
  "historical_comparison_checklist", "rate<=mean_since_1971 & real_hpi>=1.7*mean_since_1890", 0.7, ["housing"], ["monetary_policy", "housing_policy"],
  ["https://x.com/nickgerli1/status/2105323344748757372"], "?",
  "The 1971-2026 rate mean is pulled up by the 1979-85 inflation era, so 'normal' depends on window; relative to the 2010s, 7% is high. Shiller's index splices different methodologies and does not adjust for quality/size, overstating long-run real price growth.")

h("canada_real_gdp_per_capita_2014_2024_third_worst_oecd", "growth",
  "Canada's real GDP per capita grew only about 3.2% in total from 2014 to 2024, third worst among the 38 OECD countries.",
  "descriptive", ["CAN"], [2014, 2024], "cross_section_with_justification",
  [V("real_gdp_per_capita", "imf_weo_sdmx:NGDPRPC", "constant national currency per person; growth 2014->2024")],
  "descriptive",
  "g_i = NGDPRPC(2024)/NGDPRPC(2014) - 1 for the 38 OECD members (IMF WEO latest release). SUPPORTED if g_CAN <= 5.0% AND Canada ranks 36th or worse of 38. REFUTED if g_CAN > 8.0% OR Canada ranks 30th or better. PARTIAL otherwise. If NGDPRPC is missing for a country, use NGDP_R/LP (disclosed).",
  "peer_rank", "g_can<=0.05 & rank>=36", 0.65, ["gdp_growth"], ["fiscal_policy", "institutional_reform"],
  ["https://x.com/MaximeBernier/status/2105653253983617134"], "-",
  "Canada's weak per-capita growth partly reflects record population growth from immigration (2022-24) and the 2015 oil-price collapse hitting a commodity exporter; neither is a direct result of government size or deficits, which the post blames.")

ok = []
for d, steel in H:
    jsonschema.validate(d, schema)
    p = ROOT / "hypotheses" / d["topic"] / f'{d["hypothesis_id"]}.yaml'
    assert not p.exists() or "--force" in __import__("sys").argv, p
    p.write_text(yaml.safe_dump(d, sort_keys=False, width=200, allow_unicode=True))
    s = ROOT / "hypotheses/steelman" / f'{d["hypothesis_id"]}.md'
    s.write_text(f"# Steelman: {d['hypothesis_id']}\n\nClaim: {d['claim']}\n\nStrongest opposing case: {steel}\n\nThis test is {d['evidence_type']}, not causal.\n\nFalsification (frozen): {d['falsification']['rule']}\n\nSource post(s): {', '.join(d['source_provenance']['archive_refs'])}\n")
    ok.append(p)
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
led = {"note": "Batch 2 freeze. Specs and this ledger are committed to git BEFORE any data for these tests is fetched or run.",
       "frozen_utc": now,
       "entries": [{"file": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "frozen_utc": now,
                    "status": "pre_registered", "source_urls": d["source_provenance"]["archive_refs"]} for p, (d, _) in zip(ok, H)]}
(BATCH / "PREREG_LEDGER.json").write_text(json.dumps(led, indent=1))
print(len(ok), "specs; ledger frozen", now)
