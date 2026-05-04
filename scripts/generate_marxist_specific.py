#!/usr/bin/env python3
"""Generate specific Marxist/Marxian/Marxist-Leninist hypotheses."""

import yaml
import random
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"

random.seed(123)

def write_hypothesis(hid, spec, topic):
    out_dir = HYP_ROOT / topic
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{hid}.yaml", "w") as f:
        yaml.dump(spec, f, sort_keys=False, allow_unicode=True)

def clean_hid(prefix):
    return prefix.replace(" ", "_").replace(",", "").replace(".", "").replace("'", "").replace("-", "_").replace("(", "").replace(")", "").replace("/", "_")[:80]

# Specific Marxist hypotheses - historically grounded and theoretically specific
templates = []

# ===== MARXIAN THEORETICAL CLAIMS =====
marxian = "marxian"

# Tendency of the rate of profit to fall
# Marx claimed rising organic composition of capital → falling profit rate
# Test: capital-output ratio vs profit share over time
templates.append((
    "The organic composition of capital (capital stock to output ratio) rises over time in capitalist economies, and this rise is associated with a declining profit share, consistent with Marx's law of the tendential fall in the rate of profit.",
    marxian, "growth", {
        "title": "Rising organic composition of capital reduces profit share",
        "description": "Panel test of capital-output ratio vs profit share.",
        "prior_confidence": 0.45,
        "variables": {
            "outcome": [{"name": "profit_share_proxy", "source": "world_bank_wdi:SL.GDP.PCAP.EM.KD"}],
            "treatment": [{"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if investment/GDP does not have a negative coefficient on profit share at p < 0.05."},
    }
))

# Reserve army of labour - unemployment disciplines wages
# Marx: capital maintains a reserve army to suppress wages
# Test: unemployment vs wage share
templates.append((
    "Higher unemployment is associated with a lower labour share of GDP, consistent with the Marxian 'reserve army of labour' mechanism by which capital uses unemployment to discipline wage demands.",
    marxian, "labour", {
        "title": "Unemployment suppresses labour share",
        "description": "Panel test of unemployment vs labour share proxy.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "labour_share_proxy", "source": "world_bank_wdi:SL.GDP.PCAP.EM.KD"}],
            "treatment": [{"name": "unemployment", "source": "world_bank_wdi:SL.UEM.TOTL.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if unemployment does not have a negative coefficient on labour share at p < 0.05."},
    }
))

# Imperialism - core-periphery exploitation
# Lenin/Hobson: imperialist powers extract surplus from colonies/periphery
# Test: colonial history → lower growth in former colonies
templates.append((
    "Former European colonies experienced lower GDP per capita growth during 1960-2000 than non-colonised countries at similar initial income levels, consistent with the Marxist-Leninist theory of imperialist extraction retarding peripheral development.",
    "marxist_leninist", "growth", {
        "title": "Colonial history reduced post-independence growth",
        "description": "Panel test comparing former colonies vs non-colonies.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"}],
            "controls": [
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
                {"name": "population_growth", "source": "world_bank_wdi:SP.POP.GROW"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if colonial status does not show a negative coefficient on growth at p < 0.05."},
    }
))

# Exploitation of labour - surplus value extraction
# Marx: profit derives from unpaid labour time
# Test: labour productivity growth vs real wage growth divergence
templates.append((
    "Labour productivity growth systematically outpaces real wage growth in capitalist economies, with the gap widening over time, consistent with Marx's theory of rising surplus value extraction.",
    marxian, "labour", {
        "title": "Productivity-wage gap widens over time",
        "description": "Panel test of productivity vs wage divergence.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "labour_productivity_proxy", "source": "world_bank_wdi:SL.GDP.PCAP.EM.KD"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if labour productivity does not outpace wage growth (positive divergence) at p < 0.05."},
    }
))

# Monopoly/oligopoly - capital concentration
# Marx: capital tends to concentrate, reducing competition
# Test: market concentration proxy (large firm share) vs markups/profits
templates.append((
    "Countries with higher industrial concentration (manufacturing value added as share of GDP) exhibit higher profit shares and lower wage shares, consistent with Marxian monopoly-capital theory.",
    marxian, "distribution", {
        "title": "Industrial concentration raises profit share",
        "description": "Panel test of industrial concentration vs profit share.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "industry_share", "source": "world_bank_wdi:NV.IND.TOTL.ZS"}],
            "treatment": [{"name": "manufacturing_share", "source": "world_bank_wdi:NV.IND.MANF.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if manufacturing share does not have a positive coefficient on industry share at p < 0.05."},
    }
))

# Crisis theory - overproduction/underconsumption
# Marx: capitalist crises stem from overproduction relative to purchasing power
# Test: inequality (Gini) → crisis proxy (growth volatility)
templates.append((
    "Higher income inequality (Gini coefficient) increases the frequency and severity of economic crises (measured by GDP growth volatility), consistent with Marxian underconsumption/overproduction crisis theory.",
    marxian, "distribution", {
        "title": "Inequality raises crisis frequency",
        "description": "Panel test of Gini vs growth volatility.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_volatility_proxy", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "gini", "source": "world_bank_wdi:SI.POV.GINI"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if Gini does not have a positive coefficient on growth volatility at p < 0.05."},
    }
))

# Financialization - Minsky/Marx
# Financial sector growth crowds out productive investment
templates.append((
    "Rapid growth of the financial sector (private credit to GDP) reduces real fixed capital formation as a share of GDP, consistent with the Marxian financialization thesis that finance capital crowds out productive industrial capital.",
    marxian, "monetary", {
        "title": "Financialization crowds out real investment",
        "description": "Panel test of credit growth vs investment share.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "treatment": [{"name": "private_credit_gdp", "source": "world_bank_wdi:GFDD.DI.14"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if private credit/GDP does not have a negative coefficient on investment/GDP at p < 0.05."},
    }
))

# ===== MARXIST-LENINIST HISTORICAL CLAIMS =====
ml = "marxist_leninist"

# Soviet collectivization vs peasant agriculture
templates.append((
    "Soviet agricultural collectivisation (1928-1940) achieved faster growth in agricultural output than the preceding peasant-agriculture period (1921-1928), supporting the Marxist-Leninist claim that socialist collectivisation outperforms smallholder farming.",
    ml, "growth", {
        "title": "Soviet collectivization outperformed peasant agriculture",
        "description": "Time-series comparison of Soviet agricultural output pre and post collectivization.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_growth", "source": "world_bank_wdi:NY.GDP.MKTP.KD.ZG"}],
            "treatment": [{"name": "collectivisation_dummy", "source": "constructed: 1 for USSR 1928-1940, 0 for 1921-1928"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if collectivisation period does not show higher agricultural output growth at p < 0.05."},
    }
))

# Chinese Great Leap Forward
templates.append((
    "China's Great Leap Forward (1958-1962) achieved rapid industrialisation despite the famine, with industrial output growth exceeding that of comparable developing capitalist economies during the same period, supporting the Marxist-Leninist case for forced-pace socialist industrialisation.",
    ml, "growth", {
        "title": "Great Leap Forward industrial output exceeded capitalist peers",
        "description": "Comparison of Chinese industrial growth vs comparable countries 1958-1962.",
        "prior_confidence": 0.4,
        "variables": {
            "outcome": [{"name": "industry_growth", "source": "world_bank_wdi:NV.IND.TOTL.KD.ZG"}],
            "treatment": [{"name": "great_leap_dummy", "source": "constructed: 1 for CHN 1958-1962"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if Great Leap Forward period does not show higher industrial growth than comparable countries at p < 0.05."},
    }
))

# Cuban healthcare vs capitalist Caribbean
templates.append((
    "Cuba achieved lower infant mortality and higher life expectancy than comparable Caribbean and Central American market economies by 1990, demonstrating the Marxist-Leninist claim that socialist public-health systems outperform market-based healthcare in poor countries.",
    ml, "healthcare", {
        "title": "Cuban health outcomes exceeded capitalist Caribbean peers",
        "description": "Panel comparison of Cuban health outcomes vs Caribbean peers.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "life_expectancy", "source": "world_bank_wdi:SP.DYN.LE00.IN"}],
            "treatment": [{"name": "cuba_dummy", "source": "constructed: 1 for CUB"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "health_exp_gdp", "source": "world_bank_wdi:SH.XPD.CHEX.GD.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if Cuba does not show significantly better health outcomes than comparable Caribbean countries at p < 0.05."},
    }
))

# State ownership vs private - SOE productivity
templates.append((
    "Countries with higher state ownership of industry (proxied by public investment share) achieved faster industrial productivity growth than countries with lower state ownership during 1960-1980, supporting the Marxist-Leninist claim that public ownership accelerates industrialisation.",
    ml, "growth", {
        "title": "State ownership raised industrial productivity 1960-1980",
        "description": "Panel test of public investment vs industrial growth.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "industry_growth", "source": "world_bank_wdi:NV.IND.TOTL.KD.ZG"}],
            "treatment": [{"name": "public_investment", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if public investment does not have a positive coefficient on industrial growth at p < 0.05."},
    }
))

# Vanguard party - one-party states and development
templates.append((
    "One-party socialist states achieved faster GDP per capita growth during 1960-1989 than multi-party democracies at similar initial income levels, supporting the Marxist-Leninist claim that a vanguard party enables more effective development planning.",
    ml, "growth", {
        "title": "One-party socialist states grew faster 1960-1989",
        "description": "Panel comparison of socialist vs democratic countries.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "socialist_dummy", "source": "constructed: 1 for socialist bloc countries"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if socialist dummy does not have a positive coefficient on growth at p < 0.05."},
    }
))

# ===== DEMOCRATIC SOCIALIST SPECIFIC =====
demsoc = "democratic_socialist"

# Nordic model - specific welfare programs
templates.append((
    "Universal childcare provision (proxied by female labour force participation) raises female employment rates without reducing fertility rates, supporting the democratic-socialist claim that socialised reproductive labour expands rather than contracts demographic reproduction.",
    demsoc, "labour", {
        "title": "Universal childcare raises female employment without fertility loss",
        "description": "Panel test of female labour force participation vs fertility.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "female_labor_force", "source": "world_bank_wdi:SL.TLF.CACT.FE.ZS"}],
            "treatment": [{"name": "fertility_rate", "source": "world_bank_wdi:SP.DYN.TFRT.IN"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "education_exp_gdp", "source": "world_bank_wdi:SE.XPD.TOTL.GD.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if female labour force participation does not have a positive coefficient on fertility at p < 0.05."},
    }
))

# Public housing
templates.append((
    "Countries with higher public housing investment (proxied by government consumption) achieve lower homelessness and better housing affordability than market-reliant countries at similar income levels, supporting the democratic-socialist case for decommodified housing.",
    demsoc, "housing", {
        "title": "Public housing investment improves affordability",
        "description": "Panel test of government consumption vs housing outcomes proxy.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "urban_population", "source": "world_bank_wdi:SP.URB.TOTL.IN.ZS"}],
            "treatment": [{"name": "gov_consumption_gdp", "source": "world_bank_wdi:NE.CON.GOVT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "population_growth", "source": "world_bank_wdi:SP.POP.GROW"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government consumption does not have a positive coefficient on urban population at p < 0.05."},
    }
))

# Co-determination / worker representation
templates.append((
    "Countries with stronger worker representation (proxied by labour force participation) achieve lower strike rates and higher industrial peace without productivity loss, supporting the democratic-socialist claim that industrial democracy harmonises labour-capital relations.",
    demsoc, "labour", {
        "title": "Worker representation raises industrial peace",
        "description": "Panel test of labour participation vs industrial stability proxy.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "labour_force_participation", "source": "world_bank_wdi:SL.TLF.CACT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if labour force participation does not have a positive coefficient on growth at p < 0.05."},
    }
))

# ===== MARKET SOCIALIST SPECIFIC =====
ms = "market_socialist"

# Worker cooperatives - Mondragon
templates.append((
    "Worker-cooperative dominated sectors (proxied by self-employment share) achieve higher labour productivity growth than capitalist-firm dominated sectors, supporting the market-socialist claim that worker ownership enhances productive efficiency.",
    ms, "growth", {
        "title": "Worker cooperatives raise labour productivity",
        "description": "Panel test of self-employment vs productivity growth.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "self_employment", "source": "world_bank_wdi:SL.EMP.SELF.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if self-employment does not have a positive coefficient on growth at p < 0.05."},
    }
))

# Yugoslav self-management
templates.append((
    "Yugoslavia's worker-self-management system (1950-1990) achieved higher GDP per capita growth than neighbouring capitalist economies at similar development levels, supporting the market-socialist claim that social ownership with market coordination outperforms both capitalism and central planning.",
    ms, "growth", {
        "title": "Yugoslav self-management outperformed capitalist neighbours",
        "description": "Panel comparison of Yugoslavia vs neighbours.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "yugoslav_dummy", "source": "constructed: 1 for YUG"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if Yugoslavia does not show higher growth than neighbours at p < 0.05."},
    }
))

# ===== POST-KEYNESIAN SPECIFIC =====
pk = "post_keynesian"

# Fiscal multiplier > 1 in recessions
templates.append((
    "Government expenditure multipliers exceed 1.0 during periods of high unemployment (above the natural rate), supporting the Post-Keynesian claim that fiscal expansion is especially effective when resources are underutilised.",
    pk, "fiscal", {
        "title": "Fiscal multipliers exceed 1 in high-unemployment periods",
        "description": "Panel test of government spending vs growth in high unemployment regimes.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "unemployment", "source": "world_bank_wdi:SL.UEM.TOTL.ZS"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government expenditure does not have a positive coefficient on growth at p < 0.05, especially in high-unemployment subsamples."},
    }
))

# Wage-led vs profit-led growth
templates.append((
    "A higher wage share of GDP raises GDP per capita growth in most OECD economies, supporting the Post-Keynesian claim that wage-led demand regimes dominate profit-led regimes.",
    pk, "distribution", {
        "title": "Higher wage share raises GDP growth",
        "description": "Panel test of wage share proxy vs growth.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "labour_share_proxy", "source": "world_bank_wdi:SL.GDP.PCAP.EM.KD"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if wage share proxy does not have a positive coefficient on growth at p < 0.05."},
    }
))

# Minsky financial instability
templates.append((
    "Rapid credit growth (private credit to GDP) increases the probability of subsequent banking crises and output collapses, supporting the Post-Keynesian/Minskyan financial instability hypothesis.",
    pk, "monetary", {
        "title": "Credit growth predicts financial crises",
        "description": "Panel test of credit growth vs subsequent crisis proxy.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "gdp_volatility", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "credit_growth", "source": "world_bank_wdi:GFDD.DI.14"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if credit growth does not have a positive coefficient on subsequent growth volatility at p < 0.05."},
    }
))

# ===== MMT SPECIFIC =====
mmt = "mmt"

# Sovereign currency issuer - no default risk
templates.append((
    "Countries with sovereign currency issuance (not pegged, not dollarised) experience lower sovereign bond spreads and greater fiscal space than countries with fixed exchange rates or currency boards, supporting the MMT claim that monetary sovereignty expands policy options.",
    mmt, "monetary", {
        "title": "Monetary sovereignty reduces bond spreads",
        "description": "Panel comparison of sovereign issuers vs pegged currencies.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "lending_rate", "source": "world_bank_wdi:FR.INR.DPST"}],
            "treatment": [{"name": "monetary_sovereignty", "source": "constructed: 1 for floating currencies"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "inflation", "source": "world_bank_wdi:FP.CPI.TOTL.ZG"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if monetary sovereignty does not have a negative coefficient on lending rates at p < 0.05."},
    }
))

# Job guarantee - public employment reduces unemployment without inflation
templates.append((
    "Higher public-sector employment as a share of total employment reduces the unemployment rate without raising consumer price inflation, supporting the MMT claim that a job guarantee can achieve full employment without inflationary pressure.",
    mmt, "labour", {
        "title": "Public employment reduces unemployment without inflation",
        "description": "Panel test of public employment vs unemployment and inflation.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "unemployment", "source": "world_bank_wdi:SL.UEM.TOTL.ZS"}],
            "treatment": [{"name": "gov_consumption_gdp", "source": "world_bank_wdi:NE.CON.GOVT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "inflation", "source": "world_bank_wdi:FP.CPI.TOTL.ZG"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government consumption does not have a negative coefficient on unemployment at p < 0.05, or if it raises inflation at p < 0.05."},
    }
))

# Deficits don't crowd out private investment
templates.append((
    "Higher fiscal deficits (lower fiscal balance) do not reduce private gross fixed capital formation as a share of GDP, supporting the MMT claim that government spending does not crowd out private investment in sovereign currency issuers.",
    mmt, "fiscal", {
        "title": "Fiscal deficits do not crowd out private investment",
        "description": "Panel test of fiscal balance vs private investment.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "private_investment", "source": "world_bank_wdi:NE.GDI.FPRV.ZS"}],
            "treatment": [{"name": "fiscal_balance", "source": "world_bank_wdi:GC.NLD.TOTL.GD.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "interest_rate", "source": "world_bank_wdi:FR.INR.RINR"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if fiscal balance has a positive coefficient on private investment at p < 0.05 (i.e., deficits reduce investment)."},
    }
))

# ===== DEGROWTH SPECIFIC =====
deg = "degrowth"

# GDP growth doesn't improve life satisfaction above threshold
templates.append((
    "Beyond a moderate GDP per capita threshold (approximately $20,000 PPP), additional GDP growth does not reduce mortality rates or improve health outcomes, supporting the degrowth claim that growth ceases to deliver wellbeing improvements at high income levels.",
    deg, "healthcare", {
        "title": "GDP growth ceases to improve health above $20k threshold",
        "description": "Panel test of GDP growth vs health outcomes in rich countries.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "life_expectancy", "source": "world_bank_wdi:SP.DYN.LE00.IN"}],
            "treatment": [{"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.PP.KD"}],
            "controls": [
                {"name": "health_exp_gdp", "source": "world_bank_wdi:SH.XPD.CHEX.GD.ZS"},
                {"name": "education_exp_gdp", "source": "world_bank_wdi:SE.XPD.TOTL.GD.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if GDP per capita has a positive coefficient on life expectancy at p < 0.05 for countries above $20,000 PPP."},
    }
))

# Reduced work hours don't reduce output proportionally
templates.append((
    "Countries with shorter average working hours achieve higher labour productivity per hour, such that reduced working time does not reduce output per worker proportionally, supporting the degrowth claim that work-time reduction is compatible with maintaining living standards.",
    deg, "labour", {
        "title": "Shorter hours raise hourly productivity",
        "description": "Panel test of work hours proxy vs hourly productivity.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "labour_productivity", "source": "world_bank_wdi:SL.GDP.PCAP.EM.KD"}],
            "treatment": [{"name": "labour_force_participation", "source": "world_bank_wdi:SL.TLF.CACT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "education_exp_gdp", "source": "world_bank_wdi:SE.XPD.TOTL.GD.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if labour force participation does not have a positive coefficient on productivity at p < 0.05."},
    }
))

# ===== ECO-SOCIALIST SPECIFIC =====
eco = "eco_socialist"

# Fossil fuel nationalization for green transition
templates.append((
    "Countries that nationalised fossil-fuel industries achieved faster reductions in CO2 intensity (CO2 per unit of GDP) than countries that left extraction to private multinational corporations, supporting the eco-socialist claim that public ownership enables faster decarbonisation.",
    eco, "energy", {
        "title": "Nationalised fossil sectors decarbonised faster",
        "description": "Panel comparison of public vs private fossil sectors.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "energy_intensity", "source": "world_bank_wdi:EG.USE.PCAP.KG.OE"}],
            "treatment": [{"name": "nationalisation_dummy", "source": "constructed: 1 for countries with nationalised oil/gas"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "industry_share", "source": "world_bank_wdi:NV.IND.TOTL.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if nationalised fossil sectors do not show lower energy intensity at p < 0.05."},
    }
))

# Public transit investment
templates.append((
    "Higher public expenditure on transport infrastructure (proxied by government expenditure) reduces per-capita energy consumption and raises public transit mode share, supporting the eco-socialist claim that public transit investment is essential for sustainable mobility.",
    eco, "energy", {
        "title": "Public transit investment reduces energy use",
        "description": "Panel test of government transport spending vs energy use.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "energy_use_pc", "source": "world_bank_wdi:EG.USE.PCAP.KG.OE"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "urban_population", "source": "world_bank_wdi:SP.URB.TOTL.IN.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government expenditure does not have a negative coefficient on energy use at p < 0.05."},
    }
))

# Now generate multiple variants for each school by combining variables
# Generate ~100 more using systematic combinations

# Additional outcomes and treatments for mass generation
additional_outcomes = [
    ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "GDP per capita growth"),
    ("life_expectancy", "world_bank_wdi:SP.DYN.LE00.IN", "life expectancy"),
    ("infant_mortality", "world_bank_wdi:SP.DYN.IMRT.IN", "infant mortality"),
    ("poverty_headcount", "world_bank_wdi:SI.POV.DDAY", "extreme poverty"),
    ("under5_mortality", "world_bank_wdi:SH.DYN.MORT", "under-5 mortality"),
    ("primary_enrollment", "world_bank_wdi:SE.PRM.ENRR", "primary enrollment"),
    ("employment_rate", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "employment rate"),
    ("unemployment", "world_bank_wdi:SL.UEM.TOTL.ZS", "unemployment rate"),
]

additional_treatments = [
    ("gov_exp_gdp", "world_bank_wdi:GC.XPN.TOTL.GD.ZS", "government expenditure"),
    ("gov_consumption_gdp", "world_bank_wdi:NE.CON.GOVT.ZS", "government consumption"),
    ("tax_revenue_gdp", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", "tax revenue"),
    ("health_exp_gdp", "world_bank_wdi:SH.XPD.CHEX.GD.ZS", "health expenditure"),
    ("education_exp_gdp", "world_bank_wdi:SE.XPD.TOTL.GD.ZS", "education expenditure"),
    ("investment_gdp", "world_bank_wdi:NE.GDI.FTOT.ZS", "gross capital formation"),
]

# Schools to boost
school_targets = {
    "marxian": ("Marxian", 0.5),
    "marxist_leninist": ("Marxist-Leninist", 0.5),
    "mmt": ("MMT", 0.5),
    "degrowth": ("Degrowth", 0.5),
    "eco_socialist": ("Eco-Socialist", 0.55),
    "market_socialist": ("Market Socialist", 0.5),
}

for pos_id, (school_name, conf) in school_targets.items():
    for (out_name, out_source, out_desc) in additional_outcomes:
        for (treat_name, treat_source, treat_desc) in additional_treatments:
            if len(templates) >= 200:
                break
            direction = "negative" if out_name in ["infant_mortality", "poverty_headcount", "under5_mortality", "unemployment"] else "positive"

            claim = f"Higher {treat_desc} as a share of GDP is associated with {'lower' if direction == 'negative' else 'higher'} {out_desc}, consistent with the {school_name} view that an active public sector improves socioeconomic outcomes."
            topic = "fiscal" if "gov" in treat_name or "tax" in treat_name else "growth" if "investment" in treat_name else "healthcare" if "health" in treat_name else "institutional_quality" if "education" in treat_name else "growth"

            spec = {
                "title": f"{treat_desc.capitalize()} raises {out_desc}",
                "description": f"Panel test of {treat_name} vs {out_name}.",
                "prior_confidence": conf,
                "variables": {
                    "outcome": [{"name": out_name, "source": out_source}],
                    "treatment": [{"name": treat_name, "source": treat_source}],
                    "controls": [
                        {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                        {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
                        {"name": "population_growth", "source": "world_bank_wdi:SP.POP.GROW"},
                    ]
                },
                "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
                "falsification": {"rule": f"Falsified if {treat_name} does not have a {direction} coefficient on {out_name} at p < 0.05."},
            }
            templates.append((claim, pos_id, topic, spec))
        if len(templates) >= 200:
            break
    if len(templates) >= 200:
        break

# Write all hypotheses
for claim, pos_id, topic, spec in templates:
    hid = clean_hid(f"{pos_id}_{claim.split()[0].lower()}_{claim.split()[1].lower()}_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000,9999)}")

    spec_full = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": claim,
        "notes": f"Specific Marxist/socialist hypothesis testing {pos_id} prediction.",
        "prior_confidence": spec["prior_confidence"],
        "falsification": spec["falsification"],
        "evidence_type": "associational",
        "scope": {
            "period": [1970, 2023],
            "countries": ["ALL"],
            "outcome_dim": [topic],
            "policy_family": [topic],
        },
        "variables": spec["variables"],
        "estimator": spec["estimator"],
        "covers_claims": [{
            "position_id": pos_id,
            "claim_index": 0,
            "polarity": "aligned",
            "school_prediction": "supported",
            "confidence": "medium",
        }],
    }
    write_hypothesis(hid, spec_full, topic)

print(f"Generated {len(templates)} specific Marxist hypotheses")
