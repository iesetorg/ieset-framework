# Steelman: secondary enrolment and subsequent fertility

## Fixed measured prediction

In countries with at least two of the three frozen anchor windows, a larger
increase in gross secondary-school enrolment from `t−5` to `t` predicts a
larger proportional fall in total fertility from `t` to `t+10`. The sample
uses nonoverlapping fertility decades anchored in 1990, 2000, and 2010.
The directional claim requires beta at most −0.003 log fertility point per
+1 percentage point in gross enrolment and a two-sided country-cluster
`p≤0.01`. All null, opposite, and insufficient-data outcomes are retained.

The strongest plausible pathway is that more adolescents in secondary school
may reach adulthood with greater educational opportunity, later family
formation, or more choices about work and childbearing. A decade horizon is
closer to the transition from secondary school to prime childbearing ages
than an immediate one-year outcome. This is a prediction about a national
education proxy, not a female-specific or individual-level pathway.

## Strongest rival account

Gross enrolment includes pupils outside the official age range, can exceed
100%, and includes both sexes. It measures neither secondary completion nor
learning. The WDI fertility series is a modeled national estimate that may
combine censuses, surveys, and registers. Urbanization, contraception,
migration, changing child mortality, conflict, family policy, and general
income growth can move both series. Baseline fertility and real income,
country fixed effects, and common decade effects limit some confounding but
cannot identify an education effect. A national association cannot establish
which women attended school or why births changed.

The exact vintage and manifest hashes, exclusion caps, key roster, model,
country-cluster uncertainty, effect-size threshold, and fallback verdicts are
frozen before any selected fertility value or null is read. The source
has no useful cell-level break flag, so the result cannot be called
break-screened. A source or method-floor failure yields `INCONCLUSIVE`.

## Prior work and credit

The corpus already has education, labour, demographic-transition, and
fertility cases, including `child_family_benefits_female_lfp_fertility_panel`
and `demo_fertility_decline_growth_slowdown_panel`. A scan of authored
hypothesis YAML did not find the exact WDI `SE.SEC.ENRR` five-year change
against a following ten-year WDI `SP.DYN.TFRT.IN` change. The local
single-test p threshold does not adjust for archive-wide model selection.

Even a `SUPPORTED` verdict is descriptive calibration only. It receives
zero causal, policy, school-score, position, and featured credit.

Sources: [WDI gross secondary enrolment](https://data.worldbank.org/indicator/SE.SEC.ENRR),
[WDI total fertility](https://data.worldbank.org/indicator/SP.DYN.TFRT.IN),
[WDI real GDP per person](https://data.worldbank.org/indicator/NY.GDP.PCAP.KD).
