# Blind source and decision plan: pre-1914 JST money and inflation

## Distinct question and boundary

The archived Friedman long-run monetary panel covers 1960–2023, has a seen
legacy result, and remains untouched. This new-ID test asks one narrower
descriptive question about four 1870–1910 decades in the original JST R6
advanced-economy panel. It does not test a policy effect, all countries,
other monetary regimes, or the archived claim's complete multi-source rule.
JST credit-boom/crisis and classical-gold-versus-fiat records use different
exposures and outcomes; this is not a duplicate crisis or regime comparison.

## Custody

The registration commit must first add this plan, the hypothesis, steelman,
and runner, with no selected money, CPI, real-output or population values or
null masks read. A metadata-only source lock is written and committed later.
Only then may the runner read selected values and write aggregates. The
runner enforces first-addition ancestry and unchanged registration bytes.
The original JST values and value-bearing row slices are never committed.

The only allowed source is `data/vintages/jst/jst_macrohistory@2026-05-05T195309Z.parquet`,
SHA-256 `4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`,
already held locally. Its 2026-05-05 fetch manifest records JST R6, 2,718
rows, 18 economies, 1870–2020, the publisher URL
`https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx`,
and documentation `https://www.macrohistory.net/database/`. The official
documentation identifies `money` as nominal broad money, `cpi` as consumer
prices, `rgdpmad` as real GDP per capita, and `pop` as population. Cite
Jordà, Schularick and Taylor (2017). JST's CC BY-NC-SA 4.0 conditions apply;
local replay requires a lawfully held exact-hash copy.

The source-key-only roster has 18 fixed ISO3 countries × the five endpoints
1870, 1880, 1890, 1900, 1910: 90 keys. It contains 72 candidate
country-decades. All 90 keys are present, but that says nothing about value
completeness or variation. The single family and every gate are in the YAML.

For each valid country-decade, compute annualized log CPI inflation and
annualized log broad-money growth less annualized log real GDP-per-capita and
population growth. Remove invalid endpoints without replacement. Retain only
countries with at least three complete decades. Require 12 countries, 48
country-decades, 10 countries in every decade, residualized exposure standard
deviation at least 0.5 percentage points, and no country above 20% of the
residualized exposure sum of squares. Fit the one registered two-way fixed-
effects slope with country-cluster uncertainty. Failed gates remain
INCONCLUSIVE. Support, refutation, and partial boundaries are frozen in the
YAML. At most one descriptive calibration record can follow.

## Mechanical sequence

1. Commit these four registration files before accessing selected values.
2. Run `python3 scripts/run_jst_pre1914_money_inflation_2026.py plan --source-parquet <local-JST-parquet>` to check only source keys and metadata.
3. Run `source-lock` with the same file. Commit the metadata-only lock separately.
4. Run `run`, inspect the gate and verdict, and commit its aggregate artifacts.
5. Run `verify` under the same system Python and source bytes for exact replay.
