# Provenance — mlc_retail_persistence

**Indicator.** Continuous years of operation of Cuba's state-sanctioned
USD-denominated ("Moneda Libremente Convertible", MLC) retail network for
staple goods.

**Series value (2024).** 6 years (2019–2024 inclusive).

## Citation chain

1. **Resolucion 115/2019** (Ministerio de Finanzas y Precios, MFP),
   28 October 2019. Authorised foreign-currency-denominated retail stores
   for imported "high-end" goods (white goods, vehicle parts).
   Source: Gaceta Oficial No. 80 Extraordinaria, 28 October 2019.

2. **Resolucion 423/2020** (BCC + MFP), July 2020. Expanded MLC retail to
   staple groceries (cooking oil, chicken, rice, soap, detergent) in
   response to COVID-era CUP devaluation. Source: Gaceta Oficial No. 41
   Extraordinaria, 16 July 2020.

3. **Reuters / AP coverage**:
   - Reuters, "Cuba opens dollar stores for basic foodstuffs", 16 July 2020.
   - AP, "Cuba's currency policy creates two classes of citizens", 30
     August 2021.
   - Reuters, "Cuba's economic crisis tests communist government", 11
     August 2024 (confirms MLC stores remain primary channel for
     imported staples).

4. **Academic**: Vidal Alejandro 2022 "Cuba's Currency Reform and the MLC
   Network"; Mesa-Lago 2022 *Cuba's New Economy* ch. 6 documents the
   structural shift to MLC retail and its persistence through the 2021
   ordenamiento.

## Methodology

- start_year = 2019 (Resolucion 115/2019 effective 28 October 2019)
- end_year = 2024 (current as of writing; bump annually if MLC retail
  remains operational)
- value = end_year - start_year + 1 = 6

## Threshold evaluation

Pre-registered threshold: `documented state-sanctioned USD-only retail
network covering staple goods operating for >=2 years`. With value=6, MET.

## Robustness

This is a regulatory-observation indicator. The MLC network is publicly
decreed and visible from Reuters/AP/independent reporting; not subject to
Cuban-state-statistics measurement disputes.
