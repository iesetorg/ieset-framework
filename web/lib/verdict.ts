/**
 * Single source of truth for parsing run-card verdict strings into UI tones
 * and short-form labels.
 *
 * The framework's verdicts come from `engine/runs/<id>/diagnostics.json`'s
 * `verdict` field, written by replication.py. They are free-form prose, but
 * authors follow conventions:
 *   "supported …"            — clean ≥-threshold pass
 *   "supported_subset …"     — for SOCIAL-OUTCOME claims: indicators tested
 *                              passed but canonical-literature basket has
 *                              documented gaps. Amber, NOT green.
 *   "weakly supported …"     — direction correct but identification flawed
 *                              (e.g. pre-trend fails, donor pool thin)
 *   "partial …"              — direction correct but magnitude below threshold
 *   "mixed …"                — multi-spec; some pass some fail
 *   "weakened …"             — pre-registered residual exceeds threshold
 *                              (test-quality failure, not a clean refute)
 *   "inconclusive …"         — data gaps prevent verdict
 *   "refuted …"              — clean ≥-threshold fail in opposite direction
 *   "not supported …"        — clean fail without obvious opposite-direction
 *                              evidence (author-chosen weaker label)
 *   "blocked …"              — replication.py declined to run for documented
 *                              data-resolution reasons; treat as untested
 *
 * Centralising the parser stops the same prefix-list drifting across pages
 * (homepage, /h, /a/[id], /pos/[id], /m/[id], scoreboard).
 */

export type VerdictTone = "green" | "amber" | "red" | "muted";

export type VerdictShort =
  | "supported"
  | "supported subset"
  | "weakly supported"
  | "partial"
  | "mixed"
  | "weakened"
  | "inconclusive"
  | "refuted"
  | "not supported"
  | "blocked"
  | "run pending";

export function verdictTone(v: string | undefined): VerdictTone {
  if (!v) return "muted";
  const vl = v.toLowerCase().trim();
  if (vl.startsWith("blocked")) return "muted";
  // supported_subset must be checked BEFORE generic "supported" prefix.
  // It is amber (canonical basket incomplete), not green.
  if (vl.startsWith("supported_subset") || vl.startsWith("supported subset"))
    return "amber";
  if (vl.startsWith("supported")) return "green";
  if (
    vl.startsWith("weakly supported") ||
    vl.startsWith("weakly_supported") ||
    vl.startsWith("partial") ||
    vl.startsWith("partially") ||
    vl.startsWith("mixed")
  )
    return "amber";
  if (
    vl.startsWith("refuted") ||
    vl.startsWith("not supported") ||
    vl.startsWith("not_supported") ||
    vl.startsWith("weakened")
  )
    return "red";
  if (vl.startsWith("inconclusive")) return "muted";
  return "muted";
}

export function verdictShort(v: string | undefined): VerdictShort {
  if (!v) return "run pending";
  const vl = v.toLowerCase().trim();
  if (vl.startsWith("blocked")) return "blocked";
  if (vl.startsWith("supported_subset") || vl.startsWith("supported subset"))
    return "supported subset";
  if (vl.startsWith("supported")) return "supported";
  if (vl.startsWith("weakly supported") || vl.startsWith("weakly_supported"))
    return "weakly supported";
  if (vl.startsWith("partial") || vl.startsWith("partially")) return "partial";
  if (vl.startsWith("mixed")) return "mixed";
  if (vl.startsWith("refuted")) return "refuted";
  if (vl.startsWith("not supported") || vl.startsWith("not_supported"))
    return "not supported";
  if (vl.startsWith("weakened")) return "weakened";
  if (vl.startsWith("inconclusive")) return "inconclusive";
  return "run pending";
}
