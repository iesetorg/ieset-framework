# Protected-land forward forest and food family — source-coverage no-go

The two new IDs are one descriptive family based on the archived `protected_land_food_security_emissions_panel` question. The forest endpoint is **net forest-cover share**, not gross deforestation or land-use emissions. The food endpoint is national food-production-index growth **per person**, not household food access. The old proxy run and all school mappings remain unchanged.

## Frozen custody

- Full repository specification validation passed before measurements were opened: 6,321 specs validated, with only the repository's 28 permitted candidate-policy forward-reference warnings.
- Registration commit: `4e9f3eb637bb4f97f4fc7c12201df39f4bffaa47` (two specifications, two steelmen, and the blind plan).
- Separate metadata-only source-lock commit: `c736d28fafd3eb6961576b936cee6bef32d0ac01`. It freezes 172 ISO3 economies with all required country/year keys; key presence did not imply non-null measurement. The source references are repository-relative and hashes were verified against the pinned local corpus supplied to the runner with `--source-root <SOURCE_ROOT>`.
- Runner first-add commit: `2b40c25544e553904a534dada6bda4a8feb5d1f9`, before any selected values or null masks were read. Its key-only `--check-lock` passed before the first measurement read.
- Result commit: `637098cbc6ef4e35f81c76445656fed943e093df`. Each ID has the nine required run artifacts. The runner matched all 9/9 artifacts per ID on exact replay from the pinned local corpus.

## Frozen gate and observed failure

The shared complete-case gate required at least 50 economies, at least 15 with a protected-area-share gain of 2 percentage points or more, and exposure IQR of at least 1 percentage point. It required positive cereal-yield growth of at least 0.5 annual log point in 1995–2005, valid 2005/2015 protected-area measurements, and valid forward forest and food measurements through 2023. No sample or year was substituted after observation.

Both endpoints are **INCONCLUSIVE**: 0 of 172 source-key candidates meet the shared complete-case rule. Overlapping exclusion counts are 172 with an invalid/missing protected-area endpoint, 172 with an invalid/missing food-production endpoint, 59 below the prior yield-growth condition, and 2 with invalid/missing 2015 income. Forest-share and population fields did not cause exclusions. The sample gate failed before estimation: there is no coefficient, standard error, p-value, noninferiority conclusion, or forest-retention verdict.

The post-registration coverage diagnosis found the blockers in the frozen vintages: protected-area share has 0/172 finite 2005 measurements and 170/172 finite 2015 measurements; food-production index has 172/172 finite measurements in both 2005 and 2015, then 0/172 finite 2023 measurements. These are source-coverage facts, not estimates. Switching years now would create a different post-observation design and is not counted as a conversion in this family.

## Visibility and credit

`check_preregistration.py` reports 831 strict pre-registration pairs with both new IDs verified. The evidence-tier audit places both IDs in `archive` with `non_result_verdict`, public visibility false. Public-visible total remains **579** in this checkout, a delta of **0**. The public OPSEC check passed. No generated preregistration/evidence/census/web indexes were committed. No causal, policy, school, position, or featured credit is claimed; no push, merge, or deployment was performed.
