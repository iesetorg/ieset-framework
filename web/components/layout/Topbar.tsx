import Link from "next/link";

import { NavDropdown, type NavDropdownItem } from "./NavDropdown";

const LIBRARY: NavDropdownItem[] = [
  {
    href: "/h",
    label: "Hypotheses",
    blurb: "Pre-registered tests with falsification rules",
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
    blurb: "The six invariants the framework commits to",
  },
];

export function Topbar() {
  return (
    <header className="sticky top-0 z-10 border-b border-rule bg-white px-8 py-4">
      <div className="mx-auto flex max-w-content items-baseline justify-between">
        <Link
          href="/"
          className="text-[17px] font-bold tracking-tight text-ink hover:no-underline"
        >
          IESET<span className="text-accent">.</span>
        </Link>
        <nav className="text-sm">
          {/* Flagship dashboards first — these are the things to look at */}
          <Link
            href="/how-it-works"
            className="ml-6 font-medium text-muted hover:text-ink hover:no-underline"
          >
            How it works
          </Link>
          <Link
            href="/scoreboard"
            className="ml-6 font-medium text-muted hover:text-ink hover:no-underline"
          >
            Scoreboard
          </Link>
          <Link
            href="/policy-browser"
            className="ml-6 font-medium text-muted hover:text-ink hover:no-underline"
          >
            Policy Browser
          </Link>
          <Link
            href="/atlas"
            className="ml-6 font-medium text-muted hover:text-ink hover:no-underline"
          >
            Atlas
          </Link>
          <NavDropdown label="Library" items={LIBRARY} />
          <NavDropdown label="Explore" items={EXPLORE} />
          <NavDropdown label="About" items={ABOUT} align="right" />
        </nav>
      </div>
    </header>
  );
}
