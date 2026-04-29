# BLOCKED — immigration_crime_rate_vs_native_controlled

**Status:** blocked at v1 wiring stage.

## Reason

The pre-registered outcome is **per-capita crime rates by nativity** (foreign-born vs native-born), disaggregated by offence type, sourced from destination-country administrative releases (SCB Sweden, BKA Germany, ONS England-Wales, FBI UCR US, CBS Netherlands). No such nativity-disaggregated crime-rate panel exists in `data/vintages/`. The only crime-related WDI series available is `VC.IHR.PSRC.P5` (intentional homicides per 100k, aggregate by country and year) — this cannot be split by nativity, gender, age, or offence type and therefore cannot be used to estimate the spec's log-rate-ratio outcome.

Channel availability is also limited:
- Age, gender, SES composition by nativity — not in vintages (would require destination-country admin microdata or harmonised survey extracts such as ESS, EU-SILC by migrant background).
- Years-since-arrival, legal-status mix — not in vintages.
- Neighbourhood concentration / segregation indices — not in vintages.

## Honest identification disclosure (per task instructions)

Even if proxy data were assembled from country-aggregate sources, this hypothesis is **fundamentally correlational** without an instrument. The spec's `decomposition_channels` (age, gender, SES) are mediator-style controls; they cannot recover a causal foreign-born effect because:
- Migration into a destination country is selected on unobservables (motivation, prior labour-market history) that also predict offending.
- "Reporting-rate bias" (police-recorded vs self-reported victimisation) is not separately identifiable without parallel survey panels (NCVS / Veiligheidsmonitor / CSEW), which are not in vintages.

When this hypothesis is unblocked, the result card should record verdict as **PARTIAL / DESCRIPTIVE** rather than SUPPORTED/REFUTED unless the spec's pre-registered cutoff (|log-rate-ratio| < 0.10 in ≥60% of countries) fires unambiguously, and should explicitly flag the residual selection-on-unobservables and reporting-bias channels as un-identified.

## Path to unblock

1. Add destination-country admin fetchers — Sweden BRÅ, Norway SSB, Netherlands CBS, England-Wales ONS, Germany BKA (where ethnicity disclosure is legally permitted) — for nativity- and offence-type-disaggregated rates.
2. Add EU-SILC / ESS extracts for age-sex-SES composition by migrant background.
3. Add destination-country segregation indices (Dissimilarity Index from harmonised census microdata).
4. Add complementary self-report victimisation surveys (NCVS, CSEW, Veiligheidsmonitor) for reporting-bias triangulation.

Pre-registration is preserved; the v1 pipeline cannot execute the decomposition until at least the outcome panel ships.
