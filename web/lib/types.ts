// Content types mirror the JSON Schemas under /schemas/.
// Kept loose (many optional fields) because draft/candidate specs have fewer fields populated.

export type HypothesisStatus = "draft" | "candidate" | "pre_registered";
export type EvidenceType = "causal" | "associational" | "descriptive";
export type TemporalStructure = "panel" | "time_series" | "cross_section_with_justification";

export interface Variable {
  name: string;
  source?: string;
  transformation?: string;
  notes?: string;
}

export interface Hypothesis {
  hypothesis_id: string;
  version: number;
  status: HypothesisStatus;
  topic: string;
  claim: string;
  evidence_type?: EvidenceType;

  sample?: {
    countries: string[];
    period: [number, number];
    temporal_structure: TemporalStructure;
    cross_section_justification?: string;
    exclusion_rules?: string[];
  };

  variables?: {
    outcome?: Variable[];
    treatment?: Variable[];
    decomposition_channels?: Variable[];
    controls?: Variable[];
    instruments?: Variable[];
  };

  intervention_channel?: "fiscal" | "regulatory" | "bundled";
  intervention_channel_justification?: string;

  estimator?: {
    template: string;
    clustering?: string;
    fixed_effects?: string[];
    random_seed?: number;
    notes?: string;
  };

  falsification?: {
    rule: string;
    test: string;
    threshold?: string | number | null;
  };

  prior_confidence?: number;
  disclosure?: string;
  conflict_disclosure?: string;
  steelman?: string;
  linked_hypotheses?: string[];
  linked_conditions?: string[];
  notes?: string;
  methodology_note?: string;

  // Phase 2 (April 2026): scope block for claim→hypothesis link gating.
  scope?: {
    period: [number, number];
    countries: string[];
    outcome_dim: string[];
    policy_family?: string[];
    treatment_tags?: string[];
  };

  // Phase 3 (April 2026): authoritative reverse-index of position claims this
  // hypothesis covers. When present, the polarity here overrides the
  // position-side claim_polarity. See scripts/validate_link_reciprocity.py.
  covers_claims?: Array<{
    position_id: string;
    claim_index: number;
    polarity: ClaimPolarity;
    school_prediction?: "supported" | "falsified" | "mixed";
    confidence?: "high" | "medium" | "low";
    notes?: string;
  }>;

  // Populated at load time — not part of the YAML schema
  _file?: string;
  _first_commit?: { hash: string; iso: string } | null;
  _steelman_html?: string;
}

// Publisher record for resolving source tokens in the UI
export interface Publisher {
  id: string;
  name: string;
  license: string;
  credibility_tier: 1 | 2 | 3 | 4 | 5;
  status: "ready" | "pending" | "scrape_needed" | "reconstruct_needed" | "gap";
  endpoint?: string;
  aliases?: string[];
  fetcher_module?: string;
}

// Parsed source token (one publisher:series pair, stripped of parenthetical notes)
export interface SourceToken {
  raw: string;
  publisher: string;          // canonical id after alias resolution
  publisher_alias?: string;   // original if an alias was used
  series: string;
  status: Publisher["status"];
  credibility_tier: Publisher["credibility_tier"];
  license: string;
}

// -----------------------------------------------------------------------------
// Condition (conditional taxonomy entry)
// -----------------------------------------------------------------------------

export type ConditionCategory =
  | "conditions_favoring_markets"
  | "conditions_favoring_intervention"
  | "conditions_with_distributional_considerations"
  | "conditions_specific_institutional_models";

export type ConditionConfidence = "low" | "medium" | "medium_high" | "high";

export interface ConditionCase {
  id: string;
  description: string;
  citations?: string[];
}

export interface ConditionSubAnalysis {
  id: string;
  observation: string;
  framework_position: string;
  [extra: string]: unknown;
}

export interface Condition {
  id: string;
  category: ConditionCategory;
  description: string;
  institutional_features_that_make_the_model_work?: Record<string, string>;
  supporting_cases?: ConditionCase[];
  disconfirming_cases?: ConditionCase[];
  failed_replications?: ConditionCase[];
  policy_implications?: string;
  what_the_model_is_not?: string[];
  framework_position: string;
  confidence: ConditionConfidence;
  linked_hypotheses?: string[];
  linked_model_ids?: string[];
  sub_analyses?: ConditionSubAnalysis[];

  // Populated at load time
  _file?: string;
  _first_commit?: { hash: string; iso: string } | null;
}

// -----------------------------------------------------------------------------
// Position (school of thought)
// -----------------------------------------------------------------------------

export type PositionStatus = "draft" | "candidate" | "published";
export type SchoolPrediction = "supported" | "falsified" | "mixed";
export type EmpiricalStatus = "untested" | "supported" | "falsified" | "mixed";
export type ClaimPolarity = "aligned" | "inverted";

export interface PositionClaim {
  claim: string;
  linked_hypothesis_id: string;
  school_prediction: SchoolPrediction;
  claim_polarity?: ClaimPolarity;
  empirical_status?: EmpiricalStatus;
  notes?: string;
}

export interface Position {
  position_id: string;
  school: string;
  short_name?: string;
  status: PositionStatus;
  proponents?: string[];
  key_texts?: string[];
  steelman: string;
  falsifiable_specific_claims?: PositionClaim[];
  empirical_record_summary?: string;
  scope_decisions?: string[];
  linked_hypotheses?: string[];
  notes?: string;

  // Populated at load time
  _file?: string;
  _first_commit?: { hash: string; iso: string } | null;
}
