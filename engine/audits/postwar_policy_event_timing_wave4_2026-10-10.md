# Postwar single-event policy timing, wave 4 — 2026-10-10

This bounded pass reviews nine candidate policy records whose former `timeframe`
tracked a longer governing movement. Dates below come from cited legal or
responsible-agency records, not policy IDs. The event records now use the year
the specified action first applied, while retaining a separate date for an
earlier statute or treaty signature. A single-year `end` bounds the coded event;
it does not assert that the resulting law, treaty or institution expired then.

| Policy | Source-reviewed date boundary | Retained policy axis and removed claims |
| --- | --- | --- |
| `uk_iron_steel_nationalisation_1949` | [Iron and Steel Act 1949](https://www.legislation.gov.uk/ukpga/Geo6/12-13-14/72/pdfs/ukpga_19490072_en.pdf) received assent **24 November 1949**. The [1953 compensation regulations](https://www.legislation.gov.uk/uksi/1953/1848/pdfs/uksi_19531848_en.pdf) identify **15 February 1951** as the general public-ownership transfer; Act §29 starts licensing three months after transfer. The [1953 appointed-day order](https://www.legislation.gov.uk/uksi/1953/1019/pdfs/uksi_19531019_en.pdf) ended the 1949 Act on **13 July 1953**. | Start/end **1951**, direct sectoral licensing only. Shareholder compensation is not coded as social-transfer expansion; later capital spending and reduced competition are not inferred from the Act. |
| `germany_gwb_competition_law_1957` | [Bundestag history](https://www.bundestag.de/dokumente/textarchiv/1957-07-04-kartellgesetz-901240) distinguishes parliamentary passage on **4 July 1957** from the Act dated **27 July 1957**; [Bundeskartellamt history](https://www.bundeskartellamt.de/DE/Bundeskartellamt/UeberUns/ueberuns_node.html) dates legal entry and agency operation to **1 January 1958**. | Start/end **1958** for first application, enacted **1957**; product-market competition only. Monetary, trade and labour axes came from other policies or coexistence. |
| `germany_bundesbank_law_1957` | [Deutsche Bundesbank](https://www.bundesbank.de/en/press/press-releases/deutsche-bundesbank-to-celebrate-its-60th-anniversary-670796) dates the signed Act to **26 July 1957** and entry/operation to **1 August 1957**. | Start/end **1957**; central-bank independence only. The record no longer assigns GWB competition, EEC trade or wage bargaining to the bank statute. |
| `france_eec_accession_rome_treaty_1957`, `germany_eec_accession_1957`, `italy_eec_accession_rome_treaty_1957` | [EUR-Lex's Treaty summary](https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=celex%3A11957E%2FTXT) identifies all three as original signatories: signature **25 March 1957**, application **1 January 1958**. [Treaty Article 13](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A11957E013) phases out internal duties; it does not say all tariffs vanished on entry. | Each founding-membership record starts/ends **1958** and retains only a weak trade-openness commitment. Domestic licensing, national central-bank independence, later CAP payments and observed growth are not assigned to the 1958 entry event. |
| `france_smic_1970` | [Légifrance Law 70-7](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000693898/) is dated **2 January 1970** and dates its original operative provisions to **4 January 1970**; Article 6 says the initial SMIC equalled the then SMIG. | Start/end **1970**; direct statutory labour-market rigidity only. Later payroll relief, EEC trade and public wage costs are outside this law's adoption event. |
| `japan_gatt_accession_1955` | [WTO's contracting-party list](https://www.wto.org/english/thewto_e/gattmem_e.htm) dates accession to **10 September 1955**. A [contemporaneous GATT record](https://www.wto.org/gatt_docs/English/SULPDF/90690179.pdf) says 14 parties invoked Article XXXV against applying GATT to Japan, preventing a claim of universal MFN access. | Start/end **1955**; weak, qualified trade-openness commitment only. Import licensing, subsidies and central-bank autonomy were not enacted by accession. |
| `japan_oecd_accession_1964` | [OECD legal membership list](https://www.oecd.org/en/about/legal.html) dates membership to **28 April 1964**. [OECD's historical review](https://www.oecd.org/content/dam/oecd/en/publications/reports/1974/04/oecd-observer-volume-1974-issue-2_g1g3417c/observer-v1974-2-en.pdf) says Japan adhered to the capital code but initially reserved 18 of about 50 transaction categories. | Start/end **1964**. No axis is assigned merely for membership: the provided event sources do not date a specific goods-trade, industry-subsidy, sectoral-licensing or BOJ-autonomy change to accession day. |

The nine files previously carried 36 policy-axis entries and 72 inferred
hypothesis links. They now carry eight direct policy-axis entries, no inferred
hypothesis links, and `suppress_inferred_axis_links: true`. These are descriptive
coding repairs, not outcome-effect estimates or hypothesis graduations.

**Drift-map implication:** `scripts/compute_country_drift.py` reads
`movements/*.yaml` and their `axes_summary`, not policy `axes_moved`. This wave
does not edit a movement, so the constructed national drift paths change by
**zero countries, zero country-years and zero axis steps**. The generated grid
remains 145 countries × 21 axes, 1789–2026. Existing derived files remain
unmodified; source integration should regenerate policy indexes separately.
