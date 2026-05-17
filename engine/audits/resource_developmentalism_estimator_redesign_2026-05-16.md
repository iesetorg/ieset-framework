# Resource Developmentalism Estimator Redesign - 2026-05-16

Target: `resource_developmentalism_rent_seeking_trap`

Status: design note for the hardening swarm. No run artifacts were overwritten by this note.

## Why The Current Generic FE Run Is Insufficient

The current result card estimates only the first loaded outcome, `export_diversification_index`, in a contemporaneous two-way fixed-effects model. That is not the same as the preregistered claim, which asks whether resource-funded developmentalist states produce early public-investment gains but weaker long-run diversification and lower TFP growth than market-open resource peers over 30-year windows.

Current generic design misses four core requirements:

- It does not estimate all listed outcomes.
- It does not implement 5-, 10-, or 30-year lag/window structure.
- It does not explicitly define `market_open_resource_peer`.
- It does not distinguish uncoded controls from true market-open comparator cases.

## Proposed Hardened Design

The hardened replication should become a bespoke multi-table analysis rather than a single generic `panel_fe` call.

### Outcome Families

Report these as separate tables:

| Family | Primary measure | Current fallback | Interpretation |
| --- | --- | --- | --- |
| Export concentration/diversification | product-level HHI/Theil from UNCTAD/BACI/Comtrade if available | WDI broad `export_diversification_index` and `export_concentration_hhi_broad` | core long-run diversification claim |
| TFP/productivity | PWT `rtfpna` 5-year and 10-year changes | annual PWT growth | core productivity claim |
| Manufacturing structure | WDI manufacturing VA share; manufacturing export share if available | WDI manufacturing VA share | Dutch disease / productive-structure channel |
| Early investment gains | gross capital formation, public investment, infrastructure proxy | WDI investment share or PWT capital deepening | steelman channel |

No single outcome should determine the verdict alone. The result card should state whether each arm supports, weakens, refutes, or leaves the claim unresolved.

### Treatment Variants

Use a treatment ladder:

1. `resource_developmentalism_intensity`: current 0/0.5/1 movement-derived series.
2. `resource_developmentalism_binary`: intensity > 0.
3. `resource_developmentalism_lag_5`: 5-year lag.
4. `resource_developmentalism_lag_10`: 10-year lag.
5. `resource_developmentalism_cumulative_10`: rolling 10-year exposure.
6. `resource_developmentalism_cumulative_30`: rolling 30-year exposure where coverage allows.
7. `resource_developmentalism_x_resource_rents`: intensity multiplied by total rents.
8. `resource_statist_socialist`: subtype once treatment audit lands.
9. `market_open_resource_peer`: explicit comparator, not default zero.

Unknown or uncoded country-years should be excluded from comparator designs rather than treated as market-open peers.

### Sample Ladders

Report sample ladders rather than one blended result:

| Sample | Rule |
| --- | --- |
| Broad listed sample | Countries listed in hypothesis, 1970-2020 |
| Resource-rich country-years | WDI total rents >= 5 percent of GDP |
| Resource-rich countries | Average total rents >= 5 percent during sample |
| WGI-era sample | 1996+ with WGI controls |
| Long-run institutional sample | 1970+ with non-WGI alternatives such as Fraser legal system, Polity/V-Dem where feasible |
| Coded-comparator sample | Only country-years explicitly coded as resource-developmentalist, market-open peer, mixed, or rule-bound resource manager |

The result card must not call a 1996-2018 estimate a 1970-2020 test without a clear caveat.

### Control Ladders

For each main outcome, estimate:

1. no controls, country/year FE only
2. resource rents
3. resource rents + initial income
4. resource rents + initial income + WGI
5. resource rents + initial income + long-run institutional alternative
6. region-year FE if feasible

Institutional quality is plausibly a mediator as well as a confounder, so WGI should be reported as a robustness/control horizon, not silently imposed as the sole design.

### Lag And Placebo Structure

Minimum lag ladder:

- lead 5 years
- contemporaneous
- lag 1 year
- lag 5 years
- lag 10 years
- rolling 10-year exposure
- rolling 30-year exposure where enough history exists

Interpretation:

- A significant lagged negative diversification result with null placebo leads would support the trap mechanism more than the current contemporaneous null.
- A result that appears only in contemporaneous models but vanishes under lags should be treated as weak.
- A result that flips only when WGI is added should be classified as sample/control-sensitive.

### Comparator Design

The phrase “market-open resource peers” needs explicit coding. Candidate variables:

- Fraser `freedom_to_trade_internationally`
- Fraser `legal_system_property_rights`
- Heritage trade/investment/property-rights dimensions for recent cross-sections only
- Chinn-Ito capital openness
- movement alignment with classical liberal / market liberal positions
- manually coded rule-bound resource institutions such as SWF discipline

Comparator categories:

- resource developmentalist/statist
- market-open resource peer
- rule-bound resource manager
- mixed
- uncoded

The main comparator model should exclude `uncoded`. The broad FE model can stay as an exploratory robustness check.

## Suggested Output Artifacts

The hardened replication should write:

- `engine/runs/resource_developmentalism_rent_seeking_trap/diagnostics.json`
- `engine/runs/resource_developmentalism_rent_seeking_trap/result_card.md`
- `engine/runs/resource_developmentalism_rent_seeking_trap/manifest.yaml`
- `engine/runs/resource_developmentalism_rent_seeking_trap/model_results.parquet`
- `engine/runs/resource_developmentalism_rent_seeking_trap/sample_ladder.json`
- refreshed `evidence_packet.yaml`

Diagnostics should include:

- outcome family table
- model ladder table
- lag/window table
- sample ladder table
- treatment exposure counts
- comparator category counts
- provenance list of input vintages
- QA classification: `scoreboard_candidate`, `directional_partial`, `research_only`, `hold_repair`, or `failed_design`

## Verdict Logic

The hardened verdict should avoid single-coefficient grading.

Candidate classification rule:

- `SUPPORTED`: product-level export concentration worsens and TFP/manufacturing outcomes weaken under lagged/cumulative resource-developmentalist exposure, with placebo leads null and comparator sample clean.
- `DIRECTIONAL_PARTIAL`: core diversification or TFP arm supports the claim, but the other arm is weak, sample-limited, or proxy-only.
- `REFUTED`: clean comparator design shows no weakening or positive long-run outcomes across diversification and TFP, with adequate power.
- `RESEARCH_ONLY`: treatment coding, product-level data, or comparator definition remains too weak.
- `HOLD_REPAIR`: stale artifacts, missing manifest, broad-proxy overclaim, or uncoded controls remain unresolved.

## Implementation Sequence

1. Wait for artifact, data, treatment, and fast-pass worker outputs.
2. If treatment audit says current treatment is too noisy, repair coding before model implementation.
3. If fast pass shows lag signal survives basic controls, implement bespoke replication.
4. If fast pass shows no signal except in proxy/timing-sensitive models, classify as `research_only` until product-level trade data lands.
5. Regenerate evidence packet only after hardened diagnostics and manifest exist.

## Immediate Decision Gate

Proceed to bespoke replication only if the fast-pass audit shows at least one credible signal in:

- lagged export diversification/concentration,
- cumulative exposure,
- TFP or manufacturing channel,
- or a clean resource-rich sample after excluding uncoded controls.

Otherwise the next wave should focus on treatment subtype coding and product-level trade data before further estimation.
