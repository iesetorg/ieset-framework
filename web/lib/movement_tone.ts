/**
 * Map a movement to an ideological tone for chart annotation. The tone is
 * based on the movement's coalition string + axes_summary direction pattern,
 * not on the country or party label. Used by /country/[iso3] to colour
 * the drift-trajectory dots.
 *
 * Heuristic rather than principled — the framework already codes axes
 * direction precisely, but this lookup just tags whether the era pulled
 * the country net-statist (left), net-market (right), centrist (mixed),
 * or authoritarian (when democratic accountability is the salient feature
 * regardless of fiscal direction). For the rare cases the heuristic fails
 * we fall back to "neutral" rather than guess.
 */

export type MovementTone = "left" | "right" | "centrist" | "auth" | "neutral";

interface MovementShape {
  movement_id: string;
  axes_summary?: Array<{ axis: string; direction: string; magnitude?: string }>;
  coalition?: string;
  doctrine?: string;
}

/**
 * Compute a movement's net statist-vs-market signal from its axes_summary.
 * Returns +1 (statist), -1 (market), 0 (mixed/none).
 */
export function statistMarketScore(m: MovementShape): number {
  if (!m.axes_summary) return 0;
  const PRO_STATE = new Set([
    "fiscal.tax_progressivity",
    "fiscal.tax_corporate",
    "fiscal.tax_capital",
    "fiscal.transfer_expansion",
    "fiscal.spending_level",
    "fiscal.sectoral_subsidy",
    "regulatory.environmental_stringency",
    "regulatory.financial_deregulation",
    "regulatory.sectoral_licensing",
    "monetary.monetary_expansion_direction",
  ]);
  const PRO_MARKET = new Set([
    "regulatory.labour_market_flexibility",
    "regulatory.product_market_competition",
    "regulatory.trade_openness",
    "monetary.central_bank_independence",
  ]);
  const MAG: Record<string, number> = { weak: 1, moderate: 2, strong: 3 };
  const SIGN: Record<string, number> = { "+": 1, "-": -1, "0": 0, mixed: 0 };
  let score = 0;
  for (const e of m.axes_summary) {
    const sign = SIGN[e.direction] ?? 0;
    const mag = MAG[e.magnitude ?? ""] ?? 1.5;
    const step = sign * mag;
    if (PRO_STATE.has(e.axis)) score += step;
    else if (PRO_MARKET.has(e.axis)) score -= step;
  }
  return score;
}

/** Coalition / doctrine keywords that flag a non-democratic / authoritarian
 *  era. We tag these separately because their direction-of-drift signal is
 *  less informative than the institutional-takeover signal. */
const AUTH_KEYWORDS = [
  "junta",
  "military",
  "dictatorship",
  "authoritarian",
  "single-party",
  "one-party",
  "coup",
  "martial law",
  "kleptocra",
];

export function classifyMovementTone(m: MovementShape): MovementTone {
  const lcCoalition = (m.coalition ?? "").toLowerCase();
  const lcDoctrine = (m.doctrine ?? "").toLowerCase();
  const isAuth = AUTH_KEYWORDS.some(
    (kw) => lcCoalition.includes(kw) || lcDoctrine.includes(kw)
  );
  if (isAuth) return "auth";
  const score = statistMarketScore(m);
  if (score > 1.0) return "left";
  if (score < -1.0) return "right";
  if (score >= -1.0 && score <= 1.0 && m.axes_summary && m.axes_summary.length > 0) {
    return "centrist";
  }
  return "neutral";
}
