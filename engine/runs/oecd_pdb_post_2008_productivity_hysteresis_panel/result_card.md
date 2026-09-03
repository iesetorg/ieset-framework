# Post-2008 productivity hysteresis

**Verdict:** SUPPORTED

> **RE-SCOPED to supported (descriptive) tier — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: Level-shift dummy with no pre-2008 trend control and no COVID-window handling.


**Claim:** OECD labour-productivity growth was persistently lower after 2008 than before 2008.

**Test:** `lp_growth ~ post_2008 + C(country)`

**Sample:** n=859, countries=31, years=1995–2024.

**Key coefficients**
- `post_2008`: beta=-1.323, p=7.49e-11, 90/95 CI approx [-1.722, -0.925]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** RE-SCOPED to supported (descriptive) tier · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 17) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- Level-shift dummy with no pre-2008 trend control and no COVID-window handling — documented deceleration misattributed to crisis hysteresis.

No original content has been deleted; this correction is additive.
