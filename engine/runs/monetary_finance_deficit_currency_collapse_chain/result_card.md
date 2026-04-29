# Monetary-finance -> currency-collapse chain (six EM cases)

**Verdict:** partial — Currency depreciation confirmed in 4/6 cases, but inflation-acceleration second-order response missed: 4/6 (need 5/6). 3rd-order holds, 2nd-order weak.

## Summary

- Per-case 2nd-order test: post-event 3-yr mean inflation >= 2x pre-event 5-yr mean. Pass: **4/6** (gate: >=5/6).
- Per-case 3rd-order test: cumulative LCU/PPP$ depreciation >=30% over T-1..T+3. Pass: **4/6** (gate: >=4/6).

### Per-case detail

| Country | Event | Pre-infl | Post-infl | Mult | FX chg% | Infl pass | FX pass |
|---------|-------|----------|-----------|------|---------|-----------|---------|
| ARG | 2019 | 30.0 | 54.3 | 1.81 | nan% | N | N |
| TUR | 2021 | 12.6 | 61.6 | 4.90 | 395% | Y | Y |
| VEN | 2013 | 26.6 | 146.3 | 5.51 | nan% | Y | N |
| LKA | 2020 | 4.3 | 22.9 | 5.34 | 68% | Y | Y |
| GHA | 2020 | 12.8 | 27.0 | 2.11 | 96% | Y | Y |
| EGY | 2022 | 13.7 | 26.0 | 1.90 | 88% | N | Y |

## Method

Six EM cases of documented monetary-finance intensification, each with a
country-specific event year T (ARG 2019, TUR 2021, VEN 2013, LKA 2020,
GHA 2020, EGY 2022). For each case:

1. Compute mean CPI inflation (IMF PCPIPCH) in pre-window T-5..T-1 and
   post-window T+1..T+3. The ratio is the 'inflation multiple'. Gate:
   ratio >= 2.0 -> 2nd-order chain confirmed for that case.
2. Compute LCU/PPP$ ratio (WDI PA.NUS.PRVT.PP) at T-1 and T+3. The
   change is the cumulative depreciation. Gate: change >= +30% -> 3rd-
   order currency-collapse channel confirmed for that case.

Chain SUPPORTED if 2nd-order gate passes in >=5/6 cases AND 3rd-order
gate passes in >=4/6. Asymmetric thresholds reflect the spec's
expectation that inflation transmission is near-mechanical while
currency response can be muted in cases with capital controls or
managed-float regimes (where parallel-FX would be the cleaner test,
but parallel-FX series for ARG/TUR/EGY/LKA/GHA are not on disk in
this repo's vintage tree — only Venezuela has dolartoday).

## Data

- imf:PCPIPCH (CPI inflation, annual % change)
- world_bank_wdi:PA.NUS.PRVT.PP (private-sector PPP conversion factor)
- imf:GGXWDG_NGDP (gov debt/GDP, context)
- imf:GGXCNL_NGDP (gov primary balance/GDP, context)

## Caveats

- Real-wage erosion (spec 2nd-order outcome) is not separately tested:
  no harmonised real-wage series for the six cases is on disk. CPI
  inflation acceleration is the primary 2nd-order signal here.
- Dollarisation share of bank deposits, parallel-FX premia, capital-
  control stringency, and emigration flows (spec 3rd-order outcomes)
  are not separately tested: bcra/tcmb/cbsl/cbe vintage data not on
  disk. PPP-currency depreciation is used as a single 3rd-order proxy.
- VEN dolartoday parallel-rate is on disk and could supplement future
  v2 work; for v1 a single PPP proxy keeps the cross-case test uniform.
