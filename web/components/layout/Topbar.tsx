import Link from "next/link";

import { NavDropdown, type NavDropdownItem } from "./NavDropdown";

const LIBRARY: NavDropdownItem[] = [
  {
    href: "/h",
    label: "Hypotheses",
    blurb: "Registered tests with explicit verification status",
  },
  {
    href: "/p",
    label: "Policies",
    blurb: "Specific reforms coded on channel-separated axes",
  },
  {
    href: "/m",
    label: "Movements",
    blurb: "Governments coded by what they actually did",
  },
  {
    href: "/pos",
    label: "Positions",
    blurb: "Schools of thought + their predictions",
  },
  {
    href: "/a",
    label: "Axes",
    blurb: "The standard policy levers everything is coded on",
  },
];

const EXPLORE: NavDropdownItem[] = [
  {
    href: "/scoreboard",
    label: "Scoreboard",
    blurb: "Schools of thought scored against tested predictions",
  },
  {
    href: "/evidence",
    label: "Evidence quality",
    blurb: "Tiers, estimator exclusions, reference set, and review status",
  },
  {
    href: "/atlas",
    label: "Atlas",
    blurb: "Movements and policy trajectories across countries",
  },
  {
    href: "/drift",
    label: "Drift",
    blurb: "How movements move on the policy axes over time",
  },
  {
    href: "/c",
    label: "Conditions",
    blurb: "Conditional taxonomy of when markets vs intervention favour",
  },
];

const ABOUT: NavDropdownItem[] = [
  {
    href: "/methodology",
    label: "Methodology",
    blurb: "The integrity invariants the framework commits to",
  },
  {
    href: "/methods-paper",
    label: "Methods paper",
    blurb: "Working paper on design, failure modes, and limitations",
  },
  {
    href: "/production",
    label: "Production",
    blurb: "How the corpus is built — LLM-assisted, human-directed",
  },
  {
    href: "/disclosure",
    label: "Transparency",
    blurb: "Author perspective and audit commitments",
  },
  {
    href: "/updates",
    label: "Updates",
    blurb: "Public changelog and integrity notes",
  },
  {
    href: "/contribute",
    label: "Contribute",
    blurb: "How to challenge, repair, or extend the framework",
  },
  {
    href: "/terms",
    label: "Terms",
    blurb: "Use, contribution, and research limitations",
  },
  {
    href: "/privacy",
    label: "Privacy",
    blurb: "Visitor, contribution, and provenance data handling",
  },
];

export function Topbar() {
  return (
    <header className="sticky top-0 z-10 border-b border-rule bg-white px-8 py-4">
      <div className="mx-auto flex max-w-content flex-wrap items-baseline justify-between gap-x-6 gap-y-3">
        <Link
          href="/"
          className="text-[17px] font-bold tracking-tight text-ink hover:no-underline"
        >
          IESET<span className="text-accent">.</span>
        </Link>
        <nav aria-label="Main navigation" className="relative flex w-full min-w-0 flex-wrap items-baseline gap-x-6 gap-y-2 text-sm lg:w-auto">
          {/* Flagship dashboards first — these are the things to look at */}
          <Link
            href="/how-it-works"
            className="font-medium text-muted hover:text-ink hover:no-underline"
          >
            How it works
          </Link>
          <Link
            href="/policy-browser"
            className="font-medium text-muted hover:text-ink hover:no-underline"
          >
            Policy Browser
          </Link>
          <Link
            href="/h"
            className="font-medium text-muted hover:text-ink hover:no-underline"
          >
            Hypotheses
          </Link>
          <NavDropdown label="Library" items={LIBRARY} />
          <NavDropdown label="Explore" items={EXPLORE} />
          <NavDropdown label="About" items={ABOUT} align="right" />
        </nav>
      </div>
    </header>
  );
}
