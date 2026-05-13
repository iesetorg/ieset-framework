# PMR reform productivity compounder

**Verdict:** REFUTED_OR_WEAK

**Claim:** Countries with larger PMR declines from 2018 to 2023 saw faster PDB labour-productivity growth in the following window.

**Test:** `lp_growth_2018_2024 ~ pmr_decline_2018_2023`

**Sample:** n=31, countries=31, years=None–None.

**Key coefficients**
- `pmr_decline_2018_2023`: beta=-1.827, p=0.198, 90/95 CI approx [-4.612, 0.9568]

**Data:** `oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0` from `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
