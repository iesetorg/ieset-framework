# Steelman: remittance share and next-year male prime-age participation

## Registered question

In a fixed 148-country/economy roster outside the old 13-country fit, is a one-percentage-point-higher World Bank personal-remittances-received share of GDP in year *t* associated with a meaningfully lower ILO-modelled male age-25-to-54 labour-force participation **level** in exact year *t+1*? The sole primary fit uses treatment years 2000–2022, outcome years 2001–2023, real PPP GDP per capita and fertility at *t*, country/economy and treatment-year effects, and country-clustered uncertainty. The preregistered meaningful-negative effect is at most −0.2 percentage points of participation per percentage point of remittance share, with a two-sided eight-slot Bonferroni cutoff of 0.00625. There is no post-result alternate outcome.

## Why the negative association could be real

Remittances can relax a household income constraint. Some working-age men may spend more time in education, caregiving, job search, or self-employment outside measured labour-force activity, and some households may hold out for better jobs. A one-year lag permits adjustment. Country effects remove stable area differences; year effects remove common global shocks; the two controls address broad income and demographic covariation. A broad, fixed out-of-old-sample roster checks whether the original sign appears beyond the old migrant-corridor countries.

## Strong opposing account

Weak local employment may induce migration and remittances, so causation can run from labour markets to remittance receipts. Remittance share can rise when GDP falls even with unchanged transfers. Commodity shocks, exchange rates, conflict, structural change, migration selection, and country-specific trends can affect both variables. A country/year-effects model and two controls do not remove these confounders. The outcome is an ILO **modelled estimate**, not a direct survey count. ILO's model can itself use macroeconomic inputs, including World Bank/IMF indicators, so source-family and model-input dependence further limits independence. The annual series includes revisions and projections; this primary design stops at 2023, but earlier data can still be imputed or revised. The supplied `obs_status` codes blank and `R` are counted without assigning undocumented meanings.

## Historical integrity boundary

The archived `demo_remittance_corridor_dependency` result remains **PARTIAL**: 312 fitted rows across 13 countries, coefficient +0.079581 and p=0.380169. Its historical `run_panel_fe.py` normalized the ILO file to country/year/value and averaged multiple sex and age rows before fitting. Thus that card did **not** measure the specified male age-25-to-54 endpoint. This new ID repairs the endpoint by selecting physical indicator `EAP_2WAP_SEX_AGE_RT`, `SEX_M`, and `AGE_AGGREGATE_Y25-54` from the pinned `_A` annual file, and excludes all 13 old fitted countries. The old result is not adopted, rewritten, or treated as an unseen comparator.

## Frozen adjudication and limits

The 148-area roster was selected using only exact-year country keys, categorical ILO dimensions/status/source codes, and Arrow value null masks across four pinned files; the null-mask envelope is 3,220 pairs. Registration requires at least 500 fully valid pairs, 40 retained areas, and eight years per retained area. An unidentified or nonfinite primary estimate is `INCONCLUSIVE`. With an estimable model, `SUPPORTED` requires a coefficient ≤−0.2 and two-sided p≤0.00625; `REFUTED` requires the lower end of its 99.375% cluster interval to exceed −0.2; all other cases are `PARTIAL`. This is a descriptive calibration result only. It cannot validate the old household-smoothing, reservation-wage, migration, Dutch-disease, policy, or causal story, and earns no school, welfare, or policy-score credit. One slot is reserved in an eight-group simple-pair screen; that conservative cutoff does not cure selection across the wider archive.

Source definitions: [ILOSTAT data catalogue](https://ilostat.ilo.org/data/) and [ILO modelled-estimate methods](https://ilostat.ilo.org/dataviz/weso/); all actual input bytes and manifest hashes are frozen in the specification.
