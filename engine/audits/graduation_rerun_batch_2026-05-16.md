# Graduation Rerun Batch - 2026-05-16

Queue source: `engine/audits/runnable_graduation_queue_2026-05-16.md`

Command pattern:

- Batch 1: `python3 scripts/rerun_preflight_ready_inconclusive.py --apply --limit 25 --force`
- Batch 2: explicit queue slice 26-50 through `scripts/rerun_preflight_ready_inconclusive.py::apply_reruns`
- Batch 3: explicit queue slice 51-66 through `scripts/rerun_preflight_ready_inconclusive.py::apply_reruns`

## Result

All 66 legitimate queued hypotheses were attempted.

| Outcome after rerun | Count |
| --- | ---: |
| Graduated to real verdict | 3 |
| Stayed inconclusive | 63 |
| Crashed | 0 |

Real verdicts produced:

| Hypothesis | Template | Verdict |
| --- | --- | --- |
| `nuclear_phaseout_accident_risk_reduction_value` | `descriptive` | `SUPPORTED` |
| `wto_accession_productivity_spillover_panel` | `event_study` | `PARTIAL` |
| `labour_market_reform_almp_complementarity_effect` | `panel_fe` | `SUPPORTED` |

## Batch Notes

Batch 1 attempted 25 candidates:

- Real verdicts: 2
- Stayed inconclusive: 23
- Crashes: 0

Batch 2 attempted 25 candidates:

- Real verdicts: 1
- Stayed inconclusive: 24
- Crashes: 0

Batch 3 attempted the remaining 16 legitimate queued candidates:

- Real verdicts: 0
- Stayed inconclusive: 16
- Crashes: 0

During Batch 3, a parser overshot the intended queue section and also passed five non-queue markdown bullets to the runner:

- `wits:export_product_hhi_wits`
- `data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet`
- `export_complexity_market_access_vs_subsidy`
- `consumer_choice_variety_trade_market_reform`
- `quality_adjusted_consumption_market_liberal_panel`

The two data-token entries returned `spec not found`. The three trade/product hypotheses were checked afterward; their run artifacts showed no git diff from the accidental pass.

## Blocker Breakdown For The 63 Still Inconclusive

| Blocker | Count |
| --- | ---: |
| Insufficient observations / listwise deletion | 23 |
| Insufficient pre-period coverage | 17 |
| Insufficient pre/post observations | 12 |
| No within-country treatment variation | 10 |
| Country not in panel | 1 |

## Interpretation

The preflight-ready queue was necessary but not sufficient. The data now load, but most of these specs still fail estimator-specific identification gates after filtering.

The highest-yield repair lane is not more blind rerunning. It is schema/design repair:

1. For `panel_fe` failures with no within-country variation, switch to event-study/synth-DiD designs, remove absorbed country-constant treatments, or change fixed effects.
2. For listwise-deletion failures, inspect which control is collapsing the sample and add sample ladders.
3. For synth-DiD failures, expand donor pools or use event/descriptive designs where pre-period coverage is structurally too thin.
4. For descriptive/event-study failures, adjust windows only if the preregistered event design permits it; otherwise leave inconclusive.

## Next Best Batch

The next runnable wave should target the 10 no-within-country-variation cases and the 23 listwise-deletion cases, because those are most likely repairable by design/lists rather than new external data.
