# Fiscal multipliers at the ZLB vs normal regime

**Verdict:** inconclusive (data gap on quarterly OECD national accounts panel + Ramey-Zubairy / Guajardo-Leigh-Pescatori narrative fiscal-shock series; US-only OLS-LP diagnostic indicative only — h=8 ZLB multiplier -0.10 vs normal 0.52, gap -0.62, against claimed direction (ZLB <= normal); threshold for SUPPORTED would have been gap >= +0.50 on the panel LP-IV).

## Summary

The spec calls for a state-dependent LP-IV across an OECD panel of 21 countries (1995-2021), instrumenting government-spending innovations with the Ramey-Zubairy defence-news series and the Guajardo-Leigh-Pescatori narrative consolidations. Neither the quarterly OECD national-accounts panel (real GDP, government consumption) nor the narrative fiscal-shock series are on disk under any publisher. The pre-registered identification therefore cannot be run.

Missing inputs flagged by `assess_required_panel_inputs()`:

- oecd:NAQ_GDP (quarterly real GDP, panel)
- oecd:NAQ_government_consumption (quarterly govt consumption, panel)
- manual: Ramey-Zubairy defence-news / Guajardo-Leigh-Pescatori narrative consolidations

## Informative diagnostic - US-only OLS LP

To keep the run artefact-complete, this script also runs a US-only downgraded state-dependent OLS local projection on the FRED quarterly data (GDPC1, FGEXPND deflated by GDPDEF, FEDFUNDS for the ZLB indicator). Sample window 1995-2021 ex 2020Q2 (34 ZLB quarters, 73 normal quarters). The shock is the OLS innovation of dlog real federal expenditures after lag-1 controls (Auerbach-Gorodnichenko forecast-error proxy). Multiplier scaled by steady-state G/Y = 0.218. **This does not adjudicate the spec's panel-LP-IV claim** and is reported only to indicate whether the US signal points toward or away from the New-Keynesian prediction.

- h=4: ZLB multiplier 0.10 (n=30), normal multiplier 0.57 (n=71), gap -0.47.
- h=8: ZLB multiplier -0.10 (n=28), normal multiplier 0.52 (n=69), gap -0.62.
- h=12: ZLB multiplier -0.23 (n=28), normal multiplier 0.54 (n=65), gap -0.77.

At the spec's primary horizon h=8, the US-only diagnostic gap is -0.62 (threshold for SUPPORTED on the panel LP-IV would have been >= +0.50).

## Method (pre-registered, blocked)

1. Quarterly OECD-panel real GDP and government consumption (OECD NAQ_GDP / quarterly national accounts).
2. Country-quarter ZLB indicator constructed from short-rate <= 0.25%.
3. Narrative fiscal-shock series as instruments (Ramey-Zubairy defence-news; Guajardo-Leigh-Pescatori).
4. State-dependent local-projection IV a la Ramey-Zubairy / Auerbach-Gorodnichenko, country-clustered SEs, country+year FE.
5. Cumulative multiplier at h=8 quarters compared across the ZLB and normal regimes; SUPPORTED if (ZLB - normal) >= +0.50.

## Data

Available (US-only diagnostic):
- fred:GDPC1 (real GDP, quarterly)
- fred:FGEXPND (federal government expenditures, quarterly)
- fred:GDPDEF (GDP deflator, quarterly)
- fred:FEDFUNDS (effective federal funds rate, monthly to quarterly mean)

Required for the spec but missing on disk:
- oecd:NAQ_GDP (quarterly real GDP, panel)
- oecd:NAQ_government_consumption (quarterly govt consumption, panel)
- manual: Ramey-Zubairy defence-news / Guajardo-Leigh-Pescatori narrative consolidations

Fetcher backlog:
- OECD quarterly national accounts (NAQ_GDP, NAQ_government_consumption) for the 21-country panel.
- A `manual` publisher hosting the Ramey-Zubairy defence-news and Owyang-Ramey-Zubairy international-panel news shocks, plus the Guajardo-Leigh-Pescatori narrative consolidations.
