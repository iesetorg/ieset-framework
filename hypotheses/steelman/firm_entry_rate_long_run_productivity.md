# Steelman — Firm entry rate predicts long-run productivity growth

## Strongest version of the claim

Across OECD and emerging-market panels, higher firm-entry rates are a robust leading indicator of stronger 20-year total-factor-productivity growth, even after controlling for convergence dynamics, human-capital stocks, and capital deepening. The mechanism is Schumpeterian creative destruction: new entrants introduce superior technologies and business models, discipline incumbents, and reallocate resources toward higher-productivity uses. The claim is not that entry is the *only* growth driver, but that it is a quantitatively important and empirically detectable one, distinct from state-investment or incumbent-scale channels.

## Key evidence the claim would need

1. **Panel-FE coefficient:** A positive, significant coefficient on firm-entry rate in a two-way fixed-effects regression of forward-differenced TFP on entry rates, with standard errors clustered by country.
2. **Cross-sectional robustness:** The bivariate correlation between mean entry rate and mean TFP growth across countries is positive and significant.
3. **Horse-race dominance:** In a regression with both entry rate and state-investment share, the entry-rate coefficient is at least as precisely estimated (larger absolute t-statistic) as the state-investment coefficient.
4. **Data quality:** Firm-registration data must be administrative (not modelled), with reasonable coverage back to at least 1990 for OECD members and 2000 for emerging markets.

## Best counterarguments

1. **Reverse causation:** Fast-growing countries attract more entrepreneurs, so entry rates rise *because of* expected productivity growth, not before it.
2. **Omitted variable:** Entry rates correlate with general institutional quality (rule of law, contract enforcement, education). The panel-FE design may not fully absorb this if institutional quality evolves slowly.
3. **Measurement error:** Cross-country firm-registration data conflate high-productivity startups with low-productivity informal sole proprietors. A country with many street vendors has high "entry" but low productivity impact.
4. **State-investment complementarity:** East Asian developmental states combined low entry rates with high state-directed investment and achieved rapid TFP growth. The horse-race may falsely treat complementary channels as substitutes.

## Boundary conditions

The claim is strongest for middle-income catch-up economies where technology adoption gaps are large and incumbent rigidities are binding. It is weaker for: (i) frontier economies where most productivity growth comes from incumbent R&D (Switzerland, Germany); (ii) resource economies where entry is concentrated in non-tradable services; (iii) post-crisis episodes where entry surges reflect distress-driven churn rather than innovation.

## Relation to existing hypotheses

Directly linked to `business_dynamism_frontier_income_growth` and `austrian_kirzner_entrepreneurship_business_dynamism_decline_us_1980_2020`. Tensions with incumbent-subsidy hypotheses: if `incumbent_subsidy_market_share_persistence` finds strong negative effects of subsidies on concentration and productivity, the entry-growth channel provides the causal mechanism (subsidies block entry). Complementary to `product_market_regulation_tfp_30yr_panel`: PMR reforms are one policy lever that raises entry rates.
