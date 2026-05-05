import type { RunArtifacts } from "@/lib/content";
import type { Hypothesis, Variable } from "@/lib/types";
import { verdictShort } from "@/lib/verdict";

type VariableWithRole = Variable & { role: string };

function humanize(text: string | undefined): string {
  return (text ?? "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function sentenceCase(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function firstSentence(text: string | undefined): string {
  const clean = (text ?? "").replace(/\s+/g, " ").trim();
  return clean.split(/(?<=[.!?])\s+/)[0] ?? clean;
}

function verdictBucket(run: RunArtifacts): string {
  return verdictShort(run.verdict).toLowerCase();
}

function confidenceLabel(run: RunArtifacts): string {
  const bucket = verdictBucket(run);
  const packet = run.evidence_packet;
  const data = packet?.data as { data_quality?: { grade?: string; missing_series_count?: number } } | undefined;
  const grade = data?.data_quality?.grade ?? "";
  const missing = data?.data_quality?.missing_series_count ?? 0;

  if (!run.exists) return "Not run yet";
  if (bucket.includes("supported") && grade === "reproducible_hash_verified") return "Clear support";
  if (bucket.includes("refuted") && grade === "reproducible_hash_verified") return "Clear refutation";
  if (bucket.includes("partial")) return "Mixed or noisy";
  if (bucket.includes("inconclusive") && missing > 0) return "Not enough data";
  if (bucket.includes("inconclusive")) return "Coverage too thin";
  return "Needs review";
}

function plainAnswer(run: RunArtifacts): string {
  if (!run.exists) {
    return "This question has been registered, but the data test has not run yet.";
  }
  const verdict = run.verdict ?? "Result available.";
  const bucket = verdictBucket(run);
  const afterDash = verdict.split(/\s[-—]\s/).slice(1).join(" - ").trim();
  const core = firstSentence(afterDash || verdict);

  if (bucket.includes("supported")) {
    return `The data clearly moved in the predicted direction. ${core}`;
  }
  if (bucket.includes("refuted")) {
    return `The data did not support the prediction. ${core}`;
  }
  if (bucket.includes("partial")) {
    return `The evidence is suggestive but not decisive. ${core}`;
  }
  if (bucket.includes("inconclusive")) {
    return `This test cannot make a firm call yet. ${core}`;
  }
  return core;
}

function plainMethod(hypothesis: Hypothesis): string {
  const sample = hypothesis.sample;
  const estimator = hypothesis.estimator?.template;
  const parts = [];
  if (sample) {
    parts.push(
      `It compares ${sample.countries.length} country or place units from ${sample.period[0]} to ${sample.period[1]}`
    );
  } else {
    parts.push("It compares the outcome and policy measures specified before the run");
  }
  if (estimator) parts.push(`using a ${humanize(estimator)} design`);
  if (hypothesis.estimator?.fixed_effects?.length) {
    parts.push(`with fixed effects for ${hypothesis.estimator.fixed_effects.map(humanize).join(" and ")}`);
  }
  return `${parts.join(", ")}.`;
}

function whyItMatters(hypothesis: Hypothesis): string {
  const topic = humanize(hypothesis.topic);
  if (topic.includes("labour")) {
    return "Labor-market rules often help some workers while risking job loss or slower hiring for others. This test looks for that tradeoff in observable employment or unemployment data.";
  }
  if (topic.includes("distribution")) {
    return "Distributional claims often sound morally clear but are empirically complex. This test asks whether the proposed channel explains real differences across places.";
  }
  if (topic.includes("housing")) {
    return "Housing policy affects rents, mobility, household budgets, and construction. The test looks for measurable effects rather than relying on slogans.";
  }
  if (topic.includes("growth")) {
    return "Growth claims can look convincing in single success stories. This test asks whether the pattern survives a broader comparison.";
  }
  return `This matters because ${topic || "policy"} claims should change belief only when they survive a pre-declared empirical test.`;
}

function variableExplanation(v: VariableWithRole): string {
  const name = sentenceCase(humanize(v.name));
  if (v.role === "outcome") return `${name}: the thing we are trying to explain.`;
  if (v.role === "treatment") return `${name}: the policy or condition whose effect is being tested.`;
  if (v.role === "channel") return `${name}: a proposed pathway from policy to outcome.`;
  if (v.role === "control") return `${name}: a background factor included so the comparison is fairer.`;
  return `${name}: one of the measures used in the test.`;
}

function dataQuality(run: RunArtifacts): string {
  const packet = run.evidence_packet;
  const data = packet?.data as { data_quality?: { grade?: string; input_count?: number; missing_series_count?: number } } | undefined;
  const quality = data?.data_quality;
  if (!quality) return "No evidence packet has been generated yet.";
  const grade = humanize(quality.grade);
  return `${quality.input_count ?? 0} input datasets, ${quality.missing_series_count ?? 0} unresolved missing series, provenance status: ${grade}.`;
}

export function PolicyBriefCard({
  hypothesis,
  run,
  variables,
}: {
  hypothesis: Hypothesis;
  run: RunArtifacts;
  variables: VariableWithRole[];
}) {
  const question = firstSentence(hypothesis.claim);
  const topVariables = variables.slice(0, 4);
  const confidence = confidenceLabel(run);

  return (
    <section className="mb-10 overflow-hidden rounded border border-rule bg-white">
      <div className="border-b border-rule bg-panel px-5 py-4">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="sc text-[10px] font-semibold text-muted">policy brief</span>
          <span className="rounded-sm bg-code-bg px-2 py-[2px] text-[11px] font-medium text-ink">
            {confidence}
          </span>
        </div>
        <h2 className="m-0 max-w-[900px] text-[22px] font-semibold leading-[1.25] text-ink">
          What this test is asking
        </h2>
        <p className="mb-0 mt-2 max-w-[860px] text-[16px] leading-[1.55] text-ink">
          {question}
        </p>
      </div>

      <div className="grid gap-0 md:grid-cols-[1.15fr_0.85fr]">
        <div className="border-b border-rule p-5 md:border-b-0 md:border-r">
          <div className="mb-5">
            <div className="sc mb-1.5 text-[10px] font-semibold text-muted">plain answer</div>
            <p className="m-0 text-[15px] leading-[1.65] text-ink">{plainAnswer(run)}</p>
          </div>
          <div className="mb-5">
            <div className="sc mb-1.5 text-[10px] font-semibold text-muted">why it matters</div>
            <p className="m-0 text-[14px] leading-[1.6] text-muted">{whyItMatters(hypothesis)}</p>
          </div>
          <div>
            <div className="sc mb-1.5 text-[10px] font-semibold text-muted">how the test works</div>
            <p className="m-0 text-[14px] leading-[1.6] text-muted">{plainMethod(hypothesis)}</p>
          </div>
        </div>

        <div className="p-5">
          <div className="mb-5">
            <div className="sc mb-2 text-[10px] font-semibold text-muted">what was measured</div>
            {topVariables.length > 0 ? (
              <ul className="m-0 list-none space-y-2 p-0">
                {topVariables.map((v, i) => (
                  <li key={`${v.role}-${v.name}-${i}`} className="text-[13px] leading-[1.45] text-muted">
                    <span className="font-semibold text-ink">{v.role}</span>{" "}
                    {variableExplanation(v)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="m-0 text-[13px] text-muted">The run artifacts define the measured variables.</p>
            )}
          </div>
          <div className="mb-5">
            <div className="sc mb-1.5 text-[10px] font-semibold text-muted">what this does not prove</div>
            <p className="m-0 text-[13px] leading-[1.55] text-muted">
              A single test is not the whole truth. It narrows the claim under a specific sample,
              time period, and method. Strong policy conclusions need the pattern to survive nearby
              tests, alternative data, and serious objections.
            </p>
          </div>
          <div>
            <div className="sc mb-1.5 text-[10px] font-semibold text-muted">verification</div>
            <p className="m-0 text-[13px] leading-[1.55] text-muted">{dataQuality(run)}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
