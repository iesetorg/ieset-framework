"use client";

import { useState } from "react";

export function SteelmanBlock({
  html,
  sourcePath,
}: {
  html?: string;
  sourcePath?: string;
}) {
  const [open, setOpen] = useState(false);
  if (!html) return null;
  return (
    <div className="overflow-hidden rounded border border-rule bg-panel">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-5 py-3.5 text-left hover:bg-[#f3f1ec]"
      >
        <div>
          <div className="text-sm font-semibold text-amber">
            {open ? "Hide the steelman" : "Open the steelman"}
          </div>
          {sourcePath && (
            <div className="mt-0.5 text-xs text-muted">{sourcePath}</div>
          )}
        </div>
        <span className="text-xs text-muted">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div
          className="prose-body border-t border-rule px-6 pb-3 pt-5 text-[14.5px]"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )}
    </div>
  );
}
