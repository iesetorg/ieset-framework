# U.S. Judiciary Act of 1789: policy-only coverage audit (10 October 2026)

## Finding and scope

The policy corpus had a 4 March 1789 marker for the legal start of constitutional government (`us_constitutional_government_1789`) but no separate entry for the Judiciary Act. This statute is a distinct institutional act, so `us_judiciary_act_1789` records it as a **candidate policy-only event**. It adds no movement or numeric drift step.

## Primary-source date and content check

- [The enrolled Act and National Archives transcript](https://www.archives.gov/milestone-documents/federal-judiciary-act) identify Washington's signature on **24 September 1789**. [The Statutes at Large text, 1 Stat. 73, ch. 20](https://wwws.loc.gov/law/help/statutes-at-large/1st-congress/session-1/c1s1ch20.pdf) ends with the same approval date. That is the `enacted_date`, not the 4 March constitutional commencement.
- Sections 1–6 of the [statute](https://wwws.loc.gov/law/help/statutes-at-large/1st-congress/session-1/c1s1ch20.pdf) established a six-justice Supreme Court, thirteen federal districts and district courts, and circuit courts. Sections 9, 11, and 25 specify **bounded** federal and appellate jurisdictions. The Act did not give lower courts every federal-question power potentially allowed by Article III; the [National Archives explanation](https://www.archives.gov/milestone-documents/federal-judiciary-act) states this limit explicitly.
- The statute scheduled the New York and New Jersey district courts' first regular sessions for **3 November 1789** (the first Tuesday of November). These are scheduled dates, not proof that both courts actually convened that day. Circuit sessions were scheduled across districts in April–May 1790. The [Supreme Court's own history](https://www.supremecourt.gov/about/faq_general.aspx) identifies **2 February 1790** as its first actual opening, following a one-day quorum delay. Practical operation therefore had no single nationwide date; `effective_date` is intentionally omitted.

## Geographic and inference boundary

The Act was federal legislation (`scope: national`) but section 2 named thirteen districts in the **eleven then-covered states**, with Maine and Kentucky being districts within Massachusetts and Virginia. It named no North Carolina or Rhode Island district, and it did not extend the same institutions to every present-day U.S. location. The country tag identifies the federal government, not uniform historical reach. The record has no `axes_moved`, `enacted_by`, outcome claim, or hypothesis link. An institutional rule-of-law score would require a separate, reviewed movement and explicit treatment of the Act's limited jurisdiction and unequal historical coverage. This entry alone changes neither the 1789 U.S. numeric drift series nor the public hypothesis census.

## Verification

`python3 scripts/validate_specs.py` accepted 6,240 specifications; its 47 candidate forward-reference warnings were pre-existing permitted warnings. `python3 scripts/compute_country_drift.py --check` passed with the existing 1789–2026 grid (145 countries, 21 axes), confirming this policy-only addition does not alter the generated drift map. `git diff --check` passed.
