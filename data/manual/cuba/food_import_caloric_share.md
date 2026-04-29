# Provenance — food_import_caloric_share

**Indicator.** Share of Cuban food supply (caloric value) sourced from
imports.

**Series values.** 70% (2015), 75% (2018), 80% (2020), 80% (2022).

## Why FAOSTAT FBS alone is insufficient

The FAOSTAT Food Balance Sheets bulk dataset publishes per-item
production, import, and export quantities in tonnes (1000 t units), but
ships caloric quantities only as supply totals (kcal, kcal/capita/day).
There is no element row for "import quantity in kcal" — caloric-share
calculations require a kcal-conversion-factor table applied to the tonnage
imports, which Cuban academic and policy sources publish directly. The
IESET FAOSTAT fetcher emits a tonnage-based import share for the LatAm
panel as a transparency cross-check (Cuba 2010-2019 ≈ 13-18% by tonnage,
which is *not* the caloric figure — staple imports like rice and wheat
have high caloric density per tonne whereas Cuba's residual sugar/citrus
exports have low caloric density per tonne, so caloric-share runs ~4-5x
the tonnage share for Cuba specifically).

## Citation chain

1. **Nova-González, Armando** (Cuban academic, Universidad de La Habana
   CEEC). *"La agricultura en Cuba: evolución y trayectoria, 1959-2018"*,
   2020. Estimates 70% caloric food imports as of 2015; rising through
   2018.

2. **Mesa-Lago, Carmelo.** *Cuba's New Economy: Towards a Mixed Economy.*
   2022. Chapter 5 places Cuba's caloric food import share at 75-80% for
   2018-2019, citing FAO FBS-derived calculations and ONEI agricultural
   yearbooks.

3. **MINAG (Ministerio de la Agricultura) Cuba official statement.**
   Minister Ydael Pérez Brito, National Assembly address, December 2021:
   "Cuba importa cerca del 80% de los alimentos que consume" (Cuba imports
   approximately 80% of the food consumed).
   Source: Granma, 16 December 2021; Reuters, 16 December 2021.

4. **MINAG 2023 reaffirmation.** Cuban Minister of Agriculture, May 2023
   National Assembly review, again cited 80% imported food share. Source:
   Reuters reporting, 14ymedio coverage.

## Threshold evaluation

Pre-registered threshold: `>60% of food supply imported by caloric value
in any year 2015-2023`. Maximum observed = 80% (2020, 2022) → MET.

## Methodology note

The values here are point-estimate-with-citation. They are not a
machine-derived FAOSTAT panel — the caloric-share calculation requires
either (a) an FAO Production-PINs aggregation we do not currently
replicate, or (b) the academic/official statements above. We default to
(b) for tractability and document the gap honestly.

If a future fetcher implements the caloric conversion from FAOSTAT FBS
tonnage rows, this manual series should be retired in favour of the
machine-derived panel.
