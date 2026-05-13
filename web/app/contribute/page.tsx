import { loadRepoMarkdown } from "@/lib/content";

export const metadata = {
  title: "Contribute",
  description:
    "How to challenge, repair, or extend IESET with specific evidence, code, and mapping corrections.",
};

export default async function ContributePage() {
  const html = await loadRepoMarkdown("CONTRIBUTING.md");
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <div className="prose-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
