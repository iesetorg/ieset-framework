# Small open economy frontier convergence

**Verdict:** SUPPORTED

**Claim:** Small open OECD economies show conditional labour-productivity convergence toward the annual frontier.

**Test:** `lp_growth ~ frontier_gap_lag + C(country) + C(year)`

**Sample:** n=527, countries=14, years=1971–2025.

**Key coefficients**
- `frontier_gap_lag`: beta=3.529, p=0.0462, 90/95 CI approx [0.05981, 6.999]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
