# Disclosure

This framework does not claim neutrality. The author's priors are
disclosed here, and the framework's defence is structural openness to
adversarial correction, not absent bias. This document is tracked in
git; any update to a disclosed position or prior appears in commit
history.

---

## The author behind IESET

IESET is built and maintained under an institute banner by a single
named author with roughly two decades of working life across public
markets, venture capital, private real-estate development, digital
assets, and applied geopolitical analysis. The framework grew out of
a long-running frustration on both ends of the public-economics
debate: academic econometrics that is rigorous but irrelevant to live
policy questions, and policy commentary that is influential but
empirically untestable. IESET is the bridge the author wanted to
exist and could not find — a public, falsifiable, audit-trailed
ledger of which schools' predictions actually clear the empirical
bar over time.

The author has spent the last decade or so allocating capital across
multiple cycles, geographies, and asset classes. That experience
shows up in the framework in three ways: (1) the channel-separated
intervention model — fiscal versus regulatory — which any practising
allocator learns to disentangle the hard way; (2) the trajectory-
over-snapshot bias, because reading countries through their *changes
in policy regime* rather than their *current label* is how operators
actually price risk; and (3) the indicator-set integrity gate, which
came directly from watching how easy it is to game a thesis by
choosing the favourable subset of measurements.

The institute formalises this work for public review. The author's
identity is held back from the front of the framework on purpose:
the framework's claims should stand on their methodology and
their replication trail, not on the author's credentials. The
adversarial-review channel is open to anyone who can write a coherent
challenge.

---

## Disclosed intellectual priors

- **Market-liberal framing.** The author's baseline belief is that
  market mechanisms outperform state allocation for most goods,
  services, capital allocation among firms, trade, innovation, and
  responsiveness to preferences. This prior is falsifiable and will
  be updated by evidence; several conditions in the condition
  taxonomy (natural monopolies, resource rents, health-insurance
  adverse selection, foundational R&D, pandemic coordination,
  public goods) are acknowledged cases where state-organised
  mechanisms outperform pure market allocation.

- **Institutional quality as the upstream variable.** The author
  believes that institutional quality — state capacity, rule of law,
  property rights, low corruption, independent judiciary — is
  typically the binding constraint on development outcomes,
  upstream of the market-versus-state question.

- **Channel-separated intervention.** The author believes fiscal
  and regulatory intervention are causally distinct and should not
  be bundled under "neoliberalism" or "statism" labels. Empirical
  correlation between the two does not justify treating them as
  one variable.

- **Welfare architecture over welfare footprint.** The author
  believes the design of welfare systems (forced-saving individual
  accounts vs universal transfers vs hybrid) matters more than
  their headline size as a share of GDP.

- **Trajectory over snapshot.** The author believes within-country
  change over time is more causally informative than cross-sectional
  comparison. Most published policy commentary that compares country
  X to country Y at a single time is operating below the empirical
  bar IESET sets.

- **Scoped monetary claims.** The author does not endorse strict
  Austrian Business Cycle Theory orthodoxy, nor strict MMT, nor
  strict monetarism in their pure forms. The framework's monetary
  claims are scoped to empirically defensible territory; the
  hypotheses live in `hypotheses/monetary/`.

These priors are expected to shape *hypothesis choice*. They are not
permitted to shape *pre-registered hypothesis outcomes* —
falsification criteria are specified before runs and honoured after
them. The author has personally watched several of these priors take
losses on the scoreboard: the canonical-basket integrity gate, for
instance, refuted a market-liberal-friendly degrowth proof-of-concept
(Costa Rica wellbeing) on the safety leg, and the framework reports
that finding prominently rather than burying it.

---

## Disclosed economic positions

The author holds active economic positions across several asset
classes and geographies. These are disclosed because the framework's
outputs could plausibly move opinion on policy questions that affect
those positions.

| Category | Positions (general categories, not specific holdings) |
|----------|-------------------------------------------------------|
| Venture capital | Active investment decisions across an early-stage portfolio |
| Real estate development | Holdings across East Asia and Latin America |
| Digital assets / cryptocurrency | Active positions across major networks |
| Public markets | Long-only and long-short exposure |
| Geopolitical analysis | Advisory and analytical work |

**How conflicts are handled per-hypothesis.** Any hypothesis whose
outcome could directly benefit a specific named position above must
add a `conflict_disclosure` field to its YAML naming the position.
Generic market-liberal hypotheses whose outcomes benefit the overall
investment thesis are covered by this framework-level disclosure and
do not require per-hypothesis notes.

**What is not disclosed publicly.** Specific portfolio company names,
property addresses, position sizes, counterparties, and individual
trading positions. The framework-level categorical disclosure is
sufficient for the honesty claim; line-item disclosure would
compromise third parties without adding meaningful integrity to the
verdict-grading process.

---

## What this disclosure commits the author to

1. **Pre-registering every hypothesis before running it.** Git
   timestamps are the audit trail; the engine refuses to score a
   run whose threshold was set after the data landed.
2. **Publishing every run, including ones that falsify the author's
   prior.** There is no post-hoc filter. The Costa Rica refutation,
   the Cuba degrowth `inconclusive`, and the Japan wellbeing
   `supported_subset` are all visible on the public scoreboard
   exactly because the framework refused to grade SUPPORTED on a
   favourable indicator subset.
3. **Maintaining steelman files for every hypothesis.** The
   strongest opposing argument is written charitably and kept
   alongside the hypothesis. An empty or placeholder steelman is a
   review failure.
4. **Publishing a review log.** Contributions from opposing-prior
   reviewers are logged with outcomes, including ones that update
   the framework's conclusions.
5. **Asymmetric credit for prior-updating findings.** Results that
   update the author's belief against disclosed priors are surfaced
   prominently, not buried.

---

## What this disclosure does *not* do

It does not make the framework neutral. It makes it legibly biased,
which is the strongest form of intellectual honesty available given
human epistemics. A reader who mistrusts the author's disclosed
priors can:

- Inspect the pre-registrations (the spec is committed to git before
  any run, with timestamps that cannot be retroactively faked)
- Replicate any result (every run ships its own
  `replication.py` and a `manifest.yaml` pinning input vintages by
  sha256)
- Submit adversarial contributions via the `review/` channel
- Read the steelman file for any hypothesis

The defence is structural, not personal.

---

## Updates

Material changes to disclosed priors or positions appear here as
dated entries.

- **Initial disclosure** — Phase 0 foundation; institutional
  publication banner under IESET.
- **Indicator-set integrity** — Added as the sixth invariant after
  an audit pass caught five social-outcome specs grading SUPPORTED
  on favourable subsets of the canonical-literature indicator
  baskets. The canonical-basket gate now caps such verdicts at
  `supported_subset`. This is the framework's first publicly
  auditable case of the integrity model catching its own gaming —
  exactly the structural correction the disclosure model promises.
