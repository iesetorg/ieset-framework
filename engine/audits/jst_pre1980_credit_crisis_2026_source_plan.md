# Blind source and decision plan: JST historical credit and crisis

**Pre-source correction:** The first registration commit treated `crisisJST`
as an active-year flag and required a 0-to-1 transition. The publisher's crisis
chronology says it is already a first-year onset flag. A second commit corrects
the specification, steelman, plan, and runner together before any source lock
or selected loan/GDP/crisis value or null mask was opened. The runner requires
exactly these two registration commits, checks their unchanged bytes, and
requires the metadata source lock to descend from the correction. The first
version is retained in Git for audit; the corrected rule is the one measured.

## Custody and evidence boundary

Registration files are this plan, the v2 hypothesis, its steelman, and
`scripts/run_jst_pre1980_credit_crisis_2026.py`. They must first appear in one
Git commit before selected `tloans`, `gdp`, or `crisisjst` values or null masks
are opened. A metadata-only source-lock manifest must first appear in a later
Git commit. The run directory must appear only after that custody commit.
The runner enforces first-addition ancestry and unchanged committed bytes.
Raw JST value rows or a derived value-bearing slice are never committed.

The only allowed data source is the already local JST R6 parquet
`data/vintages/jst/jst_macrohistory@2026-05-05T195309Z.parquet`, SHA-256
`4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`.
The 2026-05-05 IESET fetch manifest identifies the original publisher URL as
`https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx` and
the official documentation as `https://www.macrohistory.net/database/`.
The official documentation defines `tloans` as total nominal loans to the
non-financial private sector, `gdp` as nominal GDP in local currency, and the
crisis variable as a systemic financial-crisis 0/1 dummy. The publisher's
[crisis chronology](https://www.macrohistory.net/app/download/9844625569/JSTcrisis_chronology.pdf)
states that `crisisJST` equals 1 only in the first year of a crisis and 0
otherwise; this is already an incident-onset code. This is the 18
advanced-economy R6 panel, not a world sample. Cite Jordà, Schularick and
Taylor (2017) and retain the source's CC BY-NC-SA 4.0 conditions. No raw
or derived source data should be redistributed outside those conditions.

## Exact rows and analysis

The eighteen ISO3 codes are in the hypothesis. The thirteen anchors are
1875–1905 by five years, 1925, 1930, and 1955–1970 by five years. Every
anchor requires annual keys t−5 through t+5 within one of 1870–1913,
1920–1939, or 1946–1979. Union of fixed source years is 1870–1910,
1920–1935, and 1950–1975: exactly 1,494 country-year keys. The metadata-only
manifest records their roster hash, source URL, original parquet SHA-256,
and source schema. The replay reads only `country_iso3`, `year`, `tloans`,
`gdp`, and `crisisjst` from the ignored local parquet. Duplicates and missing
keys fail closed; no fallback vintage, country, or model is permitted.

For each candidate anchor, compute the five-year loan/GDP difference in
percentage points. The 80th percentile is calculated separately in each era
over all exposure-valid candidates, before any crisis-history or forward
outcome filtering; linear interpolation of sorted observations defines the
percentile. High exposure includes ties at the cutoff, but if ties make its
share exceed 35%, the family is INCONCLUSIVE. The at-risk set requires exact
binary crisis values in t−4:t+5 and no crisis onset in t−4:t. Forward
incident onset is any `crisisjst[y]==1` in t+1:t+5, exactly as coded by JST;
even adjacent first-year flags are not merged. The primary
endpoint is risk(high)/risk(other), with raw counts and risk difference.
The source grid alone contains no information about measured completeness or
incident-event counts; those floors are assessed only after custody lock.
The 234 candidate anchors may yield fewer than ten incident events; that
would force INCONCLUSIVE, not justify changing years or thresholds.

With source, cutoff, and sample floors met, SUPPORTED requires risk ratio ≥2,
risk difference ≥0.02, and ≥4 events among high-exposure anchors; REFUTED
requires risk ratio ≤1 and nonpositive risk difference; all other numerical
outcomes are PARTIAL. Missingness and event floors are exact in the YAML.
There is one closed descriptive family, no alpha/p-value, and at most one
descriptive calibration record. Neither the older post-1980 result nor any
school claim is reinterpreted or credited by this test.

## Mechanical sequence

1. Commit the four registration files without source values or result files.
2. Run `python3 scripts/run_jst_pre1980_credit_crisis_2026.py plan
   --source-parquet <LOCAL_HOME>/IESET/data/vintages/jst/jst_macrohistory@2026-05-05T195309Z.parquet`
   to check the 1,494 fixed source keys only.
3. Run the same command with `source-lock` instead of `plan`. It writes only
   `data/pinned_evidence/jst_pre1980_credit_crisis_2026.source.json`, which
   contains custody metadata and no loan, GDP, or crisis values.
4. Commit only that manifest as a separate source-lock commit.
5. Run `python3 scripts/run_jst_pre1980_credit_crisis_2026.py run
   --source-parquet <same licensed local parquet>`, commit the aggregate
   result directory, then run `verify` with the same original parquet.
   Report INCONCLUSIVE honestly if any gate fails. Replayers must have their
   own lawfully held copy of the exact SHA-256 source; the repository does not
   redistribute JST's licensed values.
