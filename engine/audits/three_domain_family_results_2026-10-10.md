# Three-domain forward calibration — locked descriptive family

Registration `0321a985831c690cd839d99ff80708ee8c504525` preceded source lock `4483ef1f424fb945eb0504ce059421e31d07e135` and results. All three tests stay in the Bonferroni denominator: family α=0.01; n=3; two-sided p≤0.0033333333333333335. No selected values or masks were opened before source lock.

| Test | Complete / key countries | HC3 beta | Two-sided p | Verdict | Failed gates |
| --- | ---: | ---: | ---: | --- | --- |
| wgi_rule_of_law_homicide_forward_2026 | 117/119 | -0.1390610752784087 | 0.38150249054042107 | PARTIAL | none |
| faostat_tractor_stock_food_production_forward_2026 | 98/100 | -0.019237870245981732 | 0.4884571729442777 | PARTIAL | none |
| wdi_self_employment_productivity_forward_2026 | 176/215 | 0.004303814802987093 | 0.4884425284028001 | INCONCLUSIVE | max_top_country_residualized_exposure_share, min_exposure_p90_p10_spread |

The FAOSTAT tractor parquet lacks a matching tracked fetch manifest; its same-timestamp raw archive and both exact hashes are pinned, while source-derivation proof remains limited. FAOSTAT A/E/X flag counts are in diagnostics. Key rows and modelled WDI fields do not establish observed complete cases. These are distinct descriptive associations only; no causal, policy, school, position or featured credit. The local three-test correction does not repair archive-wide selection.

Exact replay: `python3 -B scripts/run_three_domain_family_2026.py --verify`.
