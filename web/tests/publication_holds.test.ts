import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { projectEvidenceAudit } from "../scripts/publication_holds.mjs";

function record(hypothesisId: string, visible: boolean, registration: string) {
  return {
    hypothesis_id: hypothesisId,
    public_visible: visible,
    registration_status: registration,
    tier: visible ? "calibration" : "archive",
    verdict_bucket: visible ? "supported" : "missing",
    reference_set: false,
    estimator_floor_failures: [],
    exclusion_reasons: [],
  };
}

function source(...records: ReturnType<typeof record>[]) {
  return { records, reference_set: [], summary: {} };
}

test("holds accept private and run-free public sources only", () => {
  const root = mkdtempSync(join(tmpdir(), "ieset-hold-state-"));
  const holds = { ids: new Set(["held_a", "held_b"]), evidenceQualified: 1 };
  try {
    const privateSource = source(
      record("held_a", true, "verified"),
      record("held_b", false, "legacy_same_commit"),
    );
    assert.equal(projectEvidenceAudit(privateSource, holds, root).summary.public_visible, 0);

    const publicSource = source(
      record("held_a", false, "registered_no_run"),
      record("held_b", false, "registered_no_run"),
    );
    assert.equal(projectEvidenceAudit(publicSource, holds, root).summary.public_visible, 0);

    mkdirSync(join(root, "engine", "runs", "held_a"), { recursive: true });
    assert.throws(
      () => projectEvidenceAudit(publicSource, holds, root),
      /run-free public projection/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("holds reject intermediate visibility and registration states", () => {
  const root = mkdtempSync(join(tmpdir(), "ieset-hold-state-"));
  const holds = { ids: new Set(["held_a", "held_b"]), evidenceQualified: 1 };
  try {
    const staleRegistration = source(
      record("held_a", false, "verified"),
      record("held_b", false, "registered_no_run"),
    );
    assert.throws(
      () => projectEvidenceAudit(staleRegistration, holds, root),
      /run-free public projection/,
    );

    const extraVisible = source(
      record("held_a", true, "verified"),
      record("held_b", true, "verified"),
    );
    assert.throws(
      () => projectEvidenceAudit(extraVisible, holds, root),
      /run-free public projection/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
