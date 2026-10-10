# jst_pre1980_credit_boom_crisis_onset_v2

**Verdict: PARTIAL** — frozen descriptive five-year incident-onset risk contrast

Original JST R6 advanced-economy panel, before 1980. Descriptive risk comparison; no causal credit-policy effect is identified.

- Frozen candidates: 234 country-anchors in 18 countries across 13 years; 196 had valid loan/GDP exposure.
- At-risk anchors: 166; incident onsets: 31.
- High group: 7/35; other group: 24/131.
- Original local parquet SHA-256: 4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f.
- Registration commit: 55bf6b5e5afd864073d3910ae76b9493b09a4764.
- Metadata source-lock commit: 690eef717413bfe367c831ccfd9f2c8e088e08bc.
- One descriptive family; no p-value, causal, school, position, or policy-score credit.
- Raw risk ratio: 1.0917; risk difference: 0.0168 (probability scale).

## Evidence boundary

The original JST R6 data cover 18 advanced economies and are subject to CC BY-NC-SA 4.0 terms. Historical series may be spliced across archival sources. Crises and credit growth share macroeconomic causes; the raw contrast has no causal interpretation. The old post-1980 result is untouched.
The repository contains no JST value rows. Replay needs a lawfully held local copy with the exact pinned SHA-256 and source attribution:
Jordà, Schularick and Taylor (2017). https://www.macrohistory.net/database/

Reproduce: python3 scripts/run_jst_pre1980_credit_crisis_2026.py verify --source-parquet <local-JST-R6-parquet>
