# Prospective preregistration audit: sustained FDI inflows → resident patent filings

**Status:** frozen pre-outcome package; no patent `value`, value-null mask, or `obs_status` column has been read. This document records only source schema, country/year/indicator keys, treatment and control values, and file/manifest hashes. It is not a result.

## Independent question and provenance

The single test asks whether a sustained net FDI inflow above a fixed 3%-of-GDP threshold is associated with more subsequent *resident patent filings per million*. It is distinct from existing trade-share → resident-patent and FDI-policy → supplier-productivity hypotheses. A text catalog check found 77 FDI and 32 patent YAMLs; only two contained both terms, and neither specified this direct FDI-flow/resident-filing pair. This is a selected new test, not an independent archive-wide replication.

| Role | Physical frozen source | SHA-256 | Fetch manifest |
| --- | --- | --- | --- |
| FDI | `data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-05-05T195106Z.parquet` | `626691877048dc78d5f7b4f6948dd680d3e111aedff252d1286ca2fd40b8abc5` | `fetch_run_2026-05-05T200056Z.yaml` |
| Resident patents | `data/vintages/world_bank_wdi/IP.PAT.RESD@2026-05-05T203341Z.parquet` | `617c357fceaff7a4f21710f710426f9ad2c01e710e9c0432b9085a41e7b887fe` | `fetch_run_2026-05-05T210519Z.yaml` |
| Population | `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet` | `6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456` | `fetch_run_2026-05-05T200056Z.yaml` |
| GDP per person | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `fetch_run_2026-05-05T200056Z.yaml` |
| GDP growth | `data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet` | `db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58` | `fetch_run_2026-05-05T200056Z.yaml` |

The 20:00:56 fetch manifest SHA-256 is `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945`; the 21:05:19 manifest SHA-256 is `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112`. The runner copies only the five narrow source entries into its later lock. No whole fetch manifest or local path-bearing manifest is added to this package.

World Bank defines FDI as *net* inflows giving lasting management interest, from balance-of-payments and supplemented sources; it is a GDP ratio and includes more than physical investment ([definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/BX.KLT.DINV.WD.GD.ZS)). Its resident-patent series is sourced from WIPO and counts applications rather than grants ([definition](https://databank.worldbank.org/metadataglossary/sustainable-development-goals-%28sdgs%29/series/IP.PAT.RESD)). [WIPO methodology](https://www.wipo.int/en/web/ip-statistics/about) says missing non-PCT office values may be zero or unreported, so no missing-to-zero conversion is allowed.

## Blind roster and exposure selection

The cohort is the 112 listed ISO-3 countries/economies with at least five million residents in the pinned population source at exact 2004. Treatment years are 2004–2019, with FDI at t−2, t−1, t; GDP controls at t; and positive population denominators at t and t+3. Patent `country_iso3`, `indicator_id`, and `year` keys were projected solely to establish exact t/t+3 key presence. The WDI files use a rectangular API country/year grid, so key presence **does not establish** observed patent values or completeness. The frozen sorted CSV has 1,723 treatment/control-valid country-year keys from 110 economies, SHA-256 `70ceb9453eabd876e0fa173188675eaf819b919dc60a7990fc64320a955500a4`. South Sudan supplies two such keys and may be excluded by the predeclared minimum five *complete* pairs per retained country; no row is trimmed for FDI magnitude.

The continuous three-year FDI mean is highly leveraged: in the treatment/control-only panel, the top 1% of rows hold 44.8% of squared residualized exposure after country effects, year effects, log GDP per person, and GDP growth. A *binary* exposure at a 3% mean threshold yields 702 exposed keys across 74 economies and 66 within-country switchers. Its pre-outcome residualized exposure shares are 2.75% for the largest country, 12.66% for the top five countries, and 8.77% for the top 1% of rows. The 3% cut was chosen using treatment/control information only and is frozen here. It is not a causal threshold or a policy target.

## Frozen design and stop rules

- Outcome: exact t→t+3 change in log(1 + WIPO resident patent applications per million residents), allowing true recorded zero but rejecting missing/negative/nonfinite counts and nonblank observation status.
- Estimand: OLS coefficient on the binary 3%-plus sustained-FDI event, with baseline log patent intensity, log real GDP per person at t, GDP growth at t, country effects, and treatment-year effects. Country-cluster CR1 standard errors, Student t(G−1), two-sided p.
- Complete-case gate: after the fixed country-five-year rule, at least 400 rows, 35 countries, 100 exposed rows, 25 exposed countries, and 25 countries with both exposed and unexposed complete years.
- Influence gate: residualize the event against *all* frozen controls and effects on the measured complete-case panel; require largest country ≤15%, largest five countries combined ≤35%, and largest 1% of rows ≤20% of squared residualized exposure. No winsorization or row deletion to pass a gate.
- Verdict: if any size, switch, influence, rank, or finite-inference gate fails, **INCONCLUSIVE**. Otherwise **SUPPORTED** for β≥+0.05 log points and p≤0.01; **REFUTED** for β≤−0.05 log points and p≤0.01; every other estimable result **PARTIAL**. This one test has local family alpha 0.01.

The patent endpoint may prove too sparse after measurement. No outcome completeness or coefficient has been checked; failure is an honest inconclusive result. The test carries zero causal, policy, position, school-score, and featured credit. Registration files must enter one committed preregistration commit; a narrow source lock must enter a later separate commit. Only after both commits may the runner open patent values/statuses. No source substitution, outcome-based roster edits, or extra estimators are permitted.
