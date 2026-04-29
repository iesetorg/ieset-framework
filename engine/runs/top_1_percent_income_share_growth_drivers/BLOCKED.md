# BLOCKED — top_1_percent_income_share_growth_drivers

**Status:** blocked at v1 wiring stage.

## Reason

The pre-registered outcome — top-1% pre-tax national income share (`owid:top-1-share-of-total-income` per spec, ultimately WID.world) — is not present in `data/vintages/owid/` or any other publisher folder. Available OWID inequality vintages cover `economic-inequality-gini-index` and `gini-coefficient-after-tax-lis` only. Without the outcome series the decomposition cannot run.

Channel availability is also partially gated:
- `eurostat:nama_10_a64` (skill-services + finance VA share) — available.
- `bis:WS_SPP` (equity index) — not in current vintages.
- `oecd:OECD.ECO.GCRD,DSD_PMR@DF_PMR,1.2` (concentration) — present but only 2 cycle years (2018, 2023), insufficient for a 1980-2020 panel.
- `owid:top-marginal-income-tax-rate` — not in vintages.

## Path to unblock

1. Wire WID native fetcher (`wid_world` publisher) for top-1% pre-tax share, OR add OWID `top-1-share-of-total-income` mirror to the run-bootstrap manifest.
2. Add BIS `WS_SPP` to the fetch manifest.
3. Backfill OECD PMR with historical vintages (2003, 2008, 2013).
4. Add OWID `top-marginal-income-tax-rate` to the bootstrap manifest.

Pre-registration is preserved; v1 will run when these vintages ship.
