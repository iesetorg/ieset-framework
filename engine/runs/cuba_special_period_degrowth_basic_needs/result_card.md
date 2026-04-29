# Cuba Special Period basic-needs preservation — v3 honesty correction

**Verdict:** inconclusive — canonical basic-needs basket incomplete. v2 graded SUPPORTED on a 3-indicator favourable subset (LE/IMR/enrolment) while caloric supply collapsed ~30% (Garfield & Santana 1997) and the 1994 balsero crisis revealed mass emigration. v3 requires the canonical basket (Streeten/Sen/UNDP HDI extensions). Missing canonical inputs: P2_caloric_supply_1989_2000, P4_emigration_annual_1989_2000. FAO caloric obs in window: 0/12; emigration obs: 2/12.

## Why v3 lands inconclusive

v2 graded SUPPORTED on a 3-indicator subset (LE / IMR / primary enrolment) while caveats explicitly noted that caloric supply per capita dropped ~30% from ~2,900 to ~1,800 kcal/cap/day between 1989 and 1993 (Garfield & Santana 1997 / FAO FBS) and that the 1994 balsero crisis produced ~35,000 emigration attempts in August alone. That's indicator gaming.

Canonical basic-needs literature (Streeten 1981, Sen, UNDP HDI extensions) treats food security as the primary basic need; emigration as the canonical revealed-preference welfare metric. SUPPORTED on a favourable subset while the canonical-primary indicator collapsed is not an honest affirmation.

## v3 canonical basket

| Dimension | Source | On disk for 1989-2000? |
|---|---|---|
| GDP per capita | WDI NY.GDP.PCAP.KD | ✓ |
| Caloric supply / cap / day | FAO FBS | **✗** (slug covers 2010+ only) |
| Life expectancy | WDI SP.DYN.LE00.IN | ✓ |
| Infant mortality | WDI SP.DYN.IMRT.IN | ✓ |
| Primary enrolment | WDI SE.PRM.ENRR | ✓ |
| Emigration (annual) | cuba_manual | **✗** (decade-stamp only) |

4 of 6 canonical dimensions testable; 2 are documented data gaps. Per the framework's indicator-integrity rule, omission of canonical indicators triggers METHOD_VALID failure → inconclusive, not SUPPORTED on the favourable subset.

## INFORMATIVE-only v2 subset numbers (NOT a verdict)

- gdp_pc_peak_to_trough_decline_fraction: 0.3662
- max_le_decline_fraction: 0.0000
- max_imr_rise_fraction: 0.0000
- max_enrol_decline_fraction: 0.0372

## Documented qualitative evidence (un-tested)

- Caloric collapse 1989→1993: ~30% decline (Garfield & Santana 1997)
- 1994 balsero crisis: ~35,000 attempts in August alone
- Libreta persistence: 63% of households as of 2024

## Fetcher backlog

- faostat:food_balance_sheets full annual 1961+
- cuba_manual emigration annual 1989-2000

## Archives

v0 at ARCHIVED_v0/. v2 (3-indicator subset, SUPPORTED) at ARCHIVED_v2/.
