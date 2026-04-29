# Result card — eu_post_2021_gas_shock_industrial_output_impact

**Estimator:** differences.ATTgt  
**N obs:** 225  
**N treated:** 8  
**N controls:** 8  
**Period:** [2010, 2024]  
**Outcome:** log industrial VA per capita (constant USD)

## Overall ATT (Callaway-Sant'Anna SimpleAggregation)
- **ATT (simple): 0.0086** log points
- ATT (post 0..10 mean): 0.0086

## Event-study profile
Full event-time records in diagnostics.json. Selected rows:

| event time | ATT | 95% lower | 95% upper |
|---:|---:|---:|---:|
| -5 | 0.0017 | -0.0169 | 0.0203 |
| -4 | 0.0023 | -0.0173 | 0.0218 |
| -3 | 0.0162 | 0.0028 | 0.0296 |
| -2 | -0.0421 | -0.0733 | -0.0108 |
| -1 | 0.0050 | -0.0364 | 0.0463 |
| 0 | 0.0158 | -0.0189 | 0.0505 |
| 1 | 0.0250 | -0.0088 | 0.0588 |
| 2 | -0.0151 | -0.1176 | 0.0874 |

## Pre-trend test
- Max abs ATT in pre-window (-5..-2): 0.0421
- Pre-trend pass (zero inside all pre-period 95% CIs): **False**

## Verdict
**NOT SUPPORTED — ATT not in expected direction (expected negative, got 0.0086)**

## Falsification rule (from YAML)
Not supported if (a) the interaction of post-2021Q4 × gas-exposure is zero or
positive at p<0.10 on industrial production (should be negative), OR (b) the
effect vanishes after controlling for oil price and COVID residual, OR (c) the
synthetic-control DEU post-shock gap is within the 95th percentile of placebo
gaps. This run executes the binary EU-vs-non-EU CS-DiD piece.
