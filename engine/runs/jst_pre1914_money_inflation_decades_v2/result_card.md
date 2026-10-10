# jst_pre1914_money_inflation_decades_v2

**Verdict: INCONCLUSIVE** — registered sample or exposure gate failed

One descriptive 1870–1910 JST R6 historical money/inflation question.

- Complete endpoint pairs: 60/72; retained: 60 in 16 countries.
- Frozen source SHA-256: 4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f.
- Registration commit: 20523810a5bd27853ea26025f8ddf19fc2f15102.
- Metadata source-lock commit: f2790bcfe15ea1abd1b04cb4196ace374494f242.

Failed frozen gates:
- one country exceeds 20 percent of within-FE treatment variation.

This contemporaneous association does not identify a monetary or policy effect. No school, position, policy, causal, or featured credit is granted. The old 1960–2023 result remains archived and unchanged.

JST historical data are CC BY-NC-SA 4.0. No source-value rows are committed; replay requires a lawfully held exact-hash local copy. Cite Jordà, Schularick and Taylor (2017).

Reproduce: python3 scripts/run_jst_pre1914_money_inflation_2026.py verify --source-parquet <local-JST-R6-parquet>
