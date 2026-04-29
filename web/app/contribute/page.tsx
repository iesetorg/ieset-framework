import { loadRepoMarkdown } from "@/lib/content";

export const metadata = {
  title: "Contribute",
  description:
    "Adversarial review protocol. Reviewers with priors different from the author's are the most valuable contributors.",
};

export default async function ContributePage() {
  const html = await loadRepoMarkdown("CONTRIBUTING.md");
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <div className="prose-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
