# Result card — German Energiewende industrial cost trajectory

**Verdict:** refuted — Germany's industrial GVA gap on 2015-2020 average is +0.095 log (wrong sign for industrial-cost-penalty story), placebo p=0.4444444444444444.

Outcome: log industrial GVA real (WDI NV.IND.TOTL.KD). Treated: DEU. Donors used: FRA, SWE, NOR, FIN, NLD, BEL, ITA, ESP.
Pre-period 2005-2010; post-period 2011-2024.
Treatment date: 2011 (Energiewende formal enactment).

## Synthetic control fit

| Metric | Value |
|---|---:|
| Pre-period RMSPE | 0.0146 |
| Post-period RMSPE | 0.0842 |
| Post/Pre RMSPE ratio | 5.78 |
| Mean post-2011 gap (DEU − synth) | +0.059 log |
| Cumulative post-2011 gap | +0.826 log-yr |
| Mean 2015-2020 gap (excl. war) | +0.095 log |
| Placebo rank | 4/9 |
| Placebo p-value | 0.4444444444444444 |

## Donor weights

| Donor | Weight |
|---|---:|
| FRA | 0.000 |
| SWE | 0.828 |
| NOR | 0.000 |
| FIN | 0.000 |
| NLD | 0.172 |
| BEL | 0.000 |
| ITA | 0.000 |
| ESP | 0.000 |

## Pre-trend gap series (log industrial GVA, DEU − synthetic)

| Year | DEU | Synth | Gap |
|---:|---:|---:|---:|
| 2005 | 0.000 | 0.000 | +0.000 |
| 2006 | 0.048 | 0.049 | -0.001 |
| 2007 | 0.083 | 0.099 | -0.016 |
| 2008 | 0.069 | 0.059 | +0.010 |
| 2009 | -0.080 | -0.075 | -0.005 |
| 2010 | 0.057 | 0.027 | +0.030 |

## Post-period gap series

| Year | DEU | Synth | Gap |
|---:|---:|---:|---:|
| 2011 | 0.106 | 0.066 | +0.040 |
| 2012 | 0.108 | 0.038 | +0.069 |
| 2013 | 0.096 | 0.000 | +0.096 |
| 2014 | 0.136 | -0.002 | +0.139 |
| 2015 | 0.142 | 0.049 | +0.094 |
| 2016 | 0.177 | 0.053 | +0.124 |
| 2017 | 0.208 | 0.084 | +0.124 |
| 2018 | 0.220 | 0.106 | +0.114 |
| 2019 | 0.207 | 0.125 | +0.082 |
| 2020 | 0.146 | 0.111 | +0.035 |
| 2021 | 0.191 | 0.178 | +0.013 |
| 2022 | 0.171 | 0.205 | -0.034 |
| 2023 | 0.147 | 0.167 | -0.020 |
| 2024 | 0.107 | 0.156 | -0.049 |

## Data-status caveat

Original YAML primary outcome is IEA industrial electricity price (band IC, USD/MWh).
That fetcher has not landed; this v1 run uses log industrial GVA as the downstream
output proxy for the price→output transmission story. The pre-registered second-stage
regression of manufacturing VA on the synthetic-control price gap CANNOT run without
the IEA series and is deferred. The verdict is therefore reported as v1 partial:
the run tests the COMBINED (price + transmission) effect at lower power, not the
isolated cost-penalty channel the YAML's primary specification calls for.

## Steelman-live concerns

1. 2022-2024 gas shock dominates post-period; the without-war sensitivity is reported.
2. DEU is the sole treated unit — synthetic-control external validity is narrow.
3. 2011 treatment date conflates Energiewende decision with 2014-2017 plant closures
   and 2022 final phase-out; YAML asks for 2022 as secondary date (not separately run here).
4. Industrial GVA captures industrial composition shifts (e.g. EVs vs. ICE) that may
   move independent of energy-cost channel.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
