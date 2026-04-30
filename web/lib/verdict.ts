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

// ---------------------------------------------------------------------------
// Falsification-rule sharpening detector.
//
// Many specs in the library still carry the generic stub-promotion boilerplate
// in their falsification.rule field. The auto-grader will happily emit
// "supported / refuted / partial" against that boilerplate, but the verdict is
// against a generic "p<0.10 + correct sign" rule, NOT against a dispositive
// pre-registered threshold a fair reader of the claim would defend.
//
// We detect that text and downgrade those verdicts to amber regardless of what
// the diagnostics.json says. Same gating logic the canonical-basket gate uses
// for social-outcome claims, applied to falsification-rule quality.
//
// The full boilerplate string (all variants seen) keys off the unique tail
// phrase "when this stub is promoted from draft" — that text never appears in
// any sharpened spec.
const STUB_RULE_MARKER = "when this stub is promoted from draft";

export function isStubFalsificationRule(rule: string | undefined): boolean {
  if (!rule) return false;
  return rule.toLowerCase().includes(STUB_RULE_MARKER);
}

/**
 * Like verdictTone() but downgrades to amber when the falsification rule is
 * still the stub boilerplate. Pass the spec's falsification.rule alongside
 * the verdict string. If the rule is sharpened, this is identical to
 * verdictTone(verdict). If the rule is boilerplate, green and red both
 * collapse to amber so the reader doesn't see clean SUPPORTED / refuted on
 * an unsharpened spec.
 */
export function verdictToneRespectingRule(
  verdict: string | undefined,
  falsificationRule: string | undefined
): VerdictTone {
  const baseTone = verdictTone(verdict);
  if (!isStubFalsificationRule(falsificationRule)) return baseTone;
  // Boilerplate rule: collapse decisive tones to amber.
  if (baseTone === "green" || baseTone === "red") return "amber";
  return baseTone;
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
