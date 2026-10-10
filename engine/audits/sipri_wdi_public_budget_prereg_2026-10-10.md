# Prospective SIPRI military burden → later public-spending intensity

This is a bounded **two-cell correlated extension** of existing SIPRI military-burden hypotheses. It tests education and domestic public-health spending intensities, not independent data sources or causal substitutions. Both cells are retained in the family-wide 0.01/2 multiplicity denominator, including failed cells. The local correction does not repair archive-wide selection.

## Value-blind source and design freeze

Only source metadata, manifests, file hashes, schemas, country identifiers, years and indicator IDs were used. The shared immutable roster has 2310 physical opportunities, 165 ISO3 countries and annual t=2003–2016 anchors. WDI supplies full country/year skeletons, so these are upper bounds, not complete-case counts. No selected SIPRI/WDI measurements, WDI status columns, value-null masks or signs were opened before this registration. Commit both specs, steelmans, roster, this plan and the runner together. Commit the exact source lock separately. The runner checks both commits before its first value read.

## Locked test

Treatment: SIPRI military expenditure percent GDP change t−3→t. Two separate outcomes: WDI government education expenditure percent GDP, and WHO-sourced WDI domestic general government health expenditure percent GDP, each changing t→t+3. Controls: the same outcome's prior t−3→t change and t level, WDI general government expense percent GDP at t, and log constant-dollar GDP per capita at t. Country and annual anchor fixed effects. Equal rows, country CR1 standard errors, Student t(G−1), two-sided 99.5% intervals. Five fixed country-hash omission folds. Yearly windows overlap.

Complete cases require exact endpoints and blank/A WDI status; finite range 0–20 percent GDP for military/outcome levels, |three-year changes|≤5 percentage points for military and both prior/future outcome changes; general expense 0–100 and real income >0. At least three complete anchors per retained country, 300 complete rows, 50 countries, 10 distinct anchors, 60 material military changes (≥0.25 points) spanning 20 countries; residualized treatment SD≥0.15 and outcome SD≥0.10 points; top 1% rows ≤25% and top country ≤20% of residual treatment sum of squares; full-rank designs and finite CR1 uncertainty. Each omission fold needs 200 rows and 35 countries. Failed gates yield INCONCLUSIVE. Otherwise a beta≤−0.30 (or ≥+0.30), p≤0.005, and ≥4/5 same-sign fold betas is SUPPORTED (or REFUTED); weaker results are PARTIAL.

## Source custody and rights

SIPRI `milex_share_gdp` is derived from [SIPRI Milex XLSX](https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1948-2023.xlsx); raw redistribution is limited by [SIPRI terms](https://www.sipri.org/about/terms-and-conditions). The October 2026 WDI indicator API vintages are government education `SE.XPD.TOTL.GD.ZS` (UNESCO), domestic public health `SH.XPD.GHED.GD.ZS` (WHO GHED), government expense `GC.XPN.TOTL.GD.ZS`, and constant-dollar income `NY.GDP.PCAP.KD`; WDI metadata states CC BY 4.0. Exact routes, cache SHA-256 and fetch manifest SHA-256 are pinned in the runner and source lock. Raw Parquets remain ignored. Packets contain derived diagnostics only.

The measures share a GDP denominator. Security, fiscal and national-accounting shocks can move both. The two outcomes are related budget-intensity indicators, not proof of a tradeoff, and do not earn causal, policy, school, position or featured credit.
