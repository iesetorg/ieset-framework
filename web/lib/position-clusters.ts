// Five-bucket cluster taxonomy for positions, used by /atlas to color countries
// by the ideological cluster of the movements active at the slider year.
//
// Clusters are intentionally coarser than the 17-position taxonomy — at world-map
// scale you can't tell two shades of blue apart, and the audience for the atlas
// is "see broad ideological geography over time", not "discriminate post-Keynesian
// from MMT". The /pos pages still keep the full 17-school breakdown.

export type ClusterId =
  | "market_liberal"
  | "centrist"
  | "developmentalist"
  | "social_democratic"
  | "radical_left"
  | "mixed"
  | "none";

export interface ClusterDef {
  id: ClusterId;
  label: string;
  color: string;
  // positions whose `aligned` flag pulls a movement into this cluster
  positions: string[];
}

export const CLUSTERS: ClusterDef[] = [
  {
    id: "market_liberal",
    label: "Market-liberal",
    color: "#1f4e79", // deep blue (site accent)
    positions: [
      "austrian",
      "chicago_monetarism",
      "chicago_monetarist", // agent-authored variant
      "classical_liberal",
      "ordoliberal",
      "market_liberal", // alias seen in some movement YAMLs
    ],
  },
  {
    id: "centrist",
    label: "Centrist / institutional",
    color: "#5b8a87", // teal
    positions: [
      "new_keynesian",
      "empirical_pragmatist",
      "institutionalism",
      "third_way", // Blair/Clinton synthesis — neoliberal-leaning centrism
      "christian_democratic", // German/EU centre-right post-war centrism
      "social_liberal", // Rawlsian-leaning centrist-left
    ],
  },
  {
    id: "developmentalist",
    label: "Developmentalist",
    color: "#b7791f", // amber
    positions: [
      "developmentalism",
      "developmentalist", // agent-authored variant
      "national_conservative", // industrial-policy + protectionism right
    ],
  },
  {
    id: "social_democratic",
    label: "Social-democratic",
    color: "#d97757", // terracotta
    positions: [
      "social_democratic",
      "democratic_socialist",
      "ecological", // green-left, treating as social-democratic adjacent for atlas-scale colouring
    ],
  },
  {
    id: "radical_left",
    label: "Heterodox / radical-left",
    color: "#9e2f2f", // deep red
    positions: [
      "post_keynesian",
      "mmt",
      "marxian",
      "marxist_leninist",
      "market_socialist",
      "eco_socialist",
      "degrowth",
    ],
  },
];

export const MIXED_COLOR = "#8a8a8a"; // when no cluster wins decisively
export const NONE_COLOR = "#e8e6e0"; // active movements with no aligned positions
export const EMPTY_COLOR = "#f3f3f1"; // no active movements at this year

// Aliases — non-canonical position_ids that movement YAMLs use, mapped
// to the closest canonical position. Without these, movements like
// Bolsonaro (uses neoliberal/right_populism/libertarian) show as no-school-
// signal grey on the atlas because none of those IDs match any cluster.
const POSITION_ALIASES: Record<string, string> = {
  // market-liberal family
  neoliberal: "classical_liberal",
  neoclassical: "chicago_monetarism",
  supply_side: "chicago_monetarism",
  libertarian: "austrian",
  imf_washington_consensus: "chicago_monetarism",
  ordo_liberal: "ordoliberal", // underscore typo
  // centrist family
  keynesian: "new_keynesian",
  // developmentalist / national-conservative family
  right_populism: "national_conservative",
  populist_nationalism: "national_conservative",
  conservative_nationalism: "national_conservative",
  neoconservative: "national_conservative",
  ethno_nationalist_developmentalism: "developmentalism",
  political_islam: "national_conservative", // religious-traditionalist authoritarian developmentalism
  // social-democratic / ecological family
  social_democracy: "social_democratic",
  green_political_economy: "ecological",
  green_interventionism: "ecological",
  // radical-left family
  modern_monetary_theory: "mmt",
  dependency_theory: "marxian",
};

// position_id → cluster_id lookup
const _byPosition: Map<string, ClusterId> = (() => {
  const m = new Map<string, ClusterId>();
  for (const c of CLUSTERS) for (const p of c.positions) m.set(p, c.id);
  return m;
})();

export function clusterForPosition(positionId: string): ClusterId | null {
  const direct = _byPosition.get(positionId);
  if (direct) return direct;
  const aliased = POSITION_ALIASES[positionId];
  if (aliased) return _byPosition.get(aliased) ?? null;
  return null;
}

export function colorForCluster(c: ClusterId): string {
  if (c === "mixed") return MIXED_COLOR;
  if (c === "none") return NONE_COLOR;
  return CLUSTERS.find((x) => x.id === c)?.color ?? EMPTY_COLOR;
}

// Score a single movement's cluster from its position_alignments. Returns the
// dominant cluster (highest weighted score) plus a breakdown.
export interface AlignmentEntry {
  position_id: string;
  alignment: string; // "aligned" | "partially_aligned" | "opposed"
}

const ALIGNMENT_WEIGHT: Record<string, number> = {
  aligned: 1.0,
  partially_aligned: 0.5,
  opposed: -0.5,
};

export function dominantClusterFor(
  alignments: AlignmentEntry[] | undefined
): { cluster: ClusterId; score: number } {
  if (!alignments || alignments.length === 0) {
    return { cluster: "none", score: 0 };
  }
  const scores = new Map<ClusterId, number>();
  for (const a of alignments) {
    const c = clusterForPosition(a.position_id);
    if (!c) continue;
    const w = ALIGNMENT_WEIGHT[a.alignment] ?? 0;
    if (w === 0) continue;
    scores.set(c, (scores.get(c) ?? 0) + w);
  }
  let best: ClusterId = "none";
  let bestScore = 0;
  for (const [c, s] of scores) {
    if (s > bestScore) {
      best = c;
      bestScore = s;
    }
  }
  return { cluster: best, score: bestScore };
}
