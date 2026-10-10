# Source-locked remittance forward family audit

## Chronology and custody

- Original scientific registration: `32c4cee26edc73c1bae87d23963d90d81a4a48af`. The repository-wide schema check passed **6,317** specifications before selected values or null masks were first opened. The thresholds, estimands, periods, source paths, and hashes in that registration were never changed.
- Replacement metadata-only source lock: `da47dbe1ddcebbe0b4241c6d56dd19eb9b780988`. It pins the same four WDI source hashes, selected country/year key hashes, and 216-economy ISO3/XKX roster. An earlier local-only lock contained an unused workstation-root field. This replacement omits only that field. **This administrative path redaction was made after the first result had been observed; the rerun is not a new blind discovery.** The earlier lock is superseded and must not be published.
- Replacement runner: `63409e33034925606dff35920f7dbd0091830ffd`. The numerical estimator is unchanged; it points to the replacement lock and checks first path additions without following unrelated similar files. The registration and replacement lock are strict ancestors of result commit `dd45a2c3bda896e8e936883d4cb4d6940a1a8d64`.
- Both cases replayed byte for byte across all nine standard run artifacts. Their diagnostics, coefficient Parquet, chart data, metric Parquet, and result cards are byte-identical to the earlier local-only results. A separate NumPy least-squares and HC3 sandwich calculation matched coefficients and standard errors within `1e-9`.

## Frozen family outcomes

| New case | Complete economies | Exposure spread | Primary estimate per 10-point remittance-share rise | Gate and verdict | Public tier |
| --- | ---: | --- | --- | --- | --- |
| `wdi_remittance_pre2015_forward_current_account_v2` | 160/216 | 47 at >=5% GDP; IQR 5.799 pp | beta +0.203927 current-account/GDP pp; HC3 SE 1.523418; two-sided p 0.893685 | All floors pass, including influence 0.192711 <=0.20 and 160/160 leave-one-out fits. **PARTIAL** under the frozen beta >=0.5 and Bonferroni p <=0.025 rule. | Calibration, visible |
| `wdi_remittance_pre2015_forward_private_consumption_v2` | 127/216 | 35 at >=5% GDP; IQR 5.096 pp | beta +0.174862 private-consumption growth pp; HC3 SE 0.570767; p 0.759846 | Influence 0.235911 exceeds the frozen 0.20 ceiling. **INCONCLUSIVE**, even though the model can be fitted. | Archive, hidden |

The endpoints differ economically but share exposure, source family, timing, and candidate roster. They count as **one independent evidence family**, with a two-test correction. This replacement adds **one** public calibration case relative to the pre-family baseline, moving the local evidence-tier count from **576 to 577** visible cases. It adds zero featured, causal, policy, school, or position credit. Neither older remittance record is relabelled.

## Reproduction and limits

From a checkout with the four pinned local vintages, run `python3 scripts/run_wdi_remittance_pre2015_forward_2020_2023_family.py --replay --source-root <SOURCE_ROOT>`. The sources are ignored local Parquet evidence and are verified by SHA-256 before values are read. The results describe baseline-adjusted forecasts; migration, global shocks, income, measurement, and remittances can change together. No policy intervention is identified. The consumption influence failure remains a no-go under the frozen gate.
