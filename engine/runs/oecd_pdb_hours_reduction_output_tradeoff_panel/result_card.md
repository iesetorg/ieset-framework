# Hours reduction output tradeoff

**Verdict:** SUPPORTED

> **QUARANTINED pending a prospective v2 test (2026-10-09).** The stored estimate and label below remain visible for audit, but this run carries no new public credit because the decision rule does not test the English claim in the correct direction.

**Claim:** Average-hours reductions are not mechanically associated with lower real GVA growth in OECD PDB panels after fixed effects.

**Test:** `gva_growth ~ hours_growth + C(country) + C(year)`

**Sample:** n=1113, countries=31, years=1971–2025.

**Key coefficients**
- `hours_growth`: beta=0.2197, p=0.000153, 90/95 CI approx [0.106, 0.3335]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.

## Correction — sign and claim mismatch

The estimated coefficient on `hours_growth` is **positive** (+0.2197, 95% CI +0.106 to +0.333). In this regression, lower hours growth predicts lower GVA growth, whereas the English claim says hours reductions are not associated with lower output growth. The frozen `not_negative_large` support rule accepts a lower confidence bound above −0.5, which does not establish that English claim. The original numeric result and v1 verdict are retained for inspection; any corrected claim and test must be registered prospectively.
