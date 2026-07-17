import Link from "next/link";

import { EntityMap } from "@/components/diagrams/EntityMap";
import { UserJourneys } from "@/components/diagrams/UserJourneys";
import { Pipeline } from "@/components/diagrams/Pipeline";
import { AxisMatching } from "@/components/diagrams/AxisMatching";
import { Legend } from "@/components/diagrams/Legend";

export const metadata = {
  title: "How it works",
  description:
    "How IESET turns economic-policy claims into pre-registered tests, reproducible data runs, linked evidence pages, and scoreboard updates.",
};

interface TabCard {
  href: string;
  name: string;
  plainEnglish: string;
  example: string;
  howItFits: string;
}

const LOOP_STEPS = [
  {
    kicker: "01",
    title: "State the claim",
    body:
      "A prediction has to name the mechanism, outcome, sample, period, and what evidence would count against it.",
  },
  {
    kicker: "02",
    title: "Lock the rule",
    body:
      "The hypothesis and falsification rule are committed before estimation, so the target cannot move after the data arrives.",
  },
  {
    kicker: "03",
    title: "Run the record",
    body:
      "Publisher data is pinned to a vintage, the estimator runs, and the result is published with code and diagnostics.",
  },
  {
    kicker: "04",
    title: "Update the map",
    body:
      "Verdicts flow back to policies, movements, schools, axes, and the scoreboard, with steelmen and critiques kept attached.",
  },
];

const tabs: TabCard[] = [
  {
    href: "/h",
    name: "/h — Hypotheses",
    plainEnglish:
      "A specific, testable economic question written down before we look at the data — together with exactly what result would make us admit we were wrong.",
    example:
      'Example: "Did Chávez-era Venezuela collapse economically compared with its Latin American neighbours?" The question is written down, the data sources are named, and the test that would disprove it is spelled out. When the analysis runs, the page shows the verdict (supported / partial / refuted) and lets you re-run the code yourself.',
    howItFits:
      "Hypotheses are the answers. Policies, Movements, and Positions all point at hypotheses for their empirical backing — a policy points at the hypothesis that tested its outcome, a school points at the hypotheses testing its predictions.",
  },
  {
    href: "/p",
    name: "/p — Policies",
    plainEnglish:
      "A specific real-world reform — a law, a tariff, a subsidy, a central-bank decision — and a structured description of what exactly it changed.",
    example:
      "Example: El Salvador's 2021 Bitcoin Law. The page lists what the policy did (made Bitcoin legal tender alongside the dollar), who enacted it (Bukele's first term), and on a short list of standard levers — taxes, regulation, money, property rights — it shows which ones the policy pushed up, down, or left alone. That structured description is what lets the site find similar historical policies automatically.",
    howItFits:
      "Every policy links up to the Movement that passed it, and down to the Hypotheses that test its outcomes. It also gets compared to every other policy in the library to produce a 'similar historical policies' ranking.",
  },
  {
    href: "/m",
    name: "/m — Movements",
    plainEnglish:
      "A government or political movement — the people in power for a period — described by what they actually did, not by what party label they wore.",
    example:
      "Example: Bukele's first term (2019–2024). The page covers his doctrine, lists the specific policies his government passed (Bitcoin Law, CECOT mega-prison, constitutional-chamber removal…), and shows how those policies score on each lever. A movement is the sum of its policies; a left-wing government that cut taxes ends up scored the same as a right-wing one that cut taxes.",
    howItFits:
      "Movements are a convenient container — they group the policies one government passed. You drill down to individual policies, and from there to the hypotheses testing their outcomes.",
  },
  {
    href: "/pos",
    name: "/pos — Positions (schools of thought)",
    plainEnglish:
      "A school of economic thought — Keynesian, Austrian, MMT, Chicago, and so on — stated as a list of specific, empirical predictions the school makes.",
    example:
      "Example: Austrian Business Cycle Theory. The page lays out the school's steelman (the strongest version of its argument), then a list of specific predictions it makes (\"monetary expansion causes asset price inflation\", \"hyperinflation requires fiscal dominance\"). Each prediction is tied to a hypothesis — so as hypotheses run, the school's track record updates automatically.",
    howItFits:
      "Positions point at hypotheses via predictions, and at axes via their derived fingerprint. The Scoreboard aggregates how each school is doing across all its predictions.",
  },
  {
    href: "/a",
    name: "/a — Axes (the levers of policy)",
    plainEnglish:
      "The short, fixed list of standard policy levers every policy and movement is described on — so reforms from different countries and decades can be compared like-for-like.",
    example:
      'Example: "regulatory.financial_deregulation" is one lever. Its page defines what "up" and "down" mean, lists the data publishers that measure it, shows every policy in the library that moved it (grouped by direction), and shows every hypothesis in the library that tests outcomes on it. Think of an axis as a standard sliding scale that every reform gets scored on.',
    howItFits:
      "Axes are the shared vocabulary. Policies describe themselves in terms of axes; movements inherit axis scores from their policies; schools' predictions derive axis fingerprints; hypotheses test outcomes on axes. This is what makes 'find me similar historical reforms' possible.",
  },
  {
    href: "/scoreboard",
    name: "/scoreboard",
    plainEnglish:
      "A leaderboard showing how each school of thought is doing against the evidence — what fraction of its predictions held up once tested, and whether those wins look positive-sum or merely redistributive.",
    example:
      "Example: a school with 3 of 5 tested predictions supported ranks differently from one with 1 of 1. Both the rate and the sample size matter. If a Marxian or interventionist claim shows a short-run distributional gain, the next question is whether it created durable surplus or shifted costs into investment, productivity, supply, inflation, or fiscal capacity. The scoreboard updates automatically when a hypothesis finishes running.",
    howItFits:
      "The scoreboard is what you get when you roll up all positions × their predictions × their hypotheses' verdicts. It's the public summary of 'which schools the data supports so far'.",
  },
  {
    href: "/methodology",
    name: "/methodology",
    plainEnglish:
      "The six rules the whole framework commits to — so you can check that the site is actually playing by its own rules.",
    example:
      'Example: "the claim must be committed to git before the data is examined" is rule #1. The git history is public; anyone can verify it. These rules are the reason every other page is shaped the way it is.',
    howItFits:
      "Methodology is the spec. If a page on the site violates a rule, that's a bug — and contributors get paid for catching it.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-content px-8 py-10">
      {/* ----- Intro ----- */}
      <h1 className="m-0 mb-3 text-[30px] font-semibold tracking-[-0.02em] md:text-[34px]">
        How it works
      </h1>
      <p className="mb-5 max-w-[820px] text-[17px] leading-[1.55] text-muted">
        IESET turns economic arguments into auditable bets. A school, policy
        proposal, or historical claim has to say what should happen in the
        world; the rule is written down before the data is touched; the run
        uses pinned public-source data; the result updates the pages that
        depended on that claim.
      </p>
      <p className="mb-8 max-w-[820px] text-[15px] leading-[1.65] text-muted">
        The goal is not to make politics bloodless. The goal is to stop
        confident narratives from floating above the record. If a claim is
        important enough to shape policy, it should be specific enough to
        test, strong enough to steelman, and open enough for critics to break.
      </p>
      <p className="mb-8 max-w-[820px] text-[15px] leading-[1.65] text-muted">
        That is why the framework separates moral intent from empirical
        mechanism. A policy can redistribute income and still fail its broader
        claim if the evidence shows a zero-sum tradeoff, weaker production, or
        a shrinking base. The live scoreboard is where those tradeoffs become
        visible instead of staying hidden inside rhetoric.
      </p>

      <section className="mb-10 grid grid-cols-1 gap-3 md:grid-cols-4">
        {LOOP_STEPS.map((step) => (
          <div key={step.title} className="rounded border border-rule bg-white p-4">
            <div className="mb-1 font-mono text-[11px] text-accent">
              {step.kicker}
            </div>
            <h2 className="mb-1.5 text-[15px] font-semibold leading-snug text-ink">
              {step.title}
            </h2>
            <p className="m-0 text-[13px] leading-[1.55] text-muted">
              {step.body}
            </p>
          </div>
        ))}
      </section>

      {/* ----- A — Entity map ----- */}
      <DiagramSection
        id="entity-map"
        label="Diagram A"
        title="What are the pieces, and how do they link?"
        blurb="There are five kinds of card in the library: a Hypothesis, a Policy, a Movement, a Position, and an Axis. The diagram below shows them in two stacked panels. Top: the Axis sits at the centre as the shared policy-lever vocabulary that every other card is described in — that's the glue that lets a policy find its historical analogues and a school's predictions find their evidence. Bottom: the four non-axis cards also chain to each other directly — a Movement enacts Policies, Policies are tested by Hypotheses, and Positions (schools of thought) make their predictions on those Hypotheses."
        drawio="/diagrams/A_entity_map.drawio"
      >
        <EntityMap />
      </DiagramSection>

      {/* ----- Plain-English preamble before tabs ----- */}
      <section className="mb-10 rounded border-l-[3px] border-accent bg-accent-soft px-5 py-4">
        <div className="sc mb-1.5 text-[10px] font-semibold tracking-[0.1em] text-accent">
          the system in plain English
        </div>
        <p className="m-0 mb-2 text-[14.5px] leading-[1.7] text-ink">
          Imagine a library. Every book is a specific economic policy question
          — for instance, <em>&quot;does rent control reduce housing supply?&quot;</em>.
          Each book is written <strong>before</strong> anyone looks at the data,
          and spells out exactly what result would make the author admit
          they were wrong. When the analysis finally runs, the verdict gets
          stamped on the cover.
        </p>
        <p className="m-0 mb-2 text-[14.5px] leading-[1.7] text-ink">
          Alongside the books, the library keeps three other card catalogues:
          one of <strong>real policies</strong> (actual laws and reforms), one of{" "}
          <strong>governments</strong> that passed them, and one of{" "}
          <strong>schools of economic thought</strong> and what each school
          predicts.
        </p>
        <p className="m-0 text-[14.5px] leading-[1.7] text-ink">
          What makes the library searchable is a short list of{" "}
          <strong>standard policy levers</strong> (taxes, regulation, money,
          property rights, and so on) — every policy, every government, every
          school, and every question is described using the same set of levers.
          That shared vocabulary is what lets you show up and say &quot;I&apos;m
          drafting reform X&quot; and the library can say back &quot;here are
          five historical reforms that moved the same levers in the same
          direction, and here&apos;s what happened next&quot;.
        </p>
      </section>

      {/* ----- Tab-by-tab explainer ----- */}
      <section className="mb-16">
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
            Tab-by-tab — what each page is, and how it fits
          </h2>
        </div>
        <p className="mb-5 max-w-[780px] text-[14px] leading-[1.6] text-muted">
          Each page of the site holds one kind of card catalogue. For each
          one: what it is in plain English, an example of what you&apos;d find
          there, and how it connects to the others.
        </p>
        <div className="grid grid-cols-1 gap-3">
          {tabs.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className="group block rounded border border-rule bg-white p-5 hover:border-rule-strong hover:no-underline"
            >
              <div className="mb-3 flex items-baseline gap-3">
                <code className="text-[14px] font-semibold text-ink group-hover:text-accent">
                  {t.name}
                </code>
                <span className="text-[12px] text-faint">→</span>
              </div>

              <div className="mb-3">
                <div className="sc mb-1 text-[10px] text-muted">what it is</div>
                <p className="m-0 text-[14.5px] leading-[1.6] text-ink">
                  {t.plainEnglish}
                </p>
              </div>

              <div className="mb-3 border-l-[3px] border-rule pl-3">
                <div className="sc mb-1 text-[10px] text-muted">example</div>
                <p className="m-0 text-[13.5px] leading-[1.6] text-muted">
                  {t.example}
                </p>
              </div>

              <div>
                <div className="sc mb-1 text-[10px] text-accent">how it fits</div>
                <p className="m-0 text-[13px] leading-[1.55] text-ink/85">
                  {t.howItFits}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ----- B — Journeys ----- */}
      <DiagramSection
        id="user-journeys"
        label="Diagram B"
        title="Three kinds of person who arrive at the site"
        blurb="A journalist wants a citable answer in one page. A researcher wants to re-run the analysis from scratch to verify it. A policymaker is drafting a new reform and wants to know what happened when similar reforms were tried before. All three end up looking at the same underlying cards — just from different angles."
        drawio="/diagrams/B_user_journeys.drawio"
      >
        <UserJourneys />
      </DiagramSection>

      {/* ----- C — Pipeline ----- */}
      <DiagramSection
        id="pipeline"
        label="Diagram C"
        title="How a question becomes a published verdict"
        blurb="Every hypothesis walks this path: someone writes the question down (committed to a public git history), the system checks it's well-formed, the exact data sources get frozen in time, the analysis code runs and produces a result, the verdict gets published. The git commit timestamp is the proof that the question was written before the data was examined — nobody can silently reshape the question to fit the answer. Critics get paid to find holes; if a critique lands, the whole path runs again with a new question."
        drawio="/diagrams/C_pipeline.drawio"
      >
        <Pipeline />
      </DiagramSection>

      {/* ----- D — Matching ----- */}
      <DiagramSection
        id="axis-matching"
        label="Diagram D"
        title="How the library finds similar historical policies"
        blurb="You describe a proposed reform by saying which policy levers it would move and in which direction — \u201chigher\u201d/\u201clower\u201d/\u201cno change\u201d on taxes, regulation, money, and so on. The library compares that pattern against every historical policy and ranks them by overlap. Reforms that pushed the same levers in the same direction score highest; those that pushed the same levers in the opposite direction are still relevant (they show what the other side of the bet looked like). The same comparison runs behind the scenes on every policy page — that's where the 'similar historical policies' list comes from."
        drawio="/diagrams/D_axis_matching.drawio"
      >
        <AxisMatching />
      </DiagramSection>

      {/* ----- E — Legend ----- */}
      <DiagramSection
        id="legend"
        label="Diagram E"
        title="Reading guide — what the colours and symbols mean"
        blurb="The site uses a small number of visual shortcuts over and over: green/amber/red verdict strips, up/down arrows for direction, coloured dots for data-source status, and a few short chips. Read this once and every other page gets faster to skim."
        drawio="/diagrams/E_legend.drawio"
      >
        <Legend />
      </DiagramSection>

      {/* ----- Honest limits ----- */}
      <section className="mb-10 rounded border border-amber-200 bg-amber-50/50 p-6">
        <h3 className="m-0 mb-3 text-[15px] font-semibold text-ink">
          Honest limit: economic vs social-policy data asymmetry
        </h3>
        <div className="space-y-3 text-[14px] leading-[1.65] text-muted">
          <p className="m-0">
            The framework is structurally better at testing{" "}
            <strong className="text-ink">economic</strong> claims (growth,
            inflation, productivity, fiscal multipliers) than{" "}
            <strong className="text-ink">social-welfare</strong> claims —
            because the on-disk data favours the former. WDI / FRED / IMF /
            OECD-macro / PWT / BIS cover macroeconomic aggregates well; food
            security, mental health, subjective wellbeing, time poverty,
            housing affordability, and amenable-mortality indicators are
            sparse or missing.
          </p>
          <p className="m-0">
            Pre-registration discipline catches threshold-fiddling. It does
            NOT catch{" "}
            <strong className="text-ink">indicator-selection bias</strong> —
            where the spec author defines the test using the favourable
            subset of the canonical literature basket. Three social-outcome
            specs hit this gaming pattern (Cuba degrowth, Cuba resilience,
            Japan wellbeing) before the canonical-basket-gate landed in the
            engine. Each tested life expectancy + a chosen subset and
            graded SUPPORTED while caveats noted that the canonical-primary
            dimension was degrading (caloric collapse, optic neuropathy
            epidemic, fertility crash).
          </p>
          <p className="m-0">
            The fix has two parts. (1) The{" "}
            <strong className="text-ink">canonical-basket gate</strong>: any
            social-outcome claim must enumerate every dimension in the
            literature-canonical basket (Streeten 1981 for basic needs;
            OECD Better Life Index / WHR for wellbeing; UNDP HDR for human
            development) and either test it or document it as a data gap.
            Omitted canonical dimensions trigger a{" "}
            <code className="rounded bg-panel px-1 text-[12px]">
              supported_subset
            </code>{" "}
            verdict tier — amber on the scoreboard, NOT green. (2) A
            published{" "}
            <a
              href="https://github.com/iesetorg/ieset-framework1"
              className="text-accent underline hover:no-underline"
            >
              social-policy data backlog
            </a>{" "}
            inventories the missing fetchers (Gallup WHR Cantril ladder,
            FAO Food Balance Sheets full annual, OECD amenable mortality,
            HALE, 5-year cancer survival, OPHI MPI, OECD waiting times),
            so social-claim verdicts will tighten as the backlog clears.
          </p>
          <p className="m-0">
            Concrete consequence: claims like &ldquo;Costa Rica achieves
            high wellbeing at low throughput&rdquo; that look SUPPORTED on
            LE+CO2 alone come back{" "}
            <strong className="text-ink">refuted</strong> when the safety
            leg is added (CRI homicide rate 2.19× USA in 2010-2020).
            That&apos;s the integrity gate working.
          </p>
        </div>
      </section>

      {/* ----- Close ----- */}
      <section className="rounded border border-rule bg-panel p-6">
        <h3 className="m-0 mb-2 text-[15px] font-semibold text-ink">
          The framework in one sentence
        </h3>
        <p className="m-0 text-[14px] leading-[1.65] text-muted">
          Commit a falsifiable claim before you see the data; measure policy
          by what it did on channel-separated axes, not by who did it; link
          everything so a proposed reform can find its historical analogues
          and its empirical evidence in one click; let anyone who can write
          a coherent challenge reopen the verdict.
        </p>
      </section>
    </div>
  );
}

function DiagramSection({
  id,
  label,
  title,
  blurb,
  drawio,
  children,
}: {
  id: string;
  label: string;
  title: string;
  blurb: string;
  drawio: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="mb-16 scroll-mt-20">
      <div className="mb-3 flex items-baseline justify-between gap-4">
        <div>
          <div className="sc text-[10px] text-accent">{label}</div>
          <h2 className="m-0 mt-0.5 text-[20px] font-semibold leading-snug text-ink md:text-[22px]">
            {title}
          </h2>
        </div>
        <a
          href={drawio}
          download
          className="flex-none rounded border border-rule-strong bg-white px-3 py-1.5 text-[11.5px] font-medium text-ink hover:bg-panel hover:no-underline"
        >
          Download .drawio ↓
        </a>
      </div>
      <p className="mb-5 max-w-[820px] text-[14.5px] leading-[1.6] text-muted">
        {blurb}
      </p>
      <div className="overflow-hidden rounded border border-rule bg-white p-4">
        {children}
      </div>
    </section>
  );
}
