# Result card — labor_share_decline_causes

**Verdict:** weakened — residual time-trend share exceeds 0.50 threshold

Pre-registered residual-share threshold: 0.50 (channels should absorb at least half of the within-country labour-share trend).

## Coefficient summary

| Spec | Term | Estimate | SE | n_obs |
|---|---|---:|---:|---:|
| baseline | time_trend | -0.1236 | 0.0741 | 340 |
| full | time_trend | +0.1697 | 0.0920 | 219 |

Residual share (|full / baseline|): **1.374**  (threshold 0.50)

Observed mean cross-country labour-share change over 2004–2020: -0.60 percentage points.

## Channels (full spec)

- log_industry_va: +3.5120 (4.4273), p=0.429
- trade_openness: -0.1077 (0.0167), p=0.000
- housing_va_share: -135.8578 (26.8980), p=0.000
- log_population: +11.1541 (16.1471), p=0.491
- log_gdp_pc_ppp: -27.9609 (6.2233), p=0.000

## Deviations from pre-registration

- OWID labor-share-of-gdp (SDG 10.4.1, 2004-2020) substitutes for the spec's OECD SDD ANA NAD 1980-2020 series; the analytic period truncates to 17 years.
- Capital-intensity channel uses WDI NV.IND.TOTL.KD log-level (industry value added) as a low-fidelity proxy because NE.GDI.FTOT.ZS is not in vintages.
- Import-penetration uses NE.TRD.GNFS.ZS (aggregate trade openness) instead of TM.VAL.MANF.ZS.UN.
- OECD PMR concentration channel dropped — only 2018 and 2023 cycle years available, panel-infeasible.
- WDI SL.EMP.SELF.ZS self-employment channel dropped — not in vintages.

Two of the four pre-registered channels (housing-VA share, trade openness as globalisation proxy) are present; the housing-stripped robustness sub-test cannot be run without the OECD ANA breakdown.

## Honest interpretation

This v1 run cannot test the spec's full multi-channel attribution. It tests a weaker proposition: whether a within-country time-trend in labour share shrinks once capital-deepening, trade-openness, and housing-VA share are conditioned on. A proper implementation requires wiring (a) OECD SDD ANA NAD labour share, (b) NE.GDI.FTOT.ZS or STAN capital stock, (c) TM.VAL.MANF.ZS.UN or a China-shock IV, (d) SL.EMP.SELF.ZS, and (e) historical OECD PMR cycles. The verdict should be read as a v1-data-gated indicator, not a definitive test.
