# Soviet collapse manual-drop data — provenance & citations

This directory holds curated CSV data for primary academic and statistical
sources that are not available via the automated fetcher pipeline for the
Soviet/post-Soviet 1989-1998 collapse window. Each CSV is read by
`scripts/_build_soviet_collapse_vintages.py` and emitted as a tidy parquet
vintage under the appropriate publisher namespace
(`data/vintages/<publisher>/<series>@<utc_stamp>.parquet`), so the
multi-metric checklist runner can consume the data alongside automated
fetchers.

Curation principle: every numeric observation is traceable to a primary
source listed below. Where multiple sources disagree the consensus
mid-point or the most recent academic reconstruction is used and the
disagreement noted.

## File-by-file primary sources

### `rosstat_male_life_expectancy_rus_2026-04-24.csv`
Russian male period life expectancy at birth, 1987-1999 (years).
- Goskomstat / Rosstat *Demographic Yearbook of Russia* (various editions
  1995-2005), vital-registration tabulations.
- Human Mortality Database (HMD) Russia data file, Berkeley / MPIDR
  (https://www.mortality.org), accessed via WHO HFA-DB cross-tabulation.
- Shkolnikov, V.M., McKee, M., Leon, D.A. (2001). "Changes in life
  expectancy in Russia in the mid-1990s." *The Lancet* 357: 917-921.
- Brainerd, E. and Cutler, D.M. (2005). "Autopsy on an Empire: Understanding
  Mortality in Russia and the Former Soviet Union." *Journal of Economic
  Perspectives* 19(1): 107-130, Table 1 (Russian male LE 1989: 64.2,
  1994 trough: 57.6).

The 1987 baseline (64.9) is the Gorbachev-era anti-alcohol-campaign peak;
the 1994 trough (57.4) follows hyperinflation and labour-market collapse.
A second trough at 1999 (59.0) follows the August 1998 default. The
peak-to-trough decline (~7.5 years) is the largest peacetime male LE
collapse in the modern demographic record.

### `oecd_sopemi_fsu_emigration_1989_1996.csv`
Cumulative recorded emigration from FSU territory to OECD destinations,
1989-1996, in millions.
- OECD SOPEMI *Trends in International Migration* annual reports
  1992-2000 (continuous reporting system on migration).
- Israeli Central Bureau of Statistics, *Statistical Abstract of Israel*
  (various editions 1991-2000), aliyah from former-USSR.
- German Federal Statistical Office (Destatis), Aussiedler / Spätaussiedler
  arrivals statistics 1989-1996 (Bundesverwaltungsamt registry,
  Bundesinstitut für Bevölkerungsforschung tabulations).
- Heleniak, T. (1997). "The changing nationality composition of the
  Central Asian and Transcaucasian states." *Post-Soviet Geography and
  Economics* 38(6): 357-378.
- Tishkov, V., Zayinchkovskaya, Z., Vitkovskaya, G. (2005). *Migration
  in the Countries of the Former Soviet Union*. Global Commission on
  International Migration paper.

The 1989-1996 cumulative total reaches approximately 2.45 million across
the three primary destinations: Israel (~720k Jewish-quota olim), Germany
(~1.55M Aussiedler + Jewish quota), USA (~180k FSU refugees + diversity
visa). Series carries the cumulative stock so the multi-metric runner's
fallback "max in window" gives the 1996 cumulative total.

### `cbr_currency_regime_events_1989_1998.csv`
Cumulative count of major currency-regime events affecting the Soviet /
Russian ruble, 1989-1998.
- Pavlov, V. (Soviet Prime Minister), confiscatory currency reform decree
  22 January 1991 (50- and 100-ruble notes invalidated overnight) — see
  USSR Council of Ministers Decree No. 16 of 22 Jan 1991.
- Russian Federation Presidential Decree No. 822 of 4 August 1997 on the
  redenomination of the rouble (1000:1, effective 1 January 1998).
- Ministry of Finance / Central Bank of Russia announcement of 17 August
  1998 — sovereign default on GKOs and forced ruble devaluation
  (~70% peak-to-trough vs USD by year-end 1998).
- Aslund, A. (2007). *Russia's Capitalist Revolution: Why Market Reform
  Succeeded and Democracy Failed*. Peterson Institute, ch. 5.
- IMF Article IV consultation staff reports for the Russian Federation,
  1992-1999 (IMF Country Reports).

This file emits an "events to date" running count under the `cbr` /
`imf` publishers so provenance is recorded; the multi-metric runner
will still classify the metric PENDING_EVAL because the threshold is a
discrete event count (`>=2`), but the underlying decree-by-decree event
log is now archived in this CSV for human review.

### `goskomstat_industrial_production_index_rus_1985_1998.csv`
Russian industrial production index 1985-1998, base 1989 = 100.
- Goskomstat SSSR / Rosstat *Narodnoye Khozyaystvo* (Народное хозяйство)
  annual statistical compendium, various editions 1989-2000.
- IMF *International Financial Statistics* industrial production line
  66 for the Russian Federation 1992-1998.
- World Bank ECA Region *World Development Indicators* archive
  reconstruction.

This duplicates the existing WDI NV.IND.TOTL.KD coverage but adds the
1985-1991 pre-collapse Soviet baseline (Russian SSR series spliced with
post-1991 RSFSR / Russian Federation series).

## Curation timestamp

All files added 2026-04-24 to close the data gap on the
`soviet_union_central_planning_gdp_collapse_1989_1991` multi-metric
hypothesis run.
