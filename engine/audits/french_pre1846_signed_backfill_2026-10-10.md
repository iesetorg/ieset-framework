# Conservative French pre-1846 signed backfill — 2026-10-10

## Scope and source decision

This isolated candidate begins at committed `c594bfc524d39e6355e32c005efb2a0ab6dda135`. It adds two French national policy episodes, each with one `institutional.rule_of_law` `+ weak` step. The dates are enactment or promulgation years, not estimates of full enforcement or measured rule-of-law levels. Both policies remain `candidate`; neither infers hypothesis support.

| Year | Child policy | Movement | Source basis | Scored claim |
| --- | --- | --- | --- | --- |
| 1804 | `fr_civil_code_1804` | `fr_consulate_civil_codification_1804` | [French National Assembly codification history](https://www.assemblee-nationale.fr/dyn/histoire-et-patrimoine/consulat-et-premier-empire/la-codification-juridique) dates the law consolidating 36 civil laws to 21 March 1804; [the original consolidation law](https://www.assemblee-nationale.fr/evenements/code-civil/cc1804-loi.pdf) preserves the separate executory dates of its component laws. | National legal uniformity and published civil rules justify only a weak positive formal rule-of-law coding. [Unequal family law](https://www.assemblee-nationale.fr/11/rapports/r1240.asp) and imperial coercion block a broader claim. |
| 1814 | `fr_charter_1814` | `fr_bourbon_restoration_charter_1814` | [French National Assembly Charter history](https://www.assemblee-nationale.fr/dyn/histoire-et-patrimoine/restauration/la-charte-constitutionnelle) dates promulgation to 4 June 1814 and describes formal equality before law, judicial independence, and chamber approval of taxation. | These written constraints justify only a weak positive formal rule-of-law coding. Royal initiative and ordinance power, no full separation of powers, and a tax-qualified franchise cap the claim. |

The two focused movements replace the broad archived periods for this import. They link only to the exact child policies above. No other archived policy, axis, or hypothesis link is imported. In particular, the 1830 revised Charter is not silently credited to the 1814 movement.

## Why the other archived scores remain withheld

- The archived French 1789–1791 movement gives a strong rule-of-law increase and a property-rights increase to the August decrees and Declaration together. The [French National Assembly](https://www.assemblee-nationale.fr/dyn/histoire-et-patrimoine/revolution-francaise/nuit-du-4-aout-abolition-des-privileges) says the August decrees received legal force with letters patent published 3 November 1789 and that abolition was staged into 1792–1793. A single strong 1789 national outcome step would hide the staged legal scope and contested enforcement. A separately dated, narrower legal-content coding needs its own review.
- The archived French 1792–1799 episode is `mixed`, not a signed step. Its Convention and Directory policies span opposed institutions and do not supply a single defensible cumulative sign.
- The archived broad 1799–1815 French codification step is `+ moderate`; this import reduces the 1804 Civil Code child to `+ weak` and excludes other imperial years and policies.
- The archived 1814–1848 French episode combines the 1814 and 1830 Charters and later practice. Only the 1814 Charter's formal provisions are coded here; later reforms and the Charter's survival require separate dating and source review.
- The archived U.S. 1789–1800 Federalist scores infer product-market competition from federal commerce authority and spending share from debt assumption without the required comparative spending/GDP evidence. First Bank `financial_deregulation -` also has the wrong sign under the current [axis definition](../../axes.yaml), where negative means looser financial regulation. The existing 1789 constitutional policy remains an unscored context marker.
- The archived U.S. 1801–1815 trade step centers on the 1807 Embargo, which was repealed in 1809. A `- strong` step carried permanently by this cumulative chart would misrepresent a short-lived embargo without a balancing dated reversal. War financing does not itself establish spending share of GDP.
- The archived 1816 Second Bank `financial_deregulation - moderate` similarly conflicts with the current axis sign. Its institutional effect and later expiration would need separate coding.
- The archived 1820–1857 sectional-law movement attributes its signed rule-of-law step to the 1857 Dred Scott decision. Its movement interval starts in 1820, but its documented step is after this pre-1846 backfill window; it does not supply an earlier scored year.

## Generated drift and verification

- Ran `python3 scripts/validate_specs.py`: 6,193 spec files valid with clean cross-references; 47 unrelated candidate forward-reference warnings were reported.
- Regenerated `data/derived/country_drift.json` and `.csv` with `python3 scripts/compute_country_drift.py`; `--check` passed.
- Ran four focused drift test modules: 32 passed.
- Earliest signed year changes 1846 → 1804. The annual grid changes 181 → 223 years; countries remain 145 and axes remain 21.
- Only France's `institutional.rule_of_law` existing-year trajectory changes: +2 in every 1846–2026 year. It is 1 in 1804–1813, 2 in 1814–1845, and 5 in 2026 (versus 3 before). France's first rule-of-law year changes 1901 → 1804; its movement count changes 14 → 16. No other country-axis trajectory or France's final composite drift changes; the latter remains 2.0 because this institutional axis is outside that composite.
- The CSV grows from 46,011 to 46,108 rows. Its 42 pre-1846 rows are exclusively the French rule-of-law series. The derived values are cumulative authored directional scores, not an observed historical country-year panel.

## Display boundary

The integrated drift page now uses a cited pre-1850 policy-context window independent of `data.year_min`. Policy-only 1789, 1802, 1815, 1833, and 1844 cards and dashed markers remain visible; the linked 1804 and 1814 French policies are identified separately. The page labels first signed axis coding (1804) and earliest composite coding (1846) separately and shows the early French rule-of-law axis. Dashed policy-only markers do not contribute scores, even when they appear within the movement grid. The chart suppresses pre-coverage zeroes and bounds its zero reference to the first plotted signed step.
