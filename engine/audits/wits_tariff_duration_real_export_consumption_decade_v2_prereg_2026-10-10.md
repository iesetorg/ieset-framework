# Blind source-key plan: tariff duration and two real outcomes

This is the first-addition plan for one new descriptive hypothesis:
wits_tariff_duration_real_export_consumption_decade_v2. It is a new ID.
The verified archived tariff_protection_duration_growth_drag result stays
archived. Its old generic PARTIAL regression used current tariff level and
private-consumption share, whereas its frozen claim requires constructed
protection duration plus real exports and real consumption per person. The
original rule also gives conflicting roles to its frontier subsample. The
new design fixes one measured two-outcome question before looking at the
selected treatment or outcome values.

## Source-key screen

The source-key roster is exactly the 66 countries in the archived claim
minus TWN, whose keys are absent from all selected WITS, WDI, and WGI files.
All other 65 countries have the required country/year keys: ten WITS
tariff years 2001–2010; twenty WDI real-export-growth years 2001–2020;
WDI real private-consumption-per-person years 2000, 2010, and 2020;
and 2010 keys for GDP per person, WGI rule of law, merchandise terms of
trade, and gross investment share. This is an upper bound only: row keys
may exist where values are null or invalid. No selected value, null mask,
observation status, coefficient, or fit was opened for the new design.

| Role | Exact preserved file | Source custody |
| --- | --- | --- |
| Weighted applied merchandise tariff | data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet | data/manifests/fetch_run_2026-07-23T151550Z.yaml |
| Real goods-and-services export growth | data/vintages/world_bank_wdi/NE.EXP.GNFS.KD.ZG@2026-05-03T054026Z.parquet | data/manifests/baseline_pull.yaml names the indicator; no exact fetch-time manifest for this local vintage was found |
| Real private consumption per person | data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet | data/manifests/fetch_run_2026-05-05T200056Z.yaml |
| Real GDP per person | data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet | same May 5 fetch manifest |
| Rule of law | data/vintages/wgi/GOV_WGI_RL.EST@2026-05-05T195218Z.parquet | same May 5 fetch manifest |
| Merchandise terms of trade | data/vintages/world_bank_wdi/TT.PRI.MRCH.XD.WD@2026-05-05T203119Z.parquet | data/manifests/fetch_run_2026-05-05T203305Z.yaml |
| Gross investment share | data/vintages/world_bank_wdi/NE.GDI.TOTL.ZS@2026-05-05T194659Z.parquet | same May 5 fetch manifest |

The six sources with exact fetch manifests must match their manifest
Parquet paths and SHA-256 digests during source-lock preparation and replay.
The export baseline configuration is checked for its indicator but cannot
substitute for a missing fetch receipt.

The 65 keys are source-key candidates, not 65 measured cases. The outcome
is real exports of goods and services, not nominal merchandise exports or
export complexity. The WITS tariff series is the weighted mean applied
merchandise tariff, not a legislative event or sector protection schedule.
The export vintage's missing fetch-time manifest is a binding
source-custody limit even if its bytes are locked and exactly replayed.
The original local byte hash, raw Parquet metadata, and fetcher method are
recorded in `engine/audits/wits_tariff_duration_real_export_consumption_decade_v2_source_provenance_2026-10-10.md`.

## Frozen decision

For each of the 65 candidates, require all 2001–2010 tariff values and
construct exposure as years strictly above 15 percent divided by ten.
Use 2010 tariff level as a separate control. Future export growth is the
2011–2020 mean of annual real-export-growth rates. Future private-consumption
growth is the 2010–2020 annualised log change of positive real expenditure
per person. Fit both outcomes on the identical complete-country sample
with the exact controls and HC3 estimator in the YAML and runner. Each model
has its own matching 2001–2010 outcome pretrend.

A valid model needs at least 40 countries; at least 10 zero-duration
countries and 10 with two or more high-tariff years; full rank and finite
uncertainty; single-country residualized-duration concentration at most
20 percent; and at least 35 successful leave-one-country-out fits with
no more than two failures for each endpoint. Any failure is INCONCLUSIVE. Both endpoints are co-primary.
Two-sided p<=0.025 is the fixed Bonferroni threshold. REFUTED takes
precedence for a positive, meaningful, stable coefficient in either
endpoint; SUPPORTED needs both coefficients negative, meaningful and
stable; otherwise PARTIAL. There is no alternate window, source, unit,
country, model, or gate selected after reading values.

The first commit must add the YAML, steelman, this plan, source
provenance note, and frozen runner.
A later commit must add the source-byte and key lock produced by the runner.
Only after that later commit may the runner read selected values or emit
result artifacts. The archived original ID and its files must remain
unchanged. One successful public result is one descriptive calibration
record, never policy, causal, school, position, or featured evidence.
