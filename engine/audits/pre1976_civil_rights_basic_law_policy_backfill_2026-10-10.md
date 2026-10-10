# Pre-1976 civil-rights and Basic Law policy backfill — 2026-10-10

This bounded source audit checked the existing historical policies and the
main checkout's uncommitted historical additions before selecting events.
It adds three distinct **national legal policy events**, repairs one dated
existing event, and corrects one German movement step. These are statutory
and constitutional records, **not measured outcome effects or graduated
hypotheses**. Inferred hypothesis links are suppressed.

| Policy ID | Official event evidence | Scope, coding, and movement relationship |
| --- | --- | --- |
| `de_basic_law_1949` | The [Bundestag](https://www.bundestag.de/parlament/grundgesetz/aktueller-begriff-grundgesetz-643586) dates promulgation to **23 May 1949** and legal effect to **24 May 1949**. Its [history](https://www.bundestag.de/dokumente/textarchiv/1949-05-23-grundgesetz-641776) identifies the multiparty Parliamentary Council and initial West German territory. The [Federal Constitutional Court](https://www.bundesverfassungsgericht.de/EN/TheFederalConstitutionalCourt/History/history_node.html) dates its own start to **7 September 1951**. | DEU denotes the 1949 West German jurisdiction, not the whole territory of present-day Germany. Formal constitutional rights and judicial architecture are `institutional.rule_of_law + moderate`; no observed enforcement effect is assigned. The Erhard movement cites the Basic Law as its context, but did **not** enact it, so this policy has no `enacted_by` or reciprocal child-policy link. |
| `us_civil_rights_act_1964` | The [National Archives enrolled Act and transcript](https://www.archives.gov/milestone-documents/civil-rights-act) date signing to **2 July 1964**. Titles II, IV, and VI established covered equal-treatment and federal-enforcement rules; §716 delayed major Title VII employment provisions by one year. | National federal law enacted during Johnson's Great Society movement; reciprocal movement-policy link added. Only direct formal `institutional.rule_of_law + moderate` is coded. The movement's existing strong **aggregate** rule-of-law step is now explicitly attributed to its 1964 starting statute, rather than describing 1965 voting preclearance as a 1964 event. |
| `us_fair_housing_act_1968` | [Public Law 90-284](https://www.govinfo.gov/content/pkg/STATUTE-82/pdf/STATUTE-82-Pg73.pdf), Title VIII, was approved **11 April 1968**. [HUD's statutory text, §803](https://www.hud.gov/sites/dfiles/GC/documents/HUDBasicLawsJune2025.pdf) makes its sale/rental bar effective at enactment for federal or federally aided dwellings, then extends it to other non-exempt dwellings **1 January 1969**. | National federal statute enacted during Johnson's movement; reciprocal link added. `effective_date` is the first limited treatment date, not full coverage. Only direct formal `institutional.rule_of_law + weak` is coded; statutory exemptions and staggered treatment remain explicit. |
| `us_voting_rights_act_1965` (repair) | The [National Archives Act and transcript](https://www.archives.gov/milestone-documents/voting-rights-act) date enactment to **6 August 1965**. §2 applies nationwide; §5 preclearance was limited to covered jurisdictions. | Corrected the inherited 1964–1968 movement window to the 1965 law date. Removed three speculative fiscal axes and eight generic inferred hypothesis links. Retained only the direct equal-vote rule-of-law axis, with no claim that a registration, transfer, or spending outcome was measured here. |

## Drift and evidence boundaries

The German movement's rule-of-law step previously inherited the movement's
**1948** start despite relying on the 1949 Basic Law. It is now attributed to
**1949**, the first operative constitutional year. The Court's 1951 operation
is a separate date and is not pulled into 1949. The US Great Society
rule-of-law step remains in **1964**, now grounded in the enacted Civil Rights
Act. The 1965 voting and 1968 housing laws remain distinct policy events and
are not duplicated as new numeric steps. The drift generator scores authored
movement `axes_summary`, not each child policy's `axes_moved`.

This backfill does not infer pre-1789 numeric drift, apply West German 1949
policy to East Germany, claim realised rights outcomes, or convert policies
into hypothesis evidence. Later work should measure implementation and
outcomes with treated units and appropriate contemporaneous controls; 1968
housing treatment especially needs its staged coverage and exemptions.

## Validation and generated artifacts

- `scripts/validate_specs.py`: **6,410** specs and cross-references clean;
  28 unrelated candidate-policy forward-reference warnings remain permitted.
- `scripts/validate_link_reciprocity.py --summary`: **5,065** position links and
  **5,065** hypothesis coverages, **0 errors, 0 warnings**.
- Policy browser, evidence, and event-treatment indexes each contain
  **3,423** policies, up by three; the second-order requirements index
  contains **3,399** in its filtered scope, also up by three. Semantic JSON
  comparison by policy ID found exactly the three additions and the Voting
  Rights Act repair; the second-order movement row adds only the two new LBJ
  child policies. Array insertion makes the text diff of the large generated
  JSON files look much larger than the semantic change.
- `scripts/compute_country_drift.py --check` passes for 145 countries, 21
  axes, and years **1789–2026**. The sole numeric CSV difference is removal
  of `DEU,institutional.rule_of_law,1948,3.0`; the first nonzero German row is
  now **1949** at `3.0`. The US 1964 rule-of-law path is unchanged.
