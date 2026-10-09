# U.S. minimum-wage timing and scope audit — 2026-10-09

## What the source measures

The pinned [U.S. Department of Labor history](https://www.dol.gov/agencies/whd/state/minimum-wage/history) is a table of selected **January 1** state and federal hourly rates, not a dated state-law event log. Its 39 selected years span 1968–2024; every year from 2005 through 2024 is present. The IESET `effective_minimum_wage` is the larger of the parsed state statutory rate and federal floor. A rise can therefore come from a federal change where the state rate does not bind.

## Timing repair

The original `data/derived/us_state_minimum_wage_treatment_panel.parquet` is retained byte-for-byte (SHA-256 `3e2c602b4eafcc922f0166d9cee2be33fc2882a6e5bb80858e55564d36dc2e44`) for historical replay. It used a within-state difference across the **previous observed** year and called that an annual change. There are 486 rows after a gap longer than one year, all before 2006: 175 were labeled `increase`, 18 `first_bind`, 3 `decrease`, and 290 `no_change`. Those 196 apparent change events cannot be dated to the listed January 1 year.

The separately pinned `us_state_minimum_wage_treatment_panel_v2.parquet` keeps the same 2,106 state-year levels, but assigns annual differences only when the preceding calendar year exists. The 486 gap rows are `interval_censored` with missing annual changes. A first observed binding rate is a `first_bind` event only with an adjacent prior nonbinding year. The v2 build has 20 such dated first-binding events. Its two small input vintages are pinned with the manifest and byte hashes. No original run packet, verdict, or panel was rewritten.

## Public hypothesis scope

The ten public `pcw100_us_mw_increase_event_*` hypotheses fit 2006–2024, a consecutive-year window. Their input treatment and event labels in that window match v2 row for row; this timing repair does **not** change their estimates or verdicts. Their registered transformation already says the **effective** floor rises, but the claim and result contrast call it a **state minimum-wage policy event**. In the exact 50-state-plus-DC frame, 419 of 969 state-years have a positive effective-floor change; 71 of those 419 (18 in 2008, 23 in 2009, 30 in 2010) have no state statutory rate above the federal floor. The corresponding increases came from federal floor changes. An earlier 402-event denominator came from a narrower count and is superseded here by the exact 419 rows used in the registered model (also reported as `high_n: 419` in its diagnostics).

An external scope-note registry now puts this distinction on each affected public hypothesis page and in its metadata. The original registration text and saved result remain visible as historical records. All ten remain **descriptive calibration**; the cards do not establish a state legislative treatment or a causal wage effect. They gain no featured or school credit from this repair.

## Checks

- Both copied input vintages matched the source checkout by SHA-256 and a schema/path/secret scan found no personal path or credential bytes.
- The 2006–2024 v2 effective levels, annual changes, and event types equal the original panel row for row; 486 earlier gaps have missing annual changes and `interval_censored` labels.
- The focused panel tests and web type check passed after the repair.
