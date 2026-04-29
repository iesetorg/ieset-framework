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

interface MovementYaml {
  movement_id: string;
  name: string;
  countries: string[];
  timeframe: { start: number; end: number | string };
  position_alignments?: { position_id: string; alignment: string }[];
  scope?: "national" | "subnational" | "supranational";
}

const REPO_ROOT = resolve(process.cwd(), "..");
const NOW = new Date().getUTCFullYear();
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
      iso3: ISO_NUMERIC_TO_ALPHA3[numeric] ?? null,
      name: f.properties?.name ?? numeric,
      d: path(f) ?? "",
    };
  });
}

async function loadMovements(): Promise<AtlasMovement[]> {
  const dir = join(REPO_ROOT, "movements");
  if (!existsSync(dir)) return [];
  const entries = await readdir(dir);
  const out: AtlasMovement[] = [];
  for (const e of entries) {
    if (!e.endsWith(".yaml") || e.startsWith("_")) continue;
    const raw = await readFile(join(dir, e), "utf8");
    const doc = yaml.load(raw) as MovementYaml | null;
    if (!doc?.movement_id) continue;
    const start =
      typeof doc.timeframe?.start === "number"
        ? doc.timeframe.start
        : Number.isFinite(parseInt(String(doc.timeframe?.start), 10))
        ? parseInt(String(doc.timeframe.start), 10)
        : 1900;
    const endRaw = doc.timeframe?.end;
    const end =
      typeof endRaw === "number"
        ? endRaw
        : endRaw === "ongoing" || endRaw === "present"
        ? ONGOING_SENTINEL
        : Number.isFinite(parseInt(String(endRaw), 10))
        ? parseInt(String(endRaw), 10)
        : ONGOING_SENTINEL;
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
    });
  }
  return out;
}

export const metadata = {
  title: "Atlas — movements over time",
  description:
    "Interactive world map of every governing movement in the library, with a year slider. Hover a country to see active movements at that point in time.",
};

export default async function AtlasPage() {
  const [movements, paths] = await Promise.all([
    loadMovements(),
    loadCountryPaths(),
  ]);
  const yearMin = movements.length
    ? Math.max(1900, Math.min(...movements.map((m) => m.start)))
    : 1900;
  const yearMax = NOW;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[30px] font-semibold tracking-[-0.02em] md:text-[34px]">
        Atlas
      </h1>
      <p className="mb-6 max-w-[780px] text-[16px] leading-[1.55] text-muted">
        Drag the slider to a year. Each shaded country has at least one
        movement in the library that was governing at that moment. Hover for
        the names; click through on the movement page itself for the policy
        fingerprint.
      </p>

      <WorldMap
        movements={movements}
        paths={paths}
        yearMin={yearMin}
        yearMax={yearMax}
      />
    </div>
  );
}
