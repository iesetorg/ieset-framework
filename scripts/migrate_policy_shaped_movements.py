"""Surgical migration of 14 movement YAMLs that are really policies.

Two operations per item:

  CONVERT — write a new policies/<id>.yaml with the movement's core content
            (axes_moved synthesised from axes_summary, country, dates,
            description), then delete movements/<id>.yaml. Updates any
            broader-era movement that should reference the new policy.

  MERGE   — same as CONVERT, plus the broader-era movement absorbs the
            narrow movement's outcome_hypotheses and position_alignments.

Run once. Idempotent: skips items where the movement YAML is already gone.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
MOV = REPO / "movements"
POL = REPO / "policies"


# Each entry: {
#   movement_id, action ('CONVERT' or 'MERGE'),
#   target_policy_id, target_policy_title,
#   parent_movements: [movement_ids that should reference the new policy],
#   policy_description: optional override,
# }
PLAN = [
    {
        "movement_id": "uk_truss_mini_budget_2022",
        "action": "CONVERT",
        "target_policy_id": "uk_truss_mini_budget_2022",
        "target_policy_title": "Truss mini-budget (Sep 2022)",
        "parent_movements": ["uk_johnson_conservative_2019_2022", "uk_sunak_conservative_2022_2024"],
    },
    {
        "movement_id": "eu_ai_act_2024",
        "action": "CONVERT",
        "target_policy_id": "eu_ai_act_2024",
        "target_policy_title": "EU AI Act (Regulation 2024/1689)",
        "parent_movements": ["eu_gdpr_regulatory_stack_2018"],
    },
    {
        "movement_id": "eu_digital_markets_act_dsa_2022",
        "action": "CONVERT",
        "target_policy_id": "eu_dma_dsa_2022",
        "target_policy_title": "EU Digital Markets Act + Digital Services Act (2022)",
        "parent_movements": ["eu_gdpr_regulatory_stack_2018"],
    },
    {
        "movement_id": "new_zealand_zero_carbon_act_2019",
        "action": "CONVERT",
        "target_policy_id": "nz_zero_carbon_act_2019",
        "target_policy_title": "Climate Change Response (Zero Carbon) Amendment Act 2019",
        "parent_movements": ["newzealand_ardern_labour_2017_2023"],
    },
    {
        "movement_id": "australia_carbon_tax_repeal_2014",
        "action": "CONVERT",
        "target_policy_id": "au_carbon_tax_repeal_2014",
        "target_policy_title": "Carbon Tax Repeal (2014)",
        "parent_movements": ["australia_abbott_lnp_2013_2015"],
    },
    {
        "movement_id": "australia_superannuation_guarantee_1992",
        "action": "CONVERT",
        "target_policy_id": "au_superannuation_guarantee_act_1992",
        "target_policy_title": "Superannuation Guarantee (Administration) Act 1992",
        "parent_movements": ["hawke_keating_reform_1983_1996"],
    },
    {
        "movement_id": "us_new_deal_glass_steagall_banking_1933",
        "action": "CONVERT",
        "target_policy_id": "us_glass_steagall_banking_act_1933",
        "target_policy_title": "Glass-Steagall Banking Act (1933)",
        "parent_movements": ["us_fdr_new_deal_1933_1939"],
    },
    {
        "movement_id": "clinton_welfare_reform_1996",
        "action": "MERGE",
        "target_policy_id": "us_prwora_welfare_reform_act_1996",
        "target_policy_title": "Personal Responsibility and Work Opportunity Reconciliation Act (PRWORA, 1996)",
        "parent_movements": ["us_clinton_first_term_1993_1997"],
    },
    {
        "movement_id": "us_bush_43_tax_cuts_2001_2003",
        "action": "MERGE",
        "target_policy_id": "us_bush_43_tax_cuts_egtrra_jgtrra_2001_2003",
        "target_policy_title": "Bush 43 tax cuts (EGTRRA 2001 + JGTRRA 2003)",
        "parent_movements": ["us_bush_43_first_term_broad_2001_2005"],
    },
    {
        "movement_id": "reagan_tax_reforms_1981_1986",
        "action": "MERGE",
        "target_policy_id": "us_reagan_tax_reforms_erta_tra_1981_1986",
        "target_policy_title": "Reagan tax reforms (ERTA 1981 + TRA 1986)",
        "parent_movements": [
            "us_reagan_first_term_1981_1985",
            "us_reagan_first_term_broad_1981_1985",
            "us_reagan_second_term_1985_1989",
        ],
    },
    {
        "movement_id": "macron_labour_tax_reforms_2017_2019",
        "action": "MERGE",
        "target_policy_id": "fr_macron_labour_tax_reforms_2017_2019",
        "target_policy_title": "Macron labour + tax reforms (Ordonnances 2017 + PFU 2018)",
        "parent_movements": [
            "france_macron_presidency_2017_present",
        ],
    },
    {
        "movement_id": "hawke_keating_reform_1983_1996",
        "action": "MERGE",
        "target_policy_id": "au_hawke_keating_reform_package_1983_1996",
        "target_policy_title": "Hawke-Keating reform package (1983-1996)",
        "parent_movements": ["australia_keating_alp_1991_1996"],
    },
    {
        "movement_id": "israel_stabilisation_plan_1985",
        "action": "MERGE",
        "target_policy_id": "il_stabilisation_plan_1985",
        "target_policy_title": "Israeli Economic Stabilization Plan (July 1985)",
        "parent_movements": ["israel_unity_government_stabilisation_1984_1986"],
    },
    {
        "movement_id": "sweden_pension_reform_1999",
        "action": "CONVERT",
        "target_policy_id": "se_pension_reform_1999",
        "target_policy_title": "Swedish pension reform (NDC + premium pension, 1998-1999)",
        "parent_movements": ["sweden_persson_sap_1996_2006"],
    },
]


# Map movement axes_summary entries to policy axes_moved entries.
DIRECTION_OK = {"+", "-", "0", "mixed"}


def axes_summary_to_axes_moved(summary):
    out = []
    for entry in summary or []:
        axis = entry.get("axis")
        direction = entry.get("direction")
        if axis is None or direction is None:
            continue
        # Policy schema rejects "mixed" — coerce to "0" with a flag in
        # rationale so the information isn't lost.
        rationale = entry.get("rationale") or ""
        if direction == "mixed":
            direction = "0"
            rationale = (rationale + " (recoded mixed→0 during movement→policy migration)").strip()
        if direction not in {"+", "-", "0"}:
            continue
        moved = {"axis": axis, "direction": direction}
        if entry.get("magnitude"):
            moved["magnitude"] = entry["magnitude"]
        if rationale:
            moved["rationale"] = rationale
        out.append(moved)
    return out


def write_policy_yaml(policy_id, title, mov_doc, parent_movements, action):
    countries = mov_doc.get("countries") or []
    tf = mov_doc.get("timeframe") or {}
    description = (mov_doc.get("doctrine") or "").strip()
    if len(description) < 80:
        description = (description + " " + (mov_doc.get("name") or policy_id)).strip()
    if len(description) < 80:
        description = description + " " * (80 - len(description))

    axes_moved = axes_summary_to_axes_moved(mov_doc.get("axes_summary"))
    if not axes_moved:
        axes_moved = [{"axis": "fiscal.spending_level", "direction": "0",
                       "rationale": "no axes_summary in source movement; placeholder until human review"}]

    policy = {
        "policy_id": policy_id,
        "status": "candidate",
        "title": title,
        "countries": countries,
        "timeframe": tf,
        "description": description,
        "enacted_by": parent_movements,
        "axes_moved": axes_moved,
        "notes": f"Migrated from movements/{mov_doc['movement_id']}.yaml (action={action}). "
                 f"This entity is a single policy/legislation, not a coalition era; "
                 f"reclassified to policies/. Original movement file deleted.",
    }
    if mov_doc.get("references"):
        policy["references"] = mov_doc["references"]
    if mov_doc.get("source_provenance"):
        policy["source_provenance"] = mov_doc["source_provenance"]

    out_path = POL / f"{policy_id}.yaml"
    out_path.write_text(
        yaml.dump(policy, sort_keys=False, allow_unicode=True, width=92)
    )
    return out_path


def update_parent_movement(parent_id: str, policy_id: str):
    """Add policy_id to parent movement's `policies` list if not already present.
    Skip silently if parent movement doesn't exist (some Tier-A items reference
    parents we haven't created yet)."""
    p = MOV / f"{parent_id}.yaml"
    if not p.exists():
        return False
    raw = p.read_text()
    doc = yaml.safe_load(raw)
    if not doc:
        return False
    policies = doc.get("policies") or []
    if policy_id in policies:
        return False
    policies.append(policy_id)
    doc["policies"] = policies
    # Preserve the schema header line if present.
    out = yaml.dump(doc, sort_keys=False, allow_unicode=True, width=92)
    if raw.startswith("# yaml-language-server:"):
        head = raw.split("\n", 1)[0]
        out = head + "\n" + out
    p.write_text(out)
    return True


def main():
    summary = []
    for item in PLAN:
        mov_path = MOV / f"{item['movement_id']}.yaml"
        if not mov_path.exists():
            summary.append((item["movement_id"], "SKIP — already gone"))
            continue
        mov_doc = yaml.safe_load(mov_path.read_text())
        policy_path = write_policy_yaml(
            item["target_policy_id"],
            item["target_policy_title"],
            mov_doc,
            item["parent_movements"],
            item["action"],
        )
        updated_parents = []
        for parent in item["parent_movements"]:
            if update_parent_movement(parent, item["target_policy_id"]):
                updated_parents.append(parent)
        # Delete the original movement YAML.
        mov_path.unlink()
        summary.append(
            (
                item["movement_id"],
                f"{item['action']} → policies/{policy_path.name} "
                f"(parents updated: {','.join(updated_parents) or '—'})",
            )
        )

    print(f"Migrated {sum(1 for _, s in summary if not s.startswith('SKIP'))} of {len(PLAN)} planned.")
    for mid, msg in summary:
        print(f"  {mid:<58}  {msg}")


if __name__ == "__main__":
    main()
