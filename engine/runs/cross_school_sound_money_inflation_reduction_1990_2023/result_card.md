# Result card - cross_school_sound_money_inflation_reduction_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Sound-money institutions predict lower inflation.

## School Coverage

austrian, chicago_monetarism

## What Was Measured

- Outcome: `inflation`.
- Treatment: `efw_sound_money`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **3,961 observations**, **163 countries**.
- Coefficient on treatment: **-23.3366** (SE 12.1822, p=0.0554).

## Specification

`Q('inflation') ~ Q('efw_sound_money') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
