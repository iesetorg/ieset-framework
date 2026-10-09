# Business R&D and resident patent intensity: prospective registration

This is one new measured associational question, not a repair or relabeling of
an older run. Before this registration, the Eurostat business-R&D to tertiary
employment study was visible as PARTIAL (773 pairs/35 countries, p=0.507052).
Older WDI *total* R&D/patent candidate claims and WIPO-outcome studies also
exist. This study asks a narrower question: business-enterprise sector R&D
intensity at `t` versus the change in log(1 + resident patent applications per
million) from `t` to `t+3`. It does not provide a data-disjoint replication.

No numeric values or null masks in the proposed treatment or outcome were
opened to choose this design. The spec, steelman, runner, verifier, and plan
share one first-addition registration commit. A hash-checked source lock must
be committed separately before measured-column access, with results in a
third commit regardless of verdict. Exact replay recomputes and compares every
stored result artifact.

Eurostat `rd_e_gerdtot` is selected at `freq=A, sectperf=BES, unit=PC_GDP`.
The WIPO resident-application indicator `IP.PAT.RESD` was transported via the
World Bank API, so its custody is a WIPO-origin WDI mirror, not an independent
WIPO download. WDI `SP.POP.TOTL` supplies de facto population. All three raw
vintages are hash-pinned to tracked fetch manifests. Patent and population
levels at both endpoints require nonnegative/positive finite values and blank
or null observation-status codes; Eurostat's raw slice lacks retained flags.

The fixed roster is the 35 ISO3 countries in the spec and treatment years
1995–2021. Exact dimension/country/year keys give 826 possible pairs across
35 countries after five key years per country; values and flags may reduce
the sample. No imputation, country swap, or vintage switch is allowed. Require
at least 400 complete pairs, 25 countries, five complete years per retained
country, and 15 countries with within-country treatment variation. Estimate
one two-way country/year fixed-effect OLS coefficient on R&D share, with the
baseline log patent intensity as a fixed covariate and country-clustered
normal-Wald uncertainty. If the model is rank deficient or uncertainty is
nonfinite, report INCONCLUSIVE.

The earlier R&D outcome was screened at p≤0.01 and is now visible. This
selected second R&D screen uses a stricter two-sided p≤0.005, corresponding
to 0.01/2 for the two now known R&D outcomes. A positive coefficient crossing
that threshold SUPPORTS the narrow association; a negative crossing REFUTES;
every other estimable result is PARTIAL. This local guard does not retroactively
change the prior registration and does not establish error control across the
adaptive corpus search or older R&D/patent candidates. The result remains
descriptive calibration only, with zero causal, policy, position, featured,
and school-score credit.

| Role | Raw path | SHA-256 | Tracked manifest |
| --- | --- | --- | --- |
| Business R&D intensity | `data/vintages/eurostat/rd_e_gerdtot@2026-05-05T210242Z.parquet` | `fea284d7b17e31a3803749fca052f6a110ed1b8e703a9151964d1d15f58df152` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| Resident patent applications | `data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet` | `8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e` | `data/manifests/fetch_run_2026-05-19T095056Z.yaml` |
| WDI total population | `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet` | `6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |

Raw vintages are ignored by Git. Replay elsewhere requires recovering the
identical bytes. Filing practices, GDP and population denominators, reverse
timing, and common shocks limit interpretation.
