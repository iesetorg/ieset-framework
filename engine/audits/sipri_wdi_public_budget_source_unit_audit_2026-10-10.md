# SIPRI–WDI public-spending extension: first-pass unit audit

The two specifications, roster, preregistration note and runner were committed together at `f48625d261fb27fc81d327b24eae80a6b736deba` without reading selected values or null masks. The exact five-source lock followed at `26f07bd233911df4cf9192cad9a93393210744ae`. The first selected-value execution produced both saved run packets at `59c18d329e5ba49d4539ba0cb4f6ab6cf61849f3`; no coefficient, sign or directional inference was estimated in either cell.

| Frozen cell | Complete rows / countries | Raw-unit material rows / countries | Failed gates | Verdict |
| --- | ---: | ---: | --- | --- |
| Later government education expenditure/GDP share | 854 / 95 | 0 / 0 | Minimum 60 material rows and 20 material countries | INCONCLUSIVE |
| Later domestic government health expenditure/GDP share | 1,428 / 124 | 0 / 0 | Minimum 60 material rows and 20 material countries | INCONCLUSIVE |

The registered treatment, range and meaningful-effect units are **percentage points of GDP**. The source Parquet locked as `5ccce854cc3127eb0510b2f9f0e99741fb4a037a5950c745137970e7c618d3be` stores SIPRI's Share of GDP as **fractions**. For example, post-lock metadata diagnostics show its finite 2000–2016 median is approximately `0.015`; the registered unit would express this as approximately `1.5` percentage points. The frozen runner omitted that deterministic ×100 conversion, making the registered 0.25-point material-change floor effectively 25 percentage points. This is a source-unit implementation error, not evidence of no substantive military-burden changes. No frozen spec, lock, runner, threshold, source or measured packet was edited after the result.

Exact replay of these two **inconclusive first-pass packets** succeeds with `python3 scripts/run_sipri_wdi_public_budget_2026.py verify --source-root <local-source-root>` where `<local-source-root>` contains the ignored, hash-matched SIPRI and WDI Parquets. Raw source values remain ignored; only aggregate diagnostics are committed. These packets have zero causal, policy, school, position and featured credit. A later percentage-point repair, if pursued, needs a separately documented post-gate implementation and must retain these initial failures as audit evidence.

The source lock was committed once for the two-member family. The central
evidence reader now checks that shared lock, every original sibling packet,
and the registration→lock→run order before recognizing its **INCONCLUSIVE**
verdicts. This path accepts only inconclusive families and keeps both records
in the archive; it grants no public or school-score credit.

The related fixed-investment study has an already-committed post-lock unit adapter, `scripts/run_sipri_military_fixed_investment_2026_unit_fix.py`. Its saved PARTIAL packet replays through that adapter. Calling its original preregistration runner's `verify` directly compares unscaled first-pass calculations against the corrected packet and therefore fails; this is not by itself an integrity breach. The current public evidence ledger labels that older record `calibration` and `public_visible=true` with no school-score credit. Its post-gate repair and related limitations remain material to that interpretation.
