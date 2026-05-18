# Worker C Institutions Lane - 2026-05-19

Worker: C

Scope: market-friendly queue ranks 26-40, focused on institutional quality, governance, freedom, regulatory predictability, and quality-of-life mechanisms. I claimed ranks 26-32 and stopped at seven clean run artifacts, so I did not need the fallback ranks 76-90.

No edits were made to scoreboard UI, fetch manifests, daily-rate-limited backfill files, or hypothesis YAMLs.

## Claimed IDs

| Rank | Hypothesis | Verdict | Estimate summary | Artifact status |
| ---: | --- | --- | --- | --- |
| 26 | `intervention_qol_corruption_interaction` | PARTIAL | coef `+0.8165`, p `0.273`, n `1000`, countries `40` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |
| 27 | `regulatory_predictability_cross_sector_investment` | REFUTED | coef `+2.52`, p `0.0591`, n `750`, countries `30` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |
| 28 | `federalism_market_experimentation` | PARTIAL | coef `+0.8997`, p `0.193`, n `1000`, countries `40` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |
| 29 | `economic_freedom_personal_freedom` | PARTIAL | coef `-0.08966`, p `0.196`, n `1000`, countries `40` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |
| 30 | `property_rights_median_income_growth_1980_2024` | PARTIAL | coef `+374.3`, p `0.543`, n `1000`, countries `40` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |
| 31 | `crony_capitalism_not_market_freedom` | SUPPORTED | coef `+0.205`, p `0.0329`, n `1000`, countries `40` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |
| 32 | `state_ownership_media_freedom` | PARTIAL | coef `-0.003697`, p `0.679`, n `967`, countries `39` | clean: diagnostics, result card, manifest, evidence packet, replication wrapper |

All seven evidence packets report `reproducible_hash_verified`, with four pinned local inputs and zero missing series.

## Notes

- The runs use the canonical `scripts/run_panel_fe.py` estimator. The added or standardized run-local wrappers delegate to that canonical runner with `--force`; they do not duplicate estimator logic.
- `property_rights_median_income_growth_1980_2024` remains a weak panel result. The generic FE runner falls back to statsmodels because the preregistered property-rights treatment/control overlap creates rank pressure. I left the spec unchanged.
- `regulatory_predictability_cross_sector_investment` is formally REFUTED against the registered negative direction because the treatment coefficient is positive and significant at the 10 percent gate.
- Ranks 33-40 were left unclaimed because the requested 5-7 clean artifacts were satisfied inside ranks 26-32.

## Files Changed

For each claimed run, these files were created or refreshed:

- `engine/runs/<id>/diagnostics.json`
- `engine/runs/<id>/result_card.md`
- `engine/runs/<id>/manifest.yaml`
- `engine/runs/<id>/evidence_packet.yaml`
- `engine/runs/<id>/replication.py`

Audit file:

- `engine/audits/swarm_2026-05-19_worker_C_institutions_26_40.md`

## Commands Run

```sh
git status --short
sed -n '175,285p' engine/queue_market_friendly_100.yaml
find engine/runs -maxdepth 2 -type f \( -name result_card.md -o -name diagnostics.json -o -name manifest.yaml -o -name evidence_packet.yaml \) | rg '/(intervention_qol_corruption_interaction|regulatory_predictability_cross_sector_investment|federalism_market_experimentation|economic_freedom_personal_freedom|property_rights_median_income_growth_1980_2024|crony_capitalism_not_market_freedom|state_ownership_media_freedom|campaign_favoritism_subsidy_allocation|sector_neutral_tax_vs_exemption_cumulation|tax_complexity_trust_government|interventionist_subsidy_consumption_decay|tax_simplicity_disposable_income_growth|energy_qol_market_broad_scope|infrastructure_user_pricing_quality|state_monopoly_infrastructure_cost_overrun)/'
python3 scripts/run_panel_fe.py intervention_qol_corruption_interaction --force
python3 scripts/run_panel_fe.py regulatory_predictability_cross_sector_investment --force
python3 scripts/run_panel_fe.py federalism_market_experimentation --force
python3 scripts/run_panel_fe.py economic_freedom_personal_freedom --force
python3 scripts/run_panel_fe.py property_rights_median_income_growth_1980_2024 --force
python3 scripts/run_panel_fe.py crony_capitalism_not_market_freedom --force
python3 scripts/run_panel_fe.py state_ownership_media_freedom --force
chmod +x engine/runs/intervention_qol_corruption_interaction/replication.py engine/runs/regulatory_predictability_cross_sector_investment/replication.py engine/runs/federalism_market_experimentation/replication.py engine/runs/economic_freedom_personal_freedom/replication.py engine/runs/property_rights_median_income_growth_1980_2024/replication.py engine/runs/crony_capitalism_not_market_freedom/replication.py engine/runs/state_ownership_media_freedom/replication.py
python3 - <<'PY'  # generated seven manifest.yaml files from diagnostics and canonical latest_vintage resolution
python3 scripts/generate_evidence_packets.py --run intervention_qol_corruption_interaction --run regulatory_predictability_cross_sector_investment --run federalism_market_experimentation --run economic_freedom_personal_freedom --run property_rights_median_income_growth_1980_2024 --run crony_capitalism_not_market_freedom --run state_ownership_media_freedom --no-index
```

Validation commands:

```sh
for d in intervention_qol_corruption_interaction regulatory_predictability_cross_sector_investment federalism_market_experimentation economic_freedom_personal_freedom property_rights_median_income_growth_1980_2024 crony_capitalism_not_market_freedom state_ownership_media_freedom; do printf '%s\t' "$d"; for f in diagnostics.json result_card.md manifest.yaml evidence_packet.yaml replication.py; do test -f engine/runs/$d/$f && printf '%s=Y ' "$f" || printf '%s=N ' "$f"; done; printf '\n'; done
for d in intervention_qol_corruption_interaction regulatory_predictability_cross_sector_investment federalism_market_experimentation economic_freedom_personal_freedom property_rights_median_income_growth_1980_2024 crony_capitalism_not_market_freedom state_ownership_media_freedom; do jq -r '[.hypothesis_id,.verdict_label,.verdict_reason,.estimate.n_obs,.estimate.n_countries] | @tsv' engine/runs/$d/diagnostics.json; done
for d in intervention_qol_corruption_interaction regulatory_predictability_cross_sector_investment federalism_market_experimentation economic_freedom_personal_freedom property_rights_median_income_growth_1980_2024 crony_capitalism_not_market_freedom state_ownership_media_freedom; do printf '%s\t' "$d"; python3 -c "import sys,yaml; p=yaml.safe_load(open(sys.argv[1])); q=p['data']['data_quality']; print(q['grade']+'\tinputs='+str(q['input_count'])+'\tmissing='+str(q['missing_series_count']))" engine/runs/$d/evidence_packet.yaml; done
```

## Blockers

No blocking data failures remain for the seven claimed artifacts. Parquet reads emitted benign Arrow `sysctlbyname` sandbox warnings during runner execution, but all canonical runner commands exited 0 and evidence packets verified hashes.

Concurrent dirty files seen at start of lane were left untouched:

- `web/app/scoreboard/page.tsx`
- `data/manifests/fetch_run_2026-05-17T231721Z.yaml`
- `data/manifests/fetch_run_2026-05-17T231736Z.yaml`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231721Z.*`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231736Z.*`
