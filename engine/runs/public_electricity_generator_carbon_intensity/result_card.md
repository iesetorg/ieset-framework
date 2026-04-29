# Public electricity generators — lower-carbon mix vs privatised, 1970-1999

**Verdict:** SUPPORTED — Public cohort (FRA, SWE) fossil share averaged 8.5% vs private cohort (GBR, USA, DEU, ITA, ESP, BEL, NLD: 7 with data) 68.7% over 1985-1999; ratio 0.12 ≤ 0.75 threshold (≥25% lower). Non-fossil share gap: +60.1pp (public higher). NOTE: 1970-1984 sub-window of the spec (15/30 years) is data-gapped on OWID-Ember; verdict is on the 1985-1999 sub-window only. Causal attribution to public ownership is contested per the spec's own disclosure (resource endowments + postwar planning are correlated).

## Summary

- Spec window: 1970–1999. Public cohort: FRA (EDF, nationalised 1946–2005) and SWE (Vattenfall, public from 1909). Private/privatised comparators: GBR, USA, DEU, ITA, ESP, BEL, NLD.
- **Structural data gap:** OWID-Ember electricity-share series begin in 1985. The 1970–1984 sub-window (15 years, 50% of the spec's 30-year window) cannot be tested with publishers on disk. The IEA energy-balance fetcher needed for the spec's preferred gCO2/kWh outcome has not shipped.
- **Testable sub-window 1985–1999:** Public cohort mean fossil share = **8.5%**; private cohort (with data: GBR, USA, DEU, ITA, ESP, BEL, NLD) mean fossil share = **68.7%**.
- Ratio public/private = **0.12**. Spec's 25%-lower threshold corresponds to ratio ≤ 0.75.
- Informative: public-cohort non-fossil (nuclear + renewables) share is **+60.1pp** higher than private cohort. OWID CO2-intensity-of-GDP ratio public/private = 0.62.

## Method

**Primary statistic:** ratio of public-cohort mean fossil share of electricity to private-cohort mean fossil share, averaged across overlap years in 1985–1999.

**Threshold map:**
- ratio ≤ 0.75 → SUPPORTED (≥25% lower)
- 0.75 < ratio < 1.0 → partial
- ratio ≥ 1.0 → refuted

**Method validity gate:** at least 5 years of OWID coverage in 1985-1999 for both public-cohort countries AND for at least 4 of 7 private comparators. PASSED: public 2/2, private 7/7.

**Why fossil share, not gCO2/kWh?** The spec's preferred outcome is electricity-sector CO2 intensity (gCO2/kWh) from IEA energy balances. That fetcher has not shipped. OWID-Ember share-electricity-fossil-fuels is the closest publisher-on-disk proxy: lower fossil share => lower grid CO2 intensity, with near-1:1 ranking in this period because non-fossil = nuclear + hydro + nascent renewables (gas/coal carbon factors dominate). Reported alongside is OWID co2-intensity (CO2/GDP) for context.

## Data

- owid:share-electricity-fossil-fuels (Ember-derived; primary outcome proxy)
- owid:share-electricity-nuclear (Ember-derived; informative)
- owid:share-electricity-renewables (Ember-derived; informative)
- owid:co2-intensity (informative — CO2/GDP, not electricity-specific)

## Caveats

- **Causal attribution is contested** even if the descriptive gap holds. Per the spec's own disclosure: EDF's nuclear-heavy mix and Vattenfall's hydro+nuclear mix were largely the products of national resource endowments (Sweden's hydro; France's uranium-policy-driven Messmer plan from 1973) and postwar industrial planning, not cleanly attributable to public-ownership status.
- **Matched-private comparators are scarce.** The 'private' cohort mixes IOU-dominant USA (regulated monopolies, not market-disciplined) with continental utilities that were variously state-owned, municipally owned, or only privatised mid-window (GBR 1990; ITA ENEL partial 1992; ESP partial 1990s).
- **1970–1984 unmeasured.** The spec's claim explicitly covers the 1970s; the structural data gap means the verdict above can only speak to the 1985-1999 window. A v2 using the IEA energy-balance fetcher could close this gap.
- **No statistical inference.** The spec calls for p<0.10 in 5-year rolling windows; with N=2 public countries the conventional t-test is degenerate, so we report descriptive ratios and rolling-window diagnostics instead. See diagnostics.json's `rolling_5yr_table`.
