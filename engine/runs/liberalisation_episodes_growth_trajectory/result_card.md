# Liberalisation episodes and growth trajectory

**Verdict:** refuted — Both the post-reform growth pickup and the clean-pre-trend conditions fail. h=3 -0.47pp (p=0.30); h=5 +1.99pp (p=0.17); h=10 +0.34pp (p=0.68). Pre-trends: h=-3 -1.28pp; h=-5 +5.62pp.

## Summary

- Episodes detected: **31** across **31** countries (year of largest 5-year jump in Fraser EFW aggregate score per country, conditional on jump ≥ +0.5 points).
- Method validity: **OK** — event study estimates GDP-per-capita log-growth deviation from country mean at horizons [-5, -3, 0, 3, 5, 10].

### Event-study coefficients (excess log-growth over country baseline)

| Horizon h | Coef | SE | p | n cells |
|---:|---:|---:|---:|---:|
| -5 | +5.62pp | 2.29pp | 0.004 | 31 |
| -3 | -1.28pp | 0.58pp | 0.028 | 31 |
| +0 | +4.39pp | 1.72pp | 0.000 | 31 |
| +3 | -0.47pp | 0.47pp | 0.300 | 31 |
| +5 | +1.99pp | 1.56pp | 0.170 | 31 |
| +10 | +0.34pp | 0.66pp | 0.676 | 29 |

## Method

- **Treatment**: liberalisation episode at the country-year of the LARGEST 5-year jump in Fraser EFW aggregate score (`efw_summary`) per country, conditional on that jump being ≥ +0.5 points. One episode per country (the EFW panel is 5-year-spaced 1970-2000 and annual after, so 5 yr is the natural unit; one-per-country prevents stacked-event-study double-counting of the same multi-decade reform wave).
- **Outcome**: real GDP-per-capita log-growth (year-on-year), preferring NY.GDP.PCAP.PP.KD (PPP) and falling back to NY.GDP.PCAP.KD where PPP is missing. 2020 dropped (COVID).
- **Event study**: per (country, episode, h), average growth in years e+h ± 1, demean by country sample mean, then average across (country, episode) cells. Country-block bootstrap (1000 reps) for SE / two-sided p-values.
- **Falsification rule (sharpened)**: SUPPORTED requires h ∈ {3,5,10} all ≥ +0.5pp/yr AND p<0.1; AND pre-trend at h ∈ {-3,-5} not significantly positive. REFUTED if either condition fails.

## Data

- fraser_efw:efw_panel (Economic Freedom of the World, aggregate score)
- world_bank_wdi:NY.GDP.PCAP.PP.KD (PPP per-capita GDP)
- world_bank_wdi:NY.GDP.PCAP.KD (constant-USD per-capita GDP, fallback)

## Caveats

- Episode catalogue is derived from EFW jumps, which is an indicator-based (not narrative) coding. Spec mentions Sachs-Warner and Wacziarg-Welch dating; those would refine the catalogue but are not on disk.
- Event horizons constrained by EFW coverage (most countries from 1980; pre-1980 episodes therefore underweighted).
- Country baseline-demeaning absorbs slow-moving country-fixed differences; richer two-way FE would need iterative within-estimation. Block-bootstrap by country mimics country-clustered SEs.
