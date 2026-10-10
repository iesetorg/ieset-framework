# FAOSTAT food-supply and nutrition family — preregistration

Frozen before any selected FAOSTAT `Value`, row `Flag`, or null pattern was read. The earlier source scan used only item names/codes, units, M49 identifiers, calendar labels and element labels from the preserved parquet. The ZIP header and separate flag codebook were inspected; no row flags were opened. This is a retrospective local family after many older IESET nutrition hypotheses and cannot claim an archive-wide prospective discovery guarantee.

## Source and identification boundary

- Source: FAOSTAT Suite of Food Security Indicators, 2026-04-29 ZIP preserved at `data/vintages/faostat/food_security@2026-05-02T212150Z.zip`, with a locally derived parquet key view. The exact source hash is recorded in a separate source-lock commit before any measurement. The original ZIP has one normalized CSV, area/item/element/flag codebooks. The derived parquet has no surviving fetch manifest; the runner consumes the raw ZIP directly.
- Official catalog: https://data.fao.org/catalog/dataset/955d6564-40a9-48b4-b51b-f19d65bb3539 ; FAO statistical database terms: https://www.fao.org/contact-us/terms/db-terms-of-use/en . Attribute FAO and upstream UNICEF, WHO and World Bank estimators in output.
- The FAO three-year food-supply indicator is average *availability*, not observed individual consumption. Child anthropometric prevalence and women’s anemia are external or modeled status measures. The item code selection avoids FAO undernourishment, which is partly constructed from dietary energy supply.
- Use M49 to ISO3 via the committed crosswalk; exclude unmapped codes and `BMU,COK,HKG,MAC,NCL,NIU,PYF,TWN` to avoid non-national or contested separately reported economies. This fixed selector is applied before values.

## Fixed design

- Eight theory-specific pathways below; no mechanical 5×4 exposure/outcome product. Every registered case remains in the local family denominator, including failed gates. They are correlated and must not be counted as independent experiments.
- Exposure windows are exactly 2000–02, 2005–07, 2010–12 and 2015–17, centered at anchors 2001, 2006, 2011 and 2016. Outcomes are the exact annual rates in 2005, 2010, 2015 and 2020, respectively. There is at least a three-year endpoint separation from the exposure window end.
- Country and anchor fixed-effect OLS. Country-cluster CR1 uncertainty; two-sided Student t(G−1). Only countries with two or more complete anchors enter. Model has no time-varying adjustment, so every estimate is descriptive and confounded.
- Source values require A/E/X flags, exact units, finite numbers and registered bounds. No imputation, winsorization, alternate anchor, alternate estimator, or source substitution.
- Case floors: ≥300 complete country-wave rows, ≥80 countries, ≥3 represented anchors, ≥20 countries spanning the exposure-specific material change, full rank and positive finite cluster SE. Residualized exposure contribution caps: one country ≤20%, one anchor ≤45%.
- Family alpha 0.01 with Bonferroni p≤0.00125 over all eight. Meaningful signed magnitude ≥0.25 outcome percentage point per registered exposure unit. Predicted sign + cutoff is SUPPORTED descriptive association; equally strong opposite sign is REFUTED; estimable weaker evidence is PARTIAL; gate failure is INCONCLUSIVE. No policy/causal/school/featured credit.

## Key-only coverage (upper bounds; no measurement or missingness opened)

| Case | Exposure → later outcome | Key pairs with ≥2 waves | Countries | By anchor |
| --- | --- | ---: | ---: | --- |
| `energy_stunting` | `21010` → `21025` | 554 | 139 | 2001:139, 2006:139, 2011:138, 2016:138 |
| `energy_low_birthweight` | `21010` → `21049` | 542 | 136 | 2001:136, 2006:136, 2011:135, 2016:135 |
| `protein_stunting` | `21013` → `21025` | 568 | 147 | 2001:137, 2006:139, 2011:146, 2016:146 |
| `protein_low_birthweight` | `21013` → `21049` | 566 | 145 | 2001:138, 2006:140, 2011:144, 2016:144 |
| `animal_protein_anemia` | `21014` → `21043` | 672 | 173 | 2001:163, 2006:165, 2011:172, 2016:172 |
| `animal_protein_low_birthweight` | `21014` → `21049` | 566 | 145 | 2001:138, 2006:140, 2011:144, 2016:144 |
| `staple_share_anemia` | `21012` → `21043` | 672 | 173 | 2001:163, 2006:165, 2011:172, 2016:172 |
| `fat_overweight` | `21061` → `21041` | 576 | 149 | 2001:139, 2006:141, 2011:148, 2016:148 |

No numeric-cell availability is inferred from these keys. A low result count under frozen gates is an honest outcome, not a reason to change rows, sources or thresholds.

## Pathway rationale and caveats

- Energy adequacy and total protein availability test broad energy/nutrient sufficiency against child stunting and low birthweight. Animal-origin protein tests a different nutrient mix against women’s anemia and low birthweight. Staple share is a coarse diversity proxy against anemia. Fat availability tests energy-density exposure against child overweight. These are hypotheses about national ecological covariance; income, infections, sanitation, pregnancy care and other confounders remain.
- The FAO food-supply variability indicator was screened and excluded before freeze because its full-series detrending and preceding-five-year method complicates temporal interpretation. Wasting was excluded before freeze because only 75 repeated-wave key pairs in 30 countries were available under the fixed schedule. These screens used identifiers, years and official methodology, not values.
- The eight cases share FAO vintages and several endpoints. The local correction does not account for selection across the full IESET archive. Later model revisions and estimates can induce apparently smooth correlations.

## Chronology contract

Commit this preregistration, all eight specs/steelmen, the roster, crosswalk and runner together. Commit the exact raw ZIP hash and source lock separately. Only then may `--run` read selected `Value` and `Flag` fields. Failed cells must be archived with a result packet, and replay must be byte-exact.
