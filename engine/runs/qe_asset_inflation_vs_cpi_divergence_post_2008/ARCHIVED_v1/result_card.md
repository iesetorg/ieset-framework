# Post-2008 QE asset inflation vs CPI divergence

**Verdict:** refuted — Only 2 of 8 countries had even a 0.10 log-point asset-vs-CPI gap by 2020 (mean GAP_2020 = -0.02). The post-2008 divergence story does not survive a panel test.

## Summary

- Sample: 8 advanced QE economies (USA, GBR, JPN, DEU, FRA, ITA, ESP, NLD).
- Cumulative-log gap between asset prices (equities for USA, BIS residential property for others) and CPI, 2008 base.
- Mean GAP_2020 = **-0.02 log-points** (~-2% asset-vs-CPI excess).
- 1 of 8 countries cleared the 0.3 log-point threshold (PRIMARY A; need 5).
- 1 of 3 eligible countries narrowed the gap by >= 25% by 2023 (PRIMARY B; need 4).
- USA WALCL/GDP > 15% in post-2008 window: **True** (2009 ratio = 14.39%).

## Method

1. CPI cumulative log-index from BIS WS_LONG_CPI annual %change.
2. Asset cumulative log-index from Shiller real total return (USA primary) or BIS WS_SPP residential property (other countries).
3. GAP_h = asset_log(h) - cpi_log(h). Compute at h=2020 (PRIMARY A) and h=2023 (PRIMARY B - sanity check that the 2021-23 CPI shock narrowed the gap).
4. Verdict requires PRIMARY A AND PRIMARY B. REFUTED if fewer than 3 countries cleared the 0.10 log-point floor.

## Caveats

- The spec called for cross-country central-bank balance-sheet treatment series (ECB, BoE, BoJ); only FRED:WALCL is on disk for the USA. The hypothesis is therefore tested as an *associational* post-2008 divergence, not as an LP impulse response. The QE-active indicator confirms regime classification for the USA only.
- Property-price index used as the asset proxy for non-US countries. This is conservative for the hypothesis: equity returns over 2008-2020 typically exceeded property returns, so the asset side of the gap is understated for the euro-area panel.
- 2020 used as the primary horizon to match the spec's '2009-2020 window only closing once the 2021-2023 CPI shock materialised'.

## Data

- bis:WS_LONG_CPI (cross-country annual CPI %change)
- bis:WS_SPP (residential property index — euro panel)
- shiller:ie_data (US S&P composite real total return)
- shiller:home_price_index (US real home price)
- fred:WALCL + fred:GDP (US Fed balance-sheet ratio)
- world_bank_wdi:NY.GDP.MKTP.KD (real GDP panel control)
