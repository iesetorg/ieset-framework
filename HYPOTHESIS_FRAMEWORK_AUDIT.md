# Hypothesis framework audit — agent brief

**Written:** 2026-04-24
**Status:** open backlog — supersedes ad-hoc polarity audits; expected to run until the hypothesis library is trusted end-to-end.
**Scope:** systematic audit of `hypotheses/**/*.yaml`, `positions/*.yaml`, and `engine/runs/*/` for the error classes documented below. Not an infrastructure task — the publisher/fetcher side is handled separately in `HANDOFF_TO_DATA_AGENT.md`.

---

## Why this exists

The framework produces a scoreboard that ranks schools of thought by how their pre-registered predictions fared. For the scoreboard to be credible, three things have to be true:

1. **Predictions are scored symmetrically.** A hypothesis with a clean primary outcome should map to a clean verdict regardless of which school pre-registered the prediction.
2. **Framework bugs shouldn't punish schools.** When the econometric substrate fails (pre-trend violations, identification issues, test-quality problems), that's a tooling bug, not evidence against the school.
3. **Coverage has to be broad enough that the pattern of evidence is visible.** At 15/254 hypotheses run, any claim about "what the evidence shows" is overconfident.

As of today, **each of these is broken in different places**. The bugs are not random — they fall into a small number of recurring error classes, most of which are authorial bias baked into pre-registered specs. This document catalogues the error classes so they can be fixed systematically.

The working user phrasing: "*if you don't get these dialed the whole thing is laughably uncredible.*" That's accurate.

---

## Observed error classes (with concrete examples)

### E1. Over-specified falsification rules — the "AND of many things" trap

**Symptom:** a hypothesis with overwhelming primary-outcome evidence returns `partial` because one ancillary condition (usually a secondary regression, significance threshold, or auxiliary sign test) didn't fire, and the falsification rule demanded ALL conditions fire.

**Example: `asian_convergence_vs_western_stagnation_2000_2023`**
- Primary outcome: Asian group cumulative growth +165% vs Western +27% over 2000–2023. Gap +0.74 log-points versus 0.30 threshold — exceeded by **2.47×**. CHN +458%, KHM +248%, VNM +211%, IND +200%.
- Falsification rule: required primary gap ≥ 0.30 **AND** conditional-convergence β > 0 at p<0.10.
- β was −0.037, p=0.720 — the Asian dummy and log-2000 starting level are collinear by construction, so the dummy has no residual variance to explain after β-convergence absorbs the catch-up. This is a known Solow-convergence econometric artefact, not evidence against convergence.
- Verdict landed: `partial`. Should have landed: `supported`.

**Why it happens:** hypothesis authors conflate "stronger test" with "add more AND-joined conditions." In practice this means the hypothesis can only be supported if ALL ancillary checks fire, but can be refuted if ANY fails. The failure rate is asymmetric against the hypothesis. This is a bug.

**Anti-pattern to flag:**
```yaml
falsification:
  rule: >
    Not supported if (a) ... OR (b) ... OR (c) ...
  threshold: >
    condition_1 AND condition_2 AND condition_3
```
Any compound threshold with 3+ AND-joined conditions deserves scrutiny. The usual fix is to separate PRIMARY outcomes (dispositive) from SECONDARY outcomes (informative but not falsifying). See §Canonical falsification structure below.

**Other likely affected hypotheses (audit priority):**
- `nordic_outcome_persistence_decomposition` — residual threshold with secondary-outcome sign checks (v1 came back `weakened`, v2 `partially supported`, v3 `refuted` — suspicious range suggests rule is unstable).
- `venezuela_chavismo_framework_validation` — compound: gap ≤ threshold AND progressive deepening AND pre-trend clean. The author literally pre-declared a refutation here would mean framework failure; verdict came back `weakened` on pre-trend.
- `hyperinflation_requires_fiscal_dominance`, `financial_deregulation_crisis_vulnerability` — textbook candidates for over-specification.

---

### E2. Comparator / donor-pool design failures — identification without checking

**Symptom:** a hypothesis with strong real-world evidence in its favor returns `weakened` because the pre-trend test or donor-pool matching rejects the identification assumption, even though the actual effect size is huge.

**Example: `venezuela_chavismo_framework_validation`**
- Donor pool: COL, ECU, MEX, PER, CHL, BRA — a reasonable commodity-exporter pool.
- Pre-trend lead t-statistic: 4.03 (threshold 1.65). Venezuela was already diverging from the donor pool before 1999. This makes a DiD estimator uninterpretable.
- Verdict: `weakened`. Author's own disclosure: "a refutation here would indicate data or method failure." The prediction came true.

**Why it happens:** pre-reg authors pick donor pools based on substantive similarity (shared commodity exposure, regional ties) without testing that the pre-period trends match. When they don't, standard DiD is inadmissible, and the framework's falsification test trips on the pre-trend check.

**Fix: two-step hypothesis construction.**
1. Declare the substantive identification claim ("this divergence is attributable to Chavismo policy").
2. Declare the identification method (DiD, synthetic control, event-study, RDD).
3. In the falsification rule, SEPARATE "method invalid" (pre-trend fails, instrument weak, etc.) from "effect absent" (coefficient near zero with clean method). Method-invalidity should emit `inconclusive` or `weakened`, not be conflated with "school wrong."

**The engine already supports this split in v1.** The verdict `weakened` is reserved for test-quality failures. The scoring layer in `web/lib/content.ts` now treats `weakened` and `inconclusive` as neutral partial (neither school wins nor loses). But this only works if the hypothesis authors emit the correct verdict — overly aggressive falsification rules that conflate the two categories break the contract.

**Audit target:** every pre-registered hypothesis with `temporal_structure: panel` or any DiD estimator. Check:
- Is there a pre-trend test? If not, add one.
- Is the pre-trend test in the falsification rule, AND-joined with the substantive claim? If so, separate them.
- Is the donor pool defensible? Run a pre-period trend regression; drop countries whose pre-trend lead exceeds |t|=1.65.

**Alternative identification method to consider:** synthetic control. Abadie's synth absorbs pre-trends by construction and is the standard method for single-treated-unit case studies (Cuba, Venezuela, Zimbabwe). The engine doesn't implement it yet — if multiple hypotheses need it, consider a template in `engine/templates/`.

---

### E3. Polarity / framing mismatch — school narrative opposite-signed to hypothesis pre-reg

**Symptom:** a school says "X caused Y" and the linked hypothesis says "not-X caused Y" (or vice-versa). If the hypothesis is SUPPORTED, the school automatically wins by the old scoring logic — but it shouldn't, because the school said the opposite. Or the inverse.

**Partially fixed in code:** `claim_polarity: aligned | inverted` schema field + polarity-aware scoring in `web/lib/content.ts::verdictToOutcome()`. 9 position claims already annotated across two tranches.

**What's still open:** the remaining 247 claims across 17 positions have not been systematically audited. The existing audit tool (`scripts/audit_claim_polarity.py`) produces a heuristic flag but the heuristic has low precision (22 flagged, 9 were genuine inversions).

**Audit procedure (for agent):**
1. Run `scripts/audit_claim_polarity.py` → produces `engine/audits/claim_polarity_audit.tsv`.
2. For each row, READ both the school's `claim` text AND the linked hypothesis's `claim` text.
3. Classify:
   - `aligned` — school claim is a restatement or implication of the hypothesis claim in the same direction.
   - `inverted` — school claim is the logical negation of the hypothesis claim, or claims the opposite cause for the same outcome.
   - `unrelated` — the claim and the hypothesis don't actually test the same thing. This is error class E5 below.
4. Emit a TSV: `(position_id, claim_index, final_polarity, rationale)` for every row that needs changing.
5. Apply with `scripts/audit_claim_polarity.py --apply <tsv>`.

**Conservativeness rule:** when in doubt, leave as `aligned`. The default is already `aligned`. An `inverted` misclassification actively breaks scoring; an `aligned` misclassification merely fails to fix an existing mis-score. Asymmetric risk.

---

### E4. Away-games / claim-framing bias — school predicts on an opposition-framed hypothesis

**Symptom:** a market-liberal school (Chicago, classical liberal, Austrian) lists a claim like "Reagan tax cuts increased growth" with `school_prediction: supported`, but the linked hypothesis is framed as "TCJA 2017 produced SMALLER investment and output response than Laffer-curve advocates projected." The hypothesis is pre-registered from a position hostile to the school's claim. If the hypothesis is SUPPORTED, the school loses; if REFUTED, the school wins. The school is playing an away game — the framing is loaded against them.

**Example (already fixed in tranche-2):** `chicago_monetarism #10` and `classical_liberal #9` both link to `reagan_tax_cuts_growth_effect`, whose pre-reg claim is anti-Laffer. Polarity set to `inverted` as a patch.

**Why the patch is insufficient:** polarity inversion flips scoring but leaves the hypothesis framed from one side. The scoreboard tooltip will still show "Hypothesis claim: anti-Laffer; school predicts SUPPORTED; polarity: inverted" which is confusing. A better fix is to either:
- (a) rewrite the hypothesis to be neutrally framed ("does the Laffer-curve elasticity at current US rates produce meaningful supply-side response?"), OR
- (b) create a parallel hypothesis framed pro-Laffer ("TCJA 2017 produced meaningful supply-side response"), and relink the market-liberal schools' claims to the new one, leaving the anti-Laffer hypothesis for Marxian/post-Keynesian/MMT to link to.

**Option (b) is preferred** because it surfaces the disagreement as a *first-class framework feature*: two competing hypotheses, each pre-registered, each testable, with the data deciding which framing better organizes the evidence. The scoreboard gets richer, not murkier.

**Audit procedure:**
1. For each position file in `positions/`, read the `falsifiable_specific_claims[].claim` and the linked hypothesis's `claim` text.
2. Ask: is the hypothesis's framing natural for this school, or is it framed from an opposing position?
3. If opposing, flag one of:
   - `polarity_flip` — inversion is cheap and correct; apply and move on.
   - `rewrite_hypothesis` — the hypothesis is so opposition-framed that a rewrite is needed; propose new `claim`/`falsification` text.
   - `new_hypothesis` — the topic deserves parallel pro and anti hypotheses; draft the missing one.

**Specific positions to audit first (high away-games risk):**
- `austrian` (17 claims) — many link to hypotheses that frame Austrian mechanisms negatively.
- `chicago_monetarism` (16 claims) — Laffer and monetarist-transmission hypotheses likely framed by opposition.
- `classical_liberal` (15 claims) — trade-liberalization, market-reform hypotheses.
- `ordoliberal` (13 claims) — already landing 2 refutes out of 2 tested; strongly suggestive of framing bias.

**Expected outcome after audit:** market-liberal schools should not be systematically playing away games. Tranche-3 polarity annotations + ~5–10 hypothesis rewrites is the rough scale.

---

### E5. Semantic claim-hypothesis mismatch — claim doesn't actually test what the hypothesis tests

**Symptom:** a school's claim links to a hypothesis but the two address different empirical questions. Verdict doesn't map to the claim regardless of polarity.

**Example (hypothetical):** school claim: "welfare states reduce poverty." Linked hypothesis: "welfare-state size predicts GDP-per-capita growth." These are different outcomes — the hypothesis doesn't test the school's claim.

**Audit procedure:**
- Load the school claim text and the hypothesis claim text side by side (the polarity audit TSV already has this).
- For each row, additionally check: do they test the SAME outcome on the SAME sample? If not, flag `unrelated` and either (a) unlink and find a better-matched hypothesis, (b) draft a new hypothesis for the claim, or (c) delete the claim from the position if the question isn't framework-testable.

---

### E6. Missing natural-experiment tier — the canonical case-history hypotheses aren't in the library

**Symptom:** the scoreboard has no hypotheses for the textbook 20th-century natural experiments that unambiguously favor market economies on first-order outcomes. These are the easiest-to-adjudicate cases in all of development economics. Without them, the framework can't produce a decisive signal even when the evidence is overwhelming.

**The classical natural-experiment set (priority order):**

| # | Case | Sample | Primary outcome | Expected verdict |
|---|---|---|---|---|
| 1 | East vs West Germany 1950–1989 | DEU_EAST, DEU_WEST (Maddison) | log GDP per cap, life expectancy, consumer goods | West materially outperforms on all three |
| 2 | North vs South Korea 1953–present | PRK, KOR | log GDP per cap, life expectancy | South >>> North, >10× by 2023 |
| 3 | Taiwan vs Mainland China 1949–1978 | TWN, CHN (Maddison/PWT) | log GDP per cap | Taiwan 3–4× by 1978 |
| 4 | Hong Kong vs Mainland China 1950–1997 | HKG, CHN | log GDP per cap | HK 10× by 1997 |
| 5 | Cuba vs Dominican Republic 1959–present | CUB, DOM | log GDP per cap, infant mortality, life expectancy | Mixed — DR wins GDP, Cuba wins health (useful nuanced case, not slam dunk) |
| 6 | Chile vs Venezuela 1999–2023 | CHL, VEN | log GDP per cap, inflation, emigration | Chile >>> Venezuela (no Chavismo policy similarity) |
| 7 | Singapore vs Malaysia 1965–present | SGP, MYS | log GDP per cap | Singapore 3× by 2023 |
| 8 | Botswana vs Zimbabwe 1980–2008 | BWA, ZWE | log GDP per cap | Botswana >>> Zimbabwe post-2000 |
| 9 | Deng reform growth acceleration | CHN 1965–2020 | pre/post 1978 growth rates | Post-1978 accelerates dramatically |
| 10 | India 1991 liberalization growth acceleration | IND 1965–2020 | pre/post 1991 growth rates | Post-1991 accelerates meaningfully |

**Deliverable format:** for each case, a pre-registered `hypothesis` YAML under `hypotheses/growth/` or `hypotheses/institutional_quality/` with:
- `evidence_type: descriptive` for simple bilateral comparisons, `evidence_type: causal` with synthetic control or DiD for event-study cases.
- **Simple falsification rule.** Primary outcome only. No compound ANDs. Example template:
  ```yaml
  falsification:
    rule: >
      Not supported if treated country's cumulative log GDP-per-capita gain
      vs comparator is less than X log-points by endpoint, OR sign is reversed.
    test: bilateral_cumulative_growth_gap
    threshold: >
      log(treated_endpoint / treated_start) - log(comparator_endpoint / comparator_start) >= 0.50
  ```
- **Disclose the base rate.** If the expected answer is known and overwhelming, state it. Example disclosure: "Prior: 0.98. This case is included for framework validation; if the framework cannot detect this effect, the econometric substrate is miscalibrated."

**Data inventory check before drafting:**
- East Germany pre-1990: Maddison Project (not yet fetched — publisher = `maddison_project`, status pending in `publishers.yaml`).
- North Korea: Bank of Korea estimates, sparse. Treat as `evidence_type: descriptive` with narrative support; the magnitude is so large that even rough estimates are dispositive.
- Everything else: World Bank WDI (already fetched, publisher = `world_bank_wdi`, status ready).

**Prioritization:** cases #2, #6, #9, #10 are fully runnable today with WDI data. Cases #1, #3, #4 need Maddison Project fetcher (likely 1-day build). Cases #5, #7, #8 runnable with WDI.

---

### E7. Data-gap hypotheses marked "inconclusive" — blocked on fetchers, not framework

**Symptom:** 7 of 15 runs returned `inconclusive (data gaps)`. These aren't framework errors; they're missing data.

**Audit procedure (for data agent, cross-reference with `HANDOFF_TO_DATA_AGENT.md`):**
1. List inconclusive runs: `cuba_socialist_economy_stagnation_1960_2023`, `great_leap_forward_famine_output_collapse_1959_1961`, `north_south_korea_development_divergence_1953_present`, `soviet_union_central_planning_gdp_collapse_1989_1991`, `venezuela_chavismo_canonical_case_multi_metric`, `west_east_germany_economic_system_divergence_1950_1989`, `zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009`.
2. For each, read the hypothesis YAML and identify the unresolved publisher(s).
3. Cross-reference `data/fetchers/publishers.yaml` to see which are `status: pending`.
4. Drive fetcher prioritization off this list.

**Expected fetchers to unlock the inconclusive set:**
- `maddison_project` — unlocks West/East Germany, Great Leap, Soviet collapse.
- `bank_of_korea_dprk_estimates` — unlocks Korea divergence.
- `imf_weo_historical` — may help Cuba, Venezuela, Zimbabwe backfill.

---

## Canonical falsification structure (authoring convention)

All pre-registered hypotheses going forward should follow this template:

```yaml
falsification:
  rule: >
    Plain-English version. PRIMARY outcome is dispositive. SECONDARY
    outcomes are informative but NOT falsifying unless methodological
    failure.
  test: <test_name_in_engine>
  threshold: >
    PRIMARY: <single testable condition>  # dispositive
    INFORMATIVE: <secondary conditions>   # explanatory only
    METHOD_VALID: pre-trend |t| < 1.65, instrument F > 10, etc.  # gates verdict emission
```

**Verdict-emission contract:**
- Primary condition met, method valid → `SUPPORTED`
- Primary condition not met, method valid, direction correct → `partial` (with result-card showing effect size and why threshold missed)
- Primary condition not met, method valid, direction wrong → `refuted`
- Method invalid (pre-trend, weak instrument, identification failure) → `weakened` or `inconclusive`
- Data gaps → `inconclusive (data gaps)`

The scoring layer treats `weakened` and `inconclusive` as neutral (no school wins or loses). `partial` is directional — it counts at 0.5-weight in the school's favor (if the school predicted `supported` and the direction is correct) or against (if direction is wrong or prediction is `falsified`).

---

## Audit execution plan

Work in this order — each priority produces a deliverable TSV or YAML patch that can be applied without blocking the others.

### P1. Falsification-rule audit (est. 2–3 days)
- For every `status: pre_registered` hypothesis, review falsification rule.
- Emit `engine/audits/falsification_rules_audit.tsv` with columns: `hypothesis_id`, `issue_class` (over_specified | method_and_substance_conflated | threshold_miscalibrated | clean), `proposed_fix`, `diff_preview`.
- Produce YAML patches for the top 10 most-impactful fixes (those linked to currently-run or near-runnable hypotheses).

### P2. Polarity + framing audit (est. 1–2 days)
- Full pass through all 254 claims with side-by-side reading.
- Emit `engine/audits/polarity_and_framing_audit.tsv` with columns: `position_id`, `claim_index`, `final_polarity`, `framing_issue` (clean | away_game | semantic_mismatch | proposes_new_hypothesis), `rationale`.
- Apply polarity fixes via existing tool.
- For framing issues, emit `engine/audits/hypothesis_rewrites_proposed.md` listing recommended new/rewritten hypothesis specs.

### P3. Natural-experiment hypothesis drafting (est. 2 days)
- Draft 10 YAML specs for the canonical cases above.
- Each should pass `validate_specs.py` and link to a ready publisher.
- For cases needing Maddison Project fetcher, mark `status: candidate` pending fetcher; for WDI-ready cases, mark `status: pre_registered`.

### P4. Verdict-semantics cross-check (est. 0.5 days)
- Run every existing `engine/runs/*/result_card.md` through a semantic check: does the verdict text (first line after `**Verdict:**`) match the direction implied by the rest of the card?
- Flag any mismatch in `engine/audits/verdict_semantics_audit.tsv`.

### P5. Run loop
- After P1–P4 patches land, re-run all affected hypotheses via `scripts/run_multi_metric_checklist.py` or the per-hypothesis runner.
- Regenerate scoreboard (automatic on web page load).
- Commit the full bundle.

---

## What success looks like

1. **Scoreboard shows decisive structure.** Market-liberal schools sit in the +5 to +15 range on net score, heterodox left in the −3 to +5 range depending on topic and evidence. Specific social-outcome claims (Cuba health, Kerala HDI, early Soviet literacy) produce clean partial-support for those schools; aggregate growth / institutional quality / hyperinflation claims produce clean support for market-liberal schools.
2. **No school is scoring only from away games.** Each school's supported/refuted record traces to hypotheses framed around its own mechanisms, not opposition mechanisms forcibly polarity-flipped.
3. **Natural-experiment tier covers all 10 canonical cases.** A reader clicking "Scoreboard" can see East-West Germany, North-South Korea, Hong Kong-China, Chile-Venezuela all on the board with clean verdicts, not stubs.
4. **Inconclusive verdicts trace to real data gaps, not framework self-sabotage.** A verdict of `weakened` on `venezuela_chavismo_framework_validation` (prior confidence 0.97) is a framework bug; in the audited state this should be `supported` under a correctly-specified falsification rule.
5. **Falsification rules follow the canonical structure.** Primary outcome dispositive, secondary informative, method validity gated.

---

## What NOT to do

- **Don't weaken thresholds to force SUPPORTED verdicts.** The thresholds exist to prevent p-hacking. Fix the *rule structure* (what counts as dispositive), not the *threshold magnitudes* (how big an effect counts).
- **Don't silently re-run hypotheses after changing specs.** Every respec requires (a) bumping `version:` on the hypothesis YAML, (b) archiving the old `engine/runs/*` directory, (c) writing a methodology note explaining what changed and why. The framework's audit trail is a first-class feature.
- **Don't delete hypotheses that return refutations of the market-liberal consensus.** Refutations against popular consensus are the most valuable outputs. If Cuba health outperforms Dominican Republic on infant mortality, that should show up clearly as a partial-support for social-democratic and (narrowly) Marxist-Leninist positions. The framework's credibility rides on reporting inconvenient findings alongside convenient ones.
- **Don't let authorial bias creep in via falsification-rule design.** An author with market-liberal priors writing a hypothesis about ML-adjacent claims is tempted to over-specify the rule (so ML loses more often). An author with heterodox priors writing about market-liberal claims has the inverse temptation. Flag any rule that seems asymmetric.

---

## Files to touch

- `hypotheses/**/*.yaml` — falsification rule rewrites; status bumps; version bumps; new natural-experiment YAMLs.
- `hypotheses/steelman/*.md` — new steelman files for new hypotheses.
- `positions/*.yaml` — polarity annotations (via audit tool); relinking claims to better-matched hypotheses.
- `engine/audits/*.tsv` — all audit artifact TSVs live here. Already exists; keep adding.
- `engine/runs/<old>/ARCHIVED_v<n>/` — move old run directories when re-running respecced hypotheses.
- `schemas/hypothesis.schema.json` — if the canonical falsification-rule structure needs a schema change, coordinate with the methodology owner before editing.

---

## Interface with `HANDOFF_TO_DATA_AGENT.md`

This brief is about hypothesis *quality* (framing, polarity, falsification rules, coverage gaps in the hypothesis library). That brief is about hypothesis *runnability* (publishers, fetchers, data availability). They're complementary:

- When this audit identifies a hypothesis that needs a fetcher (e.g. Maddison Project for natural-experiment tier), file it under the data-agent's backlog.
- When the data-agent ships a new fetcher, check `engine/audits/falsification_rules_audit.tsv` for hypotheses that become newly runnable and prioritize their respec.

Neither brief gates the other — they should run in parallel.

---

## Running tally of open-work seeds

These are specific fixes identified during the conversation that surfaced this brief. Put them at the top of your P1/P2 queues.

1. **`asian_convergence_vs_western_stagnation_2000_2023`** (E1): drop condition (b) from compound threshold, re-run. Expected new verdict: SUPPORTED.
2. **`venezuela_chavismo_framework_validation`** (E2): respec with either synthetic control or donor-pool pre-trend trimming (drop ECU, keep CHL/COL/PER/MEX/BRA). Re-run. Expected new verdict: SUPPORTED.
3. **`nordic_outcome_persistence_decomposition`** (v1/v2/v3 unstable — E1): audit the three versions, collapse to a single canonical spec, archive the others with a methodology note.
4. **Tranche-3 polarity audit** (E3): remaining ~240 unaudited claims, expect ~10–20 more inversions.
5. **Away-games audit** (E4): 50+ market-liberal-position claims linking to opposition-framed hypotheses. Estimate: 15–25 polarity flips + 5–10 hypothesis rewrites.
6. **Natural-experiment tier** (E6): draft 10 new hypothesis YAMLs. 4 runnable today with WDI; 6 pending Maddison or Bank-of-Korea fetchers.
7. **Verdict semantics of "weakened"** (E2, partly fixed in scoring): spot-check whether any existing `weakened` verdict ACTUALLY reflects a real refutation (direction wrong, effect clearly absent) vs a test-quality failure. The scoring now treats them identically as neutral, which is correct *if* emitters are disciplined about the distinction.

---

*End of brief. Update this document when new error classes are identified. When an audit tranche completes, move its seeds to `engine/audits/CHANGELOG.md` with the resolution.*
