# Steelman — EU Single Market 1993 productivity and trade gains

**The strongest argument against this hypothesis:**

The post-1993 trajectory of EU-12 economies is not a clean test of the
Single Market because it overlaps with three other large institutional
shocks the design cannot separate:

1. **Maastricht / EMU preparation (1992-1999) and euro launch (1999-2002).**
   The 1993 Single Market activation date sits inside the Maastricht
   convergence process. Periphery countries (ESP, ITA, IRL, PRT, GRC)
   pursued large fiscal consolidations and disinflations to meet the
   convergence criteria; the lower interest-rate environment they
   converged into produced a credit-and-housing boom that flattered
   GDP growth 1995-2007. Attributing the productivity-proxy DiD
   ("EU-12 closed the gap to non-EU OECD") to the Single Market
   over-credits the rules-based-integration channel relative to the
   monetary-convergence channel. The headline +4.8 log-point DiD on
   log GDP per capita PPP is consistent with both stories.

2. **Eastern enlargement preparation and the 2004 accession.** The
   EU-15 (which is close to EU-12 plus AUT/SWE/FIN) opened its
   internal market progressively to the Visegrad-4 from the late
   1990s through 2004 accession. EU-12 manufacturing supply chains
   were restructured toward CEE production locations; this raised
   measured trade openness in EU-12 (the trade-openness DiD primary
   would inflate) but the productivity story is more ambiguous —
   relocation of low-productivity stages of production raises
   measured TFP in the home country mechanically. The +11.8pp
   trade-openness DiD does not distinguish "Single Market deepens
   intra-EU trade" from "EU enlargement opens new low-cost
   sourcing." Both are real; only the first is what the hypothesis
   is testing.

3. **Ireland's tax-base distortion.** Ireland accounts for the
   largest country-level deltas in the panel (log GDP per capita
   PPP delta +55%, trade openness delta +52pp). Ireland's
   measured GDP from the late 1990s onward is severely distorted by
   multinational-tax-base relocation; the 2015 "leprechaun economics"
   GDP revision (+26% in one year) makes clear that Irish GDP is not
   measuring real Irish output. The Single Market is only one of
   several channels enabling Irish corporate-tax-driven inversions.
   Excluding Ireland would meaningfully reduce both DiDs; the result
   card should report robustness to Ireland exclusion.

**Specific objections the hypothesis must engage with:**

1. **Trade-openness DiD over-counts intra-EU re-routing.** A genuine
   Single Market effect would show up in *intra-EU* trade share
   (eurostat:ext_lt_intratrd, the spec's preferred series, not on
   disk). Total trade openness (NE.TRD.GNFS.ZS) confounds intra-EU
   and extra-EU dynamics. The hypothesis as currently tested cannot
   show the gain came from rules-based-integration channels rather
   than generic trade liberalisation also benefiting non-EU OECD.
   The control set's positive +7.3pp trade-openness gain (CAN +20pp
   from NAFTA, AUS +9pp, USA +6pp) shows the global
   trade-liberalisation tide was rising for everyone in this period.

2. **Productivity proxy is too coarse.** Log GDP per capita PPP
   captures a mix of TFP, capital deepening, hours, and demographic
   composition. The PWT rtfpna informative outcome shows a near-zero
   DiD (+0.005 index points), which is the more direct productivity
   measure. A reader could plausibly argue the Single Market
   produced *demand-side* convergence (catching-up via investment
   inflows) rather than the *supply-side* productivity gains the
   Ordoliberal claim is really making.

3. **Selection of the comparator set.** The non-EU OECD set
   (USA/JPN/CAN/AUS/NOR/CHE) includes Norway and Switzerland —
   both of which adopted significant Single Market rules through
   EEA (NOR) and bilateral agreements (CHE). They are partially
   treated, biasing the DiD toward zero on the trade primary and
   making +5pp threshold easier to clear than it should be. A
   stricter comparator set excluding NOR and CHE would tighten the
   test.

4. **Counter-claim: EU productivity has fallen behind the US since
   the late 1990s.** A widely-cited stylised fact (van Ark, O'Mahony,
   Timmer) is that EU labour productivity growth slowed relative to
   US growth from 1995 onward, the opposite of what one would
   expect if the Single Market produced productivity gains. The
   pre/post DiD on a 1980-2010 window misses this if the EU-12
   was catching up 1980-1993 and that catching-up continued at the
   same pace post-1993; the DiD would record a pseudo-positive
   reading that just reflects the long convergence trend, not a
   1993 break.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Acknowledge that the +4.8 log-point GDP-PC-PPP DiD is jointly
    attributable to Single Market, EMU convergence, and Eastern
    enlargement supply-chain restructuring; it cannot be cleanly
    attributed to the rules-based integration channel alone.

(b) Report Ireland as the largest-leverage observation and note
    that excluding it would reduce both primary DiDs.

(c) Flag that the PWT rtfpna informative TFP DiD (+0.005 index
    points, near zero) is the more direct productivity test and
    does NOT support a strong supply-side productivity-gain
    interpretation. The headline SUPPORTED reading rests primarily
    on the trade and per-capita-output channels.

(d) Note that the spec's preferred intra-EU trade share series is
    not on disk; substituting total trade openness conservatively
    risks a false-positive on the trade primary because non-EU
    OECD partners NOR and CHE are partially treated by EEA /
    bilateral agreements. A v2 with the Eurostat intra-EU series
    and a tighter comparator set (drop NOR, CHE) would be a
    stronger test.

The strongest version of the steelman argues the hypothesis
conflates the Single Market's effect with the joint effect of
Maastricht, EMU, and Eastern enlargement. A genuine
single-market-only test would compare 1993-1999 (Single Market
active, EMU not yet locked in) to 1980-1992 with controls for the
convergence-criteria fiscal-monetary stance — a much harder
identification task this v1 does not attempt.
