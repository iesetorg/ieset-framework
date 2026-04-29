# Universal transfer programmes → labour-force participation decline

**Verdict:** partial — Prime-age LFP fell by ≥1.0pp in 2/5 cases (threshold for SUPPORTED: ≥3). First-order improved in 3/4 cases. Mixed: consistent with the spec's design-dependence caveat — some programmes show the chain, others do not.

## Summary

- Cases tested: 5 (ARG, ESP, GBR, VEN, USA)
- Cases with usable prime-age LFP pre/post data: 5/5
- Cases showing LFP decline ≥1.0pp post-rollout: **2/5** (need ≥3 for SUPPORTED)
- Cases with first-order welfare gain (Gini or extreme-poverty drop): 3/4

### Case-by-case

- **ARG** (Planes Trabajar / Argentina Trabaja / Potenciar Trabajo, rollout 2003): prime-age LFP Δ = +0.48pp; first-order Δ = -4.92 (gini_index).
- **ESP** (Ingreso Mínimo Vital, rollout 2020): prime-age LFP Δ = -0.31pp; first-order Δ = -1.64 (gini_index).
- **GBR** (Universal Credit rollout (post tax-credit consolidation), rollout 2013): prime-age LFP Δ = +0.65pp; first-order Δ = -0.94 (gini_index).
- **VEN** (CLAP food box, rollout 2016): prime-age LFP Δ = -10.15pp; first-order Δ = no data.
- **USA** (Expanded Child Tax Credit (2021 ARPA), rollout 2021): prime-age LFP Δ = -1.10pp; first-order Δ = +0.17 (gini_index).

## Method

For each of the five programmes the script computes:
1. The 5y-mean prime-age (ILO age-band 25+) labour-force    participation rate, both sexes, in the 5y window before rollout.
2. The 5y-mean prime-age LFP in the 5y window after rollout    (excluding pandemic years 2020-2021 for ESP and USA).
3. The post-minus-pre delta in pp.
4. The Gini index pre-vs-post delta (or, when Gini lacks coverage,    extreme-poverty $2.15/day).

Verdict rule:
- SUPPORTED if ≥3/5 cases show LFP decline   ≥1.0pp AND ≥3/5   cases show first-order welfare gain.
- REFUTED if ≥4/5 cases show LFP rise (chain fails).
- PARTIAL if 2/5 cases show LFP decline (mixed; design-dependent).
- INCONCLUSIVE if <3/5 cases have data covering both windows.

## Data

- ilostat:EAP_2WAP_SEX_AGE_RT_A (LFP rate; sex=T, age 25+ classif1)
- world_bank_wdi:SI.POV.GINI (Gini index)
- world_bank_wdi:SI.POV.DDAY ($2.15/day extreme-poverty headcount)

## Caveats

- The spec's preferred outcomes (bottom-decile LFP, hours-worked,   effective marginal tax rate, programme-spend-as-pct-GDP,   long-tenure recipient subsequent-employment probability) require   household-microdata or OECD Benefits-and-Wages files not in   vintages. National aggregate LFP is a conservative proxy; if   bottom-decile LFP fell sharply but the upper deciles rose, the   national aggregate would mask the chain's appearance.
- 5y pre/post-mean comparison rather than Callaway-Sant'Anna DiD   because the panel donor pool the C-S template requires is not   constructible from these annual aggregates alone.
- VEN data after 2014 is sparse in WDI/ILO due to the country's   statistical disclosure interruption.
