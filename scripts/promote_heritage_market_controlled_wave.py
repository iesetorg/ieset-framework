#!/usr/bin/env python3
"""Generate income/region-controlled Heritage market-order robustness specs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from promote_heritage_market_cross_section_wave import (
    COMPONENTS,
    OUTCOMES,
    ROOT,
    SCHEMA_HEADER,
    STEELMAN,
    latest_heritage_panel,
)


HYPOTHESES = ROOT / "hypotheses"
AUDITS = ROOT / "engine" / "audits"
INCOME_CONTROL = "world_bank_wdi:NY.GDP.PCAP.PP.KD"


def controlled_outcomes() -> list[dict]:
    # GDP per capita itself is the income control, so testing it here would be
    # mechanically over-controlled. Private consumption stays in: it asks
    # whether market scores predict consumption above same-income comparisons.
    return [outcome for outcome in OUTCOMES if outcome["slug"] != "gdp_pc_ppp"]


def spec_for(component: dict, outcome: dict, countries: list[str], market_year: int) -> dict:
    hid = f"heritage_{component['slug']}_{outcome['slug']}_income_region_robustness"
    comparison = "higher" if outcome["expected_sign"] == "+" else "lower"
    period = [market_year, market_year]
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": outcome["topic"],
        "claim": (
            f"Conditional on latest real GDP per capita and broad Heritage region, countries with higher "
            f"Heritage {component['label']} in {market_year} have {comparison} latest-available "
            f"{outcome['label']}. This tests whether the free-market/market-order association survives "
            "a first income-and-region robustness screen."
        ),
        "methodology_note": (
            "Second-stage Heritage market-order robustness wave. The original wave used top-vs-bottom "
            "quartile contrasts; this wave estimates a controlled cross-sectional OLS coefficient for the "
            "same Heritage pillar after log GDP per capita and Heritage region fixed effects."
        ),
        "evidence_type": "descriptive",
        "sample": {
            "countries": countries,
            "period": period,
            "temporal_structure": "cross_section_with_justification",
            "cross_section_justification": (
                "Heritage IEF cleaned local vintages currently cover 2024-2026. The 2024 score is used "
                "to avoid post-outcome look-ahead. WDI outcome and income-control observations use latest "
                "available country observations from 2018-2024."
            ),
            "exclusion_rules": [
                "drop countries missing the Heritage component score",
                "drop countries without a WDI outcome observation from 2018 through 2024",
                "drop countries without a WDI GDP-per-capita control observation from 2018 through 2024",
                "drop countries without a Heritage region label",
            ],
        },
        "scope": {
            "period": list(period),
            "countries": ["GLOBAL"],
            "outcome_dim": outcome["dims"],
            "policy_family": component["families"],
            "treatment_tags": [*component["tags"], "income_region_robustness"],
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
            "controls": [
                {
                    "name": "log_gdp_pc_ppp",
                    "source": INCOME_CONTROL,
                    "transformation": "latest_available_since_2018_log",
                },
                {
                    "name": "heritage_region_fixed_effects",
                    "source": "heritage_ief:ief_panel",
                    "transformation": f"{market_year}_region_dummies",
                },
            ],
        },
        "estimator": {
            "template": "descriptive",
            "notes": (
                "Controlled cross-sectional OLS: outcome on standardized Heritage pillar score, log GDP "
                "per capita, and Heritage region fixed effects. This is still descriptive, but stricter "
                "than the first-wave top-vs-bottom gap."
            ),
        },
        "falsification": {
            "rule": (
                "SUPPORTED if the controlled standardized market-score coefficient has the pre-registered "
                "direction at p<=0.10. REFUTED if the opposite direction is significant at p<=0.10. "
                "Otherwise PARTIAL; insufficient controlled coverage is INCONCLUSIVE_DATA_PENDING."
            ),
            "test": f"heritage_market_controlled_{hid}",
            "threshold": {
                "p_value": 0.10,
                "expected_sign": outcome["expected_sign"],
                "treatment_component": component["column"],
                "tail_quantile": 0.25,
                "min_outcome_year": 2018,
                "market_score_year": market_year,
                "robustness_design": "ols_income_region",
                "income_control_source": INCOME_CONTROL,
                "region_fixed_effects": True,
            },
        },
        "prior_confidence": 0.48,
        "disclosure": (
            "This is a harder follow-up to a pro-market screen and is expected to downgrade many first-wave "
            "supports if income or region explain the association. It should be read as robustness triage, "
            "not causal proof."
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
        f"The strongest pro-market interpretation is that Heritage {component['label']} captures an "
        "institutional or policy-regime feature that matters even among countries with similar income levels "
        f"and within similar broad regions, so it should still predict {outcome['label']} after those controls.\n\n"
        "The strongest objection is over-control and omitted-variable instability: GDP per capita is itself "
        "partly downstream of institutions, while region fixed effects are coarse and can absorb meaningful "
        "historical/institutional variation. A causal version needs panel timing, reform episodes, instruments, "
        "or synthetic comparisons.\n"
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
    outcomes = controlled_outcomes()

    ids: list[str] = []
    created = 0
    refreshed = 0
    for component in COMPONENTS:
        for outcome in outcomes:
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
    ids_path = AUDITS / f"heritage_market_controlled_wave_{stamp}.ids"
    json_path = AUDITS / f"heritage_market_controlled_wave_{stamp}.json"
    ids_path.write_text("\n".join(ids) + "\n")
    json_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "heritage_panel": str(heritage_path.relative_to(ROOT)),
                "market_score_year": market_year,
                "sample_countries": len(sample),
                "components": len(COMPONENTS),
                "outcomes": len(outcomes),
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
        f"generated {len(ids)} controlled Heritage robustness specs "
        f"({created} created, {refreshed} refreshed); ids: {ids_path.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
