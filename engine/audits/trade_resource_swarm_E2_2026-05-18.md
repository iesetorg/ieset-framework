# Trade/Resource Swarm E2 Audit

Date: 2026-05-18
Worker: E
Scope: trade/resource/product-market channel repairs. No scoreboard or position files edited.

## Artifacts Produced

1. `consumer_choice_variety_trade_market_reform`
   - Verdict: REFUTED proxy screen.
   - Main estimates: PWT log real consumption on WDI trade openness, coef -0.1431, p=0.000147; WITS log product-count proxy, coef -0.00386, p=0.887; WITS export HHI, coef +0.00593, p=0.357.
   - Files: run-local `replication.py`, `diagnostics.json`, `result_card.md`, `manifest.yaml`, `chart_data.json`, `evidence_packet.yaml`.
   - Caveat: continuous trade-openness proxy, not Wacziarg-Welch reform episodes or domestic SKU availability.

2. `export_complexity_market_access_vs_subsidy`
   - Verdict: PARTIAL proxy screen.
   - Main estimates: WDI high-tech export share on market-access index, coef +4.587, p=0.0303; WDI high-tech export share on subsidy/state-burden index, coef +0.419, p=0.818; derived export diversification on market-access index, coef -0.0170, p=0.349.
   - Files: run-local `replication.py`, `diagnostics.json`, `result_card.md`, `manifest.yaml`, `chart_data.json`, `evidence_packet.yaml`.
   - Caveat: Harvard ECI, direct subsidy intensity, and direct tariff-faced-abroad data remain missing.

3. `quality_adjusted_consumption_market_liberal_panel`
   - Verdict: PARTIAL, reproduced by wrapper.
   - Estimate: PWT `rconna` on EFW summary index, coef -0.03337, p=0.189.
   - Files added/refreshed: `manifest.yaml`, `evidence_packet.yaml`, refreshed wrapper outputs.
   - Caveat: product-variety quality-adjustment input remains missing.

4. `resource_developmentalism_rent_seeking_trap`
   - Verdict: PARTIAL broad proxy, reproduced by wrapper.
   - Estimate: broad WDI/derived panel, coef -0.008094, p=0.758.
   - Subtype sidecar: clean subtype-comparator sample has 332 rows and 12 countries, but country+year FE causal scoring remains blocked because treatment is between-country in eligible rows.
   - Files added/refreshed: `manifest.yaml`, `evidence_packet.yaml`, refreshed wrapper outputs and subtype diagnostics.
   - Caveat: do not promote as a clean subtype causal result.

5. `market_order_trade_openness_high_tech_exports_panel`
   - Verdict: PARTIAL, reproduced by wrapper.
   - Estimate: WDI high-tech exports on WDI trade openness, coef +0.01609, p=0.501.
   - Files added/refreshed: `manifest.yaml`, `evidence_packet.yaml`, refreshed wrapper outputs.
   - Evidence packet quality: reproducible hash verified.

6. `trade_openness_consumer_welfare_1980_2024`
   - Verdict: PARTIAL, reproduced by wrapper.
   - Estimate: WDI private consumption per capita on WDI trade openness, coef -11.93, p=0.212.
   - Files added/refreshed: `manifest.yaml`, `evidence_packet.yaml`, refreshed wrapper outputs.
   - Evidence packet quality: reproducible hash verified.

## Commands Run

- `python3 engine/runs/consumer_choice_variety_trade_market_reform/replication.py`
- `python3 engine/runs/export_complexity_market_access_vs_subsidy/replication.py`
- `python3 engine/runs/quality_adjusted_consumption_market_liberal_panel/replication.py`
- `python3 engine/runs/resource_developmentalism_rent_seeking_trap/replication.py`
- `python3 engine/runs/resource_developmentalism_rent_seeking_trap/subtype_fallback_diagnostics.py`
- `python3 engine/runs/market_order_trade_openness_high_tech_exports_panel/replication.py`
- `python3 engine/runs/trade_openness_consumer_welfare_1980_2024/replication.py`
- `python3 scripts/generate_evidence_packets.py --run consumer_choice_variety_trade_market_reform --run export_complexity_market_access_vs_subsidy --run quality_adjusted_consumption_market_liberal_panel --run resource_developmentalism_rent_seeking_trap --run market_order_trade_openness_high_tech_exports_panel --run trade_openness_consumer_welfare_1980_2024 --no-index`
- `python3 -m py_compile engine/runs/consumer_choice_variety_trade_market_reform/replication.py engine/runs/export_complexity_market_access_vs_subsidy/replication.py engine/runs/quality_adjusted_consumption_market_liberal_panel/replication.py engine/runs/resource_developmentalism_rent_seeking_trap/replication.py engine/runs/resource_developmentalism_rent_seeking_trap/subtype_fallback_diagnostics.py engine/runs/market_order_trade_openness_high_tech_exports_panel/replication.py engine/runs/trade_openness_consumer_welfare_1980_2024/replication.py scripts/generate_evidence_packets.py`

## Blockers

- `consumer_choice_variety_trade_market_reform`: Wacziarg-Welch episode dates, state industrial-policy episode intensity, and domestic SKU/final-goods availability remain absent. Current verdict is a proxy screen only.
- `export_complexity_market_access_vs_subsidy`: Harvard Atlas ECI, direct subsidy-intensity, direct tariff-faced-abroad, and direct HS6 product-count panels remain absent. Current verdict is a proxy screen only.
- `quality_adjusted_consumption_market_liberal_panel`: product-variety quality-adjustment input remains unresolved.
- `resource_developmentalism_rent_seeking_trap`: subtype sidecar validates coding but blocks clean country+year FE causal scoring because treatment has no within-country variation in the eligible subtype sample.

## Churn To Restore

- None from Worker E beyond the lane files listed above.
- `py_compile` left no `__pycache__` directories under the checked paths.
- Pre-existing dirty files left untouched: `web/app/scoreboard/page.tsx`, `data/manifests/fetch_run_2026-05-17T2317*.yaml`, and `engine/audits/daily_rate_limited_data_backfill_2026-05-17T2317*`.
- Additional concurrent dirty files from other lanes were observed in finance/energy run directories and audits; they were not read, reverted, or modified by Worker E.
