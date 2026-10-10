# OECD statutory tax cuts and next-year business registration growth: prospective two-test family

This is a prospective **descriptive calibration** study. Before this registration, only the selected OECD tax values, World Bank indicator schema and country/year keys, exact source hashes and manifests, and visible earlier hypothesis text were inspected. No selected WDI `value`, null mask, or `obs_status` was opened. The two tests stay in one Bonferroni family with alpha 0.01 and two-sided p ≤ 0.005 each. This correction is local to these tests, not to the visible IESET archive. Neither test can receive school, policy, causal, or featured credit.

## Source and prior-work lock

- **CIT treatment:** OECD combined central-plus-subcentral statutory corporate income-tax rate, `CIT_C/ST` from `OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0` with key `.A.CIT_C.ST......`. Frozen file `data/vintages/oecd/oecd_combined_corporate_income_tax_rate@2026-07-23T153857Z.parquet`, SHA-256 `3e9c5987717087d04d5f82461fc1a3fb5e406ba646fb9f333f8c542e5f3f5ee1`.
- **PIT treatment:** OECD top statutory personal income-tax rate, `TS_PIT` from `OECD.CTP.TPS,DSD_TAX_PIT@DF_PIT_TOP_EARN_THRESH,1.0` with key `.A..TS_PIT.PT_WG_EARN_G.......`. Frozen file `data/vintages/oecd/oecd_top_statutory_pit_rate@2026-07-23T153857Z.parquet`, SHA-256 `b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151`. One source value, France 2013 at 122.796992%, is outside the possible 0–100% rate range. The prespecified validity screen excludes that endpoint and the 2013 and 2014 changes involving it. This is a source-value screen made before outcome access.
- Both OECD tax files have fetch manifest `data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml`, SHA-256 `6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18`. The manifest's general methodology URL points to revenue statistics and is not the right definition for these rates; the selected SDMX entries and [OECD corporate rate](https://www.oecd.org/en/data/datasets/corporate-income-tax-rates-database.html) and [OECD PIT flow](https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.CTP.TPS&df%5Bid%5D=DSD_TAX_PIT%40DF_PIT_TOP_EARN_THRESH&df%5Bvs%5D=1.0) define them.
- **Outcome:** World Bank WDI `IC.BUS.NREG`, new limited-liability corporations registered in a calendar year. Frozen file `data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet`, SHA-256 `213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae`; fetch manifest `data/manifests/fetch_run_2026-05-05T210519Z.yaml`, SHA-256 `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112`. [World Bank metadata](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/IC.BUS.NREG) calls it a count, not a rate, active-firm count, or job count. The raw vintage has 17,556 rows with a synthetic 1960–2025 country/year grid. Five income-group aggregate rows per year have blank country codes, producing 264 duplicate blank-code/year keys; these are removed using keys before any outcome read. Surviving three-letter country/year keys are unique. Key presence is **not** a claim that the registration value is observed.

A text audit of the 2,030 canonical hypothesis specs at the time of the text screen found no exact OECD CIT-cut or top-PIT-cut versus WDI registration-growth pairing. Related work is visible: `tax_simplicity_entrepreneurship_panel` uses Doing Business compliance costs and WDI registrations, `capital_gains_tax_cut_investment_response_panel` lists registrations as an auxiliary outcome, and existing OECD CIT and PIT prospective studies use other outcomes. The family p adjustment therefore does not provide archive-wide selection control.

## Frozen key roster and exposure design

The key-only roster is `data/pinned_evidence/oecd_tax_registration_family_2026_key_roster.csv`, SHA-256 `7f52d0b7316e08e79693ded46fc47d1006f614fd515e5147fb4f5f0509a9cc92`. Its entries are sorted by case (`cit`, `pit`), treatment year, and country code. A candidate treatment year is 2007–2018 inclusive; it needs the exact selected tax rate at t−1 and t, WDI **keys** at t and t+1, finite tax rates in [0,100], and at least five candidate years per country. The latest outcome year is 2019, before pandemic-era values. There is no nearest-year matching, imputation, country substitution, or window extension.

Code each annual tax change once from pre-read treatment values: **cut** if rate(t)−rate(t−1) ≤ −1 percentage point, **hike** if ≥ +1, and **stable** otherwise. Large valid reforms remain in the panel. The primary cut contrast includes a separate hike indicator so a hike is not treated as the stable reference. This category design was selected because a continuous-rate OLS design failed a treatment-only influence screen: the largest 1% of residualized CIT changes held 66.8% of tax-change variation and PIT 39.8%. No outcome information informed the categorical switch. The categorical cut signal, partialled on country, year and the hike indicator, has the following pre-read coverage:

| Test | Key-only pairs / countries | Cut years / countries | Hike years / countries | Stable years | Top 1% partialled-cut variance | Top country partialled-cut variance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CIT | 1,691 / 141 | 196 / 93 | 56 / 37 | 1,439 | 10.5% | 2.2% |
| Top PIT | 454 / 38 | 43 / 23 | 43 / 23 | 368 | 13.6% | 7.6% |

After the **separate committed source lock**, read the selected WDI outcome values and status. Keep a pair only when both endpoint counts are finite, strictly positive, and have blank `obs_status`. Require at least five complete pairs per country. Do not cap or winsorize outcome log changes. The primary outcome is `ln(N(t+1))−ln(N(t))`, where N is the raw registration count.

## Estimator and verdict gates

Fit exactly one model per tax source:

`Δln registrations(c,t→t+1) = α_c + λ_t + β_cut 1[Δtax≤−1] + β_hike 1[Δtax≥+1] + ε(c,t)`.

The comparison group has `|Δtax|<1`. Fit OLS with country and treatment-year effects, country-cluster CR1, and two-sided Student t(G−1) inference. There are no additional controls, alternate lags, country substitutions, or model searches. The primary coefficient is `β_cut`; the hike coefficient is a prespecified nuisance estimate and receives no independent verdict. Require full design rank, finite positive cluster uncertainty, and a post-complete-case partialled-cut top-1%-row variance share ≤30% and top-country share ≤20%.

| Test | Minimum complete pairs / countries | Minimum complete cut years / countries | Minimum complete hike years / countries | Meaningful cut beta |
| --- | ---: | ---: | ---: | ---: |
| CIT | 700 / 60 | 70 / 35 | 20 / 15 | +0.05 log point |
| Top PIT | 250 / 25 | 20 / 12 | 15 / 10 | +0.05 log point |

These floors are below the key-only upper bounds but are not guaranteed by keys. The meaningful magnitude corresponds to about 5.1% higher next-year registration growth in a cut year than a tax-stable year. If any source, chronology, complete-case, event, rank, concentration, or inference gate fails, verdict **INCONCLUSIVE**. Otherwise **SUPPORTED** requires `β_cut≥+0.05` and two-sided `p≤0.005`; **REFUTED** requires `β_cut≤−0.05` at the same p cutoff; all other estimable results are **PARTIAL**. Both tests remain in the two-test family even if one is inconclusive.

## Interpretation limits

OECD statutory rates are not effective business or owner tax rates. Top PIT primarily describes gross wage earnings at the highest bracket and is an especially weak proxy for the tax faced by a newly incorporated company; its direction is uncertain. New registrations can reflect registry scope or processing changes, migration, population growth, business cycles, legal-form substitution, and tax anticipation. Country and year effects and one-year ordering do not identify policy effects. This design deliberately yields descriptive calibration only with zero causal, policy, school, and featured credit. Preserve null, opposite, missing, and inconclusive findings.
