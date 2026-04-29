# Result card — German decline 2018-2025: regulatory not fiscal

**Verdict:** partial — DEU below synthetic by -0.251 cumulative over 2018-2022 (sign correct), but magnitude or placebo p=0.36363636363636365 below pre-registered thresholds. Regulatory-vs-fiscal channel split unresolved (data-gated).

Outcome: log industrial GVA real (WDI NV.IND.TOTL.KD), rebased per country.
Treated: DEU. Donors used: FRA, NLD, BEL, ITA, ESP, POL, CZE, AUT, SWE, FIN.
Pre 2005-2017, post 2018-2025.

## Synthetic control fit

| Metric | Value |
|---|---:|
| Pre-period RMSPE | 0.0271 |
| Post-period RMSPE | 0.0872 |
| Post/Pre RMSPE ratio | 3.21 |
| Mean post-2018 gap | -0.072 log |
| Cumulative 5-yr gap (2018-2022) | -0.251 log-yr |
| Placebo rank | 4/11 |
| Placebo p-value | 0.36363636363636365 |

## Donor weights

| Donor | Weight |
|---|---:|
| FRA | 0.000 |
| NLD | 0.000 |
| BEL | 0.000 |
| ITA | 0.000 |
| ESP | 0.000 |
| POL | 0.183 |
| CZE | 0.000 |
| AUT | 0.333 |
| SWE | 0.484 |
| FIN | 0.000 |

## Post-period gap

| Year | DEU (rebased) | Synth | Gap |
|---:|---:|---:|---:|
| 2018 | 0.220 | 0.213 | +0.007 |
| 2019 | 0.207 | 0.231 | -0.024 |
| 2020 | 0.146 | 0.197 | -0.051 |
| 2021 | 0.191 | 0.253 | -0.062 |
| 2022 | 0.171 | 0.293 | -0.122 |
| 2023 | 0.147 | 0.263 | -0.116 |
| 2024 | 0.107 | 0.241 | -0.134 |

## Fiscal-channel partial check (degraded)

Available channels: debt_gdp, trade_open

- `debt_gdp_deu_delta_2017_to_2023` = -1.700
- `debt_gdp_donor_avg_delta_2017_to_2023` = +2.291
- `debt_gdp_deu_minus_donor_delta` = -3.991
- `trade_open_deu_delta_2017_to_2023` = +4.508
- `trade_open_donor_avg_delta_2017_to_2023` = +5.006
- `trade_open_deu_minus_donor_delta` = -0.498

**Regulatory-channel status:** PENDING (OECD EPS, IEA elec price, Russia gas share fetchers required)

## Data-status caveat

The hypothesis's HEADLINE test is the regulatory-vs-fiscal variance decomposition
of the post-2018 synthetic gap. Running it requires:
- OECD Environmental Policy Stringency index — pending
- IEA industrial electricity price — pending
- Russian gas import share — pending
- China industrial-production index — pending
- OECD SDD household disposable income — pending

v1 here runs the synthetic-control divergence only. The verdict gates on the
synthetic-control component of the falsification rule; the regulatory-vs-fiscal
channel-attribution component is reported as PENDING and does not contribute to
the verdict. When the four pending fetchers ship, v1.1 reruns and the verdict
resolves cleanly.

## Steelman-live concerns

1. 2020-2021 COVID and 2022-2023 Russia-Ukraine energy shock are large confounds
   in the post-2018 window; sensitivities pending.
2. DEU sole treated unit; external validity narrow.
3. The 'regulatory-vs-fiscal' framing requires both bundles fully measured to
   evaluate — currently fiscal-side has WDI gov consumption + IMF debt/GDP
   available; regulatory-side awaits EPS + IEA + gas-share.
4. Industrial GVA reflects sector-mix shifts (e.g. EVs, software) independent of
   the regulatory channel.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
