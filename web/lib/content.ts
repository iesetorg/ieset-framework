import { readFile, readdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve, dirname, basename } from "node:path";
import { execSync } from "node:child_process";
import yaml from "js-yaml";
import { remark } from "remark";
import remarkHtml from "remark-html";

import type {
  Condition,
  Hypothesis,
  Position,
  Publisher,
  SourceToken,
  Variable,
} from "./types";

// Repo root is one level up from /web
export const REPO_ROOT = resolve(process.cwd(), "..");

// -----------------------------------------------------------------------------
// Hypothesis loader
// -----------------------------------------------------------------------------

const SKIP_TOPIC_DIRS = new Set(["conditional_taxonomy", "steelman"]);

async function listHypothesisFiles(): Promise<string[]> {
  const hypRoot = join(REPO_ROOT, "hypotheses");
  if (!existsSync(hypRoot)) return [];
  const out: string[] = [];
  for (const entry of await readdir(hypRoot, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    if (SKIP_TOPIC_DIRS.has(entry.name)) continue;
    const topicDir = join(hypRoot, entry.name);
    for (const file of await readdir(topicDir)) {
      if (file.endsWith(".yaml")) out.push(join(topicDir, file));
    }
  }
  return out;
}

export async function loadHypothesis(id: string): Promise<Hypothesis | null> {
  const files = await listHypothesisFiles();
  for (const file of files) {
    if (basename(file, ".yaml") === id) {
      return parseHypothesis(file);
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Public-visibility gate.
//
// The repo carries 270+ hypothesis YAMLs but only a subset are READY to show
// publicly. The rest are stubs without a real replication.py, or auto-graded
// against the generic falsification boilerplate ("…when this stub is promoted
// from draft"). Showing those in the homepage / scoreboard / hypothesis index
// would hand readers fake-clean SUPPORTED/refuted verdicts that aren't pinned
// to a dispositive pre-registered threshold.
//
// A hypothesis is publicly visible iff:
//   1. A run directory exists with a real replication.py (not just an
//      auto-generated diagnostics stub).
//   2. diagnostics.json has a verdict that doesn't start with stub / pending /
//      blocked / error markers.
//   3. The falsification rule is sharpened — either the rule field itself is
//      not the boilerplate, OR the methodology_note explains the dispositive
//      sharpening and the replication.py encodes it.
//
// Hidden hypotheses still have their YAML on disk and can be drilled into by
// link, but they don't appear in indexes / scoreboards / featured lists. This
// is the "fix or hide" call from the integrity audit.
import { existsSync as _existsSync } from "node:fs";
const _STUB_RULE_MARKER = "when this stub is promoted from draft";

export function isHypothesisPubliclyVisible(
  h: Hypothesis,
  run: { exists?: boolean; verdict?: string }
): boolean {
  if (!run.exists) return false;
  const v = (run.verdict ?? "").toLowerCase().trim();
  if (!v) return false;
  if (
    v.startsWith("inconclusive") ||
    v.startsWith("blocked") ||
    v.startsWith("error") ||
    v.startsWith("no verdict")
  )
    return false;
  // Must have a replication.py — pure auto-grader stubs don't count.
  const replPath = join(REPO_ROOT, "engine", "runs", h.hypothesis_id, "replication.py");
  if (!_existsSync(replPath)) return false;

  // Falsification rule sharpened?
  const rule = h.falsification?.rule ?? "";
  const ruleSharpened = !rule.toLowerCase().includes(_STUB_RULE_MARKER);
  if (ruleSharpened) return true;

  // Stub rule but methodology_note explains the sharpening:
  const mn = (h.notes ?? "").toLowerCase() + " " + ((h as unknown as { methodology_note?: string }).methodology_note ?? "").toLowerCase();
  if (mn.includes("dispositive") || mn.includes("sharpened") || mn.includes("primary (dispositive")) return true;

  return false;
}

// Memoize at module scope. Static export hits this from many pages.
let _allHypothesesCache: Promise<Hypothesis[]> | null = null;

export async function loadAllHypotheses(): Promise<Hypothesis[]> {
  if (_allHypothesesCache) return _allHypothesesCache;
  _allHypothesesCache = (async () => {
    const files = await listHypothesisFiles();
    const all = await Promise.all(files.map((f) => parseHypothesis(f)));
    // Skip files that failed to parse rather than 500ing the whole site —
    // a malformed hypothesis YAML should be a per-file warning, not a global crash.
    const ok = all.filter((h): h is Hypothesis => h !== null);
    return ok.sort((a, b) => a.hypothesis_id.localeCompare(b.hypothesis_id));
  })();
  return _allHypothesesCache;
}

async function parseHypothesis(absPath: string): Promise<Hypothesis | null> {
  const raw = await readFile(absPath, "utf8");
  let doc: (Hypothesis & { title?: string; description?: string }) | null = null;
  try {
    doc = yaml.load(raw) as Hypothesis & {
      title?: string;
      description?: string;
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.warn(
      `[content.ts] skipped malformed hypothesis YAML: ${absPath.replace(
        REPO_ROOT + "/",
        ""
      )} — ${msg.split("\n")[0]}`
    );
    return null;
  }
  if (!doc || typeof doc !== "object" || !doc.hypothesis_id) {
    return null;
  }
  doc._file = absPath.replace(REPO_ROOT + "/", "");
  doc._first_commit = firstCommit(doc._file);
  // Normalise: wave-3 specs use `title` + `description` instead of `claim`.
  // Synthesize a claim so the rest of the app can treat hypotheses uniformly.
  if (!doc.claim) {
    if (doc.title && doc.description) {
      doc.claim = `${doc.title.trim()}. ${doc.description.trim()}`;
    } else {
      doc.claim = doc.title?.trim() ?? doc.description?.trim() ?? doc.hypothesis_id;
    }
  }
  if (!doc.topic) {
    const parent = absPath.split("/").slice(-2, -1)[0];
    doc.topic = parent ?? "uncategorised";
  }
  if (doc.steelman) {
    doc._steelman_html = await loadSteelman(doc.steelman);
  }
  return doc;
}

// -----------------------------------------------------------------------------
// Steelman loader
// -----------------------------------------------------------------------------

async function loadSteelman(repoRelPath: string): Promise<string | undefined> {
  const abs = join(REPO_ROOT, repoRelPath);
  if (!existsSync(abs)) return undefined;
  const raw = await readFile(abs, "utf8");
  const processed = await remark().use(remarkHtml).process(raw);
  return processed.toString();
}

// -----------------------------------------------------------------------------
// Publisher registry
// -----------------------------------------------------------------------------

let publisherRegistry: Map<string, Publisher> | null = null;

async function loadPublisherRegistry(): Promise<Map<string, Publisher>> {
  if (publisherRegistry) return publisherRegistry;
  const path = join(REPO_ROOT, "data", "fetchers", "publishers.yaml");
  if (!existsSync(path)) {
    publisherRegistry = new Map();
    return publisherRegistry;
  }
  const raw = await readFile(path, "utf8");
  const doc = yaml.load(raw) as { publishers?: Record<string, Omit<Publisher, "id">> };
  const map = new Map<string, Publisher>();
  for (const [pubId, rec] of Object.entries(doc.publishers ?? {})) {
    const full: Publisher = { ...rec, id: pubId };
    map.set(pubId, full);
    for (const alias of rec.aliases ?? []) {
      map.set(alias, full);
    }
  }
  publisherRegistry = map;
  return map;
}

// -----------------------------------------------------------------------------
// Source-string parsing (mirror of scripts/derive_coverage.py)
// -----------------------------------------------------------------------------

const SOURCE_TOKEN_RE =
  /([a-z][a-z0-9_]*[a-z0-9]):([A-Za-z0-9_.-]+(?:\s*\([A-Z]{2,5}\))?)/g;

export async function parseSourceString(source: string | undefined): Promise<SourceToken[]> {
  if (!source) return [];
  if (source.trim().toLowerCase().startsWith("constructed:")) {
    return [
      {
        raw: source,
        publisher: "constructed",
        series: source.slice(source.indexOf(":") + 1).trim().slice(0, 120),
        status: "ready",
        credibility_tier: 5,
        license: "constructed",
      },
    ];
  }
  const registry = await loadPublisherRegistry();
  const out: SourceToken[] = [];
  for (const match of source.matchAll(SOURCE_TOKEN_RE)) {
    const pubId = match[1];
    const series = match[2].trim();
    const rec = registry.get(pubId);
    if (!rec) {
      out.push({
        raw: match[0],
        publisher: pubId,
        series,
        status: "gap",
        credibility_tier: 5,
        license: "unknown",
      });
    } else {
      out.push({
        raw: match[0],
        publisher: rec.id,
        publisher_alias: rec.id !== pubId ? pubId : undefined,
        series,
        status: rec.status,
        credibility_tier: rec.credibility_tier,
        license: rec.license,
      });
    }
  }
  return out;
}

// -----------------------------------------------------------------------------
// Git first-commit timestamp (invariant 1 — pre-registration)
//
// Performance: at corpus scale (200+ hypotheses × 50+ pages × per-spec git
// shell-out), naive per-call `git log` exceeded the static-export time budget.
// We bulk-load all "added" commits in one diff-filter pass at module-init time
// and look up by path. Falls back to per-file lookup only when the bulk-load
// missed something (e.g. uncommitted file).
// -----------------------------------------------------------------------------

let _firstCommitCache: Map<string, { hash: string; iso: string }> | null = null;

function buildFirstCommitCache(): Map<string, { hash: string; iso: string }> {
  const map = new Map<string, { hash: string; iso: string }>();
  try {
    // Walk every commit, oldest first, and record the first time each path appears.
    // --diff-filter=A means "only show commits that ADDED that path".
    const out = execSync(
      `git log --diff-filter=A --reverse --name-only --format='COMMIT %H|%aI'`,
      { cwd: REPO_ROOT, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }
    );
    let curHash = "";
    let curIso = "";
    for (const line of out.split("\n")) {
      if (line.startsWith("COMMIT ")) {
        const [hash, iso] = line.slice("COMMIT ".length).split("|");
        curHash = hash;
        curIso = iso;
      } else if (line.trim()) {
        if (!map.has(line)) {
          map.set(line, { hash: curHash.slice(0, 7), iso: curIso });
        }
      }
    }
  } catch {
    /* fall back to per-file lookup */
  }
  return map;
}

function firstCommit(repoRelPath: string): { hash: string; iso: string } | null {
  if (!_firstCommitCache) _firstCommitCache = buildFirstCommitCache();
  const hit = _firstCommitCache.get(repoRelPath);
  if (hit) return hit;
  // Fall back: file may have been --follow renamed, or be uncommitted.
  try {
    const out = execSync(
      `git log --diff-filter=A --follow --format='%H|%aI' -- "${repoRelPath}"`,
      { cwd: REPO_ROOT, encoding: "utf8" }
    ).trim();
    if (!out) return null;
    const [hash, iso] = out.split("\n").pop()!.replace(/'/g, "").split("|");
    const rec = { hash: hash.slice(0, 7), iso };
    _firstCommitCache.set(repoRelPath, rec);
    return rec;
  } catch {
    return null;
  }
}

// -----------------------------------------------------------------------------
// Chart data loader — looks for engine/runs/<id>/chart_data.json
// -----------------------------------------------------------------------------

export async function loadChartData(hypothesisId: string): Promise<unknown | null> {
  const path = join(REPO_ROOT, "engine", "runs", hypothesisId, "chart_data.json");
  if (!existsSync(path)) return null;
  const raw = await readFile(path, "utf8");
  const parsed = parseJsonArtifact(raw, path);

  // Only hand the chart component payloads matching its supported line-chart
  // contract. Several run generators write tabular diagnostics to
  // chart_data.json; those are useful artifacts, but rendering them as a line
  // chart crashes on hydration because they do not have `series[].points`.
  if (!isLineChartPayload(parsed)) return null;
  return parsed;
}

function parseJsonArtifact(raw: string, path: string): unknown {
  try {
    return JSON.parse(raw);
  } catch (err) {
    const sanitized = raw.replace(
      /([:[,]\s*)(?:NaN|-?Infinity)(\s*[,}\]])/g,
      "$1null$2"
    );
    if (sanitized !== raw) return JSON.parse(sanitized);
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not parse JSON artifact ${path}: ${msg}`);
  }
}

function isLineChartPayload(value: unknown): boolean {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  if (record.type !== "line") return false;
  if (!record.x_axis || typeof record.x_axis !== "object") return false;
  if (!record.y_axis || typeof record.y_axis !== "object") return false;
  if (!Array.isArray(record.series)) return false;

  return record.series.every((series) => {
    if (!series || typeof series !== "object" || Array.isArray(series)) {
      return false;
    }
    const s = series as Record<string, unknown>;
    if (typeof s.id !== "string" || typeof s.label !== "string") return false;
    if (!Array.isArray(s.points)) return false;
    return s.points.every((point) => {
      if (!point || typeof point !== "object" || Array.isArray(point)) {
        return false;
      }
      const p = point as Record<string, unknown>;
      return typeof p.x === "number" && typeof p.y === "number";
    });
  });
}

// -----------------------------------------------------------------------------
// Run artifacts — diagnostics + result-card markdown
// -----------------------------------------------------------------------------

export interface RunArtifacts {
  exists: boolean;
  verdict?: string;
  diagnostics?: Record<string, unknown>;
  evidence_packet?: Record<string, unknown>;
  result_card_html?: string;
  run_dir_rel?: string;
}

const _runArtifactsCache = new Map<string, Promise<RunArtifacts>>();

export async function loadRunArtifacts(hypothesisId: string): Promise<RunArtifacts> {
  const cached = _runArtifactsCache.get(hypothesisId);
  if (cached) return cached;
  const promise = (async (): Promise<RunArtifacts> => {
    const runDir = join(REPO_ROOT, "engine", "runs", hypothesisId);
    if (!existsSync(runDir)) return { exists: false };

    const out: RunArtifacts = {
      exists: true,
      run_dir_rel: `engine/runs/${hypothesisId}`,
    };

    const diagPath = join(runDir, "diagnostics.json");
    if (existsSync(diagPath)) {
      try {
        out.diagnostics = parseJsonArtifact(
          await readFile(diagPath, "utf8"),
          diagPath
        ) as Record<string, unknown>;
        out.verdict = out.diagnostics?.verdict as string | undefined;
      } catch {
        /* ignore */
      }
    }

    const packetPath = join(runDir, "evidence_packet.yaml");
    if (existsSync(packetPath)) {
      try {
        const parsed = yaml.load(await readFile(packetPath, "utf8"));
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          out.evidence_packet = parsed as Record<string, unknown>;
        }
      } catch {
        /* ignore */
      }
    }

    const cardPath = join(runDir, "result_card.md");
    if (existsSync(cardPath)) {
      const raw = await readFile(cardPath, "utf8");
      const processed = await remark().use(remarkHtml).process(raw);
      out.result_card_html = processed.toString();
    }

    return out;
  })();
  _runArtifactsCache.set(hypothesisId, promise);
  return promise;
}

// -----------------------------------------------------------------------------
// Position scoreboard — cross-reference position predictions vs hypothesis runs
// -----------------------------------------------------------------------------

export type ClaimOutcome =
  | "supports_position"
  | "refutes_position"
  | "partial_supports"
  | "partial_refutes"
  | "partial"
  | "untested";

export interface ScoredClaim {
  claim: string;
  linked_hypothesis_id: string;
  school_prediction: string;
  claim_polarity: "aligned" | "inverted";
  evidence_type?: string;
  evidence_weight: number;
  coverage_confidence?: string;
  coverage_confidence_weight: number;
  hypothesis_prior_confidence?: number;
  screening_weight: number;
  attribution_weight: number;
  integrity_weight: number;
  second_order_declared_gate_status?: string;
  second_order_strict_gate_status?: string;
  second_order_declared_scoreboard_eligible?: boolean;
  second_order_strict_scoreboard_eligible?: boolean;
  second_order_failure_credit_kind?: string;
  second_order_failure_credit_multiplier?: number;
  second_order_required_data_gaps?: string[];
  verdict?: string;
  outcome: ClaimOutcome;
  outcome_score: number;
  adjusted_outcome_score: number;
  integrity_outcome_score: number;
  integrity_flags: string[];
  hypothesis_exists: boolean;
}

export interface PositionScore {
  position_id: string;
  school: string;
  total_claims: number;
  supports: number;
  refutes: number;
  partial_supports: number;
  partial_refutes: number;
  partial: number; // "neutral" partials — test-quality failures, undirected mixes
  untested: number;
  tested: number;
  /** sum of supports + 0.5*partial_supports - 0.5*partial_refutes - refutes */
  net_score: number;
  /** evidence-quality-adjusted net_score */
  adjusted_net_score: number;
  /** sum of evidence weights for tested predictions */
  adjusted_tested_weight: number;
  /**
   * attribution-aware score: evidence type × claim-link confidence × screening
   * caution × causal-attribution discount for negative-prediction wins.
   */
  integrity_net_score: number;
  /** sum of integrity weights for tested predictions */
  integrity_tested_weight: number;
  /** full verdicts only: supports - refutes */
  decisive_net: number;
  /** heuristic no-call band for tiny aggregate margins */
  signal_threshold: number;
  /** net_score / tested, useful for detecting tiny aggregate margins */
  net_margin_rate: number;
  score_signal: "positive_signal" | "negative_signal" | "too_close_to_call" | "untested";
  adjusted_signal_threshold: number;
  adjusted_net_margin_rate: number;
  adjusted_score_signal: "positive_signal" | "negative_signal" | "too_close_to_call" | "untested";
  integrity_signal_threshold: number;
  integrity_net_margin_rate: number;
  integrity_score_signal: "positive_signal" | "negative_signal" | "too_close_to_call" | "untested";
  support_rate: number;
  scored_claims: ScoredClaim[];
}

export interface ScoreboardSecondOrderGateSummary {
  generated_at?: string;
  scope?: string;
  methodology?: Record<string, string>;
  summary?: Record<string, unknown>;
}

export interface ScoreboardSecondOrderClaimGate {
  position_id: string;
  claim_index: number;
  hypothesis_id?: string;
  declared_gate_status?: string;
  strict_gate_status?: string;
  declared_scoreboard_eligible?: boolean;
  strict_scoreboard_eligible?: boolean;
  failure_credit_kind?: string;
  failure_credit_multiplier?: number;
  required_data_gaps?: string[];
}

let _scoreboardSecondOrderGateSummaryCache: Promise<ScoreboardSecondOrderGateSummary | null> | null = null;
let _scoreboardSecondOrderGateIndexCache: Promise<Map<string, ScoreboardSecondOrderClaimGate> | null> | null = null;

async function loadScoreboardSecondOrderGateArtifact(): Promise<{
  generated_at?: string;
  scope?: string;
  methodology?: Record<string, string>;
  summary?: Record<string, unknown>;
  claim_links?: ScoreboardSecondOrderClaimGate[];
} | null> {
  const path = join(REPO_ROOT, "engine", "scoreboard_second_order_gates.json");
  if (!existsSync(path)) return null;
  const raw = await readFile(path, "utf8");
  return JSON.parse(raw) as {
    generated_at?: string;
    scope?: string;
    methodology?: Record<string, string>;
    summary?: Record<string, unknown>;
    claim_links?: ScoreboardSecondOrderClaimGate[];
  };
}

export async function loadScoreboardSecondOrderGateSummary(): Promise<ScoreboardSecondOrderGateSummary | null> {
  if (_scoreboardSecondOrderGateSummaryCache) return _scoreboardSecondOrderGateSummaryCache;
  _scoreboardSecondOrderGateSummaryCache = (async () => {
    const parsed = await loadScoreboardSecondOrderGateArtifact();
    if (!parsed) return null;
    return {
      generated_at: parsed.generated_at,
      scope: parsed.scope,
      methodology: parsed.methodology,
      summary: parsed.summary,
    };
  })();
  return _scoreboardSecondOrderGateSummaryCache;
}

async function loadScoreboardSecondOrderGateIndex(): Promise<Map<string, ScoreboardSecondOrderClaimGate> | null> {
  if (_scoreboardSecondOrderGateIndexCache) return _scoreboardSecondOrderGateIndexCache;
  _scoreboardSecondOrderGateIndexCache = (async () => {
    const parsed = await loadScoreboardSecondOrderGateArtifact();
    if (!parsed?.claim_links) return null;
    const index = new Map<string, ScoreboardSecondOrderClaimGate>();
    for (const row of parsed.claim_links) {
      index.set(`${row.position_id}#${row.claim_index}`, row);
    }
    return index;
  })();
  return _scoreboardSecondOrderGateIndexCache;
}

function evidenceWeight(evidenceType: string | undefined): number {
  if (evidenceType === "causal") return 1;
  if (evidenceType === "associational") return 0.5;
  // Descriptive and canonical-case checklist runs are valuable evidence, but
  // they are pattern matches rather than causal identification. Keep them on
  // the board, but stop them from dominating doctrine-level school rankings.
  if (evidenceType === "descriptive" || evidenceType === "canonical_case_multi_metric") {
    return 0.25;
  }
  return 0.25;
}

function outcomeScore(outcome: ClaimOutcome): number {
  if (outcome === "supports_position") return 1;
  if (outcome === "partial_supports") return 0.5;
  if (outcome === "partial_refutes") return -0.5;
  if (outcome === "refutes_position") return -1;
  return 0;
}

function coverageConfidenceWeight(confidence: string | undefined): number {
  if (confidence === "high") return 1;
  if (confidence === "medium") return 0.75;
  if (confidence === "low") return 0.5;
  return 0.75;
}

function compactLowerText(parts: Array<string | number | undefined | null>): string {
  return parts
    .filter((p) => p !== undefined && p !== null)
    .map((p) => String(p).toLowerCase())
    .join(" ");
}

function methodologyScreeningWeight(
  h: Hypothesis | undefined,
  coverageNotes: string | undefined
): { weight: number; flags: string[] } {
  if (!h) return { weight: 0.75, flags: ["missing_hypothesis_metadata"] };
  const text = compactLowerText([
    coverageNotes,
    h.methodology_note,
    h.disclosure,
    h.conflict_disclosure,
    h.notes,
    h.estimator?.notes,
  ]);
  const flags: string[] = [];
  let weight = 1;

  if (
    text.includes("triage") ||
    text.includes("not bespoke") ||
    text.includes("not final scoreboard evidence") ||
    text.includes("generic panel") ||
    text.includes("alias-repair")
  ) {
    weight = Math.min(weight, 0.5);
    flags.push("screening_or_triage_evidence");
  } else if (
    text.includes("first-pass") ||
    text.includes("proxy-first") ||
    text.includes("candidate screen") ||
    text.includes("candidate spec") ||
    text.includes("broad panel proxies") ||
    text.includes("throughput wave") ||
    text.includes("swarm") ||
    text.includes("local-data first-pass") ||
    text.includes("generated from")
  ) {
    weight = Math.min(weight, 0.7);
    flags.push("first_pass_or_proxy_evidence");
  }

  if (
    text.includes("identification challenge is severe") ||
    text.includes("endogenously chosen") ||
    text.includes("data-gated") ||
    text.includes("manual assembly")
  ) {
    weight = Math.min(weight, 0.85);
    flags.push("identification_caveat");
  }

  return { weight, flags };
}

function hasMechanismDiscriminatingDesign(h: Hypothesis | undefined): boolean {
  if (!h) return false;
  if ((h.variables?.decomposition_channels ?? []).length > 0) return true;
  const text = compactLowerText([
    h.estimator?.template,
    h.estimator?.notes,
    h.falsification?.test,
    h.falsification?.rule,
    h.methodology_note,
    h.notes,
  ]);
  return (
    text.includes("natural experiment") ||
    text.includes("synthetic control") ||
    text.includes("difference-in-differences") ||
    text.includes("diff-in-diff") ||
    text.includes("event study") ||
    text.includes("instrument") ||
    text.includes("mechanism") ||
    text.includes("decomposition")
  );
}

function attributionWeightForClaim(params: {
  schoolPrediction: string;
  outcomeScore: number;
  evidenceType: string | undefined;
  linkedHyp: Hypothesis | undefined;
  screeningWeight: number;
}): { weight: number; flags: string[] } {
  const prediction = params.schoolPrediction.toLowerCase();
  if (prediction !== "falsified" || params.outcomeScore <= 0) {
    return { weight: 1, flags: [] };
  }

  const flags = ["negative_prediction_attribution_discount"];
  let weight = 0.25;
  if (params.evidenceType === "causal") {
    weight = 0.75;
    flags.push("causal_failure_test");
  } else if (hasMechanismDiscriminatingDesign(params.linkedHyp)) {
    weight = 0.5;
    flags.push("mechanism_discriminating_test");
  } else if (
    params.evidenceType === "descriptive" ||
    params.evidenceType === "canonical_case_multi_metric"
  ) {
    weight = 0.1;
    flags.push("descriptive_failure_not_causal_attribution");
  } else {
    flags.push("associational_failure_not_causal_attribution");
  }

  if (params.screeningWeight <= 0.5) {
    weight = Math.min(weight, 0.15);
    flags.push("screening_failure_credit_cap");
  } else if (params.screeningWeight < 0.8) {
    weight = Math.min(weight, 0.25);
    flags.push("first_pass_failure_credit_cap");
  }

  return { weight, flags };
}

function scoreSignal(
  netScore: number,
  tested: number,
  minimumThreshold = 5
): Pick<PositionScore, "signal_threshold" | "net_margin_rate" | "score_signal"> {
  if (tested <= 0) {
    return {
      signal_threshold: 0,
      net_margin_rate: 0,
      score_signal: "untested",
    };
  }
  // A one- or two-claim wobble should not read as a school-level finding.
  // The raw score remains available, but the UI/API expose this no-call band
  // so small positive/negative margins are not presented as directional wins.
  const signal_threshold = Math.max(minimumThreshold, tested * 0.05);
  const net_margin_rate = netScore / tested;
  if (Math.abs(netScore) <= signal_threshold) {
    return { signal_threshold, net_margin_rate, score_signal: "too_close_to_call" };
  }
  return {
    signal_threshold,
    net_margin_rate,
    score_signal: netScore > 0 ? "positive_signal" : "negative_signal",
  };
}

function adjustedScoreSignal(
  netScore: number,
  adjustedTestedWeight: number
): Pick<
  PositionScore,
  "adjusted_signal_threshold" | "adjusted_net_margin_rate" | "adjusted_score_signal"
> {
  const signal = scoreSignal(netScore, adjustedTestedWeight);
  return {
    adjusted_signal_threshold: signal.signal_threshold,
    adjusted_net_margin_rate: signal.net_margin_rate,
    adjusted_score_signal: signal.score_signal,
  };
}

function verdictToOutcome(
  verdict: string | undefined,
  prediction: string,
  polarity: "aligned" | "inverted" = "aligned"
): ClaimOutcome {
  if (!verdict) return "untested";
  const v = verdict.toLowerCase().trim();
  const p = prediction.toLowerCase();
  // "blocked" runs never produced a real test result — treat as untested
  // (the test couldn't run, no evidence either way).
  if (v.startsWith("blocked")) return "untested";
  // "supported_subset" — for SOCIAL-OUTCOME claims where the canonical-
  // literature indicator basket is incomplete on disk. The indicators that
  // were tested passed, but the canonical basket has documented gaps so
  // this is NOT a clean SUPPORTED. We treat it as a directional
  // partial-toward-support signal (amber on the scoreboard, not green).
  // Must be checked BEFORE the generic "supported" prefix match.
  const hypSupportedSubset = v.startsWith("supported_subset") || v.startsWith("supported subset");
  // "not supported" / "not_supported" — clean refutation signal even though
  // the prefix isn't literally "refuted". Authors use this when the test
  // ran cleanly but the predicted direction didn't show up.
  let hypSupported = v.startsWith("supported") && !hypSupportedSubset;
  let hypRefuted =
    v.startsWith("refuted") ||
    v.startsWith("not supported") ||
    v.startsWith("not_supported");
  // "weakened" is a test-quality verdict — the hypothesis wasn't cleanly ruled
  // in or out (e.g. pre-trend violations, residual thresholds missed). It
  // contributes evidence *against* the hypothesis but is not a clean refutation,
  // so we treat it as a one-way refutation signal: it counts as refutes when the
  // school's narrative aligns with the hypothesis, but under inverted polarity
  // it degrades to "partial" rather than flipping all the way to supports — a
  // failed test shouldn't hand the opposing school a clean win.
  const hypWeakened = v.startsWith("weakened");
  const hypInconclusive = v.startsWith("inconclusive");
  // "partial" / "partially supported" / "mixed" / "weakly supported" are
  // *directional* verdicts — the effect moved in the hypothesis's predicted
  // direction but didn't clear the pre-registered threshold (or significance,
  // or robustness). They carry weak evidentiary weight in favour of the
  // hypothesis.
  //
  // Some generic runners also emit PARTIAL for neutral test-quality states
  // such as "direction inconclusive" or "effect magnitude effectively zero".
  // Those should count as tested but should not give either side a half-win.
  const hypNeutralPartial =
    v.startsWith("partial") &&
    (v.includes("direction inconclusive") ||
      v.includes("claim direction not auto-inferred") ||
      v.includes("effect magnitude effectively zero") ||
      v.includes("standard error/p-value not estimable"));
  const hypPartialTowardSupport =
    (!hypNeutralPartial && v.startsWith("partial")) ||
    v.startsWith("mixed") ||
    v.startsWith("weakly supported") ||
    v.startsWith("weakly_supported") ||
    hypSupportedSubset;

  // When the school's narrative claim is opposite-signed to the hypothesis's
  // pre-registered claim, flip the effective hypothesis verdict before comparing
  // against the school's prediction. A hypothesis SUPPORTED with inverted polarity
  // means the school's narrative is REFUTED (and vice-versa). The partial-toward-
  // support signal flips to partial-toward-refute.
  let partialPolarity: "toward_support" | "toward_refute" | null =
    hypPartialTowardSupport ? "toward_support" : null;
  if (polarity === "inverted") {
    [hypSupported, hypRefuted] = [hypRefuted, hypSupported];
    if (partialPolarity === "toward_support") partialPolarity = "toward_refute";
  }

  // Test-quality failures — framework couldn't cleanly rule in or out.
  // Neutral partial regardless of polarity: neither school should win nor lose
  // from an identification failure.
  if (hypWeakened || hypInconclusive || hypNeutralPartial) return "partial";

  // Directional partial: weak signal in school's favour or against
  if (partialPolarity === "toward_support") {
    if (p === "supported") return "partial_supports";
    if (p === "falsified") return "partial_refutes";
    return "partial";
  }
  if (partialPolarity === "toward_refute") {
    if (p === "supported") return "partial_refutes";
    if (p === "falsified") return "partial_supports";
    return "partial";
  }

  if (p === "supported" && hypSupported) return "supports_position";
  if (p === "supported" && hypRefuted) return "refutes_position";
  if (p === "falsified" && hypRefuted) return "supports_position";
  if (p === "falsified" && hypSupported) return "refutes_position";
  if (p === "mixed") return "partial";
  return "untested";
}

export async function scoreAllPositions(): Promise<PositionScore[]> {
  const positions = await loadAllPositions();
  const hypotheses = await loadAllHypotheses();
  const secondOrderGateIndex = await loadScoreboardSecondOrderGateIndex();
  const hypIds = new Set(hypotheses.map((h) => h.hypothesis_id));

  // Phase 3 (April 2026): Build the authoritative hypothesis-side coverage
  // index. Key is `${position_id}#${claim_index}` → the covers_claims entry
  // from whichever hypothesis declares coverage of that claim. The scoring
  // pipeline now prefers hypothesis-side polarity + school_prediction over
  // the position-side fields, since the hypothesis is the authority on
  // whether it actually tests what the claim asserts and in what direction.
  // See scripts/validate_link_reciprocity.py for the build-time consistency
  // gate. Position-side fields remain the fallback for claims whose
  // hypothesis hasn't declared covers_claims yet (Phase 4 migration in
  // progress).
  const coverageIndex = new Map<
    string,
    NonNullable<Hypothesis["covers_claims"]>[number]
  >();
  for (const h of hypotheses) {
    for (const entry of h.covers_claims ?? []) {
      const key = `${entry.position_id}#${entry.claim_index}`;
      coverageIndex.set(key, entry);
    }
  }

  const scores: PositionScore[] = [];

  for (const pos of positions) {
    const claims = pos.falsifiable_specific_claims ?? [];
    const scored: ScoredClaim[] = [];
    let supports = 0,
      refutes = 0,
      partial_supports = 0,
      partial_refutes = 0,
      partial = 0,
      untested = 0;
    let adjusted_net_score = 0;
    let adjusted_tested_weight = 0;
    let integrity_net_score = 0;
    let integrity_tested_weight = 0;

    const hypById = new Map(hypotheses.map((h) => [h.hypothesis_id, h] as const));
    for (let idx = 0; idx < claims.length; idx++) {
      const c = claims[idx];
      const exists = hypIds.has(c.linked_hypothesis_id);
      let verdict: string | undefined;
      const linkedHyp = hypById.get(c.linked_hypothesis_id);
      if (exists) {
        const run = await loadRunArtifacts(c.linked_hypothesis_id);
        // Public-visibility gate: only count verdicts from hypotheses that
        // pass the integrity bar (sharpened rule + real replication + real
        // verdict). Verdicts auto-graded against the generic falsification
        // boilerplate are excluded from school net-scores — they're not
        // dispositive enough to update a position's standing.
        if (linkedHyp && isHypothesisPubliclyVisible(linkedHyp, run)) {
          verdict = run.verdict;
        }
      }
      // Phase 3: hypothesis-side coverage takes precedence. If the linked
      // hypothesis has declared a covers_claims entry for this specific
      // (position, claim_index) pair, trust the hypothesis's polarity and
      // school_prediction. Falls back to position-side fields for un-migrated
      // claims.
      const coverageEntry = coverageIndex.get(`${pos.position_id}#${idx}`);
      const polarity: "aligned" | "inverted" =
        (coverageEntry?.polarity ?? c.claim_polarity) === "inverted"
          ? "inverted"
          : "aligned";
      const school_prediction =
        coverageEntry?.school_prediction ?? c.school_prediction;
      const outcome = verdictToOutcome(verdict, school_prediction, polarity);
      const evidence_type = linkedHyp?.evidence_type;
      const evidence_weight = evidenceWeight(evidence_type);
      const outcome_score = outcomeScore(outcome);
      const adjusted_outcome_score = outcome_score * evidence_weight;
      const coverage_confidence = coverageEntry?.confidence;
      const coverage_confidence_weight = coverageConfidenceWeight(coverage_confidence);
      const screening = methodologyScreeningWeight(linkedHyp, coverageEntry?.notes);
      const attribution = attributionWeightForClaim({
        schoolPrediction: school_prediction,
        outcomeScore: outcome_score,
        evidenceType: evidence_type,
        linkedHyp,
        screeningWeight: screening.weight,
      });
      const secondOrderGate = secondOrderGateIndex?.get(`${pos.position_id}#${idx}`);
      const secondOrderStrictEligible =
        secondOrderGate?.strict_scoreboard_eligible ?? false;
      const gateFailureMultiplier =
        secondOrderGate?.failure_credit_kind &&
        secondOrderGate.failure_credit_kind !== "not_failure_prediction_win"
          ? secondOrderGate.failure_credit_multiplier ?? 1
          : 1;
      const secondOrderMultiplier = secondOrderStrictEligible
        ? Math.min(1, gateFailureMultiplier)
        : 0;
      const integrity_weight =
        evidence_weight *
        coverage_confidence_weight *
        screening.weight *
        attribution.weight *
        secondOrderMultiplier;
      const integrity_outcome_score = outcome_score * integrity_weight;
      adjusted_net_score += adjusted_outcome_score;
      integrity_net_score += integrity_outcome_score;
      if (outcome !== "untested") adjusted_tested_weight += evidence_weight;
      if (outcome !== "untested") integrity_tested_weight += integrity_weight;
      scored.push({
        claim: c.claim,
        linked_hypothesis_id: c.linked_hypothesis_id,
        school_prediction,
        claim_polarity: polarity,
        evidence_type,
        evidence_weight,
        coverage_confidence,
        coverage_confidence_weight,
        hypothesis_prior_confidence: linkedHyp?.prior_confidence,
        screening_weight: screening.weight,
        attribution_weight: attribution.weight,
        integrity_weight,
        second_order_declared_gate_status: secondOrderGate?.declared_gate_status,
        second_order_strict_gate_status: secondOrderGate?.strict_gate_status,
        second_order_declared_scoreboard_eligible: secondOrderGate?.declared_scoreboard_eligible,
        second_order_strict_scoreboard_eligible: secondOrderGate?.strict_scoreboard_eligible,
        second_order_failure_credit_kind: secondOrderGate?.failure_credit_kind,
        second_order_failure_credit_multiplier: secondOrderGate?.failure_credit_multiplier,
        second_order_required_data_gaps: secondOrderGate?.required_data_gaps,
        verdict,
        outcome,
        outcome_score,
        adjusted_outcome_score,
        integrity_outcome_score,
        integrity_flags: [...screening.flags, ...attribution.flags],
        hypothesis_exists: exists,
      });
      if (outcome === "supports_position") supports++;
      else if (outcome === "refutes_position") refutes++;
      else if (outcome === "partial_supports") partial_supports++;
      else if (outcome === "partial_refutes") partial_refutes++;
      else if (outcome === "partial") partial++;
      else untested++;
    }

    const tested =
      supports + refutes + partial_supports + partial_refutes + partial;
    // Weighted net: full verdicts count 1, directional partials count 0.5,
    // neutral partials (test-quality failures) count 0.
    const net_score =
      supports + 0.5 * partial_supports - 0.5 * partial_refutes - refutes;
    const decisive_net = supports - refutes;
    const signal = scoreSignal(net_score, tested);
    const adjustedSignal = adjustedScoreSignal(adjusted_net_score, adjusted_tested_weight);
    const integritySignal = scoreSignal(integrity_net_score, integrity_tested_weight);
    // support_rate is the share of directional, non-neutral evidence that
    // agrees with the school. Partial supports count half; partial refutes
    // remain in the denominator but do not add support.
    const weighted_pos = supports + 0.5 * partial_supports;
    const weighted_total =
      supports + refutes + partial_supports + partial_refutes;
    scores.push({
      position_id: pos.position_id,
      school: pos.school,
      total_claims: claims.length,
      supports,
      refutes,
      partial_supports,
      partial_refutes,
      partial,
      untested,
      tested,
      net_score,
      adjusted_net_score,
      adjusted_tested_weight,
      integrity_net_score,
      integrity_tested_weight,
      decisive_net,
      signal_threshold: signal.signal_threshold,
      net_margin_rate: signal.net_margin_rate,
      score_signal: signal.score_signal,
      adjusted_signal_threshold: adjustedSignal.adjusted_signal_threshold,
      adjusted_net_margin_rate: adjustedSignal.adjusted_net_margin_rate,
      adjusted_score_signal: adjustedSignal.adjusted_score_signal,
      integrity_signal_threshold: integritySignal.signal_threshold,
      integrity_net_margin_rate: integritySignal.net_margin_rate,
      integrity_score_signal: integritySignal.score_signal,
      support_rate: weighted_total > 0 ? weighted_pos / weighted_total : 0,
      scored_claims: scored,
    });
  }

  scores.sort((a, b) => {
    if (a.tested === 0 && b.tested === 0) return 0;
    if (a.tested === 0) return 1;
    if (b.tested === 0) return -1;
    const netDiff = b.integrity_net_score - a.integrity_net_score;
    if (Math.abs(netDiff) > 0.001) return netDiff;
    const integrityWeightDiff = b.integrity_tested_weight - a.integrity_tested_weight;
    if (Math.abs(integrityWeightDiff) > 0.001) return integrityWeightDiff;
    return a.position_id.localeCompare(b.position_id);
  });

  return scores;
}

// -----------------------------------------------------------------------------
// Methodology / disclosure / contribute markdown
// -----------------------------------------------------------------------------

export async function loadRepoMarkdown(filename: string): Promise<string> {
  const path = join(REPO_ROOT, filename);
  if (!existsSync(path)) return `# ${filename} not found`;
  const raw = await readFile(path, "utf8");
  const processed = await remark().use(remarkHtml).process(raw);
  return processed.toString();
}

// -----------------------------------------------------------------------------
// Condition loader — hypotheses/conditional_taxonomy/*.yaml
// -----------------------------------------------------------------------------

async function listConditionFiles(): Promise<string[]> {
  const dir = join(REPO_ROOT, "hypotheses", "conditional_taxonomy");
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  for (const file of await readdir(dir)) {
    if (file.endsWith(".yaml")) out.push(join(dir, file));
  }
  return out;
}

async function parseCondition(absPath: string): Promise<Condition> {
  const raw = await readFile(absPath, "utf8");
  const doc = yaml.load(raw) as Condition;
  doc._file = absPath.replace(REPO_ROOT + "/", "");
  doc._first_commit = firstCommit(doc._file);
  return doc;
}

export async function loadCondition(id: string): Promise<Condition | null> {
  const files = await listConditionFiles();
  for (const file of files) {
    if (basename(file, ".yaml") === id) {
      return parseCondition(file);
    }
  }
  return null;
}

let _allConditionsCache: Promise<Condition[]> | null = null;
export async function loadAllConditions(): Promise<Condition[]> {
  if (_allConditionsCache) return _allConditionsCache;
  _allConditionsCache = (async () => {
    const files = await listConditionFiles();
    const all = await Promise.all(files.map((f) => parseCondition(f)));
    return all.sort((a, b) => a.id.localeCompare(b.id));
  })();
  return _allConditionsCache;
}

// -----------------------------------------------------------------------------
// Position loader — positions/*.yaml
// -----------------------------------------------------------------------------

async function listPositionFiles(): Promise<string[]> {
  const dir = join(REPO_ROOT, "positions");
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  for (const file of await readdir(dir)) {
    // Underscore prefix marks derived/index files (e.g. _axis_index.yaml),
    // not real positions. Including them here puts a phantom row on /pos
    // with position_id=undefined and an /pos/undefined link.
    if (file.startsWith("_")) continue;
    if (file.endsWith(".yaml")) out.push(join(dir, file));
  }
  return out;
}

async function parsePosition(absPath: string): Promise<Position> {
  const raw = await readFile(absPath, "utf8");
  const doc = yaml.load(raw) as Position;
  doc._file = absPath.replace(REPO_ROOT + "/", "");
  doc._first_commit = firstCommit(doc._file);
  return doc;
}

export async function loadPosition(id: string): Promise<Position | null> {
  const files = await listPositionFiles();
  for (const file of files) {
    if (basename(file, ".yaml") === id) {
      return parsePosition(file);
    }
  }
  return null;
}

let _allPositionsCache: Promise<Position[]> | null = null;
export async function loadAllPositions(): Promise<Position[]> {
  if (_allPositionsCache) return _allPositionsCache;
  _allPositionsCache = (async () => {
    const files = await listPositionFiles();
    const all = await Promise.all(files.map((f) => parsePosition(f)));
    return all.sort((a, b) => a.position_id.localeCompare(b.position_id));
  })();
  return _allPositionsCache;
}

// -----------------------------------------------------------------------------
// Hypothesis → schools reverse index
// -----------------------------------------------------------------------------
//
// For the hypothesis index UI: which schools predict on this hypothesis, and
// what each school expects the verdict to be (after polarity-flip).
//
// Note this is the reverse of position.falsifiable_specific_claims, with
// covers_claims taking precedence (Phase 3 authority). The returned
// "expected_verdict" is the verdict the school would call a win — i.e. it
// already accounts for claim_polarity inversion.

export interface SchoolPredictionOnHypothesis {
  position_id: string;
  school: string;
  expected_verdict: "supported" | "falsified" | "mixed";
  /** What the school's narrative claim said in the original; before polarity flip. */
  raw_school_prediction: "supported" | "falsified" | "mixed";
  polarity: "aligned" | "inverted";
}

let _hypToSchoolsCache: Record<
  string,
  SchoolPredictionOnHypothesis[]
> | null = null;

export async function loadHypothesisSchoolPredictions(): Promise<
  Record<string, SchoolPredictionOnHypothesis[]>
> {
  if (_hypToSchoolsCache) return _hypToSchoolsCache;
  const [positions, hypotheses] = await Promise.all([
    loadAllPositions(),
    loadAllHypotheses(),
  ]);

  // Authoritative coverage_index: (position_id, claim_index) -> covers_claims entry
  const coverageIndex = new Map<
    string,
    NonNullable<Hypothesis["covers_claims"]>[number]
  >();
  for (const h of hypotheses) {
    for (const entry of h.covers_claims ?? []) {
      coverageIndex.set(`${entry.position_id}#${entry.claim_index}`, entry);
    }
  }

  const out: Record<string, SchoolPredictionOnHypothesis[]> = {};
  for (const pos of positions) {
    const claims = pos.falsifiable_specific_claims ?? [];
    for (let idx = 0; idx < claims.length; idx++) {
      const c = claims[idx];
      const hid = c.linked_hypothesis_id;
      if (!hid) continue;
      const cov = coverageIndex.get(`${pos.position_id}#${idx}`);
      const polarity: "aligned" | "inverted" =
        (cov?.polarity ?? c.claim_polarity ?? "aligned") === "inverted"
          ? "inverted"
          : "aligned";
      const raw = (cov?.school_prediction ?? c.school_prediction) as
        | "supported"
        | "falsified"
        | "mixed";
      // Polarity flip: if the school's claim is inverted relative to the
      // hypothesis's pre-reg claim, then a "supported" hypothesis verdict
      // means the school's claim was REFUTED.
      const expected: "supported" | "falsified" | "mixed" =
        polarity === "inverted"
          ? raw === "supported"
            ? "falsified"
            : raw === "falsified"
            ? "supported"
            : "mixed"
          : raw;
      (out[hid] ??= []).push({
        position_id: pos.position_id,
        school: pos.school,
        expected_verdict: expected,
        raw_school_prediction: raw,
        polarity,
      });
    }
  }
  // Deduplicate: a position can have multiple falsifiable_specific_claims that
  // link to the same hypothesis_id. Render only the first chip per
  // (position, hypothesis) pair — the chip's role is "this school has a stake
  // in this hypothesis", not "show every claim". Multiple competing claims
  // from the same school on the same hypothesis is a spec-design issue surfaced
  // by validate_specs, not something to render as duplicate chips (which would
  // also break React keys and produce duplicate-key console warnings).
  for (const hid of Object.keys(out)) {
    const seen = new Set<string>();
    out[hid] = out[hid].filter((s) => {
      if (seen.has(s.position_id)) return false;
      seen.add(s.position_id);
      return true;
    });
  }
  _hypToSchoolsCache = out;
  return out;
}

export async function schoolPredictionsForHypothesis(
  hypothesisId: string
): Promise<SchoolPredictionOnHypothesis[]> {
  const idx = await loadHypothesisSchoolPredictions();
  return idx[hypothesisId] ?? [];
}

// -----------------------------------------------------------------------------
// Axes loader (axes.yaml — shared across policies, movements, axis browser)
// -----------------------------------------------------------------------------

export interface Axis {
  id: string;
  channel: string;
  description: string;
  direction_semantics?: Record<string, string>;
  source_publishers?: string[];
  typical_proxies?: string[];
}

let _axesCache: Record<string, Axis> | null = null;

export async function loadAxes(): Promise<Record<string, Axis>> {
  if (_axesCache) return _axesCache;
  const file = join(REPO_ROOT, "axes.yaml");
  if (!existsSync(file)) return (_axesCache = {});
  const raw = await readFile(file, "utf8");
  const doc = yaml.load(raw) as { axes?: Axis[] };
  const map: Record<string, Axis> = {};
  for (const a of doc?.axes ?? []) {
    if (a.id) map[a.id] = a;
  }
  _axesCache = map;
  return map;
}

export async function loadAllAxes(): Promise<Axis[]> {
  const m = await loadAxes();
  return Object.values(m).sort((a, b) => a.id.localeCompare(b.id));
}

export function axisShortLabel(axis: string): string {
  const parts = axis.split(".");
  const tail = parts[parts.length - 1] ?? axis;
  return tail.replace(/_/g, " ");
}

export function axisDirectionLabel(
  axis: Axis | undefined,
  direction: string
): string | undefined {
  if (!axis?.direction_semantics) return undefined;
  return axis.direction_semantics[direction];
}
