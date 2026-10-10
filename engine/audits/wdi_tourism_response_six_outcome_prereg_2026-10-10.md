# Tourism arrival growth and six economic response margins — preregistration

This is one prospective **six-test descriptive family**. The exposure is annual log growth in inbound international arrival **trips** from `t-1` to `t`, for `t=2007..2018`. Each outcome is a different economic margin measured from `t` to `t+1`:

1. Adult (15+) employment-to-population rate, percentage-point change (modelled ILO estimate, WDI `SL.EMP.TOTL.SP.ZS`).
2. Gross fixed capital formation share of GDP, percentage-point change (WDI `NE.GDI.FTOT.ZS`; this includes public and private investment).
3. New formal limited-liability registrations per million residents, change in `log1p` density (WDI `IC.BUS.NREG` and `SP.POP.TOTL`).
4. Services value-added share of GDP, percentage-point change (WDI `NV.SRV.TOTL.ZS`).
5. Consumer-price inflation rate, percentage-point change (WDI `FP.CPI.TOTL.ZG`).
6. Real GDP growth rate, percentage-point acceleration (WDI `NY.GDP.MKTP.KD.ZG`).

These outcomes are distinct labor, investment, formal-entry, sector-composition, price, and aggregate-output margins. They share the tourism exposure and many countries and are **not six independent replications**. All six stay in the family denominator, including inconclusive results. Two-sided family alpha `0.01` yields a fixed Bonferroni cutoff `0.01/6`. This family was selected **after** the existing `wdi_tourism_arrivals_oecd_youth_employment_forward_2026` result was visible as **SUPPORTED** (beta `+3.38566`, two-sided p `0.00325316`, under its separate two-test family). That case tests **15–24 OECD employment**, not the adult ILO rate or the other five outcomes here. This prior positive result informed selection of the tourism exposure, so six-test Bonferroni does not control archive-wide selection. Existing single-country tourism records and a REER-to-arrivals case are also distinct. None provides evidence credit for this family.

## Pre-value custody and roster

Only raw schemas, country/year **keys**, file SHA-256 bytes, and tracked fetch-manifest metadata were read before registration. No selected source `value`, outcome null mask, sign, coefficient, or fit was opened. WDI emits a rectangular 216-economy × 12-year envelope even when measurements are missing; the 2,592 rows in `data/pinned_evidence/wdi_tourism_response_2026_key_roster.csv` are **not** complete-case evidence. The roster includes ISO 3166 alpha-3 countries and territories (plus XKX if present), excludes WDI aggregate codes, and is sorted by treatment year then ISO3. The exact roster SHA-256 is `018d735c2c6be4687db392b07e1872f6e5cb5fb6c8f50354f7a54f4dad09ff61`.

The measured-value files below must be present byte-identically in this isolated checkout before any selected values are opened. Five were already tracked in the consolidated base: GDP per person, population, fixed investment, inflation, and GDP growth. The other four, including arrivals, must be copied from the dirty main checkout and committed **after** this registration commit together with a source-lock manifest. Their existing fetch manifests are tracked in the consolidated base. The runner must verify original paths, byte hashes, manifest entries, unchanged prior tracked sources, frozen specifications, and Git chronology before opening values. The final result must be committed later still and exactly replayed. The WDI source files are under CC-BY-4.0 according to the fetch manifests; source provenance for ILO-modelled adult employment and UN Tourism arrivals remains attributed to their origin providers. This custody correction supersedes a local preregistration commit `b0843b214dddeadbe01bb54a3488647c649e16be` whose checker incorrectly assumed all nine raw files were newly pinned; no selected values were opened and no analysis gate changed before this corrected registration.

| Role | Pinned source (under `data/vintages/world_bank_wdi/`) | SHA-256 | Fetch manifest |
| --- | --- | --- | --- |
| Arrivals | `ST.INT.ARVL@2026-05-05T203952Z.parquet` | `1336df1cce2b3a2e784f917caa9487753d4cf53ad4ec65e5ea2fb045b0d41da5` | `fetch_run_2026-05-05T210519Z.yaml` |
| GDP per person | `NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `fetch_run_2026-05-05T200056Z.yaml` |
| Population | `SP.POP.TOTL@2026-05-05T194826Z.parquet` | `6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456` | `fetch_run_2026-05-05T200056Z.yaml` |
| Adult employment | `SL.EMP.TOTL.SP.ZS@2026-05-05T194751Z.parquet` | `13dd1ff36a27d38b5398196789130886c158c0d48ff0d8327567c9673bdbaeef` | `fetch_run_2026-05-05T200056Z.yaml` |
| Fixed investment | `NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet` | `fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21` | `fetch_run_2026-05-05T203305Z.yaml` |
| Business entry | `IC.BUS.NREG@2026-05-05T203439Z.parquet` | `213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae` | `fetch_run_2026-05-05T210519Z.yaml` |
| Services share | `NV.SRV.TOTL.ZS@2026-05-05T195011Z.parquet` | `3e4ecdf108553bd3449986ab0603ac062873ebc42bf40d2fa2c16dc52fc11fed` | `fetch_run_2026-05-05T200056Z.yaml` |
| Inflation | `FP.CPI.TOTL.ZG@2026-05-05T194737Z.parquet` | `dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0` | `fetch_run_2026-05-05T200056Z.yaml` |
| GDP growth | `NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet` | `db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58` | `fetch_run_2026-05-05T200056Z.yaml` |

The fetch-manifest SHA-256 values are `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` (20:00:56), `53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0` (20:33:05), and `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` (21:05:19).

## Frozen estimator and gates

For each response, retain only finite measurements with WDI observation status blank or `A` at the required endpoints, positive arrival counts and GDP per person, and absolute annual log arrival change at most `0.30`. Adult employment and services share must lie in `[0,100]`, fixed-investment share in `[0,200]`, registrations at or above zero with positive population, CPI inflation in `[-20,50]` percent, and real GDP growth in `[-30,30]` percent. The business response uses `log1p(1e6*registrations/population)` at both dates. No imputation or nearest-year join.

Country and treatment-year fixed-effect OLS regresses outcome change on arrival log change, baseline outcome level, and log real GDP per person at `t`, with an intercept. Country-cluster CR1 uncertainty uses two-sided Student t with `G-1` country degrees of freedom. The same complete-case floor applies to each test: at least **300 country-years/25 countries**, at least **60 rows/20 countries** with `|arrival log change| >= 0.10`, and at least five complete treatment years per retained country. Require full rank, finite positive cluster uncertainty, and maximum one-country share of squared residualized exposure `<=0.20`.

Each claim predicts a positive coefficient. Meaningful coefficients per **one log-point** increase in annual arrivals are: employment `+1.0` percentage point, investment `+0.5` point, business entry `+0.05` log point, services share `+0.5` point, inflation acceleration `+0.5` point, and GDP growth acceleration `+0.5` point. SUPPORTED requires the positive magnitude and `p<=0.01/6`; REFUTED requires the opposite magnitude and same cutoff. Other estimable fits are PARTIAL. A failed source, sample, variation, rank, concentration, or uncertainty gate is INCONCLUSIVE and archived. There are no post-result alternative windows, subgroup tests, outcome substitutions, or threshold changes.

Arrival trips are not distinct visitors or spending; national collection methods differ. Global demand, exchange rates, transport supply, political shocks, and domestic growth can jointly shift arrivals and these outcomes, so country/year effects and forward timing do not identify tourism's causal effect. The ILO employment series is modelled; registration counts formal limited-liability firms rather than all entrepreneurship. The six-test correction does not erase archive-wide search. No result receives causal, policy, school, position, or featured credit.

Source definitions: [international tourism arrivals](https://data.worldbank.org/indicator/ST.INT.ARVL), [adult employment ratio](https://data.worldbank.org/indicator/SL.EMP.TOTL.SP.ZS), and [new formal businesses registered](https://data.worldbank.org/indicator/IC.BUS.NREG).
