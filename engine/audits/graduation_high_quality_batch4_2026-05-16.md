# High-Quality Graduation Batch 4 — 2026-05-16

## Purpose

This batch continued the exact-gate approach from batch 3. The focus was monetary/fiscal hypotheses where the generic runners were technically producing artifacts, but not testing the actual falsification surfaces.

## Repairs Applied

- Added an exact CPI-threshold evaluator for `monetary_finance_zlb_no_inflation`.
  - Checks the registered CPI YoY >3% falsification gate in the 2008-2014 and 2020-2021 windows.
  - Uses local FRED CPI for USA and Japan.
  - Marks Eurozone CPI as a coverage caveat because the local ECB CPI source is not loaded.
- Added a USA coverage-gated evaluator for `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`.
  - Checks USA core-CPI divergence from the 2003-2007 pre-QE baseline.
  - Checks USA 5y5y inflation expectations against the ±0.75pp anchored band.
  - Computes Fed balance sheet as a share of GDP from FRED `WALCL` and `GDP`.
  - Explicitly refuses to generalize to Japan/ECB/BoE until their core-CPI and expectations gates are loaded.
- Added an exact event-count evaluator for the US issuer-solvency pair.
  - Replaces generic pre/post artifacts with a zero-event/debt-threshold shape.
  - Keeps the result at `WEAKENED` because the default/CDS/auction event gates are still spec-coded rather than machine-fetched.

## Results

| Hypothesis | Verdict | Key result | Interpretation |
| --- | --- | --- | --- |
| `monetary_finance_zlb_no_inflation` | REFUTED | USA CPI YoY breaches the 3% gate in both windows: 3.81% in 2008 and 4.68% in 2021 | The spec's own falsification rule says any CPI YoY >3% in those windows falsifies; Japan clears, Eurozone CPI is not loaded, but the USA breach is dispositive. |
| `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020` | WEAKENED | USA core-CPI divergence max is -1.09pp; USA 5y5y expectations stay inside the anchored band; Fed balance sheet reaches 29.63% of GDP in 2020 | USA subtest supports decoupling on CPI/expectations, but the cross-institution claim is not loaded and the 30%-of-GDP balance-sheet claim is just below the gate on annual averages. |
| `usd_issuer_solvency_no_default_post_1971` | WEAKENED | Coded zero qualifying events; gross federal debt/GDP crosses 100% in 2014 and peaks at 122.3% in 2020 | Correct shape, but default/CDS/auction evidence is not yet machine-readable. |
| `us_dollar_issuer_solvency_record` | WEAKENED | Same zero-event/debt-threshold result through the draft's 1971-2023 window | Replaces the previous generic pre/post artifact with a claim-matched event-count artifact. |

## Detail

### Monetary Finance ZLB CPI Gate

| Country | Window | Peak CPI YoY | Year | Gate |
| --- | --- | ---: | ---: | --- |
| USA | 2008-2014 | 3.81% | 2008 | Breach |
| USA | 2020-2021 | 4.68% | 2021 | Breach |
| JPN | 2008-2014 | 2.76% | 2014 | Pass |
| JPN | 2020-2021 | -0.03% | 2020 | Pass |

### Central-Bank Decoupling USA Subtest

- USA core-CPI baseline, 2003-2007: 2.05% YoY.
- Max absolute core-CPI divergence, 2008-2020: -1.09pp in 2010, inside the ±2pp gate.
- USA 5y5y expectation baseline, 2003-2007: 2.40%.
- Anchored band: 1.65% to 3.15%; 2008-2020 annual observations stay within it.
- Fed balance sheet max, 2008-2020: 29.63% of GDP in 2020, just below the 30% claim gate.

### US Issuer Solvency Event Count

- Qualifying event count: 0, but currently spec-coded.
- Gross federal debt/GDP crosses 100% in 2014 under the local FRED annualized vintage.
- Gross federal debt/GDP peak in loaded sample: 122.3% in 2020.
- Missing before scoreboard-grade support: machine-readable default-event registry, CDS gate, and Treasury auction-clearing gate.

## Next Best Follow-Ups

1. Load Eurozone CPI for `monetary_finance_zlb_no_inflation` so the refuted result can report all three economies.
2. Load Japan/ECB/BoE core-CPI and 5y5y expectations for `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`; this is the main blocker to full graduation.
3. Build a `sovereign_default_events` vintage covering USA/JPN issuer-solvency specs, plus optional CDS and auction-clearing panels.
