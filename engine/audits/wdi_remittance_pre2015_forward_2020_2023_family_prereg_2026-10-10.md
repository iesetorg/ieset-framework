# Blind source-key plan: remittances and two later outcomes

This is one descriptive family with two genuinely different endpoints: external balance and real household consumption growth. The old wdi_remittance_current_account_cushion_2000_2023 and wdi_remittance_consumption_resilience_2009_2021 runs used selected high-remittance rosters and whole-period exposure means; their old results are known and do not grade the new forward estimates. The questions, periods, controls, source paths, SHA-256 hashes, floors, and two-test correction are fixed before selected values or null masks are opened.

All four source Parquet schemas contain country_iso3, year, and value. A key-only screen found 216 ISO 3166 alpha-3 or XKX economies with every required country/year key. Key presence does not establish non-null observations. The separate metadata-only source lock freezes the sorted roster, key hashes, exact source bytes, and registration commit.

Source hashes and paths are in the registered threshold. Remittances use BX.TRF.PWKR.DT.GD.ZS; current accounts use BN.CAB.XOKA.GD.ZS; consumption growth uses NE.CON.PRVT.KD.ZG; real income uses NY.GDP.PCAP.KD. Their respective vintages are dated 2026-04-30, 2026-05-05, 2026-04-30, and 2026-05-05.

After this registration commit passes full schema validation, run --prepare-lock using metadata and keys only, commit the lock, then run. Every result must be exact replayable. The family counts as one independent evidence family even if both cases become public calibration. No causal, policy, school, position, or featured credit.
