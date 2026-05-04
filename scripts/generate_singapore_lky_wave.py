#!/usr/bin/env python3
"""Generate and run a Lee Kuan Yew / Singapore study wave.

This wave is intentionally conservative: it uses only local vintages already in
`data/vintages`, writes falsifiable hypothesis specs, steelmen, direct policy
links, and local replication artifacts. HDB/homeownership is registered as a
blocked data-gap study because the repo does not yet contain an HDB/homeownership
vintage.
"""
from __future__ import annotations

import json
import sys
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import yaml

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
STEEL = ROOT / "hypotheses" / "steelman"
POLICIES = ROOT / "policies"

sys.path.insert(0, str(ROOT / "scripts"))
from run_multi_metric_checklist import load_panel_series, latest_vintage  # noqa: E402

PEERS = ["HKG", "KOR", "MYS", "THA", "IDN", "PHL"]
PEERS_WITH_TWN = ["HKG", "KOR", "MYS", "THA", "IDN", "PHL", "TWN"]


@dataclass(frozen=True)
class Metric:
    metric_id: str
    description: str
    source: str
    threshold: str
    window: str
    evaluator: Callable[[], tuple[Optional[float], Optional[bool], str]]
    direction: str = "supports_claim"
    independence_justification: str = "Independent outcome/source layer within the Singapore LKY case bundle."


@dataclass(frozen=True)
class Study:
    hid: str
    topic: str
    claim: str
    sample_countries: list[str]
    period: tuple[int, int]
    outcome_dim: list[str]
    policy_family: list[str]
    treatment_tags: list[str]
    variables: list[dict]
    metrics: list[Metric]
    support_threshold: int
    refute_threshold: int
    prior: float
    disclosure: str
    steelman: str
    notes: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def split_source(src: str) -> tuple[str, str]:
    pub, _, series = src.partition(":")
    return pub, series


def panel(src: str) -> pd.DataFrame:
    pub, series = split_source(src)
    df = load_panel_series(pub, series)
    if df is None:
        return pd.DataFrame(columns=["country", "year", "value"])
    return df.dropna(subset=["country", "year", "value"]).copy()


def value_at(src: str, country: str, year: int, tolerance: int = 3) -> Optional[float]:
    df = panel(src)
    sub = df[df["country"] == country].copy()
    if sub.empty:
        return None
    sub["dist"] = (sub["year"].astype(int) - year).abs()
    sub = sub[sub["dist"] <= tolerance].sort_values(["dist", "year"])
    if sub.empty:
        return None
    return float(sub.iloc[0]["value"])


def mean_between(src: str, country: str, start: int, end: int) -> Optional[float]:
    df = panel(src)
    sub = df[(df["country"] == country) & (df["year"] >= start) & (df["year"] <= end)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def ratio(src: str, country: str, start: int, end: int) -> Optional[float]:
    a = value_at(src, country, start)
    b = value_at(src, country, end)
    if a is None or b is None or a == 0:
        return None
    return float(b / a)


def pp_change(src: str, country: str, start: int, end: int) -> Optional[float]:
    a = value_at(src, country, start)
    b = value_at(src, country, end)
    if a is None or b is None:
        return None
    return float(b - a)


def peer_median_at(src: str, peers: list[str], year: int) -> Optional[float]:
    vals = [value_at(src, c, year) for c in peers]
    vals = [v for v in vals if v is not None]
    if len(vals) < 3:
        return None
    return float(pd.Series(vals).median())


def endpoint_vs_peer_median(src: str, country: str, peers: list[str], year: int) -> Optional[float]:
    v = value_at(src, country, year)
    med = peer_median_at(src, peers, year)
    if v is None or med is None or med == 0:
        return None
    return float(v / med)


def gt(value: Optional[float], cutoff: float, label: str) -> tuple[Optional[float], Optional[bool], str]:
    if value is None:
        return None, None, f"missing data for {label}"
    return value, value >= cutoff, f"{label} = {value:.3f}; threshold >= {cutoff:g}"


def lt(value: Optional[float], cutoff: float, label: str) -> tuple[Optional[float], Optional[bool], str]:
    if value is None:
        return None, None, f"missing data for {label}"
    return value, value <= cutoff, f"{label} = {value:.3f}; threshold <= {cutoff:g}"


def m(metric_id: str, description: str, source: str, threshold: str, window: str,
      evaluator: Callable[[], tuple[Optional[float], Optional[bool], str]],
      independence: str) -> Metric:
    return Metric(metric_id, description, source, threshold, window, evaluator,
                  independence_justification=independence)


def studies() -> list[Study]:
    gdp_growth = "world_bank_wdi:NY.GDP.PCAP.KD.ZG"
    gdp_pc = "world_bank_wdi:NY.GDP.PCAP.KD"
    gcf = "world_bank_wdi:NE.GDI.TOTL.ZS"
    trade = "world_bank_wdi:NE.TRD.GNFS.ZS"
    exports = "world_bank_wdi:NE.EXP.GNFS.ZS"
    fdi = "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS"
    manuf_va = "world_bank_wdi:NV.IND.MANF.ZS"
    manuf_exports = "world_bank_wdi:TX.VAL.MANF.ZS.UN"
    cc = "wgi:CC.EST"
    ge = "wgi:GE.EST"
    rl = "wgi:RL.EST"
    hc = "pwt:hc"
    upper_sec = "world_bank_wdi:SE.SEC.CUAT.UP.ZS"
    tertiary = "world_bank_wdi:SE.TER.ENRR"
    savings = "world_bank_wdi:NY.GNS.ICTR.ZS"
    tax = "world_bank_wdi:GC.TAX.TOTL.GD.ZS"
    net_lending = "world_bank_wdi:GC.NLD.TOTL.GD.ZS"
    efw = "fraser_efw:summary_index"
    trade_freedom = "fraser_efw:freedom_to_trade_internationally"

    return [
        Study(
            hid="singapore_lky_growth_takeoff_1965_1990",
            topic="growth",
            claim=(
                "Singapore's Lee Kuan Yew era growth takeoff from 1965 to 1990 was not a "
                "small city-state accounting artifact: real GDP per capita grew rapidly, the "
                "level multiplied several-fold, investment rates stayed high, and the 1990 "
                "income level exceeded regional market-economy peers by a large margin."
            ),
            sample_countries=["SGP"] + PEERS,
            period=(1965, 1990),
            outcome_dim=["gdp_growth", "productivity"],
            policy_family=["institutional_reform", "trade_policy", "industrial_policy"],
            treatment_tags=["lee_kuan_yew_1965", "singapore_export_oriented_growth", "edb_1961"],
            variables=[
                {"name": "real_gdp_pc_growth", "source": gdp_growth, "transformation": "annual_mean"},
                {"name": "real_gdp_pc_level", "source": gdp_pc, "transformation": "endpoint_ratio"},
                {"name": "gross_capital_formation_pct_gdp", "source": gcf, "transformation": "annual_mean"},
            ],
            metrics=[
                m("real_gdp_pc_growth_avg", "Average annual real GDP per-capita growth, 1965-1990", gdp_growth, ">= 5.0%", "1965-1990", lambda: gt(mean_between(gdp_growth, "SGP", 1965, 1990), 5.0, "SGP average GDP-pc growth 1965-1990"), "Annual growth-rate series distinct from endpoint level comparisons."),
                m("real_gdp_pc_level_multiplier", "Real GDP per-capita endpoint multiplier, 1965-1990", gdp_pc, ">= 4.0x", "1965-1990", lambda: gt(ratio(gdp_pc, "SGP", 1965, 1990), 4.0, "SGP GDP-pc 1990/1965 ratio"), "Level-based cumulative growth check separate from annual growth rates."),
                m("income_level_vs_peer_median_1990", "Singapore 1990 real GDP per capita vs regional peer median", gdp_pc, ">= 3.0x peer median", "1990", lambda: gt(endpoint_vs_peer_median(gdp_pc, "SGP", PEERS, 1990), 3.0, "SGP 1990 GDP-pc / peer median"), "Cross-country benchmark against nearby market-economy peers."),
                m("investment_share_high", "Gross capital formation averaged high during takeoff", gcf, ">= 30% of GDP", "1965-1990", lambda: gt(mean_between(gcf, "SGP", 1965, 1990), 30.0, "SGP gross capital formation mean"), "Investment share is an expenditure-side channel distinct from GDP levels."),
                m("city_state_peer_check", "Singapore 1990 real GDP per capita at least matched Hong Kong", gdp_pc, ">= 1.0x Hong Kong", "1990", lambda: gt((value_at(gdp_pc, "SGP", 1990) or 0) / (value_at(gdp_pc, "HKG", 1990) or 1), 1.0, "SGP/HKG GDP-pc 1990"), "Hong Kong check reduces pure city-state geography objection."),
            ],
            support_threshold=4,
            refute_threshold=2,
            prior=0.82,
            disclosure="Prior expects the LKY-era growth pattern to clear descriptive thresholds; the design does not isolate which part of the policy bundle caused the growth.",
            steelman="The strongest objection is that Singapore was a uniquely located entrepot city with British legal inheritance, port geography, and Cold War security guarantees. A supported verdict here should not be read as proof that the exact LKY bundle generalises to large countries or democracies.",
            notes="Custom local-data checklist; descriptive, not causal identification.",
        ),
        Study(
            hid="singapore_lky_trade_openness_port_state_1965_1990",
            topic="trade",
            claim=(
                "The LKY-era Singapore model was extraordinarily trade-open rather than autarkic: "
                "trade and exports were far above GDP, trade openness beat regional peers, and "
                "manufactured exports became a dominant share by 1990."
            ),
            sample_countries=["SGP"] + PEERS,
            period=(1965, 1990),
            outcome_dim=["trade_liberalisation", "industrial_capability"],
            policy_family=["trade_policy", "industrial_policy", "institutional_reform"],
            treatment_tags=["singapore_port_state", "export_oriented_industrialisation", "container_port_1972"],
            variables=[
                {"name": "trade_openness", "source": trade, "transformation": "annual_mean"},
                {"name": "exports_pct_gdp", "source": exports, "transformation": "annual_mean"},
                {"name": "manufactured_exports_share", "source": manuf_exports, "transformation": "endpoint_change"},
            ],
            metrics=[
                m("trade_openness_mean", "Trade/GDP averaged extremely high", trade, ">= 250% of GDP", "1965-1990", lambda: gt(mean_between(trade, "SGP", 1965, 1990), 250.0, "SGP trade/GDP mean"), "Trade/GDP is the core openness measure."),
                m("exports_share_mean", "Exports/GDP averaged above the size of domestic GDP", exports, ">= 120% of GDP", "1965-1990", lambda: gt(mean_between(exports, "SGP", 1965, 1990), 120.0, "SGP exports/GDP mean"), "Exports/GDP separately checks outward orientation."),
                m("trade_vs_peer_median_1990", "Trade openness exceeded regional peer median in 1990", trade, ">= 2.0x peer median", "1990", lambda: gt(endpoint_vs_peer_median(trade, "SGP", PEERS, 1990), 2.0, "SGP 1990 trade/GDP / peer median"), "Peer-median comparison reduces level-only interpretation."),
                m("manufactured_exports_upgrade", "Manufactured exports share rose strongly from 1965 to 1990", manuf_exports, ">= 30pp increase", "1965-1990", lambda: gt(pp_change(manuf_exports, "SGP", 1965, 1990), 30.0, "SGP manufactured-export share change"), "Export composition check is independent from gross openness."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.88,
            disclosure="Prior is high because Singapore's entrepot and export orientation are canonical; the test is valuable mainly to keep the claim pinned to data.",
            steelman="Singapore's trade ratios are inflated by re-exports and entrepot accounting. A supported trade-openness result does not prove all small or large economies can replicate the same trade/GDP ratios, nor that manufacturing upgrading was caused by free trade alone.",
            notes="Port-state accounting is a central caveat; result card reports the descriptive pattern only.",
        ),
        Study(
            hid="singapore_lky_fdi_manufacturing_upgrade_1970_1990",
            topic="growth",
            claim=(
                "Singapore's LKY-era industrial strategy worked through disciplined openness to "
                "foreign capital and manufacturing upgrading: FDI inflows were persistently high, "
                "FDI intensity exceeded regional peers, manufacturing value added rose sharply, and "
                "manufactured exports dominated by 1990."
            ),
            sample_countries=["SGP"] + PEERS,
            period=(1970, 1990),
            outcome_dim=["industrial_capability", "capital_flows", "trade_liberalisation"],
            policy_family=["industrial_policy", "trade_policy", "institutional_reform"],
            treatment_tags=["edb_1961", "fdi_opening", "jurong_industrial_estate"],
            variables=[
                {"name": "fdi_inflows_pct_gdp", "source": fdi, "transformation": "annual_mean"},
                {"name": "manufacturing_value_added_pct_gdp", "source": manuf_va, "transformation": "endpoint_change"},
                {"name": "manufactured_exports_share", "source": manuf_exports, "transformation": "endpoint_level"},
            ],
            metrics=[
                m("fdi_intensity_mean", "FDI inflows averaged a large GDP share", fdi, ">= 5% of GDP", "1970-1990", lambda: gt(mean_between(fdi, "SGP", 1970, 1990), 5.0, "SGP FDI/GDP mean"), "FDI inflow series is independent from manufacturing/output shares."),
                m("fdi_vs_peer_median_1990", "FDI intensity in 1990 exceeded regional peer median", fdi, ">= 3.0x peer median", "1990", lambda: gt(endpoint_vs_peer_median(fdi, "SGP", PEERS, 1990), 3.0, "SGP 1990 FDI/GDP / peer median"), "Cross-country FDI comparison tests exceptional capital openness."),
                m("manufacturing_va_share_gain", "Manufacturing value-added share rose during early industrialisation", manuf_va, ">= 10pp increase", "1965-1980", lambda: gt(pp_change(manuf_va, "SGP", 1965, 1980), 10.0, "SGP manufacturing VA share change"), "Domestic production-structure check separate from FDI."),
                m("manufactured_exports_share_1990", "Manufactured exports were dominant by 1990", manuf_exports, ">= 60% of merchandise exports", "1990", lambda: gt(value_at(manuf_exports, "SGP", 1990), 60.0, "SGP manufactured exports share 1990"), "Export-composition check separate from value added."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.80,
            disclosure="Prior expects support but acknowledges selection: this is the successful Singapore case, not the distribution of all EDB-style industrial-policy attempts.",
            steelman="The developmentalist steelman is strong: EDB targeting, land assembly, infrastructure, skills policy, and multinational courting were active state interventions. If supported, the result is not a laissez-faire-only win; it is evidence for a high-state-capacity, externally disciplined market-development hybrid.",
            notes="Designed to avoid collapsing Singapore into either pure laissez-faire or pure planning.",
        ),
        Study(
            hid="singapore_lky_rule_of_law_government_effectiveness_legacy_1996_2024",
            topic="institutional_quality",
            claim=(
                "Singapore's post-LKY institutional legacy is visible in WGI data: control of "
                "corruption, government effectiveness, and rule of law remain near the top of the "
                "regional peer set from 1996 to 2024. This is a legacy pattern, not a direct causal "
                "test of Lee Kuan Yew's premiership."
            ),
            sample_countries=["SGP"] + PEERS,
            period=(1996, 2024),
            outcome_dim=["institutional_quality"],
            policy_family=["institutional_reform"],
            treatment_tags=["prevention_of_corruption_act_1960", "cpib_anti_corruption", "lky_institutional_legacy"],
            variables=[
                {"name": "control_of_corruption", "source": cc, "transformation": "annual_mean"},
                {"name": "government_effectiveness", "source": ge, "transformation": "annual_mean"},
                {"name": "rule_of_law", "source": rl, "transformation": "annual_mean"},
            ],
            metrics=[
                m("control_corruption_mean", "Control of corruption mean is very high", cc, ">= 1.75", "1996-2024", lambda: gt(mean_between(cc, "SGP", 1996, 2024), 1.75, "SGP WGI CC mean"), "Corruption-control pillar distinct from administrative effectiveness."),
                m("government_effectiveness_mean", "Government effectiveness mean is very high", ge, ">= 2.00", "1996-2024", lambda: gt(mean_between(ge, "SGP", 1996, 2024), 2.0, "SGP WGI GE mean"), "Administrative effectiveness pillar distinct from legal-rule pillar."),
                m("rule_of_law_mean", "Rule of law mean remains high", rl, ">= 1.25", "1996-2024", lambda: gt(mean_between(rl, "SGP", 1996, 2024), 1.25, "SGP WGI RL mean"), "Rule of law pillar distinct from corruption and GE."),
                m("corruption_control_peer_gap_2024", "2024 corruption control exceeds regional peer median by a large margin", cc, ">= 1.0 point above peer median", "2024", lambda: gt((value_at(cc, "SGP", 2024) or 0) - (peer_median_at(cc, PEERS, 2024) or 0), 1.0, "SGP 2024 CC minus peer median"), "Peer-gap check prevents absolute-threshold-only grading."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.86,
            disclosure="Prior is high, but WGI starts after Lee stepped down as prime minister; the spec is explicitly legacy-pattern evidence.",
            steelman="WGI is perception-based and post-1996, so it cannot by itself prove LKY caused the institutional equilibrium. It may also conflate clean administration with constrained political competition and press freedom, which this hypothesis does not score as welfare-positive or negative.",
            notes="Legacy pattern only; direct LKY-era corruption data remains a data need.",
        ),
        Study(
            hid="singapore_lky_human_capital_upgrade_1965_2010",
            topic="labour",
            claim=(
                "Singapore's LKY-era and immediate post-LKY human-capital trajectory shows a "
                "large education upgrade: PWT human-capital index roughly doubled, upper-secondary "
                "attainment rose sharply, tertiary enrolment became mass-participation, and the 2010 "
                "human-capital level reached advanced-economy territory."
            ),
            sample_countries=["SGP"] + PEERS_WITH_TWN,
            period=(1965, 2010),
            outcome_dim=["employment_labour", "productivity", "industrial_capability"],
            policy_family=["labour_market", "industrial_policy", "institutional_reform"],
            treatment_tags=["singapore_bilingual_education", "skills_upgrading", "human_capital_upgrade"],
            variables=[
                {"name": "pwt_human_capital", "source": hc, "transformation": "endpoint_change"},
                {"name": "upper_secondary_attainment", "source": upper_sec, "transformation": "endpoint_change"},
                {"name": "tertiary_gross_enrolment", "source": tertiary, "transformation": "endpoint_level"},
            ],
            metrics=[
                m("pwt_hc_index_gain", "PWT human-capital index gain from 1965 to 2010", hc, ">= 1.20 index points", "1965-2010", lambda: gt(pp_change(hc, "SGP", 1965, 2010), 1.2, "SGP PWT hc change"), "PWT human-capital stock measure independent from WDI attainment/enrolment."),
                m("pwt_hc_index_ratio", "PWT human-capital index endpoint ratio", hc, ">= 1.8x", "1965-2010", lambda: gt(ratio(hc, "SGP", 1965, 2010), 1.8, "SGP PWT hc 2010/1965"), "Ratio check complements absolute index-point change."),
                m("upper_secondary_attainment_gain", "Upper-secondary attainment rose from 1980 to 2010", upper_sec, ">= 35pp increase", "1980-2010", lambda: gt(pp_change(upper_sec, "SGP", 1980, 2010), 35.0, "SGP upper-secondary attainment change"), "Attainment stock measure distinct from PWT index."),
                m("tertiary_enrolment_mass_participation", "Tertiary gross enrolment reached mass-participation scale by 2010", tertiary, ">= 70%", "2010", lambda: gt(value_at(tertiary, "SGP", 2010), 70.0, "SGP tertiary gross enrolment 2010"), "Flow enrolment measure distinct from attainment stock."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.78,
            disclosure="Prior expects support; education data has gaps in the early WDI record, so the spec uses PWT hc plus later WDI attainment/enrolment checks.",
            steelman="Education upgrading is not uniquely LKY-caused: family income growth, migration selection, English-language advantages, and later post-1990 reforms matter. A supported result should be read as confirming the human-capital pattern, not assigning causal shares.",
            notes="Combines PWT and WDI because no single local series spans every desired education margin.",
        ),
        Study(
            hid="singapore_lky_low_tax_high_savings_market_rules_1970_1990",
            topic="fiscal",
            claim=(
                "The LKY-era Singapore fiscal-market model combined high national savings, "
                "relatively low tax take, fiscal surpluses, and high economic/trade-freedom scores "
                "rather than relying on a large transfer state."
            ),
            sample_countries=["SGP"] + PEERS,
            period=(1970, 1990),
            outcome_dim=["fiscal_policy", "taxation", "trade_liberalisation", "institutional_quality"],
            policy_family=["tax_policy", "institutional_reform", "trade_policy", "welfare_architecture"],
            treatment_tags=["cpf_forced_saving", "low_tax_state", "fiscal_surplus", "market_rules"],
            variables=[
                {"name": "gross_savings_pct_gni", "source": savings, "transformation": "annual_mean"},
                {"name": "tax_revenue_pct_gdp", "source": tax, "transformation": "annual_mean"},
                {"name": "net_lending_pct_gdp", "source": net_lending, "transformation": "annual_mean"},
                {"name": "efw_summary_index", "source": efw, "transformation": "endpoint_level"},
                {"name": "efw_trade_freedom", "source": trade_freedom, "transformation": "endpoint_level"},
            ],
            metrics=[
                m("gross_savings_high", "Gross savings averaged high after WDI coverage begins", savings, ">= 30% of GNI", "1972-1990", lambda: gt(mean_between(savings, "SGP", 1972, 1990), 30.0, "SGP gross savings mean"), "Savings series is separate from fiscal-balance and EFW measures."),
                m("tax_take_low", "Tax revenue share stayed relatively low", tax, "<= 18% of GDP", "1972-1990", lambda: lt(mean_between(tax, "SGP", 1972, 1990), 18.0, "SGP tax revenue/GDP mean"), "Tax share checks state financing footprint."),
                m("net_lending_surplus", "General government net lending averaged in surplus", net_lending, ">= 3% of GDP", "1972-1990", lambda: gt(mean_between(net_lending, "SGP", 1972, 1990), 3.0, "SGP net lending/GDP mean"), "Fiscal balance check distinct from tax/savings."),
                m("economic_freedom_1990", "EFW summary index reached high-market-rule level", efw, ">= 8.0", "1990", lambda: gt(value_at(efw, "SGP", 1990), 8.0, "SGP EFW summary 1990"), "Market-rule institutional composite independent from WDI fiscal data."),
                m("trade_freedom_1990", "EFW trade-freedom score reached near-ceiling by 1990", trade_freedom, ">= 9.0", "1990", lambda: gt(value_at(trade_freedom, "SGP", 1990), 9.0, "SGP EFW trade freedom 1990"), "Trade-freedom subindex separately checks openness-policy stance."),
            ],
            support_threshold=4,
            refute_threshold=2,
            prior=0.76,
            disclosure="Prior expects support, but the framing risks overstating 'small state' because CPF/HDB are compulsory and state-shaped even when not counted as transfer spending.",
            steelman="The heterodox steelman is that Singapore's low tax and high savings were embedded in compulsory savings, public land ownership, HDB housing provision, and state-guided investment. Supported fiscal-market metrics do not make the case a pure libertarian model.",
            notes="Designed to separate tax/spending footprint from compulsory-saving and housing architecture caveats.",
        ),
    ]


def hypothesis_doc(study: Study) -> dict:
    return {
        "hypothesis_id": study.hid,
        "version": 1,
        "status": "pre_registered",
        "topic": study.topic,
        "claim": study.claim,
        "evidence_type": "canonical_case_multi_metric",
        "sample": {
            "countries": study.sample_countries,
            "period": list(study.period),
            "temporal_structure": "panel" if len(study.sample_countries) > 1 else "time_series",
        },
        "canonical_metrics": [
            {
                "metric_id": metric.metric_id,
                "description": metric.description,
                "threshold": metric.threshold,
                "window": metric.window,
                "source": metric.source,
                "direction": metric.direction,
                "independence_justification": metric.independence_justification,
            }
            for metric in study.metrics
        ],
        "multi_metric_falsification": {
            "total_metrics": len(study.metrics),
            "support_threshold": study.support_threshold,
            "refute_threshold": study.refute_threshold,
        },
        "variables": {"outcome": study.variables},
        "estimator": {
            "template": "multi_metric_checklist",
            "clustering": "none",
            "notes": "Custom Lee Kuan Yew / Singapore checklist using local WDI, WGI, PWT, and Fraser EFW vintages.",
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if at least {study.support_threshold} of {len(study.metrics)} pre-registered "
                f"metrics meet their thresholds. REFUTED if at most {study.refute_threshold} metrics meet "
                "after available data are evaluated. Otherwise PARTIAL or INCONCLUSIVE_DATA_PENDING."
            ),
            "test": f"{study.hid}_local_multimetric_checklist",
            "threshold": f"MET >= {study.support_threshold} of {len(study.metrics)}; REFUTE when MET <= {study.refute_threshold}",
        },
        "prior_confidence": study.prior,
        "disclosure": study.disclosure,
        "steelman": f"hypotheses/steelman/{study.hid}.md",
        "scope": {
            "period": list(study.period),
            "countries": study.sample_countries,
            "outcome_dim": study.outcome_dim,
            "policy_family": study.policy_family,
            "treatment_tags": study.treatment_tags,
        },
        "notes": study.notes,
    }


def evaluate(study: Study) -> tuple[str, str, list[dict]]:
    rows = []
    met = 0
    pending = 0
    for metric in study.metrics:
        observed, ok, note = metric.evaluator()
        if ok is True:
            status = "MET"
            met += 1
        elif ok is False:
            status = "NOT_MET"
        else:
            status = "PENDING_DATA"
            pending += 1
        rows.append({
            "metric_id": metric.metric_id,
            "description": metric.description,
            "source": metric.source,
            "window": metric.window,
            "threshold": metric.threshold,
            "observed": observed,
            "status": status,
            "note": note,
        })
    if pending == len(rows):
        return "INCONCLUSIVE_DATA_PENDING", "all metrics pending data", rows
    if met >= study.support_threshold:
        return "SUPPORTED", f"{met} of {len(rows)} metrics met threshold (support threshold {study.support_threshold})", rows
    if met <= study.refute_threshold and pending == 0:
        return "REFUTED", f"only {met} of {len(rows)} metrics met threshold (refute threshold {study.refute_threshold})", rows
    return "PARTIAL", f"{met} of {len(rows)} metrics met; {pending} pending", rows


def source_paths(study: Study) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for metric in study.metrics:
        pub, series = split_source(metric.source)
        p = latest_vintage(pub, series)
        if p is not None:
            paths[metric.source] = p
    return paths


def write_study(study: Study) -> None:
    out_dir = ROOT / "hypotheses" / study.topic
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
    text += yaml.dump(hypothesis_doc(study), Dumper=NoAliasDumper, sort_keys=False, width=92)
    (out_dir / f"{study.hid}.yaml").write_text(text)

    STEEL.mkdir(parents=True, exist_ok=True)
    (STEEL / f"{study.hid}.md").write_text(f"# Steelman: {study.hid}\n\n{study.steelman}\n")

    verdict, reason, rows = evaluate(study)
    run_dir = RUNS / study.hid
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = source_paths(study)
    pd.DataFrame(rows).to_parquet(run_dir / "coefficients.parquet", index=False)
    (run_dir / "chart_data.json").write_text(json.dumps(rows, indent=2) + "\n")
    diag = {
        "hypothesis_id": study.hid,
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "template": "singapore_lky_local_multimetric_checklist",
        "metrics": rows,
        "support_threshold": study.support_threshold,
        "refute_threshold": study.refute_threshold,
        "vintages": {src: str(p.relative_to(ROOT)) for src, p in paths.items()},
        "sha256": {src: sha256(p) for src, p in paths.items()},
        "runner": "scripts/generate_singapore_lky_wave.py",
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    (run_dir / "manifest.yaml").write_text(yaml.dump({
        "hypothesis_id": study.hid,
        "status": verdict,
        "reason": reason,
        "vintages": {src: str(p.relative_to(ROOT)) for src, p in paths.items()},
    }, Dumper=NoAliasDumper, sort_keys=False))
    table = pd.DataFrame(rows)
    cols = ["metric_id", "observed", "threshold", "status", "note"]
    lines = [
        f"# Result card - {study.hid}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {study.claim}",
        f"- **Falsification rule:** SUPPORTED if at least {study.support_threshold} of {len(study.metrics)} metrics meet their thresholds; REFUTED if at most {study.refute_threshold} meet after available data are evaluated.",
        f"- **Falsification test:** {study.hid}_local_multimetric_checklist",
        "",
        "## Metric Results",
        "| metric | observed | threshold | status | note |",
        "|---|---:|---|---|---|",
    ]
    for _, row in table[cols].iterrows():
        observed = "pending" if pd.isna(row["observed"]) else f"{row['observed']:.3f}"
        note = str(row["note"]).replace("|", "/")
        lines.append(f"| {row['metric_id']} | {observed} | {row['threshold']} | {row['status']} | {note} |")
    lines += [
        "",
        "## Interpretation",
        "This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.",
        "",
        "## Sources",
    ]
    for src, path in paths.items():
        lines.append(f"- `{src}` -> `{path.relative_to(ROOT)}`")
    lines += ["", f"## Steelman", f"See `hypotheses/steelman/{study.hid}.md`.", ""]
    (run_dir / "result_card.md").write_text("\n".join(lines))
    (run_dir / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        '"""Regenerate the Singapore LKY local checklist wave."""\n'
        "from pathlib import Path\n"
        "import runpy\n\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "runpy.run_path(str(root / 'scripts' / 'generate_singapore_lky_wave.py'), run_name='__main__')\n"
    )
    print(f"{study.hid}: {verdict} - {reason}")


def write_hdb_blocked() -> None:
    hid = "singapore_lky_hdb_homeownership_public_housing_1960_1990"
    doc = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": "housing",
        "claim": (
            "Singapore's HDB public-housing and CPF housing-finance system increased mass "
            "homeownership and reduced overcrowding between 1960 and 1990 without relying on a "
            "general tax-financed public-housing entitlement model."
        ),
        "evidence_type": "descriptive",
        "sample": {"countries": ["SGP"], "period": [1960, 1990], "temporal_structure": "time_series"},
        "variables": {"outcome": [
            {"name": "homeownership_rate", "source": "singapore_hdb:homeownership_rate", "transformation": "endpoint_change"},
            {"name": "share_population_in_hdb_flats", "source": "singapore_hdb:hdb_resident_share", "transformation": "endpoint_change"},
            {"name": "persons_per_room_or_overcrowding", "source": "singapore_hdb:overcrowding", "transformation": "endpoint_change"},
        ]},
        "estimator": {"template": "descriptive", "clustering": "none", "notes": "Data-gated HDB/homeownership study; runner intentionally refuses to grade until Singapore HDB vintages are present."},
        "falsification": {
            "rule": "SUPPORTED if homeownership rises by at least 45 percentage points, HDB resident share exceeds 70 percent by 1990, and overcrowding falls materially. REFUTED if homeownership rises by less than 20 percentage points or HDB resident share remains below 40 percent.",
            "test": "singapore_hdb_homeownership_endpoint_check",
            "threshold": "homeownership_change >= 45pp AND hdb_resident_share_1990 >= 70; refute if homeownership_change < 20pp OR hdb_share_1990 < 40",
        },
        "prior_confidence": 0.80,
        "disclosure": "Prior expects support, but no local HDB vintage is present. The spec is included as a visible data-repair target rather than auto-scored.",
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {
            "period": [1960, 1990],
            "countries": ["SGP"],
            "outcome_dim": ["housing", "welfare_state"],
            "policy_family": ["housing_policy", "welfare_architecture"],
            "treatment_tags": ["hdb_1960", "cpf_housing_finance", "public_housing_homeownership"],
        },
        "notes": "Major Singapore/LKY pillar. Requires HDB annual-report or SingStat housing vintage before graduation.",
    }
    out_dir = ROOT / "hypotheses" / "housing"
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
    text += yaml.dump(doc, Dumper=NoAliasDumper, sort_keys=False, width=92)
    (out_dir / f"{hid}.yaml").write_text(text)
    STEEL.mkdir(parents=True, exist_ok=True)
    (STEEL / f"{hid}.md").write_text(
        "# Steelman: Singapore HDB homeownership public housing\n\n"
        "The strongest objection is that HDB's achievements combine heavy state land control, compulsory savings, resale restrictions, ethnic quotas, and a small-city geography. Even if homeownership outcomes are strong, the model may not generalise and should not be treated as simple free-market housing policy.\n"
    )
    run_dir = RUNS / hid
    run_dir.mkdir(parents=True, exist_ok=True)
    diag = {
        "hypothesis_id": hid,
        "verdict": "INCONCLUSIVE_DATA_PENDING - Singapore HDB/homeownership vintages are not on disk",
        "verdict_label": "INCONCLUSIVE_DATA_PENDING",
        "verdict_reason": "No local singapore_hdb vintages for homeownership_rate, hdb_resident_share, or overcrowding.",
        "missing_sources": ["singapore_hdb:homeownership_rate", "singapore_hdb:hdb_resident_share", "singapore_hdb:overcrowding"],
        "runner": "scripts/generate_singapore_lky_wave.py",
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    (run_dir / "manifest.yaml").write_text(yaml.dump({
        "hypothesis_id": hid,
        "status": "INCONCLUSIVE_DATA_PENDING",
        "reason": diag["verdict_reason"],
    }, Dumper=NoAliasDumper, sort_keys=False))
    (run_dir / "BLOCKED.md").write_text(
        "# Blocked - Singapore HDB homeownership study\n\n"
        "Required local vintages:\n"
        "- `singapore_hdb:homeownership_rate` annual or census endpoints, 1960-1990.\n"
        "- `singapore_hdb:hdb_resident_share` annual/census endpoints, 1960-1990.\n"
        "- `singapore_hdb:overcrowding` persons-per-room or equivalent housing-quality measure.\n\n"
        "Do not score this hypothesis until those vintages are ingested and provenance is recorded.\n"
    )
    (run_dir / "result_card.md").write_text(
        f"# Result card - {hid}\n\n"
        "**Verdict:** INCONCLUSIVE_DATA_PENDING - Singapore HDB/homeownership vintages are not on disk\n\n"
        "## Missing data\n\n"
        "- `singapore_hdb:homeownership_rate`\n"
        "- `singapore_hdb:hdb_resident_share`\n"
        "- `singapore_hdb:overcrowding`\n\n"
        "This is registered as a high-priority data-repair study rather than a scored result.\n"
    )
    (run_dir / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        '"""Regenerate the Singapore LKY local checklist wave."""\n'
        "from pathlib import Path\n"
        "import runpy\n\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "runpy.run_path(str(root / 'scripts' / 'generate_singapore_lky_wave.py'), run_name='__main__')\n"
    )
    print(f"{hid}: INCONCLUSIVE_DATA_PENDING - missing HDB vintages")


def write_policies() -> None:
    policies = [
        {
            "policy_id": "singapore_edb_export_industrialisation_1961",
            "status": "candidate",
            "title": "Singapore EDB export industrialisation, 1961",
            "countries": ["SGP"],
            "timeframe": {"start": 1961, "end": 1990},
            "description": "Singapore created the Economic Development Board in 1961 to coordinate industrial estates, investment promotion, tax incentives, skills support, and multinational manufacturing attraction. Under Lee Kuan Yew's government after independence, the EDB became the central institution for export-oriented industrialisation rather than import-substitution autarky.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "strong", "intended": True, "rationale": "EDB strategy intentionally courted export manufacturers and foreign investors."},
                {"axis": "fiscal.sectoral_subsidy", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Tax incentives, industrial estates, and targeted promotion supported selected sectors."},
                {"axis": "institutional.property_rights", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Foreign-investor guarantees and commercial-law credibility strengthened investment security."},
            ],
            "linked_hypotheses": ["singapore_lky_growth_takeoff_1965_1990", "singapore_lky_fdi_manufacturing_upgrade_1970_1990"],
            "linked_conditions": ["innovation_and_technology_diffusion", "capital_allocation_among_firms"],
            "notes": "Directly linked to new LKY/Singapore local-data studies.",
        },
        {
            "policy_id": "singapore_container_port_strategy_1972",
            "status": "candidate",
            "title": "Singapore container port strategy, 1972",
            "countries": ["SGP"],
            "timeframe": {"start": 1972, "end": 1990},
            "description": "Singapore opened the Tanjong Pagar container terminal in 1972 and used port corporatisation, logistics investment, and customs/transport coordination to deepen its role as a high-throughput trade hub. The policy bundle reinforced the LKY-era choice to build a globally connected port-state economy.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "strong", "intended": True, "rationale": "Container-port investment lowered trade frictions and expanded logistics openness."},
                {"axis": "regulatory.product_market_competition", "direction": "+", "magnitude": "weak", "intended": True, "rationale": "Port efficiency improved contestability for export/import-linked firms."},
            ],
            "linked_hypotheses": ["singapore_lky_trade_openness_port_state_1965_1990", "singapore_lky_growth_takeoff_1965_1990"],
            "notes": "Direct policy card for the trade-openness and port-state LKY study.",
        },
        {
            "policy_id": "singapore_prevention_corruption_act_cpib_1960",
            "status": "candidate",
            "title": "Singapore Prevention of Corruption Act and CPIB strengthening, 1960",
            "countries": ["SGP"],
            "timeframe": {"start": 1960, "end": "ongoing"},
            "description": "The Prevention of Corruption Act 1960 strengthened Singapore's anti-corruption powers and, under Lee Kuan Yew's government, was paired with an empowered Corrupt Practices Investigation Bureau, high civil-service discipline, and prosecution credibility. The policy content moved institutional enforcement rather than redistribution or macro demand management.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "institutional.rule_of_law", "direction": "+", "magnitude": "strong", "intended": True, "rationale": "Anti-corruption investigation and prosecution powers strengthened predictable public integrity enforcement."},
                {"axis": "institutional.judicial_independence", "direction": "+", "magnitude": "weak", "intended": True, "rationale": "Credible prosecution and court enforcement were part of the anti-corruption architecture, though the broader political system remains contested."},
            ],
            "linked_hypotheses": ["singapore_lky_rule_of_law_government_effectiveness_legacy_1996_2024"],
            "notes": "Legacy WGI evidence is post-1996 and should not be treated as direct causal proof of the 1960 act.",
        },
        {
            "policy_id": "singapore_bilingual_skills_policy_1966_1979",
            "status": "candidate",
            "title": "Singapore bilingual and skills-upgrading policy, 1966-1979",
            "countries": ["SGP"],
            "timeframe": {"start": 1966, "end": 1979},
            "description": "Singapore's education policy from the late 1960s through the 1979 education reforms expanded English-plus-mother-tongue bilingual schooling, technical education, streaming, and workforce skills formation. The policy aimed to make a small labour force usable by multinational manufacturing and services while preserving social cohesion.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Education and technical-training expansion required public spending and institutional capacity."},
                {"axis": "regulatory.labour_market_flexibility", "direction": "+", "magnitude": "weak", "intended": True, "rationale": "Skills formation improved labour-market adaptability rather than employment protection rigidity."},
            ],
            "linked_hypotheses": ["singapore_lky_human_capital_upgrade_1965_2010", "singapore_lky_fdi_manufacturing_upgrade_1970_1990"],
            "notes": "Axis coding is imperfect because the axis taxonomy lacks a direct education/human-capital axis.",
        },
        {
            "policy_id": "singapore_hdb_homeownership_program_1960",
            "status": "candidate",
            "title": "Singapore HDB homeownership programme, 1960",
            "countries": ["SGP"],
            "timeframe": {"start": 1960, "end": "ongoing"},
            "description": "Singapore created the Housing and Development Board in 1960 and later connected public housing purchase to CPF savings, producing a distinctive public-land, leasehold homeownership, ethnic-integration, and forced-saving housing architecture. This is one of the central LKY-era policy pillars but requires dedicated HDB/SingStat data before scoring.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Public housing construction and land assembly expanded state housing provision."},
                {"axis": "institutional.property_rights", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Leasehold homeownership created broad household asset claims, though under state land and resale rules."},
                {"axis": "fiscal.transfer_expansion", "direction": "mixed", "magnitude": "weak", "intended": True, "rationale": "The architecture subsidised housing access but relied heavily on compulsory individual savings rather than pure cash transfers."},
            ],
            "linked_hypotheses": ["singapore_lky_hdb_homeownership_public_housing_1960_1990", "singapore_lky_low_tax_high_savings_market_rules_1970_1990"],
            "notes": "Directly exposes the HDB data gap in the policy browser.",
        },
        {
            "policy_id": "singapore_cpf_housing_and_savings_expansion_1968_1984",
            "status": "candidate",
            "title": "Singapore CPF housing and savings expansion, 1968-1984",
            "countries": ["SGP"],
            "timeframe": {"start": 1968, "end": 1984},
            "description": "Singapore expanded CPF beyond retirement saving into housing finance from 1968 and later medical saving through Medisave in 1984. The result was a compulsory individual-account architecture that raised measured savings and asset accumulation while limiting general tax-financed transfer expansion.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "fiscal.transfer_expansion", "direction": "-", "magnitude": "moderate", "intended": True, "rationale": "Compulsory individual accounts substituted for broad tax-financed cash transfers."},
                {"axis": "institutional.property_rights", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "CPF balances are individually attributed claims used for housing, retirement, and medical accounts."},
                {"axis": "fiscal.spending_level", "direction": "-", "magnitude": "weak", "intended": True, "rationale": "Forced saving reduced pressure for a larger pay-as-you-go welfare state."},
            ],
            "linked_hypotheses": ["singapore_lky_low_tax_high_savings_market_rules_1970_1990", "singapore_cpf_national_savings_effect", "singapore_cpf_institutional_complementarity"],
            "notes": "Complements existing CPF policy cards with direct links to the new fiscal-market LKY study.",
        },
    ]
    for doc in policies:
        text = "# yaml-language-server: $schema=../schemas/policy.schema.json\n"
        text += yaml.dump(doc, Dumper=NoAliasDumper, sort_keys=False, width=92)
        (POLICIES / f"{doc['policy_id']}.yaml").write_text(text)


def main() -> None:
    for study in studies():
        write_study(study)
    write_hdb_blocked()
    write_policies()


if __name__ == "__main__":
    main()
