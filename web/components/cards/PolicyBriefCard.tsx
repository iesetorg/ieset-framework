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

function friendlyName(text: string | undefined): string {
  const clean = humanize(text);
  const direct: Record<string, string> = {
    teen_employment_to_population: "teen job rate",
    low_education_unemployment_rate: "unemployment among workers with less education",
    low_skill_employment_share: "share of jobs held by lower-skill workers",
    minimum_to_median_wage_ratio: "how high the minimum wage is compared with typical local pay",
    state_minimum_wage: "state minimum wage",
    minimum_wage_real_level: "inflation-adjusted minimum wage",
    intergenerational_earnings_elasticity: "how strongly parents' income predicts their children's income",
    bottom_to_top_quintile_transition_probability: "chance that children from low-income families reach the top",
    education_spending_inequality: "unequal school funding",
    residential_segregation_by_income: "income separation between neighborhoods",
    price_to_income_ratio_tier1_cities: "housing costs in high-opportunity cities",
    gdp_per_capita_real: "real income per person",
    gdp_per_capita_ppp: "cost-of-living adjusted income per person",
    disposable_income_gini: "income inequality after taxes and transfers",
    government_effectiveness: "basic government quality",
  };
  if (text && direct[text]) return direct[text];

  const replacements: Record<string, string> = {
    gdp: "income",
    ppp: "cost-of-living adjusted",
    tfp: "productivity",
    gini: "inequality",
    fdi: "foreign investment",
    soe: "state-owned firms",
    epl: "employment protection rules",
    oecd: "rich-country",
    pcap: "per person",
    min: "minimum",
  };
  return clean
    .split(" ")
    .map((word) => replacements[word.toLowerCase()] ?? word)
    .join(" ");
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

function primaryVariable(variables: VariableWithRole[], role: string): string | undefined {
  return variables.find((v) => v.role === role)?.name;
}

function plainQuestion(hypothesis: Hypothesis, variables: VariableWithRole[]): string {
  const id = hypothesis.hypothesis_id.toLowerCase();
  const claim = hypothesis.claim.toLowerCase();
  const topic = humanize(hypothesis.topic).toLowerCase();
  const outcome = friendlyName(primaryVariable(variables, "outcome"));
  const treatment = friendlyName(primaryVariable(variables, "treatment"));
  const channel = friendlyName(primaryVariable(variables, "channel"));
  const period = hypothesis.sample?.period;
  const periodText = period ? ` from ${period[0]} to ${period[1]}` : "";

  if (claim.includes("minimum-wage") || claim.includes("minimum wage") || id.includes("minimum_wage")) {
    return "When minimum wages rise high relative to normal local pay, do lower-skill workers keep their jobs, or does hiring fall at the margin?";
  }

  if (claim.includes("intergenerational") || claim.includes("mobility")) {
    return "Do children have a better shot at moving up when schools, housing, and neighborhoods give them access to opportunity, rather than simply because a country redistributes more income?";
  }

  if (topic.includes("housing") || claim.includes("rent control") || claim.includes("zoning")) {
    return "Does the housing rule being tested make homes easier to build, rent, or afford, or does it quietly reduce supply and push costs elsewhere?";
  }

  if (topic.includes("growth") || claim.includes("productivity") || claim.includes("income")) {
    return "Over a long period, do more market-oriented institutions translate into higher income or productivity, once the comparison looks beyond a single success story?";
  }

  if (topic.includes("health") || claim.includes("healthcare") || claim.includes("medical")) {
    return "Does the healthcare rule being tested improve access, cost, or outcomes for patients, or does it mainly shift pressure around the system?";
  }

  if (topic.includes("technology") || claim.includes("innovation") || claim.includes("patent")) {
    return "Does the policy environment make innovation easier to fund, build, and scale, or does it slow down useful new technology?";
  }

  if (topic.includes("trade") || claim.includes("tariff") || claim.includes("openness")) {
    return "When countries open more of the economy to trade and competition, do people end up with better long-run income or productivity outcomes?";
  }

  if (treatment && outcome) {
    return `In plain terms, this asks whether ${treatment} is actually linked to better or worse ${outcome}${periodText}.`;
  }

  if (channel && outcome) {
    return `In plain terms, this asks whether ${channel} is a real pathway to better or worse ${outcome}${periodText}.`;
  }

  return `In plain terms, this asks whether the policy story survives a real-world data check${periodText}.`;
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

function measureGroups(variables: VariableWithRole[]): Array<{ title: string; items: string[] }> {
  const outcomes = variables.filter((v) => v.role === "outcome").slice(0, 3).map((v) => friendlyName(v.name));
  const treatments = variables.filter((v) => v.role === "treatment").slice(0, 2).map((v) => friendlyName(v.name));
  const channels = variables.filter((v) => v.role === "channel").slice(0, 2).map((v) => friendlyName(v.name));

  const groups = [];
  if (treatments.length) {
    groups.push({
      title: "What changed",
      items: treatments,
    });
  }
  if (channels.length) {
    groups.push({
      title: "Possible pathway",
      items: channels,
    });
  }
  if (outcomes.length) {
    groups.push({
      title: "What we checked",
      items: outcomes,
    });
  }
  return groups;
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
  const question = plainQuestion(hypothesis, variables);
  const measured = measureGroups(variables);
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
          In ordinary language
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
            {measured.length > 0 ? (
              <div className="space-y-3">
                {measured.map((group) => (
                  <div key={group.title}>
                    <div className="mb-1 text-[12px] font-semibold text-ink">{group.title}</div>
                    <ul className="m-0 list-none space-y-1 p-0">
                      {group.items.map((item) => (
                        <li key={item} className="text-[13px] leading-[1.45] text-muted">
                          {sentenceCase(item)}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
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
