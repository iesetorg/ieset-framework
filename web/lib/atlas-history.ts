/** Authored coverage and sourced historical context are separate from ideology scores. */
export interface AtlasCountry {
  iso3: string;
  name: string;
  kind?: "country_or_territory" | "historical" | "disputed";
}

export interface HistoricalMovement {
  movement_id: string;
  name: string;
  countries: string[];
  start: number;
  end: number;
  scope?: "national" | "subnational" | "supranational";
  country_drift_role?: "primary" | "context_only";
}

export interface AtlasPolicyRecord {
  policy_id: string;
  title: string;
  countries: string[];
  year: number;
  date_basis: "enacted_date" | "timeframe_start";
  status: string;
  scope?: "national" | "subnational" | "supranational";
}

export interface HistoricalSource { title: string; url: string }
export interface HistoricalEvent {
  id: string;
  start_year: number;
  end_year?: number;
  title: string;
  summary: string;
  sources: HistoricalSource[];
  source_event_code?: string;
  source_row_id?: string | number;
}
export interface CountryHistoricalContext {
  iso3: string;
  title: string;
  summary: string;
  checked_on: string;
  sources: HistoricalSource[];
  events: HistoricalEvent[];
  coverage: { start_year: number | null; end_year: number | null };
  status: "recorded" | "no_recorded_events" | "not_covered" | "unmapped";
  mapping_note?: string;
  source_country_names: string[];
}
export interface EarlierHistoricalEntity extends Omit<CountryHistoricalContext, "iso3"> {
  source_country: string;
  source_cowcode: number;
}
export interface ConstitutionalHistory {
  schema_version: number;
  dataset: {
    name: string;
    version: string;
    coverage_start: number;
    coverage_end: number;
    source_url: string;
    citation?: string;
    source_notes?: string[];
    [key: string]: unknown;
  };
  countries: CountryHistoricalContext[];
  historical_entities?: EarlierHistoricalEntity[];
}
export interface CoverageInterval { start: number; end: number }
export interface AtlasCoverage extends AtlasCountry {
  first_national_year: number | null;
  last_national_year: number | null;
  national_movement_count: number;
  authored_movement_count: number;
  subnational_movement_count: number;
  supranational_movement_count: number;
  context_only_movement_count: number;
  national_policy_count: number;
  first_policy_year: number | null;
  intervals: CoverageInterval[];
  gaps: CoverageInterval[];
}

export function validHistoricalYear(year: unknown): year is number {
  return typeof year === "number" && Number.isInteger(year) && year > 0;
}
export function isNationalPrimary(movement: HistoricalMovement): boolean {
  return (movement.scope ?? "national") === "national"
    && movement.country_drift_role !== "context_only";
}
export function validMovementInterval(movement: HistoricalMovement, asOfYear: number): boolean {
  return validHistoricalYear(movement.start) && validHistoricalYear(movement.end)
    && movement.start <= movement.end && movement.start <= asOfYear;
}
/** Use actual national records, never a guessed 1900 start for missing history. */
export function earliestNationalYear(movements: HistoricalMovement[], asOfYear: number): number {
  const years = movements.filter(m => isNationalPrimary(m) && validMovementInterval(m, asOfYear)).map(m => m.start);
  return years.length ? Math.min(...years) : asOfYear;
}

function mergeIntervals(intervals: CoverageInterval[]): CoverageInterval[] {
  const result: CoverageInterval[] = [];
  for (const item of intervals.slice().sort((a, b) => a.start - b.start || a.end - b.end)) {
    const last = result[result.length - 1];
    if (last && item.start <= last.end + 1) last.end = Math.max(last.end, item.end);
    else result.push({ ...item });
  }
  return result;
}

export function buildAtlasCoverage(
  countries: AtlasCountry[], movements: HistoricalMovement[], policies: AtlasPolicyRecord[], asOfYear: number,
): AtlasCoverage[] {
  const registry = new Map(countries.map(country => [country.iso3, country]));
  for (const row of [...movements, ...policies]) {
    for (const iso3 of row.countries) if (!registry.has(iso3)) registry.set(iso3, { iso3, name: iso3 });
  }
  return [...registry.values()].map(country => {
    const authored = movements.filter(m => m.countries.includes(country.iso3) && validMovementInterval(m, asOfYear));
    const national = authored.filter(isNationalPrimary);
    const countryPolicies = policies.filter(p => p.countries.includes(country.iso3)
      && (p.scope ?? "national") === "national" && validHistoricalYear(p.year) && p.year <= asOfYear);
    const intervals = mergeIntervals(national.map(m => ({ start: m.start, end: Math.min(m.end, asOfYear) })));
    return {
      ...country,
      first_national_year: intervals[0]?.start ?? null,
      last_national_year: intervals[intervals.length - 1]?.end ?? null,
      national_movement_count: national.length,
      authored_movement_count: authored.length,
      subnational_movement_count: authored.filter(m => m.scope === "subnational").length,
      supranational_movement_count: authored.filter(m => m.scope === "supranational").length,
      context_only_movement_count: authored.filter(m => m.country_drift_role === "context_only").length,
      national_policy_count: countryPolicies.length,
      first_policy_year: countryPolicies.length ? Math.min(...countryPolicies.map(p => p.year)) : null,
      intervals,
      gaps: intervals.slice(1).map((interval, i) => ({ start: intervals[i].end + 1, end: interval.start - 1 })),
    };
  }).sort((a, b) => a.name.localeCompare(b.name) || a.iso3.localeCompare(b.iso3));
}

/** Source event rows are discrete unless their source explicitly supplies an end year. */
export function historicalEventsAtYear(context: CountryHistoricalContext | undefined, year: number): HistoricalEvent[] {
  if (!context || context.coverage.start_year === null || context.coverage.end_year === null
    || year < context.coverage.start_year || year > context.coverage.end_year) return [];
  return context.events.filter(event => validHistoricalYear(event.start_year)
    && event.start_year <= year && (event.end_year ?? event.start_year) >= year);
}

/** Familiar names supplement official registry and source-native country labels. */
const COUNTRY_SEARCH_ALIASES: Record<string, string[]> = {
  CIV: ["Ivory Coast"], GBR: ["UK", "Britain", "United Kingdom"], USA: ["USA", "United States", "America"],
  KOR: ["South Korea"], PRK: ["North Korea"], TUR: ["Turkey"], RUS: ["Russia"], IRN: ["Iran"],
  SYR: ["Syria"], TZA: ["Tanzania"], VNM: ["Vietnam"], LAO: ["Laos"], BOL: ["Bolivia"],
  VEN: ["Venezuela"], MDA: ["Moldova"], COD: ["DR Congo", "Democratic Republic of the Congo"],
};
export function normalizeHistorySearch(text: string): string {
  return text.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[’']/g, "").toLocaleLowerCase();
}
export function countryMatchesHistorySearch(country: AtlasCountry, context: CountryHistoricalContext | undefined, query: string): boolean {
  return normalizeHistorySearch([country.name, country.iso3, ...(context?.source_country_names ?? []),
    ...(COUNTRY_SEARCH_ALIASES[country.iso3] ?? [])].join(" ")).includes(normalizeHistorySearch(query.trim()));
}

/** Supplement event dates can extend navigation; they never extend source observations between events. */
export function constitutionalLayerBounds(history: ConstitutionalHistory | null, supplements: CountryHistoricalContext[], asOfYear: number): { start: number; end: number } {
  const years = supplements.flatMap(context => context.events.flatMap(event => [event.start_year, event.end_year ?? event.start_year]))
    .filter(year => validHistoricalYear(year) && year <= asOfYear);
  if (history) years.push(history.dataset.coverage_start, Math.min(history.dataset.coverage_end, asOfYear));
  return years.length ? { start: Math.min(...years), end: Math.max(...years) } : { start: asOfYear, end: asOfYear };
}
