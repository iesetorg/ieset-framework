# Result card — maduro_era_venezuelan_collapse_decomposition_2013_2023

**Verdict:** weakened — residual share 47.268 > threshold 0.50; channels do not jointly absorb the gap

Pre-registered residual-share threshold: 0.50.

## Coefficient summary

| Spec | Term | Estimate | SE | n_obs |
|---|---|---:|---:|---:|
| baseline | ven_post_2013 | +0.0218 | 0.0918 | 128 |
| full | ven_post_2013 | +1.0320 | 0.2220 | 128 |

Residual share: **47.268** (threshold 0.50)

VEN cumulative log-GDP-pc-PPP change from 2013 to 2018: -0.694  (≈-50.0%).

## Channels (full spec)

- oil_shock_exposure: -0.1479 (0.0603), p=0.016
- monetary_fusion: -1.1384 (0.1256), p=0.000
- political_destab: +0.2013 (0.1686), p=0.235
- wgi_rl: +0.2022 (0.1813), p=0.267

## Deviations from pre-registration

- Oil-shock, monetary-fusion, sanctions, and political-destabilisation
  channels are reduced-form stepwise indicators in the absence of
  vintage-stored constructed series.
- Donor-pool synthetic-control + Shapley channel-attribution sub-specs
  are deferred.
- Per-channel variance-share decomposition (the spec's formal test) is
  not run; verdict relies on the residual-share statistic.
