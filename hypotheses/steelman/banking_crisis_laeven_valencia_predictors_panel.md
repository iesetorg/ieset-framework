# Steelman — Laeven-Valencia banking-crisis predictor panel

## The strongest opposing argument

Crisis-prediction logits are notoriously sensitive to the specific window, predictor lag, and crisis-coding choice. The Laeven-Valencia coding itself is contested at the margin (which year does Spain 2008 begin? was Italy 2011 a banking crisis or a sovereign-debt crisis?). A 0.75 rolling-origin AUC sounds disciplined but the literature has reported in-sample AUCs from 0.6 to 0.9 across nominally similar specifications, and the truly out-of-sample track record (forecasting crises that occurred after the model was published) is much weaker.

Berg-Pattillo's classical critique applies: most of the explanatory power comes from a few obvious cases (Asia 1997, GFC 2008) and the model offers little improvement over a "credit grew fast and current account is bad" rule of thumb that any informed observer would write down without a regression.

## What the framework still captures

A pre-registered AUC threshold of 0.75 on rolling-origin CV is a stiffer test than the in-sample AUCs in the source literature. If the four predictors plus country/year FE clear that bar out-of-sample on the 1980-2020 panel, that is meaningful confirmation that the standard early-warning bundle has real signal even after controlling for the unobserved country and year heterogeneity that simpler cross-sectional specifications confound with.
