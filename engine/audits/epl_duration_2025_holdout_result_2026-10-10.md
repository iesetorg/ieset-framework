# OECD EPL and 2025 long-term unemployment holdout

Registration `5c3c2d88140797e893457e8edcccca0615842392`; source lock `ad31e371915cb16c0e86802b5a547b4237f7cdc0`.

**PARTIAL** — method-valid holdout does not clear the frozen directional threshold.

25 of 25 roster countries have complete source-matched cells. EPR coefficient -0.389082 share points per EPR index point; HC3 SE 1.06034; two-sided p 0.713662; 99% CI [-3.12033, +2.34217].

The outcome is the share of unemployed people with spells of at least 12 months, derived from Eurostat's actual long-term and total unemployment rates. This later-year country association has zero causal, policy, school, position, or featured credit. It does not repair or reclassify the old mismeasured result.

The registered source-quality and interpretation limits remain in `engine/audits/epl_duration_2025_holdout_prereg_2026-10-10.md`; the old result remains separately quarantined.

Independent estimator check: `statsmodels.OLS(...).fit(cov_type="HC3", use_t=False)` on the 25 locked country rows reproduced the coefficient, HC3 standard error, and two-sided normal p-value above to reported precision. The explicit `engine/school_score_exclusions.json` entry fixes school-score eligibility at false and scoreboard weight cap at zero while leaving this result public as calibration.
