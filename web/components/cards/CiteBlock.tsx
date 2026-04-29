"use client";

import { useState } from "react";

export function CiteBlock({
  permalink,
  bibtex,
  replicationHref,
}: {
  permalink: string;
  bibtex: string;
  replicationHref?: string;
}) {
  const [copied, setCopied] = useState<"url" | "bibtex" | null>(null);

  const copy = async (value: string, which: "url" | "bibtex") => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(which);
      setTimeout(() => setCopied(null), 1800);
    } catch {
      // no-op
    }
  };

  return (
    <div className="mb-3.5 rounded border border-rule bg-white p-4">
      <h3 className="sc mb-3 !mt-0">Cite</h3>
      <div className="mb-2 break-all rounded bg-code-bg p-2 font-mono text-[11px] leading-snug text-muted">
        {permalink}
      </div>
      <button
        onClick={() => copy(permalink, "url")}
        className="mb-2 block w-full rounded border border-rule-strong bg-white px-3 py-2 text-xs font-medium text-ink hover:bg-panel"
      >
        {copied === "url" ? "copied" : "Copy permalink"}
      </button>
      <button
        onClick={() => copy(bibtex, "bibtex")}
        className="mb-2 block w-full rounded border border-rule-strong bg-white px-3 py-2 text-xs font-medium text-ink hover:bg-panel"
      >
        {copied === "bibtex" ? "copied" : "Copy BibTeX"}
      </button>
      {replicationHref && (
        <a
          href={replicationHref}
          className="block w-full rounded border border-rule-strong bg-white px-3 py-2 text-center text-xs font-medium text-ink hover:bg-panel hover:no-underline"
        >
          Open replication notebook
        </a>
      )}
    </div>
  );
}
