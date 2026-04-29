# Result card — Rule of law and institutional growth

**Verdict:** PARTIAL — only 0 of 3 legs pass falsification; panel β_RL=-0.0114 (p=0.713); cross-section β_RL=+0.0046 (p=0.066)

## Primary spec (TWFE, country + year FE; no GE control)

Outcome: 5-year-forward cumulative log GDP per capita growth.
Treatment: WGI Rule of Law (RL.EST). Controls: log GDP per capita,
trade openness, secondary school enrolment.

| Term | Estimate | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| rule_of_law | -0.0114 | 0.0310 | [-0.072, +0.049] | 0.713 | -0.37 |

n = 917 country-years, R² within = 0.227

## Robustness: TWFE with WGI Government Effectiveness added

| Term | Estimate | SE | p |
|---|---:|---:|---:|
| rule_of_law | -0.0289 | 0.0318 | 0.363 |
| gov_effective | +0.0472 | 0.0269 | 0.079 |

RL attenuation when GE added: -153% (above 70% threshold).

## Cross-section (country means)

n = 59 countries.
β_RL on mean annual log growth = +0.0046 (SE 0.0025, p 0.066, t +1.84). R² = 0.491.

## Falsification rule applied

Spec requires at least 2 of 3 legs:
- Panel TWFE β_RL > 0 at p<0.05: **✗**
- Cross-section β_RL > 0 at p<0.05: **✗**
- Coefficient attenuation when GE added < 70%: **✗** (-153%)

Pass count: **0 / 3**.

## Steelman live concerns

See `hypotheses/steelman/rule_of_law_institutional_growth.md`. Key concerns:
1. WGI subcomponents (RL, GE, CC, RQ) are highly collinear; identifying off
   the non-overlapping component is fragile (Glaeser-La Porta 2004).
2. Reverse causality: faster-growing countries may attract investment that
   improves rule-of-law perceptions (which is what WGI measures).
3. WGI is a perception index averaged across analyst sources, not an
   institutional outcome measure; halo bias plausible.
4. 5-year-forward growth windows shrink the sample at the panel ends.

## Provenance

Data: WDI NY.GDP.PCAP.KD, NE.TRD.GNFS.ZS, SE.SEC.ENRR; WGI RL.EST, GE.EST.
See `manifest.yaml`. Reproduces from `replication.py`.
