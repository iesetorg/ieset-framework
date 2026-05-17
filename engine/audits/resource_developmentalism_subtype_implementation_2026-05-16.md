# Resource Developmentalism Subtype Implementation - 2026-05-16

Target: `resource_developmentalism_rent_seeking_trap`

Draft coding file: `data/manual/resource_developmentalism_subtype_coding_2026-05-16.csv`

This is a local manual subtype layer only. It does not modify movement YAML, hypothesis YAML, run artifacts, shared runner code, or scoreboard files.

## Inputs

- `engine/audits/resource_developmentalism_swarm_synthesis_2026-05-16.md`
- `engine/audits/resource_developmentalism_subtype_review_queue_2026-05-16.md`
- `engine/audits/resource_developmentalism_subtype_review_queue_2026-05-16.csv`
- `engine/audits/resource_developmentalism_treatment_inventory_2026-05-16.csv`
- `engine/audits/resource_developmentalism_case_map_2026-05-16.md`
- `engine/audits/resource_developmentalism_treatment_audit_2026-05-16.md`

## Coding Decisions

The CSV seeds all 32 queue targets and uses only the requested subtype and episode-role vocabularies.

Adjacent queue splits were normalized into non-overlapping inclusive episode windows so a later annual panel builder can explode rows without duplicate country-years. Where the review queue explicitly recommended splits, the draft uses multiple rows instead of umbrella rows. Uncertain cases remain marked in `review_status`; this file is not a final scored treatment.

`clean_comparator_eligible` uses:

- `yes`: usable clean comparator candidate after subtype coding.
- `conditional`: plausible comparator but still needs movement linkage, resource-exposure review, or sample-scope review.
- `no`: not a clean comparator.

## Row Counts

Total rows: 106

Countries covered: 32

Rows by subtype:

| subtype | rows | countries |
| --- | ---: | --- |
| `resource_developmentalist` | 24 | ARE, IDN, MYS, SAU |
| `resource_statist_socialist` | 3 | SYR, VEN |
| `resource_nationalisation_shock` | 4 | AUS, CAN, VEN |
| `market_open_resource_peer` | 14 | AUS, CAN, COL, PER, VNM |
| `rule_bound_resource_manager` | 6 | BWA, CHL, NOR |
| `mixed` | 45 | CHN, COD, ETH, IRN, KWT, NGA, PER, PNG, RWA, SYR, VEN |
| `uncoded` | 10 | BHR, CMR, GAB, GHA, LBY, MNG, OMN, QAT, TTO, ZMB |

Rows by episode role:

| episode_role | rows | countries |
| --- | ---: | --- |
| `treated` | 27 | ARE, IDN, MYS, SAU, SYR, VEN |
| `comparator` | 20 | AUS, BWA, CAN, CHL, COL, NOR, PER, VNM |
| `shock` | 4 | AUS, CAN, VEN |
| `excluded` | 45 | CHN, COD, ETH, IRN, KWT, NGA, PER, PNG, RWA, SYR, VEN |
| `uncoded` | 10 | BHR, CMR, GAB, GHA, LBY, MNG, OMN, QAT, TTO, ZMB |

Clean comparator eligibility:

| eligibility | rows | countries |
| --- | ---: | --- |
| `yes` | 13 | AUS, BWA, CHL, COL, NOR, PER |
| `conditional` | 7 | CAN, NOR, VNM |
| `no` | 86 | all other rows |

## Clean Comparator Candidates

Rows marked `yes`:

- Norway: 1979-1985 early oil/macro adjustment; 2001-2020 handlingsregel fiscal-rule era.
- Botswana: 1966-2020 diamond institutional-success comparator, with sample-scope flag.
- Chile: 2001-2005 structural-balance rule; 2006-2020 copper funds and fiscal-rule period.
- Australia: 1996-2009, 2011-2012, and 2014-2020 market-open resource-peer rows, with 2010 and 2013 shock years split out.
- Colombia: 2002-2010, 2011-2014, and 2015-2022 market-continuity resource-peer rows.
- Peru: 2001-2006 Toledo open-mining row and 2016-2018 PPK open-comparator row.

Rows marked `conditional`:

- Vietnam: 1989-1990, 1991-1997, 1999-2006, 2007-2014, and 2022-2026 market-opening rows. These require resource-exposure review before clean use.
- Norway: 1990-2000 oil-fund buildout row. This needs a confirmed local movement link.
- Canada: 1985-2020 non-NEP market-open peer placeholder. This needs explicit local movement rows before clean use.

## Excluded And Mixed Cases

The draft creates 45 `mixed` plus `excluded` rows. These cases should not enter either the main positive treatment or the clean comparator model without narrower hand coding:

- Kuwait: oil welfare and SWF compact remains rentier-welfare/mixed.
- Papua New Guinea: resource dependence is confounded by fragmented politics, customary land, conflict, and project-state dynamics.
- Iran: oil statism is confounded by revolution, war, sanctions, privatization, and reform cycles.
- Nigeria: military dirigisme, SAP liberalization, predation, civilian reform, and Buhari nationalism are separate mechanisms.
- Zaire/DRC: Mobutu mineral-rent predation is not a developmentalist treatment.
- China, Ethiopia, and Rwanda: WDI-threshold positives are treated as nonresource developmentalist false positives or excluded sensitivities.
- Syria: only 1974-1985 is provisionally treated as resource-statist socialist; other broad Baathist windows remain mixed/excluded.
- Venezuela: Perez is a shock, early/PDVSA Chavismo is treated, and Maduro/fallback years are mixed holdouts.
- Peru: Garcia and Humala windows are mixed and excluded from clean comparator rows.

## Uncoded Cases

The draft preserves 10 uncoded target-window rows and prevents them from collapsing into residual zero controls:

- Qatar, Oman, Bahrain, Libya, Trinidad and Tobago, Gabon, Cameroon, Zambia, Mongolia, and Ghana.

Ghana is flagged separately because its current positive inventory row is post-2020 while the 1970-2020 resource/ERP episodes remain uncoded.

## Integration Edits Needed Later

Do not replace the existing `resource_developmentalism` scalar until the hypothesis and runner design are approved. Add this as sidecar subtype vintages first.

Exact edits for `scripts/build_movement_vintages.py`:

1. Add a constant near the existing resource constants:
   - `RESOURCE_DEV_SUBTYPE_CODING = ROOT / "data" / "manual" / "resource_developmentalism_subtype_coding_2026-05-16.csv"`
   - Add allowed subtype, role, and clean-comparator value sets matching this CSV.
2. Add `load_resource_developmentalism_subtype_coding(path)`:
   - Read with `pd.read_csv`.
   - Validate all required columns.
   - Validate subtype and episode-role vocabularies.
   - Coerce `episode_start` and `episode_end` to integers.
   - Reject `episode_end < episode_start`.
   - Reject overlapping country-year rows unless an explicit precedence rule is added.
3. Add an episode-expansion helper:
   - Explode each CSV row into annual `country_iso3`, `year`, `subtype`, `episode_role`, `clean_comparator_eligible`, `confidence`, and `review_status`.
   - Left-merge onto `base` to keep the same country-year grid as other movement vintages.
4. Add numeric sidecar frames with `value` columns so current `write_series()` can emit them:
   - `resource_developmentalism_subtype_treated_any`: `episode_role == "treated"`.
   - `resource_developmentalism_subtype_clean_comparator`: `clean_comparator_eligible == "yes"`.
   - `resource_developmentalism_subtype_conditional_comparator`: `clean_comparator_eligible == "conditional"`.
   - One indicator for each subtype, for example `resource_developmentalism_subtype_resource_developmentalist`.
   - One indicator for each role, for example `resource_developmentalism_role_shock`.
5. Optionally write a long categorical parquet with `write_vintage()` directly:
   - Suggested series id: `resource_developmentalism_subtype_long`.
   - Keep categorical columns for audit and debugging rather than forcing them into one numeric `value`.
6. In `build(args)`, call the subtype builder immediately after the current `resource_developmentalism` and `resource_developmentalism_alignment` writes.
7. Set `source_url` to `local://data/manual/resource_developmentalism_subtype_coding_2026-05-16.csv`.
8. Set `extra` metadata to include:
   - `manual_subtype_schema: true`
   - `row_count: 106`
   - `country_count: 32`
   - `clean_comparator_yes_rows: 13`
   - `clean_comparator_conditional_rows: 7`
   - `replaces_generic_scalar: false`
9. Update the target hypothesis only after subtype and product-export measurement are both ready.

## Validation

CSV parser validation passed:

- Required columns present: yes.
- Missing required row values: 0.
- Invalid subtype values: 0.
- Invalid episode-role values: 0.
- Country-year overlaps inside the manual CSV: 0.

`git diff --check --no-index` was run on:

- `data/manual/resource_developmentalism_subtype_coding_2026-05-16.csv`
- `engine/audits/resource_developmentalism_subtype_implementation_2026-05-16.md`

Both checks reported no whitespace errors. Note that `data/manual/**/*.csv` is ignored by the current `.gitignore`, so the CSV exists locally but will not appear in ordinary `git status` output unless explicitly force-added or the ignore rule is changed later.
