# Initial state-share predicts drift reversal

**Verdict:** partial — Direction is correct (β = -0.0245) but neither the significance threshold (p = 0.8254) nor the explanatory threshold (R² = 0.002) is met. Suggestive only.

## Primary specification (ISR excluded)

- n = 25
- β (initial_share) = -0.0245 per pp of GDP (SE = 0.1097, t = -0.223, two-sided p = 0.8254)
- R² = 0.002
- Threshold: β < 0 AND p < 0.1 AND R² ≥ 0.2

## With log-GDP-pc control

- n = 25
- β (initial_share) = -0.0508 (p = 0.6585)
- β (log_init_gdp_pc) = +1.7850 (p = 0.3562)
- R² = 0.041

## Secondary spec — full sample with ISR

- n = 26
- β (initial_share) = -0.0732 (p = 0.4619)
- R² = 0.023

## Country-level data

| Country | Initial share (% GDP) | Slope/decade | Drift obs | Movements |
|---|---:|---:|---:|---:|
| KOR | 18.5 | +1.370 | 50 | 13 |
| ESP | 24.0 | -5.768 | 49 | 16 |
| JPN | 27.0 | +3.354 | 50 | 18 |
| CHE | 27.5 | +1.236 | 50 | 3 |
| GRC | 29.0 | -9.690 | 50 | 14 |
| AUS | 29.0 | +1.201 | 50 | 9 |
| USA | 29.5 | +5.065 | 50 | 29 |
| PRT | 30.0 | -8.077 | 50 | 10 |
| ITA | 37.5 | -11.046 | 50 | 25 |
| FIN | 37.5 | -6.597 | 47 | 12 |
| NZL | 37.5 | -7.599 | 50 | 11 |
| CAN | 39.5 | -7.406 | 46 | 11 |
| CZE | 42.0 | -4.773 | 33 | 8 |
| GBR | 42.5 | -0.432 | 50 | 20 |
| DEU | 43.0 | +10.239 | 50 | 20 |
| IRL | 43.0 | -0.043 | 47 | 17 |
| POL | 44.0 | -3.915 | 50 | 17 |
| FRA | 44.5 | -0.709 | 50 | 17 |
| NOR | 46.0 | -1.484 | 50 | 9 |
| AUT | 46.5 | +4.024 | 50 | 15 |
| NLD | 49.0 | -6.662 | 49 | 18 |
| HUN | 49.0 | -5.103 | 50 | 11 |
| BEL | 51.0 | -2.617 | 50 | 14 |
| DNK | 51.0 | -5.365 | 50 | 10 |
| SWE | 55.5 | -0.451 | 50 | 14 |
| ISR | 63.5 | -8.935 | 49 | 17 |

## Method

Cross-sectional OLS, n=26 liberal democracies. Outcome = per-decade
OLS slope of `statist_drift` composite from
`data/derived/country_drift.json` (same outcome construction as
`fiscal_rule_presence_dampens_statist_drift`: anchor at the first
non-zero drift observation, then OLS slope × 10).

Treatment = hand-coded 1976-1980 average general-government total
expenditure share of GDP (post-1989 transitions POL/CZE/HUN: 1995-1999,
since pre-transition socialist-bloc data is non-comparable).
Control = log GDP-pc constant 2015 USD averaged over the same window.

Primary spec excludes ISR (Israel) per the spec's own outlier flag —
the 1976-1980 share of ~63.5% GDP reflects post-Yom-Kippur-War
emergency spending and is far outside the range. Secondary spec keeps
ISR for robustness; if signs flip between specs that's reported.

## Falsification legs

- Direction correct (β < 0): **True**
- Significant at p<0.1: **False**
- R² ≥ 0.2: **False**

## Steelman live concerns

See `hypotheses/steelman/initial_state_share_predicts_drift_reversal.md`.
Particularly relevant: (i) the corpus' policy-direction coding is itself
constructed from movements that may be biased toward market-pivot framing;
(ii) the 1976-1980 starting window is long after the main post-war
expansion of the state — earlier baselines (1960s) would produce different
rankings; (iii) regression-to-the-median in coded measures can be a
Galtonian artefact rather than a substantive convergence story.

## Provenance

- `data/derived/country_drift.json` (built by `scripts/compute_country_drift.py`)
- `world_bank_wdi:NY.GDP.PCAP.KD` (latest vintage on disk)
- INITIAL_GOVT_SHARE dictionary in this script (hand-coded from spec)

