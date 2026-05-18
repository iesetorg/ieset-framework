# Worker D heritage market graduation audit - ranks 1-15

Date: 2026-05-19

Scope: Worker D claimed seven strengthened variants derived from ranks 2, 3, 6, 7, 9, 12, and 15 of `engine/queue_heritage_market_graduation.yaml`. The original Heritage income-region screens remain candidate screens only and are not presented as scoreboard evidence here.

## Method

For each claimed candidate I created a new pre-registered WGI/WDI panel spec with:

- time-varying WGI institutional/regulatory treatment proxy;
- WDI outcome and macro controls;
- 1996-2023 country panel;
- country and year fixed effects;
- country-clustered standard errors;
- explicit p<0.10 sign threshold.

The canonical runner was `scripts/run_panel_fe.py`. The first verdicts below are associational panel artifacts, not causal scoreboard proof.

## Claimed IDs and outcomes

| Queue rank | Original candidate screen | Strengthened registered panel ID | Verdict type | Result |
|---:|---|---|---|---|
| 2 | `heritage_government_integrity_private_consumption_pc_income_region_robustness` | `heritage_government_integrity_private_consumption_pc_wgi_panel` | true panel verdict | PARTIAL: coef=+211.063, p=0.6568, n=1266, countries=52 |
| 3 | `heritage_property_rights_private_consumption_pc_income_region_robustness` | `heritage_property_rights_private_consumption_pc_wgi_panel` | true panel verdict | PARTIAL: coef=+623.731, p=0.3128, n=1266, countries=52 |
| 6 | `heritage_government_integrity_private_credit_depth_income_region_robustness` | `heritage_government_integrity_private_credit_depth_wgi_panel` | true panel verdict | REFUTED: coef=-13.366, p=0.0883, n=1133, countries=52 |
| 7 | `heritage_government_integrity_life_expectancy_income_region_robustness` | `heritage_government_integrity_life_expectancy_wgi_panel` | true panel verdict | PARTIAL: coef=-0.0916, p=0.7900, n=1297, countries=52 |
| 9 | `heritage_business_freedom_life_expectancy_income_region_robustness` | `heritage_business_freedom_life_expectancy_wgi_panel` | true panel verdict | PARTIAL: coef=-0.3679, p=0.4447, n=1297, countries=52 |
| 12 | `heritage_property_rights_private_credit_depth_income_region_robustness` | `heritage_property_rights_private_credit_depth_wgi_panel` | true panel verdict | PARTIAL: coef=-2.286, p=0.7500, n=1133, countries=52 |
| 15 | `heritage_business_freedom_private_credit_depth_income_region_robustness` | `heritage_business_freedom_private_credit_depth_wgi_panel` | true panel verdict | PARTIAL: coef=+3.797, p=0.6506, n=1133, countries=52 |

## Files changed

Hypothesis specs:

- `hypotheses/growth/heritage_government_integrity_private_consumption_pc_wgi_panel.yaml`
- `hypotheses/growth/heritage_property_rights_private_consumption_pc_wgi_panel.yaml`
- `hypotheses/regulatory/heritage_government_integrity_private_credit_depth_wgi_panel.yaml`
- `hypotheses/regulatory/heritage_property_rights_private_credit_depth_wgi_panel.yaml`
- `hypotheses/regulatory/heritage_business_freedom_private_credit_depth_wgi_panel.yaml`
- `hypotheses/healthcare/heritage_government_integrity_life_expectancy_wgi_panel.yaml`
- `hypotheses/healthcare/heritage_business_freedom_life_expectancy_wgi_panel.yaml`

Run artifacts:

- `engine/runs/heritage_government_integrity_private_consumption_pc_wgi_panel/result_card.md`
- `engine/runs/heritage_government_integrity_private_consumption_pc_wgi_panel/diagnostics.json`
- `engine/runs/heritage_property_rights_private_consumption_pc_wgi_panel/result_card.md`
- `engine/runs/heritage_property_rights_private_consumption_pc_wgi_panel/diagnostics.json`
- `engine/runs/heritage_government_integrity_private_credit_depth_wgi_panel/result_card.md`
- `engine/runs/heritage_government_integrity_private_credit_depth_wgi_panel/diagnostics.json`
- `engine/runs/heritage_property_rights_private_credit_depth_wgi_panel/result_card.md`
- `engine/runs/heritage_property_rights_private_credit_depth_wgi_panel/diagnostics.json`
- `engine/runs/heritage_business_freedom_private_credit_depth_wgi_panel/result_card.md`
- `engine/runs/heritage_business_freedom_private_credit_depth_wgi_panel/diagnostics.json`
- `engine/runs/heritage_government_integrity_life_expectancy_wgi_panel/result_card.md`
- `engine/runs/heritage_government_integrity_life_expectancy_wgi_panel/diagnostics.json`
- `engine/runs/heritage_business_freedom_life_expectancy_wgi_panel/result_card.md`
- `engine/runs/heritage_business_freedom_life_expectancy_wgi_panel/diagnostics.json`

Audit:

- `engine/audits/swarm_2026-05-19_worker_D_heritage_1_15.md`

## Commands run

```bash
sed -n '1,220p' engine/queue_heritage_market_graduation.yaml
sed -n '220,380p' engine/queue_heritage_market_graduation.yaml
rg -n "WGI|wgi|WDI|country/year|country fixed|year fixed|panel" engine/runs engine/hypotheses data scripts -g '*.py' -g '*.md' -g '*.yaml'
find hypotheses -maxdepth 3 -type f
sed -n '1,260p' scripts/run_panel_fe.py
sed -n '1772,1915p' scripts/run_panel_fe.py
sed -n '1915,2220p' scripts/run_panel_fe.py
sed -n '2220,2765p' scripts/run_panel_fe.py
find data/vintages -maxdepth 2 -type f | rg '(wgi/(RQ\.EST|GOV_WGI_RQ\.EST)|world_bank_wdi/(NE\.CON\.PRVT\.PC\.KD|SL\.UEM\.TOTL\.ZS|SL\.EMP\.TOTL\.SP\.ZS|NY\.GDP\.PCAP\.KD\.ZG|TX\.VAL\.TECH\.MF\.ZS|NE\.GDI\.TOTL\.ZS))' | sort
python3 scripts/run_panel_fe.py heritage_government_integrity_private_consumption_pc_wgi_panel
python3 scripts/run_panel_fe.py heritage_property_rights_private_consumption_pc_wgi_panel
python3 scripts/run_panel_fe.py heritage_government_integrity_private_credit_depth_wgi_panel
python3 scripts/run_panel_fe.py heritage_property_rights_private_credit_depth_wgi_panel
python3 scripts/run_panel_fe.py heritage_business_freedom_private_credit_depth_wgi_panel
python3 scripts/run_panel_fe.py heritage_government_integrity_life_expectancy_wgi_panel
python3 scripts/run_panel_fe.py heritage_business_freedom_life_expectancy_wgi_panel
python3 -c "read the seven diagnostics.json files and print verdict, coefficient, p-value, n, countries, and method"
python3 -c "validate the seven new hypothesis YAML files against schemas/hypothesis.schema.json with jsonschema"
git status --short
```

Notes:

- The `rg ... engine/hypotheses ...` reconnaissance command reported `engine/hypotheses` missing, but still surfaced the needed panel-runner and WGI/WDI context from existing paths.
- The parquet reads printed Arrow `sysctlbyname` warnings under the sandbox; all seven runner processes exited successfully and wrote diagnostics.
