#!/usr/bin/env python3
"""Build a pre-registration queue from the controlled Heritage robustness wave.

The controlled Heritage runs are candidate screens. They are useful for
triaging Austrian, ordoliberal, and broader market-liberal hypotheses, but they
must not be mapped directly into position scoreboards. A queued item only
becomes scoreboard-eligible after a stronger design is registered before
estimation, run, and validated.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDITS = ROOT / "engine" / "audits"
RUNS = ROOT / "engine" / "runs"


COMPONENT_TO_PROXY = {
    "overall_score": "wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite",
    "property_rights": "wgi:RL.EST",
    "judicial_effectiveness": "wgi:RL.EST",
    "government_integrity": "wgi:CC.EST",
    "tax_burden": "world_bank_wdi:GC.TAX.TOTL.GD.ZS",
    "government_spending": "world_bank_wdi:GC.XPN.TOTL.GD.ZS",
    "business_freedom": "wgi:RQ.EST",
    "labor_freedom": "world_bank_wdi:SL.EMP.TOTL.SP.ZS / OECD labour proxies",
    "monetary_freedom": "world_bank_wdi:FP.CPI.TOTL.ZG + central-bank-institution proxy",
    "trade_freedom": "world_bank_wdi:NE.TRD.GNFS.ZS / tariff proxy",
    "investment_freedom": "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
    "financial_freedom": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
}


COMPONENT_SLUG = {
    "overall_score": "economic_freedom",
    "property_rights": "property_rights",
    "judicial_effectiveness": "judicial_effectiveness",
    "government_integrity": "government_integrity",
    "tax_burden": "tax_burden",
    "government_spending": "government_spending",
    "business_freedom": "business_freedom",
    "labor_freedom": "labor_freedom",
    "monetary_freedom": "monetary_freedom",
    "trade_freedom": "trade_freedom",
    "investment_freedom": "investment_freedom",
    "financial_freedom": "financial_freedom",
}


def controlled_ids() -> list[str]:
    candidates = sorted(AUDITS.glob("heritage_market_controlled_wave_*.ids"))
    if not candidates:
        raise SystemExit("No controlled Heritage wave ids file found")
    return [line.strip() for line in candidates[-1].read_text().splitlines() if line.strip()]


def load_records(ids: list[str]) -> list[dict]:
    records = []
    for hid in ids:
        diag = json.loads((RUNS / hid / "diagnostics.json").read_text())
        ols = diag.get("controlled_ols") or {}
        p_value = ols.get("p_value")
        records.append(
            {
                "hypothesis_id": hid,
                "verdict_label": diag.get("verdict_label"),
                "treatment_component": diag.get("treatment_component"),
                "outcome_source": diag.get("outcome_source"),
                "expected_sign": diag.get("expected_sign"),
                "coef": ols.get("coef"),
                "p_value": p_value if isinstance(p_value, (int, float)) and math.isfinite(p_value) else None,
                "n": ols.get("n"),
            }
        )
    return records


def add_bh_q(records: list[dict]) -> None:
    finite = sorted([(i, rec["p_value"]) for i, rec in enumerate(records) if rec["p_value"] is not None], key=lambda x: x[1])
    m = len(finite)
    q_values = [None] * len(records)
    prev = 1.0
    for rank, (i, p_value) in reversed(list(enumerate(finite, start=1))):
        q_value = min(prev, p_value * m / rank)
        q_values[i] = q_value
        prev = q_value
    for i, q_value in enumerate(q_values):
        records[i]["bh_q_value"] = q_value


def outcome_slug(hypothesis_id: str, component: str) -> str:
    suffix = hypothesis_id.split("heritage_", 1)[1].removesuffix("_income_region_robustness")
    return suffix[len(COMPONENT_SLUG[component]) + 1 :]


def queue_item(rank: int, rec: dict) -> dict:
    component = rec["treatment_component"]
    verdict = rec["verdict_label"]
    if verdict == "SUPPORTED":
        track = "graduate_to_panel_fe_or_event_design"
        next_action = (
            "Register a panel/event robustness spec using the listed time-varying proxy, country/year fixed "
            "effects, income controls, and leave-one-region-out checks."
        )
    elif verdict == "REFUTED":
        track = "respec_or_counter_hypothesis"
        next_action = (
            "Do not publish as a pro-market win. Register the counter-hypothesis or a complementarity spec "
            "that allows market order plus fiscal/welfare capacity."
        )
    else:
        track = "hold_for_data_or_design_upgrade"
        next_action = "Hold unless a stronger treatment measure or country episode is available."
    return {
        "rank": rank,
        "hypothesis_id": rec["hypothesis_id"],
        "controlled_verdict": verdict,
        "scoreboard_eligible": False,
        "scoreboard_gate": "candidate_screen_only__requires_pre_registered_panel_or_event_spec",
        "component": component,
        "outcome_slug": outcome_slug(rec["hypothesis_id"], component),
        "p_value": rec["p_value"],
        "bh_q_value": rec.get("bh_q_value"),
        "coef": rec["coef"],
        "n": rec["n"],
        "graduation_track": track,
        "preregistration_track": track,
        "suggested_time_varying_proxy": COMPONENT_TO_PROXY.get(component, "TBD"),
        "next_action": next_action,
        "run_path": f"engine/runs/{rec['hypothesis_id']}",
    }


def main() -> int:
    ids = controlled_ids()
    records = load_records(ids)
    add_bh_q(records)
    supported = [
        rec
        for rec in records
        if rec["verdict_label"] == "SUPPORTED" and rec.get("bh_q_value") is not None and rec["bh_q_value"] <= 0.10
    ]
    refuted = [
        rec
        for rec in records
        if rec["verdict_label"] == "REFUTED" and rec.get("bh_q_value") is not None and rec["bh_q_value"] <= 0.10
    ]
    supported = sorted(supported, key=lambda rec: (rec["bh_q_value"], rec["p_value"]))[:50]
    refuted = sorted(refuted, key=lambda rec: (rec["bh_q_value"], rec["p_value"]))
    queue = [queue_item(i + 1, rec) for i, rec in enumerate([*supported, *refuted])]

    counts = Counter(item["graduation_track"] for item in queue)
    by_component = defaultdict(Counter)
    for item in queue:
        by_component[item["component"]][item["graduation_track"]] += 1

    out_yaml = ROOT / "engine" / "queue_heritage_market_graduation.yaml"
    out_md = AUDITS / "heritage_market_graduation_queue_2026-05-02.md"
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "engine/audits/heritage_market_controlled_wave_2026-05-02.ids",
        "selection_rule": "Top 50 FDR-supported controlled results plus all FDR-refuted controlled results.",
        "methodology_gate": {
            "scoreboard_status": "not_eligible",
            "reason": (
                "These records are post-estimation candidate screens. They identify hypotheses worth "
                "registering, but they are not scoreboard evidence and must not create position claims "
                "or hypothesis covers_claims."
            ),
            "eligibility_rule": (
                "Create a stronger panel/event-study spec before estimation; run it after registration; "
                "promote to scoreboard only if that registered design passes validation."
            ),
        },
        "counts": dict(counts),
        "queue": queue,
    }
    out_yaml.write_text(yaml.safe_dump(doc, sort_keys=False, width=100))

    lines = [
        "# Heritage Market Pre-Registration Queue - 2026-05-02",
        "",
        "## Methodology Gate",
        "",
        "- Scoreboard status: not eligible.",
        "- These are post-estimation candidate screens, not scoreboard claims.",
        "- Do not create position `falsifiable_specific_claims` or hypothesis `covers_claims` from this queue.",
        "- To advance: register a stronger panel/event spec before estimation, then run and validate it.",
        "",
        "## Selection Rule",
        "",
        "- Top 50 controlled supports with BH/FDR q<=0.10.",
        "- All controlled refutations with BH/FDR q<=0.10.",
        "- Purpose: identify which Heritage market-order results deserve stronger panel/event designs and which fiscal-size claims should be respecified rather than promoted.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Component Mix", ""])
    for component in sorted(by_component):
        lines.append(f"- {component}: {dict(by_component[component])}")
    lines.extend(["", "## Top Queue Items", ""])
    for item in queue[:30]:
        lines.append(
            f"- #{item['rank']} {item['hypothesis_id']} | {item['controlled_verdict']} | "
            f"q={item['bh_q_value']:.4g} | track={item['graduation_track']} | proxy={item['suggested_time_varying_proxy']}"
        )
    out_md.write_text("\n".join(lines) + "\n")
    print(f"wrote {out_yaml.relative_to(ROOT)}")
    print(f"wrote {out_md.relative_to(ROOT)}")
    print(dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
