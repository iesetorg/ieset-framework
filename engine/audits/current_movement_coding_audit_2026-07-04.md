# Current Movement Coding Audit - 2026-07-04

Scope: quick atlas-facing review of countries where the 2026 year slider was
likely to show stale incumbent coding after recent national elections or
executive handovers. New records are `candidate` status because most 2026
governments have only weeks or months of observable policy content.

## Updated Turnovers

| Country | Previous atlas current | Corrected current movement | Trigger |
| --- | --- | --- | --- |
| Chile | `chile_boric_ad_2022_present` | `chile_kast_republican_2026_present` | Kast inaugurated 2026-03-11 after 2025 runoff. |
| Colombia | `colombia_petro_2022_present` | `colombia_de_la_espriella_2026_present` | De la Espriella confirmed president-elect after 2026 runoff; handover scheduled 2026-08-07. |
| Bolivia | `bolivia_arce_mas_2020_present` | `bolivia_rodrigo_paz_pdc_2025_present` | Rodrigo Paz took office 2025-11-08. |
| Peru | `peru_boluarte_post_castillo_2022_present` | `peru_keiko_fujimori_2026_present` | Fujimori proclaimed president-elect; handover scheduled 2026-07-28. |
| Costa Rica | no current executive movement | `costa_rica_laura_fernandez_ppso_2026_present` | Laura Fernandez elected 2026 and took office 2026-05-08. |
| Hungary | `hungary_orban_fourth_term_2022_present` | `hungary_magyar_tisza_2026_present` | Tisza won 2026 election; Magyar sworn in May 2026. |
| Bangladesh | `bangladesh_yunus_interim_2024_present` | `bangladesh_tarique_rahman_bnp_2026_present` | BNP won 2026 election; Rahman sworn in 2026-02-17. |
| Thailand | `thailand_paetongtarn_pheu_thai_2024_present` | `thailand_anutin_bhumjaithai_2026_present` | Bhumjaithai won 2026 snap election; Second Anutin cabinet sworn in. |
| Benin | `benin_talon_pag_reform_state_2016_2026` | `benin_wadagni_pag_2026_present` | Wadagni elected and succeeded Talon in 2026. |
| Uganda | `uganda_museveni_nrm_2021_2026` | `uganda_museveni_nrm_seventh_2026_present` | Museveni reelected to seventh term in 2026. |
| Bulgaria | `bulgaria_rule_of_law_schengen_push_2023_present` | `bulgaria_radev_progressive_bulgaria_2026_present` | Radev/Progressive Bulgaria won 2026 snap election and formed government. |

## Already Current / No New Record

| Country | Reason |
| --- | --- |
| Japan | `japan_takaichi_ldp_2025_present` already covered the current cabinet; only the older Ishiba display name was clarified. |
| Canada | `canada_carney_liberal_2025_present` already covered the current government; Trudeau's predecessor movement was ended at 2025. |

## Source Checks

- Chile: Guardian 2025-12-15; El Pais Chile 2026-03-11.
- Colombia: El Pais Colombia 2026-06-24 and 2026-07-04; Guardian 2026-06-24.
- Bolivia: AP 2025-11-09; El Pais 2025-11-08.
- Peru: AP 2026-07-04; El Pais 2026-07-04; FT 2026-07-04.
- Costa Rica: TSE/2026 election reporting; Al Jazeera and France24 election coverage.
- Hungary: AP May 2026; Guardian 2026-05-09; Le Monde 2026-05-10.
- Bangladesh: Guardian 2026-02-17; Le Monde 2026-02-13.
- Thailand: Guardian 2026-02-08; AP 2026-02-08; Second Anutin cabinet reporting.
- Benin: Reuters/AP April 2026 and Benin Constitutional Court reporting.
- Uganda: Washington Post 2026-01-16; El Pais 2026-01-16.
- Bulgaria: El Pais 2026-04-19; Le Monde 2026-04-20; cabinet formation reporting 2026-05-08.

## Validation Note

`python3 scripts/validate_specs.py` still fails on an unrelated pre-existing
hypothesis enum error:

`hypotheses/fiscal/inheritance_tax_family_business_continuity.yaml` uses
`scope.outcome_dim: firm_dynamics`, which is not in the allowed schema enum.

The new/current movement files validate structurally. Their unresolved policy
IDs are candidate-level forward references, which the validator reports as
warnings and explicitly permits for non-canonical movements.
