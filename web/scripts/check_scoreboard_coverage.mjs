import { readFileSync } from "node:fs";
import { join } from "node:path";

const out = join(process.cwd(), "out");
const scoreboard = JSON.parse(readFileSync(join(out, "api", "scoreboard.json"), "utf8"));
const html = readFileSync(join(out, "scoreboard", "index.html"), "utf8");
const schools = scoreboard.positions ?? [];

if (schools.length !== scoreboard.ranked_school_count) {
  throw new Error("The exported scoreboard omits a ranked school");
}

let linkedClaims = 0;
for (const school of schools) {
  const positionId = school.position_id;
  const browseUrl = `/pos/${positionId}/#linked-hypotheses`;
  if (!html.includes(`href="${browseUrl}"`)) {
    throw new Error(`The scoreboard does not link to ${positionId}'s hypotheses`);
  }

  const schoolHtml = readFileSync(
    join(out, "pos", positionId, "index.html"),
    "utf8",
  );
  if (!schoolHtml.includes('id="linked-hypotheses"')) {
    throw new Error(`${positionId} has no linked-hypotheses section`);
  }

  const claimLinks = school.scored_claims ?? [];
  linkedClaims += claimLinks.length;
  if (claimLinks.length !== school.total_claims) {
    throw new Error(`${positionId} claim count differs from its exported links`);
  }
  for (const claim of claimLinks) {
    if (!claim.hypothesis_exists) continue;
    const hypothesisUrl = `/h/${claim.linked_hypothesis_id}/`;
    if (!schoolHtml.includes(`href="${hypothesisUrl}"`)) {
      throw new Error(`${positionId} hides linked hypothesis ${claim.linked_hypothesis_id}`);
    }
  }
}

console.log(`scoreboard coverage: ${schools.length} schools and ${linkedClaims} authored claim links are browsable`);
