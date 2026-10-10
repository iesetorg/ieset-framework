# Revenue Act 1869 and U.S. banking policy source repair — 2026-10-10

This bounded corpus pass adds two candidate provisions of the Revenue Act
1869 and corrects two existing U.S. banking records. Statutes and official
institutional histories establish dates and formal scope. None measures a
realized outcome, validates a causal claim, or graduates a hypothesis.

| Record | Source-locked treatment | Evidence boundary |
| --- | --- | --- |
| `uk_revenue_act_1869_fire_insurance_stamp_duty_repeal` | [Revenue Act 1869, sections 12–13 and schedule C](https://www.legislation.gov.uk/ukpga/Vict/32-33/14/pdfs/ukpga_18690014_en.pdf), Royal Assent 24 June, specified fire-only insurance stamp-duty repeal 25 June | Earlier policies and offences were saved; a limited refund applied to specified policies crossing the change. No insurance tax or premium series is attached, and the current axes lack a narrow insurance stamp-duty measure, so no axis is coded. |
| `uk_revenue_act_1869_tea_sales_licence_repeal` | Same original Act, sections 14–15 and schedule D, Royal Assent 24 June, specified sales excise-licence repeal 5 July | Covers coffee, tea, cocoa nuts, chocolate, and pepper, not all food sales or import duties. Section 15 preserves rights and rules of Irish sellers. The only coded axis is `regulatory.sectoral_licensing -`, without magnitude or entry-effect claim. |
| `us_glass_steagall_banking_act_1933` | [Original Banking Act of 1933](https://www.govinfo.gov/content/pkg/STATUTE-48/pdf/STATUTE-48-Pg162-2.pdf), signed 16 June; [FDIC's chronology](https://www.fdic.gov/history/1930-1939) dates temporary federal coverage to 1 January 1934; [Federal Reserve History](https://www.federalreservehistory.org/essays/glass-steagall-act) distinguishes later partial repeal | Corrected the inherited 1999 endpoint: key securities-affiliation provisions were repealed, but the FDIC and other provisions continued. Retained the direct financial-regulation axis. Removed duplicate parent movement, speculative transfer/spending/rule-of-law axes, and generic inferred hypothesis links. |
| `us_banking_act_1935_fed_restructuring` | [Federal Reserve History](https://www.federalreservehistory.org/essays/banking-act-of-1935) dates the Act to 23 August 1935 and documents Board/FOMC restructuring and removal of Treasury and Comptroller seats after 1936; [FOMC chronology](https://www.federalreservehistory.org/essays/federal-open-market-committee) dates the new committee's first meeting to March 1936 | Corrected an inherited 1933 start and 1999 end from the different 1933 law. Replaced generic bank-regulation/rule-of-law coding with a narrow formal central-bank-independence direction, without magnitude or a de facto outcome claim. Added its reciprocal child-policy link to the FDR New Deal movement without changing movement `axes_summary`. |

The 1869 records use `GBR` for the historical United Kingdom of Great
Britain and Ireland; neither creates an independent modern `IRL` map score.
No existing authored UK movement spans 1869, so both are policy-only records
and do not change numeric drift. They are different provisions of one Act,
with different treatments and dates, not independent empirical tests.
`linked_hypotheses_inferred` remains empty and inference is suppressed.

The corpus grows from 3,423 to 3,425 policy source records. This branch
changes no hypothesis specification, preregistration, run, result, or
movement `axes_summary`; its independent public hypothesis-tier contribution
is **zero**. Generated policy indexes and full integration validation belong
in the consolidated branch after merge.
