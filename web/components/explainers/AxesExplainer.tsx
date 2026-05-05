import Link from "next/link";

/**
 * Foundational explainer for the policy-content axes system.
 *
 * Used at the top of /a (axes index), on the homepage, and linked from
 * /methodology. The framework's whole epistemology rests on this: party
 * labels lie; axes are the language we use to score policy content
 * apples-to-apples across countries and decades.
 *
 * Variant "full" renders the long-form explainer with the worked example.
 * Variant "compact" renders a capsule for the homepage / inline placements
 * where space is tight.
 */

interface AxesExplainerProps {
  variant?: "full" | "compact";
}

export function AxesExplainer({ variant = "full" }: AxesExplainerProps) {
  if (variant === "compact") {
    return (
      <div className="rounded-lg border border-rule bg-panel p-5">
        <div className="mb-2 flex items-center gap-2">
          <span className="rounded-full bg-accent-soft px-2.5 py-[3px] text-[10.5px] font-semibold uppercase tracking-wider text-accent">
            Axes — the framework&apos;s spine
          </span>
        </div>
        <p className="m-0 mb-3 text-[14.5px] leading-[1.55] text-ink">
          Party labels are a bad measurement device. &quot;Left&quot; and
          &quot;right&quot; mean different things in different countries, and
          campaign mood is not evidence. The framework codes every policy by
          channel — fiscal, regulatory, monetary, institutional — so the same
          content is scored the same way no matter who enacted it.
        </p>
        <div className="grid grid-cols-1 gap-2.5 text-[13px] sm:grid-cols-3">
          <ExplainStep
            title="Each policy moves axes"
            body={
              <>
                A tax-cut policy moves{" "}
                <code className="font-mono text-[11.5px]">
                  fiscal.tax_progressivity
                </code>{" "}
                in the <span className="text-red font-semibold">−</span>{" "}
                direction.
              </>
            }
          />
          <ExplainStep
            title="Movements aggregate"
            body={
              <>
                A government&apos;s axes_summary fingerprints what it actually
                did, regardless of how it labelled itself.
              </>
            }
          />
          <ExplainStep
            title="Hypotheses test"
            body={
              <>
                When axis X moves direction Y, does outcome Z follow? Schools
                that predicted right or wrong are scored on the{" "}
                <Link href="/scoreboard" className="text-accent hover:underline">
                  Scoreboard
                </Link>
                .
              </>
            }
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-3 text-[12.5px]">
          <Link
            href="/a"
            className="text-accent hover:underline"
          >
            Browse the axes →
          </Link>
          <Link
            href="/a"
            className="text-muted hover:text-ink hover:underline"
          >
            Why this design
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-rule bg-white p-6">
      <h2 className="m-0 mb-3 text-[22px] font-semibold tracking-[-0.01em]">
        What axes are, and how they work
      </h2>
      <p className="m-0 mb-4 max-w-[760px] text-[15px] leading-[1.6] text-ink">
        Party labels are a bad measurement device. &quot;Left&quot; and
        &quot;right&quot; mean opposite things in different countries —
        Hungary&apos;s Orbán is statist-left on fiscal but hard-right on
        rule-of-law; Macron is centrist-left on social policy but supply-side
        on labour and tax. Lumping them by label destroys the information that
        matters. So instead the framework codes every policy on a fixed set of
        channel-separated axes that describe what the policy{" "}
        <em>actually does</em>.
      </p>

      <div className="mb-5 grid grid-cols-2 gap-3 text-[13px] md:grid-cols-4">
        <ChannelTag channel="fiscal" count={6} />
        <ChannelTag channel="regulatory" count={8} />
        <ChannelTag channel="monetary" count={2} />
        <ChannelTag channel="institutional" count={3} />
      </div>

      <h3 className="mb-2 mt-6 text-[15px] font-semibold">
        How the four entity types interlock through axes
      </h3>
      <div className="mb-4 overflow-x-auto rounded border border-rule bg-panel p-4">
        <pre className="m-0 whitespace-pre font-mono text-[11.5px] leading-[1.65] text-ink">
{`POLICY     ──axes_moved──▶  AXES (19 ids, +/−/0)
  │                           ▲
  ▼                           │
MOVEMENT   ──axes_summary─────┘   (aggregates: + / − / 0 / mixed)
  │
  ▼
HYPOTHESIS  ──tests: when an axis moves direction X, does outcome Y follow?

POSITION   ──claims: axis X moving direction Y produces good outcome Z
            (predictions linked to specific hypotheses, scored on Scoreboard)`}
        </pre>
      </div>

      <h3 className="mb-2 mt-6 text-[15px] font-semibold">
        Example — Thatcher 1979 cuts top income tax 83 → 60%
      </h3>
      <ol className="m-0 mb-3 list-decimal pl-5 text-[14px] leading-[1.7] text-ink">
        <li>
          The policy YAML lists <code className="font-mono text-[12px]">axes_moved: [{`{`}axis: fiscal.tax_progressivity, direction: −{`}`}]</code>.
        </li>
        <li>
          The Thatcherism movement aggregates this with other policies into
          its{" "}
          <code className="font-mono text-[12px]">axes_summary</code> showing
          progressivity ↓, product-market competition ↑, financial deregulation ↑.
        </li>
        <li>
          The Chicago position predicts: when{" "}
          <code className="font-mono text-[12px]">fiscal.tax_progressivity</code>{" "}
          moves −, growth rises within five years. That&apos;s a falsifiable
          claim linked to a specific hypothesis.
        </li>
        <li>
          The hypothesis runs against real data and produces a verdict. The
          verdict feeds back into Chicago&apos;s support rate on the Scoreboard.
        </li>
      </ol>
      <p className="m-0 max-w-[760px] text-[14px] leading-[1.6] text-muted">
        That whole chain — from a specific policy enactment to a school of
        thought&apos;s track record — is only possible <em>because</em> of the
        axes. Without them, the discussion is stuck arguing about whether
        Thatcherism was &quot;neoliberal&quot; — a word fight, not an empirical
        question.
      </p>

      <div className="mt-5 flex items-center gap-2 rounded bg-accent-soft px-3 py-2 text-[12.5px] text-accent">
        <span aria-hidden>→</span>
        <span>
          <strong>Invariant 3:</strong> two governments that move the same
          axes the same direction get scored identically, regardless of their
          party label. Ideological tribes don&apos;t earn or lose points from
          who they look like; only from what their policies actually move.
        </span>
      </div>

      <div className="mt-5 flex flex-wrap gap-4 text-[13px]">
        <Link href="/a" className="text-accent hover:underline">
          Browse all 19 axes →
        </Link>
        <Link
          href="/a"
          className="text-muted hover:text-ink hover:underline"
        >
          Methodology — why this design
        </Link>
      </div>
    </div>
  );
}

function ExplainStep({
  title,
  body,
}: {
  title: string;
  body: React.ReactNode;
}) {
  return (
    <div className="rounded border border-rule bg-white p-3">
      <div className="mb-1 flex items-center gap-1.5">
        <span className="inline-flex h-[9px] w-[9px] rounded-full bg-accent">
          <span className="sr-only">axis step</span>
        </span>
        <span className="text-[12px] font-semibold uppercase tracking-wider text-muted">
          {title}
        </span>
      </div>
      <div className="text-[13px] leading-[1.5] text-ink">{body}</div>
    </div>
  );
}

const CHANNEL_DESC: Record<string, string> = {
  fiscal:
    "How the state taxes and spends — progressivity, corporate, capital, transfers, spending share, sectoral subsidies.",
  regulatory:
    "Rules outside the budget — labour, product-market, environment, finance, immigration, trade, licensing, energy security.",
  monetary:
    "Central bank independence, monetary expansion direction.",
  institutional:
    "Rule of law, property rights, judicial independence — the rails everything else runs on.",
};

const CHANNEL_COLOR: Record<string, { bg: string; fg: string; ring: string }> = {
  fiscal: { bg: "#eef3fb", fg: "#1f3f63", ring: "#cad8eb" },
  regulatory: { bg: "#f3eef6", fg: "#4d2a5e", ring: "#dccae6" },
  monetary: { bg: "#fdf2e9", fg: "#7a4419", ring: "#ecd2b5" },
  institutional: { bg: "#eef6ef", fg: "#234d2c", ring: "#c8dccc" },
};

function ChannelTag({ channel, count }: { channel: string; count: number }) {
  const c = CHANNEL_COLOR[channel];
  return (
    <Link
      href={`/a#${channel}`}
      className="block rounded border p-2.5 hover:no-underline"
      style={{ background: c.bg, borderColor: c.ring }}
    >
      <div
        className="text-[12px] font-semibold uppercase tracking-wider"
        style={{ color: c.fg }}
      >
        {channel} · {count}
      </div>
      <div className="mt-1 text-[12.5px] leading-[1.45] text-ink">
        {CHANNEL_DESC[channel]}
      </div>
    </Link>
  );
}
