import { loadRepoMarkdown } from "@/lib/content";

export const metadata = {
  title: "Disclosure",
  description:
    "Author priors, conflicts, and structural commitments. The framework does not claim neutrality.",
};

export default async function DisclosurePage() {
  const html = await loadRepoMarkdown("DISCLOSURE.md");
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <div className="prose-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
