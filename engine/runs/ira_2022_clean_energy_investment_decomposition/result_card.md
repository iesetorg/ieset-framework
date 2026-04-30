# Result card — ira_2022_clean_energy_investment_decomposition

**Verdict:** INCONCLUSIVE_DATA_PENDING — outcome 'log_us_cumulative_clean_energy_tax_credit_outlay_usd' not loaded; missing: ['constructed: US Treasury / OMB outlay tabulations cross-checked against CBO 2022/2023/2024 reestimates. fred:FYONET (deficit baseline) + Treasury Green Book line items. Manual-drop pending.', 'irena:capacity', 'constructed: BEA NIPA private fixed investment in clean-energy manufacturing + DOE LPO loan-guarantee tracker + BloombergNEF announced-capex tracker. Manual-drop under data/manual/derived/. Cross-checks: fred:PNFI (private nonresidential fixed investment) and fred:IPN331S (manufacturing IP).', 'bls:CES1021100001', 'constructed: BloombergNEF / IEA Energy Technology Perspectives — share of global clean-energy manufacturing capex by location (USA, EU, CHN). Manual-drop under data/manual/iea/.']

## Pre-registration
- **Claim:** The Inflation Reduction Act (IRA, signed August 2022) produced a measurable step-change in US clean-energy investment, manufacturing reshoring, and fiscal cost over 2022-2026 relative to a pre-IRA trajectory and to non-US comparators (EU, China, Japan, Korea). Specifically, cumulative tax-credit outlays exceeded the original CBO estimate of ~$369bn (10-year), utility- scale clean-energy MW deployed accelerated above the 2018-2021 trend, announced battery + EV + solar manufacturing capex relocated to the US at a rate that materially raised the US share of new global clean-energy manufacturing investment, and clean-energy-related job postings rose. The decomposition tests which of these channels (deployment, manufacturing, jobs, fiscal cost) materialised at the magnitudes claimed by Treasury and by the IRA's defenders, and which fell short.
- **Falsification rule:** Not supported if (a) the USA × post-2022 effect on clean-energy MW added is within the 95% CI of the pre-IRA trend extrapolation (no deployment acceleration), OR (b) US share of global clean-manufacturing capex does not rise above its 2018-2021 mean by at least 5 percentage points by end-2025, OR (c) clean-energy employment is flat or declines relative to total manufacturing employment, OR (d) total tax-credit outlays fall below the original CBO 10-year estimate (suggesting take-up failure). If only the fiscal-cost channel materialises (deficit rises) without deployment / capex / jobs response, classify as "fiscal cost without industrial response."
- **Falsification test:** ira_decomposition_panel

## Estimate
- _Error:_ outcome 'log_us_cumulative_clean_energy_tax_credit_outlay_usd' not loaded; missing: ['constructed: US Treasury / OMB outlay tabulations cross-checked against CBO 2022/2023/2024 reestimates. fred:FYONET (deficit baseline) + Treasury Green Book line items. Manual-drop pending.', 'irena:capacity', 'constructed: BEA NIPA private fixed investment in clean-energy manufacturing + DOE LPO loan-guarantee tracker + BloombergNEF announced-capex tracker. Manual-drop under data/manual/derived/. Cross-checks: fred:PNFI (private nonresidential fixed investment) and fred:IPN331S (manufacturing IP).', 'bls:CES1021100001', 'constructed: BloombergNEF / IEA Energy Technology Perspectives — share of global clean-energy manufacturing capex by location (USA, EU, CHN). Manual-drop under data/manual/iea/.']

## Variables resolved
- `fred:GFDEGDQ188S` → us_federal_deficit_share_gdp (outcome, publisher=fred, n=60)
- `world_bank_wdi:NY.GDP.MKTP.KD` → log_real_gdp (controls, publisher=world_bank_wdi, n=14131)

### Variables missing data
- `constructed: US Treasury / OMB outlay tabulations cross-checked against CBO 2022/2023/2024 reestimates. fred:FYONET (deficit baseline) + Treasury Green Book line items. Manual-drop pending.` (outcome, name=log_us_cumulative_clean_energy_tax_credit_outlay_usd) — vintage not on disk
- `irena:capacity` (outcome, name=us_utility_scale_clean_energy_mw_added) — vintage not on disk
- `constructed: BEA NIPA private fixed investment in clean-energy manufacturing + DOE LPO loan-guarantee tracker + BloombergNEF announced-capex tracker. Manual-drop under data/manual/derived/. Cross-checks: fred:PNFI (private nonresidential fixed investment) and fred:IPN331S (manufacturing IP).` (outcome, name=log_us_clean_manufacturing_announced_capex_usd) — vintage not on disk
- `bls:CES1021100001` (outcome, name=us_clean_energy_employment) — vintage not on disk
- `constructed: BloombergNEF / IEA Energy Technology Perspectives — share of global clean-energy manufacturing capex by location (USA, EU, CHN). Manual-drop under data/manual/iea/.` (outcome, name=comparator_clean_manufacturing_capex_share_global) — vintage not on disk
- `constructed: indicator = 1 for USA from 2022-08 (IRA enactment) onwards; 0 otherwise.` (treatment, name=us_post_ira_dummy) — vintage not on disk
- `constructed: interaction of post-IRA dummy with subsector eligibility (battery / EV / solar / wind eligible = 1; non-eligible manufacturing = 0). Identifies whether eligible subsectors accelerate relative to non-eligible.` (treatment, name=us_post_ira_eligible_subsector_interaction) — vintage not on disk
- `fred:DFII10` (controls, name=real_interest_rate) — vintage not on disk
- `imf_pcps:POILBRE` (controls, name=brent_oil_log) — vintage not on disk
- `constructed: same BloombergNEF / IEA tracker, China share. Used to control for global clean-energy capex cycle independent of IRA.` (controls, name=china_clean_manufacturing_capex_share) — vintage not on disk

_Generated by `scripts/run_panel_fe.py` at 2026-04-30T08:43:10+00:00_