import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import yaml from "js-yaml";
import * as d3 from "d3";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";
import type { FeatureCollection, Geometry } from "geojson";

import { WorldMap, type AtlasMovement, type CountryPath } from "@/components/atlas/WorldMap";
import { ISO_NUMERIC_TO_ALPHA3 } from "@/lib/iso-numeric-to-alpha3";
import { dominantClusterFor } from "@/lib/position-clusters";
import { parseElectionReviews } from "@/lib/atlas-elections";
import { buildAtlasCoverage, earliestNationalYear, validHistoricalYear,
  type AtlasCountry, type AtlasPolicyRecord, type ConstitutionalHistory, type CountryHistoricalContext } from "@/lib/atlas-history";

interface MovementYaml {
  movement_id: string;
  name: string;
  countries: string[];
  timeframe: { start: number; end: number | string };
  position_alignments?: { position_id: string; alignment: string }[];
  policies?: string[];
  scope?: "national" | "subnational" | "supranational";
  country_drift_role?: "primary" | "context_only";
}

const REPO_ROOT = resolve(process.cwd(), "..");
const NOW = new Date().getUTCFullYear();
const AS_OF = new Date().toISOString().slice(0, 10);
// Encode "ongoing" as a sentinel that's bigger than any current year so the
// slider treats them as active through the present.
const ONGOING_SENTINEL = NOW;

async function loadCountryPaths(): Promise<CountryPath[]> {
  const topoFile = join(REPO_ROOT, "web", "public", "world-110m.json");
  const raw = await readFile(topoFile, "utf8");
  const topology = JSON.parse(raw) as Topology;
  const fc = feature(
    topology,
    topology.objects.countries
  ) as unknown as FeatureCollection<Geometry, { name: string }>;
  const W = 960;
  const H = 520;
  const projection = d3.geoEqualEarth().fitSize([W, H], fc);
  const path = d3.geoPath(projection);
  return fc.features.map((f, idx) => {
    const numeric = String(f.id ?? "");
    // Some topojson features (Antarctica, certain small territories) have no
    // `f.id`, leaving `numeric === ""`. Falling back to a stable per-feature
    // key (name or index) prevents React duplicate-key warnings when multiple
    // un-IDed features get rendered together.
    const stableId =
      numeric ||
      String(f.properties?.name ?? "") ||
      `feature-${idx}`;
    return {
      id: stableId,
      iso3: ISO_NUMERIC_TO_ALPHA3[numeric] ?? (f.properties?.name === "Kosovo" ? "XKX" : null),
      name: f.properties?.name ?? numeric,
      d: path(f) ?? "",
    };
  });
}

async function loadMovements(): Promise<{ movements: AtlasMovement[]; policies: AtlasPolicyRecord[] }> {
  const dir = join(REPO_ROOT, "movements");
  if (!existsSync(dir)) return { movements: [], policies: [] };
  const policies: AtlasPolicyRecord[] = [];
  const policyIds = new Set<string>();
  const policyDir = join(REPO_ROOT, "policies");
  if (existsSync(policyDir)) {
    for (const file of await readdir(policyDir)) {
      if (!file.endsWith(".yaml") || file.startsWith("_")) continue;
      const policy = yaml.load(await readFile(join(policyDir, file), "utf8")) as {
        policy_id?: string; title?: string; countries?: string[]; status?: string;
        timeframe?: { start?: number; enacted_date?: string | Date };
        scope?: "national" | "subnational" | "supranational";
      } | null;
      if (typeof policy?.policy_id !== "string") continue;
      policyIds.add(policy.policy_id);
      const enacted = policy.timeframe?.enacted_date;
      const enactedYear = enacted instanceof Date ? enacted.getUTCFullYear()
        : typeof enacted === "string" && /^\d{4}-\d{2}-\d{2}$/.test(enacted) ? Number(enacted.slice(0, 4)) : undefined;
      const year = enactedYear ?? policy.timeframe?.start;
      if (validHistoricalYear(year)) policies.push({ policy_id: policy.policy_id,
        title: policy.title ?? policy.policy_id, countries: policy.countries ?? [], year,
        date_basis: enactedYear !== undefined ? "enacted_date" : "timeframe_start",
        status: policy.status ?? "candidate", scope: policy.scope });
    }
  }
  const entries = await readdir(dir);
  const out: AtlasMovement[] = [];
  for (const e of entries) {
    if (!e.endsWith(".yaml") || e.startsWith("_")) continue;
    const raw = await readFile(join(dir, e), "utf8");
    const doc = yaml.load(raw) as MovementYaml | null;
    if (!doc?.movement_id) continue;
    const start = doc.timeframe?.start;
    if (!validHistoricalYear(start)) throw new Error(`Atlas movement ${doc.movement_id} has no valid start year`);
    const endRaw = doc.timeframe?.end;
    const end = typeof endRaw === "number" ? endRaw
      : endRaw === "ongoing" || endRaw === "present" || endRaw === undefined ? ONGOING_SENTINEL : NaN;
    if (!validHistoricalYear(end) || end < start) throw new Error(`Atlas movement ${doc.movement_id} has an invalid end year`);
    const dom = dominantClusterFor(doc.position_alignments);
    out.push({
      movement_id: doc.movement_id,
      name: doc.name,
      countries: doc.countries ?? [],
      start,
      end,
      cluster: dom.cluster,
      cluster_score: dom.score,
      scope: doc.scope,
      country_drift_role: doc.country_drift_role,
      policy_coding_ready: Array.isArray(doc.policies) && doc.policies.length > 0
        && doc.policies.every(id => policyIds.has(id)),
    });
  }
  return { movements: out, policies };
}

async function loadElectionReviews() {
  const dir = join(REPO_ROOT, "data", "atlas");
  if (!existsSync(dir)) return [];
  const files = (await readdir(dir)).filter(name => /^election_reviews_[a-z]+\.json$/.test(name)).sort();
  const rows = await Promise.all(files.map(async name =>
    parseElectionReviews(JSON.parse(await readFile(join(dir, name), "utf8")), name)
  ));
  // Validate across files too: two regions must not silently disagree about one country.
  const reviews = parseElectionReviews(rows.flat());
  if (reviews.some(review => review.checked_on > AS_OF)) {
    throw new Error("Atlas election review is dated after the current build date");
  }
  return reviews.sort((a, b) => a.country.localeCompare(b.country));
}

async function loadCountryRegistry(): Promise<AtlasCountry[]> {
  const path = join(REPO_ROOT, "data", "atlas", "countries.json");
  if (!existsSync(path)) return [];
  const rows = JSON.parse(await readFile(path, "utf8")) as AtlasCountry[];
  if (!Array.isArray(rows) || rows.some(row => !/^[A-Z]{3}$/.test(row.iso3) || !row.name)) {
    throw new Error("Invalid atlas country registry");
  }
  return rows;
}

async function loadConstitutionalHistory(): Promise<ConstitutionalHistory | null> {
  const path = join(REPO_ROOT, "data", "atlas", "constitutional_history.json");
  if (!existsSync(path)) return null;
  const data = JSON.parse(await readFile(path, "utf8")) as ConstitutionalHistory;
  if (!Array.isArray(data.countries) || !validHistoricalYear(data.dataset?.coverage_start)
    || !validHistoricalYear(data.dataset?.coverage_end) || data.dataset.coverage_start > data.dataset.coverage_end) {
    throw new Error("Invalid atlas constitutional history dataset");
  }
  return data;
}

async function loadHistoricalSupplements(): Promise<CountryHistoricalContext[]> {
  const path = join(REPO_ROOT, "data", "atlas", "historical_context_supplements.json");
  if (!existsSync(path)) return [];
  const rows = JSON.parse(await readFile(path, "utf8")) as CountryHistoricalContext[];
  if (!Array.isArray(rows) || rows.some(row => !/^[A-Z]{3}$/.test(row.iso3) || !Array.isArray(row.events))) {
    throw new Error("Invalid atlas historical supplements");
  }
  return rows;
}

export const metadata = {
  title: "Atlas — movements over time",
  description:
    "Explore authored policy movements by year, with dated election results, government-formation checks, and sources for selected countries.",
  alternates: { canonical: "https://framework.ieset.org/atlas/" },
};

export default async function AtlasPage() {
  const [corpus, paths, electionReviews, registry, constitutionalHistory, historicalSupplements] = await Promise.all([
    loadMovements(), loadCountryPaths(), loadElectionReviews(), loadCountryRegistry(), loadConstitutionalHistory(), loadHistoricalSupplements(),
  ]);
  const { movements, policies } = corpus;
  const countryRegistry = new Map<string, AtlasCountry>();
  for (const path of paths) if (path.iso3) countryRegistry.set(path.iso3, { iso3: path.iso3, name: path.name });
  for (const country of registry) countryRegistry.set(country.iso3, country);
  const coverage = buildAtlasCoverage([...countryRegistry.values()], movements, policies, NOW);
  const yearMin = earliestNationalYear(movements, NOW);
  const yearMax = NOW;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[30px] font-semibold tracking-[-0.02em] md:text-[34px]">
        Atlas
      </h1>
      <p className="mb-6 max-w-[780px] text-[16px] leading-[1.55] text-muted">
        Explore authored policy movements by year. Colours reflect the library’s
        policy coding; they do not classify an election winner by party name.
        Recent election and government checks appear below the map. Coverage is
        selective, and an ongoing movement is not proof that its government is
        still in office.
      </p>

      <WorldMap
        movements={movements}
        paths={paths}
        yearMin={yearMin}
        yearMax={yearMax}
        electionReviews={electionReviews}
        asOf={AS_OF}
        coverage={coverage}
        policies={policies}
        constitutionalHistory={constitutionalHistory}
        historicalSupplements={historicalSupplements}
      />
    </div>
  );
}
