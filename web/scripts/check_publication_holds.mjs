#!/usr/bin/env node
import { readdir, readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { loadPublicationHolds, projectEvidenceAudit } from "./publication_holds.mjs";

const repoRoot = resolve(fileURLToPath(new URL("../../", import.meta.url)));
const out = join(repoRoot, "web", "out");
if (!existsSync(out)) throw new Error(`Missing static export: ${out}`);

const holds = loadPublicationHolds(repoRoot);
const source = JSON.parse(await readFile(join(repoRoot, "engine", "evidence_tier_audit.json"), "utf8"));
const expected = projectEvidenceAudit(source, holds);
const published = JSON.parse(await readFile(join(out, "evidence-tiers.json"), "utf8"));
const census = JSON.parse(await readFile(join(out, "stats.json"), "utf8"));
const index = JSON.parse(await readFile(join(out, "api", "hypotheses.json"), "utf8"));

if (published.summary.hypotheses !== expected.summary.hypotheses ||
    published.summary.public_visible !== expected.summary.public_visible ||
    published.records.length !== expected.records.length ||
    census.counts.hypothesis_specs !== expected.summary.hypotheses ||
    census.counts.public_visible_results !== expected.summary.public_visible ||
    census.counts.publication_rights_held_records !== holds.ids.size ||
    census.counts.publication_rights_held_evidence_qualified !== holds.evidenceQualified ||
    index.total !== expected.summary.hypotheses ||
    index.public_count !== expected.summary.public_visible ||
    index.items.length !== expected.summary.hypotheses) {
  throw new Error("Published evidence ledger, census, or hypothesis index has inconsistent rights-filtered counts");
}

const ids = [...holds.ids];
for (const id of ids) {
  for (const path of [
    join(out, "h", id, "index.html"),
    join(out, "h", `${id}.html`),
    join(out, "api", "h", `${id}.json`),
  ]) {
    if (existsSync(path)) throw new Error(`Held result route exists: ${relative(out, path)}`);
  }
}

async function* files(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* files(path);
    else if (entry.isFile()) yield path;
  }
}

const matcher = new RegExp(ids.join("|"));
let scanned = 0;
for await (const path of files(out)) {
  const rel = relative(out, path);
  if (matcher.test(rel) || matcher.test((await readFile(path)).toString("utf8"))) {
    throw new Error(`Held result ID leaked into static export: ${rel}`);
  }
  scanned++;
}

console.log(`publication holds: ${holds.ids.size} records (${holds.evidenceQualified} evidence-qualified) absent from ${scanned} static files`);
console.log(`published corpus: ${expected.summary.hypotheses} records, ${expected.summary.public_visible} public results`);
