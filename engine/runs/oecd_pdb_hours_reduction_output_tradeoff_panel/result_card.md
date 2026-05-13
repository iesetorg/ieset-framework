# Hours reduction output tradeoff

**Verdict:** SUPPORTED

**Claim:** Average-hours reductions are not mechanically associated with lower real GVA growth in OECD PDB panels after fixed effects.

**Test:** `gva_growth ~ hours_growth + C(country) + C(year)`

**Sample:** n=1113, countries=31, years=1971–2025.

**Key coefficients**
- `hours_growth`: beta=0.2197, p=0.000153, 90/95 CI approx [0.106, 0.3335]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
