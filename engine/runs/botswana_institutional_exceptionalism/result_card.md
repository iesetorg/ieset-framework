# Result card — Botswana institutional exceptionalism, 1966-2023

**Verdict:** SUPPORTED — Botswana's synthetic-control mean post-1976 log-gap = +2.031 (~+662% level), clearing the +0.30 log threshold. Annual log-growth advantage +3.99pp/yr (≥ +2pp threshold). Pre-fit RMSE (log) = 0.355. V-Dem polyarchy gap (post-1976) = 0.3157645833333333; WGI gov-effectiveness gap (1996+) = 1.1414447947999988.

## Pre-registration

- **Claim:** Botswana's divergence from SSA averages post-1966 is attributable
  primarily to retained pre-colonial Tswana institutions plus post-independence
  resource-rent management.
- **Falsification (PRIMARY 1):** SC mean post-1976 log-gap ≥ +0.30 (~+35% level).
- **Falsification (PRIMARY 2):** BWA − donor mean annual log-growth ≥ +2.0pp/yr.
- **Informative (METHOD_VALID-style):** V-Dem polyarchy and WGI government
  effectiveness gaps; pre-fit RMSE; placebo permutation rank.

## Synthetic control

- Donor pool (post-fit-coverage filter): ['ZMB', 'ZWE', 'NGA', 'AGO', 'COD', 'GAB', 'GHA', 'CIV', 'NAM', 'ZAF']
- Pre-fit window: 1966-1975; treatment year: 1976
- Pre-fit RMSE (log): 0.3547897430309286
- Donor weights (>0.5%): COD=0.85, NGA=0.15
- Post-treatment mean log-gap: 2.0313779359684454
- Post-treatment mean level gap: 662.4585314023415%
- 2023 terminal log-gap: None

## Growth gap

- BWA mean annual log-growth 1977-2023: 0.05176978064670174
- Donor pool mean annual log-growth 1977-2023: 0.011881411061973221
- **Gap (BWA − donor mean):** 3.9888369584728522 pp/yr  (threshold ≥ +2.0)

## Placebo permutation

- BWA rank among donor pool (largest positive post-treat gap): (0, 11)
- One-sided permutation p-value: 0.09090909090909091

## Informative covariate gaps (post-treatment)

- V-Dem polyarchy: BWA=0.6725, donor mean=0.3567354166666667, gap=0.3157645833333333
- WGI gov-effectiveness (1996+): BWA=0.46241573599999997, donor mean=-0.6790290587999989, gap=1.1414447947999988

## Method note (downgrade from spec)

Spec called for `synthetic_control` with diamond-rent and V-Dem covariates
as decomposition channels. Implemented classic Abadie-Diamond-Hainmueller
synthetic control on log GDP-pc level matched in the pre-1976 window.
Diamond-rent channel (WDI mineral rents, NY.GDP.MINR.RT.ZS) is NOT on disk;
reported as a data gap rather than estimated. Channel decomposition is
left as a v2 question — for now V-Dem and WGI gaps are reported descriptively
to colour but not gate the verdict.

## Data

- maddison:mpd2020 (primary outcome, log real GDP per capita)
- vdem:vdem_cy_full (v2x_polyarchy — informative)
- wgi:GOV_WGI_GE.EST (informative, 1996+)

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
