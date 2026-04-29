import { loadAllPolicies, type Policy } from "@/lib/policies";
import { loadAxes } from "@/lib/content";
import { loadPolicyPositionAlignments } from "@/lib/matching";
import {
  PolicyFilterTable,
  type PolicyRow,
} from "@/components/policies/PolicyFilterTable";

// Slim each Policy down to just the fields the client filter table renders,
// so we don't ship description / references / steelman HTML over the wire.
function policyToRow(p: Policy): PolicyRow {
  const enactedLabel = p.timeframe.enacted_date
    ? p.timeframe.enacted_date.slice(0, 7)
    : String(p.timeframe.start);
  return {
    policy_id: p.policy_id,
    title: p.title,
    countries: p.countries,
    start_year: p.timeframe.start,
    enacted_label: enactedLabel,
    axes_moved: (p.axes_moved ?? []).map((a) => ({
      axis: a.axis,
      direction: a.direction,
    })),
  };
}

export const metadata = {
  title: "Policies",
  description:
    "Specific policy reforms coded on channel-separated axes. Each policy links to the empirical hypotheses that test its outcomes.",
};

export default async function PoliciesIndex() {
  const [all, axesMap, policyPositions] = await Promise.all([
    loadAllPolicies(),
    loadAxes(),
    loadPolicyPositionAlignments(),
  ]);
  const countries = new Set(all.flatMap((p) => p.countries));
  const rows = all.map(policyToRow);

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[30px] font-semibold tracking-[-0.02em] md:text-[34px]">
        Policies
      </h1>
      <p className="mb-6 max-w-[780px] text-[17px] leading-[1.55] text-muted">
        Each policy is a specific reform — a law, tariff, spending programme,
        central-bank decision — coded by what it moved on each
        channel-separated axis (fiscal, regulatory, monetary, institutional).
        Policies are the matching unit for finding historical analogues of a
        proposed reform; the linked hypotheses test the outcomes.
      </p>

      <div className="mb-3 text-[13px] text-muted">
        {all.length} policies across {countries.size} countries
      </div>

      {/* COMBINED LEGEND — channel colours + alignment glyphs */}
      <div className="mb-6 grid gap-2 text-[11px] text-muted md:grid-cols-2">
        <div className="flex flex-wrap items-center gap-3">
          <span className="sc text-[10px]">axis channel</span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#eef3fb", border: "1px solid #cad8eb" }}
            />
            fiscal
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#f3eef6", border: "1px solid #dccae6" }}
            />
            regulatory
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#fdf2e9", border: "1px solid #ecd2b5" }}
            />
            monetary
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#eef6ef", border: "1px solid #c8dccc" }}
            />
            institutional
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
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
      </div>

      <PolicyFilterTable
        rows={rows}
        axesMap={axesMap}
        policyPositions={policyPositions}
      />
    </div>
  );
}
