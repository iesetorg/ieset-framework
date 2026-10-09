# Atlas election reviews

The `election_reviews_*.json` files contain dated, sourced national election
and government checks. They are a selective review, not a claim that every
country or every election has been verified. The atlas reads these files
directly at build time; publication requires a new site build and deployment.

Keep one review per ISO3 across all files. Record election status separately
from government formation: a plurality, provisional count, coalition agreement,
or nomination to form a government does not establish an executive handover.
Use `coverage_note` for uncertified results, sources unavailable directly,
interim-government gaps, and missing policy evidence.

- `checked_on`: the actual source-review date, never an automatic freshness stamp.
- `election_date`: polling/runoff date; explain multi-day polls in the type or summary.
- `government_start_date`: verified assumption of office; explain any pre-election
  cabinet or scheduled future start explicitly.
- `movement_ids`: current governing-movement IDs, or an empty array while the
  government has no authored policy-content record. A caretaker can retain its
  current ID while formation is pending.
- `superseded_movement_ids`: explicitly retired predecessors. The current-year
  map hides them after a formed government's effective start date.
- `superseded_on`: use when a separately verified retirement preceded the current
  election/formation process, as in Latvia. Supply the source proving that date.
- `sources`: descriptive titles and direct HTTP(S) evidence links.

Older annual map slices retain governments active at any time during their year.
The current-year map applies verified handovers and leaves reviewed governments
unclassified when their movement or referenced policy records are missing.
Resolved policy references are a structural minimum, not a validation of policy
effects or ideological assignments. Do not create policy IDs or axis directions
from campaign promises merely to colour an election winner.

After editing, run `npm run test:site` from `web` and
`venv/bin/python scripts/validate_specs.py` from the repository root. The atlas
tests validate dates, unique countries, safe links, movement/country references,
and the distinction between historical coverage and current office-holding.

## Historical coverage

The policy-movement layer begins at the earliest authored national movement (currently 1789).
Its country inventory includes ISO countries **and territories**, plus explicitly
labelled historical and disputed entries. Small countries remain searchable even
when the low-resolution map has no polygon for them. Present-day map boundaries
are reference geography, not reconstructed borders or a claim that today's state
existed under the same authority in every selected year.

Three kinds of evidence remain distinct:

1. **Policy movements** are authored national movement intervals. Empty years
   remain gaps; neither a dated policy nor a constitutional event fills them.
2. **Policy records** expose dated national policies independently of movement
   coverage. Their candidate/canonical status and date basis remain visible.
3. **Constitutional history** imports the Comparative Constitutions Project's
   chronology with source identifiers, entity mappings and country-specific
   coverage limits. These events do not create policy scores, movements or
   ideological alignments. Source years are not interpolated into new observations.

The 2026-10-09 policy review adds sixteen independently sourced economic-policy
records in thirteen countries. Three bounded reform episodes have conservative
axis coding; the remaining institution-founding records have no axis direction.
Creating a central bank alone does not prove independence, monetary expansion,
financial tightening or an increase in government spending. One-year intervals
mark documented decisions, not the full lifespan of institutions or laws.
The record-level review is in `historical_policy_review_2026_10_09.json`.

Run the historical import and coverage audits in check mode after changes, along
with the site tests and specification validation. Changes to movement axes also
require regenerating the country drift data and its coverage audit. All data
layers are published by rebuilding the site; a local audit is not evidence of a
production deployment.

The separate `historical_context_supplements.json` file adds nine selected events
from official sources for Saint Lucia, Palau, Palestine, San Marino and Vatican
City. San Marino extends the historical-context layer to 1600; a verified Vatican
law extends that layer to 2026. Neither changes the pinned CCP 1789–2025 range.
The country timelines preserve the original CCP gap notice and label each added
event as a primary-source supplement. These selected dates do not fill the years
between events or imply a complete constitutional history.

Historical maintenance commands (from repository root):

```sh
venv/bin/python scripts/import_atlas_constitutional_history.py --check
venv/bin/python scripts/audit_atlas_history.py --check
venv/bin/python -m pytest tests/test_atlas_constitutional_history.py tests/test_atlas_history_audit.py
```
