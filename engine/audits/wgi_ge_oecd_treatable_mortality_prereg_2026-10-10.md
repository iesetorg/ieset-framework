# Proposed prospective registration: government effectiveness and treatable mortality

**Registration boundary:** The first Git commit containing this audit, the hypothesis, steelman, fixed key roster, runner, and synthetic tests is the authoritative registration timestamp. Before that commit, these files are only a proposal. At drafting, no registration commit, source lock, mortality measurement, or result existed.

## Question and evidence boundary

Does a higher World Bank Worldwide Governance Indicators government-effectiveness estimate at calendar year `t` predict a lower OECD treatable-mortality rate at exact `t+1`, conditional on WDI real GDP per capita at `t` and country and treatment-year fixed effects? This is a **single descriptive association**, not a government-policy effect. The WGI estimate is a perceptions-based composite and may incorporate perceptions of health services. OECD mortality is source-distinct from the WGI treatment; WDI income is a control. The sources and units cannot isolate health-service quality or any regulatory/fiscal channel.

The design was selected after inspecting WGI treatment and WDI control values, and **only** the selected OECD outcome Parquet schema, categorical dimensions, country/year keys, file hash, and fetch manifest. The selected OECD outcome `value`, `Observation value`, null mask, `OBS_STATUS`, `OBS_STATUS2`, `OBS_STATUS3`, fitted statistics, and public numerical snippets were not opened. Hashing the raw file pinned its bytes without decoding those columns. A rejected OECD-minimum-wage-to-Eurostat-poverty proposal had only 170 candidate pairs/17 countries; its outcome measurements were likewise unopened. No result from the older OECD mortality studies was used to select the sign or gates.

## Frozen source custody

| Role | Pinned raw vintage and SHA-256 | Tracked fetch manifest and SHA-256 |
| --- | --- | --- |
| WGI government effectiveness | `data/vintages/wgi/GOV_WGI_GE.EST@2026-05-05T195208Z.parquet` — `607d47979340b803fec2fefc1e57c94a7a167432317451ea0b1ade3ee0503edc` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` — `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| WDI real GDP per capita | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` — `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | Same WDI/WGI fetch manifest and hash above |
| OECD treatable mortality | `data/vintages/oecd/OECD.ELS.HD_DSD_HEALTH_STAT_DF_AMENABLE_MORT_1.0@2026-05-01T071213Z.parquet` — `e00d243302893fb2bcf455a6d75ab8e5467a208186683d52d291f235a4279f94` | `data/manifests/fetch_run_2026-05-01T071226Z.yaml` — `bf47fbd459e6074ad737def46b88a7fb9fa86d317fb0666567e50931ea861148` |

The runner checks each whole-file hash and its exact publisher, series ID, path, and entry hash in the tracked manifest. The OECD manifest's transport URL has `DF_AM,1.1` while its registered `series_id` is `DF_AMENABLE_MORT,1.0`; the raw file's exact `TRTM` dimension and hash, not a URL substring, select the outcome. The raw vintages are Git-ignored and must be supplied byte-for-byte to a replay; the runner accepts a local `--source-root` but never saves that machine path. Missing or mismatched custody stops the study before outcome access.

## Frozen keys and selector

`data/pinned_evidence/wgi_ge_oecd_treatable_mortality_2026_key_roster.csv` has SHA-256 `15f38fe6043ad1a2c45224ee7424824699201ffd0c45754a559043d68b90e608`. It contains exactly **781** unique treatment-year/country pairs in **45** named countries, with at least **11** candidate pairs per country. Treatment years are 2000 and 2002–2018; 2001 has no WGI key. The roster uses finite WGI values in `[-3,3]`, positive finite WDI GDP per capita, exact OECD *keys* at `t+1`, and a minimum of eight candidate years per country. Key presence is an upper bound, not evidence of a valid measured mortality value or status.

The OECD selector is exactly `FREQ=A`, `MEASURE=TRTM`, `UNIT_MEASURE=DT_10P5HB`, `AGE=_T`, `SEX=_T`, `CALC_METHODOLOGY=STANDARD`, and `_Z` in `SOCIO_ECON_STATUS`, `DEATH_CAUSE`, `GESTATION_THRESHOLD`, `HEALTH_STATUS`, `DISEASE`, and `CANCER_SITE`. National `REF_AREA` must match the roster ISO3 code. All other rows, aggregates, alternate mortality measures, sexes, age groups, units, or years are excluded. Duplicate selected keys stop rather than average. Once the source lock is separately committed, selected outcome values must be finite and strictly positive; the normalized `value` must agree with `Observation value`; all three observation-status fields must be blank or `A`. Invalid outcome cells are omitted without imputation or data-dependent trimming. Countries then need at least eight complete pairs.

## Fixed estimator and gates

Estimate one OLS model: `log(TRTM_rate[c,t+1]) = β·GE[c,t] + γ·log(real_GDP_pc[c,t]) + country_c + year_t + error[c,t]`. Cluster by country using CR1; use a two-sided Student t test with `G−1` degrees of freedom and a matching 99% confidence interval. The primary coefficient is β per one WGI index point. The controls, lag, log transform, and country roster cannot change after outcome access. There is no primary subgroup or alternate specification.

The measured fit requires **at least 450 complete pairs in 30 countries**, at least eight complete treatment years per retained country, a full-rank design, and finite positive clustered uncertainty. Partial WGI variation after removing log GDP per capita, country, and year effects may contribute at most **20%** of squared residual signal from the top 1% of rows, **15%** from the largest country, and **20%** from the largest year. On the pre-value 781-key envelope, these shares were **12.6%, 7.1%, and 11.6%** respectively; they must be rechecked after complete-case filtering. Any failed gate yields **INCONCLUSIVE**, regardless of coefficient sign.

If estimable, **SUPPORTED** requires β≤−0.05 log points per WGI index point and two-sided `p≤0.01`; **REFUTED** requires β≥+0.05 at the same cutoff. Otherwise the result is **PARTIAL**. The 0.01 cutoff is a conservative local screen for this adaptively selected study; it is **not** a correction across IESET's historical search. The run must preserve all failed gates and its verdict, including an inconclusive outcome. No result may be selected for school, position, policy, causal, or featured credit.

## Duplicate screen and limits

An exact-source-pair search of canonical hypothesis YAML and the prospective-audit index found no WGI `GOV_WGI_GE.EST` → OECD `TRTM` treatable-mortality study. Existing hypotheses use OECD treatable mortality against public health spending or physician measures; other studies use WGI government effectiveness against electricity access and education. The broad theme has therefore been examined, and this new pair is **not** an independent archive-wide holdout or a validation of those prior results. Underlying country/year observations can overlap. WGI method changes and OECD cause-of-death coding changes may matter; selected raw OECD status flags do not establish full coding comparability. Reverse causality, health spending, technology, demography, disease patterns, and country-specific trends remain. Any favorable association is a narrow calibration only.

## Chronology contract

1. Commit the six package files together as the first registration commit. Before that commit, `preflight` may inspect only treatment/control values and OECD selector/key columns.
2. Run `lock` after the registration commit. It writes a narrow source-lock JSON with exact source identities and registration commit, then commit that lock in a **separate** later commit. `lock` itself never reads measured OECD columns.
3. Only after the source-lock commit, run the guarded measurement. It writes the standard immutable run packet: `result.json`, `diagnostics.json`, `manifest.yaml`, `hypothesis.yaml`, `replication.py`, `coefficients.parquet`, `chart_data.json`, `result_card.md`, and `evidence_packet.yaml`, including an inconclusive verdict and failed gates when applicable. Commit all nine in a **third** commit. `diagnostics.json` declares `correction.disposition=descriptive_calibration_only` and zero causal/policy/school/featured credit. The run-local `replication.py` invokes guarded verification; `verify` is usable only after the measured-result commit and recomputes and byte-compares all nine artifacts after confirming the three-commit order. No source-lock or measured run was performed while preparing this package.
