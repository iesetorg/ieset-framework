# Slovakia and Croatia policy-axis and timing corrections — 2026-10-10

Scope: five policy records and their two parent movements. This is a source-coding repair, not a new empirical test, causal estimate, or hypothesis graduation. The policy browser and other broad indexes should be refreshed after these source edits.

## Primary decisions and operative dates

| Record | Primary source and decision | First operative date | Disposition |
| --- | --- | --- | --- |
| `sk_euro_adoption_2009` | [Council Decision 2008/608/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008D0608), 8 Jul 2008; [Council Regulation 694/2008](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008R0694) fixed 30.1260 SKK per euro. | 1 Jan 2009 euro changeover and abrogation of Slovakia's derogation. | Corrected decision/effect dates. Removed `trade_openness + moderate` and `central_bank_independence 0 strong`: lower conversion costs are outside the trade-policy axis, and Eurosystem membership alone does not measure CBI from fiscal authority or establish a neutral observation. |
| `sk_healthcare_user_fee_abolition_2006` | [Government Regulation 485/2006](https://static.slov-lex.sk/static/SK/ZZ/2006/485/20060901.print.html), approved 4 Aug and published 22 Aug 2006, set specified outpatient and inpatient patient charges to zero. | 1 Sep 2006. | Corrected source and decision/effect dates. Removed `transfer_expansion + weak`: a public-service fee waiver is not a cash or near-cash transfer programme. The underlying healthcare law was not repealed. |
| `hr_euro_adoption_2023` | [Council Decision (EU) 2022/1211](https://eur-lex.europa.eu/eli/dec/2022/1211/oj), 12 Jul 2022. | 1 Jan 2023 euro adoption. | Corrected decision/effect dates. Removed `trade_openness + moderate` and `central_bank_independence 0 strong` for the same axis-definition reasons as Slovakia. |
| `hr_schengen_accession_2023` | [Council Decision (EU) 2022/2451](https://eur-lex.europa.eu/eli/dec/2022/2451/oj), 8 Dec 2022. | Checks on persons at internal land/sea borders lifted 1 Jan 2023; air checks lifted 26 Mar 2023. | Corrected decision/effect dates. Retained only `immigration_openness + moderate`, narrowly as a border-enforcement-posture change. Removed `trade_openness + weak` (not a tariff, goods barrier, or FTA decision) and `rule_of_law + weak` (verification of prior Schengen conditions is not a new general judicial or contract-enforcement reform). No new residence or work rights are inferred. |
| `hr_labour_act_amendments_2023` | [Official Gazette NN 151/2022](https://narodne-novine.nn.hr/clanci/sluzbeni/2022_12_151_2343.html), adopted 16 Dec and published 22 Dec 2022. | General commencement 1 Jan 2023; Article 55 on 1 Jul 2023; Article 56, including platform-work provisions, on 1 Jan 2024. | Retained `labour_market_flexibility mixed moderate` for fixed-term and other operative employment rules. Removed `rule_of_law + weak`: domain-specific employment duties do not establish a general institutional rule-of-law gain. Platform-work provisions are not treated as January 2023 exposure. |

The Slovakia Fico parent no longer carries movement-level steps for currency conversion, CBI neutrality, patient-fee waiver, or simple retention of the earlier flat tax. Its nine mechanical `position_alignments` scores were calculated from those withdrawn steps; with no supported `axes_summary` remaining, the position generator returns no replacement scores, so those stale entries are withheld. The separate 2009 scrappage child remains linked but needs its own source/date review before drift scoring. The Croatia Plenkovic parent retains only the border and mixed labour steps, each explicitly attributed to the source-backed 2023 operative year rather than the government's 2016 start. Its removed trade and general rule-of-law steps are not reassigned.

All five affected policy records have empty inferred hypothesis links and `suppress_inferred_axis_links: true`. Generic axis-overlap suggestions formerly connected several to unrelated studies; there were no direct policy-result links to preserve. This changes related-evidence presentation on index refresh, not any hypothesis verdict.

## Country drift effect

The drift builder scores movement `axes_summary`, not policy `axes_moved`. Comparing the regenerated files to the previous checked-in series, only `SVK` and `HRV` country objects changed; the 145-country, 21-axis, 1846–2026 range is unchanged.

| Series | Before | After |
| --- | --- | --- |
| SVK `trade_openness`, from 2006 | 5 | 3; false Fico-era `+2` removed. |
| SVK `transfer_expansion`, from 2006 | −1 | −2; false patient-fee `+1` removed. |
| SVK `central_bank_independence` first coded year | 2006 | No coded SVK axis event remains. |
| SVK statist composite, from 2006 | −11 in 2006; 2 in 2026 | −10 in 2006; 3 in 2026. The Fico movement marker is neutral rather than left-coded. |
| HRV `trade_openness` and `rule_of_law`, from 2016 | +2 and +1 | 0 and 0; unsupported parent steps removed. |
| HRV `immigration_openness` | +2 from 2016 | +2 from 2023; 2016–2022 is 0. |
| HRV `labour_market_flexibility` first coded year | 2016 | 2023; its mixed direction contributes zero to the composite. |
| HRV statist composite, from 2016 | −2 | 0; Plenkovic marker changes from right-coded to centrist. |

For the historical-floor check, the existing dated national movement and policy files were searched for events before 1846. None were authored. `peel_conservative_split_1846` and `uk_corn_law_repeal_1846` remain the earliest dated national records; earlier tariff history mentioned in prose is not a separate scored event. The map therefore honestly begins in 1846.
