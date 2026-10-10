# WHO exposure changes and later premature NCD mortality — locked results

Registration `a2b524ff965411f0ee6360bfeb03d12c397f14ca` strictly preceded source lock `4cae7d23789c82fefebe84eb3d7dafe7fc526e23` and all measured runs.
Three original WHO source files were SHA-256 checked against the tracked bootstrap fetch manifest. Their license is CC-BY-NC-SA-3.0 IGO; redistribution needs review before publishing.
This is one two-test descriptive family, two-sided family alpha 0.01, Bonferroni cutoff 0.005. Both tests remain in the denominator.

| Comparison | Source-key countries | Complete | HC3 slope | Two-sided p | Region holdout signs | Gate failures | Verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| smoking | 161 | 161 | 0.012020939361503398 | 0.8305923195768038 | +5/6, -1/6 | none | **PARTIAL** |
| pm25 | 184 | 184 | -0.06925646714522106 | 0.43732366550407953 | +1/6, -5/6 | min_material_exposure_countries | **INCONCLUSIVE** |

Positive exposure and mortality changes both mean a decline. The slope is a percentage-point change in the mortality probability per one-unit exposure decline, adjusting for baseline exposure, baseline mortality, and WHO region.
The smoking series is modelled age-standardized prevalence for both sexes; PM2.5 uses the total-residence category. WHO NCD mortality is a modelled probability for dying between ages 30 and 70 from four major disease groups. WHO cautions that 2020–2021 estimates can undercount pandemic-related NCD deaths where vital registration is weak.
No policy effect, exposure causal effect, school claim, position score, or featured status follows from either result. The two tests share countries and the mortality series; archive-wide selection is unadjusted.

Definitions: [WHO tobacco prevalence](https://www.who.int/data/gho/data/themes/topics/sdg-target-3_a-tobacco-control), [WHO NCD mortality](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/probability-of-dying-between-exact-ages-30-and-70-from-any-of-cardiovascular-disease-cancer-diabetes-or-chronic-respiratory-%28-%29/), [WHO PM2.5](https://data.who.int/indicators/i/87345F3/F810947).

Exact replay: `python3 -B scripts/run_who_exposure_ncd_2026.py --verify`.
