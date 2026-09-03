# OECD PDB GDP/hour frontier convergence

**Verdict:** SUPPORTED

> **RE-SCOPED to supported (descriptive) tier — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: frontier_gap_lag β=3.099 on a lagged level gap.


**Claim:** Countries farther below the annual OECD labour-productivity frontier subsequently grow faster in GDP per hour.

**Test:** `gdp_hour_growth ~ frontier_gap_lag + C(country) + C(year)`

**Sample:** n=1122, countries=31, years=1971–2025.

**Key coefficients**
- `frontier_gap_lag`: beta=3.099, p=0.000167, 90/95 CI approx [1.486, 4.712]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** RE-SCOPED to supported (descriptive) tier · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 11) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- frontier_gap_lag β=3.099 on a lagged level gap — units/normalization red flag (likely 100× misread on the card).
- The identical econometric structure was declared a tooling artefact in the archived `asian_convergence_vs_western_stagnation_2000_2023` run — asymmetric treatment.

No original content has been deleted; this correction is additive.
