# OECD top PIT and later growth: temporal holdout registration

**Registration state:** design and source-key roster only. The selected OECD top-PIT, WDI GDP and trade **values and null masks have not been opened in this branch**. No coefficient, confidence interval, verdict, or run artifact exists. The prior OECD top-PIT/Gini study disclosed an out-of-range France 2013 rate; the frozen [0,100] validity rule handles that value without replacement. The old `top_marginal_rate_growth_tradeoff` PARTIAL result (65 rows, five countries, p=0.312) is known.

## Lineage and independence

The first old run and spec were added at `e8f99a82cd6c6efec2e4fab8b3fc7da10d3a3155`. Its spec fixed 1945–1980. That commit's `scripts/run_panel_fe.py` applied `filter_sample` to the explicit period before fitting; its saved diagnostic reports 65 rows and five countries. The new treatment years 2000–2016 and GDP endpoint years 1997–2019 are separated from that old fitted period. Other IESET top-PIT studies are visible, so this is only a holdout relative to the named old run, not globally unseen evidence. The old high-70-percent/Laffer claim cannot be inherited by a modern OECD rate panel.

## Fixed contract

- One primary test, `oecd_top_pit_forward_growth_temporal_holdout_v2`, in a family of one. No alternate endpoint, treatment, geography, lag, or source search.
- The exact roster `data/pinned_evidence/oecd_top_pit_forward_growth_temporal_holdout_v2_key_roster.csv` has 646 keys in 38 OECD countries at t=2000–2016, sorted by year then ISO3, SHA-256 `48caf338dfbe15839a3bd185cb570823ef9253be45d122b4d97847e12c2c430e`. This is an **upper bound** from country/year columns only; a key does not prove a usable value.
- Outcome: annual percentage-point log growth of WDI constant-2015-dollar GDP per person from exact t to t+3, divided by three. Treatment: OECD top statutory personal income-tax percentage rate at t divided by ten. Controls: log GDP per person at t, exact t-3 to t annualized log growth, trade share at t; country and treatment-year effects.
- All three GDP levels must be finite and positive, tax finite and in [0,100], and trade finite and nonnegative. No missing-value fills, interpolation, substitutions, capping, or winsorization. Keep countries with at least ten complete years.
- Estimator gate: at least 450 complete country-years, 30 countries, and 15 countries whose retained within-country top-rate range is at least five points; full-rank design, finite positive country-cluster CR1 uncertainty. Residualize tax exposure on all other regressors; squared residualized exposure may have at most 20% in the top 1% of rows, 20% in one country, and 25% in one year.
- Main threshold: a two-sided 99.5% Student-t(G−1) interval for annualized growth percentage points per +10 top-rate points. **SUPPORTED** only if its lower bound exceeds −0.3; **REFUTED** only if its upper bound is below −0.3; otherwise **PARTIAL**. A decisive label also requires every leave-one-country-out coefficient to stay on the same side of −0.3. Any custody/sample/influence/inference failure is **INCONCLUSIVE**. One-test alpha 0.005 does not correct the entire visible archive.
- Public status, if any, is descriptive calibration only; `school_score_eligible=false`, `school_score_credit=0`, `policy_score_eligible=false`, `policy_score_credit=0`, `causal_credit=0`, `featured_eligible=false`. No links to schools or policies.

## Source custody and semantics

The source files and whole-fetch manifests are hash-pinned in the YAML and runner. The OECD series is the [top statutory personal income-tax rate at the earnings threshold](https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.CTP.TPS&df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_TAX_PIT%40DF_PIT_TOP_EARN_THRESH&df%5Bvs%5D=1.0); it is not an average effective rate or an all-income tax measure. The GDP outcome is [World Bank `NY.GDP.PCAP.KD`](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/NY.GDP.PCAP.KD), constant 2015 dollars per person. Source acquisition hashes: OECD PIT `b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151`; WDI GDP `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f`; WDI trade `4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1`.

The next commit must add the source lock without selected values. Only after that commit may the runner read treatment, GDP, trade values and null masks, fit the frozen model, and create an evidence packet. This registration and runner must remain byte-identical to their first-addition commit.
