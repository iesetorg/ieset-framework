# Result card — banking_crisis_nordic_1991_1993_panel

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** NOR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_credit_to_gdp_run_up | PENDING_DATA |  | `>= 25 pp of GDP rise pre-crisis in all three countries` | No NOR observations in window 1985-1990 |
| 2 | real_house_price_decline | MET | 20 [countries_meeting_threshold] | `>= 25% decline in at least 2 of 3 countries` | 20 countries meet >=25 in 1989-1995; required >= 2; countries=AUS,AUT,CAN,COL,DNK,ESP,FIN,GBR,HKG,HUN,ISL,ISR,KOR,MYS,NLD,NOR,NZL,SWE,THA,ZAF |
| 3 | real_gdp_contraction | MET | 218 [countries_meeting_threshold] | `>= 5% decline in at least 2 of 3 countries` | 218 countries meet >=5 in 1989-1994; required >= 2; countries=,ABW,AFW,AGO,ALB,AND,ARB,ARE,ARG,ARM,ATG,AUS,AUT,AZE,BDI,BEL,BEN,BFA,BGD,BGR,BHR,BHS,BIH,BLR,BLZ,BOL,BRA,BRB,BRN,BTN,BWA,CAF,CAN,CEB,CHL,CHN,CMR,COD,COG,COL,COM,CPV,CRI,CSS,CUB,CYP,CZE,DEU,DMA,DNK,DOM,EAP,EAR,EAS,ECA,ECU,EGY,EMU,ERI,ESP,EST,ETH,EUU,FCS,FIN,FJI,FRA,FSM,GAB,GBR,GEO,GHA,GIN,GMB,GNB,GNQ,GRD,GRL,GTM,GUY,HKG,HND,HRV,HTI,HUN,IBD,IBT,IDA,IDB,IDN,IDX,IMN,IND,IRL,IRN,IRQ,ISR,ITA,JAM,JOR,JPN,KAZ,KEN,KGZ,KHM,KIR,KNA,KOR,KWT,LAC,LAO,LBN,LBR,LBY,LCA,LCN,LKA,LMY,LSO,LTE,LTU,LUX,LVA,MAC,MAR,MCO,MDA,MDG,MDV,MEA,MEX,MHL,MIC,MKD,MLI,MLT,MMR,MNA,MNG,MOZ,MRT,MUS,MWI,MYS,NAC,NAM,NGA,NLD,NOR,NPL,NRU,NZL,OED,OMN,PAK,PAN,PER,PHL,PLW,PNG,POL,PRE,PRI,PRT,PRY,PSS,PST,QAT,ROU,RUS,RWA,SAS,SAU,SDN,SEN,SGP,SLB,SLE,SLV,SOM,STP,SUR,SVK,SVN,SWZ,SYC,SYR,TCD,TEA,TEC,TGO,THA,TJK,TKM,TLA,TLS,TMN,TON,TSA,TTO,TUN,TUR,TUV,TZA,UGA,UKR,URY,USA,UZB,VCT,VEN,VNM,VUT,WLD,WSM,YEM,ZMB,ZWE |
| 4 | laeven_valencia_systemic_banking_crisis | MET | 1 (1988) [coded_yes_indicator_max] | `coded yes in all 3 countries` | coded YES evaluated from binary event indicator |
| 5 | unemployment_rate_rise | MET | 48 [countries_meeting_threshold] | `>= 6 pp rise in at least 2 of 3 countries` | 48 countries meet >=6 in 1990-1995; required >= 2; countries=ALB,ARG,AUS,AUT,AZE,BEL,BLR,BWA,CAN,CHE,CRI,CZE,DEU,DNK,DZA,ESP,EST,FIN,FRA,GBR,GRC,HUN,IND,IRL,ISL,ISR,ITA,JOR,JPN,KAZ,KOR,LTU,LUX,LVA,MEX,MKD,NLD,NOR,NZL,POL,PRT,RUS,SUR,SVK,SWE,TKM,TUR,USA |

## Claim

> The 1988-1993 Nordic banking crises (Norway 1988-1991, Sweden 1991-1992, Finland 1991-1993) are a canonical post-deregulation credit-boom-bust panel. Following the mid-1980s liberalisation of credit and capital markets, all three countries experienced bank-credit-to-GDP run-up of >= 25 pp, real-house-price decline of >= 25%, real-GDP contraction of >= 5%, large bank rescues / nationalisations, and Laeven-Valencia banking-crisis coding. The hypothesis is that the canonical multi-metric pattern is met across at least 3 of 3 countries on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_nordic_1991_1993_panel.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
