# Absolute decoupling of GDP from material throughput, global, 1990-2020

**Verdict:** SUPPORTED (production-based proxy) — Population-weighted mean per-capita CO2 in 2020 was 231% of its 1990 level across the 26-country panel (>= 95% floor). No global absolute decoupling visible in production-based throughput. Cumulative real per-capita GDP grew +107% on average over the same window. 12 of 26 countries individually achieved sustained per-country absolute decoupling. NOTE: Consumption-based MF/CO2 unavailable on disk — the offshoring critique remains untested; see methodology_note.

## Summary

- Sample: 26 of 26 countries with both 1990 and 2020 observations.
- Population-weighted mean per-capita CO2 in 2020: **231% of 1990 baseline**.
- Simple cross-country mean: 109%; median 79%.
- Mean cumulative real per-capita GDP growth 1990-2020: **+107%**.
- Per-country decoupling (>= 30% GDP growth AND >= 10% CO2 drop): **12 of 26** countries — AUT, BEL, CAN, DEU, DNK, ESP, FIN, GBR, IRL, NLD, SWE, USA.

## Method

Cross-country snapshot of two ratios over 1990-2020:

1. PRIMARY: population-weighted mean of (CO2 per capita 2020 / CO2 per capita 1990). SUPPORTED if >= 0.95; REFUTED if <= 0.8; PARTIAL otherwise.
2. SECONDARY: country count where 2020 per-capita CO2 fell at least 10% AND per-capita GDP rose at least 30%.

## Data gap (important caveat)

The spec calls for UNEP/IRP Domestic Material Consumption + Material Footprint and the consumption-based reframing. Neither of those nor consumption-based CO2 (GCP/Eora MRIO) is available in `data/vintages/`. Per the spec's own TODO note, we substituted production-based CO2 per capita as a throughput proxy. This means the run can speak to the production-based half of the claim but NOT to the offshoring/consumption-based half. A SUPPORTED verdict is therefore provisional in the strong sense; only a REFUTED verdict on production-based throughput would dispositively refute the broader claim.

## Data

- world_bank_wdi:NY.GDP.PCAP.KD
- world_bank_wdi:SP.POP.TOTL
- owid:co2-emissions-per-capita (production-based)
