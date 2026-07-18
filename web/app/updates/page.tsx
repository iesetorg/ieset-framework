import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Updates",
  description:
    "Public log of methodology notes, integrity fixes, and corpus status changes for IESET.",
  alternates: { canonical: "https://framework.ieset.org/updates/" },
};

const UPDATES: Array<{
  date: string;
  title: string;
  body: string;
  hrefs?: Array<{ label: string; href: string }>;
}> = [
  {
    date: "2026-07-18",
    title: "Public surface scrub + legitimacy plumbing",
    body: "Private operator automation removed from the public repository. Hypothesis pages now deep-link the first spec commit (not HEAD), expose run timing, and ship OG/JSON-LD metadata. Added /production disclosure, robots/sitemap/llms.txt, and a single stats.json census endpoint.",
    hrefs: [
      { label: "Production method", href: "/production/" },
      { label: "stats.json", href: "/stats.json" },
    ],
  },
  {
    date: "2026-07-17",
    title: "Corpus census and registration labels",
    body: "Machine-readable engine/public_corpus_census.json became the authoritative count source. Historical same-commit registrations remain inspectable as legacy_same_commit; only verified topology receives public-index credit.",
    hrefs: [
      { label: "Methodology", href: "/methodology/" },
      { label: "Contribute / review pilot", href: "/contribute/" },
    ],
  },
  {
    date: "2026-04-29",
    title: "Framework launch",
    body: "Initial public release of the pre-registration-first hypothesis library, axis vocabulary, and scoreboard.",
  },
];

export default function UpdatesPage() {
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <div className="mb-2 flex items-baseline justify-between gap-4">
        <p className="m-0 text-[12px] font-semibold uppercase tracking-wider text-muted">
          Changelog
        </p>
        <a
          href="/feed.xml"
          className="text-[13px] text-accent underline hover:no-underline"
        >
          RSS feed
        </a>
      </div>
      <h1 className="m-0 text-[34px] font-semibold tracking-[-0.02em]">
        Updates
      </h1>
      <p className="mt-4 text-[16px] leading-[1.55] text-muted">
        Methodology changes, integrity notes, and public-surface status. This
        page is the present-tense home of the accountability log referenced in
        the methodology.
      </p>

      <ol className="mt-10 m-0 list-none space-y-8 p-0">
        {UPDATES.map((u) => (
          <li
            key={u.date + u.title}
            className="border-t border-rule pt-6 first:border-t-0 first:pt-0"
          >
            <div className="font-mono text-[12px] text-muted">{u.date}</div>
            <h2 className="mt-1 m-0 text-[18px] font-semibold text-ink">
              {u.title}
            </h2>
            <p className="mt-2 m-0 text-[15px] leading-[1.65] text-ink">
              {u.body}
            </p>
            {u.hrefs && u.hrefs.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-3 text-[13px]">
                {u.hrefs.map((h) => (
                  <Link
                    key={h.href}
                    href={h.href}
                    className="text-accent underline hover:no-underline"
                  >
                    {h.label} →
                  </Link>
                ))}
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
