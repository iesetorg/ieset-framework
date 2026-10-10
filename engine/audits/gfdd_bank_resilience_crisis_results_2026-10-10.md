# GFDD bank resilience and later systemic-crisis onset: frozen results

Registration `46fa6022ad5dd9d0c1128b70e73f8612f98aa628`; eight distinct source locks, from `293173ee9b4be123ed32811851800de7d392b9de` through `dff98b635fdc27e2a802078206d73e4961677efb`.

| Signal | Verdict | At-risk rows / countries | Events / countries | Beta per +1 SD | Raw p | Holm p | Gate failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Bank Z-score | PARTIAL | 235 / 88 | 10 / 10 | +0.043027 | 0.2776 | 1 | none |
| Bank nonperforming loans to gross loans | INCONCLUSIVE | 123 / 49 | 8 / 8 | — | — | 1 | min_valid_countries, min_future_crisis_windows |
| Bank capital to total assets | INCONCLUSIVE | 111 / 46 | 6 / 6 | — | — | 1 | min_valid_rows, min_valid_countries, min_future_crisis_windows, min_future_crisis_countries |
| Bank credit to bank deposits | PARTIAL | 333 / 117 | 11 / 11 | +0.061192 | 0.30336 | 1 | none |
| Bank regulatory capital to risk-weighted assets | INCONCLUSIVE | 128 / 50 | 8 / 8 | — | — | 1 | min_future_crisis_windows |
| Liquid assets to deposits and short-term funding | INCONCLUSIVE | 233 / 86 | 10 / 10 | — | — | 1 | top_country_indicator_concentration |
| Provisions to nonperforming loans | INCONCLUSIVE | 105 / 44 | 6 / 6 | — | — | 1 | min_valid_rows, min_valid_countries, min_future_crisis_windows, min_future_crisis_countries |
| Bank cost to income ratio | INCONCLUSIVE | 216 / 81 | 10 / 10 | — | — | 1 | top_one_percent_indicator_concentration, top_country_indicator_concentration |

The eight indicators share outcome and countries; Holm adjusts the frozen family only. Baseline data are observational signals, not bank-regulation treatments. GFDD raw parquet hashes are pinned but no tracked GFDD fetch manifest exists. No causal, policy, school, position or featured credit.
