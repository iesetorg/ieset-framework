# Remittance changes, secondary enrolment, and formal entry: prospective registration

This fixes **two descriptive calibrations before reading either selected outcome**.
The registration commit must contain this audit, both v1 specifications,
both steelmen, the fixed key roster, guarded runner, and its synthetic tests.
A later, separate commit must add only the runner's narrow source lock. Only
after those commits may the runner read the selected enrolment or registration
value, validity/null mask, or observation-status columns. Keep both tests,
including missing, contrary, or inconclusive results, in the denominator.
Neither can earn causal, policy, school, position, or featured credit.

## Questions and data meanings

1. Does a larger change in World Bank personal remittances **received as a
   percentage of GDP** from year t-1 to t predict a higher change in UNESCO
   UIS secondary **gross enrolment ratio** from t to t+2? This is a
   percentage-point ratio change, not completed education, learning, or the
   number of children enrolled. Gross enrolment counts students of any age
   against the official secondary-school-age population and can exceed 100.
2. Does the same remittance-share change predict higher growth in
   log(1 + the number of newly registered limited-liability firms) from t to
   t+1? A zero count is valid. This is the World Bank Entrepreneurship
   Database's formal limited-liability registration count, not all startups,
   active enterprises, informal firms, jobs, or a business-formation rate.

The two endpoints test household human-capital allocation and formal entry,
not interchangeable measures of one outcome. Earlier IESET remittance
studies use shock-year consumption/GDP resilience or male prime-age labour
participation; no exact remittance-to-either-endpoint pair was found in the
canonical specifications. Earlier governance tests use the enrolment source,
and the OECD-tax family uses the registrations source. Reusing source
vintages and country-years is disclosed and does **not** create independent
replication or archive-wide multiplicity control.

Source definitions: [World Bank personal remittances](https://data.worldbank.org/indicator/BX.TRF.PWKR.DT.GD.ZS),
[UNESCO UIS gross-enrolment ratio](https://uis.unesco.org/en/glossary-term/gross-enrolment-ratio),
and [World Bank formal registration limitations](https://databank.worldbank.org/metadataglossary/jobs/series/IC.BUS.NREG).

## Frozen raw custody

Only the following exact local vintages and their tracked fetch manifests may
be used. The fetch manifests stay in their existing tracked locations; the
source lock copies only a narrow list of these exact entries, with relative
paths and SHA-256 digests.

| Role | Preserved parquet | SHA-256 | Tracked fetch manifest; SHA-256 |
| --- | --- | --- | --- |
| Exposure | `data/vintages/world_bank_wdi/BX.TRF.PWKR.DT.GD.ZS@2026-04-30T114721Z.parquet` | `9139bffa26cd6f78bf8a963400e703398b9d59919bb92ab0b2ec2b7e04885b1d` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml`; `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |
| School outcome | `data/vintages/world_bank_wdi/SE.SEC.ENRR@2026-05-05T204008Z.parquet` | `787f29eb93204dbf11dd408449910c28b523376c054734f1fc68d4215b7b2044` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml`; `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| Entry outcome | `data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet` | `213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae` | same 2026-05-05T210519Z manifest |
| Income control | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml`; `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| Real-growth control | `data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet` | `db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58` | same 2026-05-05T200056Z manifest |

Each physical WDI parquet has `country_iso3`, `indicator_id`, `year`,
`value`, and `obs_status` fields. The two selected outcome parquets were
opened **only** for `country_iso3`, `indicator_id`, and `year`; byte hashes
and tracked manifest metadata were checked. Neither selected `value`,
validity/null mask, nor `obs_status` was inspected. Treatment and both
prespecified GDP-control values were opened to fix the exposure roster and
sample feasibility. No coefficient, outcome sign, or complete-case count was
used to choose this design.

## Fixed roster and exposure screen

`data/pinned_evidence/remittance_schooling_entry_family_2026_key_roster.csv`
has SHA-256
`f7358d7c138542807b3ff8789c3e95f31a1efb9b82d8d3033e68a7c64467cc58`.
It fixes **2,744** treatment-year keys in **180** named countries/economies
from 2006 through 2021. Construction used ISO3 country/economy codes that
also occur in the WDI files, never regional or income-group aggregates.
Each key has exact remittance years t-1 and t, positive real GDP per person
and finite real GDP growth at t, exact outcome **keys** at t/t+2 or t/t+1,
and at least five treatment/control candidate years in its country. The raw
WDI outcome files have a synthetic calendar grid; key presence says nothing
about an observed outcome. Each selected file has 11,880 country/year keys
within the 180-country roster, an upper envelope rather than a usable sample.

Personal remittance shares must be finite and nonnegative at both exposure
years. Preserve their full valid changes, including large changes and zeros.
The pre-outcome treatment/control screen found 215 increases of at least one
GDP percentage point (80 countries) and 169 decreases of at least one point
(64 countries). The annual-change median is -0.001 pp; the 1st and 99th
percentiles are -3.374 and +4.492 pp. Among changes with absolute magnitude
at least one point, the top raw squared-exposure contributions were Tajikistan
13.74% and Liberia 12.76%. These are treatment-only diagnostics; the required
post-complete-case **residualized** concentration gate is separate.

## Locked estimator and decision rule

For each endpoint, keep finite nonnegative measured values at the two exact
years only when both WDI observation-status fields are blank. Do not cap
gross enrolment at 100; retain zero registrations with log1p. Require at
least five complete pairs per retained country, **300** complete pairs,
**30** countries, and **20** countries with at least one retained treatment
year having absolute remittance-share change at least one GDP point. All
otherwise valid large exposure or outcome changes remain; no trimming,
winsorization, imputation, replacement years, substituted source, or
post-outcome subgroup selection.

For t in 2006-2021, fit exactly once per endpoint:

`outcome_change(c,t) = country_FE(c) + treatment_year_FE(t) + beta * delta_remittance_share(c,t) + baseline_outcome(c,t) + log(real_GDPpc(c,t)) + real_GDP_growth(c,t) + error(c,t)`.

The school outcome is the t-to-t+2 ratio change in percentage points, with
the t ratio as its baseline control. Formal entry is
`log1p(count(t+1)) - log1p(count(t))`, with `log1p(count(t))` as the baseline
control. Use full-rank OLS, country-cluster CR1 covariance, and a two-sided
Student t reference with retained country count minus one degrees of freedom.
Residualize remittance change on **all other** model columns, including both
fixed effects and baseline outcome; if any country supplies more than **30%**
of its residual sum of squares, mark the test INCONCLUSIVE. Nonfinite or
nonpositive cluster uncertainty is also INCONCLUSIVE.

The two-sided family alpha is **0.01**, allocated equally to these two fixed
tests: each directional verdict needs p <= **0.005**. A school beta of at
least **+0.2 enrolment-ratio percentage points** per +1 GDP percentage point
remittance change is SUPPORTED at that p; a beta at most -0.2 is REFUTED.
For formal entry, replace 0.2 with **0.02 log point** in the same rule.
Every other estimable result is PARTIAL. A failed source, chronology, sample,
variation, concentration, rank, or inference gate is INCONCLUSIVE. Both
cases stay in the family even if either fails. This correction applies only
to the two newly registered tests.

## Interpretation and release boundary

Remittances include personal transfers and compensation of some nonresident
workers. The GDP-share denominator can jump in downturns. Migration
selection, recipient resources, destination-country cycles, local schooling
policy, registry digitization, and legal-form substitution can jointly move
exposure and outcomes. Fixed effects and forward timing do not remove these
threats. Gross enrolment can rise through over-age enrolment or repetition
without completion; registrations can rise while operating firms do not.

No result is a causal remittance effect, government-policy effect, school
score, welfare estimate, or featured finding. Publish only the exact
reviewed descriptive verdict and its data limitations after strict
registration, source-lock chronology, result replay, integrity, and evidence
audits. Do not use this prospective family to relabel an older archived
same-commit study.
