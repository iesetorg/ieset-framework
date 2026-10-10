# U.S. Progressive Era 1906 axis-content audit — 2026-10-10

This follow-up checks the content of the 1906 policy codes against the existing axis taxonomy after the separate timing correction. It changes no legal dates, does not infer measured policy effects, and awards no hypothesis credit.

## Statutes and axis fit

The checked-in `axes.yaml` defines `regulatory.sectoral_licensing` as sector-specific licensing, concentration or quota allocation, and **state-controlled entry**; its positive direction means tighter licensing or more state gating. It defines `regulatory.product_market_competition` as positive for lower entry barriers and negative for more restrictive regulation and higher entry barriers. The `institutional.rule_of_law` axis concerns contract enforcement, judicial independence, and equal treatment before law.

| 1906 record | Primary record | Coding judgment |
| --- | --- | --- |
| Food and Drugs Act, 34 Stat. 768–772 | [Statute text, §§1–5](https://www.govinfo.gov/content/pkg/STATUTE-34/pdf/STATUTE-34-Pg768.pdf); [FDA history of the act and enforcement](https://www.fda.gov/about-fda/changes-science-law-and-regulatory-authorities/part-i-1906-food-and-drugs-act-and-its-enforcement) | The act prohibits adulteration and misbranding in interstate trade and provides postmarket investigation and enforcement. It does not require federal permission before a producer may enter the market. Remove the `sectoral_licensing` +moderate claim. The act's notice, hearing, and court provisions do not alone establish a change in the national `rule_of_law` substrate, so remove the weak positive claim as well. This policy retains its historical link without an axis score; the present taxonomy has no dedicated consumer-product-safety axis. |
| Hepburn Act, 34 Stat. 584 | [National Archives, Hepburn Rate Bill](https://www.archives.gov/legislative/features/hepburn) | Expanded ICC power over railroad shipping rates is rate oversight, not a carrier-entry license. Remove `sectoral_licensing` +strong. Rate limits constrain tariff discretion and were also intended to curb unfair railroad practices; the statute alone cannot establish a net change in entry or rivalry. Change `product_market_competition` from −weak to `mixed`, with no magnitude. This is an unscored direction, not a new positive or negative step. |

The Progressive Era movement retains the 1906 policy links, but removes its +moderate `sectoral_licensing` summary step. Its remaining four signed steps still occur in 1913 and 1914. The movement begins historically in 1901 without placing those later statutory decisions in 1901. No `price_control_intensity` step was substituted from the rate statute: this audit does not establish the scope, implementation, or comparability needed to score that separate axis.

## Exact derived-map difference from the timing-only commit

The comparison base is the prior timing repair, commit `10e79272686a326341ba5e8b4035fefa2c6dd6be`. Regenerated `data/derived/country_drift.json` and `.csv` keep the **1789–2026**, **145-country**, **21-axis** grid. Only the United States country entry changes:

| Field | Exact country-years and change |
| --- | --- |
| `regulatory.sectoral_licensing` cumulative series | USA **1906–2026 inclusive**, 121 years: −2 each year. The 1906 value becomes 0 from 2; the 2026 value becomes 4 from 6. |
| `statist_drift` cumulative composite | USA **1906–2026 inclusive**, 121 years: −2 each year. The 1906 value becomes 3 from 5; the 2026 value becomes 32 from 34. |
| `axis_first_year.regulatory.sectoral_licensing` | USA **1906 → 1933**, because a later New Deal movement remains coded on this axis. |
| Progressive movement display `tone` | USA 1901 event **left → centrist**, recalculated from its four retained signed axes. Its event year, end year, and movement count do not change. |

No other U.S. axis series, country, year, or first-year field changes. The first U.S. composite year remains 1862. Removing policy-level `rule_of_law` and changing Hepburn competition direction do not independently affect this movement-derived map; its 1906 change comes from the removed movement axis. Existing historical 1906 laws remain visible, while the map preserves the absence of a supported signed 1906 step.

## Verification and generated-index handoff

- `scripts/validate_specs.py`: all 6,291 specs valid; the 36 permitted candidate forward references are reported as such.
- `scripts/validate_link_reciprocity.py --strict --summary`: 5,065 links on each side, zero errors and warnings.
- `scripts/compute_country_drift.py --check`: derived country map current.
- Focused drift and policy-index tests: 45 passed against locally regenerated policy indexes.
- Public OPSEC and whitespace checks: passed.

Policy browser, evidence, event-treatment, and second-order indexes were regenerated locally to verify the source changes. They contained large unrelated deltas because the isolated base had previously stale generated policy indexes. This commit retains only the two 1906 policy files, the movement, the focused test, this and the timing audit, and the derived drift map. The consolidated branch will regenerate its policy indexes after the source changes are integrated. No push, merge, or deployment was performed from this worktree.
