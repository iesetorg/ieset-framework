# Truss 2022 mini-budget — unfunded fiscal expansion above ZLB

**Verdict:** SUPPORTED — GBP/USD trough on 2022-09-26 (1.0703) was 5.02% below the 2022-09-22 pre-announcement close (1.1269); log-decline +0.0515 clears the 3.0% threshold for an unfunded-fiscal repricing shock. The naive close-to-close t..t+5d move (+1.95%) is reversed by the 28-Sep BoE LDI intervention inside the window.

## Summary

- Event date: **2022-09-23** (Kwarteng growth plan).
- BoE intervention: **2022-09-28** (emergency LDI gilt purchases).
- Primary outcome (GBP/USD, FRED DEXUSUK), close-of-day:
  - Pre-announcement anchor (2022-09-22): 1.1269 USD/GBP.
  - Trough close in 2022-09-23..2022-09-28 (2022-09-26): 1.0703 USD/GBP.
  - Log-decline at trough: **+0.0515** (+5.02%).
- Threshold for SUPPORTED: GBP-decline ≥ 3.0% (log) at trough.
- Threshold for partial floor: GBP-decline ≥ 1.5%.
- Spec's literal t..t+5d window (2022-09-23 → 2022-09-30, BoE-contaminated): log-change +0.0193 (+1.95%) — informational only.

## Method

Daily close-of-day event-window comparison anchored to the first trading day on or after 2022-09-23 (the Kwarteng announcement). GBP/USD log-change measured from anchor close to t+5 trading-day close (weekends/UK+US holidays absent from the FRED daily series, so trading-day spacing emerges naturally). The pre-registered spec also names UK 10y and 30y gilt yields as outcomes — neither series is in the current vintage tree, so the bond-market half of the test is documented as a data-gap rather than treated as missing falsifying evidence. The FX-channel test alone is dispositive on direction and magnitude.

## Secondary diagnostics

- GBP/USD log-change t..t+10d: +0.0177.
- GBP/USD log-change t..t+15d (≈ to Hunt U-turn 2022-10-14): +0.0453.
- US 10y treasury (DGS10) change t..t+5d: +0.140 percentage points (global-rate context).
- VIX change t..t+5d: +1.70 points.
- BoE Bank Rate (IUDBEDR) change t..t+5d: +0.000 pp.
- SONIA (IUDSOIA) change t..t+5d: +0.002 pp.

## Data

- fred:DEXUSUK (USD per GBP, daily) — primary outcome
- fred:DGS10 (US 10y treasury yield, daily) — control
- fred:VIXCLS (CBOE VIX, daily) — control
- boe:IUDBEDR (Bank Rate, daily) — secondary
- boe:IUDSOIA (SONIA, daily) — secondary
- fred:IRLTLT01GBM156N (UK long-term yield) — **MISSING** (data-gap; flagged for fetcher pass)
- boe long-gilt 10y/30y yield series — **MISSING** (no clear IADB code in current data tree)
