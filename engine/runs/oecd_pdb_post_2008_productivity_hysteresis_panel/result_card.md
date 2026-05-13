# Post-2008 productivity hysteresis

**Verdict:** SUPPORTED

**Claim:** OECD labour-productivity growth was persistently lower after 2008 than before 2008.

**Test:** `lp_growth ~ post_2008 + C(country)`

**Sample:** n=859, countries=31, years=1995–2024.

**Key coefficients**
- `post_2008`: beta=-1.323, p=7.49e-11, 90/95 CI approx [-1.722, -0.925]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
