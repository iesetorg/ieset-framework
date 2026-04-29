import Link from "next/link";

import { loadAllConditions } from "@/lib/content";
import { Badge } from "@/components/badges/Badge";
import type { Condition, ConditionConfidence } from "@/lib/types";

export const metadata = {
  title: "Conditions",
  description:
    "The IESET conditional taxonomy — when markets work, when intervention works, when distributional considerations change the verdict, and specific institutional models.",
};

const CATEGORY_ORDER: Condition["category"][] = [
  "conditions_favoring_markets",
  "conditions_favoring_intervention",
  "conditions_with_distributional_considerations",
  "conditions_specific_institutional_models",
];

export default async function ConditionsIndex() {
  const all = await loadAllConditions();

  const byCategory = new Map<Condition["category"], Condition[]>();
  for (const c of all) {
    const list = byCategory.get(c.category) ?? [];
    list.push(c);
    byCategory.set(c.category, list);
  }

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[32px] font-semibold tracking-[-0.02em]">
        Conditions
      </h1>
      <p className="mb-8 max-w-[780px] text-[17px] text-muted">
        The conditional taxonomy states when markets work, when intervention
        works, when distributional considerations change the verdict, and the
        specific institutional models that operate outside the
        market/intervention dichotomy. Entries link to the hypotheses that
        furnish their empirical evidence.
      </p>

      <div className="mb-6 flex flex-wrap gap-2 text-[13px]">
        <span className="text-muted">Filter by category:</span>
        {CATEGORY_ORDER.map((cat) => (
          <a
            key={cat}
            href={`#${cat}`}
            className="rounded border border-rule px-2.5 py-1 text-ink hover:border-accent hover:text-accent hover:no-underline"
          >
            {categoryLabel(cat)}
          </a>
        ))}
      </div>

      {CATEGORY_ORDER.map((cat) => {
        const items = byCategory.get(cat) ?? [];
        if (items.length === 0) return null;
        return (
          <section id={cat} key={cat} className="mb-10 scroll-mt-24">
            <h2 className="sc mb-3">{categoryLabel(cat)}</h2>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-rule">
                    <th className="p-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                      Entry
                    </th>
                    <th className="p-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                      Confidence
                    </th>
                    <th className="p-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                      Linked hypotheses
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((c) => (
                    <tr
                      key={c.id}
                      className="border-b border-rule hover:bg-panel"
                    >
                      <td className="p-2.5 align-top">
                        <Link
                          href={`/c/${c.id}`}
                          className="font-medium text-ink"
                        >
                          {humanName(c.id)}
                        </Link>
                        <div className="mt-0.5 font-mono text-[11px] text-faint">
                          {c.id}
                        </div>
                      </td>
                      <td className="p-2.5 align-top">
                        <Badge variant={confidenceVariant(c.confidence)} dot>
                          {c.confidence.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="p-2.5 align-top text-muted">
                        {c.linked_hypotheses?.length ?? 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
    </div>
  );
}

function humanName(id: string): string {
  const words = id.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function categoryLabel(cat: Condition["category"]): string {
  switch (cat) {
    case "conditions_favoring_markets":
      return "Conditions favoring markets";
    case "conditions_favoring_intervention":
      return "Conditions favoring intervention";
    case "conditions_with_distributional_considerations":
      return "Distributional considerations";
    case "conditions_specific_institutional_models":
      return "Specific institutional models";
  }
}

function confidenceVariant(
  c: ConditionConfidence
): "green" | "amber" | "muted" | "accent" {
  if (c === "high") return "green";
  if (c === "medium_high") return "accent";
  if (c === "medium") return "amber";
  return "muted";
}
