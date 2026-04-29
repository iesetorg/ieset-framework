import Link from "next/link";

import type { Axis } from "@/lib/content";

/**
 * Inline chip representing one of the 19 canonical policy-content axes.
 *
 * Use this anywhere an axis ID would otherwise appear as bare text. It:
 *  - shows the human-friendly short label ("transfer expansion") instead of
 *    the raw id ("fiscal.transfer_expansion")
 *  - tags the channel via colour
 *  - encodes the direction (+/−/0/mixed) as a glyph if provided
 *  - shows the in-corpus definition + direction semantics on hover, so a
 *    reader never has to leave the page to learn what the axis means
 *  - links to /a/<id> for the full axis page
 */

const CHANNEL_COLOR: Record<string, { bg: string; fg: string; ring: string }> = {
  fiscal: { bg: "#eef3fb", fg: "#1f3f63", ring: "#cad8eb" },
  regulatory: { bg: "#f3eef6", fg: "#4d2a5e", ring: "#dccae6" },
  monetary: { bg: "#fdf2e9", fg: "#7a4419", ring: "#ecd2b5" },
  institutional: { bg: "#eef6ef", fg: "#234d2c", ring: "#c8dccc" },
};

function chipColor(channel: string): { bg: string; fg: string; ring: string } {
  return CHANNEL_COLOR[channel] ?? { bg: "#f3f3f1", fg: "#444", ring: "#dcdad4" };
}

function dirGlyph(d: string | undefined): string {
  if (d === "+") return "↑";
  if (d === "-") return "↓";
  if (d === "mixed") return "~";
  if (d === "0") return "—";
  return "";
}

function dirTone(d: string | undefined): { bg: string; fg: string } | null {
  if (d === "+") return { bg: "#dff1e4", fg: "#2c7a4f" };
  if (d === "-") return { bg: "#f3d9d9", fg: "#9e2f2f" };
  if (d === "mixed") return { bg: "#fdf1da", fg: "#b7791f" };
  if (d === "0") return { bg: "#f3f3f1", fg: "#636363" };
  return null;
}

function shortLabel(id: string): string {
  return id.split(".").slice(-1)[0].replace(/_/g, " ");
}

export interface AxisChipProps {
  axisId: string;
  axisDef?: Axis;
  direction?: string;
  /** When true, omit the channel colour pill and render minimal — for use inside dense tables. */
  minimal?: boolean;
  /** When true, hide the hover explainer (e.g. when the surrounding card already explains). */
  noExplain?: boolean;
}

export function AxisChip({
  axisId,
  axisDef,
  direction,
  minimal = false,
  noExplain = false,
}: AxisChipProps) {
  const channel = axisDef?.channel ?? axisId.split(".")[0];
  const color = chipColor(channel);
  const label = shortLabel(axisId);
  const dt = dirTone(direction);
  const dirText =
    direction && axisDef?.direction_semantics?.[direction]
      ? axisDef.direction_semantics[direction]
      : undefined;

  return (
    <span className="group relative inline-flex">
      <Link
        href={`/a/${axisId}`}
        className="inline-flex items-center gap-1.5 rounded px-1.5 py-[2px] text-[12px] font-medium leading-snug ring-1 ring-inset hover:no-underline"
        style={
          minimal
            ? { color: color.fg }
            : { background: color.bg, color: color.fg, borderColor: color.ring }
        }
      >
        {/* channel dot */}
        {!minimal && (
          <span
            className="inline-block h-[5px] w-[5px] rounded-full"
            style={{ background: color.fg }}
            aria-hidden
          />
        )}
        <span className="capitalize">{label}</span>
        {direction && dt && (
          <span
            className="ml-0.5 inline-flex h-[16px] w-[16px] items-center justify-center rounded-sm text-[10px] font-bold leading-none"
            style={{ background: dt.bg, color: dt.fg }}
            title={`direction: ${direction}`}
            aria-label={`direction ${direction}`}
          >
            {dirGlyph(direction)}
          </span>
        )}
      </Link>

      {/* hover explainer */}
      {!noExplain && axisDef && (
        <span
          role="tooltip"
          className="pointer-events-none invisible absolute left-0 top-full z-20 mt-1 w-[320px] rounded border border-rule-strong bg-white p-3 text-[12.5px] leading-[1.5] text-ink opacity-0 shadow-lg transition-opacity group-hover:visible group-hover:opacity-100"
        >
          <div className="mb-1 flex items-center gap-2">
            <span
              className="rounded px-1.5 py-[1px] text-[10px] font-semibold uppercase tracking-wider"
              style={{ background: color.bg, color: color.fg }}
            >
              {channel}
            </span>
            <span className="font-mono text-[10.5px] text-faint">{axisId}</span>
          </div>
          {axisDef.description && (
            <p className="m-0 mb-2 text-[12.5px] text-muted">
              {axisDef.description.trim().replace(/\s+/g, " ")}
            </p>
          )}
          {axisDef.direction_semantics && (
            <ul className="m-0 list-none space-y-0.5 p-0 text-[12px]">
              {Object.entries(axisDef.direction_semantics).map(([d, m]) => {
                const t = dirTone(d) ?? { bg: "#f3f3f1", fg: "#444" };
                return (
                  <li key={d} className="flex items-start gap-1.5">
                    <span
                      className="mt-[2px] inline-flex h-[14px] w-[14px] flex-none items-center justify-center rounded-sm text-[10px] font-bold leading-none"
                      style={{ background: t.bg, color: t.fg }}
                    >
                      {dirGlyph(d)}
                    </span>
                    <span className="text-ink">{m}</span>
                  </li>
                );
              })}
            </ul>
          )}
          {direction && dirText && (
            <div
              className="mt-2 rounded p-2 text-[12px]"
              style={{ background: dt?.bg, color: dt?.fg }}
            >
              <span className="font-semibold">This case:</span> {dirText}
            </div>
          )}
        </span>
      )}
    </span>
  );
}
