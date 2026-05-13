# OECD PDB TFP growth persistence

**Verdict:** REFUTED_OR_WEAK

**Claim:** OECD multifactor-productivity growth has country-level persistence after common year shocks.

**Test:** `tfp_growth ~ tfp_growth_lag + C(country) + C(year)`

**Sample:** n=468, countries=17, years=1986–2024.

**Key coefficients**
- `tfp_growth_lag`: beta=-0.1404, p=0.107, 90/95 CI approx [-0.3114, 0.03056]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
