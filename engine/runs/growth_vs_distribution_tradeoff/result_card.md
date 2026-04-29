# Result card — Growth vs distribution tradeoff (welfare architecture)

**Verdict:** PARTIAL — directional but does not meet all three thresholds; Δgrowth=+1.11pp, Δgini=+8.6, Δdebt=+4.4pp.

_NOTE: spec calls for wealth Gini; this run uses disposable-income Gini (SI.POV.GINI) as proxy because wealth Gini is data-gated._

## Cluster means (between-country, descriptive)

| Cluster | Growth (yoy %) | Gini (income, SI.POV.GINI) | Gross debt / GDP (%) |
|---|---:|---:|---:|
| forced_saving | 2.47 | 38.2 | 48.9 |
| tax_transfer | 1.36 | 29.6 | 53.4 |
| hybrid | 1.23 | 37.1 | 59.9 |
| **forced − tax_transfer** | **+1.11** | **+8.6** | **debt: +4.4 (tt − fs)** |

## TWFE regression coefficients (country + year FE; hybrid = reference)

Country FE absorb time-invariant architecture; identification comes from
AUS 1992 super introduction and CHL 2008 solidarity-pillar transition.
Coefficients are within-country deviation; the cluster means above are
the between-country evidence the spec also asks for.

### Outcome 1 — annual real GDP per capita growth (%)

| Term | Estimate | SE | p | n |
|---|---:|---:|---:|---:|
| arch_forced_saving | +1.204 | 0.287 | 0.000 | 525 |
| arch_tax_transfer  | +nan | nan | nan | — |

### Outcome 2 — disposable-income Gini (SI.POV.GINI)

| Term | Estimate | SE | p | n |
|---|---:|---:|---:|---:|
| arch_forced_saving | +5.157 | 1.802 | 0.005 | 321 |
| arch_tax_transfer  | +nan | nan | nan | — |

### Outcome 3 — gross general govt debt / GDP (IMF GGXWDG_NGDP)

| Term | Estimate | SE | p | n |
|---|---:|---:|---:|---:|
| arch_forced_saving | +4.069 | 5.057 | 0.421 | 483 |
| arch_tax_transfer  | +nan | nan | nan | — |

## Falsification rule applied

Spec requires ALL three thresholds:
- Δ growth (forced − tax_transfer) > −0.5 pp/yr (one-sided): **✓** (+1.11pp)
- Δ Gini (forced − tax_transfer) < +5 pts (one-sided): **✗** (+8.6pts)
- Δ debt-to-GDP (tax_transfer − forced_saving) ≥ 10pp: **✗** (+4.4pp)

## Steelman live concerns

See `hypotheses/steelman/growth_vs_distribution_tradeoff.md`. Key concerns:
1. Wealth Gini is the spec primary; income Gini under-states the architectural
   distinction (forced-saving builds household wealth that is not in income flows).
2. SGP and CHE score among the world's highest on government effectiveness;
   architecture-vs-outcomes is heavily confounded with state capacity.
3. Country FE absorb most architecture variation; identification leans on AUS 1992
   and CHL 2008 transitions which have many other contemporaneous reforms.
4. The N is too small for robust inference on cluster contrast — 4 forced-saving
   countries (after AUS/CHL splits) vs 8 tax-transfer.

## Provenance

Data: WDI NY.GDP.PCAP.KD, SI.POV.GINI, NE.TRD.GNFS.ZS, SP.POP.TOTL, SP.URB.TOTL.IN.ZS;
WGI GE.EST; IMF GGXWDG_NGDP. See `manifest.yaml`. Reproduces from `replication.py`.
