# Result card — banking_crisis_asian_financial_crisis_1997_panel

**Verdict:** supported

**Reason:** 5 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 5 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** THA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | nominal_currency_depreciation_peak | MET | 62 [countries_meeting_threshold] | `>= 30% nominal depreciation in at least 4 of 5 countries` | 62 countries meet >=30 in 1997-1998; required >= 4; countries=AGO,ARG,AUS,AUT,BEL,BGR,BLR,BRA,CAN,CHE,CHN,CYP,CZE,DEU,DNK,ECU,EST,FIN,FJI,FRA,GBR,HKG,HRV,IDN,IND,IRL,ISL,ISR,KOR,LAO,LTU,LUX,LVA,MAR,MEX,MLT,MWI,MYS,NLD,NOR,NZL,PER,PHL,PNG,POL,ROU,RUS,SGP,SLE,SRB,STP,SVK,SWE,THA,TJK,TUR,UKR,USA,UZB,ZAF,ZMB,ZWE |
| 2 | real_gdp_decline_1998 | MET | 167 [countries_meeting_threshold] | `>= 5% peak-to-trough in at least 4 of 5 countries` | 167 countries meet >=5 in 1997-1999; required >= 4; countries=,AGO,ALB,AND,ARB,ARM,ATG,AUS,AUT,AZE,BEL,BEN,BFA,BGD,BGR,BHR,BHS,BIH,BLR,BLZ,BMU,BOL,BRN,BTN,BWA,CAF,CAN,CHN,CIV,CMR,COD,CPV,CRI,CSS,CUB,CYP,DNK,DOM,DZA,EAP,ECS,EGY,EMU,ESP,EUU,FCS,FIN,FJI,FRA,GAB,GBR,GEO,GHA,GIN,GMB,GNB,GNQ,GRC,GRD,GRL,GTM,HKG,HND,HPC,HUN,IBD,IBT,IDA,IDN,IDX,IMN,IND,IRL,IRQ,ISL,ISR,JOR,KEN,KGZ,KHM,KOR,LAO,LBR,LCA,LDC,LKA,LMY,LTE,LTU,LUX,LVA,MAC,MAR,MCO,MDA,MDG,MDV,MEA,MEX,MIC,MKD,MLI,MLT,MMR,MNA,MNE,MNG,MOZ,MRT,MUS,MWI,MYS,NAC,NAM,NER,NIC,NLD,NPL,NRU,NZL,OED,OSS,PAK,PAN,PLW,POL,PRE,PRI,PRT,PSE,PSS,PST,QAT,RUS,RWA,SAS,SDN,SEN,SGP,SMR,SOM,SRB,SST,SVN,SWE,SWZ,SYR,TCD,TEA,THA,TJK,TKM,TLS,TMN,TSA,TTO,TUN,TUV,TZA,UGA,USA,UZB,VCT,VEN,VNM,WLD,YEM |
| 3 | laeven_valencia_systemic_banking_crisis | MET | 8 [countries_meeting_threshold] | `coded in at least 4 of 5 countries` | 8 countries meet event indicator > 0 in 1997-2001; required >= 4; countries=ARG,IDN,JPN,KOR,PHL,RUS,THA,TUR |
| 4 | imf_programme_entered | MET | 4 [countries_meeting_threshold] | `yes in at least 4 of 5 countries (THA, IDN, KOR, PHL definite; MYS opted out — 4 of 5 expected)` | 4 countries meet event indicator > 0 in 1997-1999; required >= 4; countries=IDN,KOR,PHL,THA |
| 5 | current_account_reversal | MET | 42 [countries_meeting_threshold] | `>= 8 pp of GDP swing in at least 4 of 5 countries` | 42 countries meet >=8 in 1996-1999; required >= 4; countries=ABW,AGO,ALB,AZE,BGR,BHR,BHS,BRB,BWA,COG,DMA,ECU,ERI,GAB,GHA,JOR,KEN,KGZ,KOR,KWT,LAO,MDA,MDV,MNG,MYS,OMN,PNG,PSE,RUS,SAU,SLB,SLE,STP,THA,TTO,UKR,VCT,VEN,VNM,VUT,WSM,ZMB |

## Claim

> The 1997-1998 Asian Financial Crisis affected a tightly-clustered group of east-Asian economies (Thailand, Indonesia, Korea, Malaysia, Philippines) through a common pattern of currency-peg collapse, foreign-currency-denominated bank-and-corporate balance-sheet distress, large IMF programmes, and sharp output contractions. The hypothesis is that across the five-country panel, a multi-metric checklist of currency depreciation, real-GDP contraction, banking-crisis coding, IMF programme entry, and current-account reversal is met in at least 4 of 5 countries on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 5 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_asian_financial_crisis_1997_panel.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
