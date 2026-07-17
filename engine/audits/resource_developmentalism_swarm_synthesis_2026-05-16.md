# Resource Developmentalism Swarm Synthesis - 2026-05-16

Target: `resource_developmentalism_rent_seeking_trap`

Plan anchor: `internal research notes`

Current result card: `engine/runs/resource_developmentalism_rent_seeking_trap/result_card.md`

## Executive Decision

Do not promote the current `PARTIAL` result to a scoreboard-safe diagnosis. Classify it as `research_only` / `hold_repair`.

The current result is useful as a screening signal, but the hardening swarm found three blockers:

1. The evidence packet is stale and the run has no local manifest.
2. The treatment is a mechanically derived scalar that mixes socialist resource statism, Gulf rentier development, rule-bound managers, market-open peers, mixed cases, and uncoded cases.
3. The current export outcome is a broad WDI-sector proxy, not a product-level diversification measure, and the fast-pass does not confirm the claim across TFP or manufacturing outcomes.

The next wave should repair treatment coding and export-product measurement before any hardened causal replication is used for scoring.

## Worker Outputs

| Lane | Output | Decision value |
| --- | --- | --- |
| Queue freeze | `engine/audits/resource_developmentalism_queue_freeze_2026-05-16.md` | Locked this as an audit/design wave and blocked edits to run artifacts, movement YAML, shared runners, and scoreboard files. |
| Artifact reconciliation | `engine/audits/resource_developmentalism_artifact_reconciliation_2026-05-16.md` | Current diagnostics and result card agree, but `evidence_packet.yaml` is stale and there is no run-local manifest. |
| Data measurement | `engine/audits/resource_developmentalism_data_measurement_plan_2026-05-16.md` | Current `export_diversification_index` is only a broad WDI proxy; product-level HHI/Theil/top-share measures are the needed upgrade. |
| Treatment coding | `engine/audits/resource_developmentalism_treatment_audit_2026-05-16.md` and `engine/audits/resource_developmentalism_treatment_inventory_2026-05-16.csv` | Current treatment construction fails the noise gate and should be treated as a screen, not a causal treatment. |
| Outcome fast pass | `engine/audits/resource_developmentalism_fast_pass_2026-05-16.md` | Reproduces the null full-control result; finds one fragile export-proxy signal under country-year rent restriction, with no TFP/manufacturing package. |
| Estimator redesign | `engine/audits/resource_developmentalism_estimator_redesign_2026-05-16.md` | Specifies the bespoke multi-outcome, lag/window, sample-ladder design needed after treatment and measurement repairs. |
| Historical case map | `engine/audits/resource_developmentalism_case_map_2026-05-16.md` | Splits cases into subtype arms and identifies obvious comparators/uncoded peers that must not remain anonymous zero controls. |
| Wave 2A subtype queue | `engine/audits/resource_developmentalism_subtype_review_queue_2026-05-16.md` and `engine/audits/resource_developmentalism_subtype_review_queue_2026-05-16.csv` | Turns the treatment audit into a prioritized local recoding queue with 32 high-impact cases and comparator eligibility flags. |
| Wave 2B product-data inventory | `engine/audits/resource_developmentalism_product_data_inventory_2026-05-16.md` | Finds no directly usable local product-level export archive; product-level diversification is blocked on BACI, Comtrade, UNCTAD, WITS, or equivalent acquisition. |

## Gate Findings

### Artifact Gate

Current `diagnostics.json` and `result_card.md` agree:

- Verdict: `PARTIAL`
- Coefficient: `-0.008094`
- p-value: `0.758`
- Observations: `1,320`
- Countries: `73`
- Treated observations: about `195`
- Effective full-control window: mostly `1996-2018`

But `evidence_packet.yaml` still describes the prior `INCONCLUSIVE_DATA_PENDING` preflight state and has stale hashes. The run directory also lacks `manifest.yaml`. Any hardened rerun must regenerate provenance only after the treatment/outcome design is repaired.

### Treatment Gate

The treatment is currently built as positive `developmentalism` alignment filtered by WDI resource-rent exposure. That makes it a screening proxy, not a hand-coded resource-developmentalism variable.

Stop-rule evidence:

- Mechanical or derived developmentalism labels touch `209 / 941` positive country-years, or `22.2%`.
- Partial developmentalism labels touch `514 / 941` positive country-years, or `54.6%`.
- Long umbrella movements of 25+ active years touch `550 / 941` positive country-years, or `58.4%`.
- Country-level rent fallback accounts for `198 / 941` positive country-years, or `21.0%`.
- Unknown/no-active/uncoded country-years are zero-filled and therefore silently treated as controls.

This triggers the treatment stop rule. The next model should not use residual zero as a market-open comparator.

### Measurement Gate

The current export outcome is a broad WDI bucket proxy:

`1 - HHI([agricultural raw materials, fuels, manufactures, ores/metals, residual other])`

That is useful for long-run screening, but it cannot support a strong product-diversification claim. The primary measurement target should be exporter-product-year concentration:

- product HHI
- inverse HHI / normalized diversification
- Theil concentration
- top-1, top-3, top-10 export shares
- active product count
- commodity export share
- manufacturing export share

Preferred source ladder:

1. CEPII BACI HS6 product-level exporter-year archive
2. UN Comtrade HS/SITC product exports
3. UNCTAD concentration/diversification/product indices
4. Existing WDI broad proxy as fallback only

### Fast-Pass Gate

The full-control model reproduces the card:

- Export proxy coefficient `-0.008`, p `0.758`, n `1,320`

The broader fast pass does not confirm the preregistered package:

- Before WGI, the export proxy coefficient is positive/marginal, then flips toward zero after WGI listwise deletion.
- TFP growth is null under every control ladder.
- Manufacturing value-added share is null under every control ladder.
- Restricting to country-years with resource rents above 5 percent creates a stronger negative export-proxy coefficient (`-0.051`, p `0.005`) under full controls, but that signal does not appear in TFP or manufacturing.
- Export lead terms are as large or larger than the current/lag terms, raising timing and pre-trend concerns.

This does not justify a final bespoke scoring run yet. It does justify a repair wave.

### Case-Coding Gate

The case map shows that the scalar pools materially different mechanisms:

- Core `resource_statist_socialist`: Algeria FLN, Angola MPLA, Iraq Ba'ath, Venezuela Chavismo, Ecuador Correa, selected Bolivia/Syria years.
- Core `resource_developmentalist`: Indonesia New Order phases, Malaysia NEP/Mahathir after resource-channel review, Kazakhstan, selected Saudi/UAE diversification episodes.
- Rule-bound managers: Norway, Botswana, Chile copper fiscal-rule cases.
- Market-open resource peers: Australia, Colombia, Peru, Canada outside NEP shock, Vietnam if no explicit oil/gas funding channel is shown.
- Nationalisation/resource-sovereignty shocks: Venezuela Perez I, Bolivia hydrocarbons, Canada NEP, Mexico Lopez Portillo/Cantarell, Australia mining-tax episodes.
- Mixed/predation/sanction cases: Nigeria, Zaire/DRC, Iran, Russia, PNG, Kuwait welfare-rentier umbrella, broad Syria.
- WDI-threshold nonresource developmentalists: China, Ethiopia, Rwanda, Cote d'Ivoire, Senegal, Kenya, Tunisia, Morocco, Tanzania, Myanmar unless a concrete resource-funding channel is established.
- Uncoded obvious resource peers: Qatar, Oman, Bahrain, Libya, Trinidad and Tobago, Gabon, Cameroon, Zambia, Mongolia, Ghana resource episodes.

The main comparison must become subtype-aware, and `uncoded` must be preserved instead of collapsed into zero.

## Next Agent Wave

## Wave 2 Update

Wave 2A and Wave 2B completed.

Treatment recoding can proceed locally. The subtype queue identifies the first 32 review targets and confirms that residual zero is unsafe as a comparator. The clearest clean comparator candidates are Norway, Botswana, Chile, and Colombia. Vietnam, Australia, Canada, and Peru are conditional comparators only after shock or mixed years are separated. Kuwait, PNG, Iran, Nigeria, Zaire/DRC, China, Ethiopia, and Rwanda should be excluded as `mixed` until episode splits are coded. Qatar, Oman, Bahrain, Libya, Trinidad and Tobago, Gabon, Cameroon, Zambia, Mongolia, and Ghana remain `uncoded` and must not enter the residual control group.

Product-level export measurement cannot proceed from current local files. The inventory found WDI broad export-share vintages and CEPII Gravity/BACI-derived aggregate tradeflow vintages, but no BACI HS6, UN Comtrade, WITS, UNCTAD concentration index vintage, or equivalent exporter-product-year archive. Wave 2C is therefore blocked as a hardened product-diversification run. It can only run a clearly labeled broad WDI fallback prototype until product data are acquired and manifested.

Updated gate:

1. Launch a local treatment-subtype implementation lane.
2. In parallel, acquire or build a product-level trade source.
3. Keep bespoke scoring blocked until both are done.

### Wave 2A - Treatment Subtype Builder

Goal: create a coded subtype layer before rerunning.

Write scope:

- New audit/design artifact under `engine/audits/`
- New derived treatment draft under `data/derived/` or equivalent only after approval of the schema
- No scoreboard edits

Tasks:

1. Define the subtype schema:
   - `resource_statist_socialist`
   - `resource_developmentalist`
   - `market_open_resource_peer`
   - `rule_bound_resource_manager`
   - `resource_nationalisation_shock`
   - `mixed`
   - `uncoded`
2. Convert the treatment inventory into a subtype review queue with confidence, evidence note, active years, and episode boundaries.
3. Preserve `uncoded` and exclude it from clean comparator models.
4. Split the highest-impact umbrella windows first: Kuwait, UAE, PNG, Iran, Nigeria, Venezuela, Saudi Arabia, Indonesia, Malaysia, Syria, Zaire/DRC, China, Ethiopia, Rwanda, Vietnam.
5. Produce a candidate coded panel and coverage report before any result-card overwrite.

### Wave 2B - Product Export Measurement Builder

Goal: replace the broad WDI proxy with product-level export concentration where feasible.

Write scope:

- New measurement audit under `engine/audits/`
- New derived vintage only if the source data is present or fetch authorization is granted

Tasks:

1. Search for local BACI HS6, UN Comtrade, UNCTAD concentration, or WITS product-level data.
2. If product lines exist, build exporter-year HHI, Theil, top-product shares, product count, commodity share, and manufacturing export share.
3. If product lines do not exist locally, produce a fetch/install checklist and keep the WDI proxy clearly labeled as broad-sector only.
4. Record coverage by treated subtype and comparator subtype.

### Wave 2C - Bespoke Replication Prototype

Goal: prepare, but do not score, the correct multi-outcome design.

Write scope:

- Prototype script or notebook only after Wave 2A and 2B define inputs
- New run outputs in a separate scratch or versioned run directory until approved

Tasks:

1. Estimate separate outcome families: product export concentration, TFP growth, manufacturing share, early capital-formation channel.
2. Report control ladders and sample ladders.
3. Include lead/lag/cumulative exposure tables.
4. Compare against explicit market-open and rule-bound resource peers.
5. Emit diagnostics classification: `scoreboard_candidate`, `directional_partial`, `research_only`, `hold_repair`, or `failed_design`.

### Wave 2D - Provenance Repair

Goal: make any future rerun auditable.

Write scope:

- New or refreshed `manifest.yaml` and `evidence_packet.yaml` only after a hardened run exists

Tasks:

1. Pin every input vintage path and hash.
2. Record hypothesis hash, runner hash, model sample, row counts, and output artifact hashes.
3. Explicitly state whether the run uses product-level export data or the broad WDI proxy.
4. Mark any old packet as superseded rather than silently overwriting the audit trail.

## Recommended Work Order

1. Launch Wave 2A and 2B in parallel.
2. Keep Wave 2C blocked until both subtype coding and export-product measurement status are known.
3. Run Wave 2D only after a hardened run exists.
4. Keep the current `PARTIAL` result in research-only status during the repair.

## Bottom Line

The swarm should not attack this diagnosis by trying to squeeze a stronger verdict out of the current generic panel. The correct attack is to sharpen the treatment, separate real comparator categories, replace the broad export proxy with product concentration, then rerun a bespoke multi-outcome design with transparent provenance.
