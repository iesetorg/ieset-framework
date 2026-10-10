# Blind source-key plan: out-of-pocket financing and later child mortality

This is one new descriptive ID. The two old generic health-financing
results are known, but neither fitted the actual out-of-pocket share
change against the later under-five-mortality change with this covariate
set. The earlier `wdi_out_of_pocket_health_spending_mortality_panel` runner
used **SH.XPD.CHEX.GD.ZS** (total spending as GDP share) as its treatment
despite the title. The `decommodified_health_oop_spending_mortality_panel`
generic run had the same treatment mismatch and a broader claim. Neither
old result will be relabelled or counted as evidence for this new question.

The selected May 5 WDI Parquet schemas have country/year/value columns.
A key-only screen found 216 ISO 3166 alpha-3 or XKX economies/territories
with every required source key. Key presence says nothing about value
completeness. No selected `value`, null mask, status, coefficient, or model
fit was opened. The source-lock step will freeze the exact sorted key
roster and hashes before any selected value may be read.

| Role | Exact local vintage | Exact fetch manifest | Required years |
| --- | --- | --- | --- |
| Out-of-pocket share of current health expenditure | `data/vintages/world_bank_wdi/SH.XPD.OOPC.CH.ZS@2026-05-05T203530Z.parquet` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` | 2005, 2015 |
| Under-five mortality per 1,000 | `data/vintages/world_bank_wdi/SH.DYN.MORT@2026-05-05T194907Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` | 2005, 2015, 2023 |
| Real GDP per person | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` | 2005, 2015 |
| Current health expenditure share of GDP | `data/vintages/world_bank_wdi/SH.XPD.CHEX.GD.ZS@2026-05-05T203513Z.parquet` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` | 2015 |

The runner must verify exact source Parquet SHA-256 values against these
manifests, check selected keys only, and write a metadata-only source lock.
The spec, steelman, this plan, and runner must enter Git in one first-addition
registration commit. The source lock must enter in a later commit. Only then
may the runner read the selected values or produce a result. Its exact
replay compares the nine standard run artifacts byte for byte. This design
has one endpoint and grants no policy, causal, school, position, or featured
score credit.
