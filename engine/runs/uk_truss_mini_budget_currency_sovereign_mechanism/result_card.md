# Truss 2022 mini-budget — currency + sovereign-yield mechanism

**Verdict:** partial — Both mechanism legs are directionally consistent but at least one fails the SUPPORTED threshold: FX leg holds (5.02% trough decline); yield leg partial (61bp spike, 28% retrace).

## Summary

- Event date: **2022-09-23** (Kwarteng growth plan).
- BoE intervention: **2022-09-28** (temporary gilt-purchase facility).

### Primary leg 1 — FX repricing (GBP/USD)

- Pre-anchor close (2022-09-22): 1.1269 USD/GBP.
- Trough close in 23-28 Sep (2022-09-26): 1.0703 USD/GBP.
- Log-decline at trough: **+0.0515** (+5.02%). Threshold for SUPPORTED: 3.0%; partial floor: 1.5%.

### Primary leg 2 — Yield channel (UK 10y minus US 10y, bp)

- Pre-anchor excess (2022-09-22): **-15bp**.
- Peak excess in 23-28 Sep (2022-09-27): **+46bp**.
- Spike size: **+61bp**. Threshold for SUPPORTED: +60bp; partial floor: +20bp.
- BoE retrace 5 trading days after intervention close: **28%** of the spike. Threshold for SUPPORTED: 50%; partial floor: 25%.

## Method

Daily close-of-day mechanism event-window test. The MMT-style institutional-rupture-not-hard-fiscal-limit reading requires two empirical patterns: (1) a sharp pre-intervention sovereign repricing in the affected currency and yield curve, and (2) evidence that BoE intervention substantively retraces the yield repricing (i.e., the issuer's bank can normalise the channel). The yield leg is computed as a UK-US 10y excess (boe:IUDMNZC minus fred:DGS10) to net out the global rate backdrop. Both legs use the 2022-09-22 close as the pre-event anchor; the yield-spike window ends at 2022-09-28 (BoE-LDI facility close); the retrace is measured 5 trading days after the BoE close. The FX leg uses the trough close in the same 23-28 Sep window. Spec also names 30y gilt (boe:IUDLG7N) and FRED UK long-term yield (fred:IRLTLT01GBM156N) — neither is on disk in the current vintage; documented as data-gap.

## Informative

- UK-US 10y excess on Truss resignation (2022-10-20): -32bp (-17bp vs pre-anchor).
- GBP/EUR cross-check (boe:XUDLERS, GBP per 1 EUR): trough 1.1159 on 2022-09-28 (log-change vs anchor -0.0280; positive = GBP weakened vs EUR).
- VIX change t..t+5d: +1.70 pts.
- BoE Bank Rate change t..t+5d: +0.000pp.
- SONIA change t..t+5d: +0.002pp.

## Data

- fred:DEXUSUK (USD per GBP, daily) — primary leg 1
- boe:IUDMNZC (UK 10y gilt yield, daily) — primary leg 2
- fred:DGS10 (US 10y treasury yield, daily) — primary leg 2 control
- fred:DGS30, fred:VIXCLS, boe:IUDBEDR, boe:IUDSOIA, boe:XUDLERS — informative
- boe:IUDLG7N (UK 30y gilt) — **MISSING** (data gap)
- fred:IRLTLT01GBM156N (UK long-term yield) — **MISSING** (data gap)
