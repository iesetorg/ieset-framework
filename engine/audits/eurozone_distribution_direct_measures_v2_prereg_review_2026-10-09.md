# Eurozone 2008/2014 EU-SILC survey-wave measures: preregistration review

Date: 2026-10-09. **Draft design only. No candidate outcome values, null
masks, changes, signs, coefficients, verdict, or result packet have been read
or produced.** This record describes structural preflight before the
first-addition registration commit. It is not a graduation.

## Historical and substantive boundary

- Old ID: `eurozone_austerity_distributional_incidence`. Its same-commit
  result card says **inconclusive (data gap)** because `ilc_peps01n` was
  absent. The selected Gini vintage cannot yield the two-wave change, and no named
  narrative consolidation-shock panel is locally pinned. The five periphery
  and six core countries and the intended 2008/2014 survey-wave endpoints were
  already known. This design is a new descriptive calibration in the **old window**;
  it is neither temporal holdout nor a repaired causal austerity estimator.
- New ID: `eurozone_distribution_2008_2014_direct_measures_v2`. It compares
  a bottom-quintile **share of national equivalised disposable income** from
  [Eurostat `ilc_di01`](https://ec.europa.eu/eurostat/databrowser/view/ilc_di01/)
  with a **relative at-risk-of-poverty rate** from
  [Eurostat `ilc_li02`](https://ec.europa.eu/eurostat/databrowser/view/ILC_LI02/).
  The latter is the proportion below 60% of each country's own contemporary
  median income, not absolute poverty. Neither outcome identifies fiscal
  treatment or the tax-side counterfactual. `covers_claims: []`.
- [Eurostat EU-SILC metadata](https://ec.europa.eu/eurostat/cache/metadata/en/ilc_sieusilc.htm)
  identify 2008 and 2014 as **survey-wave labels**. For most countries the
  underlying income reference years are 2007 and 2013. Ireland used the 12
  months before interview in those waves, as the
  [Ireland country metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/ilc_simsilc_ie.htm)
  document. Neither label should be described as literal calendar-year
  income incidence in 2008 or 2014.

## Frozen rows and source custody

| Role | Exact dimensions | Pinned local vintage and SHA-256 | Tracked fetch manifest | Structural survey-wave keys |
| --- | --- | --- | --- | ---: |
| Bottom quintile income share | `freq=A`, `quantile=QU1`, `indic_il=SHARE`, `currency=EUR` | `data/vintages/eurostat/ilc_di01@2026-04-30T115754Z.parquet` · `6dc9948f57c6dc32e967628f541bbb19c894680ae7304b9de59fd50e641c29b5` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` | 22 |
| Relative poverty rate | `freq=A`, `unit=PC`, `indic_il=LI_R_M60`, `sex=T`, `age=TOTAL` | `data/vintages/eurostat/ilc_li02@2026-05-05T205827Z.parquet` · `f49a93b5183acddb13c89b07bba923693eee92a31cf7f065bd0e652e52ea4648` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` | 22 |

Only Parquet schemas and dimension columns were read during structural
preflight. Each series has exactly one matching row for each of 11 countries
at the 2008 and 2014 survey-wave labels. `GRC` maps to Eurostat `EL`; all other ISO3-to-Eurostat
codes are fixed in the runner. Structural keys do **not** establish non-null
values. Source files are ignored raw vintages, so a clean checkout without
them cannot replay locally until the pinned files are supplied.

The [local Eurostat fetcher](../../data/fetchers/eurostat.py) converts the
JSON-stat `value` map into rows and does not preserve observation `status`
flags. The pinned Parquets therefore cannot reveal whether any selected
endpoint carries a break, estimate, provisional, or reliability flag. **No
selected flags were inspected.** A finite/range gate is necessary for this
calculation but does not certify flag-clean comparability across survey waves.
This limitation caps any eventual result at low descriptive calibration;
flag-clean qualification would require separately custodied flag data and a
new predeclared quality policy before such a claim.

## Frozen decision and method gates

Periphery is exactly `GRC, ESP, PRT, IRL, ITA`; core is exactly `AUT, BEL,
DEU, FRA, FIN, NLD`. The endpoint is each country's **2014 survey-wave
observation minus 2008 survey-wave observation** in percentage points. Groups
are unweighted means of five and six country
changes; the two gaps are periphery minus core. The 0.5 pp bottom-share
threshold is a material difference in direct-share changes; the 2.0 pp poverty threshold
retains the magnitude contemplated in the old comparison. Both are frozen
without knowing the new direct-measure outcomes.

These are **relative group-change gaps**. Support does not require an
absolute fall in the periphery's bottom share or an absolute rise in its
poverty rate; both groups could improve while the periphery improves less.

- **SUPPORTED:** share gap ≤ −0.5 pp **and** relative-poverty gap ≥ +2.0 pp.
- **REFUTED:** share gap ≥ +0.5 pp **and** relative-poverty gap ≤ −2.0 pp.
- **PARTIAL:** all values valid but neither joint directional gate clears.
- **INCONCLUSIVE:** source/manifest/key gate fails, or any of the 44 required
  unique values is missing, nonfinite, or outside 0–100. No country drop,
  interpolation, year shift, alternate currency, or substitute series.

The runner's `--preflight` reads hashes, tracked manifests, schemas and keys
only. `--run` and `--check` require the spec, steelman, and runner to have
identical bytes at `HEAD` and at one shared first-addition commit, with no
result in that commit. The value reader itself repeats this guard. `--check`
re-estimates and compares the full stored packet without writing. Results,
if later produced, qualify only for descriptive calibration and no automatic
position-claim or scoreboard credit.
