# BLOCKED — resource_rent_capture_outperforms_laissez_faire

**Status:** Cannot run with currently-fetched vintages.

## Required data not available

Primary treatment variable: `resource_rent_capture_share`. Per spec this is constructed from:
- IMF GFS resource-rent fiscal series — not fetched.
- IMF Natural Resources Fiscal Database — not fetched (specialist fetcher pending).
- Sovereign Wealth Fund disclosures (NBIM, KIA, Chile SWF, Alaska Permanent Fund) — manual coding sheet not present.
- Resource export value series — would require disaggregated trade flows not in current `world_bank_wdi` slice.

Endowment controls:
- `NY.GDP.TOTL.RT.ZS` (total natural-resource rents / GDP) — not in WDI vintages list.
- `ADJ.DRES.RT.ZS` adjusted savings — not fetched.

Outcomes: `NY.GDP.PCAP.PP.KD`, `SP.DYN.LE00.IN`, `SI.POV.GINI` are present, but without the rent-capture treatment variable the regression cannot be identified. WGI controls (GE, CC) are present.

The spec itself flags "Pending specialist fetcher for IMF Natural Resource Fiscal Framework database; v1 flags as data-gated."

## What would unblock

1. Fetch `NY.GDP.TOTL.RT.ZS` from WDI.
2. Specialist IMF Natural Resources Fiscal Framework fetcher.
3. Manual SWF / royalty-capture coding sheet committed under `data/manual/`.

## Action

No replication.py written. The primary IV is data-gated and the gate has not been met. Anchor-case comparisons (Norway vs Australia, Botswana vs Angola, Chile within-country, Alaska within-country) could in principle be run as paired-trajectory descriptives, but they are not the panel_fe estimator the audit flagged this hypothesis under.
