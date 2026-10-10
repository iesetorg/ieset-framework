import assert from "node:assert/strict";
import test from "node:test";

import { classifyMovementTone } from "../lib/movement_tone.ts";

test("bare military references in doctrine do not set tone", () => {
  assert.equal(classifyMovementTone({
    movement_id: "civilian_parliamentary_government",
    coalition: "Elected parliamentary majority with military-cadre appointments",
    doctrine: "Discussed military spending and military history",
    axes_summary: [{ axis: "fiscal.transfer_expansion", direction: "+", magnitude: "moderate" }],
  }), "left");
});

test("specific military rule, reviewed coup-era IDs, and strong terms remain authoritarian", () => {
  assert.equal(classifyMovementTone({
    movement_id: "military_rule_example", coalition: "Military junta", doctrine: "Market reform",
  }), "auth");
  assert.equal(classifyMovementTone({
    movement_id: "mmr_burmese_way_to_socialism_1962", coalition: "Revolutionary Council",
  }), "auth");
  assert.equal(classifyMovementTone({
    movement_id: "current_coup_regime", coalition: "Military junta", doctrine: "Took power in a coup",
  }), "auth");
});

test("whole-word match and reviewed historical references avoid false regime tags", () => {
  assert.equal(classifyMovementTone({
    movement_id: "coupled_policy", coalition: "Elected coalition", doctrine: "Tightly coupled policies",
    axes_summary: [{ axis: "fiscal.transfer_expansion", direction: "+", magnitude: "moderate" }],
  }), "left");
  assert.notEqual(classifyMovementTone({
    movement_id: "argentina_alfonsin_ucr_1983_1989", coalition: "Elected UCR government",
    doctrine: "Prosecuted the preceding junta",
  }), "auth");
});
