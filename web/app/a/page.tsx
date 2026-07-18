import Link from "next/link";

import { loadAllAxes } from "@/lib/content";
import { loadAllPolicies } from "@/lib/policies";
import { AxesExplainer } from "@/components/explainers/AxesExplainer";

export const metadata = {
  title: "Axes",
  description:
    "Channel-separated policy-content axes. Every policy and movement is coded on these axes; the axis browser is the entry point for finding historical policy analogues.",
  alternates: { canonical: "https://framework.ieset.org/a/" },
};

const CHANNEL_ORDER = ["fiscal", "regulatory", "monetary", "institutional"];

function channelLabel(c: string): string {
  return c.charAt(0).toUpperCase() + c.slice(1);
}

export default async function AxesIndex() {
  const axes = await loadAllAxes();
  const policies = await loadAllPolicies();

  // Count policies per axis
  const axisCounts = new Map<string, number>();
  for (const p of policies) {
    for (const a of p.axes_moved ?? []) {
      axisCounts.set(a.axis, (axisCounts.get(a.axis) ?? 0) + 1);
    }
  }

  const byChannel = new Map<string, typeof axes>();
  for (const a of axes) {
    const list = byChannel.get(a.channel) ?? [];
    list.push(a);
    byChannel.set(a.channel, list);
  }

  const orderedChannels = [
    ...CHANNEL_ORDER.filter((c) => byChannel.has(c)),
    ...[...byChannel.keys()].filter((c) => !CHANNEL_ORDER.includes(c)),
  ];

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-accent">
        the framework&apos;s spine
      </div>
      <h1 className="mb-3 text-[30px] font-semibold tracking-[-0.02em] md:text-[34px]">
        Axes — how the framework scores policy content
      </h1>
      <p className="mb-8 max-w-[780px] text-[17px] leading-[1.55] text-muted">
        Pick any axis below to see every policy that moved it — direction by
        direction, country by country. This is the substrate the rest of the
        site rides on: hypotheses test outcomes downstream of axis movements,
        positions get scored on whether their predictions about each axis hold
        up, and movements are fingerprinted by which axes they shifted.
      </p>

      <div className="mb-10">
        <AxesExplainer variant="full" />
      </div>

      <h2 className="mb-4 text-[22px] font-semibold tracking-[-0.01em]">
        The 19 axes, grouped by channel
      </h2>

      {orderedChannels.map((channel) => (
        <section key={channel} id={channel} className="mb-10 scroll-mt-20">
          <h2 className="mb-4 border-b border-rule pb-2 text-[14px] font-semibold uppercase tracking-wider text-muted">
            {channelLabel(channel)}
          </h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {byChannel.get(channel)!.map((a) => {
              const count = axisCounts.get(a.id) ?? 0;
              return (
                <Link
                  key={a.id}
                  href={`/a/${a.id}`}
                  className="group block rounded border border-rule bg-white p-4 hover:border-rule-strong hover:no-underline"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="text-[14.5px] font-semibold capitalize leading-snug text-ink group-hover:text-accent">
                        {a.id
                          .split(".")
                          .slice(-1)[0]
                          .replace(/_/g, " ")}
                      </div>
                      <div className="mt-0.5 font-mono text-[11px] text-faint">
                        {a.id}
                      </div>
                    </div>
                    <div className="flex-none tabular-nums text-[12px] text-muted">
                      {count} {count === 1 ? "policy" : "policies"}
                    </div>
                  </div>
                  {a.description && (
                    <p className="m-0 mt-2 text-[13px] leading-[1.5] text-muted">
                      {a.description.trim().replace(/\s+/g, " ").slice(0, 180)}
                      {a.description.length > 180 ? "…" : ""}
                    </p>
                  )}
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
