# Blind source-key plan: female participation and later income growth

This new v2 tests the direct female-participation/growth direction of archived `demo_female_lfp_growth_panel` with an earlier exposure and later outcome. The archive's 1980–2023 same-period result is known and remains unchanged. The new estimate does not test its gender-gap magnitude, income-group heterogeneity, or a causal labour-policy effect. One outcome is one independent family.

The two pinned WDI Parquet schemas contain `country_iso3`, `year`, and `value`. A key-only screen found 216 ISO 3166 alpha-3 or XKX national areas with every required key. Key presence says nothing about non-null or valid measurements. Female participation uses `SL.TLF.CACT.FE.ZS`; real GDP per person uses `NY.GDP.PCAP.KD`. Their exact vintage paths and SHA-256 hashes are in the specification.

The complete registration is committed and checked against the full repository schema before selected values or null masks are read. A subsequent metadata-only source lock freezes the exact roster and selected key hashes in a separate commit. The runner is committed before execution. Exact replay is required. A valid result can receive public descriptive-calibration visibility only: zero causal, policy, school, position, or featured credit.
