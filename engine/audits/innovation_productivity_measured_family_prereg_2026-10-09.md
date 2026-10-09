# Innovation, manufacturing productivity, and export mix: prospective measured family

This is a **two-test descriptive calibration family**, fixed before the candidate
numeric values or their null masks were opened. The 1995–2021 treatment years,
the 38 ISO3 countries listed in each specification, exact source dimensions,
three-year outcomes, exclusions, model, floors, and two-sided family rule are
frozen in the first-addition registration commit. Both results, including
contrary or data-limited outcomes, must be retained. No result earns causal,
policy-effect, position, featured, or school-score credit.

## Distinct primary claims

1. `resident_patents_manufacturing_productivity_forward_2026`: log(1 + WIPO
   resident patent applications per million people) in year t predicts a
   higher mean of OECD PDB manufacturing real GVA per hour growth in t+1,
   t+2, and t+3. The current-year PDB growth rate is a fixed control.
2. `manufacturing_productivity_hightech_export_mix_forward_2026`: OECD PDB
   manufacturing real GVA per hour growth in t predicts a higher WDI
   high-technology share of manufactured exports in t+3 than in t. The
   year-t share is a fixed control. A share change is not growth in the
   dollar value or domestic content of high-technology exports.

Both tests use country and treatment-year fixed effects and country-clustered
normal-Wald uncertainty. A test requires at least five complete treatment
years per country, 400 complete country-years, 20 countries, and 15 countries
with nontrivial within-country treatment variation (>1e-10 range). Values
must be finite. Patents must be nonnegative, population positive, and export
shares between 0 and 100. No imputation, substituted country, indicator,
year, source vintage, covariate, horizon, or estimator is permitted after
registration. Rank-deficient or nonfinite fits are INCONCLUSIVE. Positive
coefficients at two-sided p<=0.05/2=0.025 are SUPPORTED, negative coefficients
at that same cutoff are REFUTED, and other estimable results are PARTIAL. Both
fixed tests remain in the family denominator whatever their results.

## Source-key preflight and custody

The pre-registration check read only column schemas, exact dimension labels,
country/year keys, tracked fetch manifests, and SHA-256 bytes. It did **not**
read measured values, null masks, signs, coefficients, or outcomes for either
candidate. The country/year upper envelopes for 1995–2021 are 914 pairs / 38
countries for the patent-to-productivity test and 921 / 38 for the
productivity-to-export-share test; all 38 have at least five paired key years.
These are **not** complete-case counts or expected verdicts.

| Source | Exact selected vintage | SHA-256 | Tracked fetch manifest |
| --- | --- | --- | --- |
| OECD PDB | `data/vintages/oecd/DSD_PDB@2026-05-19T094612Z.parquet` | `3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c` | `data/manifests/fetch_run_2026-05-19T095056Z.yaml` |
| WIPO patent applications, resident | `data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet` | `8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e` | same OECD/WIPO fetch manifest |
| WDI population | `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet` | `6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| WDI high-tech export share | `data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet` | `b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994` | same WDI fetch manifest |

The exact PDB slice is annual `MEASURE=GVAHRS`, `ACTIVITY=C`, `UNIT_MEASURE=XDC_H`,
`PRICE_BASE=LR`, `TRANSFORMATION=GY`, `ASSET_CODE=_Z`, and
`CONVERSION_TYPE=_Z`. This is manufacturing real GVA per hour growth, not
aggregate TFP or an R&D measure. The WIPO parquet is a WIPO-origin indicator
transported through the World Bank API; it is not a separate WIPO download or
independent replication of WDI transport. The two raw PDB/WIPO files must be
copied from the main checkout with matching SHA-256 into this isolated
checkout after the registration commit, then a separate committed source lock
must precede any measured-value read.

## Semantic overlap and interpretation

The old same-commit `wipo_patent_applications_hightech_export_followthrough_panel`
used resident patent counts against high-tech export **value**. Its old result
and the later strict `resident_patents_hightech_exports_growth_holdout_v2`
were visible before this design. Neither tested OECD PDB manufacturing GVA
per hour. Existing strict high-tech-share tests used CEPII, WDI/WGI, tariffs,
or other predictors, not this exact PDB manufacturing productivity measure.
A repository source-pair scan found no previous registered test of either
exact pair here; that scan is not a claim of independent data. Related
innovation and trade outcomes, overlapping countries, and the shared PDB
measure are disclosed. These two tests are **not** replications of one another
or a mediation/causal chain.

Patent intensity can reflect filing rules, sector mix, and economic cycles;
manufacturing productivity can move through hours or demand; high-tech export
share can increase when other manufactured exports fall. Country and year
effects plus forward timing do not identify an effect. Results receive
descriptive calibration at most after strict registration, source, estimator,
replay, correction, and evidence-tier audits. No old result or school link is
inherited.
