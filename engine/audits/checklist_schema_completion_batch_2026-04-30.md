# Checklist Schema Completion Batch - 2026-04-30

## What Changed

- Promoted 25 canonical multi-metric checklist specs from legacy/candidate shape into schema-complete `pre_registered` specs.
- Added explicit `estimator.template: multi_metric_checklist` and falsification rules without changing canonical metric lists, metric thresholds, windows, or count rules.
- Spec commits: `c664158 pre-register banking crisis checklist specs`; `8fb901f pre-register remaining checklist specs`.
- Post-commit reruns were executed with `scripts/run_multi_metric_checklist.py <hypothesis_id> --force`.
- Added `replication.py` wrappers to every refreshed run directory.

## Verdicts

- `INCONCLUSIVE_PENDING_DATA`: 24
- `REFUTED`: 1

## Metric Resolution

- Total metric rows: 126
- MET: 28
- NOT_MET: 12
- PENDING_DATA: 53
- PENDING_EVAL: 33

## Per-Hypothesis Result

| hypothesis_id | verdict | MET | NOT_MET | PENDING_DATA | PENDING_EVAL | total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `banking_crisis_2008_gfc_canonical_multimetric` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 1 | 6 | 7 |
| `banking_crisis_argentina_2001_corralito_canonical` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 2 | 1 | 6 |
| `banking_crisis_asian_financial_crisis_1997_panel` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 2 | 1 | 5 |
| `banking_crisis_brazil_1999_real_devaluation` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 1 | 1 | 4 |
| `banking_crisis_brazil_proer_1995_1997` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 3 | 1 | 4 |
| `banking_crisis_china_2015_2020_panel` | `INCONCLUSIVE_PENDING_DATA` | 0 | 1 | 2 | 1 | 4 |
| `banking_crisis_cyprus_2013_bailin` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 2 | 0 | 5 |
| `banking_crisis_greece_2010_2018_doom_loop` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 2 | 2 | 6 |
| `banking_crisis_iceland_2008_canonical_multimetric` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 1 | 2 | 6 |
| `banking_crisis_ireland_2008_property_bust` | `INCONCLUSIVE_PENDING_DATA` | 3 | 0 | 1 | 1 | 5 |
| `banking_crisis_italy_2016_2017_mps` | `INCONCLUSIVE_PENDING_DATA` | 1 | 0 | 2 | 1 | 4 |
| `banking_crisis_japan_1990_lost_decade` | `INCONCLUSIVE_PENDING_DATA` | 0 | 1 | 4 | 0 | 5 |
| `banking_crisis_latvia_2008_parex` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 2 | 0 | 5 |
| `banking_crisis_lebanon_2019_2024_collapse` | `INCONCLUSIVE_PENDING_DATA` | 0 | 1 | 3 | 2 | 6 |
| `banking_crisis_mexico_tequila_1994_canonical` | `INCONCLUSIVE_PENDING_DATA` | 0 | 1 | 2 | 2 | 5 |
| `banking_crisis_nordic_1991_1993_panel` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 3 | 0 | 5 |
| `banking_crisis_russia_1998_default_canonical` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 2 | 1 | 5 |
| `banking_crisis_south_africa_african_bank_2014` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 3 | 1 | 4 |
| `banking_crisis_spain_2012_cajas_restructuring` | `INCONCLUSIVE_PENDING_DATA` | 3 | 0 | 1 | 1 | 5 |
| `banking_crisis_turkey_2001_canonical` | `INCONCLUSIVE_PENDING_DATA` | 1 | 0 | 2 | 2 | 5 |
| `banking_crisis_us_2023_svb_signature` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 3 | 2 | 5 |
| `banking_crisis_us_sl_crisis_1986_1995` | `INCONCLUSIVE_PENDING_DATA` | 0 | 1 | 3 | 1 | 5 |
| `banking_crisis_vietnam_2012_2015_restructuring` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 2 | 2 | 4 |
| `fiscal_dominance_japan_debt_non_crisis` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 3 | 2 | 5 |
| `mena_lebanon_currency_collapse_real_economy_2019_2024` | `REFUTED` | 2 | 3 | 1 | 0 | 6 |

## Top Data Gaps

| blocker | metrics |
| --- | ---: |
| `owid:systemic-banking-crises` | 11 |
| `jst:hpnom` | 2 |
| `Non-tidy (needs custom parser): bis:WS_SPP` | 2 |
| `imf:ARG_DEFAULT_2001` | 1 |
| `imf:ARG_CFM_CORRALITO_2001` | 1 |
| `imf:SBA_PROGRAMMES_1997_1998` | 1 |
| `imf:SBA_BRA_1998` | 1 |
| `imf:BRA_PROER_1995` | 1 |
| `imf:BRA_BANK_INTERVENTIONS_1995_1997` | 1 |
| `fred:CHNSCITRD` | 1 |
| `fred:SHCOMP` | 1 |
| `imf:ESM_CYP_2013` | 1 |
| `imf:CYP_BAILIN_2013` | 1 |
| `imf:EFF_GRC_2012` | 1 |
| `imf:GRC_CFM_2015` | 1 |
| `imf:SBA_ICL_2008` | 1 |
| `imf:EFF_IRL_2010` | 1 |
| `ecb:MPS_PRECAUTIONARY_RECAP_2017` | 1 |
| `ecb:VENETO_BANKS_RESOLUTION_2017` | 1 |
| `jst:eq_tr` | 1 |
| `Non-tidy (needs custom parser): fred:NIKKEI225` | 1 |
| `No JPN observations in window 1998-2003` | 1 |
| `imf:SBA_LVA_2008` | 1 |
| `imf:LVA_PAREX_2008` | 1 |
| `imf:LBN_DEFAULT_2020` | 1 |
| `imf:LBN_CFM_2019` | 1 |
| `No LBN observations in window 2019-2023` | 1 |
| `imf:SBA_MEX_1995` | 1 |
| `No NOR observations in window 1985-1990` | 1 |
| `imf:RUS_DEFAULT_1998` | 1 |
| `imf:ZAF_AFRICAN_BANK_2014` | 1 |
| `imf:ZAF_GBBB_2014` | 1 |
| `imf:ESM_ESP_2012` | 1 |
| `imf:SBA_TUR_2001` | 1 |
| `fred:SVB_SIGNATURE_FAILURE_2023` | 1 |
| `fred:BTFP_2023` | 1 |
| `Non-tidy (needs custom parser): fred:H41RESPPALDKNWW` | 1 |
| `fred:WILLREITPR` | 1 |
| `fred:DJUSBK` | 1 |
| `fred:BKFTTLA01USA661N` | 1 |
| `Non-tidy (needs custom parser): fred:USNUM` | 1 |
| `fred:RTC_FIRREA_1989` | 1 |
| `imf:VNM_VAMC_2013` | 1 |
| `imf:VNM_BANK_TAKEOVER_2015` | 1 |
| `imf:WEO_GGXWDG_NGDP` | 1 |
| `oecd:OECD.SDD.STES` | 1 |
| `DSD_KEI@DF_KEI` | 1 |
| `4.0` | 1 |
| `boj:policy_governance_record` | 1 |
| `academic:bof_independence_index` | 1 |

## Top Evaluator Gaps

| evaluator gap | metrics |
| --- | ---: |
| count-based threshold requires event log; data not sufficient to auto-count | 14 |
| threshold expression unparseable by regex | 7 |
| Non-tidy (needs custom parser): bis:WS_SPP | 4 |
| cross-country gap/ratio requires dedicated cross-country evaluator; data present | 3 |
| Non-tidy (needs custom parser): fred:DPSACBW027SBOG | 1 |
| Non-tidy (needs custom parser): fred:GDPC1 | 1 |
| Non-tidy (needs custom parser): bis:WS_SPP, fred:USSTHPI | 1 |
| Non-tidy (needs custom parser): fred:JPNCPIALLMINMEI | 1 |
| Non-tidy (needs custom parser): bis:WS_EER | 1 |

## Immediate Follow-Up

- Highest data leverage is still event coding: Laeven-Valencia systemic banking crises, IMF program/default/bailout/bail-in events, named bank interventions, and crisis-resolution facilities.
- Highest evaluator leverage is parser support for count/consecutive-year/threshold prose and custom tidy adapters for FRED/BIS/OECD wide or SDMX-shaped vintages.
- The strict runnability gate should now have zero `LEGACY_SCHEMA` and zero `NEEDS_TEMPLATE` blockers after `scripts/audit_runnability.py --strict` refreshes the derived report.
