# Result review: national safe WASH services and later under-five mortality

The blind registration is `894db0974d94d65881ef42040160c12beaf2fefd`.
The later exact source lock is `026cc38a58ef180a941edec8bbdcbbef9c270cfd`.
The runner opened WDI under-five mortality values only after checking both
commits and all raw/manifest hashes. Exact replay passed with
`python3 scripts/run_wash_child_mortality_2026.py --verify --source-root <local raw cache>`.

| Registered exposure | Frozen result | Complete rows / countries | Coefficient, log mortality change per +1 service pp | Two-sided p | Publication |
| --- | --- | ---: | ---: | ---: | --- |
| Safely managed drinking water | **PARTIAL** | 670 / 136 | −0.00336457 | 0.264010 | Public descriptive calibration, subject to source-rights review |
| Safely managed sanitation | **INCONCLUSIVE** | 669 / 136 | Withheld by frozen influence gate | Not reported | Archive |

For drinking water, 26 of 696 key rows lacked valid mortality triples; all
670 remaining rows across 136 countries passed the minimum sample and support
gates. The residualized-exposure shares were 24.50% in the top 1% of rows,
13.93% in the leading country, and 31.53% in the leading anchor. Each is below
its registered cap of 25%, 15%, and 35%. The slope is directionally negative,
but two-sided `p=0.264010` does not pass the family threshold `0.005`. The
family-adjusted 99.5% interval is `[−0.0119255,+0.00519631]`. An independent
matrix OLS and country-cluster CR1 calculation reproduced the coefficient and
standard error (`0.00299971`). The record supports calibration of the weak
historical association, not the prespecified directional hypothesis.

For sanitation, 14 of 683 key rows lacked valid mortality triples; sample and
support floors passed. Residualized exposure weight was 46.94% in the top 1%
of rows, 24.59% in one country, and 49.85% in one anchor. All exceed their
registered caps. The frozen protocol therefore withholds a coefficient and
archives the result as inconclusive; an attractive unguarded slope cannot be
used to rehabilitate it.

These two correlated tests belong to one retrospective descriptive family.
Neither identifies a causal WASH effect, a policy or school impact, or an
independent replication. WHO/JMP service access and UN IGME child mortality
are modeled estimates; co-development, health care, vaccination, nutrition,
fertility, conflict, and reporting changes remain live explanations. Both
records carry zero causal, policy, school, position, and featured credit. The
WHO manifest records a noncommercial share-alike license; verify rights before
putting derived displays on a public service.
