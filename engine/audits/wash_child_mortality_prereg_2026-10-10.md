# Blind registration: safe WASH services and later under-five mortality

**Family:** `wash_service_child_mortality_forward_2026_10_10`. Two correlated
exposure tests share one health outcome and one family correction. Before this
first-addition registration, WHO/JMP national service exposure values and WDI
real-income control values were inspected. Only WDI under-five mortality
country/year/indicator **keys** were read: no mortality value, value-null mask,
fitted result, sign, or verdict. Registration, source lock, and measurement must
be separate commits.

## Fixed question, direction and periods

Does a larger national rise in safely managed **drinking water** or
**sanitation** coverage from `t−4` to `t` predict a larger fall in under-five
mortality from `t` to `t+4`? Fixed anchors are 2004, 2008, 2012, 2016, 2020.
The WDI outcome is the natural log of mortality per 1,000 live births at `t+4`
divided by mortality at `t`. One exposure unit is one percentage point of
national WHO/JMP coverage change. The registered slope is negative. A slope
at most **−0.002** log points per exposure point with two-sided `p≤0.005`
supports the narrow association; a slope at least **+0.002** with that p
refutes it. Other estimable results are PARTIAL. Two-sided Bonferroni controls
this two-exposure family at 0.01, but does not adjust selection across the
wider IESET archive.

## Source custody and blind roster

| Role | Pinned raw SHA-256 | Tracked fetch-manifest SHA-256 |
| --- | --- | --- |
| WHO national safe water `WSH_WATER_SAFELY_MANAGED` | `c0ed754e9d42fda94390ebbe2be36fc630e4e2e8e05f9a1a57aeb75178a6bc91` | `fetch_run_bootstrap_2026-04-30T121833Z.yaml` `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |
| WHO national safe sanitation `WSH_SANITATION_SAFELY_MANAGED` | `c55eb958ce8409eafc335fb20eb74a0562d8650d6a3372e141f2e64243d4b077` | same WHO manifest |
| WDI real GDP per person `NY.GDP.PCAP.KD` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `fetch_run_2026-05-05T200056Z.yaml` `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| WDI under-five mortality `SH.DYN.MORT` | `ad63729ccd5d1d4be6f3da5bbcac45b8a2c87d48c063cefeba8f0ddbe4b88f55` | same WDI manifest |

Raw vintages remain in the ignored local corpus; they are not copied to this
branch. The runner checks raw and manifest hashes and requires a later committed
source lock before projecting WDI mortality values or status. The frozen
country/anchor key roster is
`data/pinned_evidence/wash_child_mortality_2026_key_roster.csv`, SHA-256
`ad59eb9f838b41eb3e1f30babd35dc05370a684b30a4403f240792505e076af9`.
Keys use national ISO3/XKX countries, WHO `COUNTRY` and
`RESIDENCEAREATYPE_TOTL`, finite service coverage `[0,100]` at `t−4,t`,
positive real income with blank/null observation status at `t−4,t`, WDI
mortality **keys** at `t−4,t,t+4`, absolute exposure jump no more than 30
points, and at least three key anchors per country. These are upper bounds;
they do not reveal whether mortality values are present.

| Exposure | Blind key rows / countries | Material rises ≥2 pp, rows / countries | Flat exposure ≤0.2 pp, rows / countries |
| --- | ---: | ---: | ---: |
| Safely managed drinking water | 696 / 142 | 189 / 52 | 174 / 53 |
| Safely managed sanitation | 683 / 139 | 264 / 64 | 115 / 45 |

## Frozen measurement and falsification gates

Keep WDI mortality values in `(0,500]` per 1,000 births and blank/null status
at all three years; no imputation or vintage replacement. Exclude countries
with fewer than three complete anchors. The model has prior service level at
`t−4`, baseline log mortality at `t`, preceding log-mortality change
`t−4→t`, log real GDP per person at `t`, preceding log-income change,
country fixed effects, and anchor fixed effects. Fit ordinary least squares
with country-cluster CR1 covariance, small-sample correction, and two-sided
Student `t(G−1)` inference. Four-year outcome windows are adjacent without
overlap; repeated countries are clustered.

Each exposure needs **500 complete rows, 100 countries, four anchors**;
at least **80 material-rise rows in 25 countries** and **20 flat rows in ten
countries**. Fail if the design lacks full rank, clustered uncertainty is
nonfinite or nonpositive, or residualized exposure squared weight exceeds
25% in the top 1% of rows, 15% in one country, or 35% in one anchor. A failed
gate yields **INCONCLUSIVE archive**, even when a coefficient could be
estimated. Gate-cleared SUPPORTED, REFUTED, and PARTIAL receive public
**descriptive calibration only**, with zero causal, policy, school, position,
and featured credit.

Both series are modeled: WHO/UNICEF JMP estimates service access from surveys,
censuses, and administrative data; the World Bank indicator uses UN IGME
under-five mortality estimates. Vaccination, clinical care, nutrition,
fertility, conflict, income, reporting, and development trends can change
both series. Controls and temporal order do not identify a causal WASH effect.
Water and sanitation are correlated, so even two public records remain one
question family. WHO manifest records `CC-BY-NC-SA-3.0 IGO`; rights review is
required before distributing raw files or derived public displays.

Definitions: [WHO safely managed drinking water](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/population-using-safely-managed-drinking-water-services-%28-%29),
[WHO safely managed sanitation](https://www.who.int/data/gho/data/indicators/indicator-details/gho/population-using-safely-managed-sanitation-services-%28-%29),
[WDI under-five mortality](https://databank.worldbank.org/metadataglossary/health-nutrition-and-population-statistics/series/SH.DYN.MORT).
