# BLOCKED - top_1_percent_income_share_growth_drivers

**Status:** superseded by the Worker D2 proxy artifact on 2026-05-18.

## What changed

The earlier wiring blocker is no longer accurate for the local proxy screen:
`owid:top-1-share-of-total-income` and `bis:WS_SPP` are now present in local
vintages, and `replication.py` writes a short-panel 2015-2022 decomposition
with OECD STAN skill-services/finance shares and OECD PMR barriers to entry.

## Remaining exact-data gaps

- Native WID top-1% pre-tax series is still preferable to the OWID mirror.
- BIS `WS_SPP` is used as a real property-price proxy, not an equity-price
  capital-income series.
- OECD STAN local coverage starts in 2015, so the registered 1980-2020 panel is
  not fully available.
- Historical Herfindahl/markup concentration and top marginal tax controls are
  still missing or too sparse.

The current verdict lives in `result_card.md`; this file is retained only to
document why the old blocked status was downgraded to a proxy-data caveat.
