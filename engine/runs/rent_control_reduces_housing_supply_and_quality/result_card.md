# Result card — rent_control_reduces_housing_supply_and_quality

**Verdict:** BLOCKED — required city/metro-level outcomes not in vintages (5 missing). Hypothesis is pre-registered ahead of fetcher work; running on country-level proxy would conflate treatment dilution with absence of effect. See BLOCKED.md.

## Status

BLOCKED on data. See BLOCKED.md.

## Missing data

- `bls:CUURS12B_rent_nyc_msa`
- `bls:CUURS24B_rent_minneapolis_msa`
- `bls:CUURS35B_rent_portland_msa`
- `eurostat:prc_hpi_q_berlin`
- `us_census:BPS_permits_metro`

## Estimator (pre-registered, awaiting data)

Callaway-Sant'Anna staggered DiD across cohorts:
- berlin_de: Mietendeckel (2020-02-23)
- stpaul_us: St Paul rent stabilisation (2021-11-02)
- nyc_us: HSTPA (2019-06-14)
- oregon_us: SB-608 (2019-02-28)

## Outcomes (pre-registered)

- housing-permit issuance (city/metro)
- rental-listing counts
- median rent

## Provenance

See `manifest.yaml`, `BLOCKED.md`, `replication.py`.
