# Result card — UK economic decline multi-movement

**Verdict:** partial — post-brexit β=-0.012 p=0.204

## Primary spec (TWFE with donor dummies + time FE)

| Term | Estimate | SE | 95% CI | p | t | Expected | Pass? |
|---|---:|---:|:---:|---:|---:|:---:|:---:|
| uk_post_2008 | -0.0344 | 0.0076 | [-0.049, -0.019] | 0.000 | -4.54 | − | ✓ |
| uk_post_brexit | -0.0116 | 0.0091 | [-0.030, +0.006] | 0.204 | -1.27 | − | ✗ |

n = 224 country-years. Donor pool: USA, CAN, AUS, NZL, DEU, NLD, CHE.

## Synthetic control gap analysis

Donor weights (sum=1): {'USA': 0.0, 'CAN': 0.22208608724374368, 'AUS': 0.2633004259008625, 'NZL': 0.39566800656819895, 'DEU': 2.254759813669794e-17, 'NLD': 0.11894548028719482, 'CHE': 2.1158630023824165e-17}
Pre-treatment fit RMSE (1996-2007): 0.0081 log-points
Post-2008 avg gap (UK actual − synthetic): -0.051 log-points
Post-2016 avg gap: -0.058 log-points
Post-2016 fraction of years UK below synthetic: 100%

## Interpretation

Partial result. The divergence signal is present post-2008 and present incrementally post-2016. Magnitudes and significance vary; see coefficient table. SC post-2016 gap negative in 100% of years. Per steelman, the UK comparison is sensitive to donor-pool choice — NLD/CHE/NOR have unique features that make UK look worse by comparison. A v2 sensitivity with FRA/ITA/JPN/KOR donor pool would tell a different story.

## Steelman-live concerns

1. Donor pool (NLD, CHE) may be cherry-picked small-high-institutional economies
2. 2008 treatment date captures global GFC + UK-specific response; disentangling requires further work
3. Post-2016 window dominated by Brexit + COVID + energy crisis; confound
4. UK has cumulative multi-movement decline (planning + energy + Brexit + Brown + austerity); single-coefficient aggregation underspecifies the causal story
5. PPP GDP per capita understates sterling-depreciation-driven nominal-USD decline but arguably overcounts real-decline

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
