# Source-backed policy-axis corrections — 2026-10-10

Scope: three policy records and one Bahrain parent movement. This is a corpus-coding repair, not an empirical outcome test or a new hypothesis graduation. The policy browser and treatment-registry indexes must be regenerated separately after these source edits.

## Primary-source decisions and treatment clocks

| Record | Source-backed decision | First operative treatment | Coding disposition |
| --- | --- | --- | --- |
| `bahrain_vat_rate_increase_2022` | [Law No. 33 of 2021](https://www.lloc.gov.bh/Legislation/HTM/K3321) was issued 18 Dec 2021; the [official amendment index](https://www.legalaffairs.gov.bh/En/Legislation/Amendments/L4818) records Official Gazette publication on 23 Dec 2021. | Article 3's 10% standard VAT rate applies from 1 Jan 2022. Article 4 temporarily retains the 5% rate for qualifying older contracts; zero-rated and exempt supplies remain distinct. | `enacted_date` corrected from 2022-01-01 to 2021-12-18; `effective_date` added as 2022-01-01. VAT is not the personal income-tax schedule measured by `fiscal.tax_progressivity`, and the VAT law does not itself cut spending. Both prior policy axes were removed pending an appropriate consumption-tax axis. |
| `si_euro_adoption_2007` | [Council Decision 2006/495/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32006D0495) is dated 11 Jul 2006. | Slovenia adopted the euro, and its derogation was abrogated, on 1 Jan 2007. | `enacted_date` corrected from 2007-01-01 to 2006-07-11; `effective_date` added as 2007-01-01. Reduced currency-conversion costs are outside the tariff, non-tariff-barrier, and FTA definition of `regulatory.trade_openness`. A transfer of monetary jurisdiction to the Eurosystem does not by itself establish a measured `monetary.central_bank_independence` change or explicitly confirmed neutral observation. Both prior policy axes were removed. |
| `uk_corn_law_repeal_1846` | The [Importation Act 1846, 9 & 10 Vict. c. 22](https://www.legislation.gov.uk/ukpga/Vict/9-10/22/pdfs/ukpga_18460022_en.pdf) is dated 26 Jun 1846 and changed duties on passage. | Lower scheduled import duties applied from 26 Jun 1846; a nominal one-shilling-per-quarter grain duty applied from 1 Feb 1849. The remaining corn duties were abolished by the separate [Revenue Act 1869, s. 4](https://www.legislation.gov.uk/ukpga/Vict/32-33/14/pdfs/ukpga_18690014_en.pdf). | The `regulatory.trade_openness + strong` step remains as a substantial tariff reduction. The description no longer states complete 1846 repeal or untested post-reform outcome claims. The 1846–1849 span describes the staged tariff change, not a policy expiry. |

## Before and after axis coding

| Record | Before | After |
| --- | --- | --- |
| Bahrain VAT policy | `fiscal.tax_progressivity − moderate`; `fiscal.spending_level − weak` | No `axes_moved` field; consumption-tax event retained as an unscored policy. |
| Bahrain 2020 parent movement | `tax_progressivity − moderate`; `immigration_openness + moderate`; `labour_market_flexibility − weak`; `rule_of_law + weak` | No `axes_summary` field. The VAT sign was wrong. The other steps describe child policies dated 2021–2022, but the drift builder would otherwise place all of them at the movement's 2020 start. They are withheld until primary sources establish operative decision years and support explicit attribution. The movement narrative and three child-policy links remain. |
| Slovenia euro policy | `central_bank_independence 0 strong`; `trade_openness + moderate` | No `axes_moved` field; currency-regime event retained without an unsupported canonical-axis sign. There was no 2007 Slovenia parent movement axis to change. |
| UK 1846 policy | `trade_openness + strong` | Same signed axis, with statutory tariff-reduction rationale and exact 1846/1849 timing. |

The three policy records now have empty `linked_hypotheses_inferred` lists with `suppress_inferred_axis_links: true`: generic axis overlap had linked them to studies of other countries or treatments. This removes unsupported related-evidence links when the policy indexes are next regenerated; it does not alter any hypothesis verdict.

## Derived country drift effect

`scripts/compute_country_drift.py` reads **movement** `axes_summary` entries, not policy `axes_moved` entries. Bahrain was therefore the only country whose checked-in drift series changed in this repair. From 2020 onward, its false personal-income-tax-progressivity level changes from `−2` to `0`, and its composite statist-drift level changes from `−1` to `0`; the 2020 movement marker remains but is neutral rather than scored. The old composite `−1` was the net of the false VAT `−2` and a backdated labour-flexibility `+1` contribution. With all four unsupported or mistimed parent steps withheld, no signed Bahrain axis contribution remains. Slovenia's current drift starts with its 2022 movement and has no 2007 euro step; its derived series is unchanged. The authored drift range remains 1846–2026.

This repair leaves the individual Bahrain Golden Residency and Wage Protection System policy records in place. It does not claim their policy text is false; their precise source-backed treatment dates and movement-level drift attribution require separate review before scoring.
