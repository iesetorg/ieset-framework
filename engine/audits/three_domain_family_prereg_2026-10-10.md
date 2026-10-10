# Three-domain forward calibration — frozen preregistration

This is a closed three-test family of distinct descriptive public questions: rule of law and later homicide, tractor stock and later food production, and self-employment share and later GDP per worker. Family-wide two-sided alpha is 0.01; all three remain in the Bonferroni denominator, so each p cutoff is 0.01/3. No failed case can be omitted or replaced after values. No policy, causal, school, position or featured credit is allowed.

The key-only roster `data/pinned_evidence/three_domain_family_key_roster.csv` contains 119, 100 and 215 valid-ISO3 country keys respectively (SHA-256 `8e1b06016aec18f323571785edbe91c228f931744c234e6822a6e2f52cbf62cc`). Only schemas, item/element/unit, country/year keys, source hashes, manifest metadata and the FAOSTAT flag legend were opened before this commit. No selected values, null/status masks, variation, sign or fit was opened. Rectangular WDI keys are not evidence of complete measurements.

## Pinned sources

| Role | Exact source | SHA-256 | Custody |
| --- | --- | --- | --- |
| law | `data/vintages/wgi/GOV_WGI_RL.EST@2026-05-05T195218Z.parquet` | `63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d` | data/manifests/fetch_run_2026-05-05T200056Z.yaml |
| homicide | `data/vintages/owid/intentional-homicides-per-100000-people@2026-04-30T114856Z.parquet` | `518ca94eb6aa1da5ae0900d984e6dc7f567ebbc21486666b2e37a1843d704694` | data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml |
| tractor | `data/vintages/faostat/faostat_machinery_main@2026-05-02T212848Z.parquet` | `81aac0eff6e8aee780fd667637333872a2cff088d61d23ef2d0db0e4e20219c6` | FAOSTAT archive/derived parquet; no tracked fetch-manifest entry |
| tractor_archive | `data/vintages/faostat/machinery@2026-05-02T212848Z.zip` | `3bf291ea8996f3b664bf176cd2926ec3a53b50b94ac75c5d6bcf74f6d2ddb009` | FAOSTAT archive/derived parquet; no tracked fetch-manifest entry |
| food | `data/vintages/world_bank_wdi/AG.PRD.FOOD.XD@2026-05-05T203847Z.parquet` | `05863480f2da10e8d59cb591a008fb54ad23e7b35d1818d1682fd7a673536876` | data/manifests/fetch_run_2026-05-05T210519Z.yaml |
| self_employment | `data/vintages/world_bank_wdi/SL.EMP.SELF.ZS@2026-04-30T115122Z.parquet` | `67abd9aef0cc6ba29de9fc1bea7bbbf6686a310a49fc7b38f782211a22dd330c` | data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml |
| productivity | `data/vintages/world_bank_wdi/SL.GDP.PCAP.EM.KD@2026-04-30T141045Z.parquet` | `a4b4194f221b89c5f08ed6c11eb691c66ddb572798948af55c0f9d4b5b284742` | data/manifests/fetch_run_2026-04-30T141104Z.yaml |

The FAOSTAT tractor series is exact item `Agricultural tractors`, element `In Use`, unit `No`, at 1990 and 2000, with flags A (official), E (estimated) and X (international organization) admitted and individually reported. Blank/other flags are excluded. The matching FAOSTAT source archive is pinned, but the derived parquet lacks a tracked fetch-manifest entry; this limits provenance claims. WDI observations require blank/A status. No interpolation, endpoint switch, proxy substitution or imputation is permitted.

## Frozen transformations and gates

### Rule of law and later homicide

Claim: Larger 2000-to-2010 rule-of-law gains predict greater 2010-to-2020 homicide-rate reductions across the frozen country roster. Source-key roster 119; exposure 2000→2010: WGI rule-of-law estimate in 2010 minus 2000; outcome 2010→2020: log(homicide rate in 2010) minus log(rate in 2020). Positive slope means later improvement. Baseline exposure and baseline outcome enter as controls with an intercept. Minimum complete countries 90; at least 20 have exposure gain ≥0.15; p90−p10 exposure-gain spread ≥0.3. Residualized exposure squared-share concentration: top country ≤0.15, top 10 ≤0.6. Each of five deterministic hash-fold omissions requires ≥70 countries and a full-rank, finite, positive-uncertainty fit. Meaningful absolute slope ≥0.2 log homicide-rate reduction per +1 WGI rule-of-law point. WGI rule of law is a perception-based composite that may itself incorporate crime and enforcement. Homicide reporting and social conditions also vary.

### Tractor stock and later food production

Claim: Larger 1990-to-2000 increases in agricultural tractors in use predict greater 2000-to-2010 growth in the food-production index across the frozen country roster. Source-key roster 100; exposure 1990→2000: log(1+tractors in use in 2000) minus log(1+tractors in use in 1990); outcome 2000→2010: log(food-production index in 2010) minus log(index in 2000). Positive slope means later improvement. Baseline exposure and baseline outcome enter as controls with an intercept. Minimum complete countries 70; at least 15 have exposure gain ≥0.1; p90−p10 exposure-gain spread ≥0.25. Residualized exposure squared-share concentration: top country ≤0.2, top 5 ≤0.65. Each of five deterministic hash-fold omissions requires ≥55 countries and a full-rank, finite, positive-uncertainty fit. Meaningful absolute slope ≥0.05 log food-production-index growth per +1 log(1+tractors) point. Tractor stock is unscaled by cultivated area and may reflect country size, farm consolidation, or record changes. Rainfall, input use, land and trade can move food output.

### Self-employment share and later worker productivity

Claim: Larger 2000-to-2010 declines in the self-employment share predict greater 2010-to-2020 growth in GDP per person employed across the frozen country roster. Source-key roster 215; exposure 2000→2010: self-employed share in 2000 minus 2010 percentage points; outcome 2010→2020: log(GDP per employed person in 2020) minus log(level in 2010). Positive slope means later improvement. Baseline exposure and baseline outcome enter as controls with an intercept. Minimum complete countries 150; at least 35 have exposure gain ≥3.0; p90−p10 exposure-gain spread ≥8.0. Residualized exposure squared-share concentration: top country ≤0.12, top 10 ≤0.5. Each of five deterministic hash-fold omissions requires ≥120 countries and a full-rank, finite, positive-uncertainty fit. Meaningful absolute slope ≥0.005 log GDP-per-worker growth per 1 percentage-point self-employment decline. The modeled self-employment share includes employers and own-account work and does not measure formal employment. Sector mix, capital deepening and GDP accounting can drive both series.

All countries are equally weighted. The fixed fold is `int(SHA256(ISO3)[0:8],16) % 5`. Full and fold fits use OLS of later outcome improvement on exposure gain plus the two baselines, HC3 robust uncertainty, and two-sided Student t. Full rank, finite positive standard error and positive residualized-exposure variation are required. Failed gates produce INCONCLUSIVE. With all gates clear, SUPPORTED requires a positive slope ≥ the meaningful bound, p≤0.01/3 and ≥4/5 positive fold signs; REFUTED requires the symmetric negative result. Other valid estimates are PARTIAL. The three-test correction does not repair archive-wide selection.

Admissible ranges: WGI [-3,3], homicide rate (0,300] per 100,000, tractors in use [0,10,000,000], food-production index (0,1000], self-employment share [0,100] percent, and GDP per employed person (0,1,000,000] constant PPP dollars. An endpoint outside the range is excluded, not winsorized.

Distinctness check: existing Bukele security cases concern specific 2019–2024 policies, existing government-effectiveness cases concern development outcomes, existing food-production cases concern trade/property rights rather than tractor stock, and existing labour cases do not test self-employment-share change against later GDP per worker. Earlier related tests remain visible; this wave cannot be counted as a policy effect or broad corpus graduation.
