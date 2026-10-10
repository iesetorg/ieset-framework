# Pre-1781 policy-context scope audit — 10 October 2026

## Decision

`us_articles_of_confederation_1781` is added as an unscored national policy-context record, and only the policy-schema year floor moves from 1788 to 1781. The numeric country drift still starts with authored signed movements in 1789. No movement, axis, hypothesis verdict, run packet, or generated drift value is changed.

## Source and legal timing

The [U.S. National Archives' original Articles transcript and provenance](https://www.archives.gov/milestone-documents/articles-of-confederation) names the thirteen states, records Congress's adoption on 15 November 1777, and states that Maryland's final ratification brought the Articles into force on **1 March 1781**. The [State Department's historical account](https://history.state.gov/milestones/1776-1783/continental-congress) independently gives the same effective date for the national government established by the Articles. The [National Archives' constitutional succession timeline](https://www.archives.gov/founding-docs/constitution-q-and-a) distinguishes the Confederation's legal end on 3 March 1789 from the new government's legal start on 4 March. The policy row therefore uses `effective_date: 1781-03-01`, `start: 1781`, and a year-only `end: 1789`; it does not mislabel the 1777 congressional adoption as legal commencement.

## Country and score boundaries

The Articles call the confederation the United States of America, so `USA` identifies a direct institutional predecessor. The original thirteen states' jurisdiction was not the full present-day U.S. territory, and the row does not imply that every resident, Indigenous polity, or contested western territory was governed by the same rules. It has no `enacted_by`, `axes_moved`, inferred hypothesis links, outcome, or numeric drift contribution. Its policy-browser presence should be read as dated legal context, not an event-study result or an annual national observation.

The earlier [1707 Articles of Union](https://www.parliament.uk/globalassets/documents/heritage/articlesofunion.pdf) are still excluded from a `GBR` country row: they created Great Britain for England and Scotland, excluding Ireland, while the browser labels `GBR` as today's United Kingdom. France's [1685 Fontainebleau edict](https://www.assemblee-nationale.fr/histoire/eglise-etat/revoc-edit-nantes.asp) was a kingdom-wide royal instrument, but the source inspected dates it to October 1685 without establishing a single kingdom-wide operative day. The [1776 Turgot edicts](https://rdf.archives-nationales.culture.gouv.fr/garance/entities/agent/051046/) have a documented Paris Parlement registration on 12 March 1776, which by itself does not establish uniform operation throughout the kingdom. None is used to backdate a national effect or a signed drift step.
