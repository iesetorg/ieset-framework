# Result card — italian_stagnation_decomposition_1999_2023

**Verdict:** weakened — residual_share 2.486 > threshold 0.40

Pre-registered residual-share threshold: 0.40 on the Italy-vs-peer log-GDP-pc-PPP gap.

## Coefficient summary

| Spec | Term | Estimate | SE | n_obs |
|---|---|---:|---:|---:|
| baseline | italy_dummy | +0.1385 | 0.0897 | 150 |
| full | italy_dummy | +0.3443 | 0.1345 | 138 |

Residual share: **2.486**  (threshold 0.40)

Italian log-GDP-pc-PPP cumulative change 1999-2023: +0.086 (≈+9.0%); spec stagnation stylised fact requires |change| < 0.10.

## Channels (full spec)

- reer: +0.0027 (0.0030), p=0.368
- debt_gdp: -0.0006 (0.0011), p=0.583
- gov_eff: +0.0688 (0.0532), p=0.199
- rule_of_law: +0.2672 (0.0645), p=0.000
- trade_openness: -0.0016 (0.0023), p=0.482
- log_population: +0.0250 (0.0811), p=0.759
- urbanisation: +0.0065 (0.0046), p=0.159

## Deviations from pre-registration

- WGI gov_eff + rule_of_law substitute for the spec's PMR/political-
  turnover/judicial-slowness channels.
- BIS REER (broad basket, real if available) is the euro-entry-
  overvaluation proxy.
- WDI urbanisation + log-population are demographic-style controls; 
  spec's old-age dependency / prime-age LFP not in vintages.
- Synthetic-control sub-spec deferred.
