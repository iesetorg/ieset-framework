# Result card — fiscal_rule_presence_dampens_statist_drift

**Verdict:** PARTIAL — gap is in the predicted direction (rule-bound -4.07 vs rule-free -1.10, gap -2.97) but Mann-Whitney one-sided p = 0.2685 fails to reject 0.10.

## Group statistics

| Group | n | Median slope/decade | Mean slope/decade |
|---|---:|---:|---:|
| Rule-bound | 14 | -4.07 | -2.97 |
| Rule-free  | 12 | -1.10 | -1.73 |
| Gap (bound − free) | | **-2.97** | |

Mann-Whitney one-sided p (H1: bound < free): **0.2685**

## Rule-bound countries

| Country | Slope/decade | Movements |
|---|---:|---:|
| [ITA](/country/ITA) | -11.05 | 25 |
| [GRC](/country/GRC) | -9.69 | 14 |
| [NLD](/country/NLD) | -6.66 | 18 |
| [FIN](/country/FIN) | -6.60 | 12 |
| [CZE](/country/CZE) | -5.84 | 10 |
| [DNK](/country/DNK) | -5.63 | 9 |
| [ESP](/country/ESP) | -5.02 | 15 |
| [HUN](/country/HUN) | -3.12 | 10 |
| [POL](/country/POL) | -1.01 | 16 |
| [SWE](/country/SWE) | -0.45 | 14 |
| [IRL](/country/IRL) | -0.04 | 17 |
| [CHE](/country/CHE) | +1.51 | 2 |
| [AUT](/country/AUT) | +4.02 | 15 |
| [DEU](/country/DEU) | +7.97 | 19 |

## Rule-free countries

| Country | Slope/decade | Movements |
|---|---:|---:|
| [PRT](/country/PRT) | -8.08 | 10 |
| [ISR](/country/ISR) | -7.93 | 16 |
| [CAN](/country/CAN) | -6.58 | 10 |
| [NZL](/country/NZL) | -5.66 | 10 |
| [BEL](/country/BEL) | -2.62 | 14 |
| [NOR](/country/NOR) | -1.48 | 9 |
| [FRA](/country/FRA) | -0.71 | 17 |
| [GBR](/country/GBR) | -0.43 | 20 |
| [AUS](/country/AUS) | +1.20 | 9 |
| [KOR](/country/KOR) | +1.95 | 11 |
| [JPN](/country/JPN) | +3.35 | 18 |
| [USA](/country/USA) | +6.27 | 24 |

## Steelman live concerns

See `hypotheses/steelman/fiscal_rule_presence_dampens_statist_drift.md`.
Particularly relevant: rule-presence is endogenous to fiscal preferences,
the binary lumps biting + non-biting rules together, and Sondervermögen-
style off-balance-sheet vehicles can circumvent rules without flipping the
treatment indicator.

## Provenance

Reproduces from `data/derived/country_drift.json` + the FISCAL_RULE_BOUND
dictionary in this script. Edit the dictionary + re-run to test alternative
codings (every assignment carries a citation in the YAML).
