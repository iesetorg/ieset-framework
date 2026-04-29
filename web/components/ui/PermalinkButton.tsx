"use client";

import { useState } from "react";

export function PermalinkButton({
  url,
  label = "Copy permalink",
}: {
  url: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(url);
          setCopied(true);
          setTimeout(() => setCopied(false), 1800);
        } catch {
          // no-op
        }
      }}
      className="block w-full rounded border border-rule-strong bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-panel"
    >
      {copied ? "copied" : label}
    </button>
  );
}
