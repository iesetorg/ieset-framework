# Historical country-drift frontier — 10 October 2026

## Earliest supported step

The national signed-axis map still begins in **1789** with the narrow French
provincial-privilege step. The 1781 U.S. Articles of Confederation are a
source-dated constitutional starting framework, not a direction of change from
an earlier U.S. national baseline. The French non-Catholic civil-status edict
was issued in November 1787 and registered by the Paris Parlement on 29
January 1788, but its own Article XXI makes operation depend on publication
and registration in the court of each person's domicile. Its current 1788
policy row is therefore useful context, not evidence of one nationwide
operative year or a calibrated country-level step. Neither policy acquires a
movement link, signed axis, or inferred outcome here. The [pre-1789 scope
audit](pre_1789_policy_context_scope_2026-10-10.md) also explains why the
1707 Great Britain union cannot be mapped unqualified to modern UK coverage.

Earlier policy-only rows after 1789, such as the UK 1802 apprentice rule and
1815 Corn Importation Act, remain dated context. Their axis magnitudes and
long-run reversals have not been reviewed as country movements. The map's
annual zero-filled years before a country's first signed step are storage
alignment, not historical observations or an absolute market/state baseline.

## Reconciled later source records

An ID inventory against `<LOCAL_HOME>/IESET/movements` found two authored
national movements missing from the integration corpus. They were reviewed
against the cited public authorities and imported with bounded policy repairs:

| Country | Signed step | Source and attribution limit |
| --- | --- | --- |
| AUS | `regulatory.financial_deregulation - strong` in 1983; `regulatory.trade_openness + strong` in 1988 | The [Reserve Bank](https://www.rba.gov.au/speeches/2013/sp-gov-211113.html) attributes the December 1983 float and exchange-control removal to the Hawke government; its [contemporary research](https://www.rba.gov.au/publications/rdp/1989/8904/deregulation-of-the-early-1980s-and-re-intermediation.html) records subsequent bank-rule relaxation. The [Bureau of Industry Economics](https://assets.pc.gov.au/2025-05/96-01.pdf) dates the tariff programme to May/July 1988. These are national policy decisions, not a measured annual economy score. Both duplicate Hawke-Keating policy umbrellas had the financial-regulation sign corrected to `-` under `axes.yaml` and now attribute the 1983 phase to Hawke as well as the later phase to Keating. |
| EST | `fiscal.tax_progressivity - strong` in 1994 | The [original Income Tax Act](https://www.riigiteataja.ee/akt/000000028610.pdf) was adopted on 8 December 1993 and took effect on 1 January 1994; the [central bank's 1994 report](https://www.eestipank.ee/en/annual-report-1994-estonian-economy-1994) records the proportional 26% rate. The policy's former `enacted_date: 1994-01-01` confused passage with effect. The movement dates the personal-tax schedule at implementation and does not score the later 2000 corporate-tax redesign. |

The source checkout also starts `biden_ira_chips_2022` in 2021 and
`lky_singapore_founding_1955_1990` in 1955. The integration corpus's 2022
and 1959 starts are better attributed to the 2022 IRA/CHIPS Acts and the 1959
PAP government, respectively; the CPF's 1955 operation preceded that PAP
government. The latter movement has no signed axes. The source and
integration corpora differ in many other axis codings, so this branch does
not copy shared movement files wholesale.

## Computed scope and checks

An in-memory before/after derivation, removing just these two movements for
the baseline, leaves the range **1789–2026** and changes only AUS and EST.
Australia's final composite changes 13 to 7 and Estonia's 6 to 3 in this
branch's current corpus. These are cumulative authored directions, not
observed statistical levels. Derived files and policy indexes are left for
integration-wide regeneration after this source branch is merged.

`validate_specs.py` passed with 6,675 specifications and 28 permitted
pre-existing forward-reference warnings. The focused full-history and
axis-timing test modules passed (13 tests). An expanded overlap test run had
one unrelated Netherlands failure, reproduced unchanged in the integration
checkout: the Kok II test expects zero central-bank-independence movement in
1998 but currently calculates +3.
