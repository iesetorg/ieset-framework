/** Fail-closed match against the checked-in Git-history school forecast gate. */
export interface SchoolPredictionTimingRow {
  position_id: string;
  claim_index: number;
  hypothesis_id: string;
  claim: string | null;
  scope: unknown;
  school_prediction: string;
  polarity: string;
  eligible: boolean;
  status: string;
}

function stable(value: unknown): string {
  if (value === undefined || value === null) return "null";
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right));
    return `{${entries.map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function canScoreSchoolPrediction(
  row: SchoolPredictionTimingRow | undefined,
  positionId: string,
  claimIndex: number,
  claim: { claim: string; linked_hypothesis_id: string; scope?: unknown },
  prediction: string,
  polarity: string,
): boolean {
  return Boolean(
    row?.eligible === true &&
    row.position_id === positionId &&
    row.claim_index === claimIndex &&
    row.hypothesis_id === claim.linked_hypothesis_id &&
    row.claim === claim.claim &&
    row.school_prediction === prediction &&
    row.polarity === polarity &&
    stable(row.scope) === stable(claim.scope)
  );
}
