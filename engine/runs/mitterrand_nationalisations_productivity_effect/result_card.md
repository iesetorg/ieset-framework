# Mitterrand nationalisations and French productivity

**Verdict:** refuted — French TFP was +2.19% ABOVE its 1975-80 pre-trend (net of European-peer controls) during the 1981-83 active-nationalisation window, not below it. The productivity-damage premise is not visible at the country level.

## Summary

Country-level event study of French TFP around the 1981-1983 nationalisations and the 1983 'tournant de la rigueur' reversal, benchmarked against European-peer controls (DEU, GBR, ITA, NLD, BEL, ESP). PWT 'rtfpna' (real TFP at constant national prices) is the primary outcome. Pre-trend window 1975-1980; treatment window 1981-1983; recovery window 1984-1990.

## Headline numbers

- FRA 1975-80 pre-trend slope (log-TFP per year): **+1.374%/yr** over n=6 pre-period years.
- FRA 1981-83 mean log-TFP gap vs its own pre-trend: **-0.668%**.
- European-peer mean 1981-83 gap (n=6 controls): **-2.863%**.
- **Net 1981-83 dip (FRA − controls): +2.195%** (threshold ≤ -1.50%; FAIL).
- FRA 1984-90 mean log-TFP gap vs its own pre-trend: **-1.541%**.
- European-peer mean 1984-90 gap: **-4.605%**.
- **Net 1984-90 gap (FRA − controls): +3.065%**.
- **Recovery delta (net 1984-90 − net 1981-83): +0.870pp** (threshold ≥ +0.75pp; PASS).

## Threshold table

| Component | Threshold | Realised | Pass |
|---|---:|---:|:---:|
| PRIMARY 1: net 1981-83 dip | ≤ -1.50% | +2.195% | no |
| PRIMARY 2: net recovery delta | ≥ +0.75pp | +0.870pp | YES |

## Per-country control results

| Country | n_pre | pre-slope (%/yr) | gap 1981-83 (%) | gap 1984-90 (%) |
|---|---:|---:|---:|---:|
| FRA (treated) | 6 | +1.374 | -0.668 | -1.541 |
| DEU (control) | 6 | +1.445 | -4.121 | -4.880 |
| GBR (control) | 6 | +0.972 | +0.232 | +1.585 |
| ITA (control) | 6 | +1.478 | -7.479 | -13.339 |
| NLD (control) | 6 | +1.155 | -3.866 | -5.065 |
| BEL (control) | 6 | +1.294 | -0.929 | -3.827 |
| ESP (control) | 6 | +1.610 | -1.013 | -2.105 |

## Informative WDI auxiliaries

- **log_real_gdp_pc** (world_bank_wdi:NY.GDP.PCAP.KD, log-units): FRA pre-window mean 21647.210; treatment-window 23563.225 (Δ vs pre +0.085); recovery-window 25760.137 (Δ vs pre +0.174).
- **gross_capital_formation_pct_gdp** (world_bank_wdi:NE.GDI.TOTL.ZS, level): FRA pre-window mean 25.701; treatment-window 23.351 (Δ vs pre -2.350); recovery-window 22.694 (Δ vs pre -3.006).
- **trade_openness** (world_bank_wdi:NE.TRD.GNFS.ZS, level): FRA pre-window mean 41.850; treatment-window 47.158 (Δ vs pre +5.308); recovery-window 45.233 (Δ vs pre +3.383).

## Method

For each country in {FRA} ∪ {DEU, GBR, ITA, NLD, BEL, ESP}: take log(rtfpna), fit OLS linear pre-trend over 1975-1980, project forward, compute mean (actual − projected) over the treatment (1981-83) and recovery (1984-90) windows. The PRIMARY estimand is the FRA gap minus the simple mean of available control gaps in the same window — i.e. how much FRA over- or under-performed its own pre-trend net of any generic European productivity slowdown. A 1.5%-of-TFP under-trend dip plus a half-closure recovery is required for SUPPORTED.

## Caveats

- **Country-level not firm-level.** The original spec requested a firm-level event study with firm + year FE comparing the 16 nationalised firms (Saint-Gobain, Thomson, Pechiney, Rhône-Poulenc, etc.) against industry-matched private comparators. No such firm-level French panel is in the repo. The country-level outcome blends nationalised-firm productivity with the rest of the French economy, attenuating the treatment effect. A SUPPORTED verdict here is consistent with — but weaker evidence than — the firm-level claim would give; a REFUTED verdict here is also weaker than firm-level would be.
- **Confounds.** 1981-1983 also saw the second oil-shock tail, three Franc devaluations, EMS exit-and-stay-in pressure, and a fiscal expansion. The control-net design absorbs Europe-common shocks but not FRA-specific simultaneous shocks. The 1983 tournant itself bundled disinflation + fiscal consolidation alongside the nationalisation reversal logic, so the recovery primary is also FRA-policy-bundle, not nationalisation-reversal-isolated.
- **Pre-trend length.** Only 6 pre-period years (1975-1980). The estimated pre-slope is therefore noisy; v2 should add a 1965-1980 specification as robustness if PWT coverage extends.
- **Disclosure (per spec).** Authorial bias risk: the classical-liberal framing wants nationalisation to damage productivity. The thresholds were pinned without seeing the result.

## Data

- pwt:rtfpna — `data/vintages/pwt/rtfpna@2026-04-27T090915Z.parquet`
- world_bank_wdi:NY.GDP.PCAP.KD — `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-27T090917Z.parquet`
- world_bank_wdi:NE.GDI.TOTL.ZS — `data/vintages/world_bank_wdi/NE.GDI.TOTL.ZS@2026-04-26T164521Z.parquet`
- world_bank_wdi:NE.TRD.GNFS.ZS — `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-04-27T093427Z.parquet`

## Steelman

See `hypotheses/steelman/mitterrand_nationalisations_productivity_effect.md`.
