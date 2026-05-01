# Coverage Growth Plan

_Generated from local audits on 2026-04-30._

## Current Surface

- Hypothesis runnability: `582` audited specs; `344` READY, `213` NEEDS_DATA, `25` NEEDS_TEMPLATE, `25` LEGACY_SCHEMA, `569` already have run directories.
- Inconclusive run load: `185` inconclusive diagnostics remain. Largest templates: `panel_fe` (`44`), `synth_did` (`24`), `did_callaway_santanna` (`19`), `descriptive` (`19`), `event_study` (`15`), `panel_fe_decomposition` (`12`), `local_projections` (`11`).
- Inconclusive reasons: preflight missing loaded variable (`59`), insufficient observations (`49`), other inconclusive (`38`), missing series other (`21`), spec-shape / stub / sample problems (`16` combined).
- Movement coverage: current-year country coverage is complete; the frontier is not "missing countries", it is movements without positions and positions without tested hypotheses.
- Claim linkage: `1101` position-claim-to-hypothesis links; `1036` PASS (`94.1%`), `3` REVIEW, `62` FAIL. The failures are mostly era, geography, outcome, and named-policy scope mismatches.
- Historical floor: `625` movements and `3029` policies exist. Only `14` movements and `68` policies begin by 1945, so the 1900-1945 backfill is still thin outside the major anchors.

## Biggest Data Levers

1. OECD bridge or fetcher: machine audit now shows `oecd` blocking `126` NEEDS_DATA specs, including `97` solo unlocks. This is the single biggest direct runnability lever. Because OECD is SDMX/open/no-key, the practical issue is endpoint mapping, caching, rate handling, and local environment access.
2. Constructed-variable compiler: inconclusive diagnostics still mention `constructed` `123` times. A large share of these are not external data at all; they are policy/event/treatment dummies, windows, ratios, peer groups, and transformations that should be compiled from existing policies, movements, and loaded vintages.
3. Series alias and small targeted fetch wave: publishers exist locally but requested series are absent. Top series-level publishers are `ecb` (`27` mentions), `imf` (`17`), `bls` (`14`), `ilostat` (`13`), `eurostat` (`11`), `fred` (`11`), `bis` (`8`), `ons` (`8`), `boe` (`7`).
4. Stale WDI/FRED reruns: diagnostics still mention WDI/FRED blockers, but prior loader work reduced several true hard gaps. Run missing-publisher reruns after every fetcher/alias wave to distinguish real gaps from stale inconclusive cards.
5. Long-run historical substrate: Maddison, JST, V-Dem, Polity5, BIS, FRED historical, WID, NBER historical, PWT/manual drops are the right spine for 1900-1950. WDI starts at 1960, so it cannot carry the early-century backfill.

## Biggest Hypothesis Levers

1. Downscope broad panels: `249` large-scope specs are profiled, and the top unresolved cases often have `0` joint rows. Split them into single-country, bilateral, or compact peer-group specs rather than trying to satisfy 20-60 country panels.
2. Run the READY-not-run queue immediately: `industrial_policy_governance_capacity_conditionality`, `post_soviet_transition_institutional_variation`, and `norway_gpfg_resource_curse_avoidance`.
3. Convert banking-crisis legacy specs: `25` mostly regulatory banking-crisis specs are missing `estimator` and `falsification`. The fastest path is a canonical multi-metric checklist template with event-window metrics.
4. Attach school predictions to orphan hypotheses: `55` hypotheses have no school mapping, including many strong growth, labour, institutional, regulatory, energy, and distribution cases.
5. Attach positions to orphan movements: `195` movements have no position mapping (`152` draft, `43` candidate). These are a direct source of new claims and one or more compact testable hypotheses per movement.
6. Repair the `62` failing claim links: many are not data problems; they are scope bugs. High-repeat fixes include DDR/DEU vs DEE/DEW country aliases, Argentina 1945 vs 1950 period boundaries, named-policy tokens like NAFTA/Nixon/REACH/Gramm-Leach, and outcome tags that need broader hypothesis mappings.

## High-Scale Campaign Order

1. Fix audit truthfulness: patched `scripts/audit_runnability.py` so already-run but data-blocked specs count in the top-blocker tables. This makes the report reflect actual coverage pressure.
2. OECD campaign: implement SDMX URL catalog + cache + alias table for the common OECD labour, national-accounts, household-income, PMR, and tax datasets. Also bridge obvious OECD-only specs to ILOSTAT, Eurostat, WDI, FRED, or national sources when those satisfy the claim.
3. Constructed-variable campaign: add a compiler that materializes treatment/event variables from `policies/` and `movements/`, plus common transforms such as ratios, differences, lags, peer means, pre/post indicators, and crisis windows.
4. Downscope campaign: for each large unresolved panel with zero joint rows, create one narrow satisfiable spec and keep the original as a broad/meta version. This is the fastest way to increase tested count without lowering rigor.
5. Legacy-template campaign: convert the 25 banking-crisis legacy specs into canonical checklist specs, then run them.
6. Coverage-link campaign: map the 55 orphan hypotheses to schools and the 195 orphan movements to positions, then generate compact candidate specs from the highest-salience movement-policy claims.
7. Historical campaign: backfill 1900-1950 movements/policies for countries whose floor still starts late, using the long-run data spine rather than WDI.

## Immediate Next Runs

- `venv/bin/python scripts/audit_runnability.py`
- `venv/bin/python scripts/audit_inconclusive_load.py`
- `venv/bin/python scripts/run_inconclusive_campaign.py --help`
- `venv/bin/python scripts/rerun_missing_publisher_inconclusive.py world_bank_wdi`
- `venv/bin/python scripts/rerun_missing_publisher_inconclusive.py fred`
- `venv/bin/python scripts/rerun_missing_publisher_inconclusive.py oecd`
