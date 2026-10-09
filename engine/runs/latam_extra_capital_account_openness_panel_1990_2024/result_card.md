# Result card — latam_extra_capital_account_openness_panel_1990_2024

**Verdict:** REFUTED — among the 10/20 declared countries with complete cases, preregistered support conjunction failed at condition(s) a, b; this is not evidence of an opposite effect

## Frozen three-part rule

- (a) FDI growth coefficient > 0 at p < 0.10: **False**; coef=0.003447426126770599, p=0.6038401785522884
- (b) FDI × WGI growth interaction > 0: **False**; coef=-0.004614834273367392
- (c) FDI × WGI growth-volatility interaction < 0: **True**; coef=-0.5557538854459635

## Method and coverage

Two-way country and year fixed effects with country-clustered uncertainty. The five-year rolling growth volatility is calculated before fitting its separate outcome model. US rate and oil price are absorbed by year effects. The historical main-effect fallback is preserved under `historical/`.
Complete-case sample: 128 country-years, 10/20 declared countries. Missing countries: CHL, CRI, DOM, GTM, NIC, PAN, SLV, TTO, URY, VEN.
The reduced coverage limits generalization beyond the analysed countries. REFUTED means the frozen three-condition support rule failed here; it does not establish a statistically significant effect in the opposite direction.

Spec SHA-256: `cdeef680cad72107ea536d8c6d075bcdce674e7005b08dfff69884ad3f4591fb`
Input-panel SHA-256: `9f27905d4451ab9836ae36b1dc4e90b66ee41b3ac7072fe439c45b510531f784`
