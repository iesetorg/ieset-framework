# High-quality graduation batch 6 - 2026-05-16

This batch repaired a specific failure mode in older descriptive trade-liberalisation cards: the generic runner compared end-period country levels against donor-pool levels, while the specs registered window-average changes or endpoint changes. The new evaluator uses the exact pre/post windows named in each falsification rule.

## Runner upgrade

- `scripts/run_descriptive.py`
  - Added reusable registered-window helpers for:
    - WDI trade openness: `world_bank_wdi:NE.TRD.GNFS.ZS`
    - WDI manufacturing share: `world_bank_wdi:NV.IND.MANF.ZS`
  - Added exact-gate handling for eight trade descriptive specs.
  - Preserved the existing generic descriptive path for all other hypotheses.

## Graduated artifacts

| Hypothesis | Verdict | Registered gate result |
| --- | --- | --- |
| `trade_lib_india_1991_tariff_cut_export_response` | SUPPORTED | India trade openness rose +14.66pp from the 1980-1990 mean to the 1992-2007 mean, clearing the +10pp gate. The wider 1992-2019 window rises +22.73pp. |
| `trade_lib_indonesia_1980s_1990s_unilateral` | REFUTED | Indonesia trade openness rose only +1.87pp from 1975-1984 to 1986-1996, below the +5pp refutation gate. Peer mean rose +28.59pp. |
| `trade_lib_egypt_fta_cascade` | SUPPORTED | Egypt openness rose +16.07pp from 1995-1999 to 2007-2010, then the 2015-2019 mean sat -21.32pp below the peak window. |
| `trade_lib_south_africa_sadc_trade` | SUPPORTED | South Africa openness changed +13.30pp from 1995-1999 to 2010-2019, inside the registered [-5,+20]pp null/modest-effect band. |
| `trade_lib_chile_bilateral_fta_cascade` | REFUTED | Chile openness rose +7.30pp, but the comparator differential moved -9.04pp, failing both the +15pp within-country and +10pp differential gates. |
| `trade_lib_mexico_eu_fta_2000` | REFUTED | Mexico openness rose +5.81pp, but comparator mean rose +11.90pp; Mexico lagged by -6.08pp, refuting the positive differential gate. |
| `trade_lib_colombia_us_fta_2012` | SUPPORTED | Colombia openness change was +1.44pp relative to comparator change, inside the +/-3pp null gate. |
| `trade_lib_argentina_mercosur_industrial_effect` | SUPPORTED | Argentina manufacturing-share change differed from comparator mean by +1.59pp over 1995-2019, inside the +/-2pp no-measurable-Mercosur-effect gate. |

## Why this matters

Several previous result cards were directionally wrong because the generic runner scored the wrong estimand:

- Indonesia was already refutable, but now for the correct reason: its registered within-country trade-openness increase is too small, not because its end-period level is below peers.
- Egypt flips from generic `REFUTED` to exact-gate `SUPPORTED`: the registered claim was a rise-then-reversal pattern, and that pattern is present.
- South Africa flips from generic `REFUTED` to exact-gate `SUPPORTED`: the registered claim was an aggregate null/modest band, not a level comparison with neighbours.
- Colombia flips from generic `REFUTED` to exact-gate `SUPPORTED`: the registered claim was no measurable acceleration relative to comparators.
- Argentina flips from generic `REFUTED` to exact-gate `SUPPORTED`: the registered claim was no manufacturing deepening relative to Latin American comparators.

## Verification

- `python3 -m py_compile scripts/run_descriptive.py`
- Targeted reruns:
  - `python3 scripts/run_descriptive.py trade_lib_india_1991_tariff_cut_export_response --force`
  - `python3 scripts/run_descriptive.py trade_lib_indonesia_1980s_1990s_unilateral --force`
  - `python3 scripts/run_descriptive.py trade_lib_egypt_fta_cascade --force`
  - `python3 scripts/run_descriptive.py trade_lib_south_africa_sadc_trade --force`
  - `python3 scripts/run_descriptive.py trade_lib_chile_bilateral_fta_cascade --force`
  - `python3 scripts/run_descriptive.py trade_lib_mexico_eu_fta_2000 --force`
  - `python3 scripts/run_descriptive.py trade_lib_colombia_us_fta_2012 --force`
  - `python3 scripts/run_descriptive.py trade_lib_argentina_mercosur_industrial_effect --force`
