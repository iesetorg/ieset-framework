# Data-Source Bridge Unlocks — 2026-05-19

This pass targeted false blockers in the runnability layer: specs that referenced
data already present locally under an equivalent publisher or series namespace.

## Changes Made

- Added bidirectional publisher-alias resolution in `scripts/audit_runnability.py`.
  This fixes cases where local vintages are stored under an alias directory, e.g.
  `irr`, while specs cite the canonical publisher `ilzetzki_reinhart_rogoff`.
- Added provenance-marker skips for non-fetcher tokens such as `dates`,
  `policy_axes`, `movement_position_alignments`, `trajectory`, `checks`,
  `tabulation`, `fallback`, and `capex`.
- Added safe publisher aliases:
  - `world_bank_wits` -> `wits`
  - `oecd_lfs`, `oecd_employment`, `oecd_epl`, `oecd_bci`, `oecd_revenue_statistics`,
    `oecd_pension_statistics`, `oecd_tiva`, `oecd_fdi`, `oecd_fdi_reg`, `oecd_stri` -> `oecd`
  - `ilo` -> `ilostat`
  - `census` -> `us_census`
- Added safe series aliases where local vintages already exist:
  - IRENA: `capacity`, `solar_pv_costs`, `wind_lcoe`
  - WGI: `RQ.EST`, `rule_of_law`
  - OECD: `OECD.SDD.NAD`, `OECD.SDD.TPS`, `DSD_SOCX@DF_SOCX_AGG`
  - OECD PMR: `overall_pmr`, `pmr_composite`, `pmr`, `barriers_to_entry`
  - PWT: `rgdpo_emp`
  - Fraser EFW: `property_rights`, `regulation_business`, `area_3`
- Normalised `australia_tobacco_excise_punitive_vs_harm_reduction_comparators`
  from the non-schema `descriptive_cross_section` template to the existing
  schema-valid `descriptive` template.

## Runnability Movement

Before this bridge pass, the current audit showed:

- `READY`: 1474
- `NEEDS_DATA`: 137
- `NEEDS_TEMPLATE`: 1
- `LEGACY_SCHEMA`: 0

After this bridge pass:

- `READY`: 1511
- `NEEDS_DATA`: 101
- `NEEDS_TEMPLATE`: 0
- `LEGACY_SCHEMA`: 0

Net effect: **+37 READY hypotheses**, **-36 NEEDS_DATA blockers**, and **-1
template blocker** without fetching new data or changing any verdict.

## Remaining Biggest True Blockers

The next actual data work should target publishers rather than alias repair:

| Publisher | Solo unlocks | Notes |
|---|---:|---|
| `boj` | 12 | Biggest monetary-policy unlock; many Japan/QE/monetarist tests. |
| `un_comtrade` | 7 | Trade/product-variety and tariff-protection tests. |
| `wipo` | 6 | Innovation, patent, public-R&D, and Korea/Taiwan capability tests. |
| `unctad` | 3 | FDI/GVC/developmentalist and industrial-policy tests. |
| `iea` | 3 | Energy-price, nuclear, subsidy, and emissions tests. |
| `barro_lee` | 3 | Human-capital controls for long-horizon growth tests. |

Series-level gaps remain visible in `engine/runnability.report.md`. Those should
be resolved with targeted fetches or explicit spec rewrites, not broad aliasing.
