# Blind registration: recorded conflict and eight national outcomes

Family: owid_conflict_multidomain_four_year_2026_10_10. Eight descriptive association cells; fixed before selected outcome values, null masks, fitted estimates, signs, or verdicts were opened for this family. Prior IESET conflict and some outcome results were visible and this is not an independent external holdout.

## Question and design

Across national four-year windows, is any OWID/UCDP state-based conflict during t+1..t+4 associated with slower contemporaneous change in health, schooling, income, invention, export breadth, or fixed investment, or with higher WITS HH Market concentration? Anchors are 1995, 1999, 2003, 2007, 2011, 2015, 2019. Each annual outcome interval is disjoint from the next except its shared endpoint. Exposure is binary any of four conflict count categories positive in t+1..t+4; prior conflict is log(1+sum counts in t-3..t). Counts must be complete finite nonnegative integers <=100 by category. No missing-as-zero.

The model is y(t+4)-y(t) on conflict-window indicator, transformed y(t), prior conflict, country and anchor effects. Country-cluster CR1 uncertainty uses Student t(G-1), two-sided. No policy or causal estimate is claimed. Binary conflict captures recorded incidence, not battle deaths, violence intensity, or all conflict types.

## Eight fixed cells

| Cell | Outcome change | Expected sign | Material beta per conflict window | Key rows / countries |
| --- | --- | --- | ---: | ---: |
| life | life expectancy at birth (years) | - | 0.2 | 1351 / 193 |
| mean_school | mean completed years of schooling (years) | - | 0.05 | 1249 / 190 |
| expected_school | expected years of schooling (years) | - | 0.1 | 1293 / 192 |
| gni | real GNI per person (four-year log percentage points) | - | 2.0 | 1324 / 191 |
| patents | resident patent filings per million (log1p filings per million) | - | 0.1 | 1358 / 194 |
| breadth | number of exported HS6 products (log product count) | - | 0.03 | 969 / 168 |
| concentration | WITS HH Market concentration index (index units) | + | 0.01 | 979 / 169 |
| investment | gross fixed capital formation share of GDP (percentage points) | - | 0.5 | 1358 / 194 |

The committed key roster is data/pinned_evidence/owid_conflict_multidomain_2026_key_roster.csv with SHA-256 8046e224ad39cb787ff95416ab5d3c3ab0714ce02e3e4a7b79bae6df485d831d. It contains only role, ISO3, and anchor keys, not values or non-null indicators. Exactly 9881 role/country/anchor rows are present. Key screening used the named source files and exact conflict annual-key presence; patent keys also require WDI population endpoints. A key is not a usable outcome value.


## Input validity frozen before measurement

- UNDP life expectancy must be finite within [20,100] years at both endpoints.
- UNDP mean completed schooling must be finite within [0,30] years at both endpoints.
- UNDP expected schooling must be finite within [0,40] years at both endpoints.
- UNDP GNI per capita must be finite and strictly positive at both endpoints; source units are 2021 PPP dollars.
- WIPO resident applications must be finite and nonnegative with blank/null or A observation status; WDI population at both endpoints must be finite and strictly positive with blank/null or A status.
- WITS unique exported HS6 products must be finite and strictly positive, with product_code 999999, partner_iso3 WLD, freq_id A, and indicator_id NMBR-XPRT-HS6-PRDCT.
- WITS HH Market concentration index must be finite in [0,1], with product_code 999999, partner_iso3 999, freq_id A, and indicator_id HH-MKT-CNCNTRTN-NDX.
- WDI gross fixed capital formation share must be finite in [0,100] with blank/null or A observation status at both endpoints.

## Frozen gates

Each cell retains only countries with >=4 complete windows. Require >=450 complete rows across >=70 countries and >=5 anchors, >=70 conflict rows across >=20 countries, >=150 non-conflict rows across >=60 countries, and >=25 countries that switch conflict status across retained windows. Require full-rank design and finite positive clustered uncertainty. After residualizing exposure on the exact controls and fixed effects, the top 1% of rows may supply at most 25% of squared exposure, one country at most 15%, and one anchor at most 25%. Any failure is INCONCLUSIVE archive.

Family alpha is 0.01, so Bonferroni two-sided p <=0.00125 for each of eight cells. Predicted-sign and opposite-sign material effects are SUPPORTED and REFUTED respectively; every other gate-cleared estimate is PARTIAL. All eight cells count in the family denominator regardless of missingness or verdict. These local gates do not correct across prior IESET search. No outcome-dependent model or sample changes.

## Exact source custody

The WITS file is named product_concentration, but its indicator_name is HH Market concentration index; this cell addresses that named market index, not product concentration. This semantic check used metadata only, before outcome-value access.

The raw files are present in the user main checkout as ignored pinned vintages; the isolated branch stores key roster and hashes, not raw redistributed bytes. The runner will require these exact SHA-256 bytes and tracked fetch-manifest entries at source lock and replay.

| Role | Raw SHA-256 | Tracked fetch manifest / SHA-256 |
| --- | --- | --- |
| conflict: owid:number-of-state-based-conflicts | f79099534287e0b42d93b9ab622eec5e0d8d47c02eebd5dbf79f40138f8f3885 | fetch_run_bootstrap_2026-04-30T121833Z.yaml / e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e |
| life: undp_hdi:life_expectancy | 13b99319b8b1a2be96f0774dfd67104e2b7a41b4ca176bf43486b65ff99f43cb | fetch_run_2026-05-05T210519Z.yaml / 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| mean_school: undp_hdi:mean_years_schooling | e3a1e5a17bf361219f2a13a1e5e4b6c5cc0faa28c620245a907f2e087a725449 | fetch_run_2026-05-05T210519Z.yaml / 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| expected_school: undp_hdi:expected_years_schooling | 86c0f5c46556a914fa8bc72405fa46ad9e8de550612d03795531d2d196d5735f | fetch_run_2026-05-05T210519Z.yaml / 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| gni: undp_hdi:gni_per_capita | 9f9c6a839567dcfa4dd3f51876f8e76755e5bddff3d5539ba0cd077d618f30a0 | fetch_run_2026-05-05T210519Z.yaml / 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| patents: wipo:patent_applications_resident | 8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e | fetch_run_2026-05-19T095056Z.yaml / cf2f7e75af5612b302af7fbb0479c196598aa060c20f858723108a8c95455de4 |
| breadth: wits:unique_hs6_products | 29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934 | fetch_run_2026-07-23T153659Z.yaml / 542aacbcc80b1856262eda14f37d0532c7a14611c8b9d698ab516529942d0b73 |
| concentration: wits:product_concentration | c59b180e07f484546e131fa6a4f47a725ecc790effbb3d395e5d2c4e36381949 | fetch_run_2026-07-23T151550Z.yaml / 96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5 |
| investment: world_bank_wdi:NE.GDI.FTOT.ZS | fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21 | fetch_run_2026-05-05T203305Z.yaml / 53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0 |
| population: world_bank_wdi:SP.POP.TOTL | 6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456 | fetch_run_2026-05-05T200056Z.yaml / a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945 |

Source rights are recorded as UNDP CC BY 4.0, OWID CC BY 4.0 with UCDP/PRIO attribution, WDI CC BY 4.0, WIPO statistics terms via World Bank transport, and WITS/World Bank terms where mirrored. Local derived metadata is not permission to redistribute raw WITS/WIPO files.

## Interpretation limit

Life expectancy, completed schooling, expected schooling, GNI, patents, export product count, market concentration, and capital formation are distinct measured endpoints but highly correlated within domains; eight visible records do not imply eight independent natural experiments. Conflict may precede, coincide with, or follow economic shocks within a four-year window. National data hide local exposure and displacement. Reporting and model revisions may alter vintages. No policy, causal, school, position, or featured credit is permitted.
