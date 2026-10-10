# Result review: voice and accountability and later state-based conflict

Blind registration `d719bad1c94056ec9ccc5fe5db4593d064a12d8a` preceded
exact source lock `e14a0757c109a7df60975db8348cf749a8249b41`.
The frozen runner first projected the four OWID conflict count columns only
after verifying those commits and the pinned raw/manifest hashes.

**Verdict: PARTIAL public descriptive calibration.** All 939 registered
country/anchor windows across 188 countries had valid category counts for
the eight required years. The data include 232 future-conflict windows across
70 countries and 707 no-future-conflict windows across 162 countries, above
both predeclared floors. Material WGI voice rises occur in 88 windows/73
countries, and flat exposures in 233 windows/152 countries. Residualized
exposure weight is 14.40% in the top 1% of rows, 4.81% in the leading
country, and 29.05% in the leading anchor; all pass the frozen 25%, 15%,
and 35% caps.

The country/anchor fixed-effects linear probability slope is **−0.0728638**
future four-year conflict-incidence probability point per +1 WGI estimate
point (country-cluster CR1 standard error **0.0565997**, two-sided
`p=0.199562`). The prespecified directional gate required beta≤−0.15 and
`p≤0.01`. Its 99% interval is `[−0.220158,+0.0744298]`. The observed sign
is negative, but the claim is not supported. Independent matrix OLS and
country-cluster CR1 calculations reproduced the coefficient and standard
error. Exact artifact replay passed with
`python3 scripts/run_voice_conflict_2026.py --verify --source-root <local raw cache>`.

This is one retrospectively selected descriptive question, not a causal
effect of democracy, a specific reform, a movement, or a policy. WGI estimates
are perception based; OWID/UCDP records state-based conflicts under its
own threshold and excludes other violence. Peace may precede voice gains,
and transitions, repression, income, neighbors, and external intervention
remain confounders. The record has zero causal, policy, school, position,
and featured credit. The source manifests record CC BY; derived public
displays should cite WGI, OWID, and UCDP/PRIO.
