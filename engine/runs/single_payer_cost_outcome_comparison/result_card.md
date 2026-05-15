# Single-payer cost-outcome comparison — v2 honesty correction

**Verdict:** supported_subset — cost test PASSES (USA per-capita PPP $10957 vs GBR/CAN mean $5663, ratio 1.93x > 1.5); single-payer matched-or-beat USA on 4/5 tested outcomes (LE/IMR/U5/UHC/OOP). BUT canonical health-system outcomes basket has 4 documented data gaps: O6_amenable_mortality, O7_hale, O8_5yr_cancer, O9_waiting_times. The spec's own disclosure flagged amenable mortality + HALE as preferred outcomes; NHS waiting times and 5-yr cancer survival (USA outperforms) NOT in test. v1 SUPPORTED was indicator-gamed. Max tier: supported_subset.

## Why v2 differs from v1

v1 graded SUPPORTED on cost (USA 1.94x GBR/CAN) + 3 simple mortality outcomes. The spec's own disclosure flagged amenable mortality vs LE — exactly the indicator-gaming concern.

Canonical health-system outcomes basket (OECD HAG, WHO HSP) includes: amenable mortality, HALE, waiting times (NHS lags USA), 5-yr cancer survival (USA leads NHS), out-of-pocket equity. v1 omitted 4 canonical dimensions.

## Canonical basket

| Dim | Status |
|---|---|
| C1_cost_per_capita | ✓ |
| O1_le | ✓ |
| O2_imr | ✓ |
| O3_u5 | ✓ |
| O4_uhc | ✓ |
| O5_oop | ✓ |
| O6_amenable_mortality | **✗ data gap** |
| O7_hale | **✗ data gap** |
| O8_5yr_cancer | **✗ data gap** |
| O9_waiting_times | **✗ data gap** |

## Numbers

- USA per-capita PPP: $10957
- SP mean: $5663
- Cost ratio: 1.93x
- Outcomes tested: 5; won: 4

## Archives

v1 at ARCHIVED_v1/.
