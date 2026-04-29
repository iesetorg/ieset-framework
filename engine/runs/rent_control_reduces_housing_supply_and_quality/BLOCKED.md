# BLOCKED — rent_control_reduces_housing_supply_and_quality

**Reason:** city/metro-level housing data not yet shipped.

## Missing data (5)

- `bls:CUURS12B_rent_nyc_msa`
- `bls:CUURS24B_rent_minneapolis_msa`
- `bls:CUURS35B_rent_portland_msa`
- `eurostat:prc_hpi_q_berlin`
- `us_census:BPS_permits_metro`

## Found data (0)

(none)

## Pre-registered treatment cohorts

- berlin_de (DEU): Mietendeckel — 2020-02-23
- stpaul_us (USA): St Paul rent stabilisation — 2021-11-02
- nyc_us (USA): HSTPA — 2019-06-14
- oregon_us (USA): SB-608 — 2019-02-28

## Why we don't fall back to country-level

Berlin is ~4% of German HPI; NYC is ~7% of US shelter CPI; running a country-level event study around these dates would attenuate the effect by an order of magnitude and risk reporting a null where a city-level analysis (per Diamond-McQuade-Qian 2019, Kholodilin-Kohl 2023) cleanly identifies a supply contraction. The YAML's framework-validation purpose ('if the model cannot reproduce the ~93%-economist-consensus finding, the framework is broken') makes it especially important to use the right resolution.

## Unblock checklist

1. `data.fetchers.bls`: MSA-level CUURS series
2. US Census BPS metro permit fetcher
3. Eurostat `prc_hpi_q` NUTS-2 / Berlin Statistik
4. Re-run — replication.py auto-detects.
