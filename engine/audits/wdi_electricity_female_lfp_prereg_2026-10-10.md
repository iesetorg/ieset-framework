# Electricity access and later female labour-force participation — preregistration

This is one **prospective descriptive cross-country test** of WDI electricity access change in **2000→2010** against female labour-force participation (LFP) change in **2010→2020**. Positive electricity gain and positive later female LFP gain are predicted to be associated. This is neither a policy evaluation nor a causal exposure estimate. Earlier visible IESET hypotheses `cross_school_electricity_access_growth_1990_2023` and `cross_school_electricity_access_child_mortality_1990_2023` use the same broad exposure but different outcomes; their visibility informed selection. This one-test p threshold does not account for archive-wide selection.

## Custody before selected values

Only parquet SHA-256 hashes, tracked fetch-manifest metadata, schema, `country_iso3`, `year`, and `obs_status` key fields were inspected. No selected `value`, outcome null mask, sign, variation, fit, or coefficient was opened. The 216-country ISO3-plus-XKX **source-key** roster is frozen at SHA-256 `a7b8e33e420cd1c0ce8160ad4e03e1102440d184842dd450027a446df26e8638`; key presence does not imply complete measurement. The two source files below are in the dirty main checkout and must first be copied into this separate checkout **after** this registration commit. A second commit must lock the raw vintages with their tracked fetch-manifest identity; measured results require a third later commit. The runner verifies byte hashes, source metadata, spec and runner bytes, and Git chronology before selected-value access.

| Series | WDI raw vintage | SHA-256 |
| --- | --- | --- |
| Electricity access (% of population) | `EG.ELC.ACCS.ZS@2026-05-05T195057Z.parquet` | `aa564cbe2947b3d1c3499d7ecb9b2c38c6aa5de073d2cc1a797cfe2fe42f2931` |
| Female LFP, ages 15+, ILO-modelled (% of female population) | `SL.TLF.CACT.FE.ZS@2026-05-05T194807Z.parquet` | `c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186` |

The tracked fetch manifest `data/manifests/fetch_run_2026-05-05T200056Z.yaml` has SHA-256 `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945`. Both entries list CC-BY-4.0. The outcome originates in the ILO modelled estimates database.

## Frozen estimator and gates

Use exact 2000/2010 electricity and exact 2010/2020 female LFP country endpoints. Retain only finite values with observation status blank or `A`; all four levels must be within `[0,100]`. No interpolation, imputation, alternative endpoint, aggregate row, or post-result country adjustment. The exposure is electricity-coverage gain in percentage points; the response is female-LFP gain in percentage points. Equal-country OLS regresses later female-LFP gain on prior electricity gain, 2010 baseline female LFP, 2000 baseline electricity access, and an intercept. HC3 uncertainty uses a two-sided Student t with model residual degrees of freedom.

A failed gate makes the result **INCONCLUSIVE**: at least **120 complete countries**, at least **30 countries with a positive ≥10-point access gain**, at least **40 countries with 2000 access <95%**, and a p90−p10 spread of access gain ≥15 points. Require full rank, finite positive HC3 uncertainty, and positive residualized-exposure variance. After residualizing exposure on baseline female LFP and baseline access, the top country's squared-exposure share must be ≤0.15 and the top ten combined share ≤0.50. Five holdout folds are fixed by `int(SHA256(ISO3)[0:8],16) % 5`; each leave-one-fold-out fit must retain ≥100 countries, full rank, and finite positive uncertainty. Hash folds check sensitivity to groups of countries but have no geographic meaning.

With all gates clear, **SUPPORTED** requires slope ≥+0.10 later female-LFP percentage points per +1 electricity-access point, two-sided p≤0.01, and positive slopes in at least four of five holdouts. **REFUTED** requires slope ≤−0.10, p≤0.01, and negative slopes in at least four holdouts. Other estimable fits are **PARTIAL**. A failed gate never becomes a directional verdict. No post-result threshold change, additional covariate, lag, country subset, or new outcome is permitted under this registration.

Electricity coverage does not measure supply reliability, affordability, hours, or appliance use. Female LFP is an ILO-modelled participation rate that includes employed and unemployed women and omits unpaid household work. Economic development, schooling, fertility, migration, social norms, industrial structure, and policy can move both variables. The baseline controls and forward timing do not identify a causal electricity or policy effect. All results receive zero causal, policy, school, position, and featured credit.

Definitions: [World Bank electricity access](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS), [World Bank/ILO female LFP](https://data.worldbank.org/indicator/SL.TLF.CACT.FE.ZS).
