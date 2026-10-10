# Policy date and provenance audit — 2026-10-10

Scope: the 3,426 policy YAML files in this isolated checkout, after the three record repairs below. Counts are audit signals, not findings that each policy has a wrong date.

## Corpus screen

| Signal | Count | Interpretation |
| --- | ---: | --- |
| No nonblank external `references` | 1,141 | 1,127 also have `enacted_by` movement links; the 14 others need independent source review. |
| No references but an asserted enacted/effective/event date of any precision | 315 | Two are less than day precision; this is not itself an exact-date cohort. |
| No references but a parsed YYYY-MM-DD enacted/effective/event date | 313 | Registry timing readiness is now withheld via `needs_exact_date_source`. Raw dates remain visible for audit. |
| First four-digit year in `policy_id` later than `timeframe.start` | 586 | Filename comparison only; IDs may contain targets or ranges. |
| Same screen, no references | 496 | Candidate review queue, not automatic date corrections. |
| Same screen, start equals an `enacted_by` movement start | 503 | Pattern consistent with inherited movement periods. |
| Same screen, no references, parent start, and later year appears in title and description | 443 | Stronger triage signal, still not legal-date proof; 151 have gaps of at least five years. |

The year screen uses the first standalone 1700–2199 year in the ID. It can flag a target year or a policy whose implementation preceded its named statute. It must not drive bulk rewriting. A nonempty `references` array means only that a source is listed; it does not establish that the source supports the asserted date.

## Three source-backed corrections

| ID | Previously shown | Corrected treatment timing and scope | Source and coding decision |
| --- | --- | --- | --- |
| `us_securities_exchange_act_1934` | 1933–1939, with parallel welfare, fiscal, and labour axes | 1934 start; enacted 6 June 1934; general first effect 1 July 1934, with staged September/October provisions | [U.S. Code §§78a, 78hh](https://www.govinfo.gov/content/pkg/USCODE-2024-title15/html/USCODE-2024-title15-chap2B.htm). Retained only the tighter financial-regulation axis; removed unrelated New Deal scores and generic inferred hypothesis links. |
| `india_bank_nationalisation_1969` | 1951–1991; bundled 1980 tranche and later credit rules | 1969 start; first acquisition effective 19 July 1969; continuing ownership is separate from a 1991 end | [India Code, 1970 Act metadata](https://www.indiacode.nic.in/indiacode/handle/123456789/1373?view_type=browse) states 31 March 1970 enactment and 19 July 1969 enforcement; [Reserve Bank of India history](https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=1160) distinguishes 14 banks in 1969 from six in 1980. Withheld four inherited axes pending intervention-specific coding; the old financial-axis sign also conflicted with axis semantics. |
| `france_pinay_rueff_stabilisation_1958` | 1945–1975; said the new franc was introduced in 1958 and bundled unrelated axes | 1958–1960 programme. Multiple component dates; no single exact event date assigned to the whole bundle. | [French finance ministry Pinay archive](https://www.economie.gouv.fr/files/files/directions_services/saef/docs_joints/rech_en_arch/Ministres/CabPinay_B-0068964_B_0068976_1A-0000409_1A-0000452.pdf) dates the Rueff committee to 15 October 1958, monetary ordinance to 27 December, and most measures to 31 December. [Légifrance monetary ordinance](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000339269) and [1959 implementing decree](https://www.legifrance.gouv.fr/loda/id/LEGIARTI000006725763/1959-12-23) distinguish the 1958 decision from the new franc's 1 January 1960 use. Retained only documented trade opening. |

`end: ongoing` on the US and India records denotes a continuing, amended statute/ownership arrangement, not a claim that the initial event treatment has been unchanged. No hypothesis verdict, registration, threshold, or movement axis was changed. The three records remain `candidate`.

## Downstream trace and boundary

- `scripts/generate_policy_browser_index.py` copies raw policy timeframe. `web/lib/policy-browser.ts` sorts/filters its browser rows from `timeframe.start`; `web/app/p/[id]/page.tsx` displays that start directly. Thus an inherited movement year can mislead policy cards even where no exact event date is asserted. `web/app/p/page.tsx` uses effective/enacted date for the timeline event year when present, otherwise the raw start. These surfaces need a separate provenance-aware display pass; this audit corrects only the three evidenced records.
- The event-treatment registry previously awarded `ready_for_event_study_timing` for any parsed full date, with no source check. Its generator now retains raw dates and `timing_status`, adds `has_source_references` and `exact_date_reference_status`, and blocks the 313 uncited exact-date rows. On this checkout, 2,137 rows have raw full dates; 1,824 have a reference present, but the dates in those references have **not** been individually verified. The flag is a minimum source-presence gate, not proof of treatment identification.
- `scripts/compute_country_drift.py` reads movement timeframe and reviewed movement axis attribution years, not policy timeframe. These policy corrections therefore do not create a pre-1789 drift step or directly alter numeric country drift. The parents of the India and France records still have broad movement-period axis coding; those require a separate country-level evidence review before any movement or map change.

No generated registry, browser, evidence, or site index is part of this commit; the integration owner will regenerate them after merging the source changes.
