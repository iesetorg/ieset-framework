import { readFileSync } from "node:fs";
import { resolve } from "node:path";

interface HoldGroup {
  source: string;
  count: number;
  currently_public: number;
  hypothesis_ids: string[];
}

interface PublicationHoldRegistry {
  schema: string;
  status: string;
  groups: HoldGroup[];
}

const registryPath = resolve(process.cwd(), "..", "engine", "publication_rights_holds.json");
const registry = JSON.parse(readFileSync(registryPath, "utf8")) as PublicationHoldRegistry;

if (registry.schema !== "ieset-publication-rights-holds-v1" ||
    registry.status !== "active_publication_hold" || !Array.isArray(registry.groups)) {
  throw new Error("Invalid publication-rights hold registry");
}

const heldIds = new Set<string>();
let evidenceQualifiedHeld = 0;
for (const group of registry.groups) {
  if (!group.source || !Array.isArray(group.hypothesis_ids) ||
      group.hypothesis_ids.length !== group.count ||
      !Number.isInteger(group.currently_public) ||
      group.currently_public < 0 || group.currently_public > group.count) {
    throw new Error(`Invalid publication-rights hold group: ${group.source ?? "unknown"}`);
  }
  evidenceQualifiedHeld += group.currently_public;
  for (const id of group.hypothesis_ids) {
    if (typeof id !== "string" || !/^[a-z0-9_]+$/.test(id) || heldIds.has(id)) {
      throw new Error(`Duplicate or invalid publication-rights hold ID: ${id}`);
    }
    heldIds.add(id);
  }
}

export const publicationHoldCounts = {
  records: heldIds.size,
  evidenceQualified: evidenceQualifiedHeld,
} as const;

export function isPublicationHeld(hypothesisId: string): boolean {
  return heldIds.has(hypothesisId);
}

export function publicationHeldIds(): ReadonlySet<string> {
  return heldIds;
}
