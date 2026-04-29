# Eurozone fiscal-rule departure -> sovereign-spread response

**Verdict:** inconclusive (data gap on 6 sovereign-yield series: fred:IRLTLT01GRM156N, fred:IRLTLT01IEM156N, fred:IRLTLT01PTM156N, +3 more) — primary event-study cannot run; per HYPOTHESIS_FRAMEWORK_AUDIT §E2 a method-validity failure emits inconclusive rather than refutation. Re-run once a fetcher lands the ECB IRS or FRED IRLTLT01* series.

## Summary

The pre-registered event-study test cannot be computed in the current data state. The PRIMARY outcome — cumulative h=20 trading-day spread (10y country yield minus 10y Bund) response across a panel of EDP-escalation / SGP-breach / budget-revision events for {GRC, IRL, PRT, ESP, ITA} in 2009-2011 — requires per-country sovereign-yield series and a German Bund 10y series. Neither is on disk in the current vintage tree:

- Missing series (6):
  - `fred:IRLTLT01GRM156N`
  - `fred:IRLTLT01IEM156N`
  - `fred:IRLTLT01PTM156N`
  - `fred:IRLTLT01ESM156N`
  - `fred:IRLTLT01ITM156N`
  - `fred:IRLTLT01DEM156N`

Per the framework's invariants on provenance and method-validity (HYPOTHESIS_FRAMEWORK_AUDIT.md §E2), data gaps on the primary outcome emit `inconclusive`, NOT a refutation. The verdict is neutral on the scoreboard pending a fetcher pass.

## Method (will run when data lands)

Event-study cumulative spread response across the pre-registered
event panel:

- GRC 2009-10-20 — ELSTAT/Papandreou deficit revision
- GRC 2009-12-08 — Fitch downgrade GRC to BBB+
- IRL 2010-09-30 — IRL bank recap / EDP intensification
- PRT 2010-04-27 — S&P downgrade PRT to A-
- ESP 2010-04-28 — S&P downgrade ESP to AA
- ITA 2011-08-05 — ECB Trichet-Draghi letter / BTP-Bund blowout

Spread response = (country_yield_t+20 − bund_t+20) − (country_yield_t-1 − bund_t-1) in basis points, where t is the first trading day on or after the event date and t+20 is 20 trading days later. The OMT activation window (2012-09-06 to 2013-03-31) is excluded — any event whose horizon touches the window is dropped from the panel.

## Thresholds

- SUPPORTED: mean panel response ≥ +50 bp.
- partial:   +25 to +50 bp.
- refuted:   < +25 bp or wrong sign.

## Data backlog (for the data-agent)

Add fetchers for:

- ECB SDW key family `IRS` (long-term interest-rate convergence criteria, monthly, by member-state).
- FRED `IRLTLT01{GRC,IRL,PRT,ESP,ITA,DEU}M156N` (OECD MEI long-term rates re-published monthly).
- (Optional, for daily) Bundesbank BBK01 series for the Bund 10y benchmark and the corresponding national-debt-management-office series for periphery 10y benchmarks.

Once any of these lands, re-run this script — no spec change required.
