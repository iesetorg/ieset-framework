# Capital deepening without TFP limit

**Verdict:** SUPPORTED

**Claim:** Capital deepening alone is a weak predictor of labour-productivity growth once MFP contribution is included.

**Test:** `lp_growth ~ capital_deepening + tfp_contribution + C(country) + C(year)`

**Sample:** n=483, countries=17, years=1986–2024.

**Key coefficients**
- `capital_deepening`: beta=0.2752, p=1.3e-43, 90/95 CI approx [0.2363, 0.3142]
- `tfp_contribution`: beta=0.9849, p=0, 90/95 CI approx [0.9567, 1.013]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
