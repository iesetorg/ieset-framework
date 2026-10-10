# Blind registration: observed internet uptake and later economic composition

**Family:** `wdi_digital_diffusion_structure_2026_10_10`  
**Status:** prepared with selected outcome schemas and `(country_iso3, indicator_id, year)` keys only. Not committed, locked, or measured in this isolated worktree.  
**Scope:** retrospective descriptive associations in existing pinned WDI files; no causal, policy, position, school, or featured credit.

## Fixed three-case family

| ID | Exact selected WDI construct | Registered sign | Practical beta per 10-point Internet uptake |
| --- | --- | ---: | ---: |
| `wdi_internet_uptake_business_registrations_forward_2026` | log(1 + new limited-liability registrations per million residents), t→t+3 | positive | 0.05 log point |
| `wdi_internet_uptake_services_employment_forward_2026` | services employment share, t→t+3 | positive | 0.5 percentage point |
| `wdi_internet_uptake_hightech_export_share_forward_2026` | high-tech share of manufactured exports, t→t+3 | positive | 1.0 percentage point |

The exposure is WDI `IT.NET.USER.ZS` internet-user share change from t−3 to t, divided by 10. **It is observed uptake, not a policy treatment.** All three endpoints have one fixed familywise two-sided Bonferroni threshold `p <= 0.01/3`. The local correction does not cover selection from the larger IESET archive. Earlier internet-use candidates and the internet-to-patent calibration were visible during design; none uses these exact directed pairs. This is not a new-data holdout or independent replication.

## Blind source-key preflight

The exact CSV contains **1,558** economy-treatment-year structural slots across **196** ISO economies for t=2009–2016, with at least five such slots per economy. Valid treatment values and supporting real income/population values are present at the required endpoints. Selected outcome **keys** exist at t−3/t/t+3 for all three endpoints. The selected WDI files use broad structural country-year grids; the key count says nothing about actual selected-value completeness. The roster SHA-256 is `6fb22b7e83afe60d5cf03f43620968bfef7d75303d07bcd9a419f4d5b10ea356`.

Observed internet uptake rises by at least 10 percentage points in **528** slots across **141** economies and changes by at most 2 points in **232** slots across **77** economies. The top 1% of raw squared uptake changes account for **0.105906**. These are treatment-only facts; no selected outcome value, null mask, observation status, derived change, coefficient, or exact-pair result snippet was read.

| Role | Exact parquet SHA-256 | Tracked provenance |
| --- | --- | --- |
| internet `world_bank_wdi:IT.NET.USER.ZS` | `c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` SHA `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| gdp_pc `world_bank_wdi:NY.GDP.PCAP.KD` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` SHA `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| population `world_bank_wdi:SP.POP.TOTL` | `6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` SHA `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| entry `world_bank_wdi:IC.BUS.NREG` | `213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` SHA `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| services `world_bank_wdi:SL.SRV.EMPL.ZS` | `5cc0fcababebe90b69eae253466a6a81beaf0f52f9c0ef5d59b8a2fa34f400c6` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` SHA `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| hightech `world_bank_wdi:TX.VAL.TECH.MF.ZS` | `b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` SHA `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |

All raw files are under `data/vintages/world_bank_wdi/` and pinned by exact path and byte hash in the runner/specs. Source manifests are tracked and independently hash-checked. The runner's `--preflight` projects selected outcomes to country, indicator, and year keys only; it does not access selected values or statuses.

## Frozen model and dispositions

At t−3, t, t+3 require finite selected values, blank/null selected observation status, and the prespecified construct bounds: nonnegative registration counts with positive population for log1p registrations per million, or [0,100] for each selected share. Keep economies with at least five complete rows. Use country and treatment-year fixed-effects OLS of outcome change t→t+3 on internet uptake t−3→t per 10 points, prior internet level, baseline outcome, prior outcome change, log real GDP per person at t, and prior three-year log income change. Country-cluster CR1 covariance uses the small-sample correction and Student t with G−1 degrees of freedom.

For each endpoint, **INCONCLUSIVE** if fewer than 400 complete rows, 50 economies, seven treatment years, 60 material-rise rows or 25 material-rise economies, 20 low-change rows or 10 low-change economies, or if the model is rank deficient, country-cluster uncertainty is nonfinite/nonpositive, or residualized uptake squared weight exceeds 25% in the top 1% of rows, 15% in one economy, or 20% in one year. **SUPPORTED** means the registered positive sign clears both its practical magnitude and `p<=0.01/3`; **REFUTED** means a comparably negative estimate clears both. Every other estimable result is **PARTIAL**. All three gate-cleared verdicts are public **descriptive calibrations only**, with zero causal, policy, school, position, and featured credit. Gate failure is archived as **INCONCLUSIVE**; neither endpoint nor threshold changes in response.

Country and year effects do not remove reverse causality, unmeasured development shocks, reporting changes, global value chains, or overlapping-window dependence. Internet use does not isolate a digital policy. Business registrations omit informal and non-limited-liability firms; services employment is modeled; high-tech exports need not imply domestic capability.

## Required chronology

Add three specs, three steelmen, this design audit, the CSV roster, runner, and synthetic tests in **one first-addition preregistration commit**. Run only `--lock`, inspect its narrow JSON, and commit it separately. Only then may `--run` read selected outcome values/status. Verify measured packets by exact replay using `--verify`; no gate revision after selected outcome access.
