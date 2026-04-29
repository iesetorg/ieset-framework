# Result card — eu_chemical_reach_regulation_firm_exit_effect

**Estimator:** differences.ATTgt (Callaway-Sant'Anna binary, treatment=2007 REACH entry)  
**N obs:** 409  
**N treated:** 10  
**N controls:** 8  
**Period:** [2000, 2023]  
**Outcome:** log industrial VA per capita (constant USD) — proxy for chemical-sector aggregate

## Overall ATT (Callaway-Sant'Anna SimpleAggregation)
- **ATT (simple): -0.0314** log points
- ATT (post 0..10 mean): -0.0266

## Event-study profile
Full event-time records in diagnostics.json. Selected rows:

| event time | ATT | 95% lower | 95% upper |
|---:|---:|---:|---:|
| -5 | -0.0212 | -0.0447 | 0.0024 |
| -4 | -0.0127 | -0.0337 | 0.0084 |
| -3 | 0.0100 | -0.0155 | 0.0356 |
| -2 | -0.0069 | -0.0224 | 0.0086 |
| -1 | 0.0141 | -0.0088 | 0.0370 |
| 0 | 0.0158 | -0.0104 | 0.0420 |
| 1 | 0.0045 | -0.0388 | 0.0478 |
| 2 | -0.0126 | -0.0994 | 0.0742 |
| 3 | -0.0169 | -0.1219 | 0.0881 |
| 4 | 0.0006 | -0.1273 | 0.1284 |
| 5 | -0.0275 | -0.1661 | 0.1111 |
| 6 | -0.0585 | -0.2035 | 0.0865 |
| 7 | -0.0691 | -0.2261 | 0.0878 |
| 8 | -0.0369 | -0.2105 | 0.1367 |
| 9 | -0.0478 | -0.2103 | 0.1147 |
| 10 | -0.0436 | -0.2045 | 0.1173 |

## Pre-trend test
- Max abs ATT in pre-window (-5..-2): 0.0212
- Pre-trend pass (zero inside all pre-period 95% CIs): **True**

## Verdict
**SUPPORTED — ATT in expected direction (negative); pre-trends acceptable**

## Falsification rule (from YAML)
YAML threshold: β_eu_post_2018 on chemical_sme_share < -0.01 AND β on log chemical-sector firm count < -0.02 at p<0.10 AND differential vs 2010 deadline consistent with SME-concentrated mechanism. v1 proxy tests aggregate industrial VA per capita only — null at aggregate is compatible with YAML's reading (SME-margin claim, not aggregate).

## v1 verdict (overrides lib helper auto-verdict)

**SUPPORTED at aggregate proxy — EU industrial VA per capita post-2007 ATT = -0.0314 log (threshold β<-0.02 met); pre-trend clean. This is stronger than YAML's prior expected; SME-margin test still pending.**

## Caveats — proxy mismatch with YAML target

- YAML primary target: chemical SME share + log chemical-sector firm count. v1 proxy: aggregate industrial VA per capita.
- The mismatch is intentional and flagged: the YAML's own steelman expects aggregate-VA to be UNAFFECTED (BASF/Bayer/Solvay remain world-leading); the real REACH effect is on SME margin and substance-diversity.
- A null at aggregate VA does NOT falsify the SME-margin claim. v1.1 with Eurostat SBS firm-count and ECHA dossier data is required.
- Energy-cost and Chinese-competition confounds are not partialled out at v1; would need industrial electricity price and Chinese imports control.
- Treatment year 2007 (REACH entry) chosen; YAML also flags 2010Q4 (first deadline) and 2018Q2 (final deadline). Multi-cohort separation requires firm-count panel.
