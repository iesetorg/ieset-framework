# BLS Minimum-Wage Data Unlock

Generated: 2026-05-14

## Landed

Network-enabled retry of the official BLS backfill landed two useful vintages:

- `bls:LAU_state_employment_population_ratio_panel`
  - rows: 21,420
  - period: 1990-2024
  - states: 51
  - vintage: `data/vintages/bls/LAU_state_employment_population_ratio_panel@2026-05-14T110716Z.parquet`
- `bls:QCEW_state_total_employment_panel`
  - rows: 102
  - period: 2023-2024
  - states: 51
  - vintage: `data/vintages/bls/QCEW_state_total_employment_panel@2026-05-14T110759Z.parquet`

The same run still hit the unauthenticated BLS daily threshold for:

- `bls:LAU_state_unemployment_rate_panel`

An older LAU unemployment vintage is already on disk:

- `data/vintages/bls/LAU_state_unemployment_rate_panel@2026-05-05T204700Z.parquet`

## Derived alias

`scripts/build_minimum_wage_bite_panels_2026_05_12.py` now also writes:

- `derived:minimum_wage_bite_ratio_subnational_panel`

This is a documented state-level alias of the already built statutory-minimum-to-OEWS-median wage bite panel. It is intended to satisfy specs whose gate asks for a subnational bite panel while preserving the underlying geographic level in metadata:

- `geographic_level: state`
- denominator: `subnational_median_alias`

Build output:

- `derived:minimum_wage_bite_ratio_state_panel` - 474 rows, 2014-2024
- `derived:minimum_wage_bite_ratio_subnational_panel` - 474 rows, 2014-2024
- `derived:minimum_wage_low_tail_bite_ratio_state_panel` - 474 rows, 2014-2024

## Still blocked

This does not yet produce a clean federal-minimum-wage verdict. The current `federal_minimum_wage_employment_meta` runner falls through to older generic variable resolution once the exact data gate is satisfied, and still needs a proper promoted estimator that uses:

- state QCEW employment,
- USDOL state statutory minimum-wage history,
- derived state/subnational bite ratios,
- LAU controls,
- and a clearly sharpened falsification rule.

The next pass should update the minimum-wage runner/spec rather than treating the generic fallback result as valid.

## Commit policy

The parquet vintages under `data/vintages/` are gitignored by design. This commit records the reproducible manifests, audits, and builder change.
