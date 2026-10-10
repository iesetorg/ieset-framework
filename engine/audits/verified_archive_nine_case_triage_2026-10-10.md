# Verified archive triage: nine cases, zero graduations

Date: 2026-10-10. Isolated branch `codex/verified-archive-triage-2026`, based on `c6737043e422f95f349f6ae2e7d6d789126f49bc`. This is a case-level review of the one verified archive whose only recorded exclusion was a missing replication path and the eight whose only recorded exclusion was a missing canonical verdict. **No original specification, threshold, run estimate, result card, or verdict was changed. No case earns public evidence or school/policy credit.**

## Tariff-duration claim: no-go despite the apparent single blocker

`tariff_protection_duration_growth_drag` was registered before its May 2 run. Its frozen treatment is *cumulative years with weighted-mean applied tariff above 15%*, with export growth and real household consumption per capita growth as joint primary outcomes. The saved generic panel run reports `protection_duration_decades` **missing**, fits the available current tariff level instead, and reports only the export-growth coefficient (-0.006557, p=0.717). It also lists export complexity, terms of trade, and product-diversification inputs as missing; the saved WDI consumption series is `NE.CON.PRVT.ZS`, not the registered real per-capita growth endpoint. Its `PARTIAL` label cannot satisfy the frozen requirement of a negative export coefficient at p<0.10, let alone the two-outcome and frontier-comparator tests. There is no source-pinned run manifest or valid exact-replay wrapper to restore the unmeasured estimand. Adding a wrapper would turn a misleading recorded sole blocker into public credit. The explicit public-evidence quarantine now records the claim mismatch; a separately preregistered source-backed run is required.

## Eight absent canonical verdicts

Each case has a verified pre-run registration, a local result card and diagnostics, and a source manifest. All 16 distinct pinned vintage files were present in the source checkout and matched their SHA-256 locks. The saved noncanonical labels describe genuinely blocked or weak results, rather than a lost `SUPPORTED`, `PARTIAL`, or `REFUTED` verdict. The existing canonical-verdict backfill deliberately rejects pending/status text. We retained that boundary.

| Archived case | Saved result vs frozen rule | Decision |
| --- | --- | --- |
| `bis_corporate_credit_boom_investment_slowdown_panel_1970_2025` | 2,607 observations, **14 countries vs minimum 20**; beta -0.00675, p=0.664 vs effect/p gates | Coverage and effect fail; remain `INCONCLUSIVE_DATA_PENDING`. |
| `bis_corporate_dsr_investment_slowdown_panel_1999_2025` | **364 vs 450 observations; 2 vs 15 countries**; beta -0.911, p=0.00213 | Positive estimate evidence in only two countries cannot override the frozen coverage floor. |
| `bis_credit_gap_private_investment_reversal_panel` | 3,147 observations, **14 vs 20 countries**; beta -1.553, p=0.00796 | Coverage fails despite directional estimate. |
| `bis_credit_gap_private_investment_slowdown_panel_1970_2025` | 3,147 observations, **14 vs 20 countries**; beta -1.553, p=0.00795 | Same underlying outcome/treatment screen and failed country floor; no second independent credit. |
| `bis_reer_volatility_investment_drag_panel_1964_2026` | 2,349 observations, **14 vs 20 countries**; beta +0.189, p=0.508 vs required negative | Coverage, direction and p gate fail. |
| `oecd_pdb_market_reform_productivity_compounder` | 31 countries; beta -1.827, p=0.198 vs expected positive at p<0.10 | Saved `REFUTED_OR_WEAK` combines weak/opposite results; it is not a canonical refutation. The 2018–24 growth average also overlaps the 2018–23 reform interval. |
| `oecd_pdb_public_sector_share_productivity_drag` | 31 countries; beta +3.489, p=0.647 vs expected negative at p<0.10 | Weak/opposite result; remain archived. |
| `oecd_pdb_tfp_growth_frontier_persistence_1970_2025` | 17 countries; beta -0.140, p=0.107 vs expected positive at p<0.10 | Weak/opposite result; remain archived. |

The five BIS legacy `replication.py` files previously invoked batch promotion writers, which could consult newer vintages and were not historical verification. They now call the existing read-only `replay_bis_pinned.replay_one` on their own archived manifests. The replay helper compares only fields actually stored in the original diagnostics: it **does not synthesize a canonical verdict** for these packets. Each of the five exact replays matched diagnostics, coefficients, charts, and result cards from the SHA-locked sources without changing packet hashes. The three OECD `reproduce_one` calls also passed exact pinned-source numerical comparison and left files untouched. Five targeted BIS replay tests passed. None of these path repairs changes evidence-tier eligibility.

Follow-up requires a new prospective design with adequate independent country coverage and claim-matched outcomes, or an independently verified contemporaneous run packet that genuinely passed the original fixed floors. Relabeling pending or weak text, lowering a country floor, or repairing the tariff wrapper alone is not eligible.
