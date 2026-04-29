"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export interface NavDropdownItem {
  href: string;
  label: string;
  blurb?: string;
}

/**
 * Dropdown that opens on hover via CSS `group-hover` (no JS timer logic),
 * with a padded wrapper that extends the hover region past the button's
 * text bounds so the cursor can travel down to the panel without the hover
 * state lapsing. Also opens on click for keyboard / mobile use.
 *
 * Design notes:
 * - The wrapper has `pb-4` (padding-bottom) so its bounding box reaches
 *   past the button's baseline. The panel is positioned `absolute top-full`,
 *   which means it starts at the wrapper's bottom edge — i.e. inside the
 *   padded hover region. The cursor never crosses dead space.
 * - We do NOT use mouseenter/mouseleave handlers; CSS handles the open
 *   state. The `useState` open flag is only for click-toggle (accessibility).
 *   Because both CSS hover AND state-driven open exist, the panel shows
 *   when EITHER fires.
 */
export function NavDropdown({
  label,
  items,
  align = "left",
}: {
  label: string;
  items: NavDropdownItem[];
  align?: "left" | "right";
}) {
  const [clicked, setClicked] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click-outside or Escape (only relevant when click-opened)
  useEffect(() => {
    if (!clicked) return;
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setClicked(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setClicked(false);
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [clicked]);

  const panelClasses = [
    "absolute top-full z-20 w-[300px] overflow-hidden rounded border border-rule bg-white shadow-lg",
    align === "right" ? "right-0" : "left-0",
    // Hidden by default; revealed by parent's group-hover OR by clicked state.
    "invisible opacity-0 transition-opacity",
    "group-hover:visible group-hover:opacity-100",
    clicked ? "!visible !opacity-100" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={ref} className="group relative inline-block pb-4">
      <button
        type="button"
        onClick={() => setClicked((v) => !v)}
        aria-expanded={clicked}
        aria-haspopup="true"
        className="ml-6 inline-flex items-center gap-1 font-medium text-muted hover:text-ink group-hover:text-ink"
      >
        {label}
        <svg
          width="10"
          height="10"
          viewBox="0 0 10 10"
          aria-hidden
          className="transition-transform group-hover:rotate-180"
        >
          <path
            d="M2 4 L5 7 L8 4"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </button>

      <div role="menu" className={panelClasses}>
        <ul className="m-0 list-none p-1">
          {items.map((item) => (
            <li key={item.href} role="none">
              <Link
                href={item.href}
                role="menuitem"
                onClick={() => setClicked(false)}
                className="block rounded px-3 py-2 text-[13px] hover:bg-panel hover:no-underline"
              >
                <div className="font-medium text-ink">{item.label}</div>
                {item.blurb && (
                  <div className="mt-0.5 text-[11.5px] leading-snug text-muted">
                    {item.blurb}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
