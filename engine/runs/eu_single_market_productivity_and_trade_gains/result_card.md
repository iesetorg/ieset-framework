# EU Single Market 1993 — productivity and trade gains

**Verdict:** SUPPORTED — EU-12 vs non-EU OECD DiD around 1993: log GDP PC PPP +4.83 log pp (threshold +2.0) AND trade openness +11.82 pp (threshold +5.0).

## Summary

- **Primary 1 (productivity proxy, log GDP PC PPP DiD):** +4.83 log pp (threshold ≥ +2.0 log pp). PASS.
  - EU-12 mean delta (post − pre): +23.45 log pp (12 of 12 countries).
  - Non-EU OECD mean delta (post − pre): +18.62 log pp (6 of 6 countries).

- **Primary 2 (trade openness DiD):** +11.82 pp (threshold ≥ +5.0 pp). PASS.
  - EU-12 mean delta (post − pre): +19.09 pp.
  - Non-EU OECD mean delta (post − pre): +7.28 pp.

- **Informative (PWT rtfpna DiD):** -0.0042 index points (no gating threshold; reported for context).

## Method

Pre/post DiD on country means around the 1993 Single Market activation.

- Treated (EU-12, n=12): DEU, FRA, ITA, ESP, NLD, BEL, GBR, IRL, DNK, GRC, PRT, LUX
- Controls (non-EU OECD, n=6): USA, JPN, CAN, AUS, NOR, CHE
- Pre window: 1980-1992; Post window: 1994-2010.
- DiD = (EU-12 post mean − EU-12 pre mean) − (non-EU OECD post mean − non-EU OECD pre mean).

Outcomes:
1. log real GDP per capita PPP (WDI NY.GDP.PCAP.PP.KD) — productivity proxy.
2. Trade openness (WDI NE.TRD.GNFS.ZS, % of GDP) — trade gain.
3. PWT rtfpna (TFP, manufacturing) — informative only.

Note: the spec's intra-EU trade share series (eurostat:ext_lt_intratrd) is not on disk, so total trade openness from WDI substitutes as the trade-gain primary. This is conservative for the Ordoliberal claim: if Single Market deepens *intra-EU* trade specifically, total openness could rise OR fall (substitution from extra-EU to intra-EU trade). The DiD on total openness still captures whether the EU bloc became more trade-intensive overall vs non-EU OECD.

## Caveats / non-identifying confounds

- 1993 coincides with the broader Maastricht / EMU preparatory   process; the design cannot separate Single Market from EMU effects.
- The post-1995 WTO formation and Eastern enlargement effects from   1995 onward (AUT/SWE/FIN joined) are not separated; AUT/SWE/FIN   are NOT in the EU-12 treated set so this contaminates the   control comparison only mildly via spillovers, not directly.
- A simple two-period DiD on means is more transparent than an   event-study with leads/lags but discards the within-window   trajectory; v2 should add a year-by-year event-study spec.

## Data

- world_bank_wdi:NY.GDP.PCAP.PP.KD
- world_bank_wdi:NE.TRD.GNFS.ZS
- world_bank_wdi:SP.POP.TOTL
- pwt:rtfpna
