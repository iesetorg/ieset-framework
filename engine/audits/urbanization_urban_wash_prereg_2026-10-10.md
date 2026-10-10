# Blind registration: urbanization and later urban water/sanitation coverage

**Family:** `urbanization_urban_wash_forward_2026_10_10` — three correlated
descriptive outcomes, not three independent policy effects. **Status at this
registration:** selected WHO/JMP outcome country/year/dimension **keys only**
were opened. No WHO selected value, value-null mask, fitted coefficient, sign,
or verdict was read. WDI urban-share exposure and income-control values were
inspected. The first-addition registration commit, later source-lock commit,
and only then measured result must be separate commits.

## Fixed question and periods

Does faster observed **national urban-population-share growth** from `t−4` to
`t` predict slower subsequent improvement in **urban-resident** service
coverage from `t` to `t+4`, after fixed controls? Anchors are 2004, 2008,
2012, 2016, and 2020. The primary outcomes are WHO/JMP urban safely managed
drinking water, urban safely managed sanitation, and urban at-least-basic
drinking water. Basic and safely managed water overlap; they remain one
family. Urban-only outcomes avoid the direct national weighted-average
composition effect of adding urban residents, but changing urban composition
and reclassification still matter.

The registered strain direction is **negative** for every outcome. A
comparably positive result refutes that direction. One exposure unit is one
percentage point of national urban-share change; one outcome unit is one
percentage point of urban service coverage change. The practical coefficient
magnitude is 0.2 outcome point per exposure point. The family uses two-sided
Bonferroni `p <= 0.01/3` for each endpoint. This local correction does not
cover selection across the wider IESET archive.

## Source custody before value access

| Role | Exact local vintage SHA-256 | Tracked fetch manifest SHA-256 |
| --- | --- | --- |
| WDI urban share `SP.URB.TOTL.IN.ZS` | `d3545e1c27b14eabafd3cbe7bbbc5edb5f21c7b97954ab76fc70392599c675f6` | `fetch_run_2026-05-05T210519Z.yaml` `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| WDI real GDP per person `NY.GDP.PCAP.KD` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `fetch_run_2026-05-05T200056Z.yaml` `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| WHO safely managed urban water `WSH_WATER_SAFELY_MANAGED` | `c0ed754e9d42fda94390ebbe2be36fc630e4e2e8e05f9a1a57aeb75178a6bc91` | `fetch_run_bootstrap_2026-04-30T121833Z.yaml` `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |
| WHO safely managed urban sanitation `WSH_SANITATION_SAFELY_MANAGED` | `c55eb958ce8409eafc335fb20eb74a0562d8650d6a3372e141f2e64243d4b077` | same WHO manifest |
| WHO at-least-basic urban water `WSH_WATER_BASIC` | `3ac26b7c74273cb93ae7e0bf6a87e6ce6bf02617f5df703ad07668fcb176e162` | same WHO manifest |

The raw vintages are in the local ignored source corpus and are **not** copied
into this branch. The runner takes `--source-root`, verifies all exact raw and
manifest hashes, and records only aggregate sample and model diagnostics.
The WHO fetch manifest records `CC-BY-NC-SA-3.0 IGO`; raw publication and
derived public-display rights need review. Source pins do not grant them.

The frozen key-only roster is
`data/pinned_evidence/urbanization_urban_wash_2026_key_roster.csv`, SHA-256
`5d573db8488c6649d85b84e45276e5c05f50ac1b3b63863064f0f57f6d14eef8`.
Its upper-bound counts use only country ISO3/XKX, `SpatialDimType=COUNTRY`,
`Dim1Type=RESIDENCEAREATYPE`, `Dim1=RESIDENCEAREATYPE_URB`, exact WHO
country/year/indicator keys at `t−4,t,t+4`, valid WDI exposure and income
values at `t−4,t`, and at least three key anchors per country. They do not
imply WHO selected values are present.

| Outcome | Blind key rows / countries | Exposure rises ≥1 point, rows / countries | Flat exposure ≤0.2 point, rows / countries |
| --- | ---: | ---: | ---: |
| Safely managed urban water | 486 / 99 | 263 / 74 | 80 / 35 |
| Safely managed urban sanitation | 590 / 120 | 294 / 83 | 102 / 48 |
| At-least-basic urban water | 850 / 174 | 436 / 123 | 140 / 62 |

## Frozen model and no-go gates

At each anchor, dependent variable is urban WHO coverage `t+4−t`; treatment
is WDI urban share `t−(t−4)`. Fixed controls are prior urban share,
baseline urban service coverage, preceding four-year service change, log real
GDP per person at `t`, and prior four-year log-income change. Include country
and anchor fixed effects, country-cluster CR1 covariance with small-sample
correction, and two-sided Student `t(G−1)`. The five four-year outcome windows
are adjacent without overlap; repeated countries still require clustering.

Keep only finite selected WHO values in `[0,100]`, no imputation or source
switch. Reject urban-share jumps with absolute magnitude over 10 points and
countries with fewer than three complete anchors. Outcome-specific complete
case floors are **350 rows/70 countries** for safe water, **400/80** for safe
sanitation, and **600/120** for basic water. Every outcome additionally needs
at least four anchors, 80 material-rise rows across 30 countries, and 20
flat-exposure rows across ten countries. Fail on rank deficiency, nonfinite or
nonpositive clustered uncertainty, or residualized-exposure concentration
above 25% in the top 1% of rows, 15% in one country, or 35% in one anchor.
These fixed gates produce **INCONCLUSIVE** even if an estimate could be
printed. Otherwise beta ≤−0.2 and `p<=0.01/3` is **SUPPORTED** for the
narrow strain association; beta ≥+0.2 and that p is **REFUTED**; any other
estimable result is **PARTIAL**. Gate-cleared PARTIAL, SUPPORTED, and REFUTED
are public **descriptive calibrations**; INCONCLUSIVE is archived. None earns
causal, policy, school, position, or featured credit.

WHO/JMP makes estimates from survey, census, and administrative inputs;
reported urban safe-water series can use regression and extrapolation. WDI
urbanization uses nationally defined urban areas and UN population estimates.
These constructed trends can co-move for measurement reasons. Unmeasured
infrastructure spending, migration composition, capacity, income, and
reclassification remain confounders.

Definitions: [WHO safely managed drinking
water](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/population-using-safely-managed-drinking-water-services-%28-%29),
[WHO safely managed
sanitation](https://www.who.int/data/gho/data/indicators/indicator-details/gho/population-using-safely-managed-sanitation-services-%28-%29),
[WHO WASH monitoring](https://www.who.int/data/gho/data/themes/topics/sdg-target-6-ensure-availability-and-sustainable-management-of-water-and-sanitation-for-all),
[World Bank urban share](https://databank.worldbank.org/metadataglossary/africa-development-indicators/series/SP.URB.TOTL.IN.ZS).
