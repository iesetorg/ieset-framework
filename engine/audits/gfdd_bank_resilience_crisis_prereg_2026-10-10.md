# Prospective GFDD bank resilience → later systemic crisis

This is one correlated eight-cell descriptive research family. Seven indicators are the complete frozen GFDD Stability topic SI.01–SI.07; the eighth is bank cost-to-income EI.07, an explicit operating-efficiency stress signal. Existing IESET credit-boom and macro-warning claims are separate; each cell conditions on the prior private-credit level and five-year change.

## Key-only freeze

Each cell has 636 key rows across 212 ISO3 countries at 2000, 2005 and 2010. The wide GFDD data has a full country×indicator×year grid, so this roster is only an upper bound. Before this registration, only file hashes, schema/indicator metadata, country/series labels and year-column names were read. No selected numeric value, null mask, future crisis flag or estimate was opened.

All eight hypotheses, steelmen, this plan, the runner and the 5,088-row roster are committed together. Each source lock is a later separate commit. The measured run must follow every lock and retain all eight cells, including design failures. The source hash, five-year windows, model, signs, bounds, complete-case floor, influence gates, five hash folds and Holm family size are fixed in the runner and specifications.

## Outcome and inference

At each anchor t, require the GFDD systemic-banking-crisis dummy to be 0 at baseline and present as 0/1 for every year t+1 through t+5; an onset is a 0-to-1 transition in that six-year sequence. The fixed floor is at least 10 onset windows across at least 8 countries per cell. Use country/anchor fixed-effect linear probability models with baseline private-credit level, prior five-year credit change and baseline real income. Country-cluster CR1 uncertainty, two-sided Student t(G−1), Holm alpha .05 across eight cells; unavailable or inconclusive cells enter Holm with p=1. Registered directional effect size is 0.03 probability points per +1 predictor SD, plus four-of-five fixed country-fold signs. Failed design gates are INCONCLUSIVE.

## Custody and limits

The pinned GFDDData and GFDDSeries parquet SHA-256 hashes are exact local locks and their metadata agrees with the official World Bank GFDD indicator glossary. This older local corpus has no tracked fetch manifest, so the precise original download transaction cannot be reconstructed. WDI GDP per capita has an exact tracked fetch manifest. No raw GFDD values are published. These are descriptive early-warning signals, not prudential-policy effects; no causal, policy, school, position or featured credit.

| Cell | GFDD indicator | Registered sign |
| --- | --- | --- |
| z_score | GFDD.SI.01 Bank Z-score | negative |
| nonperforming_loans | GFDD.SI.02 Bank nonperforming loans to gross loans | positive |
| capital_assets | GFDD.SI.03 Bank capital to total assets | negative |
| credit_deposits | GFDD.SI.04 Bank credit to bank deposits | positive |
| regulatory_capital | GFDD.SI.05 Bank regulatory capital to risk-weighted assets | negative |
| liquid_assets | GFDD.SI.06 Liquid assets to deposits and short-term funding | negative |
| loan_loss_provisions | GFDD.SI.07 Provisions to nonperforming loans | negative |
| cost_income | GFDD.EI.07 Bank cost to income ratio | positive |
