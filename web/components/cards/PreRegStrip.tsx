import type { Hypothesis } from "@/lib/types";
import type { RunArtifacts } from "@/lib/content";
import { githubCommitUrl, shortCommit } from "@/lib/site";

function formatIso(iso: string | undefined | null): string {
  if (!iso) return "—";
  try {
    // Prefer the recorded string when already ISO-ish; normalise to UTC label.
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toISOString().replace(/\.\d{3}Z$/, "Z");
  } catch {
    return iso;
  }
}

export function PreRegStrip({
  hypothesis,
  run,
}: {
  hypothesis: Hypothesis;
  run?: RunArtifacts;
}) {
  const commit = hypothesis._first_commit;
  const verified = hypothesis._registration_status === "verified";
  const legacy = hypothesis._registration_status === "legacy_same_commit";
  const short = shortCommit(commit?.hash);
  const commitHref = commit?.hash ? githubCommitUrl(commit.hash) : null;

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
          {commitHref ? (
            <>
              spec commit{" "}
              <a
                href={commitHref}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent underline hover:no-underline"
                title="First git commit that introduced this hypothesis spec"
              >
                {short}
              </a>
              {" · "}
              {formatIso(commit?.iso)}
            </>
          ) : (
            "commit pending — not yet in git history"
          )}
        </div>
        {(run?.generated_at || run?.run_first_commit) && (
          <div className="mt-1 font-mono text-[12px] text-muted">
            {run.run_first_commit?.hash ? (
              <>
                first run commit{" "}
                <a
                  href={githubCommitUrl(run.run_first_commit.hash)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent underline hover:no-underline"
                >
                  {shortCommit(run.run_first_commit.hash)}
                </a>
                {run.run_first_commit.iso
                  ? ` · ${formatIso(run.run_first_commit.iso)}`
                  : ""}
              </>
            ) : null}
            {run.generated_at ? (
              <>
                {run.run_first_commit?.hash ? " · " : ""}
                result generated {formatIso(run.generated_at)}
              </>
            ) : null}
          </div>
        )}
        <p className="mt-2 m-0 text-[12.5px] leading-snug text-muted">
          The hash is the{" "}
          <strong className="font-medium text-ink">first commit that added
          this spec file</strong>
          — not the repository HEAD. Verified status requires that commit to be
          a strict git ancestor of the first run-artifact commit.
        </p>
      </div>
    </div>
  );
}
