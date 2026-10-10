# Blind registration design: bounded inflation and three later macro outcomes

**Family:** `imf_inflation_macro_responses_2026_10_10`  
**Status:** package prepared before selected outcome values, null masks, and observation status were opened. It is not committed, source-locked, or run in this worktree.  
**Evidence type:** retrospective descriptive association from existing pinned files. Any valid result is a public calibration at most. Causal, policy, school, and featured credit are zero.

## Fixed hypotheses

| ID | Selected WDI outcome at t to t+3 | Registered sign | Practical absolute coefficient per bounded-inflation unit |
| --- | --- | ---: | ---: |
| `imf_inflation_real_consumption_pc_forward_2026` | log real private consumption per person | negative | 0.015 log point |
| `imf_inflation_fixed_investment_share_forward_2026` | gross fixed capital formation / GDP | negative | 0.75 percentage point |
| `imf_inflation_unemployment_forward_2026` | modeled unemployment rate | positive | 0.5 percentage point |

The exposure is `2 * [tanh(IMF WEO annual CPI inflation at t / 20) - tanh(IMF WEO annual CPI inflation at t-3 / 20)]`. One unit is roughly an inflation increase from 0 to 11 percent. The bounded transform retains high-inflation economies while preventing a handful of hyperinflation observations from dominating the raw scale. Exposure years are **1995–2016**; selected outcome years can reach **2019**, before the pandemic. The three endpoints form one fixed family with two-sided Bonferroni `p <= 0.01/3` and 99.6667% simultaneous intervals. This within-family correction does not correct the wider archive-selection history.

## Blind preflight, source custody, and roster

The exact key-only CSV contains **3,919** economy-treatment-year rows in **187** ISO economies. Every row has finite IMF inflation at t-3/t, positive status-clean WDI real GDP per person at t-3/t, and selected outcome *keys* at t-3/t/t+3 for all three outcomes. Every economy has at least eight such structural rows. Material exposure (`|x| >= 0.5`) appears as **281 accelerations in 121 economies** and **547 decelerations in 150 economies**. The top 1% of raw exposure rows account for 0.16498 of squared exposure. The roster SHA-256 is `d09808f487e272d30ec847fca348bd9d0c1dc10b30f6a7fb71593363b311ca3d`.

A source-role scan of the existing hypothesis specs found zero previous records with IMF or WDI CPI as treatment and any of these three exact WDI outcome series as outcome; this is a spec-inventory check, not a claim of archive-wide independent evidence.

Only the following projections were used before registration: source schemas; IMF `country_iso3, year, value, weo_flow`; WDI GDP-per-person `country_iso3, indicator_id, year, value, obs_status` as a prespecified control; and selected WDI outcome `country_iso3, indicator_id, year` **only**. No selected outcome value, null mask, observation status, derived change, coefficient, or exact directed-pair result snippet was read. WDI indicator files contain broad structural year grids, so the 3,919 rows are **not** a complete-case claim.

| Role | Exact vintage | SHA-256 | Tracked provenance |
| --- | --- | --- | --- |
| Treatment | `imf_weo_sdmx/WEO__PCPIPCH@2026-10-09T121600Z.parquet` | `89564e357988848ac8801d946f958c4dcef37881bf35ca77d4c03c225caa0568` | existing narrow `data/source_locks/cepal_imf_inflation_next_year_national_poverty_panel.yaml`, SHA `e93cb599cfc40c042a7b0cc7cac57642f0445318d97ef315bda9176d416fdc6e` |
| GDP-per-person control | `world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `fetch_run_2026-05-05T200056Z.yaml` |
| Consumption outcome | `world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet` | `e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe` | `fetch_run_2026-05-05T200056Z.yaml` |
| Investment outcome | `world_bank_wdi/NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet` | `fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21` | `fetch_run_2026-05-05T203305Z.yaml` |
| Unemployment outcome | `world_bank_wdi/SL.UEM.TOTL.ZS@2026-05-05T200521Z.parquet` | `dfb2bae82f8ae7d95de21605e2d8c57f835cc7be4eeb53d58f8362da0b9e41c9` | `fetch_run_2026-05-05T200618Z.yaml` |

The IMF source was already used in a different CEPAL national-poverty design. Its original broad fetch manifest includes unrelated local absolute paths and is absent from this isolated branch; the tracked narrow prior lock pins the exact IMF entry without copying that broad manifest. The IMF pre-2017 exposures are historical actual years, while 2017–2019 outcomes come from WDI. This is not a new future-data holdout.

## Frozen method and failure rules

For each outcome, require finite selected t-3/t/t+3 values and blank WDI observation status at all three years. Consumption must be strictly positive and is logged; investment share must be nonnegative with no upper trim; unemployment must lie in [0,100]. Drop a selected triple only by these rules, then keep economies with at least eight complete rows. The same country/year fixed-effects OLS uses bounded exposure, prior bounded inflation level, baseline outcome, prior outcome change, log real GDP per person at t, and prior three-year log GDP-per-person change. Use CR1 country-cluster covariance with finite-sample correction `G/(G-1)*(N-1)/(N-K)` and two-sided Student t with `G-1` degrees of freedom.

Each endpoint is **INCONCLUSIVE** if any exact-source/chronology or model gate fails: fewer than 1,200 complete rows, fewer than 90 economies, fewer than 15 treatment years, fewer than 75 material accelerations or decelerations, fewer than 45 economies on either material side, rank deficiency, nonfinite/zero cluster uncertainty, or residualized exposure concentration above 25% in the top 1% of rows, 15% in one economy, or 18% in one treatment year. **SUPPORTED** requires the registered sign, its practical magnitude, and `p <= 0.01/3`; the symmetric opposite sign is **REFUTED**. Every other method-valid estimate is **PARTIAL**. No measured value can be used to revise a frozen threshold, endpoint, country, lag, or estimator.

Inflation and later macro outcomes can share demand, exchange-rate, commodity, fiscal, and monetary shocks. WDI unemployment is modeled and may carry method changes; investment share is not investment productivity; mean private consumption says nothing about distribution. Neither lagging nor fixed effects identifies a policy effect.

## Chronology still required

Add the three specs, three steelmen, this design audit, CSV roster, runner, and synthetic tests in **one preregistration commit**. Then run only the runner's `--lock`, inspect the narrow JSON for local paths, and commit the lock separately. Only then may `--run` open the selected outcome measurements. Archive an INCONCLUSIVE result without changing its frozen rule, and exactly replay any completed run packet.
