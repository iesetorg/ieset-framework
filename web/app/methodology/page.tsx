import { loadRepoMarkdown } from "@/lib/content";

export const metadata = {
  title: "Methodology",
  description:
    "The six invariants every hypothesis, dataset, and model in the IESET framework must satisfy.",
};

export default async function MethodologyPage() {
  const html = await loadRepoMarkdown("METHODOLOGY.md");
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <div
        className="prose-body"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
