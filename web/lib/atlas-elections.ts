/** Election verification is separate from authored movement/policy coding. */
export interface ElectionReview {
  country: string;
  iso3: string;
  election_date: string;
  election_type: string;
  result_status: "final" | "provisional" | "runoff_pending" | "unverified";
  result_summary: string;
  government_status: "formed" | "incumbent_continues" | "formation_pending" | "unverified";
  government_summary: string;
  government_start_date?: string;
  checked_on: string;
  sources: { title: string; url: string }[];
  movement_ids: string[];
  superseded_movement_ids?: string[];
  /** A separately verified predecessor retirement can precede government formation. */
  superseded_on?: string;
  coverage_note?: string;
}

export interface MovementInterval {
  movement_id: string;
  countries: string[];
  start: number;
  end: number;
  scope?: "national" | "subnational" | "supranational";
  /** All declared policy references resolve to authored policy records; not a verdict on their claims. */
  policy_coding_ready?: boolean;
}

function isDate(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value))
    && new Date(value).toISOString().slice(0, 10) === value;
}

/** Fail visibly on malformed or conflicting source data, rather than inventing a fallback. */
export function parseElectionReviews(value: unknown, label = "Election reviews"): ElectionReview[] {
  if (!Array.isArray(value)) throw new Error(`${label}: expected an array`);
  const seen = new Set<string>();
  return value.map((entry, index) => {
    const fail = (message: string): never => { throw new Error(`${label}[${index}]: ${message}`); };
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) fail("expected a record");
    const row = entry as Record<string, unknown>;
    for (const field of ["country", "election_type", "result_summary", "government_summary"]) {
      if (typeof row[field] !== "string" || !(row[field] as string).trim()) fail(`missing ${field}`);
    }
    if (typeof row.iso3 !== "string" || !/^[A-Z]{3}$/.test(row.iso3)) fail("invalid iso3");
    const iso3 = row.iso3 as string;
    if (seen.has(iso3)) fail(`duplicate country ${iso3}`);
    seen.add(iso3);
    if (!isDate(row.election_date) || !isDate(row.checked_on)) fail("invalid election_date or checked_on");
    if (String(row.election_date) > String(row.checked_on)) fail("election date is after its review date");
    if (!["final", "provisional", "runoff_pending", "unverified"].includes(String(row.result_status))) fail("invalid result_status");
    if (!["formed", "incumbent_continues", "formation_pending", "unverified"].includes(String(row.government_status))) fail("invalid government_status");
    if (row.government_start_date !== undefined && !isDate(row.government_start_date)) fail("invalid government_start_date");
    if (row.superseded_on !== undefined && !isDate(row.superseded_on)) fail("invalid superseded_on");
    if (row.coverage_note !== undefined && typeof row.coverage_note !== "string") fail("invalid coverage_note");
    if (row.government_status === "formed" && !isDate(row.government_start_date)) fail("formed government needs a start date");
    for (const field of ["movement_ids", "superseded_movement_ids"]) {
      if (field === "superseded_movement_ids" && row[field] === undefined) continue;
      if (!Array.isArray(row[field]) || !(row[field] as unknown[]).every(id => typeof id === "string" && /^[a-z][a-z0-9_]*[a-z0-9]$/.test(id))) fail(`invalid ${field}`);
    }
    if ((row.movement_ids as string[]).some(id => (row.superseded_movement_ids as string[] | undefined)?.includes(id))) fail("current and superseded movement IDs overlap");
    if (!Array.isArray(row.sources) || !row.sources.length) fail("sources required");
    for (const source of row.sources as unknown[]) {
      if (!source || typeof source !== "object") fail("invalid source");
      const item = source as Record<string, unknown>;
      if (typeof item.title !== "string" || !item.title.trim() || typeof item.url !== "string") fail("invalid source title or URL");
      try {
        const url = new URL(item.url as string);
        if (!["https:", "http:"].includes(url.protocol)) fail("source URL must use HTTP(S)");
      } catch { fail("invalid source URL"); }
    }
    return row as unknown as ElectionReview;
  });
}

export function governmentIsEffective(review: ElectionReview, year: number, asOf: string): boolean {
  return isDate(asOf) && year === Number(asOf.slice(0, 4))
    && review.checked_on <= asOf
    && review.government_status === "formed"
    && !!review.government_start_date && review.government_start_date <= asOf;
}

function supersessionIsEffective(review: ElectionReview, year: number, asOf: string): boolean {
  return governmentIsEffective(review, year, asOf)
    || (isDate(asOf) && year === Number(asOf.slice(0, 4)) && review.checked_on <= asOf
      && !!review.superseded_on && review.superseded_on <= asOf);
}

/** Annual historical slices stay intact. A completed handover or separately verified retirement suppresses a predecessor. */
export function indexAtlasMovements<T extends MovementInterval>(
  movements: T[], reviews: ElectionReview[], year: number, asOf: string,
): Map<string, T[]> {
  const byCountry = new Map(reviews.map(review => [review.iso3, review]));
  const active = new Map<string, T[]>();
  for (const movement of movements) {
    if (movement.start > year || movement.end < year) continue;
    for (const iso3 of movement.countries) {
      const review = byCountry.get(iso3);
      if (review && isDate(asOf) && year === Number(asOf.slice(0, 4))
        && review.checked_on <= asOf && review.government_start_date
        && review.government_start_date > asOf
        && review.movement_ids.includes(movement.movement_id)) continue;
      if (review && supersessionIsEffective(review, year, asOf)
        && review.superseded_movement_ids?.includes(movement.movement_id)) continue;
      const list = active.get(iso3) ?? [];
      list.push(movement);
      active.set(iso3, list);
    }
  }
  return active;
}

/** Missing movements or unresolved policy references must not imply a coded current government. */
export function governmentNeedsCoding(
  review: ElectionReview, movements: MovementInterval[], year: number, asOf: string,
): boolean {
  const knownCurrentGovernment = supersessionIsEffective(review, year, asOf)
    || (isDate(asOf) && year === Number(asOf.slice(0, 4)) && review.checked_on <= asOf
      && review.government_status === "incumbent_continues"
      && (!review.government_start_date || review.government_start_date <= asOf));
  return knownCurrentGovernment
    && !movements.some(movement => review.movement_ids.includes(movement.movement_id)
      && movement.policy_coding_ready !== false
      && (!review.government_start_date || review.government_start_date <= asOf)
      && movement.countries.includes(review.iso3)
      && (movement.scope ?? "national") === "national"
      && movement.start <= year && movement.end >= year);
}

export const RESULT_LABELS: Record<ElectionReview["result_status"], string> = {
  final: "Final result", provisional: "Provisional result",
  runoff_pending: "Runoff pending", unverified: "Result unverified",
};
export const GOVERNMENT_LABELS: Record<ElectionReview["government_status"], string> = {
  formed: "Government formed", incumbent_continues: "Incumbent continues",
  formation_pending: "Government formation pending", unverified: "Government unverified",
};
