import Link from "next/link";

import type { Axis } from "@/lib/content";
import { axisShortLabel, axisDirectionLabel } from "@/lib/content";

export interface AxisMoveLike {
  axis: string;
  direction: string;
  magnitude?: string;
  intended?: boolean;
  rationale?: string;
}

function axisTone(direction: string) {
  if (direction === "+") return { bg: "#dff1e4", fg: "#2c7a4f", symbol: "↑" };
  if (direction === "-") return { bg: "#f3d9d9", fg: "#9e2f2f", symbol: "↓" };
  if (direction === "0") return { bg: "#f3f3f1", fg: "#636363", symbol: "—" };
  if (direction === "mixed")
    return { bg: "#fdf1da", fg: "#b7791f", symbol: "~" };
  return { bg: "#f3f3f1", fg: "#636363", symbol: "?" };
}

export function AxisTile({
  move,
  axisDef,
}: {
  move: AxisMoveLike;
  axisDef?: Axis;
}) {
  const t = axisTone(move.direction);
  const directionMeaning = axisDirectionLabel(axisDef, move.direction);
  return (
    <div className="flex items-start gap-3 rounded border border-rule bg-white p-4">
      <div
        className="flex h-9 w-9 flex-none items-center justify-center rounded text-xl font-bold"
        style={{ background: t.bg, color: t.fg }}
      >
        {t.symbol}
      </div>
      <div className="min-w-0">
        <Link
          href={`/a/${move.axis}`}
          className="text-[13.5px] font-semibold capitalize leading-snug text-ink hover:text-accent hover:no-underline"
        >
          {axisShortLabel(move.axis)} <span aria-hidden className="text-faint">→</span>
        </Link>
        <div className="font-mono text-[11px] text-faint">{move.axis}</div>
        {axisDef?.description && (
          <div className="mt-1 max-w-[420px] text-[12px] leading-[1.5] text-muted">
            {axisDef.description.trim().replace(/\s+/g, " ")}
          </div>
        )}
        <div className="mt-1 text-[11px] uppercase tracking-wider text-muted">
          {move.direction === "+"
            ? "increased"
            : move.direction === "-"
            ? "decreased"
            : move.direction === "0"
            ? "unchanged"
            : "mixed"}
          {move.magnitude && ` · ${move.magnitude}`}
          {move.intended === false && " · unintended"}
        </div>
        {directionMeaning && (
          <div className="mt-1 text-[12px] italic leading-[1.45] text-muted">
            {directionMeaning}
          </div>
        )}
        {move.rationale && (
          <div className="mt-1.5 text-[13px] leading-[1.5] text-ink/80">
            {move.rationale}
          </div>
        )}
      </div>
    </div>
  );
}
