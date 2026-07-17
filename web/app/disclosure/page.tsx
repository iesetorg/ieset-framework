import { loadRepoMarkdown } from "@/lib/content";

export const metadata = {
  title: "Transparency",
  description:
    "The methodological commitments and known limitations that keep IESET auditable.",
};

export default async function DisclosurePage() {
  const html = await loadRepoMarkdown("DISCLOSURE.md");
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <div className="prose-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
