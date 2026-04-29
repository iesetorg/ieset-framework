# Steelman — fiscal_rule_departure_credibility_loss_effect

The strongest version of this hypothesis is **not** "fiscal-rule
departure CAUSED the Greek crisis" (a counterfactual claim
unfalsifiable from observational data), but the weaker associational
claim that documented departures from EDP / SGP norms in the
periphery were FOLLOWED by large sovereign-spread widening within a
short event window, and that spread widening was concentrated in
countries with the largest documented departures
(GRC > IRL ~ PRT > ESP > ITA).

Even on this weaker reading, the quantitative bar (>=50 bp cumulative
h=20 spread response, mean across the periphery event panel) is what
the ordoliberal "credibility loss" interpretation requires; a +5 to
+20 bp average response would be too small to force the Troika
programmes the claim invokes.

The ECB-OMT exclusion is critical: from 2012-09 onward, spread
compression reflects the Draghi "whatever it takes" backstop, not
rule compliance, so any event-window touching that period must be
excluded or the test conflates the two channels. The replication
scripts the EDP-breach event dates from Eurostat / EC documents and
applies a strict 2012-09-to-2013-03 OMT-window exclusion.

## Pre-registered event panel

- **GRC, 2009-10-20** — ELSTAT/Papandreou disclosure of revised
  2009 deficit (~12.5% of GDP, later revised to ~15.4%).
- **GRC, 2009-12-08** — Fitch downgrade to BBB+; loss of A-class.
- **IRL, 2009-Q3 / 2010-09** — banking-sector NAMA recap; EDP
  intensification.
- **PRT, 2010-Q1** — first formal EDP escalation; April 2011 IMF/EU
  programme.
- **ESP, 2009-Q2** — EDP opened by Council; banking-sector strains
  through 2011.
- **ITA, 2011-Q3** — fiscal-package failures, BTP-Bund spread blow-out.

The dispositive primary is the **mean cumulative h=20 trading-day
spread response across this panel** (per HYPOTHESIS_FRAMEWORK_AUDIT
§E2 the test is dispositive only on the mean; per-event responses
are reported as informative).

## Why the data-gap verdict matters

The replication CANNOT yet be evaluated because no eurozone-periphery
sovereign-yield series is on disk (ECB SDW IRS family + FRED
IRLTLT01* country re-publications are both missing). This is a hard
method-validity failure under the framework's invariants, not a
refutation. The script is staged so that the verdict computes
automatically the day a fetcher lands the yield series.
