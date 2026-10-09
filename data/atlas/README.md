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
