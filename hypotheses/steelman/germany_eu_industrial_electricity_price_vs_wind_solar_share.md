# Steelman: germany_eu_industrial_electricity_price_vs_wind_solar_share

Claim: Higher wind+solar shares raise industrial (not wholesale) electricity prices: across EU countries, years with a higher wind+solar share of generation have higher non-household electricity prices, with Germany the headline case.

Strongest opposing case: Within-country variation in share is mostly a smooth trend absorbed partly by year effects; levies that fund renewables (EEG surcharge, abolished 2022) and network expansion are the channel, but gas prices and carbon prices move the same years. Industrial users often get levy exemptions, which weakens the link. Associational only.

This test is associational, not causal.

Falsification (frozen): OLS log(price) ~ wind_solar_share + country FE + year FE, SE clustered by country, EU27 2008-2024 annual. SUPPORTED (renewables raise industrial prices) if beta > 0 AND p < 0.05. REFUTED if beta < 0 AND p < 0.05. INCONCLUSIVE otherwise. Secondary (reported, not decisive): same model for prices incl. all taxes (I_TAX) and excl. all taxes (X_TAX); Germany-only time series (n~17) descriptive correlation and 2010->2024 change in price vs share.

Source post(s): https://x.com/dlacalle_IA/status/2106401506521907314, https://x.com/s8mb/status/2106485478820028524
