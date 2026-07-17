import type { Hypothesis } from "@/lib/types";

export function PreRegStrip({ hypothesis }: { hypothesis: Hypothesis }) {
  const commit = hypothesis._first_commit;
  const verified = hypothesis._registration_status === "verified";
  const legacy = hypothesis._registration_status === "legacy_same_commit";
  return (
    <div
      className={`mb-5 rounded px-5 py-3.5 ${
        verified ? "bg-green-soft" : "bg-amber-50"
      }`}
    >
      <div>
        <div
          className={`sc text-[11px] font-semibold tracking-[0.08em] ${
            verified ? "text-green" : "text-amber-700"
          }`}
        >
          {verified
            ? "pre-registration verified"
            : legacy
              ? "legacy same-commit record — not verified"
              : "registration record"}
        </div>
        <div className="mt-0.5 font-mono text-[13px] text-ink">
          {commit
            ? `commit ${commit.hash} · ${new Date(commit.iso)
                .toISOString()
                .slice(0, 19)}Z`
            : "commit pending — not yet in git history"}
        </div>
      </div>
    </div>
  );
}
