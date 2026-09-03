# Result card — pcw100_global_efw_sound_money_gdp_growth

- Verdict: **SUPPORTED**

> **RE-SCOPED to screen_positive tier — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: SOM (Somalia) in the top sound-money quartile.

- Cohort: `international_policy`
- Expected sign: `+`
- Reason: coefficient=+0.460998, SE=0.192413, p=0.0165805, expected_sign=+
- Observations: 163
- Units: 163
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 2.15291

## Extreme policy groups

- Low-policy units: AGO, ARG, AZE, BFA, BGD, BLR, BTN, CAF, CIV, COD, COG, COM, ETH, FJI, GAB, GHA, GIN, GNB, IRN, LAO, LBY, LKA, MLI, MMR, MOZ, MWI, NAM, NER, NPL, PAK, PNG, SDN, SEN, SLE, SYR, TCD, TGO, UKR, VEN, VNM, ZWE
- High-policy units: ALB, AUS, AUT, BEL, CAN, CHE, CHL, CYP, CZE, DEU, DNK, ESP, FIN, FRA, GBR, GRC, GTM, HKG, HRV, HUN, IRL, ISR, ITA, JOR, JPN, KOR, LUX, MLT, MUS, NLD, NZL, PAN, PER, PRT, SGP, SLV, SOM, SVK, SVN, SWE, USA

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** RE-SCOPED to screen_positive tier · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 19) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- SOM (Somalia) in the top sound-money quartile — index/coding or imputation integrity problem in the input.
- Reverse causality by construction: growth collapses cause inflation (fiscal monetization), the screen's dominant signal (X7).

No original content has been deleted; this correction is additive.

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.46099753
- Standard error: 0.19241261
- p-value: 0.016580517
- R-squared: 0.407815
- Method: statsmodels OLS with HC3 covariance
