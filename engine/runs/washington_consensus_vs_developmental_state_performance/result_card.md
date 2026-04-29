# Washington Consensus vs Developmental State performance

**Verdict:** SUPPORTED — KOR cumulative GDP-pc growth over its matched decade 1989-1999 (start level $8,878 ≈ ARG 1991 $8,730) was +0.614 log-points (+84.8%), vs ARG 1991-2001 +0.141 log-points (+15.1%). Gap = +0.473 log-points (+69.6pp), at/above the +0.30 log-point (~+35pp) SUPPORTED threshold.

## Summary

- ARG 1991-2001 (Menem-era convertibility & privatisation): real GDP-pc went $8,730 -> $10,052 (constant 2015 USD), cumulative +0.141 log-points (+15.1%).
- KOR matched decade 1989-1999 (starting GDP-pc closest to ARG 1991 level): $8,878 -> $16,403, cumulative +0.614 log-points (+84.8%).
- Cumulative log-growth gap KOR - ARG = **+0.473 log-points** (+69.6pp).
- SUPPORTED threshold: gap >= +0.30 log-points (~+35pp). Met.
- PPP robustness: not available (series missing required years).
- Supplementary KOR Park-era 1962-1972 (low-base, NOT level-matched): +0.743 log-points (+110.2%); KOR-ARG gap = +0.602.

## Method

Bilateral matched-decade comparison. ARG window is fixed to the Menem convertibility era 1991-2001 (the spec's treatment-tag window). The KOR "comparable decade" is chosen by matching on starting real GDP-pc level: KOR start year = the year minimising |KOR GDP-pc(year) - ARG GDP-pc(1991)|, using WDI NY.GDP.PCAP.KD (constant 2015 USD). The KOR window then spans [match_year, match_year+10] to mirror ARG's horizon. This is the descriptive approach the developmentalist claim invites: "compare like-for-like starting levels and see which growth model produced more cumulative real income."

Cumulative growth is reported in natural logs (additive, crisis-symmetric: a 50% boom and 50% bust net to roughly zero). PPP-based GDP-pc is computed in parallel as a robustness panel but does not gate the verdict (PPP coverage starts in 1990 so it cannot anchor a 1960s/70s KOR window).

### Steelman of the alternative reading

The market-liberal counter-frame would protest that the ARG 2001 collapse was driven by the convertibility regime's fixed peg (a Washington Consensus *deviation*: real liberal advice was a flexible exchange rate), not by privatisation per se. On that reading the comparison conflates two policies. This replication intentionally keeps the developmentalist framing as written in the spec: the matched-decade test is on the observed Argentine policy bundle as actually implemented, not on a counterfactual Washington Consensus.

## Data

- world_bank_wdi:NY.GDP.PCAP.KD (constant 2015 USD)
- world_bank_wdi:NY.GDP.PCAP.PP.KD (PPP, robustness only)
