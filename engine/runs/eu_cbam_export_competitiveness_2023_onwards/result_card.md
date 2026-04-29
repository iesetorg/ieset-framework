# Result card — eu_cbam_export_competitiveness_2023_onwards

**Estimator:** differences.ATTgt (Callaway-Sant'Anna binary)  
**N obs:** 180  
**N treated:** 9  
**N controls:** 9  
**Period:** [2015, 2024]  
**Outcome:** log_exp_pc

## Overall ATT (Callaway-Sant'Anna SimpleAggregation)
- **ATT (simple): -0.0215** log points
- ATT (post 0..10 mean): -0.0215

## Event-study profile
Full event-time records in diagnostics.json. Selected rows:

| event time | ATT | 95% lower | 95% upper |
|---:|---:|---:|---:|
| -5 | 0.0031 | -0.0161 | 0.0222 |
| -4 | 0.0222 | 0.0084 | 0.0360 |
| -3 | -0.0130 | -0.0707 | 0.0448 |
| -2 | 0.0380 | -0.0162 | 0.0922 |
| -1 | 0.0132 | -0.0197 | 0.0461 |
| 0 | -0.0148 | -0.0435 | 0.0139 |
| 1 | -0.0282 | -0.0731 | 0.0168 |

## Pre-trend test
- Max abs ATT in pre-window (-5..-2): 0.0380
- Pre-trend pass (zero inside all pre-period 95% CIs): **False**

## Verdict
**WEAKLY SUPPORTED — ATT in expected direction but pre-trend fails; weaken claim**

## Falsification rule (from YAML)
Not supported if (a) the EU-CBAM β is zero or positive at p<0.10, OR (b) effect vanishes after controlling for gas + ETS price, OR (c) pre-2023 placebo detects spurious divergence, OR (d) domestic CBAM-subsector production shows no contraction. Threshold: β < -0.05 log points at p<0.10. v1 uses aggregate-exports proxy.

## Secondary outcome — log industrial VA per capita

- ATT (simple) = -0.0084 log points
- Pre-trend pass: False

## v1 verdict (overrides lib helper auto-verdict)

**WEAKLY SUPPORTED — ATT = -0.0215 log but pre-trend fails; effect identification unreliable.**

## Caveats — v1 is a pre-registration

- Aggregate exports of goods+services is the coarse proxy; CBAM scope is HS-code-specific (steel, aluminium, cement, fertilisers, hydrogen, electricity).
- 2023-2024 is the *reporting* phase only (admin cost, no certificate purchase). Author prior was low for v1.
- v2 post-2026 will run with certificate-phase active and HS-level Comtrade data.
- Pre-period 2015-2022 contains COVID + gas-shock; identification rests on year-FE absorbing common shocks.
