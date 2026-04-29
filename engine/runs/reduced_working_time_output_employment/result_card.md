# Reduced working-time experiments — output and employment effects

**Verdict:** SUPPORTED — both treated cases satisfy the no-catastrophe primary (log-GDP gap >= -5% AND unemployment gap <= +3.0 pp). FRA: log-GDP gap +3.93 pp, unemployment gap -5.48 pp; ISL: log-GDP gap +13.05 pp, unemployment gap -4.88 pp.

## Summary

Two treated cases tested with per-country interrupted time series:

### FRA — France 35-hour week (event year 2000)

- Bucket: **ok_no_catastrophe**
- PRIMARY log real GDP: mean post-gap = +3.93 pp (log) / +0.03927 (log pp); n_pre=10, n_post=8, pre-window=[1990, 1999], post-window=[2000, 2007].
- PRIMARY unemployment rate: mean post-gap = -548.40 pp (log) / -5.484 (units); n_pre=9, n_post=8, pre-window=[1990, 1999], post-window=[2000, 2007].
- INFORMATIVE PWT avg hours worked: mean post-gap = -1527.10 pp (log) / -15.27 (units); n_pre=10, n_post=8, pre-window=[1990, 1999], post-window=[2000, 2007].
- INFORMATIVE PWT TFP (rtfpna): mean post-gap = +0.99 pp (log) / +0.00992 (units); n_pre=10, n_post=8, pre-window=[1990, 1999], post-window=[2000, 2007].

### ISL — Iceland 4-day-week trial (event year 2015)

- Bucket: **ok_no_catastrophe**
- PRIMARY log real GDP: mean post-gap = +13.05 pp (log) / +0.1305 (log pp); n_pre=10, n_post=5, pre-window=[2005, 2014], post-window=[2015, 2019].
- PRIMARY unemployment rate: mean post-gap = -487.97 pp (log) / -4.88 (units); n_pre=10, n_post=5, pre-window=[2005, 2014], post-window=[2015, 2019].
- INFORMATIVE PWT avg hours worked: mean post-gap = +5600.11 pp (log) / +56 (units); n_pre=10, n_post=5, pre-window=[2005, 2014], post-window=[2015, 2019].
- INFORMATIVE PWT TFP (rtfpna): mean post-gap = +6.07 pp (log) / +0.06073 (units); n_pre=10, n_post=5, pre-window=[2005, 2014], post-window=[2015, 2019].

## Method

Per-country interrupted time series. For each treated case (France 2000, Iceland 2015):

1. Fit a linear pre-trend on the outcome over the pre-window.
2. Project forward into the post-window.
3. Compute mean post-period gap = mean(actual minus counterfactual).

**SUPPORTED** if BOTH cases satisfy: log-GDP gap >= -5% AND unemployment gap <= +3.0 pp.
**REFUTED** if EITHER case shows: log-GDP gap < -10% OR unemployment gap > +5.0 pp.
**PARTIAL** otherwise; **inconclusive** if a case lacks >=4 pre and >=3 post observations.

Pre/post windows are truncated to avoid global-shock contamination (FRA post = 2000-2007 pre-GFC; ISL post = 2015-2019 pre-COVID).

## Caveats

- A linear pre-trend extrapolation discards within-window dynamics (business-cycle, oil shocks). Confidence is low when the pre-window residual SD is large relative to the measured post-gap.
- 'Catastrophic' is defined ex-ante at -10% log-GDP / -5pp employment as the REFUTED bar; the SUPPORTED bar (-5% / -3pp) is intentionally tight given that the original claim emphasises 'catastrophic'.
- Iceland's 4-day-week trial covered ~1.3% of the workforce at peak and was voluntary; absence of macro effect is mechanically expected. See `hypotheses/steelman/reduced_working_time_output_employment.md`.

## Data

- world_bank_wdi:NY.GDP.MKTP.KD
- world_bank_wdi:SL.UEM.TOTL.ZS (unemployment rate, % total labour force, ILO-modelled)
- pwt:avh (avg hours worked — informative)
- pwt:rtfpna (TFP — informative)
