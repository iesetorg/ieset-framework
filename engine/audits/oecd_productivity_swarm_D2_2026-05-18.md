# OECD Productivity Swarm D2 Audit - 2026-05-18

Worker: D
Scope: OECD/PWT/STAN productivity, product-market competition, services-trade,
and wage/productivity hypotheses. Scoreboard, positions, pre-existing
2026-05-17T2317 fetch manifests, and daily rate-limited backfill audits were
not edited.

## Artifacts Produced

| Hypothesis | Verdict | Action |
| --- | --- | --- |
| `sectoral_competition_services_productivity` | PARTIAL | Replaced generic FE wrapper with a run-local OECD PMR/PDB services-productivity proxy horse race; added manifest, coefficients, chart data, and evidence packet. |
| `services_trade_liberalisation_frontier_growth` | INCONCLUSIVE_DATA_PENDING | Added first reproducible wrapper using PMR trade-barrier decline as an STRI proxy against PDB services MFP growth; recorded exact STRI/goods-subsidy gaps. |
| `oecd_product_market_deregulation_tfp_panel` | PARTIAL | Repaired the failed two-year TWFE PMR design into a short-window PMR-decline cross-section for PDB MFP and GDP-per-hour growth; added manifest/evidence outputs. |
| `working_time_regulation_productivity_per_hour` | SUPPORTED | Replaced the mechanical WDI/EFW proxy with an OECD PDB country-year FE panel of hours reductions, GDP per hour, and GDP per worker. |
| `top_1_percent_income_share_growth_drivers` | SUPPORTED | Rewired the decomposition to local OWID top-1, STAN skill-services/finance shares, BIS real property prices, and PMR barriers; updated stale `BLOCKED.md` to superseded. |
| `labor_reform_real_wage_growth` | PARTIAL | Replaced GDP-per-capita proxy with OECD PDB labour compensation per hour deflated by WDI CPI, plus PDB productivity and WGI regulatory-quality controls. |

Each produced run now has `replication.py`, `result_card.md`,
`diagnostics.json`, `manifest.yaml`, `coefficients.parquet`, `chart_data.json`,
and `evidence_packet.yaml`, with shared logic in
`engine/runs/oecd_productivity_worker_d_exact.py`.

## Key Verdict Notes

- Sectoral services competition: services-competition beta -0.1182, p=0.5765;
  no registered positive/significant gate.
- Services-trade liberalisation: PMR trade-barrier decline beta +0.8831,
  p=0.2853; promising sign but exact STRI/services-TFP sources are absent.
- PMR/TFP: PMR decline beta +0.1544 on MFP, p=0.8011, and +0.1618 on GDP/hour,
  p=0.699; positive but weak.
- Working time: hours-reduction beta +0.7044 on GDP/hour, p=1.394e-09, and
  -0.3098 on GDP/worker, p=0.000374; both registered signs clear.
- Top-1 drivers: skill-services channel beta +0.4246, p=0.01692; normalized
  proxy contribution share favors skill-services plus capital-appreciation.
- Labour reform real wages: lagged regulatory-quality beta +0.5106 on real
  compensation/hour proxy, p=0.6141; does not clear the wage gate.

## Blockers And Deferrals

- `financialisation_industry_share_decoupling` was skipped because it became
  dirty before Worker D edits, consistent with a Worker C claim. I did not
  touch it.
- `services_trade_liberalisation_frontier_growth` remains exact-data gated on
  OECD STRI, sectoral services TFP, and goods-subsidy intensity. The current
  artifact is a transparent proxy screen.
- `top_1_percent_income_share_growth_drivers` still needs native WID, equity
  income/price, historical concentration, and longer STAN coverage for the
  registered 1980-2020 design.
- `labor_reform_real_wage_growth` still needs an exact labour-reform event
  panel and worker-level real wage series for scoreboard promotion.

## Verification

Commands run:

```sh
python3 -m py_compile engine/runs/oecd_productivity_worker_d_exact.py engine/runs/sectoral_competition_services_productivity/replication.py engine/runs/services_trade_liberalisation_frontier_growth/replication.py engine/runs/oecd_product_market_deregulation_tfp_panel/replication.py engine/runs/working_time_regulation_productivity_per_hour/replication.py engine/runs/top_1_percent_income_share_growth_drivers/replication.py engine/runs/labor_reform_real_wage_growth/replication.py
python3 engine/runs/sectoral_competition_services_productivity/replication.py
python3 engine/runs/services_trade_liberalisation_frontier_growth/replication.py
python3 engine/runs/oecd_product_market_deregulation_tfp_panel/replication.py
python3 engine/runs/working_time_regulation_productivity_per_hour/replication.py
python3 engine/runs/top_1_percent_income_share_growth_drivers/replication.py
python3 engine/runs/labor_reform_real_wage_growth/replication.py
python3 - <<'PY'
from pathlib import Path
import yaml
ids = ['sectoral_competition_services_productivity','services_trade_liberalisation_frontier_growth','oecd_product_market_deregulation_tfp_panel','working_time_regulation_productivity_per_hour','top_1_percent_income_share_growth_drivers','labor_reform_real_wage_growth']
for hid in ids:
    for name in ['manifest.yaml','evidence_packet.yaml']:
        yaml.safe_load((Path('engine/runs')/hid/name).read_text())
print('yaml ok', len(ids)*2)
PY
```

All final commands exited 0. The wrapper runs emitted harmless `pyarrow` sysctl
warnings in the macOS sandbox, then completed.

## Churn And Restore Notes

- No scoreboard, positions, pre-existing `data/manifests/fetch_run_2026-05-17T2317*.yaml`,
  or `engine/audits/daily_rate_limited_data_backfill_2026-05-17T2317*` files
  were edited by Worker D.
- Many unrelated run directories and swarm audits were dirty concurrently; they
  appear to be other-worker output and were left untouched.
- No Worker D file is timestamp-only churn. The generated timestamps live inside
  intentionally regenerated run artifacts.
