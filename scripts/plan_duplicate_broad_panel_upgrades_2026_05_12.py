#!/usr/bin/env python3
"""Plan upgrades for duplicate broad-panel throughput verdicts.

The conversion audit intentionally holds broad associational panels when many
hypotheses share the same treatment/outcome/result fingerprint. This script
turns those holds into a concrete work queue: which verdicts collide, which
claim-specific datasets are needed, and which items can move first.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONVERSION_AUDIT = ROOT / "engine/audits/throughput_scoreboard_conversion_2026-05-12.json"
OUT_JSON = ROOT / "engine/audits/duplicate_broad_panel_upgrade_plan_2026-05-12.json"
OUT_MD = ROOT / "engine/audits/duplicate_broad_panel_upgrade_plan_2026-05-12.md"


def latest_vintage(pattern: str) -> str | None:
    matches = sorted((ROOT / "data/vintages").glob(pattern), key=lambda p: p.stat().st_mtime)
    if not matches:
        return None
    return str(matches[-1].relative_to(ROOT))


LOCAL_DATA = {
    "vdem_full": latest_vintage("vdem/vdem_cy_full@*.parquet"),
    "vdem_codebook": latest_vintage("vdem/codebook@*.parquet"),
    "oecd_pmr": latest_vintage("oecd_pmr/PMR@*.parquet"),
    "wdi_investment_share": latest_vintage("world_bank_wdi/NE.GDI.TOTL.ZS@*.parquet"),
    "wgi_regulatory_quality": latest_vintage("wgi/GOV_WGI_RQ.EST@*.parquet"),
    "wgi_control_corruption": latest_vintage("wgi/GOV_WGI_CC.EST@*.parquet"),
}


UPGRADE_SPECS = {
    "economic_freedom_corruption_decline": {
        "priority": 1,
        "decision": "upgrade_before_scoreboard",
        "problem": "Shares a WGI control-of-corruption outcome and WGI regulatory-quality treatment with other broad institution screens, so the current verdict is not independent evidence.",
        "upgrade": "Rebuild as a corruption-specific test using a non-WGI treatment or non-WGI corruption outcome.",
        "candidate_data": [
            "V-Dem political corruption / clientelism measures",
            "World Bank Enterprise Surveys bribe incidence",
            "Transparency International CPI as alternate outcome",
            "public procurement openness or e-procurement adoption where available",
        ],
        "local_data": [
            "V-Dem full panel is available; useful variables include v2x_corr, v2x_pubcorr, v2x_execorr, v2xnp_client, v2exbribe, and v2jucorrdc.",
            "WGI control-of-corruption is available only as a fallback or comparison outcome, not the upgraded primary outcome.",
        ],
        "scoreboard_rule": "Eligible only after the outcome and treatment no longer come from the same broad WGI proxy family.",
    },
    "market_governance_qol_broad_scope": {
        "priority": 3,
        "decision": "split_or_demote_to_meta_screen",
        "problem": "The claim is intentionally broad and currently duplicates the same WGI corruption/regulatory-quality panel as the corruption hypothesis.",
        "upgrade": "Split into narrower outcome-specific hypotheses or keep as a meta-audit that summarizes independent tests rather than scoring directly.",
        "candidate_data": [
            "one governance-specific child test",
            "one income or life-expectancy child test",
            "one business dynamism or investment child test",
        ],
        "local_data": [
            "Use existing verdict inventory and local WDI/WGI/V-Dem/PMR panels to build child tests; do not reuse this broad parent as direct evidence.",
        ],
        "scoreboard_rule": "Do not convert the broad parent directly; score only child tests with distinct datasets.",
    },
    "regulatory_transparency_investment": {
        "priority": 1,
        "decision": "upgrade_before_scoreboard",
        "problem": "Outcome is investment-specific, but the treatment is still broad WGI regulatory quality and collides with nearby regulatory-governance screens.",
        "upgrade": "Replace or supplement WGI RQ with a transparent-regulation proxy and keep investment share as the outcome.",
        "candidate_data": [
            "OECD PMR administrative burden / barriers to entrepreneurship",
            "World Bank Doing Business or B-READY regulatory process measures",
            "Regulatory Indicators for Sustainable Energy / sector rule clarity where relevant",
            "investment share from WDI or PWT",
        ],
        "local_data": [
            "OECD PMR is available with ADREG_BURDEN, IMPACT_ASSESSMENT, STAKEHOLDER_ENGAG, BARRIER_ENTRY, PUBLIC_PROCUREMENT, and related measures.",
            "WDI gross capital formation share is available as the investment outcome.",
        ],
        "scoreboard_rule": "Eligible once the treatment is a direct regulatory-transparency measure and robustness holds with country and year effects.",
    },
    "qol_anomaly_weight_broad_scope_test": {
        "priority": 4,
        "decision": "demote_to_meta_audit",
        "problem": "This is a framework-level anomaly-weight claim, but the current run is just a GDP-per-capita/WGI RQ panel that duplicates other verdicts.",
        "upgrade": "Convert into a meta-evidence audit over independent scored hypotheses, with anomaly weights computed from the verdict inventory.",
        "candidate_data": [
            "scoreboard verdict inventory",
            "evidence quality weights",
            "country/period coverage metadata",
        ],
        "local_data": [
            "Use the conversion audit, scoreboard audit, and result-card metadata already generated in engine/audits and engine/runs.",
        ],
        "scoreboard_rule": "Do not score as a direct policy verdict; use it to explain confidence and anomaly handling in the policy browser.",
    },
    "occupational_licensing_income_mobility": {
        "priority": 2,
        "decision": "data_gap_then_upgrade",
        "problem": "The present test measures GDP per capita against WGI RQ, not occupational licensing or mobility.",
        "upgrade": "Rebuild with a direct licensing-burden treatment and a mobility/wage outcome.",
        "candidate_data": [
            "US state occupational licensing coverage or license burden panels",
            "OECD PMR professional-services restrictions",
            "IPUMS/CPS wage mobility or employment transitions",
            "Opportunity Atlas / Chetty mobility measures for US geography",
        ],
        "local_data": [
            "OECD PMR professional-services restrictions are available as a partial licensing proxy.",
            "A direct mobility/wage-transition outcome is not yet confirmed locally.",
        ],
        "scoreboard_rule": "Eligible only after direct licensing treatment and mobility/labour outcome are present.",
    },
}


def verdict_label(record: dict) -> str:
    verdict = record.get("verdict") or {}
    if isinstance(verdict, dict):
        return verdict.get("label") or verdict.get("verdict") or "unknown"
    return str(verdict)


def main() -> None:
    audit = json.loads(CONVERSION_AUDIT.read_text())
    held = [
        record
        for record in audit["records"]
        if record.get("conversion_bucket") == "hold_duplicate_broad_panel_qa"
    ]

    groups: dict[str, list[dict]] = defaultdict(list)
    for record in held:
        groups[record.get("fingerprint") or "missing_fingerprint"].append(record)

    planned = []
    for record in sorted(held, key=lambda r: r["hypothesis_id"]):
        hid = record["hypothesis_id"]
        spec = UPGRADE_SPECS.get(
            hid,
            {
                "priority": 5,
                "decision": "review_duplicate_context",
                "problem": "Held because this verdict shares a broad-panel fingerprint with other hypotheses.",
                "upgrade": "Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.",
                "candidate_data": [],
                "scoreboard_rule": "Keep out of scoreboard until the duplicate evidence path is resolved.",
            },
        )
        planned.append(
            {
                "hypothesis_id": hid,
                "hypothesis_path": record["hypothesis_path"],
                "verdict": verdict_label(record),
                "fingerprint": record.get("fingerprint"),
                "duplicate_group_size": len(groups[record.get("fingerprint") or "missing_fingerprint"]),
                "qa_flags": record.get("qa_flags", []),
                **spec,
            }
        )

    priority_queue = sorted(planned, key=lambda item: (item["priority"], item["hypothesis_id"]))
    payload = {
        "generated_at": "2026-05-12",
        "source_audit": str(CONVERSION_AUDIT.relative_to(ROOT)),
        "local_data_inventory": {key: value for key, value in LOCAL_DATA.items() if value},
        "summary": {
            "held_duplicate_broad_panel_items": len(held),
            "duplicate_fingerprint_groups": len(groups),
            "priority_1_near_term_upgrades": [
                item["hypothesis_id"] for item in priority_queue if item["priority"] == 1
            ],
            "priority_2_data_gap_upgrades": [
                item["hypothesis_id"] for item in priority_queue if item["priority"] == 2
            ],
            "not_direct_scoreboard_items": [
                item["hypothesis_id"]
                for item in priority_queue
                if item["decision"] in {"demote_to_meta_audit", "split_or_demote_to_meta_screen"}
            ],
        },
        "duplicate_groups": [
            {
                "fingerprint": fingerprint,
                "size": len(records),
                "hypotheses": [record["hypothesis_id"] for record in records],
            }
            for fingerprint, records in sorted(groups.items(), key=lambda pair: (-len(pair[1]), pair[0]))
        ],
        "upgrade_queue": priority_queue,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Duplicate Broad-Panel Upgrade Plan (2026-05-12)",
        "",
        "Purpose: convert the next wave of throughput verdicts without letting duplicated broad-panel screens overstate the scoreboard.",
        "",
        "## Summary",
        "",
        f"- Held duplicate broad-panel items: {len(held)}",
        f"- Duplicate fingerprint groups: {len(groups)}",
        f"- Near-term upgrades: {', '.join(payload['summary']['priority_1_near_term_upgrades']) or 'none'}",
        f"- Data-gap upgrades: {', '.join(payload['summary']['priority_2_data_gap_upgrades']) or 'none'}",
        f"- Do-not-score-directly items: {', '.join(payload['summary']['not_direct_scoreboard_items']) or 'none'}",
        "",
        "## Duplicate Groups",
        "",
    ]
    for group in payload["duplicate_groups"]:
        lines.append(f"- `{group['fingerprint']}` ({group['size']}): {', '.join(f'`{hid}`' for hid in group['hypotheses'])}")

    lines.extend(["", "## Upgrade Queue", ""])
    for item in priority_queue:
        lines.extend(
            [
                f"### {item['priority']}. `{item['hypothesis_id']}`",
                "",
                f"- Verdict: {item['verdict']}",
                f"- Decision: {item['decision']}",
                f"- Problem: {item['problem']}",
                f"- Upgrade: {item['upgrade']}",
                f"- Scoreboard rule: {item['scoreboard_rule']}",
            ]
        )
        if item["candidate_data"]:
            lines.append(f"- Candidate data: {', '.join(item['candidate_data'])}")
        if item.get("local_data"):
            lines.append(f"- Local availability: {'; '.join(item['local_data'])}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines).rstrip() + "\n")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
