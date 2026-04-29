# Provenance — libreta_persistence

**Indicator.** Continuous years of operation of Cuba's national ration-card
("libreta de abastecimiento") system.

**Series value (2024).** 63 years (1962–2024 inclusive).

## Citation chain

1. **Mesa-Lago, Carmelo.** *Cuba's Economy: Reform Without Privatization.*
   Brookings, 2014. Chapter 4 documents the 1962 introduction of the libreta
   under Resolucion No. 1, 12 de marzo de 1962, MINCIN, and traces its
   continuous operation through the Special Period to 2014. Mesa-Lago is
   the canonical academic chronologist of Cuban economic-policy persistence.

2. **OnCuba News reporting (2024).** "La libreta de abastecimiento cumple
   62 años: las cifras del racionamiento en Cuba", OnCuba, 12 March 2024.
   Confirms the libreta remains in legally-binding force and quantifies
   per-capita monthly entitlements (rice 7 lb, sugar 4 lb, beans 10 oz, etc.)
   as of early 2024.

3. **14ymedio coverage (2023–2024).** Multiple reports on libreta-product
   shortages but no policy revocation. The May 2024 anniversary coverage
   ("La libreta cumple 62 años de existencia") explicitly confirms the
   system is still operating despite chronic supply shortfalls.

4. **Gaceta Oficial de la Republica de Cuba.** No revocation resolution has
   appeared in the Gaceta Oficial since the 1962 institution. Ration product
   tables are revised periodically (most recently 2023 for sugar and rice
   per-capita allotments) but the libreta itself is unchanged.

## Methodology

- start_year = 1962 (Resolucion No. 1 MINCIN, 12 March 1962)
- end_year = 2024 (current as of writing; bump annually if libreta remains
  in force)
- value = end_year - start_year + 1 = 63

## Threshold evaluation

The hypothesis pre-registered threshold is `>=50 years of continuous
national ration-card system operation`. With value=63, this evaluates to MET.

## Robustness

This is an institutional-observation indicator, not a statistical estimate.
It is robust to GDP-revision controversies and to Cuban-state-NIPA
measurement disputes. The only way for this to be NOT_MET would be a
formal revocation in the Gaceta Oficial, which has not occurred.
