# Eurozone direct-measures quality decision — 2026-10-09

This decision is recorded **before** reading selected Eurostat outcome values
or their null masks for `eurozone_distribution_2008_2014_direct_measures_v2`.
The registered design is frozen in commit `f25373908ebace6ef640a439a37322bed1283416`.

The two local Parquets match tracked fetch manifests by series, source URL,
file path, and SHA-256. Their `value` rows can support a reproducible comparison
of the **published numeric observations** labelled as the 2008 and 2014
EU-SILC survey waves. The Eurostat fetcher did not preserve JSON-stat
observation `status` flags, the manifests contain no raw response or flag
hash, and no same-vintage flag cache was found. The quality status of each
selected observation is therefore **unknown**; source custody does not prove
that any cross-wave comparison is free of breaks, provisional values, or
reliability flags. `input_status: verified` in a complete future run means
only that the pinned numeric inputs passed hash and finite-value gates.

**Pre-result gate decision:** permit the frozen rule to produce at most a
descriptive **calibration** result about those pinned published numbers,
provided every one of the 44 registered values is valid and the exact replay
passes. Failed source, key, or value gates remain `INCONCLUSIVE`. A result
cannot establish an unqualified change in the underlying income distribution,
flag-clean comparability, an austerity effect, or school/scoreboard credit.
The 2008 and 2014 labels are survey waves; income usually refers to the
preceding calendar year, while Ireland used a rolling prior-12-month window.

Obtaining quality flags later would require a separately custodied source
vintage and a predeclared flag policy. It must not silently change the frozen
v2 rule or its current provenance boundary.
