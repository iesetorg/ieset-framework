# U.S. New Deal policy timing and duplicate review — 2026-10-10

This is a bounded source and coding repair. It changes policy metadata and the
constructed drift timeline; it does not estimate a policy effect or change any
hypothesis verdict.

## Findings and corrections

| Record | Earlier coding | Reviewed coding and source |
| --- | --- | --- |
| `us_flsa_1938` | Entire 1933–39 New Deal span; immediate 40-hour week; transfer, general-spending, and financial-regulation axes inferred from a labour statute | Enacted 25 June 1938 and first effective 24 October 1938; initial 44-hour week phased to 40 by 1940. Retain only the directly supported labour-regulation axis. [U.S. Department of Labor history](https://www.dol.gov/general/aboutdol/history/flsa1938) and [minimum-wage schedule](https://www.dol.gov/agencies/whd/minimum-wage/history/chart). |
| `us_wagner_act_1935` | Entire 1933–39 span; transfer, general-spending, and financial-regulation axes assigned to a bargaining statute | Enacted 5 July 1935; retain the labour-regulation axis. [National Archives milestone document](https://www.archives.gov/milestone-documents/national-labor-relations-act). |
| `us_social_security_act_1935` | Entire 1933–39 span; unrelated financial and labour axes and later spending/GDP level used to characterize adoption | Enacted 14 August 1935; retain the statutory transfer-programme expansion. Distinct titles rolled out at different times, so no single programme-wide effective date is asserted. [SSA chronology](https://www.ssa.gov/history/1930.html) and [statutory history](https://www.ssa.gov/OP_Home/ssact/ssact-preface.htm). |
| `us_glass_steagall_repeal_glba_1999` | Duplicate of `us_gramm_leach_bliley_1999`, dated from 1933, attributed to the FDR movement, and assigned the opposite financial-regulation direction | Remove the unreferenced duplicate. The retained Clinton-era record has 12 November 1999 enactment and 11 March 2000 effective date for Title I, 120 days later. [Public Law 106-102, §§101, 161](https://www.govinfo.gov/content/pkg/PLAW-106publ102/html/PLAW-106publ102.htm). |

The New Deal movement had placed the full transfer and labour steps at its
1933 start, even though the cited statutes came later. Its total transfer
weight of 3 now consists of a moderate 1933 emergency-relief step under the
[Federal Emergency Relief Act of 12 May 1933](https://www.govinfo.gov/content/pkg/STATUTE-48/pdf/STATUTE-48-Pg55-3.pdf)
and a weak 1935 Social Security step. Its total labour-rigidity weight of 3
now consists of a moderate 1935 Wagner Act step and a weak 1938 FLSA step.
The 1933 public-works and banking-regulation steps remain at 1933 because
their statutory bases begin that year. The magnitudes are coding judgments,
not measured effect sizes.

The regenerated national composite differs only for the United States in
1933–37: its 1933–34 level is 16 instead of 20, and its 1935–37 level is 19
instead of 20. The 1938-and-later cumulative level is unchanged. The grid
still spans 1789–2026, 145 countries, and 21 axes. No state-level event was
promoted to a national score.

## Wider timing debt

A source-key-only scan after this repair found **591** policy IDs containing
at least one four-digit year three or more years after their
`timeframe.start`, and **136** policy-to-`enacted_by` links whose start year
lies outside the linked movement's closed year span. These are review
signals, not 591 or 136 confirmed errors: period-end years, multi-year
programmes, and later amendments can legitimately differ from an initial
start. Clear examples needing separate source review include several
post-1945 accession and statute records assigned the 1945 movement start.
No dates or scores were inferred from filenames by this repair.

The deleted duplicate remains recoverable in Git history. Policy and
second-order indexes require regeneration after this source correction.
