# Female participation and later income growth: prospective v2 result audit

## Question and claim match

The archived \`demo_female_lfp_growth_panel\` asks whether female labour-force participation predicts per-capita growth. Its old 1980–2023 same-period panel run was PARTIAL (coefficient −0.1949, p=0.174). The new ID \`wdi_female_lfp_2005_2015_forward_income_growth_v2\` asks a narrower, genuinely forward question: whether the 2005–2015 change in the WDI female participation rate predicts annualized real GDP-per-person growth in 2015–2023 after conditioning on 2005 participation, 2015 income, and prior 2005–2015 income growth. It does not test the old claim's gender-gap magnitude, income-group heterogeneity, or causal mechanism; the old verdict and policy/school mappings are unchanged.

## Source custody and chronology

The complete new specification, steelman, and blind key-only plan first appeared in registration commit \`56cc1171e67d7b666254f05e019d3928a2b35602\`. Full \`scripts/validate_specs.py\` passed on that committed registration before any selected values or null masks were read (6,320 specifications validated). The separate metadata-only source lock first appeared in \`6b866f32e41b0b1754a11563e6046b2f39940223\`; the exact runner first appeared in \`c97e0ec88418b2125ce3934cb342cdea99edcef4\`. Result artifacts first appeared after these commits in \`14ee5c6d4f9e5a8423876aa9b573e6c9fe39faaf\`. The first-registration index reports this new spec as strict/verified.

The lock fixes 216 ISO 3166 alpha-3 or XKX national areas with the required country/year keys. It records 432 selected female-LFP keys and 648 selected real-income keys, their SHA-256 key digests, full source schemas, and these unchanged repository-relative source vintages:

- \`data/vintages/world_bank_wdi/SL.TLF.CACT.FE.ZS@2026-05-05T194807Z.parquet\`: SHA-256 \`c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186\`.
- \`data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet\`: SHA-256 \`0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f\`.

Key presence was not counted as a valid numeric observation. The frozen valid-value rules yielded 177 complete national areas; overlapping exclusion counts are 30 with invalid/missing female participation and 21 with invalid/missing income. Thirty-one complete areas had participation gains of at least five percentage points; the gain IQR was 5.044 percentage points. All sample and variation floors passed.

## Result and limits

The exposure coefficient was **+0.1992 annualized log-growth percentage point per 10-point female-LFP gain** (HC3 SE 0.4197, two-sided Student-t p=0.6357). The largest single area's share of squared residualized exposure was 0.078, below the frozen 0.20 limit. All 177 leave-one-area-out fits succeeded and retained a positive coefficient. The coefficient missed both the frozen +0.3 effect floor and p<=0.05, so the rule yields **PARTIAL**. This is neither evidence for a policy effect nor confirmation of the original panel's stronger magnitude and heterogeneity claims.

The runner reproduced all nine result artifacts byte-for-byte with \`--replay\`. An independent NumPy least-squares and HC3 sandwich calculation matched coefficient, SE, and p-value to floating-point precision. The source-lock hashes and first-addition commit sequence were checked by the runner. The temporary, untracked preregistration index reports 830 strict pairs, and the evidence-tier audit labels this ID \`calibration\`, \`public_visible: true\`, \`registration_status: verified\`, with no exclusion reasons. Relative to the clean source branch baseline, public-visible cases rise **579 → 580 (+1)**. This is one independent family and carries zero causal, policy, school, position, or featured credit.

Reproduction from the repository root: \`python3 scripts/run_wdi_female_lfp_forward_income_growth_2026.py --replay\`. Generated preregistration, evidence, census, and web indexes are left for consolidated regeneration; none are committed here.
