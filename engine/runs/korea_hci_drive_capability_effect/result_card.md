# Korea HCI drive capability effect (1961-1985 vs LATAM ISI)

**Verdict:** SUPPORTED — KOR-vs-LATAM cum-log gap by 1985: real exports +3.19 (>+1.00), industry VA +1.99 (>+1.00); DiD on PWT rgdpna around 1973: +0.32 (>+0.20). Pre-trend (industry VA pre-1973 gap): +0.88.

## Summary

- **PRIMARY-LEVELS (capability divergence by 1985):**
  - Real exports (WDI NE.EXP.GNFS.KD): KOR cum log-change `+4.811` vs LATAM mean `+1.617` → KOR-LATAM gap **`+3.193`** (threshold `> +1.00`, PASS).
  - Industry value added (WDI NV.IND.TOTL.KD, base 1965): KOR `+2.769` vs LATAM mean `+0.782` → gap **`+1.986`** (threshold `> +1.00`, PASS).
- **PRIMARY-DiD (HCI causal channel around 1973):**
  - PWT rgdpna: KOR DiD `+0.019` − LATAM DiD `-0.300` = **`+0.319`** (threshold `> +0.20`, PASS).
- **INFORMATIVE secondary:**
  - Industry-VA pre-trend (1965-1973 gap): `+0.877` (clean).
  - Real-exports DiD around 1973: `-1.941` (informative-only — see methodology note; pre-1973 export miracle means HCI-DiD on exports may not signal HCI's capability effect).
  - PWT rtfpna cum 1961-1985 KOR-LATAM: `+0.488`.
  - Maddison gdppc_ppp cum 1961-1985 KOR-LATAM: `+1.296`.
- **METHOD_VALID:** True (donor full-coverage counts: {'real_exports': 6, 'industry_va': 6, 'pwt_rgdpna': 6, 'pwt_rtfpna': 6, 'maddison_gdppc': 6}).

## Method

Spec calls for synth-DID with KOR treated 1973 and LATAM ISI donor
pool {BRA, ARG, MEX, COL, CHL, PER}. The dispositive outcomes asked
for in the original spec — heavy-industry export share + Hidalgo-
Hausmann ECI — are not on disk. v1 substitutes WDI real exports +
WDI industry value added + PWT real GDP / TFP as proxy outcomes,
with the synth-DID convex weights collapsed to an equal-weighted
LATAM mean (donor pool is small enough that this is informative).

Two PRIMARY tests:

1. **Levels-divergence by 1985** on real exports + industry VA. KOR's
   1961→1985 log change minus the LATAM-donor mean of the same.
   Threshold: > +1.00 log points (~e^1 ≈ 2.7x more growth) on each.
   Both must clear for SUPPORTED.
2. **DiD around 1973** on PWT rgdpna. (post-1973 KOR log-growth −
   pre-1973 KOR log-growth) − the same for LATAM mean. Threshold:
   > +0.20 log points.

Industry-VA baseline is 1965 (not 1961) because WDI NV.IND.TOTL.KD
coverage starts 1965 for ARG/MEX/COL.

## Data

- world_bank_wdi:NE.EXP.GNFS.KD
- world_bank_wdi:NV.IND.TOTL.KD
- pwt:rgdpna
- pwt:rtfpna
- maddison:gdppc_ppp

## Steelman

See `hypotheses/steelman/korea_hci_drive_capability_effect.md` for
the live concerns about this hypothesis (US security umbrella, the
1964 export-promotion turn pre-dating HCI, alternative reads of the
LATAM ISI counterfactual).
