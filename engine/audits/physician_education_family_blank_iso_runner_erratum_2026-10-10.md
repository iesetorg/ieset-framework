# Frozen-runner implementation correction: blank WDI aggregate codes

The first post-lock run loaded the selected WDI columns but aborted **before constructing eligible country rows or estimating either model**. Each selected WDI endpoint has five rows with blank `country_iso3`; the frozen runner applied duplicate-key detection before filtering to the preregistered ISO3 country rosters. A key-only check confirmed that the nonblank eligible country codes had no duplicate country-year keys.

This correction filters WDI rows to the **already frozen union of the two source-key rosters** before duplicate-key detection. It changes no raw source bytes, selected year, inclusion rule, sample floor, transformation, estimator, threshold, multiplicity denominator or run artifact format. The revised runner's Git chronology check verifies that every top-level definition other than this loader and the custody check is AST-identical to the registration commit, and that this commit changes only the runner and this erratum. The registration and source lock remain earlier commits.

No country value, missingness count, model estimate, or verdict was inspected by the agent before this correction. The failed process read the `value` column into memory and stopped at the source-key assertion; that access is disclosed here rather than described as a wholly pre-value edit.
