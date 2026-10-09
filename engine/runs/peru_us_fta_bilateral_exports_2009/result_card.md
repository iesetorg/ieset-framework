# peru_us_fta_bilateral_exports_2009

**Verdict: INCONCLUSIVE** — registered pretrend gate failed

This verdict tests a descriptive USA → PER merchandise-flow contrast. It does not identify the TPA's causal effect or welfare impact.

- Agreement effective: 2009-02-01.
- Pre: 2004–2008; post: 2010–2014; 2009 excluded from means.
- Donors: USA → ARG, BOL, BRA, ECU, PRY, URY; fixed before outcome access.
- CEPII source archive SHA-256: `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`.
- Small-slice SHA-256: `ff96d2b183fc42d243295f0e15d279e693dfb9d9665f5950399fdb702a3cbf75`.
- Registration commit: `a549d2f5ade4203a2c2061ae3cdcd44bebf1df9c`.
- Source slice commit: `8f1716597705b171a6bb85d320e2643c8e89b263`.
- School score credit: zero.
- Pretrend gap: 0.031993 log units/year; maximum absolute gap 0.030000.

## Limits

Nominal BACI goods values mix volume and price changes. The countries differ in demand, product composition and policy context; the 2008–2009 crisis overlaps the event. CEPII `fta_wto` is agreement status, not measured tariff intensity. One treaty contributes one test.

Reproduce: `python3 scripts/run_peru_us_fta_bilateral_exports_2009.py verify`
