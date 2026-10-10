# UNHCR host-country labour family: source-key no-go

**Decision:** no hypothesis registration, run, or graduation. The saved UNHCR vintages do not contain a country-of-asylum exposure panel. A global refugee trend cannot be joined to country-year labour outcomes as a host-country observation.

## Source-key inspection before any outcome values

The inventory below uses the locally saved parquet vintages under `data/vintages/unhcr/` that are excluded from Git. The May 5 manifest at `data/manifests/fetch_run_2026-05-05T212957Z.yaml` pins the displayed primary hashes. Inspection read columns, row counts, time ranges, and distinct geographic keys only; no refugee, labour, or population values were inspected.

| Series and saved vintage | SHA-256 | Rows / years | Geographic keys | Host-country usable rows |
| --- | --- | --- | --- | ---: |
| `population@2026-05-05T212209Z.parquet` | `432cf5b4223c0eb1759f00d435b58a962ba4a61c0cfbd0394576ca5fa9e8a74c` | 50 / 1975–2024 | `country_of_asylum_iso3` is `-` in every row | 0 |
| `population_origin@2026-05-05T212259Z.parquet` | `a98e8e4b0d0b8a11d225ed774f1a288df76b8c39e25412cde6533b46e6156f52` | 1,500 / 1975–2024 | 30 distinct `country_of_origin_iso3` keys; no asylum-country field | 0 |
| `asylum_decisions@2026-05-05T212302Z.parquet` | `af5bb03caead10834344e11ef914b6b466a94e880c5ef56ae36df2bfe5419e84` | 0 / no saved observations | no columns or geographic keys | 0 |
| `solutions@2026-05-05T212303Z.parquet` | `5a15b322ec8e87aa1250128acae4df47c90a4a25e4e8a7603dfba5981edce9db` | 50 / 1975–2024 | `country_iso3` is `-` in every row | 0 |

The two April 30 copies of `population` have the same hash and 50 global rows. Their `asylum_decisions` copies are likewise empty. A valid host key for a panel join is a three-letter country ISO code; none appears in any saved UNHCR country-of-asylum series. `population_origin` measures the *origin* side of displacement, so treating it as a host-country exposure would reverse the estimand. The ILO and WDI labour outcome vintages cannot repair a missing host key.

## Consequence for the proposed test

The proposed descriptive estimand would compare change in host-country refugee stock relative to population at year `t` with a later host-country employment or unemployment change, controlling for country and year. Its source join has **zero eligible country-years**, before coverage, sample-size, timing, controls, or multiplicity can be assessed. There is no credible p-value or verdict to register or publish. No causal or policy credit is assigned.

The May 5 data roundup previously described the 50-row `population` vintage as “by country of asylum.” Its column name suggests that grain, but every row is a global aggregate. This audit corrects that inventory label and the matching job label in `scripts/fetch_roundup_mega3.py`; it does not alter the underlying vintage or claim a newly measured result.

To revisit this family, first fetch and hash an actual host-country-year refugee stock panel, verify country-key coverage and duplicate structure, then freeze a design and gates **before** reading outcomes. The future design must distinguish recognised refugees from asylum seekers and IDPs, account for modelled versus observed labour series, use country/year controls and predeclared timing, and disclose noncausal interpretation and family-wise multiplicity. Those conditions are future work, not exceptions to this no-go.

## Reproduction

```python
import pandas as pd
p = 'data/vintages/unhcr/population@2026-05-05T212209Z.parquet'
t = pd.read_parquet(p, columns=['year', 'country_of_asylum_iso3'])
assert len(t) == 50
assert set(t.country_of_asylum_iso3) == {'-'}
assert t.country_of_asylum_iso3.str.fullmatch(r'[A-Z]{3}').sum() == 0
```

The reproduced file is available only in the original local corpus; this isolated worktree does not check the raw vintage into Git.
