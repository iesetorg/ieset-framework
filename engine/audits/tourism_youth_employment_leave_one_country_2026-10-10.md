# Tourism–youth-employment leave-one-country review — 2026-10-10

This is an **exploratory post-result sensitivity check** on the frozen
two-test WDI entry/tourism to OECD youth-employment family. It was not part of
the preregistered decision rule and does not change either primary verdict.
The primary tourism estimate remains a descriptive `SUPPORTED` association
under its registered sample, practical-magnitude, and Bonferroni gates; it
has zero causal, policy, school, and featured credit.

After the registration commit `6a44ffa419e9f894bbecadfff2f8620ab9ef46d7`, source lock `208634557af960bc2675dd03fa9ef746e378ad8b`, and
measured result commit `57315d3b79f358c3b7189a4723851776309c7214`, the locked tourism panel was refit 50
times, each time omitting one of its 50 countries. Each refit used the same
country- and treatment-year-fixed-effects OLS formula, country-cluster CR1
standard errors, and a two-sided Student t test with G−1 degrees of freedom.
No alternate sample or outcome definition replaced the registered primary
test.

The coefficient stayed positive in all 50 refits, ranging from **+2.878 to
+3.741 youth-employment percentage points per log arrival change**. The
two-sided p values ranged from **0.00211 to 0.00807**; **46 of 50** refits
still met the primary family's per-test p≤0.005 cutoff. The four exceptions
were omitting Korea (p=0.00807), Slovakia (0.00588), Cyprus (0.00529), or
Croatia (0.00507). The result is directionally stable but its formal
family-threshold status is sensitive to four single-country omissions,
especially Korea. This check is post hoc and is not independent confirmation.

The source vintage has no WDI method-break flags for international arrivals.
Arrival trips are not unique visitors or jobs, and border counting methods
vary. The positive association does not establish that tourism caused youth
employment growth or that tourism policy would raise it.
