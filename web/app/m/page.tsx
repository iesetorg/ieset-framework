import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import yaml from "js-yaml";

import {
  MovementFilterTable,
  type MovementRow,
} from "@/components/movements/MovementFilterTable";

interface Movement extends MovementRow {
  status: string;
}

const REPO_ROOT = resolve(process.cwd(), "..");

async function listMovements(): Promise<Movement[]> {
  const dir = join(REPO_ROOT, "movements");
  if (!existsSync(dir)) return [];
  const entries = await readdir(dir);
  const out: Movement[] = [];
  for (const e of entries) {
    if (!e.endsWith(".yaml")) continue;
    const raw = await readFile(join(dir, e), "utf8");
    const doc = yaml.load(raw) as Movement;
    if (doc?.movement_id) out.push(doc);
  }
  return out.sort((a, b) => a.movement_id.localeCompare(b.movement_id));
}

export const metadata = {
  title: "Movements",
  description:
    "Political movements and governing coalitions scored on policy content, linked to outcome hypotheses.",
};

export default async function MovementsIndex() {
  const all = await listMovements();
  const countryCount = new Set(all.flatMap((m) => m.countries)).size;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[32px] font-semibold tracking-[-0.02em]">
        Movements
      </h1>
      <p className="mb-6 max-w-[780px] text-[17px] text-muted">
        Each entry is a political movement or governing coalition coded by
        what it actually did on each policy axis — not by party label.
        Per the framework&apos;s Invariant 3, Schröder-era labour reform is
        coded market-oriented regardless of SPD; Trump tariffs are coded
        state-interventionist regardless of Republican label.
      </p>
      <div className="mb-3 text-[13px] text-muted">
        {all.length} movements across {countryCount} countries
      </div>

      {/* ALIGNMENT LEGEND */}
      <div className="mb-4 flex flex-wrap items-center gap-3 text-[11px] text-muted">
        <span className="sc text-[10px]">school alignment</span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-[14px] w-[14px] items-center justify-center rounded-sm text-[10px] font-bold"
            style={{ background: "#2c7a4f", color: "#dff1e4" }}
          >
            ✓
          </span>
          aligned
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-[14px] w-[14px] items-center justify-center rounded-sm text-[10px] font-bold"
            style={{ background: "#b7791f", color: "#fdf1da" }}
          >
            ~
          </span>
          partial
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-[14px] w-[14px] items-center justify-center rounded-sm text-[10px] font-bold"
            style={{ background: "#9e2f2f", color: "#f3d9d9" }}
          >
            ✗
          </span>
          opposed
        </span>
      </div>

      <MovementFilterTable rows={all} />
    </div>
  );
}
