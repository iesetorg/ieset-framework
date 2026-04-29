import type { RunArtifacts } from "@/lib/content";
import { verdictTone, verdictShort } from "@/lib/verdict";

const toneClasses = {
  green: { bar: "bg-green", tag: "bg-green-soft text-green", head: "text-green" },
  amber: { bar: "bg-amber", tag: "bg-amber-soft text-amber", head: "text-amber" },
  red: { bar: "bg-red", tag: "bg-red-soft text-red", head: "text-red" },
  muted: { bar: "bg-faint", tag: "bg-code-bg text-muted", head: "text-muted" },
} as const;

const toneHelp: Record<"green" | "amber" | "red" | "muted", string> = {
  green:
    "The data ran in the direction predicted and crossed the pre-registered threshold.",
  amber:
    "Mixed evidence — some predictions held, others did not. The full claim is not established.",
  red:
    "The data ran against the prediction or failed the pre-registered threshold.",
  muted: "Result card produced; verdict unclassified.",
};

export function ResultBanner({ run }: { run: RunArtifacts }) {
  if (!run.exists) {
    return (
      <div className="mb-8 rounded border border-rule bg-panel px-5 py-4">
        <div className="flex items-center gap-3 text-sm">
          <span className="inline-flex items-center rounded-sm bg-code-bg px-2 py-[3px] text-xs font-medium uppercase tracking-wider text-muted">
            run pending
          </span>
          <span className="text-muted">
            The hypothesis is pre-registered in git. The model has not yet run; no coefficients to display. Chart shows the outcome variables' raw trajectories.
          </span>
        </div>
      </div>
    );
  }

  const tone = verdictTone(run.verdict);
  const cls = toneClasses[tone];
  const label = verdictShort(run.verdict).toUpperCase();

  return (
    <div className="mb-8 overflow-hidden rounded border border-rule bg-white">
      <div className={`flex items-stretch ${cls.bar}`} style={{ height: 4 }} />
      <div className="px-5 py-4">
        <div className="mb-2 flex items-center gap-3">
          <span className={`inline-flex items-center rounded-sm px-2 py-[3px] text-xs font-semibold uppercase tracking-wider ${cls.tag}`}>
            {label}
          </span>
          <span className="font-mono text-[11px] text-muted">
            {run.run_dir_rel}
          </span>
        </div>
        <p className={`m-0 text-[15px] leading-[1.55] ${cls.head}`}>
          {run.verdict ?? "Result card available."}
        </p>
        <p className="mt-2 text-[12.5px] leading-[1.5] text-muted">
          <span className="sc mr-1.5 text-[10px]">what this means</span>
          {toneHelp[tone]}
        </p>
      </div>
    </div>
  );
}
