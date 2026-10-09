# Small open economy frontier convergence

**Verdict:** SUPPORTED

> **RE-SCOPED to descriptive calibration, with a 0.25 scoreboard weight cap (2026-10-09).** The same lagged frontier-gap design was flagged in the [adversarial audit](../../audits/ieset_adversarial_supported_claims_2026-07-31.md) for unit normalization and possible mechanical convergence. The numeric result and frozen rule are unchanged.

**Claim:** Small open OECD economies show conditional labour-productivity convergence toward the annual frontier.

**Test:** `lp_growth ~ frontier_gap_lag + C(country) + C(year)`

**Sample:** n=527, countries=14, years=1971–2025.

**Key coefficients**
- `frontier_gap_lag`: beta=3.529, p=0.0462, 90/95 CI approx [0.05981, 6.999]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.

## Correction — cross-run consistency

`lp_growth` is 100 times the annual log change, while `frontier_gap_lag` is a log-level gap. The coefficient of 3.529 is in percentage points of annual growth per one log unit of gap; a 0.1 log gap corresponds to about 0.353 percentage points. The design is a descriptive convergence association and does not establish a causal frontier-adjustment mechanism. Its evidentiary weight is capped consistently with the audited broad OECD frontier run.
