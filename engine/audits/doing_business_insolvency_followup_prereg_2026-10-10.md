# Prospective Doing Business insolvency holdout — 2026-10-10

This document and the three specifications, steelmans, fixed key roster, and
runner are being committed before any selected insolvency or macro-outcome
magnitudes are opened. The publisher workbook is the World Bank's corrected
historical Doing Business release, downloaded from its archive as
`Historical-Data--DB04-DB20-.xlsx` (SHA-256
`95bce841cd858fcf32f74fda67bc786881de4e91e1db522c78fc93f15abb265e`).
The selected worksheet is `DB21 Data`; its header positions are country code
1, DB year 5, insolvency time 81, recovery rate 83, and framework strength 84.
The original workbook, not the earlier unproven converted parquet, is source
custody. The World Bank catalog assigns CC BY 4.0.

The common roster has exactly **512** country/DB-year keys, **128** countries,
and DB years **2015–2018**. It was built with publisher country/year keys and
PWT/WDI country/year keys only. It excludes Afghanistan because selected rows
were previewed before this registration, and all 40 countries named in
`bankruptcy_law_efficiency_capital_reallocation`. This makes the cohort a
country holdout from that archived claim. No selected indicator or outcome
values were opened when the roster was fixed. The roster SHA-256 is
`528960e23fa54a820482c23ea3707f77fe433faea9a677c90a6225a0b8014482`.
The pair sources are the already-pinned WDI gross fixed capital formation
share vintage `NE.GDI.FTOT.ZS@2026-04-30T140059Z.parquet` (SHA-256
`fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21`)
and PWT `rtfpna@2026-05-05T195242Z.parquet` (SHA-256
`c919c4e3f1e766651cdf4ef3e252b99164fd2dacd234be830d98879df1cf800a`).

The three frozen cells are legal-framework strength → later fixed-capital
formation share, modeled secured-creditor recovery → later fixed-capital
formation share, and modeled resolution time → later annualized TFP growth.
They share a Bonferroni family of three at two-sided family alpha 0.01. Every
cell stays in the denominator. The first two use WDI investment share in
calendar DB year + 1; the third uses PWT TFP log change from DB year - 2 to
DB year + 1, annualized over three years. For these DB years, the publisher
describes the data as reflecting June 1 of the preceding calendar year. Thus
the macro endpoint is later than the insolvency assessment. Historical data
may have been revised after the fact, so this is **not** an ex-ante forecast.

The framework index was introduced in DB2015, so the design avoids mixing
pre-introduction framework values with that regime. It also avoids a 2020
macro endpoint. World Bank methods describe a standardized hypothetical
hotel-company insolvency case, with time/cost/outcome assessed by experts and
law review. Recovery is a modeled present value for a secured creditor; it
is not a realized bankruptcy return. The workbook has historical corrections
and the Doing Business project was later discontinued after data-integrity
concerns. Country and year fixed effects cannot eliminate changing credit
conditions, demand, income, government investment, or reverse reform
selection. These cells cannot repair or support the old financial-shock,
bailout-comparison, or firm-level capital-reallocation claim. They receive
zero causal, policy, school, position, and featured credit regardless of
directional verdict.

Chronology: commit this full registration first; create the exact common
source slice and three per-hypothesis raw-workbook locks in later, separate
commits; only then fit the frozen estimator and save all three result packets
together. The separate locks preserve the public multi-outcome family's
registration/lock/run ancestry. Failed gates yield
`INCONCLUSIVE`, not a changed cohort or threshold. No result should be
interpreted until independent exact replay and central evidence-tier audit.

Official sources: [World Bank Doing Business historical data](https://archive.doingbusiness.org/en/data),
[source license](https://datacatalog.worldbank.org/search/dataset/0038564/doing-business),
[insolvency methodology](https://archive.doingbusiness.org/en/methodology/resolving-insolvency),
[methodology changes](https://archive.doingbusiness.org/en/methodology),
[data timing and retrospective revisions](https://archive.doingbusiness.org/en/data/data-revisions),
and [project discontinuation](https://archive.doingbusiness.org/en/doingbusiness).
