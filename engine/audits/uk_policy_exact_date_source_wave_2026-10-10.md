# UK policy exact-date source wave — 10 October 2026

## Scope and count

Seven existing UK **candidate** policy records with exact date fields and no
references were checked against original legislation, parliamentary stages,
HM Treasury and HMRC publications, or the published 2024 planning framework.
Against the clean source checkout, the direct policy-spec scan falls from
**295 to 288** uncited full-date records. The same records are separate from
the eight French records in the concurrent source wave; integration must
regenerate the event-treatment index before reporting a combined count.
Policy IDs and candidate status remain unchanged. This is provenance and
timing repair, not a policy-effect estimate or hypothesis graduation.

| Policy | Date and coding repair | Primary source |
| --- | --- | --- |
| `uk_autumn_budget_2024_tax_package` | The Budget was presented 30 October 2024, when main CGT changes first applied. Employer NIC and inheritance measures had later dates. Replaced the falsely labeled enactment date with the first component effective date, marked treatment onset unresolved, and removed a spending-level sign not established by the tax-package record. | [Autumn Budget 2024](https://www.gov.uk/government/publications/autumn-budget-2024/autumn-budget-2024-html); [tax legislation and rates](https://www.gov.uk/government/publications/autumn-budget-2024-overview-of-tax-legislation-and-rates-ootlar) |
| `uk_autumn_statement_fiscal_drag_2022` | The Statement was announced 17 November 2022; the additional-rate income-tax threshold changed from 6 April 2023. Reclassified the date as effective for that component, marked the package onset unresolved, removed a speculative departmental spending sign and narrowed the progressivity rationale to the top threshold. | [Autumn Statement 2022](https://www.gov.uk/government/publications/autumn-statement-2022-documents/autumn-statement-2022-html); [Autumn Finance Bill notice](https://www.gov.uk/government/news/autumn-finance-bill-2022-published) |
| `uk_employment_rights_bill_2024` | The old 10 October 2024 “enacted” date was Bill introduction; the Employment Rights Act received Royal Assent on 18 December 2025. Corrected the old assertion of day-one ordinary unfair-dismissal rights: the final Act reduces the qualifying period to **six months**, commencing for dismissals from 1 January 2027. The package has phased commencements and principally Great Britain scope. | [Bill stages](https://bills.parliament.uk/bills/3737/stages); [Act section 25](https://www.legislation.gov.uk/ukpga/2025/36/section/25); [commencement regulations](https://www.legislation.gov.uk/uksi/2026/559/made); [implementation timeline](https://www.gov.uk/government/publications/implementing-the-plan-to-make-work-pay-and-employment-rights-act) |
| `uk_planning_housing_target_revision_2024` | The England planning framework was published 12 December 2024, not enacted as a UK-wide statute. Coded that as the policy effective date and subnational scope. Removed a property-rights reduction claim unsupported by the framework; retained a weak intended planning-entry direction, not an observed housebuilding effect. | [MHCLG publication](https://www.gov.uk/government/news/planning-overhaul-to-reach-15-million-new-homes); [December 2024 framework](https://assets.publishing.service.gov.uk/media/67aafe8f3b41f783cca46251/NPPF_December_2024.pdf) |
| `uk_vat_private_school_fees_2025` | The VAT service date was 1 January 2025; Finance Act 2025 received Royal Assent 20 March 2025 and includes retrospective and prepayment rules. Kept those dates separate, marked anticipation-sensitive onset unresolved, excluded the separately legislated business-rates change and removed an unrelated sectoral-licensing sign. | [HMRC measure](https://www.gov.uk/government/publications/vat-on-private-school-fees/applying-vat-to-private-school-fees); [Finance Act provisions](https://www.legislation.gov.uk/ukpga/2025/8/part/3/crossheading/value-added-tax/2025-03-20); [HMRC application guidance](https://www.gov.uk/guidance/charging-and-reclaiming-vat-on-goods-and-services-related-to-private-school-fees) |
| `uk_corporation_tax_increase_2023` | Finance Act 2021 received Royal Assent 10 June 2021 and set the 25% main rate for the financial year beginning 1 April 2023. Corrected enactment versus effect and attributed enactment to the Johnson government, while noting that the rate first applied under Sunak. | [Finance Act 2021 introduction](https://www.legislation.gov.uk/ukpga/2021/26/introduction/2021-12-10); [section 6](https://www.legislation.gov.uk/ukpga/2021/26/section/6); [Budget 2021 tax overview](https://www.gov.uk/government/publications/budget-2021-overview-of-tax-legislation-and-rates-ootlar/budget-2021-overview-of-tax-legislation-and-rates-ootlar) |
| `uk_full_expensing_capital_allowance_2023` | The first allowance applied to expenditure from 1 April 2023 under the 11 July 2023 Finance (No. 2) Act. Permanence was announced 22 November 2023 and enacted 22 February 2024. Preserved the first application date and marked the combined temporary/permanent record as lacking one treatment onset. | [Finance (No. 2) Act 2023, section 7](https://www.legislation.gov.uk/ukpga/2023/30/section/7); [Finance Act 2024, section 1](https://www.legislation.gov.uk/ukpga/2024/3/section/1); [Autumn Statement 2023](https://www.gov.uk/government/publications/autumn-statement-2023/autumn-statement-2023-html) |

The five records whose policy scope, date or axis meaning changed materially no
longer carry generic `linked_hypotheses_inferred` navigation. Those old links
included unrelated hypotheses and were never evidence of a causal result.
The corporation-tax and full-expensing tax-axis navigation was retained.

## Verification boundary

The source-presence count is a direct scan of policy YAML files. Generated
indexes should be refreshed by the integration owner after merging this branch.
These records provide official event provenance and conservative coding only;
no impact estimates, controlled comparisons or graduations were produced.
`python3 scripts/validate_specs.py` passed all **6,563** specs with the
repository's **28 permitted candidate forward references** and no validation
errors. `git diff --check` was also clean.
