import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";
import yaml from "js-yaml";

import { REPO_ROOT } from "./content";
import type { Hypothesis } from "./types";
import type { Policy, PolicyAxisMove } from "./policies";

// -----------------------------------------------------------------------------
// Hypothesis ↔ axis index (derived by scripts/derive_hypothesis_axes.py)
// -----------------------------------------------------------------------------

export interface HypothesisAxisTag {
  axis: string;
  score: number;
  reasons?: string[];
}

interface AxisIndexDoc {
  index: Record<string, HypothesisAxisTag[]>;
}

let _indexCache: Record<string, HypothesisAxisTag[]> | null = null;

export async function loadHypothesisAxisIndex(): Promise<
  Record<string, HypothesisAxisTag[]>
> {
  if (_indexCache) return _indexCache;
  const file = join(REPO_ROOT, "hypotheses", "_axis_index.yaml");
  if (!existsSync(file)) return (_indexCache = {});
  const raw = await readFile(file, "utf8");
  const doc = yaml.load(raw) as AxisIndexDoc;
  _indexCache = doc?.index ?? {};
  return _indexCache;
}

export async function axesForHypothesis(
  hypothesisId: string
): Promise<HypothesisAxisTag[]> {
  const idx = await loadHypothesisAxisIndex();
  return idx[hypothesisId] ?? [];
}

// -----------------------------------------------------------------------------
// Reverse index: axis → hypothesis IDs
// -----------------------------------------------------------------------------

let _reverseCache: Record<string, string[]> | null = null;

export async function hypothesesByAxis(): Promise<Record<string, string[]>> {
  if (_reverseCache) return _reverseCache;
  const idx = await loadHypothesisAxisIndex();
  const out: Record<string, string[]> = {};
  for (const [hid, tags] of Object.entries(idx)) {
    for (const t of tags) {
      (out[t.axis] ??= []).push(hid);
    }
  }
  _reverseCache = out;
  return out;
}

export async function hypothesesForAxis(axisId: string): Promise<string[]> {
  const m = await hypothesesByAxis();
  return m[axisId] ?? [];
}

// -----------------------------------------------------------------------------
// Policy → hypotheses (inferred via axis overlap)
// -----------------------------------------------------------------------------

export interface InferredHypothesisMatch {
  hypothesis_id: string;
  score: number;
  shared_axes: string[];
}

/**
 * For a policy, return hypotheses whose tagged axes overlap the policy's
 * `axes_moved`. Score = sum over shared axes of (axis-score-weight ×
 * magnitude-weight). Sorted descending, capped at `limit`.
 */
export async function hypothesesForPolicy(
  policy: Policy,
  limit = 8
): Promise<InferredHypothesisMatch[]> {
  const idx = await loadHypothesisAxisIndex();
  const policyAxes = new Set(
    (policy.axes_moved ?? []).map((m) => m.axis)
  );
  if (policyAxes.size === 0) return [];

  const candidates: Record<
    string,
    { score: number; shared: Set<string> }
  > = {};

  for (const [hid, tags] of Object.entries(idx)) {
    for (const t of tags) {
      if (policyAxes.has(t.axis)) {
        const c = (candidates[hid] ??= { score: 0, shared: new Set() });
        c.score += Math.max(1, t.score);
        c.shared.add(t.axis);
      }
    }
  }

  return Object.entries(candidates)
    .map(([hid, c]) => ({
      hypothesis_id: hid,
      score: c.score,
      shared_axes: [...c.shared],
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

// -----------------------------------------------------------------------------
// Policy ↔ policy similarity (for "similar policies" on /p/<id> and Phase 2)
// -----------------------------------------------------------------------------

export interface SimilarPolicyMatch {
  policy: Policy;
  score: number;
  shared_axes: { axis: string; same_direction: boolean }[];
}

function magnitudeWeight(m?: string): number {
  switch ((m ?? "").toLowerCase()) {
    case "strong":
      return 1.0;
    case "moderate":
      return 0.7;
    case "weak":
      return 0.4;
    default:
      return 0.6;
  }
}

/**
 * For a target policy, find other policies whose axis fingerprint overlaps.
 * Score = sum over shared axes of (same-direction ? 1 : 0.5) × avg magnitude weight.
 */
export function similarPolicies(
  target: Policy,
  corpus: Policy[],
  { limit = 10 }: { limit?: number } = {}
): SimilarPolicyMatch[] {
  const targetAxes = new Map<string, PolicyAxisMove>();
  for (const m of target.axes_moved ?? []) {
    targetAxes.set(m.axis, m);
  }
  if (targetAxes.size === 0) return [];

  const matches: SimilarPolicyMatch[] = [];
  for (const p of corpus) {
    if (p.policy_id === target.policy_id) continue;
    const shared: { axis: string; same_direction: boolean }[] = [];
    let score = 0;
    for (const m of p.axes_moved ?? []) {
      const t = targetAxes.get(m.axis);
      if (!t) continue;
      const same = t.direction === m.direction;
      const dirWeight = same ? 1.0 : 0.5;
      const magW = (magnitudeWeight(t.magnitude) + magnitudeWeight(m.magnitude)) / 2;
      score += dirWeight * magW;
      shared.push({ axis: m.axis, same_direction: same });
    }
    if (shared.length > 0) {
      matches.push({ policy: p, score, shared_axes: shared });
    }
  }
  return matches.sort((a, b) => b.score - a.score).slice(0, limit);
}

// -----------------------------------------------------------------------------
// Phase-2 entry point: match proposed axis fingerprint → historical policies
// -----------------------------------------------------------------------------

/**
 * Given a proposed policy fingerprint (a list of axis moves, e.g. from a
 * user's input on /q), return ranked historical policies.
 */
export function matchProposedFingerprint(
  proposed: { axis: string; direction: string; magnitude?: string }[],
  corpus: Policy[],
  limit = 12
): SimilarPolicyMatch[] {
  // Wrap as a synthetic policy so we can reuse similarPolicies.
  const pseudo: Policy = {
    policy_id: "__proposed__",
    status: "proposed",
    title: "Proposed policy",
    countries: [],
    timeframe: { start: new Date().getUTCFullYear(), end: "ongoing" },
    axes_moved: proposed as PolicyAxisMove[],
  };
  return similarPolicies(pseudo, corpus, { limit });
}

// -----------------------------------------------------------------------------
// Position ↔ axis index (companion to hypothesis index)
// -----------------------------------------------------------------------------

let _posIndexCache: Record<string, HypothesisAxisTag[]> | null = null;

export async function loadPositionAxisIndex(): Promise<
  Record<string, HypothesisAxisTag[]>
> {
  if (_posIndexCache) return _posIndexCache;
  const file = join(REPO_ROOT, "positions", "_axis_index.yaml");
  if (!existsSync(file)) return (_posIndexCache = {});
  const raw = await readFile(file, "utf8");
  const doc = yaml.load(raw) as AxisIndexDoc;
  _posIndexCache = doc?.index ?? {};
  return _posIndexCache;
}

export async function axesForPosition(
  positionId: string
): Promise<HypothesisAxisTag[]> {
  const idx = await loadPositionAxisIndex();
  return idx[positionId] ?? [];
}

/**
 * For a position, return hypotheses whose axes overlap the position's
 * derived axes — sorted by combined score. This is how the scoreboard /
 * position page surfaces evidence even when explicit `linked_hypothesis_id`
 * values point at hypotheses the library doesn't yet contain.
 */
export async function hypothesesForPosition(
  positionId: string,
  limit = 12
): Promise<InferredHypothesisMatch[]> {
  const posTags = await axesForPosition(positionId);
  if (posTags.length === 0) return [];
  const posAxes = new Map(posTags.map((t) => [t.axis, t.score]));

  const hypIdx = await loadHypothesisAxisIndex();
  const out: Record<string, { score: number; shared: Set<string> }> = {};
  for (const [hid, tags] of Object.entries(hypIdx)) {
    for (const t of tags) {
      const posScore = posAxes.get(t.axis);
      if (posScore === undefined) continue;
      const c = (out[hid] ??= { score: 0, shared: new Set() });
      c.score += Math.max(1, t.score) * Math.min(1.5, posScore / 10);
      c.shared.add(t.axis);
    }
  }

  return Object.entries(out)
    .map(([hid, c]) => ({
      hypothesis_id: hid,
      score: c.score,
      shared_axes: [...c.shared],
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

// -----------------------------------------------------------------------------
// Convenience: load hypothesis-id → Hypothesis map
// -----------------------------------------------------------------------------

export function hypothesisById(all: Hypothesis[]): Map<string, Hypothesis> {
  return new Map(all.map((h) => [h.hypothesis_id, h]));
}

// -----------------------------------------------------------------------------
// Policy ↔ position alignments (derived via parent movements)
// -----------------------------------------------------------------------------
//
// A policy doesn't carry position_alignments directly. But every policy is
// referenced by one or more movements, and each movement carries its own
// position_alignments. So we can derive: for each policy, what schools the
// enacting movement(s) aligned with or opposed.
//
// If multiple parent movements disagree on a school's alignment, we resolve
// by choosing the most common label (ties → "partially_aligned"), since a
// policy enacted by movements with different position-readings is, by
// definition, contested.

interface MovementShape {
  movement_id: string;
  policies?: string[];
  position_alignments?: { position_id: string; alignment: string }[];
}

let _policyPositionsCache: Record<
  string,
  { position_id: string; alignment: string }[]
> | null = null;

export async function loadPolicyPositionAlignments(): Promise<
  Record<string, { position_id: string; alignment: string }[]>
> {
  if (_policyPositionsCache) return _policyPositionsCache;
  const dir = join(REPO_ROOT, "movements");
  if (!existsSync(dir)) return (_policyPositionsCache = {});

  // policy_id -> position_id -> [alignment, ...] (across parent movements)
  const accum: Record<string, Record<string, string[]>> = {};
  for (const entry of await readdir(dir)) {
    if (!entry.endsWith(".yaml")) continue;
    const raw = await readFile(join(dir, entry), "utf8");
    const doc = yaml.load(raw) as MovementShape | null;
    if (!doc?.movement_id) continue;
    const pas = doc.position_alignments ?? [];
    if (pas.length === 0) continue;
    for (const policyId of doc.policies ?? []) {
      const perPolicy = (accum[policyId] ??= {});
      for (const a of pas) {
        (perPolicy[a.position_id] ??= []).push(a.alignment);
      }
    }
  }

  // Resolve majority alignment per (policy, position)
  const out: Record<string, { position_id: string; alignment: string }[]> = {};
  const PRIORITY: Record<string, number> = {
    aligned: 3,
    opposed: 3,
    partially_aligned: 2,
  };
  for (const [policyId, perPolicy] of Object.entries(accum)) {
    out[policyId] = Object.entries(perPolicy).map(([positionId, labels]) => {
      // Mode with priority tiebreak — distinct strong labels collapse to partial.
      const counts: Record<string, number> = {};
      for (const l of labels) counts[l] = (counts[l] ?? 0) + 1;
      const sorted = Object.entries(counts).sort(
        (a, b) =>
          b[1] - a[1] ||
          (PRIORITY[b[0]] ?? 0) - (PRIORITY[a[0]] ?? 0)
      );
      const top = sorted[0][1];
      const ties = sorted.filter(([, c]) => c === top).map(([k]) => k);
      const alignment =
        ties.length > 1 && new Set(ties).has("aligned") && new Set(ties).has("opposed")
          ? "partially_aligned"
          : ties[0];
      return { position_id: positionId, alignment };
    });
  }
  _policyPositionsCache = out;
  return out;
}

export async function positionAlignmentsForPolicy(
  policyId: string
): Promise<{ position_id: string; alignment: string }[]> {
  const idx = await loadPolicyPositionAlignments();
  return idx[policyId] ?? [];
}

// -----------------------------------------------------------------------------
// Position → movements reverse index
// -----------------------------------------------------------------------------

export interface MovementForPosition {
  movement_id: string;
  name?: string;
  countries?: string[];
  era?: { start?: number; end?: number | string };
  alignment: "aligned" | "opposed" | "partially_aligned" | string;
}

let _positionMovementsCache: Record<string, MovementForPosition[]> | null =
  null;

// Movement YAMLs use a few legacy position_id aliases that don't match the
// canonical 17 position IDs on disk. Resolve them so e.g. 180 movements tagged
// "ecological" surface on both /pos/degrowth and /pos/eco_socialist instead of
// vanishing. Each alias maps to one or more canonical position IDs.
const POSITION_ALIASES: Record<string, string[]> = {
  chicago_monetarist: ["chicago_monetarism"],
  developmentalist: ["developmentalism"],
  ordo_liberal: ["ordoliberal"],
  social_democracy: ["social_democratic"],
  modern_monetary_theory: ["mmt"],
  keynesian: ["new_keynesian", "post_keynesian"],
  market_liberal: ["classical_liberal"],
  ecological: ["degrowth", "eco_socialist"],
  green_political_economy: ["eco_socialist", "degrowth"],
  green_interventionism: ["eco_socialist"],
  neoliberal: ["classical_liberal"],
  neoclassical: ["empirical_pragmatist"],
  social_liberal: ["empirical_pragmatist"],
  third_way: ["social_democratic"],
};

function resolvePositionAliases(positionId: string): string[] {
  return POSITION_ALIASES[positionId] ?? [positionId];
}

export async function loadPositionMovementsIndex(): Promise<
  Record<string, MovementForPosition[]>
> {
  if (_positionMovementsCache) return _positionMovementsCache;
  const dir = join(REPO_ROOT, "movements");
  if (!existsSync(dir)) return (_positionMovementsCache = {});

  const out: Record<string, MovementForPosition[]> = {};
  // Track (positionId, movementId) pairs already added so an alias-fanout
  // doesn't double-list when both the canonical and alias appear.
  const seen = new Set<string>();
  for (const entry of await readdir(dir)) {
    if (!entry.endsWith(".yaml")) continue;
    const raw = await readFile(join(dir, entry), "utf8");
    const doc = yaml.load(raw) as
      | (MovementShape & {
          name?: string;
          countries?: string[];
          era?: { start?: number; end?: number | string };
        })
      | null;
    if (!doc?.movement_id) continue;
    for (const a of doc.position_alignments ?? []) {
      if (!a.position_id) continue;
      for (const canonicalId of resolvePositionAliases(a.position_id)) {
        const key = `${canonicalId}#${doc.movement_id}`;
        if (seen.has(key)) continue;
        seen.add(key);
        (out[canonicalId] ??= []).push({
          movement_id: doc.movement_id,
          name: doc.name,
          countries: doc.countries,
          era: doc.era,
          alignment: a.alignment,
        });
      }
    }
  }
  // Sort: aligned/opposed first by era start desc, then partial, then others
  for (const positionId of Object.keys(out)) {
    out[positionId].sort((a, b) => {
      const aRank = ALIGNMENT_RANK[a.alignment] ?? 9;
      const bRank = ALIGNMENT_RANK[b.alignment] ?? 9;
      if (aRank !== bRank) return aRank - bRank;
      const aStart = typeof a.era?.start === "number" ? a.era.start : 0;
      const bStart = typeof b.era?.start === "number" ? b.era.start : 0;
      return bStart - aStart;
    });
  }
  _positionMovementsCache = out;
  return out;
}

const ALIGNMENT_RANK: Record<string, number> = {
  aligned: 0,
  opposed: 1,
  partially_aligned: 2,
};

export async function movementsForPosition(
  positionId: string
): Promise<MovementForPosition[]> {
  const idx = await loadPositionMovementsIndex();
  return idx[positionId] ?? [];
}
