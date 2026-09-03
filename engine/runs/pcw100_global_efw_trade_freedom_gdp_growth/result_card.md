# Result card — pcw100_global_efw_trade_freedom_gdp_growth

- Verdict: **SUPPORTED**

> **RE-SCOPED to screen_positive tier — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: Associational cross-sectional screen (p=0.0015) emitted at full evidentiary weight (X7); reverse causality and state-failure composition of the low quartile unaddressed.

- Cohort: `international_policy`
- Expected sign: `+`
- Reason: coefficient=+0.63614, SE=0.20036, p=0.00149848, expected_sign=+
- Observations: 163
- Units: 163
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 1.89178

## Extreme policy groups

- Low-policy units: AGO, ARG, BDI, BEN, BGD, BHS, CAF, CIV, CMR, COD, COG, COM, DZA, EGY, ETH, FJI, GAB, GIN, GNB, IND, IRN, LBN, LBR, LBY, LSO, MMR, MWI, NAM, NER, NGA, NPL, PAK, RUS, SDN, SWZ, SYR, TCD, TZA, VEN, YEM, ZWE
- High-policy units: ARE, AUT, BEL, BGR, CAN, CHL, CRI, CYP, CZE, DEU, DNK, ESP, EST, FIN, FRA, GBR, GEO, GTM, HKG, HRV, HUN, IRL, ISR, ITA, LTU, LUX, LVA, MLT, MUS, NLD, NZL, PAN, PER, PRT, ROU, SGP, SVK, SVN, SWE, SYC, USA

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** RE-SCOPED to screen_positive tier · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 9) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- Associational cross-sectional screen (p=0.0015) emitted at full evidentiary weight (X7); reverse causality and state-failure composition of the low quartile unaddressed.
- v2 tier: screens emit `screen_positive`; scoreboard weight ≤ 0.25.

No original content has been deleted; this correction is additive.

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.63614014
- Standard error: 0.20036049
- p-value: 0.0014984791
- R-squared: 0.422435
- Method: statsmodels OLS with HC3 covariance
