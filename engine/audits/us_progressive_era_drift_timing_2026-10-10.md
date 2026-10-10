# U.S. Progressive Era drift timing audit — 2026-10-10

This is a bounded correction to the constructed national policy-decision map. It does not measure effects, add a hypothesis result, or claim that reform activity was absent before a coded statute. The movement remains a 1901–1917 historical umbrella; its five scored decisions now enter in the years supported by the cited laws.

## Earlier national steps checked

The authored U.S. national movements before 1933 are exactly the 1862–64 Civil War economic-institution record, the 1887–90 market-rule record, and this 1901–17 Progressive umbrella. The first two already have per-axis years:

- **1862** federal land/rail subsidy authority follows the [Homestead Act of 20 May](https://www.archives.gov/milestone-documents/homestead-act) and [Pacific Railway Act of 1 July](https://www.archives.gov/milestone-documents/pacific-railway-act). The former did not permit land entries until January 1863; the code explicitly represents enactment.
- **1864** financial-regulation attribution follows the substantially revised National Bank Act, with capital/reserve requirements. The [OCC history](https://www.occ.gov/about/who-we-are/history/history-of-the-occ/founding-occ-national-bank-system/index-founding-occ-national-banking-system.html) also records the 1863 precursor that established the OCC and national charters. The retained single 1864 step represents the later durable package, without claiming that nothing existed in 1863.
- **1887** Interstate Commerce Act is [dated 4 February](https://www.archives.gov/milestone-documents/interstate-commerce-act), but its existing product-competition direction is *mixed* and contributes zero; a rate regulator does not by itself establish more competition. **1890** Sherman Act is [dated 2 July](https://www.archives.gov/milestone-documents/sherman-anti-trust-act) and carries the movement's first signed competition step. Neither step was backdated, so neither record was changed.

## Sources and timing decision

| Movement axis | Old attribution | New attribution | Primary record |
| --- | ---: | ---: | --- |
| `regulatory.sectoral_licensing` +2 | 1901 | 1906 | [National Archives](https://www.archives.gov/legislative/features/hepburn): Hepburn Rate Act became law 29 June 1906; [FDA](https://www.fda.gov/about-fda/fda-history/milestones-us-food-and-drug-law): Food and Drugs Act signed 30 June 1906. |
| `regulatory.financial_deregulation` +2 | 1901 | 1913 | [Federal Reserve History](https://www.federalreservehistory.org/essays/federal-reserve-act-signed): Federal Reserve Act signed 23 December 1913. Reserve Banks opened later, in [November 1914](https://www.federalreservehistory.org/essays/feds-formative-years), so this is statutory adoption, not full operation. |
| `monetary.central_bank_independence` +2 | 1901 | 1913 | Federal Reserve Act as above. The original Board included the Treasury Secretary and Comptroller, and later independence rose; [Federal Reserve Board membership history](https://www.federalreserve.gov/aboutthefed/bios/board/boardmembership.htm). The existing moderate code is a partial legal-institution judgment, not a claim of modern de facto independence. |
| `fiscal.tax_progressivity` +3 | 1901 | 1913 | [National Archives](https://www.archives.gov/milestone-documents/16th-amendment): amendment ratified 3 February 1913; [IRS historical report](https://www.irs.gov/pub/irs-soi/62dbfullar.pdf): graduated federal income tax enacted 3 October 1913. |
| `regulatory.product_market_competition` +2 | 1901 | 1914 | [FTC](https://www.ftc.gov/about-ftc/history): FTC Act signed 26 September 1914; [FTC contemporary retrospective](https://www.ftc.gov/system/files/documents/public_statements/674231/19360323_freer_the_work_of_the_ftc.pdf): Clayton Act enacted 15 October 1914. |

These are source-backed event years. Direction and magnitude are inherited qualitative codes, not estimates from the cited records. The FTC did not open until 1915; the 1914 competition step codes the statutes.

## Exact derived-map effect

Only the **United States** changes. The complete authored grid stays **1789–2026, 145 countries, 21 axes**. The Progressive Era movement event still appears at its 1901 umbrella start; its scored changes do not. U.S. earliest composite coverage remains **1862**, so pre-1906 U.S. totals include earlier movements, not these later Progressive statutes. The later U.S. and all other country trajectories remain identical.

| USA series | Changed country-years | Old value | Corrected value |
| --- | --- | ---: | ---: |
| `regulatory.sectoral_licensing` | 1901–1905 | 2 | 0 |
| `regulatory.product_market_competition` | 1901–1913 | 3 | 1 |
| `regulatory.financial_deregulation` | 1901–1912 | 4 | 2 |
| `monetary.central_bank_independence` | 1901–1912 | 2 | 0 |
| `fiscal.tax_progressivity` | 1901–1912 | 3 | 0 |
| Composite statist drift | 1901–1905 | 6 | 3 |
| Composite statist drift | 1906–1912 | 6 | 5 |
| Composite statist drift | 1913 | 6 | 8 |

From **1914 onward** the cumulative values match the prior files exactly. The first signed U.S. sectoral-licensing axis year moves from 1901 to 1906; the first tax-progressivity and central-bank-independence years move from 1901 to 1913. The first financial-regulation and competition years remain 1864 and 1890 respectively because earlier U.S. movements already coded those axes.

## Scope and remaining coding questions

The `regulatory.sectoral_licensing` taxonomy emphasizes state-controlled entry, while the 1906 sources chiefly document product standards and railway rate oversight. The inherited +2 code therefore needs a separate axis-content review; this correction moves its date without asserting that the entire magnitude is proved by those laws. Likewise, 1913 central-bank independence was partial. No extra early step, effect estimate, or hypothesis credit was created to fill those uncertainties.

## Validation in the isolated worktree

This audit compares the checked-in pre-correction derived JSON with an in-memory rebuild after the movement edit. The derived JSON and CSV were then regenerated. The following checks passed on this branch:

- Spec validation: 6,291 files, no errors; 36 unresolved forward references were explicitly permitted candidate references.
- Strict position–hypothesis reciprocity: 5,065 links on each side, zero errors and zero warnings.
- Focused drift regressions: 31 passed, including the real Progressive movement timing test.
- Derived-map freshness check and whitespace check passed.
- Public-tree and commit-metadata OPSEC checks passed. These checks do not establish external publication readiness.
