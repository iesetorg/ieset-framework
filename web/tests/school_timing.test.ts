import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { canScoreSchoolPrediction, type SchoolPredictionTimingRow } from "../lib/school-timing.ts";

const row: SchoolPredictionTimingRow = {
  position_id: "school",
  claim_index: 3,
  hypothesis_id: "study",
  claim: "The defined exposure increases the outcome.",
  scope: { period: [2020, 2022], countries: ["A", "B"] },
  school_prediction: "supported",
  polarity: "aligned",
  eligible: true,
  status: "prospective_reciprocal",
};

describe("school forecast timing gate", () => {
  it("scores only an exact frozen reciprocal claim", () => {
    const claim = {
      claim: row.claim!, linked_hypothesis_id: "study",
      scope: { countries: ["A", "B"], period: [2020, 2022] },
    };
    assert.equal(canScoreSchoolPrediction(row, "school", 3, claim, "supported", "aligned"), true);
    assert.equal(canScoreSchoolPrediction(row, "school", 3, claim, "falsified", "aligned"), false);
    assert.equal(canScoreSchoolPrediction(row, "school", 3, claim, "supported", "inverted"), false);
    assert.equal(canScoreSchoolPrediction(row, "school", 4, claim, "supported", "aligned"), false);
    assert.equal(canScoreSchoolPrediction(undefined, "school", 3, claim, "supported", "aligned"), false);
  });

  it("fails closed after a claim or scope change", () => {
    const claim = { claim: row.claim!, linked_hypothesis_id: "study", scope: row.scope };
    assert.equal(canScoreSchoolPrediction({ ...row, eligible: false }, "school", 3, claim, "supported", "aligned"), false);
    assert.equal(canScoreSchoolPrediction(row, "school", 3, { ...claim, scope: { period: [2020, 2023] } }, "supported", "aligned"), false);
    assert.equal(canScoreSchoolPrediction(row, "school", 3, { ...claim, claim: "Different mechanism" }, "supported", "aligned"), false);
  });
});
