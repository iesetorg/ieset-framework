# Result card — Nordic outcome persistence decomposition

**Verdict:** weakened — primary outcome residual share exceeds 0.30 threshold

Pre-registered falsification rule: residual_share(log GDP per capita PPP) ≤ 0.30 AND residual_share(Gini) ≤ 0.50 AND residual_share(unemployment) ≤ 0.50.

## Coefficient summary

| Outcome | Baseline Nordic coef | Full Nordic coef | Residual share | Threshold | Pass? |
|---|---:|---:|---:|---:|:---:|
| `log_gdp_pc_ppp` | +0.377 (0.108) | +0.368 (0.224) | 0.98 | 0.30 | ✗ |
| `gini` | -6.587 (0.617) | -5.546 (0.932) | 0.84 | 0.50 | ✗ |
| `unemployment` | -5.573 (1.791) | -0.455 (5.944) | 0.08 | 0.50 | ✓ |

Clustered SEs by country. Baseline: PanelOLS with time effects + nordic_dummy. Full: PanelOLS with time effects + nordic_dummy + 3 channels (WGI gov effectiveness, WGI rule of law, IMF general-govt debt/GDP) + 2 controls (log population, urbanisation). Country fixed effects are NOT included because they would absorb the time-invariant Nordic indicator, making the hypothesis untestable.

### Debt source — deviation from spec literal

The pre-reg YAML specifies `world_bank_wdi:GC.DOD.TOTL.GD.ZS` for debt/GDP and notes IMF `GGXWDG_NGDP` as a v2 alternative. The WDI series turns out to have only 54 non-null obs across the 10-country × 28-year sample (central-government reporting gaps), which is numerically infeasible for the full spec. IMF GGXWDG_NGDP is dense (278/278 obs) and is used as the primary v1 debt channel. The pre-reg-literal WDI spec is retained in the coefficients table as `spec=full_wdi_prereg_literal` for transparency; its numerical instability is documented in diagnostics.json.

## Channels (log GDP PPP, full spec)

- gov_eff:        -0.112 (0.110)
- rule_of_law:    +0.102 (0.091)
- debt_gdp:       -0.002 (0.001)
- log_population: +0.056 (0.039)
- urbanisation:   +0.005 (0.004)

## Honest interpretation (engaging the steelman)

The raw log-GDP-pc-PPP Nordic-vs-comparator gap is +0.377 (≈45.9% higher PPP GDP/capita in Nordic countries, on average, over 1996 – 2023). After adding the three channels and controls it shifts to +0.368 (residual share 0.98).

The result is a weakening of the hypothesis's primary-outcome claim: the three institutional/fiscal channels account for only ≈2% of the Nordic-vs-comparator log-GDP-per-capita-PPP gap. On the secondary outcome (Gini) channels absorb ≈16%; on the tertiary (unemployment) they absorb ≈92%, a clean pass. This is the kind of mixed finding the framework's asymmetric-credit-for-prior-updating commitment in DISCLOSURE.md calls out explicitly: the author's prior favoured the decomposition; the data only partially supports it.

The steelman's strongest objection — that WGI government-effectiveness is partly downstream of the outcomes it's being used to explain — is live. Channel coefficients are suggestive but an endogeneity-robust spec (e.g. V-Dem administrative indicators) is a v2 priority when the fetcher ships. The country-FE-absorbs-variation objection is valid: this v1 design cannot distinguish 'Nordic channels explain the gap' from 'Nordic countries have time-invariant unmeasured features that look like the measured channels in cross-section'. A v2 with within-country decomposition (country FE, examining channel movement over time within each country) would test a different but related claim.

## Known v1 limitations (v2 roadmap)

- OECD EPL (labour-market flexibility) channel omitted — fetcher pending.
- WVS/V-Dem social-trust channel omitted — fetchers pending.
- Gini sample is sparse; residual share for Gini is sensitive to coverage. Eurostat Gini as robustness is a v2 addition.
- Norway SWF mechanism is absorbed into the NOR country-specific intercept; not modelled as a channel variable.

## Provenance

Run artifacts reproduce deterministically from the vintages listed in `manifest.yaml`. See `replication.py` for the full pipeline.
