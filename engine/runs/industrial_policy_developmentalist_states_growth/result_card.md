# Result card — Industrial policy developmentalist states growth

**Verdict:** SUPPORTED — avg ATT across 4 developmentalist cases (KOR/TWN/SGP/CHN) is +1.088 log-points at 40-yr horizon (~+197%). 4/4 cases above the 30 log-point threshold. Mean per-case placebo rank-p = 0.20. Polity-restricted attenuation check NOT RUN (Polity5 vintage not in repo); the polity-positive subset attenuation gate is DEFERRED.

Per-case synthetic control on log real GDP per capita (Maddison Project mpd2020).
Treated cases: {'KOR': 1961, 'TWN': 1960, 'SGP': 1965, 'CHN': 1978}.
Donor pool: ARG, BRA, MEX, CHL, IND, PAK, LKA, PHL, THA, GHA, EGY, TUR, IDN.
Horizon: 40 years post-treatment, censored to 2018 (Maddison end).

## Per-case ATT and placebo rank

| Case | t-year | Pre-RMSPE | Post-RMSPE | Ratio | ATT @ horizon | Placebo rank | p |
|---|---:|---:|---:|---:|---:|:---:|---:|
| KOR | 1961 | 0.018 | 0.886 | 49.74 | +1.276 | 3/14 | 0.21 |
| TWN | 1960 | 0.002 | 0.768 | 506.50 | +1.216 | 1/14 | 0.07 |
| SGP | 1965 | 0.026 | 0.850 | 33.26 | +1.174 | 3/14 | 0.21 |
| CHN | 1978 | 0.018 | 0.549 | 30.85 | +0.688 | 4/14 | 0.29 |

**Average ATT at 40-yr horizon:** +1.088 log-points (~+197%).
**Cases ≥0.30 log-points:** 4/4.
**Mean per-case placebo p:** 0.20.

## Per-case donor weights

### KOR (treated 1961)

| Donor | Weight |
|---|---:|
| EGY | 0.919 |
| PAK | 0.060 |
| BRA | 0.021 |

### TWN (treated 1960)

| Donor | Weight |
|---|---:|
| EGY | 0.552 |
| BRA | 0.234 |
| MEX | 0.083 |
| TUR | 0.082 |
| IDN | 0.049 |

### SGP (treated 1965)

| Donor | Weight |
|---|---:|
| CHL | 0.447 |
| THA | 0.399 |
| BRA | 0.154 |

### CHN (treated 1978)

| Donor | Weight |
|---|---:|
| IND | 0.746 |
| GHA | 0.116 |
| PAK | 0.072 |
| IDN | 0.065 |

## Method downgrade note

The YAML's `synth_did` template (Arkhangelsky-Athey-Hirshberg synthetic DiD,
with both unit and time weights jointly optimised) is approximated here by
per-case synthetic control averaged across cases. Inference uses each case's
rank within its own donor-as-placebo distribution rather than the joint
synth-DiD bootstrap. This is a power-losing simplification — disclosed.

The pre-registered Polity-attenuation gate (rerun on polity-positive donor
subset only) is DEFERRED: Polity5 vintage not in `data/vintages/`. When that
fetcher lands, the v1.1 rerun resolves the third falsification component.

## Steelman-live concerns

1. KOR/TWN/SGP/CHN starting incomes were already converging-leaders in 1960;
   selection on initial trajectory (Maddison 1950s data is sparse for several
   donors) may inflate ATT.
2. Donor pool conflates Latin-American populist-mercantilist with South-Asian
   import-substituting and African post-colonial — heterogeneous controls.
3. CHN 1978 is post-Cultural-Revolution rebound; pre-trend rebound dynamics
   inflate the gap independent of industrial policy content.
4. Maddison 2020 ends 2018; modern East Asian convergence in the 2018-2024
   window is not in this run.
5. The hypothesis is in tension with `trade_liberalisation_growth_effect`;
   both stories can hold (selective-protection + openness combo).

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
