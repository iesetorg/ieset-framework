import {
  isHypothesisPubliclyVisible,
  loadAllConditions,
  loadAllHypotheses,
  loadRunArtifacts,
} from "./content";
import type { Condition, Hypothesis } from "./types";
import { verdictShort, verdictTone, type VerdictShort, type VerdictTone } from "./verdict";

type EvidenceSource = "curated" | "reverse" | "model" | "related";

export interface ConditionEvidenceLink {
  hypothesis_id: string;
  claim: string;
  topic: string;
  source: EvidenceSource;
  verdict?: string;
  verdict_label: VerdictShort;
  verdict_tone: VerdictTone;
  publicly_visible: boolean;
  match_score?: number;
}

export interface ConditionEvidenceSummary {
  direct: ConditionEvidenceLink[];
  related: ConditionEvidenceLink[];
  direct_count: number;
  related_count: number;
  tested_count: number;
  related_available_count: number;
}

const RELATED_LIMIT = 10;
const RELATED_MIN_SCORE = 4;

const CONDITION_PROFILES: Record<string, string[]> = {
  agricultural_production_efficiency: [
    "agricultur",
    "crop",
    "farm",
    "farmer",
    "food",
    "rural",
  ],
  capital_allocation_among_firms: [
    "capital allocation",
    "misallocation",
    "investment",
    "credit",
    "firm",
    "productivity",
    "venture",
    "private credit",
  ],
  chilean_afp_forced_saving_pension_model: [
    "afp",
    "chile",
    "pension",
    "forced saving",
    "superannuation",
    "cpf",
    "retirement",
  ],
  climate_externality_mitigation: [
    "climate",
    "carbon",
    "emission",
    "co2",
    "green transition",
    "environmental",
    "renewable",
  ],
  consumer_goods_allocation: [
    "consumer goods",
    "price control",
    "shortage",
    "black market",
    "goods availability",
    "retail",
    "ration",
  ],
  consumer_preference_responsiveness: [
    "consumer preference",
    "choice",
    "price signal",
    "market signal",
    "demand",
    "quality",
    "shortage",
  ],
  foundational_r_and_d_knowledge_spillover: [
    "r&d",
    "research",
    "innovation",
    "patent",
    "knowledge spillover",
    "technology diffusion",
    "science",
  ],
  german_mittelstand_skilled_manufacturing_model: [
    "mittelstand",
    "vocational",
    "manufacturing",
    "germany",
    "apprenticeship",
    "skilled",
  ],
  growth_without_broad_participation: [
    "gini",
    "poverty",
    "inequality",
    "distribution",
    "wage",
    "labour share",
    "labor share",
    "income share",
  ],
  health_insurance_adverse_selection: [
    "health insurance",
    "healthcare",
    "single payer",
    "adverse selection",
    "medical",
    "infant mortality",
    "life expectancy",
  ],
  innovation_and_technology_diffusion: [
    "innovation",
    "technology",
    "productivity",
    "tfp",
    "high tech",
    "patent",
    "digital",
  ],
  intergenerational_mobility_institutional_determinants: [
    "intergenerational",
    "mobility",
    "income mobility",
    "rank-rank",
    "education",
    "opportunity",
  ],
  japanese_keiretsu_coordination_model: [
    "keiretsu",
    "japan",
    "industrial policy",
    "selective credit",
    "developmentalist",
    "export discipline",
  ],
  labour_share_decline_institutional_decomposition: [
    "labour share",
    "labor share",
    "wage share",
    "union",
    "collective bargaining",
    "automation",
    "capital intensity",
  ],
  natural_monopolies: [
    "natural monopoly",
    "electricity",
    "grid",
    "transmission",
    "water",
    "rail",
    "network",
    "utility",
  ],
  nordic_institutional_design: [
    "nordic",
    "norway",
    "sweden",
    "denmark",
    "finland",
    "welfare",
    "flexicurity",
  ],
  pandemic_coordination_externality: [
    "pandemic",
    "covid",
    "lockdown",
    "vaccination",
    "public health",
    "coordination",
  ],
  public_goods_non_excludable: [
    "public goods",
    "non-excludable",
    "infrastructure",
    "defense",
    "basic research",
    "broadcast",
    "commons",
    "public spending",
  ],
  resource_rent_capture_via_swf: [
    "resource rent",
    "sovereign wealth",
    "gpfg",
    "oil",
    "gas",
    "hydrocarbon",
    "extractive",
    "nationalisation",
    "royalty",
  ],
  singapore_healthcare_forced_saving_model: [
    "singapore",
    "healthcare",
    "cpf",
    "medisave",
    "forced saving",
    "health savings",
  ],
  swiss_federalism_decentralised_governance_model: [
    "swiss",
    "switzerland",
    "federalism",
    "decentral",
    "cantonal",
    "local governance",
  ],
  top_income_share_growth_channels: [
    "top income",
    "income share",
    "top 1",
    "inequality",
    "capital gains",
    "wealth",
    "executive pay",
  ],
  trade_in_goods_and_services: [
    "trade",
    "tariff",
    "export",
    "import",
    "openness",
    "fta",
    "liberalisation",
    "globalization",
  ],
};

let cache: Promise<Record<string, ConditionEvidenceSummary>> | null = null;

export async function loadConditionEvidenceIndex(): Promise<Record<string, ConditionEvidenceSummary>> {
  if (cache) return cache;
  cache = buildConditionEvidenceIndex();
  return cache;
}

export async function loadConditionEvidence(id: string): Promise<ConditionEvidenceSummary> {
  const index = await loadConditionEvidenceIndex();
  return index[id] ?? emptySummary();
}

async function buildConditionEvidenceIndex(): Promise<Record<string, ConditionEvidenceSummary>> {
  const [conditions, hypotheses] = await Promise.all([
    loadAllConditions(),
    loadAllHypotheses(),
  ]);
  const byHypothesisId = new Map(hypotheses.map((h) => [h.hypothesis_id, h]));
  const reverseConditionLinks = reverseLinks(hypotheses);
  const out: Record<string, ConditionEvidenceSummary> = {};

  await Promise.all(
    conditions.map(async (condition) => {
      const directSources = new Map<string, EvidenceSource>();
      for (const id of condition.linked_hypotheses ?? []) {
        if (byHypothesisId.has(id)) directSources.set(id, "curated");
      }
      for (const id of reverseConditionLinks.get(condition.id) ?? []) {
        if (byHypothesisId.has(id) && !directSources.has(id)) {
          directSources.set(id, "reverse");
        }
      }
      for (const id of condition.linked_model_ids ?? []) {
        if (byHypothesisId.has(id) && !directSources.has(id)) {
          directSources.set(id, "model");
        }
      }

      const relatedCandidates = hypotheses
        .map((hypothesis) => ({
          hypothesis,
          score: relatedScore(condition, hypothesis),
        }))
        .filter(({ hypothesis, score }) => score >= RELATED_MIN_SCORE && !directSources.has(hypothesis.hypothesis_id))
        .sort((a, b) => b.score - a.score || a.hypothesis.hypothesis_id.localeCompare(b.hypothesis.hypothesis_id));

      const directLinks = await Promise.all(
        [...directSources.entries()].map(([id, source]) =>
          evidenceLink(byHypothesisId.get(id), source)
        )
      );
      const relatedLinks = await Promise.all(
        relatedCandidates.slice(0, RELATED_LIMIT).map(({ hypothesis, score }) =>
          evidenceLink(hypothesis, "related", score)
        )
      );
      const direct = directLinks.filter((link): link is ConditionEvidenceLink => Boolean(link));
      const related = relatedLinks.filter((link): link is ConditionEvidenceLink => Boolean(link));
      out[condition.id] = {
        direct,
        related,
        direct_count: direct.length,
        related_count: related.length,
        related_available_count: relatedCandidates.length,
        tested_count: [...direct, ...related].filter((link) => link.publicly_visible).length,
      };
    })
  );

  return out;
}

function reverseLinks(hypotheses: Hypothesis[]): Map<string, string[]> {
  const out = new Map<string, string[]>();
  for (const hypothesis of hypotheses) {
    for (const conditionId of hypothesis.linked_conditions ?? []) {
      const list = out.get(conditionId) ?? [];
      list.push(hypothesis.hypothesis_id);
      out.set(conditionId, list);
    }
  }
  return out;
}

async function evidenceLink(
  hypothesis: Hypothesis | undefined,
  source: EvidenceSource,
  score?: number
): Promise<ConditionEvidenceLink | null> {
  if (!hypothesis) return null;
  const run = await loadRunArtifacts(hypothesis.hypothesis_id);
  return {
    hypothesis_id: hypothesis.hypothesis_id,
    claim: preview(hypothesis.claim),
    topic: hypothesis.topic,
    source,
    verdict: run.verdict,
    verdict_label: verdictShort(run.verdict),
    verdict_tone: verdictTone(run.verdict),
    publicly_visible: isHypothesisPubliclyVisible(hypothesis, run),
    match_score: score,
  };
}

function relatedScore(condition: Condition, hypothesis: Hypothesis): number {
  const terms = CONDITION_PROFILES[condition.id] ?? condition.id.split("_");
  const text = hypothesisText(hypothesis);
  let score = 0;

  for (const rawTerm of terms) {
    const term = normalize(rawTerm);
    if (!term || !text.includes(term)) continue;
    score += term.includes(" ") ? 4 : 1;
    if (normalize(hypothesis.hypothesis_id).includes(term)) score += 2;
  }
  return score;
}

function hypothesisText(hypothesis: Hypothesis): string {
  const scope = hypothesis.scope;
  const sample = hypothesis.sample;
  const variables = hypothesis.variables;
  const parts: unknown[] = [
    hypothesis.hypothesis_id,
    hypothesis.topic,
    hypothesis.claim,
    hypothesis.notes,
    hypothesis.methodology_note,
    hypothesis.disclosure,
    scope?.countries,
    scope?.outcome_dim,
    scope?.policy_family,
    scope?.treatment_tags,
    sample?.countries,
    variables?.outcome?.map((v) => [v.name, v.source]),
    variables?.treatment?.map((v) => [v.name, v.source]),
    variables?.controls?.map((v) => [v.name, v.source]),
  ];
  return normalize(parts.flat(3).filter(Boolean).join(" "));
}

function normalize(value: string): string {
  return value.toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
}

function preview(value: string): string {
  const text = value.replace(/\s+/g, " ").trim();
  if (text.length <= 180) return text;
  return text.slice(0, 180).trimEnd() + "...";
}

function emptySummary(): ConditionEvidenceSummary {
  return {
    direct: [],
    related: [],
    direct_count: 0,
    related_count: 0,
    related_available_count: 0,
    tested_count: 0,
  };
}
