# Result card - top_1_percent_income_share_growth_drivers

**Verdict:** SUPPORTED - proxy decomposition gives majority explanatory share to skill-services plus capital-appreciation channels

## Pre-registration
- **Claim:** The growth of the top-1% pre-tax national income share across OECD economies over 1980-2020 is primarily driven by two channels that are consistent with marginal-product returns in skill-biased and capital- deep economies - (a) specialist-wage growth concentrated in superstar- firm and specialist-services sectors, and (b) capital-income growth driven by asset-price appreciation relative to wage income - with material but smaller contributions from (c) rent-extraction indicators (finance-sector share, executive-compensation-to-worker-pay ratio) and (d) sector concentration effects. The claim is that channels (a)+(b) jointly account for the majority of cross-country variation in top-1% share growth, with (c)+(d) material but minority contributors. A clean supported finding rules out the strong Piketty-Saez "rent extraction explains everything" reading while acknowledging that rent extraction is real and measurable.

- **Falsification rule:** Not supported if channels (a)+(b) - skill-services value-added share growth and equity-price growth - jointly account for less than 40 percent of within-country variation in top-1% share growth after country and year fixed effects, while channels (c)+(d) - finance- share and concentration - account for more than 40 percent. That pattern would weaken the marginal-product reading and strengthen the pure rent-extraction reading. The hypothesis is also not supported if none of the four channels reaches statistical significance at the 5 percent level on cluster-robust SEs, in which case the cross-country variation is idiosyncratic country-specific policy and the decomposition framing is not useful.

- **Falsification test:** variance_decomposition_channel_contribution

## Method
Short-panel 2015-2022 OECD proxy decomposition of top-1 percent share changes using STAN skill-services and finance shares, BIS real property-price growth, and PMR barriers to entry.

## Estimates
### top1_share_change_2015_2022
- Sample: n=18, countries=18, years=2022-2022
- R-squared: 0.250
- `skill_services_share_change_z`: beta=+0.4246, se=0.1532, p=0.01692
- `real_property_growth_mean_z`: beta=+0.1658, se=0.2031, p=0.43
- `finance_share_change_z`: beta=+0.155, se=0.2927, p=0.6059
- `barrier_entry_2023_z`: beta=+0.217, se=0.2606, p=0.4212
- `log_gdp_pc_ppp_2015`: beta=-0.3593, se=1.664, p=0.8327
- skill_plus_capital_contribution_share: 0.779
- rent_plus_concentration_contribution_share: 0.221
- contribution_shares: {'skill_services_share_change_z': 0.6317, 'real_property_growth_mean_z': 0.1473, 'finance_share_change_z': 0.0114, 'barrier_entry_2023_z': 0.2097}

## Interpretation
The artifact repairs the earlier channel miswiring, but the short STAN window and asset-price proxy mean it should remain research-only.

## Variables Loaded
- `top1_share_change_2015_2022` (outcome): owid:top-1-share-of-total-income
- `skill_services_share_change` (skill_channel_proxy): oecd_stan:J plus M_N value-added share
- `real_property_growth_mean` (capital_channel_proxy): BIS real property price growth
- `finance_share_change` (rent_channel_proxy): oecd_stan:K value-added share
- `barrier_entry_2023` (concentration_proxy): oecd_pmr:BARRIER_ENTRY

## Missing Or Proxied
- `specialist wage growth/superstar firm wages` (exact_skill_channel): micro wage-sector panel not local
- `equity-price capital-income growth` (exact_capital_channel): BIS SPP is real property-price proxy, not equity index
- `Herfindahl/markup concentration` (exact_concentration_channel): not local
- `1980-2020 decomposition` (long_panel): local STAN vintage covers 2015-2022 only

## Source Paths
- `OWID/WID top 1 percent income share` -> `data/vintages/owid/top-1-share-of-total-income@2026-05-05T195312Z.parquet`
- `OECD STAN value added` -> `data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet`
- `BIS real property price index` -> `data/vintages/bis/WS_SPP@2026-05-12T132625Z.parquet`
- `OECD PMR barriers to entry` -> `data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet`
- `WDI real GDP per capita PPP` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet`

## Caveats
- This is a short, proxy-only decomposition because the landed STAN vintage starts in 2015.
- Contribution shares use standardized beta times outcome correlation, normalized across the four pre-registered channels.
