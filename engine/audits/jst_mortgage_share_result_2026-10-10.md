# Measured audit and scalability limit: JST mortgage share, house prices, and crisis

## Frozen custody and verdicts

The first registration commit is `f718e1e7a3d36e84ca2562ea7dd7f55b567dabd1`. Eight metadata-only source locks were separately committed in runner order; the final lock is `288e7688d3b30f891cd304df8f988acd0346994f`. Only then were selected source measurements opened. The exact pinned JST R6 SHA-256 and 1,512 country-year key roster were checked before measurement. Packets contain aggregate diagnostics only; raw or country-level source values were not committed.

Frozen verdicts: **2 PARTIAL, 6 INCONCLUSIVE, 0 SUPPORTED, 0 REFUTED**. The two complete, ungated cells are eligible only for descriptive public calibration after independent evidence-tier review; the six gate failures remain archived. This is one correlated eight-cell family, not eight independent replications. No result receives causal, policy, school, position, or featured credit.

| Era | Outcome | Complete countries / anchors | Crisis events | Slope per mortgage-share pp | Raw p | Holm p | Verdict / gate |
|---|---|---:|---:|---:|---:|---:|---|
| 1890–1910 | real_house_price_growth | 7 / 28 | — | — | — | 1 | INCONCLUSIVE (country_floor, country_anchor_floor, anchor_floor) |
| 1890–1910 | crisis_onset | 12 / 47 | 14 | — | — | 1 | INCONCLUSIVE (country_anchor_floor) |
| 1950–1970 | real_house_price_growth | 12 / 47 | — | — | — | 1 | INCONCLUSIVE (country_anchor_floor) |
| 1950–1970 | crisis_onset | 17 / 67 | 0 | — | — | 1 | INCONCLUSIVE (crisis_event_floor) |
| 1975–1995 | real_house_price_growth | 17 / 68 | — | +0.0013 | 0.994055 | 1 | INCONCLUSIVE (country_exposure_concentration) |
| 1975–1995 | crisis_onset | 18 / 72 | 10 | -1.5305 | 0.202246 | 1 | INCONCLUSIVE (country_exposure_concentration) |
| 2000–2020 | real_house_price_growth | 18 / 72 | — | -0.0743 | 0.572379 | 1 | PARTIAL |
| 2000–2020 | crisis_onset | 18 / 72 | 13 | +0.3621 | 0.511026 | 1 | PARTIAL |

The pre-1914 house-price cell has only seven retained countries and 28 complete intervals; the pre-1914 crisis cell has 47 intervals, one below the frozen 48 floor. The 1950–1970 crisis cell has no incident intervals, while house prices have 47 complete intervals. Both 1975–1995 cells exceed the frozen one-country exposure-concentration cap. None was rescued by changing years, country floors, concentration limits, or event definitions after measurement. The two 2000–2020 cells are PARTIAL, with neither reaching the preregistered Holm/magnitude/deletion support or refutation rule.

## Scalability no-go for the +500 target

JST R6 provides 18 advanced economies and a finite, strongly correlated set of annual macro, credit, housing, fiscal, and crisis variables. These eight tests and the preceding twenty-test investment-share family already reuse some countries, eras, and source construction, so their combined 28 record IDs do not represent 28 independent scientific replications. Repeating adjacent anchors or swapping closely related outcomes would multiply identifiers while answering essentially the same question. This measured mortgage family yielded only two public descriptive calibrations from eight predeclared cells; the other six failed frozen sample/event/concentration gates. The prior twenty-cell investment family yielded fourteen public and six archive cells. At the 20-record family cap, a further 500 public records would require at least 25 entirely passing families, and roughly 36 families at a fourteen-in-twenty pass rate. The observed dependence and coverage failures do not support such a JST grid as an honest shortcut.

Future work should prioritize distinct source populations and genuinely different, source-locked mechanisms, or repair existing archived records with independent evidence under their original rules. Do not promote or split these gated cells, manufacture independent-replication counts, or loosen the gates to pursue a numeric target. The +500 user target remains unmet in this source branch.

## Reproduction and source

Run `python3 scripts/run_jst_mortgage_share_2026.py verify --source-parquet <local-JST-R6-parquet>` after the result commit. Exact replay checks first-commit schema and bytes, source-lock ancestry, source/key hashes, model diagnostics, and every packet byte. The [JST R6 database](https://www.macrohistory.net/database/) and [publisher documentation](https://www.macrohistory.net/app/download/9834516169/JST_documentationR6.pdf) define the source variables. Cite Jordà, Schularick and Taylor (2017); source license is CC BY-NC-SA 4.0.
