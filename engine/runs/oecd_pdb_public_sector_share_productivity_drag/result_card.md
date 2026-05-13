# Public-sector share productivity drag

**Verdict:** REFUTED_OR_WEAK

**Claim:** A larger public-administration, education, and health GVA share predicts slower subsequent total-economy labour-productivity growth.

**Test:** `lp_growth ~ public_gva_share_lag + C(country) + C(year)`

**Sample:** n=990, countries=31, years=1971–2025.

**Key coefficients**
- `public_gva_share_lag`: beta=3.489, p=0.647, 90/95 CI approx [-11.45, 18.42]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
