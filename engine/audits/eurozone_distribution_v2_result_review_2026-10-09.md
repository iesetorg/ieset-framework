# Eurozone direct-measures result review — 2026-10-09

The design for `eurozone_distribution_2008_2014_direct_measures_v2` was
first added in commit `f25373908ebace6ef640a439a37322bed1283416` with no run artifacts. A separate source-
quality interpretation ceiling was committed as `3dcd9de3a10aba6dff36b19d280aef17a9f45274` before the run.
Both pinned Eurostat files matched their tracked manifests. The run found
all 22 required country-wave values in each indicator, and its read-only
`--check` replay returned `verified=true`, `wrote_files=false` after comparing
the complete stored packet.

**Verdict: PARTIAL.** The five-country periphery minus six-country core
change in bottom-quintile income share was **−0.6933 percentage points**,
passing the registered ≤−0.5 threshold. The corresponding relative-poverty
rate gap was **+0.5333 percentage points**, short of the joint ≥+2.0
threshold. The opposite joint refutation rule also failed. The complete
result therefore supports neither registered joint directional claim.

This is inspectable **descriptive calibration of pinned published numeric
observations** only. The 2008 and 2014 labels denote survey waves; income
reference periods differ from the labels, including Ireland's rolling
12-month window. The stored vintage omits observation quality flags, so
break-free comparability is unverified. No austerity treatment, causal
effect, original-claim repair, or automatic school/scoreboard credit is
inferred. Public calibration eligibility remains conditional on the regular
registration and integrity audit gates.
