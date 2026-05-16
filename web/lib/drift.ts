import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";

import { REPO_ROOT } from "./content";

/**
 * Per-country positional drift trajectories.
 *
 * The framework codes every movement on directional axes (fiscal.spending_level
 * +/-/0, regulatory.labour_market_flexibility +/-/0, etc.). When you cumulate
 * those moves over time for a country, you get a trajectory of how the policy
 * mix has drifted relative to where it was. The composite "statist drift"
 * index sums the pro-state axes minus the pro-market axes so you can see in
 * a single number whether a country has moved toward or away from a
 * larger/more-redistributive state since the corpus's start year.
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
}

export interface DriftDataset {
  year_min: number;
  year_max: number;
  years: number[];
  axes: string[];
  countries: Record<string, CountryDrift>;
  pro_state_axes: string[];
  pro_market_axes: string[];
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
};

export function countryName(iso3: string): string {
  return COUNTRY_NAME[iso3] ?? iso3;
}
