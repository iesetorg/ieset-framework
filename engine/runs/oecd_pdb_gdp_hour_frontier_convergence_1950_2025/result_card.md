# OECD PDB GDP/hour frontier convergence

**Verdict:** SUPPORTED

**Claim:** Countries farther below the annual OECD labour-productivity frontier subsequently grow faster in GDP per hour.

**Test:** `gdp_hour_growth ~ frontier_gap_lag + C(country) + C(year)`

**Sample:** n=1122, countries=31, years=1971–2025.

**Key coefficients**
- `frontier_gap_lag`: beta=3.099, p=0.000167, 90/95 CI approx [1.486, 4.712]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
