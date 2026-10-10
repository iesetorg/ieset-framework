# UK Revenue Act 1869 policy gap — 2026-10-10

This is a source and corpus-coding audit, not an outcome test or a new movement score. The new candidate is `policies/uk_corn_duty_final_abolition_1869.yaml`.

## Separate 1869 decision

The [Revenue Act 1869 (32 & 33 Vict. c. 14)](https://www.legislation.gov.uk/ukpga/Vict/32-33/14/pdfs/ukpga_18690014_en.pdf) bears the date **24 June 1869**. Section 4 ends customs duties on imported corn, grain, meal, flour, and listed related articles in Great Britain and Ireland **from 1 June 1869**. The effective provision is therefore retrospective to Royal Assent. The authored `uk_corn_law_repeal_1846` record already distinguishes its 1846–1849 tariff reduction from the later 1869 abolition, but no separate 1869 policy existed before this repair. The new record uses `enacted_date: 1869-06-24`, `effective_date: 1869-06-01`, `regulatory.trade_openness +`, and no magnitude claim. It has no inferred hypothesis links.

The UK Parliament identifies Gladstone's first administration as [1868–1874](https://www.parliament.uk/about/living-heritage/evolutionofparliament/parliamentwork/communicating/from-the-parliamentary-collections/collections-hansard/subscription-form-w-gladstone/). The only earlier authored UK movement, `peel_conservative_split_1846`, ends in 1849; the next begins in 1906. No existing parent spans 1869. The policy schema does not require `enacted_by`, so the candidate remains standalone with an informational Gladstone ministry label. GBR denotes the historical UK state that then governed the Act's Great Britain-and-Ireland territory; present-day country outlines do not encode 1869 Irish territory. The policy is not separately scored for modern IRL and must not be assigned to Peel or produce a new country-drift step absent a separately sourced 1869 movement decision.

## Other precise provisions to review separately

- **Retail excise licences:** Revenue Act 1869, sections 14–15, removes the excise-licence requirement for sellers of coffee, tea, cocoa, chocolate, and pepper **from 5 July 1869**; section 15 preserves specified Irish sellers' rights and regulatory obligations. No corresponding policy exists. This is a plausible narrow `regulatory.sectoral_licensing -` candidate after confirming the extent of the former entry barrier. It is another provision of the same Act, so it should not be multiplied into independent evidence claims automatically.
- **Fire-insurance stamp duty:** Revenue Act 1869, sections 12–13, ends the percentage stamp duty on fire-insurance contracts **from 25 June 1869** and provides a refund rule for certain earlier contracts extending beyond 24 June. No corresponding policy exists. The tax change is clear, but the current canonical axes do not supply an obvious insurance stamp-duty axis; retain it unscored if recorded.

Neither gap extends the honest **1846** country-movement floor. They also supply no empirical outcome evidence by themselves.
