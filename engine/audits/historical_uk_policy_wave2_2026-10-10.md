# Historical UK policy corpus wave 2 — 10 October 2026

This batch adds six **candidate** policy-only records, all before 1976, from original UK statutes on legislation.gov.uk. It also replaces unlinked citations in two existing records with original-act URLs and adds commencement and coverage cautions. Duplicate captures of the 1833 Factory Act, 1846 corn-duty transition, 1909 Trade Boards Act, and 1911 National Insurance Act were removed before commit; their existing IDs remain authoritative.

| New policy ID | Enacted | Later operative phase recorded | Content and territorial limit |
| --- | --- | --- | --- |
| `uk_mines_collieries_act_1842_women_children` | 10 Aug 1842 | final named phase 1 Mar 1843 | underground mine work only; no general labour rule |
| `uk_factories_act_1847_ten_hours` | 8 Jun 1847 | 11-hour step 1 Jul 1847; 10-hour step 1 May 1848 | women and young people in covered factories, not all workers |
| `uk_factory_acts_extension_act_1867_industry_coverage` | 15 Aug 1867 | incorporation in newly covered factories 1 Jan 1868 | additional listed manufactures, with exclusions and transitions |
| `uk_factory_act_1874_hours_child_schooling` | 30 Jul 1874 | general start 1 Jan 1875; some rules 1 Jan 1876 | covered factories, women, young people and children |
| `uk_trade_boards_act_1918_expansion` | 8 Aug 1918 | statutory start 1 Oct 1918 | trade-specific minimum-rate machinery, not universal wage floor |
| `uk_unemployment_insurance_act_1920_coverage` | 9 Aug 1920 | general start 8 Nov 1920 | broadened insured work with express exclusions |

The two existing records repaired are `uk_trade_boards_act_1909` and `uk_national_insurance_act_1911`. Their movement links and axis codings were preserved. Every new record has its original-act URL, dates supported by the statute, and `suppress_inferred_axis_links: true` with an empty inferred list. No policy was linked to an untested hypothesis, promoted to canonical, or used to move a country-drift axis.

**Geography and evidence boundary.** `GBR` identifies the historical United Kingdom jurisdiction, including Ireland before partition; these records do not score independent modern `IRL`. The acts regulate specific occupations, factories, groups, or import goods, and several were phased. Statutory text documents what a government enacted. It does not identify actual uptake, compliance, or causal effects. The original statutes are linked rather than copied into the repository.

After generation, the policy corpus contains 3,409 records (six more than the 3,403-record starting branch); the policy evidence index still lists eight `tested` policies. The exact schema, link, and index validation results are recorded in the commit message and terminal run.
