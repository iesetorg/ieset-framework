# Steelman: euro-area distributional comparison, 2008 and 2014 EU-SILC waves

The strongest descriptive case is that the same five countries often called
the euro-area periphery had a less favorable lower-income distributional
change than the six fixed core countries between the observations labelled
2008 and 2014. A direct test asks whether the periphery's bottom-quintile
income-share change was at least 0.5 percentage points **lower** than the
core change and its relative-poverty-rate change at least 2.0 points **higher**.
The thresholds are 0.5 and 2.0 percentage points in the respective
periphery-minus-core changes, required jointly. Both are changes in percentage
points, not percentage changes. Countries are equally weighted within each
fixed group. The rule can clear even if both groups improve in absolute terms.

The old `eurozone_austerity_distributional_incidence` run was inconclusive
because its required poverty series was absent. Its 2008 and 2014 survey-wave endpoints
and country grouping were known before this new design. The new data are
directer distributional measures, but they are neither a new time window nor
an independent prospective replication of the old claim. In particular,
`ilc_di01` QU1/SHARE/EUR is an income **share** rather than bottom-quintile
mean real income; `ilc_li02` PC/LI_R_M60/T/TOTAL measures a **relative**
low-income rate, not absolute poverty.

Eurostat's [EU-SILC metadata](https://ec.europa.eu/eurostat/cache/metadata/en/ilc_sieusilc.htm)
labels these as survey years. The income observations ordinarily refer to the
previous calendar year (2007 and 2013 for these two waves), while Ireland
then used a rolling 12 months before interview. This is a difference between
two labelled survey-wave observations, not a literal 2008-to-2014 income-year
change. The source vintages also lack Eurostat JSON-stat observation status
flags because the local fetcher did not preserve them. No selected flags were
inspected; finite 0–100 values cannot establish break-free or unflagged
comparability across waves.

A worse periphery gap could arise from unemployment, wages, taxation,
transfers, migration, national median movements, survey changes, or other
crisis differences. No registered narrative fiscal shock is present, and the
core is not an identified counterfactual. A jointly favorable result cannot
credit austerity or prove alternative tax measures would have avoided harm.
Conversely, opposite gaps would refute this narrow two-measure description,
not every austerity mechanism or the longer-run history. Mixed, small, or
one-sided complete gaps are PARTIAL.

Every one of the 22 exact country-wave keys in **each** pinned series must
have a unique finite 0–100 value. A structural row can contain no usable
value. Any missing or invalid endpoint makes the comparison INCONCLUSIVE;
there is no post-hoc country drop, survey-wave shift, imputation, or substitute
series. The two outcomes use EU-SILC and may share revisions or survey errors.
This test is descriptive calibration only, with no automatic school-claim or
scoreboard credit.
