import Link from "next/link";

import { loadAllPositions, loadAxes } from "@/lib/content";
import { axesForPosition } from "@/lib/matching";
import { AxisChip } from "@/components/badges/AxisChip";
import { Badge } from "@/components/badges/Badge";
import type { PositionStatus } from "@/lib/types";

export const metadata = {
  title: "Positions",
  description:
    "Schools of economic thought whose specific, falsifiable predictions are pinned to registry hypotheses. Cited, not endorsed.",
};

export default async function PositionsIndex() {
  const [all, axesMap] = await Promise.all([loadAllPositions(), loadAxes()]);
  // Resolve top axes per position in parallel — the index is small enough.
  const axesByPosition = await Promise.all(
    all.map(async (p) => ({
      id: p.position_id,
      axes: (await axesForPosition(p.position_id)).slice(0, 6),
    }))
  );
  const axesIndex = new Map(axesByPosition.map((r) => [r.id, r.axes]));

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[32px] font-semibold tracking-[-0.02em]">
        Positions
      </h1>
      <p className="mb-6 max-w-[780px] text-[17px] text-muted">
        Economic schools of thought — Austrian, post-Keynesian, MMT, empirical
        pragmatist, and others — each pinned to the specific, falsifiable
        predictions it makes. The framework cites these positions; it does not
        endorse any. Each school&apos;s predictions are tested independently
        against the registry&apos;s hypotheses, with registration status shown
        per record.
      </p>

      {/* CHANNEL LEGEND */}
      <div className="mb-6 flex flex-wrap items-center gap-3 text-[11px] text-muted">
        <span className="sc text-[10px]">channel</span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[10px] w-[10px] rounded-sm"
            style={{ background: "#eef3fb", border: "1px solid #cad8eb" }}
          />
          fiscal
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[10px] w-[10px] rounded-sm"
            style={{ background: "#f3eef6", border: "1px solid #dccae6" }}
          />
          regulatory
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[10px] w-[10px] rounded-sm"
            style={{ background: "#fdf2e9", border: "1px solid #ecd2b5" }}
          />
          monetary
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[10px] w-[10px] rounded-sm"
            style={{ background: "#eef6ef", border: "1px solid #c8dccc" }}
          />
          institutional
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule">
              <th className="p-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                School
              </th>
              <th className="p-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                Status
              </th>
              <th className="p-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                Axes spoken to
              </th>
              <th className="p-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-muted">
                Linked H
              </th>
            </tr>
          </thead>
          <tbody>
            {all.map((p) => {
              const axes = axesIndex.get(p.position_id) ?? [];
              return (
                <tr
                  key={p.position_id}
                  className="border-b border-rule hover:bg-panel"
                >
                  <td className="p-2.5 align-top">
                    <Link
                      href={`/pos/${p.position_id}`}
                      className="font-medium text-ink"
                    >
                      {p.school}
                    </Link>
                    <div className="mt-0.5 font-mono text-[11px] text-faint">
                      {p.position_id}
                    </div>
                  </td>
                  <td className="p-2.5 align-top">{statusBadge(p.status)}</td>
                  <td className="p-2.5 align-top">
                    <div className="flex flex-wrap gap-1">
                      {axes.length === 0 ? (
                        <span className="text-[11.5px] text-faint">—</span>
                      ) : (
                        axes.map((t) => (
                          <AxisChip
                            key={t.axis}
                            axisId={t.axis}
                            axisDef={axesMap[t.axis]}
                            noExplain
                          />
                        ))
                      )}
                    </div>
                  </td>
                  <td className="p-2.5 text-right align-top tabular-nums text-muted">
                    {(p.falsifiable_specific_claims ?? []).filter(
                      (c) => !!c.linked_hypothesis_id
                    ).length}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function statusBadge(status: PositionStatus) {
  if (status === "published") return <Badge variant="green" dot>published</Badge>;
  if (status === "candidate") return <Badge variant="amber" dot>candidate</Badge>;
  return <Badge variant="muted" dot>draft</Badge>;
}
