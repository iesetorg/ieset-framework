import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";

import { REPO_ROOT } from "./content";

/**
 * Per-country positional drift trajectories.
 *
 * The framework codes every movement on directional axes (fiscal.spending_level
 * +/-/0, regulatory.labour_market_flexibility +/-/0, etc.). When you cumulate
 * those tags over time for a country, you get a trajectory of coded movement
 * direction. Most tags are attributed to a movement's start as a period proxy;
 * reviewed axis years are exceptions. The composite "statist drift"
 * index sums the pro-state axes minus the pro-market axes so you can see in
 * a single number whether a country has moved toward or away from a
 * larger/more-redistributive state. It is not an annual enactment timeline.
 *
 * Data is computed by `scripts/compute_country_drift.py` from the movements
 * corpus and emitted as `data/derived/country_drift.json`. We load it once
 * at module-init and serve it to every page that needs it.
 */

export interface CountryDrift {
  axes: Record<string, number[]>;
  statist_drift: number[];
  movements: Array<{
    movement_id: string;
    name: string;
    leader_label?: string | null;
    year: number;
    end: number | null;
    tone?: "left" | "right" | "centrist" | "auth" | "neutral";
  }>;
  movement_count: number;
  /** Earlier array zeros are unobserved placeholders, not stable policy. */
  first_coded_year: number;
  explicit_axis_timing: Array<{
    movement_id: string;
    axis: string;
    movement_start: number;
    attribution_year: number;
    basis: string;
  }>;
}

export interface DriftDataset {
  year_min: number;
  year_max: number;
  years: number[];
  axes: string[];
  countries: Record<string, CountryDrift>;
  pro_state_axes: string[];
  pro_market_axes: string[];
  timing_model: string;
  timing_summary: {
    explicit_axis_year_entries: number;
    movement_start_proxy_entries: number;
    unresolved_later_year_rationale_entries: number;
    manual_review_note_entries: number;
    review_queue_entries: number;
    unresolved_movements: number;
  };
}

/** Observed level data, kept separate from the constructed drift score. */
export interface DriftContextObservation {
  metric_id: string;
  label: string;
  value: number;
  unit: string;
  transformation: string;
  observed_year: number;
  relation_to_first_coded_year: "opening" | "later_only";
  source_url: string;
  definition_url: string;
  publisher: string;
  license: string;
  license_url: string;
  vintage_file: string;
  vintage_sha256: string;
  caveat: string;
}

export interface DriftStartingContext {
  first_coded_year: number;
  fiscal: DriftContextObservation | null;
  market_institutions: DriftContextObservation | null;
  market_institutions_note: string;
  market_institutions_source_url: string;
  historical_context: {
    as_of_year: number;
    summary: string;
    sources: Array<{ label: string; url: string }>;
  } | null;
}

export interface DriftStartingContextDataset {
  schema: "ieset-country-drift-starting-context-v1";
  opening_window_years: number;
  method: string;
  countries: Record<string, DriftStartingContext>;
}

let _cache: Promise<DriftDataset | null> | null = null;

export function loadDrift(): Promise<DriftDataset | null> {
  if (_cache) return _cache;
  _cache = (async () => {
    const path = join(REPO_ROOT, "data", "derived", "country_drift.json");
    if (!existsSync(path)) return null;
    return JSON.parse(await readFile(path, "utf8")) as DriftDataset;
  })();
  return _cache;
}

let _startingContextCache: Promise<DriftStartingContextDataset | null> | null = null;

export function loadDriftStartingContext(): Promise<DriftStartingContextDataset | null> {
  if (_startingContextCache) return _startingContextCache;
  _startingContextCache = (async () => {
    const path = join(REPO_ROOT, "data", "derived", "country_drift_starting_context.json");
    if (!existsSync(path)) return null;
    return JSON.parse(await readFile(path, "utf8")) as DriftStartingContextDataset;
  })();
  return _startingContextCache;
}

/**
 * For an overview chart, return the N countries with the most movement
 * coverage so the trajectories aren't built from a single data point.
 */
export function topCoveredCountries(
  d: DriftDataset,
  n = 10,
  filter?: (iso3: string) => boolean
): string[] {
  const entries = Object.entries(d.countries)
    .filter(([iso3]) => (filter ? filter(iso3) : true))
    .sort(([, a], [, b]) => b.movement_count - a.movement_count)
    .slice(0, n)
    .map(([iso3]) => iso3);
  return entries;
}

/** ISO3 -> human-readable country names for the drift dataset. */
export const COUNTRY_NAME: Record<string, string> = {
  USA: "United States",
  GBR: "United Kingdom",
  DEU: "Germany",
  FRA: "France",
  ITA: "Italy",
  ESP: "Spain",
  PRT: "Portugal",
  GRC: "Greece",
  NLD: "Netherlands",
  BEL: "Belgium",
  IRL: "Ireland",
  AUT: "Austria",
  CHE: "Switzerland",
  SWE: "Sweden",
  NOR: "Norway",
  DNK: "Denmark",
  FIN: "Finland",
  POL: "Poland",
  HUN: "Hungary",
  CZE: "Czechia",
  SVK: "Slovakia",
  ROU: "Romania",
  RUS: "Russia",
  CHN: "China",
  JPN: "Japan",
  KOR: "South Korea",
  IND: "India",
  IDN: "Indonesia",
  VNM: "Vietnam",
  THA: "Thailand",
  PHL: "Philippines",
  MYS: "Malaysia",
  PAK: "Pakistan",
  BGD: "Bangladesh",
  LKA: "Sri Lanka",
  AUS: "Australia",
  NZL: "New Zealand",
  CAN: "Canada",
  MEX: "Mexico",
  BRA: "Brazil",
  ARG: "Argentina",
  CHL: "Chile",
  COL: "Colombia",
  PER: "Peru",
  VEN: "Venezuela",
  BOL: "Bolivia",
  ECU: "Ecuador",
  URY: "Uruguay",
  CUB: "Cuba",
  SLV: "El Salvador",
  ZAF: "South Africa",
  NGA: "Nigeria",
  KEN: "Kenya",
  GHA: "Ghana",
  ETH: "Ethiopia",
  EGY: "Egypt",
  TUR: "Turkey",
  IRN: "Iran",
  ISR: "Israel",
  SAU: "Saudi Arabia",
  ARE: "United Arab Emirates",
  LBN: "Lebanon",
  TZA: "Tanzania",
  RWA: "Rwanda",
  BWA: "Botswana",
  ZMB: "Zambia",
  ZWE: "Zimbabwe",
  NIC: "Nicaragua",
  SGP: "Singapore",
  YUG: "Yugoslavia",
  CSK: "Czechoslovakia",
  SUN: "Soviet Union",
  AFG: "Afghanistan",
  AGO: "Angola",
  BGR: "Bulgaria",
  BLR: "Belarus",
  CIV: "Cote d'Ivoire",
  COD: "Democratic Republic of the Congo",
  CRI: "Costa Rica",
  DZA: "Algeria",
  IRQ: "Iraq",
  KAZ: "Kazakhstan",
  KHM: "Cambodia",
  KWT: "Kuwait",
  LAO: "Laos",
  MAR: "Morocco",
  MMR: "Myanmar",
  PNG: "Papua New Guinea",
  SEN: "Senegal",
  SYR: "Syria",
  TUN: "Tunisia",
  TWN: "Taiwan",
  UKR: "Ukraine",
  BDI: "Burundi",
  BEN: "Benin",
  BFA: "Burkina Faso",
  BHR: "Bahrain",
  CAF: "Central African Republic",
  CMR: "Cameroon",
  COG: "Republic of the Congo",
  COM: "Comoros",
  CPV: "Cabo Verde",
  CYP: "Cyprus",
  DJI: "Djibouti",
  ERI: "Eritrea",
  ESH: "Western Sahara",
  EST: "Estonia",
  GAB: "Gabon",
  GIN: "Guinea",
  GMB: "Gambia",
  GNB: "Guinea-Bissau",
  GNQ: "Equatorial Guinea",
  HRV: "Croatia",
  JOR: "Jordan",
  LBR: "Liberia",
  LBY: "Libya",
  LSO: "Lesotho",
  LTU: "Lithuania",
  LUX: "Luxembourg",
  LVA: "Latvia",
  MDG: "Madagascar",
  MLI: "Mali",
  MLT: "Malta",
  MOZ: "Mozambique",
  MRT: "Mauritania",
  MUS: "Mauritius",
  MWI: "Malawi",
  NAM: "Namibia",
  NER: "Niger",
  OMN: "Oman",
  PRY: "Paraguay",
  PSE: "Palestine",
  QAT: "Qatar",
  SDN: "Sudan",
  SLE: "Sierra Leone",
  SOM: "Somalia",
  SSD: "South Sudan",
  STP: "São Tomé and Príncipe",
  SVN: "Slovenia",
  SWZ: "Eswatini",
  SYC: "Seychelles",
  TCD: "Chad",
  TGO: "Togo",
  UGA: "Uganda",
  YEM: "Yemen",
};

export function countryName(iso3: string): string {
  return COUNTRY_NAME[iso3] ?? iso3;
}
