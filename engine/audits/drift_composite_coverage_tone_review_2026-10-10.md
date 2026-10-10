# Drift composite coverage and movement-tone review — 2026-10-10

The national movement-coded drift window remains **1846–2026** across 145
countries and 21 axes. This is an authored-decision series, not an annual
observed policy-level panel. The 1846 United Kingdom Corn Law movement is its
earliest dated national input; no earlier dated national movement or policy
was found in the authored corpus. The numeric country/axis and composite
trajectories in `data/derived/country_drift.csv` are byte-for-byte unchanged
by this display repair.

## Composite coverage boundary

The previous chart and recent-slope calculation began at the country's first
movement year even if that movement had no valenced axis step. This drew
false flat-zero years for records such as Croatia, whose authored steps are
currently unvalenced or mixed, and Bahrain, which has movement text but no
scored axis. `composite_first_year` now records the earliest
nonzero contribution on one of the 14 pro-state/pro-market axes. Opposing
steps at the same date still establish coding coverage even when their net
composite is zero. The charts, country pages, and leaderboard mask years
before that boundary and omit a composite when the boundary is absent.

**141 countries have a coded composite; four movement countries do not:**
`BHR`, `GAB`, `HRV`, and `SGP`. Their country pages retain the authored
movement timeline without inventing a zero composite or recent slope.
Per-axis charts continue to use their own `axis_first_year` metadata.

## Tone labels, separate from drift scores

The old tone heuristic tagged a movement `auth` whenever `military` occurred
anywhere in coalition or doctrine, including ordinary defence policy and
mentions of a prior regime. It also matched `coup` inside unrelated words
such as *coupled* and *coupons*, and treated parliamentary `single-party
majority/minority` or prosecution of a previous junta as current-regime
evidence. A first-pass comparison found 82 `auth`-to-other candidate changes;
each was reviewed against the authored movement text before regeneration.

The accepted correction removes **66 false `auth` triggers**. A bare
`military` mention no longer sets regime tone; current military-rule
phrases in the governing coalition and reviewed explicit regime cases still
do. Strong terms use whole-word matching. Twenty-nine reviewed text exceptions
cover parliamentary and historical/opposition references. Eight demotions
were reversed because the authored current-regime description supported the
prior label; another eight borderline cases retain the prior label **pending
a separate regime criterion and source review**. These latter holds must not
be read as newly verified classifications. The derived national log now has
118 `auth` labels, down from 184. Finland's Marin, Germany's Merkel, and the
United States' Biden movement no longer receive an authoritarian tag from
their defence-policy descriptions; junta movements such as Argentina's
Proceso and Ethiopia's Derg remain tagged.

Tone is a display annotation on authored movement descriptions. It does not
change `statist_drift`, policy axes, hypothesis verdicts, causal claims, or
school scores. The Python generator and web classifier use the same rule and
reviewed ID sets. Focused drift and policy tests, the generated-output check,
eight web tests, TypeScript type checking, and the static site build passed
in this isolated checkout. This is local review evidence, not deployment.
