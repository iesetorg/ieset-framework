# Electricity access and later female labour-force participation — locked result

Registration `bcad143ca766d4e264d8d09ff8063b86b35fcb46` strictly preceded source lock `573943c37e4006d843c3a2324ec9e8573a1e2012` and the measured run. A later pre-value custody erratum `f9aeb4638ca8a3ca17b1b595718fcb6a9f337cc5` records the electricity file already tracked in the base; the analysis rule was unchanged.
The two exact WDI raw files were SHA-256 checked against the tracked fetch manifest; WDI metadata lists CC-BY-4.0 and attributes the labour series to ILO modelled estimates.

**Verdict: PARTIAL**. Complete countries: 182/216; material gain countries: 48; access gain p90−p10 spread: 17.260000000000005 points.
HC3 slope: 0.0301664150751488 female LFP percentage points per +1 electricity point; two-sided p: 0.5491524210422969; threshold: 0.01; failed gates: none.
Five deterministic hash-fold holdouts: +5/5, -0/5.

This single descriptive test was selected after visible archive electricity-to-growth and electricity-to-child-mortality studies, which use different outcomes. The p cutoff is not an archive-wide selection correction. No causal, policy, school, position, or featured credit.
World Bank indicator definitions: [access to electricity](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS), [female labour-force participation](https://data.worldbank.org/indicator/SL.TLF.CACT.FE.ZS).
Exact replay: `python3 -B scripts/run_wdi_electricity_female_lfp_2026.py --verify`.
