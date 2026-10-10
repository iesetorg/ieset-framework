# Electricity access gains and later female labour-force participation

**Verdict: PARTIAL** — descriptive calibration only; zero causal, policy, school, position, and featured credit.

Source-key economies: 216; complete cases: 182.
At least +10 percentage-point electricity gain: 48 countries; p90−p10 gain spread: 17.260000000000005 points.
HC3 slope: 0.0301664150751488 female participation percentage points per +1 point electricity access; two-sided p: 0.5491524210422969; frozen p cutoff: 0.01.
Frozen gate failures: none.
Five fixed country-hash holdouts: 5 positive, 0 negative.

Electricity access is population coverage rather than supply reliability. Female labour-force participation is an ILO-modelled 15+ rate including employed and unemployed women, not employment quality or unpaid work. Global development, schooling, fertility, industrial structure, income, and policy changes can shift both series.
Earlier electricity-to-growth and electricity-to-child-mortality tests were visible before this distinct outcome was chosen. A single-test p cutoff does not correct archive-wide selection.
Frozen registration `bcad143ca766d4e264d8d09ff8063b86b35fcb46`; later source lock `573943c37e4006d843c3a2324ec9e8573a1e2012`; documented pre-value custody erratum `f9aeb4638ca8a3ca17b1b595718fcb6a9f337cc5`. Exact replay: `python3 -B scripts/run_wdi_electricity_female_lfp_2026.py --verify`.
