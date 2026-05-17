# High-Quality Graduation Batch 3 — 2026-05-16

## Purpose

This batch focused on claim-matched threshold tests. The goal was to avoid generic pre/post or panel coefficients where the hypothesis had a sharper falsification rule.

## Repairs Applied

- Added a bespoke Japan debt-threshold evaluator to `scripts/run_descriptive.py`.
  - Tests debt/GDP crossing windows directly.
  - Checks 10y JGB yield spikes above the pre-crossing baseline.
  - Computes annual CPI YoY from the local FRED Japan CPI index.
  - For the Sargent-Wallace variant, also checks the post-100%-debt yield/CPI gates and a debt-to-yield regression through the pre-YCC window.
- Added an exact Bangladesh apparel threshold evaluator to `scripts/run_descriptive.py`.
  - Checks the two preregistered primary gates instead of relying only on the FE coefficient.
  - Gate 1: Bangladesh manufacturing value added share rises by at least 5 percentage points from 1985 to 2019.
  - Gate 2: Bangladesh real GDP-per-capita growth beats Pakistan by at least 1 percentage point per year over 2000-2019.

## Primary Results

| Hypothesis | Verdict | Key result | Interpretation |
| --- | --- | --- | --- |
| `asia_bangladesh_apparel_growth_1985_2024` | SUPPORTED | Manufacturing share +6.75pp; BGD-PAK GDP-pc growth gap +2.78pp/yr | Clears both preregistered primary gates. This supersedes the generic FE-only artifact for this hypothesis. |
| `japan_public_debt_solvency_inflation_independence` | WEAKENED | 150% and 200% debt-threshold windows clear both crisis gates; local IMF vintage does not cross 250% | Observed thresholds support the no-crisis claim, but the advertised 250% leg is not present in the local IMF debt vintage. |
| `japan_sargent_wallace_refutation_1990_2024` | WEAKENED | 100%, 150%, and 200% debt thresholds clear yield/CPI gates; debt-to-yield coefficient `-0.00026`, `p=0.977`; local IMF vintage does not cross 250% | No observed Sargent-Wallace-style breach in the local data, but the 250% threshold and machine-fetched distress-event count are not covered. |

## Japan Threshold Details

`japan_public_debt_solvency_inflation_independence`

| Debt threshold | Cross year | Debt/GDP at cross | Max 10y yield next 2y | Yield spike vs pre-cross | Max CPI YoY next 2y | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 150% | 2005 | 153.4% | 1.74% | +0.25pp | 0.25% | Pass |
| 200% | 2013 | 201.2% | 0.69% | -0.15pp | 2.76% | Pass |
| 250% | Not crossed | max local debt 228.8% | n/a | n/a | n/a | Not tested |

`japan_sargent_wallace_refutation_1990_2024`

| Debt threshold | Cross year | Debt/GDP at cross | Max 10y yield next 2y | Yield spike vs pre-cross | Max CPI YoY next 2y | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 100% | 1998 | 101.6% | 1.75% | -0.62pp | 0.65% | Pass |
| 150% | 2005 | 153.4% | 1.74% | +0.25pp | 0.25% | Pass |
| 200% | 2013 | 201.2% | 0.69% | -0.15pp | 2.76% | Pass |
| 250% | Not crossed | max local debt 228.8% | n/a | n/a | n/a | Not tested |

Additional Sargent-Wallace gate:

- Post-first-crossing max 10y JGB yield: 1.75%, below the 4% crisis gate.
- Post-first-crossing max CPI YoY: 2.76%, below the 5% crisis gate.
- Debt-to-yield regression, 1998-2015: coefficient `-0.00026`, `p=0.977`, not positive/significant.
- Caveat: CPI coverage stops in 2021 and the distress-event count is spec-coded rather than machine-fetched.

## Why These Count As Higher Quality

- Bangladesh now uses the hypothesis's own two primary thresholds, not a proxy panel coefficient.
- Japan no longer receives a misleading generic pre/post verdict.
- The local-data mismatch on Japan's claimed 250% debt threshold is explicitly surfaced instead of hidden.

## Next Best Follow-Ups

1. Acquire/verify a Japan gross-debt series that either confirms or rejects the 250% threshold claim; if the 250% claim is wrong under the canonical series, patch the specs.
2. Add a machine-readable sovereign-distress/default event vintage for Japan and the US issuer-solvency hypotheses.
3. Build the CPI-divergence derived panel for `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`.
