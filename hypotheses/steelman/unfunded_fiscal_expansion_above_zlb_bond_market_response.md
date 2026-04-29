# Steelman — Truss 2022 mini-budget as unfunded-fiscal repricing shock

**The strongest argument against this hypothesis:**

The September 2022 GBP/USD slide and gilt-yield spike were not a clean
"unfunded fiscal expansion above the ZLB triggers expected-inflation
repricing" story. They were primarily an LDI-cascade event: a
regulatory-mechanical forced-selling spiral inside the UK pension fund
sector, in which liability-driven investment funds had collateralised
gilt positions that hit margin triggers as yields rose, forcing
further gilt sales, in a self-reinforcing loop that was not in the
New-Keynesian-textbook fiscal-shock model. The Truss mini-budget was
the proximate trigger but not the dominant amplification mechanism.
A spec that codes the September 2022 episode as confirmation of the
unfunded-fiscal-expansion-above-ZLB story risks misreading a
pension-regulation accident as a macroeconomic regularity.

Specific objections the hypothesis must engage with:

1. **The dominant amplifier was institutional plumbing, not expected
   inflation.** The 2022-09-23 → 2022-09-28 yield move was concentrated
   at the long end (30y) where the LDI funds had the most leverage —
   not at the short end where expected-policy-rate revisions would
   register. A pure expected-inflation repricing story predicts the
   curve shifts roughly in parallel; the actual curve steepened
   sharply at the long end, consistent with forced-selling pressure
   on a specific maturity bucket.

2. **The BoE intervention is the natural experiment, and it argues
   *against* the unfunded-fiscal reading.** When the BoE on 2022-09-28
   announced unlimited long-gilt purchases, yields collapsed and FX
   recovered within hours — without any change to the fiscal
   announcement. If the underlying disturbance had been an
   expected-inflation repricing of unfunded fiscal expansion, a
   central-bank promise to buy bonds (which is itself inflationary)
   should have made it worse, not better. The fact that it instantly
   resolved the market stress is strong evidence that the constraint
   was not inflation expectations but collateral.

3. **The package was ~£45bn, not regime-changing.** The unfunded
   portion of the 2022 mini-budget was about 1.7% of UK GDP. The
   New-Keynesian above-ZLB model predicts a sharp response only when
   the package is large enough to plausibly shift expected inflation
   into a different regime. A 1.7%-of-GDP package is at the small end
   of historical fiscal shocks and would not, in a normal market,
   trigger a 5% FX move and a 100bp 30y-yield move on its own.

4. **Counterfactual: the same package in 2019 would not have
   produced the same response.** The institutional landscape that
   amplified the shock (LDI funds at scale + collateral cliffs) was
   a feature of the post-2010 yield-suppression environment. The
   spec generalises from a 2022-specific institutional configuration
   to "above-ZLB unfunded fiscal expansion" as a class — which is
   too broad an inference from N=1.

5. **High-frequency identification is contaminated by parallel news.**
   On 2022-09-22 (the day before the mini-budget) the Federal Reserve
   raised rates 75bp; on 2022-09-26 the dollar rallied broadly against
   most currencies, not just GBP. Some of the GBP/USD move attributed
   to the mini-budget is mechanically a USD-strength move that would
   have happened anyway. A clean test would also report
   GBP/EUR and GBP/JPY in the same window — if those moved much
   less, the unfunded-fiscal channel is partially substantiated; if
   they moved similarly, the whole "Truss-shock" framing inflates a
   USD-strength move.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the GBP/EUR move alongside GBP/USD over the same window —
ideally using boe:XUDLERS — to separate UK-specific repricing from
USD-strength noise. (XUDLERS is on disk; v1 should include it as a
secondary diagnostic.)

(b) Acknowledge that the BoE 2022-09-28 LDI intervention is *inside*
the t..t+5d window the spec literally names, which contaminates the
naive close-to-close FX move. The v1 replication uses the trough close
in the announcement → BoE-intervention sub-window as the dispositive
primary precisely to address this — but the result card should make
clear that this methodological choice is doing real work.

(c) Document the data gap on UK long-gilt yields explicitly. The bond-
market half of the spec's claim is what the New-Keynesian story most
directly predicts (long-yields rise from expected-inflation repricing);
without yield data, the FX channel alone is necessary but not
sufficient evidence. The verdict should be qualified accordingly.

(d) Flag that confirmation of the FX-trough threshold does not by
itself adjudicate between the New-Keynesian unfunded-fiscal story and
the LDI-mechanics story. Both predict an FX selloff; they differ in
predictions about the persistence of the move and about the curve
shape. Persistence: GBP/USD recovered to pre-mini-budget levels by mid-
October and beyond by end-2022, which is awkward for a regime-shift
expected-inflation reading and natural for a one-off institutional
incident. Curve shape: 30y gilt yields rose far more than 2y yields,
which favours the LDI-mechanics reading.

A v2 of the hypothesis should fetch the UK gilt term structure
(2y/10y/30y) and explicitly test the New-Keynesian implication that
the front end moves in proportion to the back end. If the back end
moves but the front end does not, the New-Keynesian story is
qualitatively wrong about this episode even if the FX threshold is
met.
