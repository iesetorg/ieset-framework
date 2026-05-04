#!/usr/bin/env python3
"""Generate a broad Heritage IEF market-order cross-section wave.

This is intentionally a hypothesis -> data -> test scaffold, not a causal
claim factory. The specs compare high- and low-scoring countries on Heritage
economic-freedom pillars against latest-available WDI outcomes. They are useful
for Austrian/ordoliberal triage because the treatment side is an explicit
market-order score, but every generated result card discloses the cross-section
limitation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESES = ROOT / "hypotheses"
STEELMAN = HYPOTHESES / "steelman"
AUDITS = ROOT / "engine" / "audits"
SCHEMA_HEADER = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"


COMPONENTS = [
    {
        "column": "overall_score",
        "slug": "economic_freedom",
        "label": "overall economic freedom",
        "families": ["institutional_reform", "regulation", "trade_policy"],
        "tags": ["heritage_ief", "economic_freedom", "market_order"],
        "channel": "bundled",
        "school_note": "Austrian/classical-liberal market-order claim and ordoliberal competitive-order claim",
    },
    {
        "column": "property_rights",
        "slug": "property_rights",
        "label": "property-rights protection",
        "families": ["institutional_reform"],
        "tags": ["heritage_ief", "property_rights", "market_order"],
        "channel": "institutional",
        "school_note": "Austrian calculation/property-rights claim and ordoliberal economic-constitution claim",
    },
    {
        "column": "judicial_effectiveness",
        "slug": "judicial_effectiveness",
        "label": "judicial effectiveness",
        "families": ["institutional_reform"],
        "tags": ["heritage_ief", "judicial_effectiveness", "rule_of_law"],
        "channel": "institutional",
        "school_note": "ordoliberal rule-bound legal-order claim",
    },
    {
        "column": "government_integrity",
        "slug": "government_integrity",
        "label": "government integrity",
        "families": ["institutional_reform"],
        "tags": ["heritage_ief", "government_integrity", "rent_seeking"],
        "channel": "institutional",
        "school_note": "Austrian rent-seeking/discretion claim and ordoliberal rule-bound-state claim",
    },
    {
        "column": "tax_burden",
        "slug": "tax_burden",
        "label": "lower-tax-burden score",
        "families": ["tax_policy", "fiscal_policy"],
        "tags": ["heritage_ief", "tax_burden", "fiscal_freedom"],
        "channel": "fiscal",
        "school_note": "Austrian/classical-liberal fiscal-burden claim",
    },
    {
        "column": "government_spending",
        "slug": "government_spending",
        "label": "lower-government-spending score",
        "families": ["fiscal_policy"],
        "tags": ["heritage_ief", "government_spending", "state_size"],
        "channel": "fiscal",
        "school_note": "Austrian fiscal-crowding/malallocation claim",
    },
    {
        "column": "business_freedom",
        "slug": "business_freedom",
        "label": "business freedom",
        "families": ["regulation", "competition_policy"],
        "tags": ["heritage_ief", "business_freedom", "entry_exit"],
        "channel": "regulatory",
        "school_note": "Austrian entrepreneurship/discovery claim and ordoliberal competition-order claim",
    },
    {
        "column": "labor_freedom",
        "slug": "labor_freedom",
        "label": "labour-market freedom",
        "families": ["labour_market", "regulation"],
        "tags": ["heritage_ief", "labor_freedom", "labour_market"],
        "channel": "regulatory",
        "school_note": "market-liberal labour flexibility claim",
    },
    {
        "column": "monetary_freedom",
        "slug": "monetary_freedom",
        "label": "monetary freedom",
        "families": ["monetary_policy", "institutional_reform"],
        "tags": ["heritage_ief", "monetary_freedom", "price_stability"],
        "channel": "monetary",
        "school_note": "Austrian hard-money/inflation-discipline claim and ordoliberal monetary-constitution claim",
    },
    {
        "column": "trade_freedom",
        "slug": "trade_freedom",
        "label": "trade freedom",
        "families": ["trade_policy", "competition_policy"],
        "tags": ["heritage_ief", "trade_freedom", "market_integration"],
        "channel": "regulatory",
        "school_note": "market-integration claim shared by classical liberal and ordoliberal traditions",
    },
    {
        "column": "investment_freedom",
        "slug": "investment_freedom",
        "label": "investment freedom",
        "families": ["regulation", "institutional_reform"],
        "tags": ["heritage_ief", "investment_freedom", "capital_mobility"],
        "channel": "regulatory",
        "school_note": "Austrian capital-allocation claim",
    },
    {
        "column": "financial_freedom",
        "slug": "financial_freedom",
        "label": "financial freedom",
        "families": ["regulation", "institutional_reform"],
        "tags": ["heritage_ief", "financial_freedom", "capital_allocation"],
        "channel": "regulatory",
        "school_note": "market-liberal capital-allocation claim with ordoliberal prudential caveat",
    },
]


OUTCOMES = [
    {
        "slug": "gdp_pc_ppp",
        "label": "real GDP per capita PPP",
        "source": "world_bank_wdi:NY.GDP.PCAP.PP.KD",
        "expected_sign": "+",
        "topic": "growth",
        "dims": ["gdp_growth"],
    },
    {
        "slug": "private_consumption_pc",
        "label": "real private consumption per capita",
        "source": "world_bank_wdi:NE.CON.PRVT.PC.KD",
        "expected_sign": "+",
        "topic": "growth",
        "dims": ["gdp_growth", "welfare_state"],
    },
    {
        "slug": "life_expectancy",
        "label": "life expectancy",
        "source": "world_bank_wdi:SP.DYN.LE00.IN",
        "expected_sign": "+",
        "topic": "healthcare",
        "dims": ["life_expectancy_health"],
    },
    {
        "slug": "under5_mortality",
        "label": "under-5 mortality",
        "source": "world_bank_wdi:SH.DYN.MORT",
        "expected_sign": "-",
        "topic": "healthcare",
        "dims": ["life_expectancy_health"],
    },
    {
        "slug": "extreme_poverty",
        "label": "extreme-poverty headcount",
        "source": "world_bank_wdi:SI.POV.DDAY",
        "expected_sign": "-",
        "topic": "distribution",
        "dims": ["poverty_inequality"],
    },
    {
        "slug": "electricity_access",
        "label": "electricity access",
        "source": "world_bank_wdi:EG.ELC.ACCS.ZS",
        "expected_sign": "+",
        "topic": "energy",
        "dims": ["energy", "welfare_state"],
    },
    {
        "slug": "physician_density",
        "label": "physician density",
        "source": "world_bank_wdi:SH.MED.PHYS.ZS",
        "expected_sign": "+",
        "topic": "healthcare",
        "dims": ["life_expectancy_health"],
    },
    {
        "slug": "tertiary_enrollment",
        "label": "tertiary enrollment",
        "source": "world_bank_wdi:SE.TER.ENRR",
        "expected_sign": "+",
        "topic": "growth",
        "dims": ["productivity"],
    },
    {
        "slug": "private_credit_depth",
        "label": "private-credit depth",
        "source": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "expected_sign": "+",
        "topic": "regulatory",
        "dims": ["financialisation", "capital_flows"],
    },
    {
        "slug": "trade_openness",
        "label": "trade openness",
        "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
        "expected_sign": "+",
        "topic": "trade",
        "dims": ["trade_liberalisation"],
    },
    {
        "slug": "investment_share",
        "label": "gross-capital-formation share",
        "source": "world_bank_wdi:NE.GDI.TOTL.ZS",
        "expected_sign": "+",
        "topic": "growth",
        "dims": ["gdp_growth", "productivity"],
    },
    {
        "slug": "inflation_rate",
        "label": "consumer-price inflation",
        "source": "world_bank_wdi:FP.CPI.TOTL.ZG",
        "expected_sign": "-",
        "topic": "monetary",
        "dims": ["inflation", "monetary_policy"],
    },
    {
        "slug": "female_lfp",
        "label": "female labour-force participation",
        "source": "world_bank_wdi:SL.TLF.CACT.FE.ZS",
        "expected_sign": "+",
        "topic": "labour",
        "dims": ["employment_labour"],
    },
    {
        "slug": "employment_rate",
        "label": "employment rate",
        "source": "world_bank_wdi:SL.EMP.TOTL.SP.ZS",
        "expected_sign": "+",
        "topic": "labour",
        "dims": ["employment_labour"],
    },
    {
        "slug": "account_ownership",
        "label": "account ownership",
        "source": "world_bank_wdi:FX.OWN.TOTL.ZS",
        "expected_sign": "+",
        "topic": "regulatory",
        "dims": ["financialisation", "welfare_state"],
    },
    {
        "slug": "high_tech_exports",
        "label": "high-technology export share",
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "expected_sign": "+",
        "topic": "trade",
        "dims": ["industrial_capability", "productivity"],
    },
]


def latest_heritage_panel() -> tuple[pd.DataFrame, Path]:
    pub_dir = ROOT / "data" / "vintages" / "heritage_ief"
    candidates = sorted(pub_dir.glob("ief_panel@*.parquet"))
    if not candidates:
        raise SystemExit("No Heritage panel vintage found. Run: venv/bin/python scripts/fetch.py heritage_ief ief_panel")
    path = candidates[-1]
    return pd.read_parquet(path), path


def spec_for(component: dict, outcome: dict, countries: list[str], market_year: int) -> dict:
    hid = f"heritage_{component['slug']}_{outcome['slug']}_current_gap"
    comparison = "higher" if outcome["expected_sign"] == "+" else "lower"
    period = [market_year, market_year]
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": outcome["topic"],
        "claim": (
            f"Countries in the top quartile of Heritage {component['label']} in {market_year} "
            f"have {comparison} latest-available {outcome['label']} than bottom-quartile countries, "
            "consistent with free-market country policy regimes outperforming less market-oriented regimes "
            f"on this outcome."
        ),
        "methodology_note": (
            "Generated by the Heritage market-order cross-section wave. This uses a broad country sample, "
            "pre-registers a top-vs-bottom quartile contrast, and routes the result through "
            "scripts/run_heritage_market_cross_section.py."
        ),
        "evidence_type": "descriptive",
        "sample": {
            "countries": countries,
            "period": period,
            "temporal_structure": "cross_section_with_justification",
            "cross_section_justification": (
                "Heritage IEF cleaned local vintages currently cover 2024-2026. The 2024 score is used "
                "to avoid post-outcome look-ahead while WDI outcomes use latest observations from 2018-2024."
            ),
            "exclusion_rules": [
                "drop countries missing the Heritage component score",
                "drop countries without a WDI outcome observation from 2018 through 2024",
            ],
        },
        "scope": {
            "period": list(period),
            "countries": ["GLOBAL"],
            "outcome_dim": outcome["dims"],
            "policy_family": component["families"],
            "treatment_tags": component["tags"],
        },
        "intervention_channel": component["channel"],
        "intervention_channel_justification": (
            f"Heritage {component['label']} is used as a country-level policy-regime/institutional score, "
            "not as a dated discrete policy shock."
        ),
        "variables": {
            "outcome": [
                {
                    "name": outcome["slug"],
                    "source": outcome["source"],
                    "transformation": "latest_available_country_level_since_2018",
                }
            ],
            "treatment": [
                {
                    "name": component["slug"],
                    "source": "heritage_ief:ief_panel",
                    "transformation": f"{market_year}_component_score:{component['column']}",
                }
            ],
        },
        "estimator": {
            "template": "descriptive",
            "notes": (
                "Welch top-vs-bottom quartile mean contrast. This is a screen for broad market-order "
                "associations, not a causal policy effect estimate."
            ),
        },
        "falsification": {
            "rule": (
                "SUPPORTED if the high-market quartile has the pre-registered outcome direction versus "
                "the low-market quartile at Welch p<=0.10. REFUTED if the opposite direction is significant "
                "at p<=0.10. Otherwise PARTIAL; insufficient group coverage is INCONCLUSIVE_DATA_PENDING."
            ),
            "test": f"heritage_market_cross_section_{hid}",
            "threshold": {
                "p_value": 0.10,
                "expected_sign": outcome["expected_sign"],
                "treatment_component": component["column"],
                "tail_quantile": 0.25,
                "min_outcome_year": 2018,
                "market_score_year": market_year,
            },
        },
        "prior_confidence": 0.58,
        "disclosure": (
            f"Designed to pressure-test a {component['school_note']} with broad public data. "
            "The test is intentionally disclosed as cross-sectional and multiple-comparison-prone."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
    }


def write_steelman(hid: str, component: dict, outcome: dict) -> None:
    STEELMAN.mkdir(parents=True, exist_ok=True)
    path = STEELMAN / f"{hid}.md"
    if path.exists():
        return
    path.write_text(
        f"# Steelman - {hid}\n\n"
        f"The strongest pro-market interpretation is that Heritage {component['label']} captures a real "
        "policy-regime difference: prices, entry, contracts, and capital allocation face fewer distortions "
        f"in the high-score countries, so higher market scores should be associated with better "
        f"{outcome['label']}.\n\n"
        "The strongest objection is that this is a cross-section. Richer countries may be able to afford "
        "better institutions, outcomes may feed back into policy scores, and geography, demography, resource "
        "endowments, or state capacity may confound the comparison. Treat this as a triage result until a "
        "panel, event, synthetic-control, or instrumented version is registered.\n"
    )


def main() -> int:
    heritage, heritage_path = latest_heritage_panel()
    available_years = sorted(int(y) for y in pd.to_numeric(heritage["year"], errors="coerce").dropna().unique())
    market_year = 2024 if 2024 in available_years else max(available_years)
    sample = (
        heritage.loc[pd.to_numeric(heritage["year"], errors="coerce") == market_year, "country_iso3"]
        .dropna()
        .astype(str)
        .str.upper()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    sample = [code for code in sample if len(code) == 3 and code.isalpha()]
    if not sample:
        raise SystemExit(f"No ISO3 countries found in Heritage panel {heritage_path}")

    ids: list[str] = []
    created = 0
    refreshed = 0
    for component in COMPONENTS:
        if component["column"] not in heritage.columns:
            raise SystemExit(f"Missing Heritage component column: {component['column']}")
        for outcome in OUTCOMES:
            spec = spec_for(component, outcome, sample, market_year)
            hid = spec["hypothesis_id"]
            topic_dir = HYPOTHESES / spec["topic"]
            topic_dir.mkdir(parents=True, exist_ok=True)
            spec_path = topic_dir / f"{hid}.yaml"
            text = SCHEMA_HEADER + yaml.safe_dump(spec, sort_keys=False, width=100)
            if spec_path.exists():
                refreshed += 1
            else:
                created += 1
            spec_path.write_text(text)
            write_steelman(hid, component, outcome)
            ids.append(hid)

    AUDITS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).date().isoformat()
    ids_path = AUDITS / f"heritage_market_cross_section_wave_{stamp}.ids"
    json_path = AUDITS / f"heritage_market_cross_section_wave_{stamp}.json"
    ids_path.write_text("\n".join(ids) + "\n")
    json_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "heritage_panel": str(heritage_path.relative_to(ROOT)),
                "market_score_year": market_year,
                "sample_countries": len(sample),
                "components": len(COMPONENTS),
                "outcomes": len(OUTCOMES),
                "hypotheses": len(ids),
                "created": created,
                "refreshed": refreshed,
                "ids_file": str(ids_path.relative_to(ROOT)),
                "ids": ids,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"generated {len(ids)} Heritage market-order specs "
        f"({created} created, {refreshed} refreshed); ids: {ids_path.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
