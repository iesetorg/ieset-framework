import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import yaml from "js-yaml";
import {
  parseElectionReviews, indexAtlasMovements, governmentNeedsCoding,
  type ElectionReview, type MovementInterval,
} from "../lib/atlas-elections.ts";

const asOf = "2026-10-09";
const review: ElectionReview = {
  country: "Example", iso3: "GBR", election_date: "2026-02-01", election_type: "Parliament",
  result_status: "final", result_summary: "A final result.", government_status: "formed",
  government_summary: "A government took office.", government_start_date: "2026-03-01",
  checked_on: asOf, sources: [{ title: "Official results", url: "https://example.org/results" }],
  movement_ids: ["new_government"], superseded_movement_ids: ["old_government"],
  coverage_note: "A reviewed handover, separate from policy coding.",
};
const oldGovernment: MovementInterval = { movement_id: "old_government", countries: ["GBR"], start: 2024, end: 2026 };
const newGovernment: MovementInterval = { movement_id: "new_government", countries: ["GBR"], start: 2026, end: 2026 };
const ids = (rows: MovementInterval[] | undefined) => rows?.map(row => row.movement_id) ?? [];

describe("atlas reviewed election transitions", () => {
  it("suppresses only an explicitly superseded current government after a completed handover", () => {
    const background = { ...oldGovernment, movement_id: "long_running_policy" };
    assert.deepEqual(ids(indexAtlasMovements([oldGovernment, newGovernment, background], [review], 2026, asOf).get("GBR")),
      ["new_government", "long_running_policy"]);
  });
  it("preserves past annual slices and their within-year overlaps", () => {
    const pastReview = { ...review, government_start_date: "2025-03-01" };
    const successor = { ...newGovernment, start: 2025 };
    assert.deepEqual(ids(indexAtlasMovements([oldGovernment, successor], [pastReview], 2025, asOf).get("GBR")),
      ["old_government", "new_government"]);
  });
  it("does not turn an election result or future start date into an in-office government", () => {
    for (const pending of [
      { ...review, government_status: "formation_pending" as const },
      { ...review, government_status: "unverified" as const },
      { ...review, government_start_date: "2026-11-01" },
      { ...review, checked_on: "2026-11-01" },
      { ...review, government_status: "formation_pending" as const, superseded_on: "2026-11-01" },
    ]) {
      assert.deepEqual(ids(indexAtlasMovements([oldGovernment], [pending], 2026, asOf).get("GBR")), ["old_government"]);
      assert.equal(governmentNeedsCoding(pending, [oldGovernment], 2026, asOf), false);
    }
  });
  it("honours a separately verified retirement while a later election's government formation remains pending", () => {
    const pending = { ...review, government_status: "formation_pending" as const,
      superseded_on: "2026-05-28", movement_ids: [] };
    assert.deepEqual(ids(indexAtlasMovements([oldGovernment], [pending], 2026, asOf).get("GBR")), []);
    assert.equal(governmentNeedsCoding(pending, [oldGovernment], 2026, asOf), true);
    assert.deepEqual(ids(indexAtlasMovements([oldGovernment], [pending], 2025, asOf).get("GBR")), ["old_government"]);
  });
  it("keeps a future-dated successor out of today's map while preserving the incumbent", () => {
    const future = { ...review, government_start_date: "2026-11-01" };
    assert.deepEqual(ids(indexAtlasMovements([oldGovernment, newGovernment], [future], 2026, asOf).get("GBR")), ["old_government"]);
    const pending = { ...review, government_status: "formation_pending" as const, government_start_date: undefined };
    assert.deepEqual(ids(indexAtlasMovements([oldGovernment, newGovernment], [pending], 2026, asOf).get("GBR")), ["old_government", "new_government"]);
  });
  it("retains suppression on the effective date itself and only in the reviewed country", () => {
    const shared = { ...oldGovernment, countries: ["GBR", "IRL"] };
    const active = indexAtlasMovements([shared], [{ ...review, government_start_date: asOf }], 2026, asOf);
    assert.deepEqual(ids(active.get("GBR")), []);
    assert.deepEqual(ids(active.get("IRL")), ["old_government"]);
  });
  it("leaves an uncoded new government unclassified even when older policy episodes remain", () => {
    const background = { ...oldGovernment, movement_id: "long_running_policy" };
    assert.equal(governmentNeedsCoding({ ...review, movement_ids: [] }, [background], 2026, asOf), true);
    assert.equal(governmentNeedsCoding(review, [newGovernment], 2026, asOf), false);
    assert.equal(governmentNeedsCoding(review, [{ ...newGovernment, scope: "subnational" }], 2026, asOf), true);
    assert.equal(governmentNeedsCoding(review, [background], 2025, asOf), false);
    assert.equal(governmentNeedsCoding({ ...review, government_status: "incumbent_continues", movement_ids: [] }, [background], 2026, asOf), true);
  });
  it("does not classify a verified winner from a linked movement with unresolved policy references", () => {
    const unresolved = { ...newGovernment, policy_coding_ready: false };
    assert.equal(governmentNeedsCoding(review, [unresolved], 2026, asOf), true);
    assert.equal(governmentNeedsCoding(review, [{ ...unresolved, policy_coding_ready: true }], 2026, asOf), false);
    assert.equal(governmentNeedsCoding(review, [unresolved], 2025, asOf), false);
  });
});

describe("election review input", () => {
  it("accepts sourced records and rejects invalid dates, statuses, links, conflicting IDs and duplicates", () => {
    assert.deepEqual(parseElectionReviews([review]), [review]);
    for (const bad of [
      { ...review, election_date: "2026-02-30" },
      { ...review, election_date: "2026-11-01" },
      { ...review, checked_on: "today" },
      { ...review, superseded_on: "2026-02-30" },
      { ...review, result_status: "probably_final" },
      { ...review, government_status: "winner" },
      { ...review, government_start_date: undefined },
      { ...review, sources: [] },
      { ...review, sources: [{ title: "Unsafe", url: "javascript:alert(1)" }] },
      { ...review, superseded_movement_ids: ["new_government"] },
    ]) assert.throws(() => parseElectionReviews([bad]));
    assert.throws(() => parseElectionReviews([review, review]), /duplicate country/);
    assert.throws(() => parseElectionReviews({}));
  });

  it("loads the real regional ledgers, with dated reviews and resolvable country-matched movement links", () => {
    const directory = new URL("../../data/atlas/", import.meta.url);
    const files = readdirSync(directory).filter(file => /^election_reviews_[a-z]+\.json$/.test(file));
    assert.ok(files.length > 0, "At least one election review ledger must be present");
    const rows = parseElectionReviews(files.flatMap(file => JSON.parse(readFileSync(new URL(file, directory), "utf8"))));
    assert.ok(rows.length > 0);
    const today = new Date().toISOString().slice(0, 10);
    const movements = new Map<string, { countries: string[] }>();
    const movementDirectory = new URL("../../movements/", import.meta.url);
    for (const file of readdirSync(movementDirectory).filter(file => file.endsWith(".yaml") && !file.startsWith("_"))) {
      const movement = yaml.load(readFileSync(new URL(file, movementDirectory), "utf8")) as { movement_id: string; countries: string[] };
      if (movement?.movement_id) movements.set(movement.movement_id, movement);
    }
    for (const row of rows) {
      assert.ok(row.checked_on <= today, `${row.iso3}: future review date`);
      assert.ok(row.election_date <= row.checked_on, `${row.iso3}: election not yet held at review`);
      for (const id of [...row.movement_ids, ...(row.superseded_movement_ids ?? [])]) {
        const movement = movements.get(id);
        assert.ok(movement, `${row.iso3}: missing movement ${id}`);
        assert.ok(movement.countries.includes(row.iso3), `${row.iso3}: movement ${id} country mismatch`);
      }
    }
  });
});
