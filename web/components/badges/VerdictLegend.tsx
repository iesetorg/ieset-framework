const ITEMS: { dot: string; label: string; help: string }[] = [
  {
    dot: "bg-green",
    label: "supported",
    help: "data ran as predicted, cleared threshold",
  },
  {
    dot: "bg-amber",
    label: "partial / mixed",
    help: "some predictions held, others didn't",
  },
  {
    dot: "bg-red",
    label: "refuted / weakened",
    help: "data ran opposite or failed threshold",
  },
  {
    dot: "bg-faint",
    label: "run pending",
    help: "registered, model not yet fired",
  },
];

export function VerdictLegend({
  compact = false,
}: {
  compact?: boolean;
}) {
  return (
    <div
      className={`flex flex-wrap items-center gap-x-5 gap-y-2 rounded border border-rule bg-panel px-4 py-2.5 ${
        compact ? "text-[11.5px]" : "text-[12.5px]"
      }`}
    >
      <span className="sc mr-1 text-[10px]">verdict key</span>
      {ITEMS.map((it) => (
        <span key={it.label} className="inline-flex items-center gap-1.5">
          <span className={`h-[8px] w-[8px] rounded-full ${it.dot}`} />
          <span className="font-medium text-ink">{it.label}</span>
          {!compact && (
            <span className="text-muted">— {it.help}</span>
          )}
        </span>
      ))}
    </div>
  );
}
