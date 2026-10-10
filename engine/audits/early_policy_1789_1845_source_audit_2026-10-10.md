# Early policy source audit, 1789–1845 — 10 October 2026

## Scope and result

The authored corpus already begins in 1789. Filtering by `timeframe.start` found three movement records in 1789–1845, all French, and ten policy records before this batch. The three movement-to-policy links (`fr_august_decrees_1789`, `fr_civil_code_1804`, and `fr_charter_1814`) and reciprocal `enacted_by` links were present. Their existing narrow date and legal-content notes did not need a speculative recoding.

Six missing legal events were added as **candidate, policy-only** records. The 1789–1845 policy set now has 16 records. None of the new records carries `enacted_by`, `axes_moved`, `linked_hypotheses`, or an inferred link. No movement file, numeric drift series, country-year score, tested-policy verdict, or hypothesis tier was changed. This is expanded legal-event coverage, not evidence of policy effects or extra hypothesis conversions.

| New policy | Source-backed timing | Narrow source-backed content and limit |
| --- | --- | --- |
| `fr_allarde_trade_professions_patente_1791` | Law of 2–17 March; Article 7 in force 1 April 1791 | Trade and occupational entry permitted subject to a paid patente and police regulations. [Légifrance Article 7](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006501995) |
| `fr_le_chapelier_professional_associations_1791` | Decree dated 14 June 1791; exact operational day withheld | Bar on restored occupational corporations and collective professional arrangements. [Légifrance initial decree](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000704780); [National Assembly account of articles and 14–17 June dating](https://www.assemblee-nationale.fr/14/rap-info/i3829.asp) |
| `uk_combination_of_workmen_act_1824` | Act passed and applicable from 21 June 1824 | Removed specified anti-combination prosecutions for workers and masters, with coercion still punishable; superseded in 1825. [Original Act, 5 Geo. 4 c. 95](https://www.legislation.gov.uk/ukpga/Geo4/5/95/pdfs/ukpga_18240095_en.pdf) |
| `uk_combination_of_workmen_act_1825` | Act passed and applicable from 6 July 1825 | Replaced 1824 law, preserved specified repeals and allowed wage/hour agreement while punishing coercion and obstruction. [Original Act, 6 Geo. 4 c. 129](https://www.legislation.gov.uk/ukpga/Geo4/6/129/pdfs/ukpga_18250129_en.pdf) |
| `uk_roman_catholic_relief_act_1829` | Act passed 13 April 1829; Section XL defers operation ten days, so exact effective date withheld | Opened Parliament and specified offices to otherwise qualified Catholics under an oath, with named exclusions. [Original Act, 10 Geo. 4 c. 7](https://www.legislation.gov.uk/ukpga/Geo4/10/7/pdfs/ukpga_18290007_en.pdf) |
| `uk_bank_charter_act_1844_note_issue` | Act passed 19 July 1844; UK-wide Section X restriction begins on passage; Bank of England issue-department separation after 31 August | New note issuers restricted UK-wide; several other rules apply only in England and Wales. [Original Act, 7 & 8 Vict. c. 32](https://www.legislation.gov.uk/ukpga/1844/32/pdfs/ukpga_18440032_en.pdf) |

For 1824–44, `GBR` denotes the historical United Kingdom of Great Britain and Ireland. These records do not create modern `IRL` country scores. The Bank Charter entry distinguishes its UK-wide Section X from England/Wales-only note-issuance provisions. The French records do not assert universal local or colonial implementation.

## Verification

`python3 scripts/validate_specs.py` passed across 6,320 spec files with clean cross-references. It reported 28 permitted, pre-existing forward references from unrelated candidate movements. No generated index or drift artifact is included in this source-only batch; the integration checkout should regenerate its policy indexes and rerun its full gates after merging.
