# Cross-domain measured follow-ups: prospective registration

This fixed two-test family is a design registration, not a result or an old-run
graduation. Candidate source values, null masks, coefficient signs, and
estimates were not opened to select either design. The first commit adding this
plan, both specifications and steelmen, and the guarded runner must precede a
separate source-lock commit and any measured-column read. Both tests remain in
the family denominator even if one fails its sample gate.

## Fixed questions and boundaries

1. In 37 named countries and treatment years 1995–2021, does faster OECD PDB
   manufacturing **hour-based unit-labour-cost growth** at year `t` predict a
   lower WDI manufactures share of merchandise exports at `t+3` relative to
   `t`? The PDB selector is `FREQ=A, MEASURE=ULCH, ACTIVITY=C,
   UNIT_MEASURE=XDC, PRICE_BASE=V, TRANSFORMATION=GY, ASSET_CODE=_Z,
   CONVERSION_TYPE=_Z`. The WDI outcome is `TX.VAL.MANF.ZS.UN`. It is a
   percentage-point change in an export **share**, not manufactured-export
   volume, domestic value added, or a policy effect.
2. In 31 named European countries and treatment years 2014–2023, do more
   Eurostat **foreign-country and stateless immigration arrivals** per 1,000
   residents at `t` predict a higher change in Eurostat Gini of equivalised
   disposable income from survey year `t` to survey year `t+2`? The usual
   EU-SILC income years are `t−1` and `t+1`, so this brackets the arrival year
   with a pre-exposure baseline and a later income outcome. Immigration selects `migr_imm1ctz` annual
   `citizen=FOR_STLS, agedef=REACH, age=TOTAL, unit=NR, sex=T`; denominator
   `demo_pjan` annual `age=TOTAL, sex=T, unit=NR`; Gini `ilc_di12` annual
   `age=TOTAL, statinfo=GINI_HND`. The population is a 1-January estimate.
   Citizenship is not birthplace or net migration; the Gini covers all
   residents and cannot identify an immigrant-specific distributional effect.
   Ireland is excluded because its pre-2020 income reference used a rolling
   period, and the UK is excluded for fewer than five joined key years.

The first question follows visible PDB/high-tech-share results, but uses a
different PDB measure and a different WDI export-share endpoint. The second
uses a Gini outcome vintage and country-years also available to an old
unemployment/Gini study; it is a new direct source pair, **not** a data-disjoint
replication. Prior results do not supply either verdict. These questions are
correlated with other IESET source families, and no global independence is
claimed.

## Frozen estimation and decision rule

Each study has one primary country/year fixed-effect OLS coefficient, a fixed
baseline level of its own outcome at `t`, and country-clustered normal-Wald
uncertainty. There is no model/covariate search. The two-sided Bonferroni
family cutoff is `0.05 / 2 = 0.025` for either direction. If its sample or
identification gate fails, a case is `INCONCLUSIVE`. If the primary coefficient
clears the cutoff in the declared sign, the narrow measured claim is
`SUPPORTED`; if it clears in the opposite sign it is `REFUTED`; every other
estimable result is `PARTIAL`.

- Unit-labour-cost test: at least 400 complete country-years, 20 countries,
  five treatment years per retained country, and 15 within-country varying
  exposures. Only finite unit-labour-cost growth and export shares in [0,100]
  survive. No country substitution or imputation.
- Immigration/Gini test: at least 180 complete country-years, 25 countries,
  five treatment years per retained country, and 15 within-country varying
  exposures. Require finite nonnegative immigration counts, positive
  population, and finite Gini values in [0,100] at both endpoints. No country
  substitution or imputation.

Key-only preflight found upper envelopes of **901 pairs/37 countries** for the
first selector and **299 pairs/31 countries** for the second after the fixed
five-key-year rule. These counts are not complete-case counts. The runner must
verify exact hashes, tracked fetch manifests, registration ancestry, and the
separate source lock before opening any measured column.

## Exact source custody

| Role | Raw path | SHA-256 | Tracked manifest |
| --- | --- | --- | --- |
| PDB | `data/vintages/oecd/DSD_PDB@2026-05-19T094612Z.parquet` | `3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c` | `data/manifests/fetch_run_2026-05-19T095056Z.yaml` |
| Manufactured export share | `data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet` | `c5077c18a1ba1b953bc1cd66ac980f36b5cda7568fc3749126b91587cf17c98b` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` |
| Immigration arrivals | `data/vintages/eurostat/migr_imm1ctz@2026-05-05T205902Z.parquet` | `b0b178278dd7d1ef68d4a03188e496b580d3e30b61f9fa21c7db13ed547bfeb1` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| Population | `data/vintages/eurostat/demo_pjan@2026-05-05T205848Z.parquet` | `c0910d085947e1c95da781ea3679f79909f41cab5c2cf5731db4e8fcf415f3e3` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| Gini | `data/vintages/eurostat/ilc_di12@2026-07-23T154401Z.parquet` | `9b1b03caebf74bf79ad77d5373b04841002ea80c017ff6e3cca884485a8adfa6` | `data/manifests/fetch_run_2026-07-23T154936Z.yaml` |

Eurostat raw slices retain dimensions and numeric `value`, but no observation
status or quality flags. The raw parquet files are ignored by Git; another
host must recover exactly these bytes for replay. No causal, policy-effect,
position, featured, or school-score credit is permitted by either result.

Source meanings and the EU-SILC income-reference timing were checked against
[Eurostat migration metadata](https://ec.europa.eu/eurostat/cache/metadata/en/migr_ind_esmsip2.htm)
and [EU-SILC metadata](https://ec.europa.eu/eurostat/cache/metadata/en/ilc_sieusilc.htm).
