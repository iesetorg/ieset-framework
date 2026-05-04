#!/usr/bin/env python3
"""Generate a second Singapore/LKY and UAE case-study wave.

The wave is conservative by design: every scored hypothesis uses only local
vintages already present in data/vintages. The output is reproducible specs,
steelmen, run artifacts, and policy links. It does not touch unrelated data
fetcher work or scratch audit files.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
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

ASIA_PEERS = ["HKG", "KOR", "MYS", "THA", "IDN", "PHL"]
GCC_PEERS = ["SAU", "KWT", "QAT", "OMN", "BHR"]


@dataclass(frozen=True)
class Metric:
    metric_id: str
    description: str
    sources: list[str]
    threshold: str
    window: str
    evaluator: Callable[[], tuple[Optional[float], Optional[bool], str]]
    direction: str = "supports_claim"
    independence_justification: str = "Independent outcome/source layer within the case bundle."


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
    status: str = "pre_registered"


def split_source(src: str) -> tuple[str, str]:
    pub, _, series = src.partition(":")
    return pub, series


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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


def sum_between(src: str, country: str, start: int, end: int) -> Optional[float]:
    df = panel(src)
    sub = df[(df["country"] == country) & (df["year"] >= start) & (df["year"] <= end)]
    if sub.empty:
        return None
    return float(sub["value"].sum())


def pp_change(src: str, country: str, start: int, end: int) -> Optional[float]:
    a = value_at(src, country, start)
    b = value_at(src, country, end)
    if a is None or b is None:
        return None
    return float(b - a)


def decrease(src: str, country: str, start: int, end: int) -> Optional[float]:
    change = pp_change(src, country, start, end)
    if change is None:
        return None
    return -change


def ratio(src: str, country: str, start: int, end: int) -> Optional[float]:
    a = value_at(src, country, start)
    b = value_at(src, country, end)
    if a is None or b is None or a == 0:
        return None
    return float(b / a)


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


def endpoint_minus_peer_median(src: str, country: str, peers: list[str], year: int) -> Optional[float]:
    v = value_at(src, country, year)
    med = peer_median_at(src, peers, year)
    if v is None or med is None:
        return None
    return float(v - med)


def arrivals_per_capita(country: str, year: int) -> Optional[float]:
    arrivals = value_at("world_bank_wdi:ST.INT.ARVL", country, year)
    pop = value_at("world_bank_wdi:SP.POP.TOTL", country, year)
    if arrivals is None or pop is None or pop == 0:
        return None
    return float(arrivals / pop)


def gt(value: Optional[float], cutoff: float, label: str) -> tuple[Optional[float], Optional[bool], str]:
    if value is None:
        return None, None, f"missing data for {label}"
    return value, value >= cutoff, f"{label} = {value:.3f}; threshold >= {cutoff:g}"


def lt(value: Optional[float], cutoff: float, label: str) -> tuple[Optional[float], Optional[bool], str]:
    if value is None:
        return None, None, f"missing data for {label}"
    return value, value <= cutoff, f"{label} = {value:.3f}; threshold <= {cutoff:g}"


def metric(metric_id: str, description: str, sources: list[str], threshold: str, window: str,
           evaluator: Callable[[], tuple[Optional[float], Optional[bool], str]],
           independence: str) -> Metric:
    return Metric(metric_id, description, sources, threshold, window, evaluator,
                  independence_justification=independence)


def studies() -> list[Study]:
    life = "world_bank_wdi:SP.DYN.LE00.IN"
    infant = "world_bank_wdi:SP.DYN.IMRT.IN"
    health_spend = "world_bank_wdi:SH.XPD.CHEX.PC.CD"
    arrivals = "world_bank_wdi:ST.INT.ARVL"
    pop = "world_bank_wdi:SP.POP.TOTL"
    tourism_receipts = "world_bank_wdi:ST.INT.RCPT.XP.ZS"
    trade = "world_bank_wdi:NE.TRD.GNFS.ZS"
    internet = "world_bank_wdi:IT.NET.USER.ZS"
    hightech = "world_bank_wdi:TX.VAL.TECH.MF.ZS"
    services = "world_bank_wdi:NV.SRV.TOTL.ZS"
    fdi = "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS"
    private_credit = "world_bank_wdi:FS.AST.PRVT.GD.ZS"
    migrant_share = "world_bank_wdi:SM.POP.TOTL.ZS"
    net_migration = "world_bank_wdi:SM.POP.NETM"
    female_lfp = "world_bank_wdi:SL.TLF.CACT.FE.ZS"
    oil_rents = "world_bank_wdi:NY.GDP.PETR.RT.ZS"
    fuel_exports = "world_bank_wdi:TX.VAL.FUEL.ZS.UN"
    efw = "fraser_efw:summary_index"
    trade_freedom = "fraser_efw:freedom_to_trade_internationally"
    regulation = "fraser_efw:regulation"
    ge = "wgi:GE.EST"
    rq = "wgi:RQ.EST"
    rl = "wgi:RL.EST"
    cc = "wgi:CC.EST"

    return [
        Study(
            hid="singapore_lky_public_health_outcomes_1965_1990",
            topic="healthcare",
            claim=(
                "Singapore's Lee Kuan Yew era public-health and disciplined social-policy bundle "
                "coincided with first-world health outcome convergence by 1990: life expectancy rose "
                "strongly, infant mortality collapsed, and Singapore beat regional market-economy peers "
                "on both endpoints."
            ),
            sample_countries=["SGP"] + ASIA_PEERS,
            period=(1965, 1990),
            outcome_dim=["life_expectancy_health", "welfare_state"],
            policy_family=["welfare_architecture", "institutional_reform"],
            treatment_tags=["lky_public_health", "singapore_medisave_1984", "urban_sanitation"],
            variables=[
                {"name": "life_expectancy", "source": life, "transformation": "endpoint_change"},
                {"name": "infant_mortality", "source": infant, "transformation": "endpoint_change"},
                {"name": "health_spending_per_capita", "source": health_spend, "transformation": "later_robustness"},
            ],
            metrics=[
                metric("life_expectancy_gain", "Life expectancy gain during LKY prime-minister era", [life], ">= 7 years", "1965-1990", lambda: gt(pp_change(life, "SGP", 1965, 1990), 7.0, "SGP life expectancy gain"), "Mortality/longevity endpoint distinct from infant survival."),
                metric("infant_mortality_drop", "Infant mortality decline during LKY prime-minister era", [infant], ">= 20 deaths per 1,000 live births decline", "1965-1990", lambda: gt(decrease(infant, "SGP", 1965, 1990), 20.0, "SGP infant mortality decline"), "Infant mortality is a separate health-outcome margin."),
                metric("life_expectancy_peer_gap_1990", "Life expectancy exceeded Asian peer median by 1990", [life], ">= 4 years above peer median", "1990", lambda: gt(endpoint_minus_peer_median(life, "SGP", ASIA_PEERS, 1990), 4.0, "SGP life expectancy minus Asian peer median"), "Peer endpoint check limits pure time-trend interpretation."),
                metric("infant_mortality_peer_ratio_1990", "Infant mortality was less than half regional peer median", [infant], "<= 0.50x peer median", "1990", lambda: lt(endpoint_vs_peer_median(infant, "SGP", ASIA_PEERS, 1990), 0.50, "SGP infant mortality / Asian peer median"), "Cross-sectional infant mortality check independent from domestic trend."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.78,
            disclosure="Prior expects support, but the design is descriptive and cannot separate sanitation, income growth, housing, primary care, and later Medisave channels.",
            steelman="The strongest objection is that health outcomes followed income growth, urban water/sanitation, and global medical diffusion, not a uniquely LKY institutional design. This test confirms outcome convergence, not the causal share of any one policy lever.",
            notes="Descriptive health-outcome convergence checklist using WDI endpoints.",
        ),
        Study(
            hid="singapore_lky_changi_air_hub_tourism_1981_2019",
            topic="trade",
            claim=(
                "Singapore's Changi airport, SIA, port-state, and open-city strategy produced a durable "
                "air-services and visitor hub: by the pre-COVID endpoint, tourist arrivals were multiple "
                "times resident population, receipts were material, and the same economy remained extremely "
                "trade-open."
            ),
            sample_countries=["SGP"] + ASIA_PEERS,
            period=(1981, 2019),
            outcome_dim=["trade_liberalisation", "capital_flows"],
            policy_family=["trade_policy", "industrial_policy"],
            treatment_tags=["changi_airport_1981", "singapore_airlines_hub", "open_city_services"],
            variables=[
                {"name": "tourist_arrivals", "source": arrivals, "transformation": "endpoint_level"},
                {"name": "tourism_receipts_share_exports", "source": tourism_receipts, "transformation": "annual_mean"},
                {"name": "trade_openness", "source": trade, "transformation": "endpoint_level"},
            ],
            metrics=[
                metric("visitor_arrivals_2019", "Visitor arrivals reached large hub scale before COVID", [arrivals], ">= 15 million", "2019", lambda: gt(value_at(arrivals, "SGP", 2019), 15_000_000.0, "SGP tourist arrivals 2019"), "Arrivals count tests absolute hub scale."),
                metric("visitor_arrivals_per_capita_2019", "Visitor arrivals exceeded resident population several-fold", [arrivals, pop], ">= 3.0 arrivals per resident", "2019", lambda: gt(arrivals_per_capita("SGP", 2019), 3.0, "SGP visitor arrivals per resident 2019"), "Per-capita intensity adjusts for city-state scale."),
                metric("tourism_receipts_export_share", "Travel receipts remained material in export basket", [tourism_receipts], ">= 2% of exports mean", "1995-2019", lambda: gt(mean_between(tourism_receipts, "SGP", 1995, 2019), 2.0, "SGP tourism receipts / exports mean"), "Receipts share checks economic significance, not just passenger counts."),
                metric("trade_openness_2019", "Open-city model coincided with extreme trade openness", [trade], ">= 300% of GDP", "2019", lambda: gt(value_at(trade, "SGP", 2019), 300.0, "SGP trade/GDP 2019"), "Trade/GDP checks the broader open-city context."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.74,
            disclosure="Prior expects support; this is a hub-scale descriptive test and not proof that an airport alone caused productivity growth.",
            steelman="Singapore's visitor and trade ratios are amplified by geography, small population, and entrepot status. A supported result should be read as successful hub formation, not a universal recipe for large inland countries.",
            notes="Uses pre-COVID 2019 endpoint to avoid pandemic collapse contaminating the hub test.",
        ),
        Study(
            hid="singapore_lky_financial_deepening_market_hub_1970_2020",
            topic="growth",
            claim=(
                "Singapore's LKY-era market-rule and financial-hub trajectory produced deep private credit, "
                "large FDI intensity, and high market-rule scores by the modern endpoint, consistent with an "
                "open financial-services hub rather than a closed developmental state."
            ),
            sample_countries=["SGP"] + ASIA_PEERS,
            period=(1970, 2020),
            outcome_dim=["capital_flows", "financialisation", "institutional_quality"],
            policy_family=["regulation", "trade_policy", "institutional_reform"],
            treatment_tags=["monetary_authority_singapore_1971", "asian_dollar_market", "financial_hub"],
            variables=[
                {"name": "private_credit_depth", "source": private_credit, "transformation": "endpoint_change"},
                {"name": "fdi_inflows_share_gdp", "source": fdi, "transformation": "annual_mean"},
                {"name": "efw_summary_index", "source": efw, "transformation": "endpoint_level"},
            ],
            metrics=[
                metric("private_credit_depth_gain", "Private credit/GDP rose materially from early post-independence levels", [private_credit], ">= 70pp increase", "1970-2020", lambda: gt(pp_change(private_credit, "SGP", 1970, 2020), 70.0, "SGP private credit/GDP change"), "Domestic financial depth check separate from FDI."),
                metric("private_credit_depth_2020", "Private credit depth reached advanced financial-hub scale", [private_credit], ">= 100% of GDP", "2020", lambda: gt(value_at(private_credit, "SGP", 2020), 100.0, "SGP private credit/GDP 2020"), "Endpoint level check complements trend."),
                metric("fdi_intensity_1990_2024", "FDI inflows remained extremely high in the mature hub era", [fdi], ">= 15% of GDP mean", "1990-2024", lambda: gt(mean_between(fdi, "SGP", 1990, 2024), 15.0, "SGP FDI/GDP mean 1990-2024"), "External capital-flow channel separate from bank credit."),
                metric("efw_market_rules_2023", "Market-rule composite remained high", [efw], ">= 8.0", "2023", lambda: gt(value_at(efw, "SGP", 2023), 8.0, "SGP EFW summary 2023"), "Institutional composite check separate from financial quantities."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.76,
            disclosure="Prior expects support; the test is not a welfare assessment of financialization or housing-credit side effects.",
            steelman="Financial deepening can amplify property cycles, inequality, and external vulnerability. Singapore's success also depended on state land control, exchange-rate management, and high regulatory capacity, so this is not a laissez-faire banking deregulation claim.",
            notes="Modern endpoint captures institutional legacy and financial-hub maturation.",
        ),
        Study(
            hid="singapore_lky_high_tech_export_digital_upgrade_1990_2024",
            topic="growth",
            claim=(
                "Singapore's LKY-era human-capital and investment-promotion base was followed by a high-tech "
                "export and digital adoption profile: internet diffusion became near-universal and high-tech "
                "manufactures remained a majority of manufactured exports by the 2020s."
            ),
            sample_countries=["SGP"] + ASIA_PEERS,
            period=(1990, 2024),
            outcome_dim=["industrial_capability", "productivity"],
            policy_family=["industrial_policy", "trade_policy"],
            treatment_tags=["national_computerisation_plan_1980", "edb_electronics_cluster", "skills_upgrading"],
            variables=[
                {"name": "internet_users", "source": internet, "transformation": "endpoint_change"},
                {"name": "high_tech_exports_share", "source": hightech, "transformation": "endpoint_level"},
                {"name": "services_value_added_share", "source": services, "transformation": "endpoint_level"},
            ],
            metrics=[
                metric("internet_diffusion_gain", "Internet users share rose from near zero to near universal", [internet], ">= 85pp increase", "1990-2024", lambda: gt(pp_change(internet, "SGP", 1990, 2024), 85.0, "SGP internet-users share change"), "Digital adoption outcome independent from export composition."),
                metric("internet_users_2024", "Internet adoption reached near-universal scale", [internet], ">= 90%", "2024", lambda: gt(value_at(internet, "SGP", 2024), 90.0, "SGP internet users 2024"), "Endpoint digital adoption check."),
                metric("hightech_exports_2024", "High-tech manufactures stayed a majority of manufactured exports", [hightech], ">= 50%", "2024", lambda: gt(value_at(hightech, "SGP", 2024), 50.0, "SGP high-tech exports share 2024"), "Export-composition check separate from adoption."),
                metric("services_share_2024", "Services value-added share stayed high in mature economy", [services], ">= 70% of GDP", "2024", lambda: gt(value_at(services, "SGP", 2024), 70.0, "SGP services value-added share 2024"), "Sectoral-structure check separate from trade composition."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.72,
            disclosure="Prior expects support; high-tech share is an outcome pattern, not proof of one industrial policy instrument.",
            steelman="The high-tech export share partly reflects multinational supply-chain accounting and global electronics cycles. Digital adoption also followed global technology diffusion, so the result does not assign causal credit solely to Singapore's state strategy.",
            notes="Post-1990 legacy test pinned to WDI digital/export series.",
        ),
        Study(
            hid="uae_jebel_ali_free_zone_trade_fdi_1985_2024",
            topic="trade",
            claim=(
                "The UAE's Jebel Ali and free-zone strategy produced a highly open trade and investment "
                "platform by Gulf standards: trade intensity is high, exceeds the GCC peer median, FDI intensity "
                "has become material, and trade-freedom scores remain high."
            ),
            sample_countries=["ARE"] + GCC_PEERS,
            period=(1985, 2024),
            outcome_dim=["trade_liberalisation", "capital_flows"],
            policy_family=["trade_policy", "regulation", "tax_policy"],
            treatment_tags=["jebel_ali_free_zone_1985", "free_zone_foreign_ownership", "reexport_hub"],
            variables=[
                {"name": "trade_openness", "source": trade, "transformation": "annual_mean"},
                {"name": "fdi_inflows_share_gdp", "source": fdi, "transformation": "annual_mean"},
                {"name": "efw_trade_freedom", "source": trade_freedom, "transformation": "endpoint_level"},
            ],
            metrics=[
                metric("trade_openness_mean", "Trade/GDP averaged high after free-zone expansion", [trade], ">= 120% of GDP", "1990-2024", lambda: gt(mean_between(trade, "ARE", 1990, 2024), 120.0, "ARE trade/GDP mean"), "Gross openness measure."),
                metric("trade_openness_vs_gcc_2023", "Trade/GDP exceeded GCC peer median", [trade], ">= 1.5x peer median", "2023", lambda: gt(endpoint_vs_peer_median(trade, "ARE", GCC_PEERS, 2023), 1.5, "ARE trade/GDP / GCC median 2023"), "Peer comparison separates general Gulf oil-exporter trend."),
                metric("fdi_intensity_mature_endpoint", "FDI inflows reached material GDP share", [fdi], ">= 5% of GDP", "2024", lambda: gt(value_at(fdi, "ARE", 2024), 5.0, "ARE FDI/GDP 2024"), "External capital-flow channel separate from trade volume."),
                metric("trade_freedom_score", "EFW trade-freedom score remained high", [trade_freedom], ">= 8.0", "2023", lambda: gt(value_at(trade_freedom, "ARE", 2023), 8.0, "ARE EFW trade freedom 2023"), "Institutional trade-policy score independent from WDI trade volumes."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.70,
            disclosure="Prior expects support; the test does not separate geography, oil-financed infrastructure, and free-zone legal design.",
            steelman="The UAE's openness is partly re-export geography and hydrocarbon-financed infrastructure. Free zones may also segment the economy, with benefits concentrated in Dubai and foreign-owned enclaves rather than broad domestic productivity.",
            notes="GCC peer benchmark keeps this from being a generic oil-state claim.",
        ),
        Study(
            hid="uae_dubai_tourism_aviation_hub_2015_2019",
            topic="trade",
            claim=(
                "Dubai/UAE aviation, airport, and tourism policy achieved exceptional pre-COVID visitor-hub "
                "scale by Gulf standards, visible in absolute arrivals, arrivals per resident, and arrivals "
                "relative to GCC peers."
            ),
            sample_countries=["ARE"] + GCC_PEERS,
            period=(2015, 2019),
            outcome_dim=["trade_liberalisation", "capital_flows"],
            policy_family=["trade_policy", "industrial_policy"],
            treatment_tags=["emirates_airline_1985", "dubai_airport_hub", "tourism_strategy"],
            variables=[
                {"name": "tourist_arrivals", "source": arrivals, "transformation": "endpoint_level"},
                {"name": "population", "source": pop, "transformation": "denominator"},
            ],
            metrics=[
                metric("visitor_arrivals_2019", "International arrivals reached very large scale", [arrivals], ">= 20 million", "2019", lambda: gt(value_at(arrivals, "ARE", 2019), 20_000_000.0, "ARE tourist arrivals 2019"), "Absolute scale check."),
                metric("visitor_arrivals_per_capita_2019", "Arrivals exceeded resident population multiple times", [arrivals, pop], ">= 2.0 arrivals per resident", "2019", lambda: gt(arrivals_per_capita("ARE", 2019), 2.0, "ARE visitor arrivals per resident 2019"), "Scale-adjusted hub intensity."),
                metric("visitor_arrivals_vs_gcc_2019", "Arrivals exceeded GCC peer median", [arrivals], ">= 2.0x peer median", "2019", lambda: gt(endpoint_vs_peer_median(arrivals, "ARE", GCC_PEERS, 2019), 2.0, "ARE arrivals / GCC median 2019"), "GCC benchmark controls regional tourism trend."),
                metric("trade_openness_context_2019", "Tourism hub sat inside a highly open economy", [trade], ">= 150% of GDP", "2019", lambda: gt(value_at(trade, "ARE", 2019), 150.0, "ARE trade/GDP 2019"), "Open-economy context separate from arrivals."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.78,
            disclosure="Prior expects support; WDI UAE arrivals coverage starts only in 2015, so the test is pre-COVID endpoint evidence rather than a full 1985-2019 time series.",
            steelman="The visitor numbers reflect airport geography, migrant population, shopping/tourism branding, and regional instability rerouting demand. A supported result is hub-scale evidence, not a full welfare or productivity accounting.",
            notes="Uses 2019 pre-COVID endpoint because 2020 travel restrictions break the series.",
        ),
        Study(
            hid="uae_dubai_internet_city_digital_adoption_2000_2024",
            topic="growth",
            claim=(
                "Dubai Internet City and the UAE digital-state strategy were followed by near-universal internet "
                "adoption and a measurable high-tech export presence, even if the high-tech export share remains "
                "far below Singapore-style electronics hubs."
            ),
            sample_countries=["ARE"] + GCC_PEERS,
            period=(2000, 2024),
            outcome_dim=["industrial_capability", "productivity"],
            policy_family=["industrial_policy", "regulation", "trade_policy"],
            treatment_tags=["dubai_internet_city_1999", "tecom_clusters", "uae_digital_government"],
            variables=[
                {"name": "internet_users", "source": internet, "transformation": "endpoint_change"},
                {"name": "high_tech_exports_share", "source": hightech, "transformation": "endpoint_change"},
            ],
            metrics=[
                metric("internet_diffusion_gain", "Internet users share rose sharply", [internet], ">= 70pp increase", "2000-2024", lambda: gt(pp_change(internet, "ARE", 2000, 2024), 70.0, "ARE internet-users share change"), "Digital adoption trend."),
                metric("internet_users_2024", "Internet users reached near universal coverage", [internet], ">= 95%", "2024", lambda: gt(value_at(internet, "ARE", 2024), 95.0, "ARE internet users 2024"), "Endpoint adoption check."),
                metric("hightech_export_share_gain", "High-tech export share rose from early coverage", [hightech], ">= 4pp increase", "2008-2023", lambda: gt(pp_change(hightech, "ARE", 2008, 2023), 4.0, "ARE high-tech export share change"), "Export capability check separate from consumer adoption."),
                metric("hightech_export_share_2023", "High-tech exports reached visible but not dominant share", [hightech], ">= 8%", "2023", lambda: gt(value_at(hightech, "ARE", 2023), 8.0, "ARE high-tech exports share 2023"), "Endpoint technology-export check."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.66,
            disclosure="Prior expects partial-to-support: digital adoption is very strong, but high-tech export depth is modest.",
            steelman="Internet adoption is a global diffusion story and the UAE's tech clusters often host regional headquarters rather than deep domestic frontier R&D. High adoption should not be confused with broad indigenous technology production.",
            notes="Separates adoption from export capability to avoid overclaiming the Dubai Internet City model.",
        ),
        Study(
            hid="uae_oil_rent_diversification_services_1990_2024",
            topic="resource_rents",
            claim=(
                "The UAE diversification model reduced direct oil-rent dependence and expanded services, "
                "while still retaining hydrocarbon-export exposure. The claim is deliberately two-sided: "
                "support requires services and oil-rent metrics to improve, but fuel-export dependence remains a risk metric."
            ),
            sample_countries=["ARE"] + GCC_PEERS,
            period=(1990, 2024),
            outcome_dim=["energy", "trade_liberalisation", "capital_flows"],
            policy_family=["industrial_policy", "fiscal_policy", "trade_policy"],
            treatment_tags=["adia_diversification_1980s", "dubai_services_pivot", "abu_dhabi_sovereign_wealth"],
            variables=[
                {"name": "oil_rents_share_gdp", "source": oil_rents, "transformation": "endpoint_change"},
                {"name": "services_value_added_share", "source": services, "transformation": "endpoint_change"},
                {"name": "fuel_exports_share", "source": fuel_exports, "transformation": "endpoint_change"},
            ],
            metrics=[
                metric("oil_rents_share_decline", "Oil rents/GDP declined materially", [oil_rents], ">= 15pp decline", "1990-2024", lambda: gt(decrease(oil_rents, "ARE", 1990, 2024), 15.0, "ARE oil rents/GDP decline"), "Rent-share check captures fiscal/resource exposure."),
                metric("services_va_share_gain", "Services value-added share rose materially", [services], ">= 10pp increase", "1990-2024", lambda: gt(pp_change(services, "ARE", 1990, 2024), 10.0, "ARE services VA share change"), "Sectoral-structure check separate from rents."),
                metric("fuel_exports_share_decline_post_2000", "Fuel-export share declined after the 2000 oil-cycle endpoint", [fuel_exports], ">= 15pp decline", "2000-2023", lambda: gt(decrease(fuel_exports, "ARE", 2000, 2023), 15.0, "ARE fuel exports share decline 2000-2023"), "Export-composition risk metric."),
                metric("trade_openness_mean", "Diversification occurred inside a highly open economy", [trade], ">= 140% of GDP mean", "1990-2024", lambda: gt(mean_between(trade, "ARE", 1990, 2024), 140.0, "ARE trade/GDP mean"), "Open-economy channel separate from resource shares."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.64,
            disclosure="Prior expects support with caveats; the fuel-export metric is included to stop the model from overclaiming non-oil transformation.",
            steelman="The UAE remains highly hydrocarbon-exposed through fiscal revenue, exports, and Abu Dhabi wealth. Dubai's services success may coexist with national oil dependence, so a supported result is diversification evidence, not proof of post-oil independence.",
            notes="Uses 2000-2023 for fuel-export trend because early UAE fuel-export series has sparse/noisy 1980s-1990s values.",
        ),
        Study(
            hid="uae_freezone_institutional_quality_wgi_1996_2024",
            topic="institutional_quality",
            claim=(
                "The UAE's free-zone, commercial-court, and state-capacity model is visible in relatively high "
                "government effectiveness, regulatory quality, rule-of-law, and market-rule scores compared with "
                "many resource-rent peers."
            ),
            sample_countries=["ARE"] + GCC_PEERS,
            period=(1996, 2024),
            outcome_dim=["institutional_quality", "capital_flows"],
            policy_family=["institutional_reform", "regulation", "trade_policy"],
            treatment_tags=["difc_2004", "adgm_common_law", "freezone_legal_architecture"],
            variables=[
                {"name": "government_effectiveness", "source": ge, "transformation": "annual_mean"},
                {"name": "regulatory_quality", "source": rq, "transformation": "annual_mean"},
                {"name": "rule_of_law", "source": rl, "transformation": "annual_mean"},
                {"name": "efw_summary_index", "source": efw, "transformation": "endpoint_level"},
            ],
            metrics=[
                metric("government_effectiveness_mean", "Government effectiveness averaged high", [ge], ">= 0.90", "1996-2024", lambda: gt(mean_between(ge, "ARE", 1996, 2024), 0.90, "ARE WGI GE mean"), "Administrative capacity pillar."),
                metric("regulatory_quality_mean", "Regulatory quality averaged high", [rq], ">= 0.75", "1996-2024", lambda: gt(mean_between(rq, "ARE", 1996, 2024), 0.75, "ARE WGI RQ mean"), "Regulatory quality pillar separate from GE."),
                metric("rule_of_law_mean", "Rule of law averaged above moderate threshold", [rl], ">= 0.60", "1996-2024", lambda: gt(mean_between(rl, "ARE", 1996, 2024), 0.60, "ARE WGI RL mean"), "Legal-quality pillar."),
                metric("efw_summary_2023", "Market-rule composite reached high score", [efw], ">= 7.0", "2023", lambda: gt(value_at(efw, "ARE", 2023), 7.0, "ARE EFW summary 2023"), "External institutional composite independent from WGI."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.68,
            disclosure="Prior expects support but this is a narrow business-institution quality claim, not a democracy or civil-liberties score.",
            steelman="Free-zone legal quality can coexist with limited political rights, migrant-labour constraints, and dual-track institutions. WGI business-facing strength should not be treated as broad liberal institutionalism.",
            notes="Institutional-quality case deliberately separates administrative/regulatory strength from political-system evaluation.",
        ),
        Study(
            hid="uae_female_labour_force_participation_1990_2024",
            topic="labour",
            claim=(
                "The UAE's education, migration, and labour-market reforms were followed by a large rise in "
                "female labour-force participation, placing the UAE above the GCC peer median by the 2020s."
            ),
            sample_countries=["ARE"] + GCC_PEERS,
            period=(1990, 2024),
            outcome_dim=["employment_labour", "demographics_migration"],
            policy_family=["labour_market", "regulation"],
            treatment_tags=["uae_women_workforce_strategy", "golden_visa_2019", "labour_reforms"],
            variables=[
                {"name": "female_lfp", "source": female_lfp, "transformation": "endpoint_change"},
            ],
            metrics=[
                metric("female_lfp_gain", "Female labour-force participation rose strongly", [female_lfp], ">= 20pp increase", "1990-2024", lambda: gt(pp_change(female_lfp, "ARE", 1990, 2024), 20.0, "ARE female LFP change"), "Domestic trend check."),
                metric("female_lfp_2024", "Female labour-force participation exceeded half of working-age women", [female_lfp], ">= 50%", "2024", lambda: gt(value_at(female_lfp, "ARE", 2024), 50.0, "ARE female LFP 2024"), "Endpoint level check."),
                metric("female_lfp_peer_gap_2024", "Female LFP exceeded GCC peer median", [female_lfp], ">= 8pp above peer median", "2024", lambda: gt(endpoint_minus_peer_median(female_lfp, "ARE", GCC_PEERS, 2024), 8.0, "ARE female LFP minus GCC median"), "GCC peer benchmark."),
                metric("female_lfp_peer_ratio_2024", "Female LFP ratio exceeded GCC peer median", [female_lfp], ">= 1.15x peer median", "2024", lambda: gt(endpoint_vs_peer_median(female_lfp, "ARE", GCC_PEERS, 2024), 1.15, "ARE female LFP / GCC median"), "Scale-normalized peer benchmark."),
            ],
            support_threshold=3,
            refute_threshold=1,
            prior=0.70,
            disclosure="Prior expects support; WDI LFP does not separate Emirati citizens from expatriate women, so interpretation must stay population-level.",
            steelman="UAE female LFP can be driven by expatriate composition, public-sector professionalisation, and measurement changes. It should not be read as complete gender equality or as proof that all legal constraints disappeared.",
            notes="Population-level labour-force outcome; citizen/expatriate split remains a data need.",
        ),
    ]


def hypothesis_doc(study: Study) -> dict:
    return {
        "hypothesis_id": study.hid,
        "version": 1,
        "status": study.status,
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
                "metric_id": m.metric_id,
                "description": m.description,
                "threshold": m.threshold,
                "window": m.window,
                "source": "; ".join(m.sources),
                "direction": m.direction,
                "independence_justification": m.independence_justification,
            }
            for m in study.metrics
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
            "notes": "Custom Singapore/UAE case checklist using local WDI, WGI, and Fraser EFW vintages.",
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if at least {study.support_threshold} of {len(study.metrics)} "
                f"pre-registered metrics meet their thresholds. REFUTED if at most "
                f"{study.refute_threshold} metrics meet after available data are evaluated. "
                "Otherwise PARTIAL or INCONCLUSIVE_DATA_PENDING."
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
    rows: list[dict] = []
    met = 0
    pending = 0
    for m in study.metrics:
        observed, ok, note = m.evaluator()
        if ok is True:
            status = "MET"
            met += 1
        elif ok is False:
            status = "NOT_MET"
        else:
            status = "PENDING_DATA"
            pending += 1
        rows.append({
            "metric_id": m.metric_id,
            "description": m.description,
            "sources": m.sources,
            "window": m.window,
            "threshold": m.threshold,
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
    for m in study.metrics:
        for src in m.sources:
            pub, series = split_source(src)
            p = latest_vintage(pub, series)
            if p is not None:
                paths[src] = p
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
        "template": "multi_metric_checklist",
        "case_wave": "singapore_uae_case_wave_2026_05_04",
        "metrics": rows,
        "support_threshold": study.support_threshold,
        "refute_threshold": study.refute_threshold,
        "vintages": {src: str(p.relative_to(ROOT)) for src, p in paths.items()},
        "sha256": {src: sha256(p) for src, p in paths.items()},
        "runner": "scripts/generate_singapore_uae_case_wave.py",
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    (run_dir / "manifest.yaml").write_text(yaml.dump({
        "hypothesis_id": study.hid,
        "status": verdict,
        "reason": reason,
        "vintages": {src: str(p.relative_to(ROOT)) for src, p in paths.items()},
    }, Dumper=NoAliasDumper, sort_keys=False))
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
    for row in rows:
        observed = "pending" if row["observed"] is None else f"{row['observed']:.3f}"
        note = str(row["note"]).replace("|", "/")
        lines.append(f"| {row['metric_id']} | {observed} | {row['threshold']} | {row['status']} | {note} |")
    lines += [
        "",
        "## Interpretation",
        "This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.",
        "",
        "## Sources",
    ]
    for src, path in paths.items():
        lines.append(f"- `{src}` -> `{path.relative_to(ROOT)}`")
    lines += ["", "## Steelman", f"See `hypotheses/steelman/{study.hid}.md`.", ""]
    (run_dir / "result_card.md").write_text("\n".join(lines))
    (run_dir / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        '"""Regenerate the Singapore/UAE case-study checklist wave."""\n'
        "from pathlib import Path\n"
        "import runpy\n\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "runpy.run_path(str(root / 'scripts' / 'generate_singapore_uae_case_wave.py'), run_name='__main__')\n"
    )
    print(f"{study.hid}: {verdict} - {reason}")


def write_policy(doc: dict) -> None:
    text = "# yaml-language-server: $schema=../schemas/policy.schema.json\n"
    text += yaml.dump(doc, Dumper=NoAliasDumper, sort_keys=False, width=92)
    (POLICIES / f"{doc['policy_id']}.yaml").write_text(text)


def ensure_policy_links(policy_id: str, hypothesis_ids: list[str]) -> None:
    path = POLICIES / f"{policy_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text()
    missing = [hid for hid in hypothesis_ids if f"- {hid}" not in text]
    if not missing:
        return
    lines = text.splitlines()
    insert_lines = ["linked_hypotheses:"] + [f"- {hid}" for hid in missing]

    for i, line in enumerate(lines):
        if line.startswith("linked_hypotheses:"):
            j = i + 1
            while j < len(lines) and (lines[j].startswith("-") or lines[j].startswith("  ")):
                j += 1
            lines[j:j] = [f"- {hid}" for hid in missing]
            path.write_text("\n".join(lines) + "\n")
            return
        if line.startswith("linked_hypotheses_inferred:"):
            lines[i:i] = insert_lines
            path.write_text("\n".join(lines) + "\n")
            return
    lines.extend(["", *insert_lines])
    path.write_text("\n".join(lines) + "\n")


def write_policies() -> None:
    new_policies = [
        {
            "policy_id": "singapore_changi_airport_opening_1981",
            "status": "candidate",
            "title": "Singapore Changi Airport opening and air-hub strategy, 1981",
            "countries": ["SGP"],
            "timeframe": {"start": 1981, "end": 2019},
            "description": "Singapore opened Changi Airport in 1981 and paired airport capacity, Singapore Airlines, tourism promotion, and logistics openness to reinforce a high-connectivity open-city model.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "strong", "intended": True, "rationale": "Airport hub strategy lowered services-trade and visitor-friction costs."},
                {"axis": "fiscal.sectoral_subsidy", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "State-backed aviation and airport infrastructure supported selected services sectors."},
            ],
            "linked_hypotheses": ["singapore_lky_changi_air_hub_tourism_1981_2019"],
            "notes": "Direct link to the second-wave Singapore air-hub test.",
        },
        {
            "policy_id": "singapore_mas_financial_hub_strategy_1971_1990",
            "status": "candidate",
            "title": "Singapore MAS and Asian-dollar financial hub strategy, 1971-1990",
            "countries": ["SGP"],
            "timeframe": {"start": 1971, "end": 1990},
            "description": "Singapore created the Monetary Authority of Singapore in 1971 and deepened Asian-dollar, banking, and capital-market infrastructure while maintaining tight prudential supervision and exchange-rate discipline.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "regulatory.financial_deregulation", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Financial hub strategy opened international banking and capital-market channels."},
                {"axis": "monetary.central_bank_independence", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "MAS institutionalised technocratic monetary and financial supervision."},
            ],
            "linked_hypotheses": ["singapore_lky_financial_deepening_market_hub_1970_2020"],
            "notes": "Financial deepening is scored as a pattern, not a deregulation-only welfare claim.",
        },
        {
            "policy_id": "singapore_national_computerisation_plan_1980",
            "status": "candidate",
            "title": "Singapore National Computerisation Plan, 1980",
            "countries": ["SGP"],
            "timeframe": {"start": 1980, "end": 2024},
            "description": "Singapore's 1980 National Computerisation Plan and later information-technology institutions built computer literacy, public-sector digitisation, and electronics/export capabilities on top of the LKY-era skills and EDB base.",
            "coalition_label_at_enactment": "People's Action Party government under Lee Kuan Yew",
            "axes_moved": [
                {"axis": "fiscal.sectoral_subsidy", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Public investment and agency coordination promoted the ICT sector."},
                {"axis": "regulatory.product_market_competition", "direction": "+", "magnitude": "weak", "intended": True, "rationale": "Digital adoption and ICT capability lowered business process frictions."},
            ],
            "linked_hypotheses": ["singapore_lky_high_tech_export_digital_upgrade_1990_2024"],
            "notes": "Legacy test: WDI digital/export outcomes are post-1990 but rooted in the earlier computerisation strategy.",
        },
        {
            "policy_id": "ae_gender_labour_market_reforms_2006_2024",
            "status": "candidate",
            "title": "UAE female workforce and labour-market reforms, 2006-2024",
            "countries": ["ARE"],
            "timeframe": {"start": 2006, "end": 2024},
            "description": "UAE reforms expanded women's education, public-sector participation, anti-discrimination rules, flexible visas, and professional labour-market access, alongside a large expatriate workforce model.",
            "coalition_label_at_enactment": "UAE federal and emirate-level governments",
            "axes_moved": [
                {"axis": "regulatory.labour_market_flexibility", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Visa and workplace reforms increased labour-market participation options."},
                {"axis": "regulatory.immigration_openness", "direction": "+", "magnitude": "moderate", "intended": True, "rationale": "Expatriate and long-term visa channels shape the aggregate workforce outcome."},
            ],
            "linked_hypotheses": ["uae_female_labour_force_participation_1990_2024"],
            "notes": "Population-level WDI outcome cannot separate citizens from expatriates.",
        },
    ]
    for doc in new_policies:
        write_policy(doc)

    # Add direct links to existing UAE/Singapore policy cards without reformatting them.
    ensure_policy_links("singapore_medisave_1984", ["singapore_lky_public_health_outcomes_1965_1990"])
    ensure_policy_links("singapore_medishield_1990", ["singapore_lky_public_health_outcomes_1965_1990"])
    ensure_policy_links("ae_jebel_ali_expansion_1985_1995", ["uae_jebel_ali_free_zone_trade_fdi_1985_2024"])
    ensure_policy_links("ae_jebel_ali_free_zone_1979", ["uae_jebel_ali_free_zone_trade_fdi_1985_2024", "uae_oil_rent_diversification_services_1990_2024"])
    ensure_policy_links("ae_emirates_airline_launch_1985", ["uae_dubai_tourism_aviation_hub_2015_2019"])
    ensure_policy_links("ae_emirates_airline_expansion_1995_2004", ["uae_dubai_tourism_aviation_hub_2015_2019"])
    ensure_policy_links("ae_dubai_internet_city_1999", ["uae_dubai_internet_city_digital_adoption_2000_2024"])
    ensure_policy_links("ae_adia_diversification_1980s", ["uae_oil_rent_diversification_services_1990_2024"])
    ensure_policy_links("ae_difc_launch_2004", ["uae_freezone_institutional_quality_wgi_1996_2024"])
    ensure_policy_links("ae_difc_establishment_law_2004", ["uae_freezone_institutional_quality_wgi_1996_2024"])


def main() -> None:
    for study in studies():
        write_study(study)
    write_policies()


if __name__ == "__main__":
    main()
