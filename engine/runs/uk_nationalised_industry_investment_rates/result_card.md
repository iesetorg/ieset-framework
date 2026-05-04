# UK nationalised-industry investment rates vs DEU/FRA peers (1950-1979)

**Verdict:** weakened — UK mean csh_i 1950-1979 23.0% vs DEU+FRA peer mean 31.9% (UK undershoots by 8.9pp — outside the ±5pp SUPPORTED band but short of the 10pp REFUTED threshold). Direction is consistent with public-ownership investment crowd-out but not dispositive.

## Summary

- UK mean gross capital formation share of GDP 1950-1979: **23.0%**.
- DEU+FRA peer mean over same window: **31.9%**.
- Gap (UK − peer mean): **-8.9pp**.
- Per-country means: GBR 23.0%, DEU 35.9%, FRA 27.9%.
- Years UK below peer mean: **30/30**.
- METHOD_VALID gate (≥28/30 obs per country): pass — coverage {'DEU': 30, 'FRA': 30, 'GBR': 30}.

## Method

Country-level mean comparison of PWT csh_i (gross capital formation share of GDP at current PPPs) for GBR vs unweighted mean of {DEU, FRA} over 1950-1979. The PRIMARY statistic is the absolute gap between the UK mean and the peer mean. SUPPORTED band: |gap| ≤ 5pp. REFUTED: UK below peers by > 10pp. Asymmetric REFUTED zone reflects the directionality of the original claim (the market-socialist position is that UK nationalised industries were not investment-starved; the natural refutation direction is therefore UK undershoot).

## Steelman (for and against)

**For the claim (market-socialist):** UK post-war investment was constrained by stop-go macro policy and BoP crises, not by ownership form per se. France and Germany also had major state industries (Renault, Charbonnages, Bundesbahn, Volkswagen) — the comparison overstates the ownership contrast. Sector-level studies (Pryke 1981) suggest UK nationalised industries had investment rates roughly in line with private-sector capital intensity given their factor mix.

**Against the claim (market-liberal):** The 8-9pp UK shortfall in country-level investment share over 1950-1979 is large by international-comparison standards. It is unlikely the entire shortfall is private-sector: the nationalised industries were ~10% of GDP and a much larger share of fixed capital formation, so a country-level investment-share gap is at least consistent with — though does not prove — sectoral-level investment crowd-out.

## Caveats (v2 downgrade from sector-level)

v2 substitutes a country-level investment-share for the original sector-level (coal/rail/steel/gas) test. This conflates the nationalised-sector signal with private-sector business investment differences (the German Wirtschaftswunder was largely private). A v3 with OECD STAN sectoral data, BoE Three Centuries, or hand-coded Pryke 1981 figures would supersede this. The v2 thresholds (5pp SUPPORTED, 10pp REFUTED) are correspondingly strict.

## Data

- pwt:csh_i — gross capital formation share of GDP at current PPPs.
- Vintage: `data/vintages/pwt/pwt_full@2026-04-30T142427Z.parquet`
- sha256: `f081fc093bc4aee806a81d69feb34b9fb8f738bad207fcc7853fe8557731bbc0`
