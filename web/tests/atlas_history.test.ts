import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { buildAtlasCoverage, earliestNationalYear, historicalEventsAtYear, countryMatchesHistorySearch, constitutionalLayerBounds,
  type HistoricalMovement, type CountryHistoricalContext } from "../lib/atlas-history.ts";
const record = (movement_id: string, start: number, end: number, extra = {}): HistoricalMovement => ({
  movement_id, name: movement_id, countries: ["FRA"], start, end, ...extra,
});

describe("atlas historical coverage", () => {
  it("unlocks eighteenth-century national history without inventing dates for missing records", () => {
    const rows = [record("french_assembly", 1789, 1791), record("bad", NaN, 2026),
      record("state", 1600, 1700, { scope: "subnational" }),
      record("supranational", 1500, 1800, { scope: "supranational" }),
      record("duplicate_context", 1700, 1800, { country_drift_role: "context_only" }),
      record("future", 2030, 2035), record("reversed", 1701, 1700)];
    assert.equal(earliestNationalYear(rows, 2026), 1789);
    assert.equal(earliestNationalYear([], 2026), 2026);
  });
  it("retains every registry country and non-map historical polity without fabricating coverage", () => {
    const rows = buildAtlasCoverage([{ iso3: "FRA", name: "France" }, { iso3: "ISL", name: "Iceland" }],
      [record("first", 1789, 1791), record("next", 1792, 1799), record("later", 1804, 1810),
        record("context", 1700, 2026, { country_drift_role: "context_only" }),
        record("old_state", 1922, 1991, { countries: ["SUN"] })], [], 2026);
    const france = rows.find(r => r.iso3 === "FRA")!;
    assert.equal(france.first_national_year, 1789);
    assert.equal(france.national_movement_count, 3);
    assert.equal(france.context_only_movement_count, 1);
    assert.deepEqual(france.intervals, [{ start: 1789, end: 1799 }, { start: 1804, end: 1810 }]);
    assert.deepEqual(france.gaps, [{ start: 1800, end: 1803 }]);
    assert.equal(rows.find(r => r.iso3 === "ISL")!.first_national_year, null);
    assert.ok(rows.find(r => r.iso3 === "SUN"));
  });
  it("exposes policy-only history without turning a dated policy into a movement interval", () => {
    const [row] = buildAtlasCoverage([{ iso3: "FRA", name: "France" }], [],
      [{ policy_id: "bank", title: "Bank", countries: ["FRA"], year: 1800,
        date_basis: "enacted_date", status: "candidate" }], 2026);
    assert.equal(row.first_policy_year, 1800);
    assert.equal(row.national_policy_count, 1);
    assert.equal(row.first_national_year, null);
    assert.deepEqual(row.intervals, []);
  });
  it("finds countries by accented official names, familiar names, and source-native labels", () => {
    const country = { iso3: "CIV", name: "Côte d'Ivoire" };
    assert.equal(countryMatchesHistorySearch(country, undefined, "cote divoire"), true);
    assert.equal(countryMatchesHistorySearch(country, undefined, "Ivory Coast"), true);
    assert.equal(countryMatchesHistorySearch({ iso3: "TUR", name: "Türkiye" },
      { source_country_names: ["Turkey/Ottoman Empire"] } as CountryHistoricalContext, "Ottoman"), true);
    assert.equal(countryMatchesHistorySearch(country, undefined, "Norway"), false);
  });
  it("extends context navigation to a primary-source event without filling the years between it and CCP", () => {
    const supplement = { iso3: "SMR", coverage: { start_year: 1600, end_year: 1974 },
      events: [{ id: "statutes", start_year: 1600 }, { id: "declaration", start_year: 1974 }] } as CountryHistoricalContext;
    assert.deepEqual(constitutionalLayerBounds(null, [supplement], 2026), { start: 1600, end: 1974 });
    assert.equal(historicalEventsAtYear(supplement, 1700).length, 0);
  });
  it("does not forward-fill a constitutional event or extend past source coverage", () => {
    const context: CountryHistoricalContext = { iso3: "FRA", title: "France", summary: "Source observations",
      checked_on: "2026-10-09", sources: [], source_country_names: ["France"], status: "recorded",
      coverage: { start_year: 1789, end_year: 2025 }, events: [
        { id: "constitution", start_year: 1791, title: "Constitution", summary: "Observed event", sources: [] },
        { id: "last", start_year: 2025, title: "Last observed year", summary: "Observed event", sources: [] },
      ] };
    assert.equal(historicalEventsAtYear(context, 1791).length, 1);
    assert.equal(historicalEventsAtYear(context, 1792).length, 0);
    assert.equal(historicalEventsAtYear(context, 2026).length, 0);
  });
});
