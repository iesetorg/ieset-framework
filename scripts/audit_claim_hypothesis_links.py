#!/usr/bin/env python3
"""Audit positions/*.yaml claim→hypothesis SCOPE ALIGNMENT.

Complements audit_claim_polarity.py. Where the polarity audit asks
"does the school's claim direction match the hypothesis's direction?",
this audit asks the prior question: "is the linked hypothesis even
testing what the claim asserts?"

For every claim, extract:
  - Era / years (from claim text via name→date mapping + explicit year matches)
  - Geography (country aliases in claim text → ISO3)
  - Outcome keywords (wage / labour-share / growth / inflation / etc)
  - Policy keywords (tax cut / deregulation / privatisation / etc)

Then compare against the hypothesis's declared:
  - sample.period (year range)
  - sample.countries (ISO3 list)
  - claim text + variables.outcome[]

Emit TSV rows with per-axis mismatch flags:
  - ERA_MISMATCH: claim years outside hypothesis period
  - GEO_MISMATCH: claim countries not in hypothesis sample
  - OUTCOME_MISMATCH: claim outcome keyword not in hypothesis text
  - POLICY_MISMATCH: claim policy keyword not in hypothesis text
  - NO_HYPOTHESIS: linked_hypothesis_id doesn't exist in library
  - PASS: all axes align (or scope fields too sparse to flag)

The output is for human triage, NOT as a hard gate. Low precision is
acceptable — this is a *review* tool that flags suspicious pairs.

Usage:
    scripts/audit_claim_hypothesis_links.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSITIONS_DIR = ROOT / "positions"
HYPOTHESES_DIR = ROOT / "hypotheses"
AUDIT_DIR = ROOT / "engine" / "audits"


# ---------------------------------------------------------------------------
# Country alias → ISO3 lookup (word-boundary matches)
# ---------------------------------------------------------------------------
COUNTRY_ALIASES: dict[str, str] = {
    # Anglosphere
    "US": "USA", "U.S.": "USA", "USA": "USA", "America": "USA",
    "American": "USA", "United States": "USA",
    "UK": "GBR", "U.K.": "GBR", "British": "GBR", "Britain": "GBR",
    "England": "GBR", "United Kingdom": "GBR",
    "Canada": "CAN", "Canadian": "CAN",
    "Australia": "AUS", "Australian": "AUS",
    "NZ": "NZL", "New Zealand": "NZL", "Kiwi": "NZL",
    "Ireland": "IRL", "Irish": "IRL",
    # Continental Europe
    "Germany": "DEU", "German": "DEU", "West Germany": "DEU",
    "East Germany": "DDR", "GDR": "DDR",
    "France": "FRA", "French": "FRA",
    "Italy": "ITA", "Italian": "ITA",
    "Spain": "ESP", "Spanish": "ESP",
    "Netherlands": "NLD", "Dutch": "NLD",
    "Belgium": "BEL", "Belgian": "BEL",
    "Austria": "AUT", "Austrian": "AUT",
    "Switzerland": "CHE", "Swiss": "CHE",
    "Portugal": "PRT", "Portuguese": "PRT",
    "Greece": "GRC", "Greek": "GRC",
    "Poland": "POL", "Polish": "POL",
    "Czech": "CZE", "Czechia": "CZE",
    "Hungary": "HUN", "Hungarian": "HUN",
    "Romania": "ROU", "Romanian": "ROU",
    "Bulgaria": "BGR", "Bulgarian": "BGR",
    "Slovakia": "SVK", "Slovenia": "SVN",
    "Estonia": "EST", "Latvia": "LVA", "Lithuania": "LTU",
    # Nordic
    "Sweden": "SWE", "Swedish": "SWE",
    "Norway": "NOR", "Norwegian": "NOR",
    "Denmark": "DNK", "Danish": "DNK",
    "Finland": "FIN", "Finnish": "FIN",
    "Iceland": "ISL", "Icelandic": "ISL",
    # Eastern Europe / post-Soviet
    "Russia": "RUS", "Russian": "RUS", "USSR": "RUS", "Soviet Union": "RUS",
    "Ukraine": "UKR", "Ukrainian": "UKR",
    "Belarus": "BLR", "Kazakhstan": "KAZ", "Uzbekistan": "UZB",
    # East Asia
    "China": "CHN", "Chinese": "CHN",
    "Hong Kong": "HKG",
    "Taiwan": "TWN", "Taiwanese": "TWN",
    "Japan": "JPN", "Japanese": "JPN",
    "Korea": "KOR", "Korean": "KOR", "South Korea": "KOR",
    "North Korea": "PRK", "DPRK": "PRK",
    "Singapore": "SGP",
    # SE + S Asia
    "Vietnam": "VNM", "Vietnamese": "VNM",
    "Indonesia": "IDN", "Indonesian": "IDN",
    "Malaysia": "MYS", "Malaysian": "MYS",
    "Thailand": "THA", "Thai": "THA",
    "Philippines": "PHL", "Philippine": "PHL", "Filipino": "PHL",
    "Cambodia": "KHM", "Cambodian": "KHM",
    "Myanmar": "MMR", "Burma": "MMR",
    "India": "IND", "Indian": "IND",
    "Pakistan": "PAK", "Pakistani": "PAK",
    "Bangladesh": "BGD", "Bangladeshi": "BGD",
    "Sri Lanka": "LKA", "Sri Lankan": "LKA",
    "Nepal": "NPL", "Bhutan": "BTN",
    # Middle East + N Africa
    "Israel": "ISR", "Israeli": "ISR",
    "Turkey": "TUR", "Turkish": "TUR",
    "Saudi Arabia": "SAU", "Saudi": "SAU",
    "UAE": "ARE", "Iran": "IRN", "Iranian": "IRN",
    "Iraq": "IRQ", "Egypt": "EGY", "Egyptian": "EGY",
    "Morocco": "MAR", "Tunisia": "TUN", "Algeria": "DZA",
    # Sub-Saharan Africa
    "South Africa": "ZAF", "Nigeria": "NGA", "Nigerian": "NGA",
    "Kenya": "KEN", "Kenyan": "KEN", "Ethiopia": "ETH",
    "Ghana": "GHA", "Ghanaian": "GHA",
    "Zimbabwe": "ZWE", "Zimbabwean": "ZWE",
    "Zambia": "ZMB", "Tanzania": "TZA", "Uganda": "UGA",
    "Senegal": "SEN", "Côte d'Ivoire": "CIV", "Ivory Coast": "CIV",
    "Angola": "AGO", "Mozambique": "MOZ", "Rwanda": "RWA",
    # Latin America
    "Mexico": "MEX", "Mexican": "MEX",
    "Guatemala": "GTM", "Honduras": "HND", "El Salvador": "SLV",
    "Nicaragua": "NIC", "Costa Rica": "CRI", "Panama": "PAN",
    "Cuba": "CUB", "Cuban": "CUB",
    "Dominican Republic": "DOM", "Haiti": "HTI",
    "Jamaica": "JAM",
    "Colombia": "COL", "Colombian": "COL",
    "Venezuela": "VEN", "Venezuelan": "VEN",
    "Ecuador": "ECU", "Ecuadorian": "ECU",
    "Peru": "PER", "Peruvian": "PER",
    "Chile": "CHL", "Chilean": "CHL",
    "Bolivia": "BOL", "Bolivian": "BOL",
    "Paraguay": "PRY", "Uruguay": "URY",
    "Argentina": "ARG", "Argentine": "ARG", "Argentinian": "ARG",
    "Brazil": "BRA", "Brazilian": "BRA",
}

# Named eras / politicians / policy events → (start, end) — inclusive
ERA_PATTERNS: list[tuple[str, tuple[int, int]]] = [
    # US presidencies / administrations
    (r"\bReagan\b|\bReagan[-\s]era\b|Reaganomics", (1981, 1989)),
    (r"\bBush\s+41\b|\bBush Sr\b", (1989, 1993)),
    (r"\bClinton\b|Clinton[-\s]era", (1993, 2001)),
    (r"\bBush\s+43\b|\bBush Jr\b|\bGeorge W\. Bush\b", (2001, 2009)),
    (r"\bObama\b|Obama[-\s]era", (2009, 2017)),
    (r"\bTrump\b|Trump[-\s]era|TCJA|\bTCJA\b", (2017, 2021)),
    (r"\bBiden\b", (2021, 2025)),
    # UK
    (r"Thatcher(?:ite|'s| era)?|Thatcher\b", (1979, 1990)),
    (r"\bBlair\b|New Labour", (1997, 2010)),
    (r"Brown(?:\s+premiership)?", (2007, 2010)),
    (r"\bCameron\b|Osborne", (2010, 2016)),
    (r"\bBrexit\b|post[-\s]Brexit", (2016, 2024)),
    (r"Corbyn(?:ism)?", (2015, 2020)),
    (r"Truss", (2022, 2023)),
    # France
    (r"Mitterrand", (1981, 1995)),
    (r"Chirac", (1995, 2007)),
    (r"Macron", (2017, 2027)),
    # Latin America
    (r"Chavismo|Chavista|Ch[áa]vez", (1999, 2013)),
    (r"Maduro(?:[-\s]era)?", (2014, 2024)),
    (r"Pinochet(?:[-\s]era)?|Chicago Boys", (1973, 1990)),
    (r"Allende", (1970, 1973)),
    (r"Milei", (2023, 2027)),
    (r"Menem", (1989, 1999)),
    (r"Kirchner(?:ism)?|CFK|Cristina Fern[aá]ndez", (2003, 2015)),
    (r"Lula", (2003, 2011)),
    (r"\bPT\b|Workers[' ]Party", (2003, 2016)),
    (r"Bolsonaro", (2019, 2023)),
    (r"Petro", (2022, 2027)),
    (r"Correa", (2007, 2017)),
    (r"Morales(?:[-\s]era)?", (2006, 2019)),
    # Germany
    (r"Schröder|Schroeder|Hartz(?:[-\s]IV)?|Agenda 2010", (1998, 2010)),
    (r"Merkel", (2005, 2021)),
    # Asia
    (r"Deng Xiaoping|Deng[-\s]?era|China[-\s]?1978", (1978, 1997)),
    (r"Mao(?:[-\s]era)?", (1949, 1976)),
    (r"India[-\s]?1991|Manmohan Singh reforms|Rao[-\s]Singh", (1991, 2004)),
    (r"\bAbenomics\b", (2012, 2020)),
    (r"Japan(?:ese)?\s+lost\s+decade(?:s)?", (1991, 2010)),
    (r"Rogernomics|Roger Douglas", (1984, 1993)),
    (r"Doi\s+Moi", (1986, 2000)),
    # US financial / policy
    (r"\bVolcker\b|Volcker\s+disinflation", (1979, 1987)),
    (r"\bNAFTA\b", (1994, 2020)),
    (r"USMCA", (2020, 2027)),
    (r"Gramm[-\s]Leach[-\s]Bliley|GLB", (1999, 2008)),
    (r"Glass[-\s]Steagall repeal", (1999, 2008)),
    (r"Dodd[-\s]Frank", (2010, 2020)),
    (r"\bTARP\b", (2008, 2010)),
    (r"\bQE\d?\b|quantitative easing", (2008, 2022)),
    (r"great recession|post[-\s]2008", (2008, 2013)),
    (r"\bGFC\b|global financial crisis|2008\s+(?:crash|crisis)", (2007, 2010)),
    (r"Great Depression", (1929, 1939)),
    (r"COVID(?:[-\s]19)?|pandemic", (2020, 2022)),
    # UK events
    (r"Big Bang\b", (1986, 1990)),
    (r"Town and Country Planning Act 1947", (1947, 1990)),
    # Historical blocks
    (r"post[-\s]WW2|post[-\s]war(?:\s+era)?", (1945, 1973)),
    (r"golden age of capitalism|post[-\s]war boom", (1945, 1973)),
    (r"Cold War(?:[-\s]era)?", (1947, 1991)),
    (r"post[-\s]Soviet|Soviet collapse|Soviet dissolution", (1991, 2000)),
    (r"Eastern\s+bloc|Warsaw Pact", (1947, 1991)),
    # Zimbabwe
    (r"Zimbabwe\s+hyperinflation|Zim\s+hyperinflation", (2000, 2008)),
    (r"Mugabe(?:[-\s]era)?", (1980, 2017)),
    # Welfare / fiscal
    (r"Clinton[-\s]era welfare reform|TANF|1996 welfare reform|PRWORA", (1996, 2005)),
    (r"Affordable Care Act|\bACA\b|Obamacare", (2010, 2020)),
    # Trade
    (r"WTO accession|China WTO", (2001, 2015)),
    (r"EU single market|Single European Act", (1993, 2020)),
    # Other
    (r"Rajapaksa", (2005, 2015)),
    (r"Nixon(?:\s+shock)?|Nixon price controls", (1971, 1974)),
    (r"Kennedy[-\s]Johnson tax cuts|Kennedy tax cuts", (1962, 1967)),
]

# Named entities: if a claim mentions one, the hypothesis should too.
# Format: canonical_name → list of regex patterns matching variants in text.
# The audit flags POLICY_NAMED_ABSENT when a claim mentions a named entity
# that is missing from the hypothesis text — strong signal of semantic drift.
NAMED_ENTITIES: dict[str, list[str]] = {
    # US presidents / administrations
    "reagan":    [r"Reagan"],
    "tcja":      [r"\bTCJA\b|Tax\s+Cuts\s+and\s+Jobs\s+Act"],
    "trump":     [r"\bTrump\b"],
    "obama":     [r"\bObama\b"],
    "biden":     [r"\bBiden\b"],
    "clinton":   [r"\bClinton\b"],
    "bush":      [r"\bBush\b"],
    "kennedy":   [r"\bKennedy\b"],
    "nixon":     [r"\bNixon\b"],
    "carter":    [r"\bCarter\b"],
    # UK
    "thatcher":  [r"Thatcher"],
    "blair":     [r"\bBlair\b|New\s+Labour"],
    "brown":     [r"\bBrown\s+premiership|Gordon\s+Brown\b"],
    "cameron":   [r"\bCameron\b"],
    "brexit":    [r"\bBrexit\b|post[-\s]Brexit|EU\s+referendum"],
    "corbyn":    [r"Corbyn"],
    "osborne":   [r"Osborne"],
    "truss":     [r"\bTruss\b"],
    # Latin America
    "chavez":    [r"Ch[áa]vez|Chavismo|Chavista"],
    "maduro":    [r"\bMaduro\b"],
    "pinochet":  [r"Pinochet|Chicago\s+Boys"],
    "allende":   [r"Allende"],
    "milei":     [r"\bMilei\b"],
    "menem":     [r"\bMenem\b"],
    "kirchner":  [r"Kirchner|Cristina\s+Fern"],
    "lula":      [r"\bLula\b"],
    "bolsonaro": [r"Bolsonaro"],
    "petro":     [r"\bPetro\b"],
    "correa":    [r"Correa"],
    "morales":   [r"\bMorales\b"],
    "fujimori":  [r"Fujimori"],
    # Germany / France
    "mitterrand":[r"Mitterrand"],
    "chirac":    [r"Chirac"],
    "sarkozy":   [r"Sarkozy"],
    "hollande":  [r"Hollande"],
    "macron":    [r"Macron"],
    "schroder":  [r"Schr[öo]der|Hartz\s+IV|Agenda\s+2010"],
    "merkel":    [r"Merkel"],
    "kohl":      [r"\bKohl\b"],
    # Asia
    "deng":      [r"Deng\s+Xiaoping|Deng[- ]era|\bDeng\b"],
    "mao":       [r"\bMao\b|Great\s+Leap|Cultural\s+Revolution"],
    "xi":        [r"Xi\s+Jinping"],
    "modi":      [r"\bModi\b"],
    "singh":     [r"Manmohan\s+Singh"],
    "abe":       [r"Abenomics|\bAbe\b"],
    "rogernomics":[r"Rogernomics|Roger\s+Douglas"],
    "park":      [r"Park\s+Chung[- ]?hee"],
    "doi_moi":   [r"Doi\s+Moi"],
    # Africa
    "mugabe":    [r"Mugabe"],
    "mandela":   [r"Mandela"],
    # Russia
    "putin":     [r"Putin"],
    "yeltsin":   [r"Yeltsin|shock\s+therapy\s+Russia"],
    "gorbachev": [r"Gorbachev|perestroika"],
    # US financial / monetary
    "volcker":   [r"Volcker"],
    "greenspan": [r"Greenspan"],
    "bernanke":  [r"Bernanke"],
    "yellen":    [r"Yellen"],
    "powell":    [r"\bPowell\b"],
    "friedman":  [r"\bFriedman\b"],
    "keynes":    [r"\bKeynes\b"],
    "hayek":     [r"\bHayek\b"],
    "marx":      [r"\bMarx\b"],
    # Policy events
    "nafta":     [r"\bNAFTA\b"],
    "usmca":     [r"\bUSMCA\b"],
    "gramm_leach":[r"Gramm[-\s]Leach[-\s]Bliley|\bGLB\b"],
    "glass_steagall":[r"Glass[-\s]Steagall"],
    "dodd_frank":[r"Dodd[-\s]Frank"],
    "tarp":      [r"\bTARP\b"],
    "qe":        [r"\bQE\d?\b|quantitative\s+easing"],
    "wto":       [r"\bWTO\b|World\s+Trade\s+Organization"],
    "eu_single_market":[r"EU\s+single\s+market|Single\s+European\s+Act"],
    "maastricht":[r"Maastricht"],
    "big_bang":  [r"Big\s+Bang\b"],
    "aca":       [r"\bACA\b|Affordable\s+Care\s+Act|Obamacare"],
    "tanf":      [r"\bTANF\b|1996\s+welfare\s+reform|PRWORA"],
    "gfc":       [r"\bGFC\b|2007[-\s]2009\s+(?:financial\s+)?crisis|global\s+financial\s+crisis|2008\s+(?:crash|crisis)"],
    "great_depression":[r"Great\s+Depression"],
    "covid":     [r"COVID|pandemic"],
    "reach":     [r"\bREACH\b"],
    "gdpr":      [r"\bGDPR\b"],
    "csrd":      [r"\bCSRD\b"],
    "ai_act":    [r"\bAI\s+Act\b"],
    "bolivarian":[r"Bolivarian"],
    "chavismo":  [r"Chavismo"],
    "deng_reform":[r"Deng\s+Xiaoping|China\s+1978|household\s+responsibility"],
    "india_1991":[r"India\s+1991|Manmohan|Rao[-\s]Singh|India.*1991"],
    "german_reunification":[r"reunification|German\s+unification"],
    "soviet_collapse":[r"Soviet\s+collapse|Soviet\s+dissolution|post[-\s]Soviet"],
    # Specific country-level entities that might get scoped off
    "solidarity":[r"Solidarity\b|Solidarno"],
    # CCP / China
    "ccp":       [r"\bCCP\b|Chinese\s+Communist\s+Party"],
    # Economic frameworks
    "laffer":    [r"Laffer"],
    "minsky":    [r"Minsky"],
    "phillips_curve":[r"Phillips\s+curve|natural[-\s]rate"],
    "solow":     [r"Solow"],
    # Zimbabwe
    "zimbabwe_hyperinflation":[r"Zimbabwe.*hyperinflation|Zim.*hyperinflation|2000[-\s]2008\s+Zimbabwe"],
}


def extract_named_entities(text: str) -> set[str]:
    """Return canonical entity names referenced in text."""
    out: set[str] = set()
    for canonical, pats in NAMED_ENTITIES.items():
        for p in pats:
            if re.search(p, text, re.IGNORECASE):
                out.add(canonical)
                break
    return out


# Outcome-family keywords: maps a token family → list of regex patterns
OUTCOME_KEYWORDS: dict[str, list[str]] = {
    "labour_share": [r"labou?r\s+share", r"wage\s+share", r"capital share"],
    "productivity": [r"productivity", r"TFP", r"total factor productivity",
                     r"output per worker", r"output per hour"],
    "wage_stagnation": [r"median\s+wage", r"real\s+wage", r"wage\s+stagnation",
                        r"productivity[-\s]compensation", r"decoupl"],
    "gdp_growth": [r"GDP growth", r"per\s*capita growth", r"income growth",
                   r"output growth", r"real GDP", r"convergence"],
    "inflation": [r"inflation", r"price\s+level", r"CPI", r"hyperinflation",
                  r"disinflation", r"deflation"],
    "poverty_inequality": [r"poverty", r"inequality", r"Gini",
                            r"top\s+\d+%", r"wealth\s+concentration",
                            r"income\s+distribution"],
    "employment_labour": [r"unemployment", r"employment", r"labou?r[-\s]force",
                          r"labou?r\s+participation", r"Phillips\s+curve",
                          r"natural[-\s]rate"],
    "housing_supply": [r"housing", r"rent\s+control", r"housing\s+supply",
                       r"zoning", r"rental"],
    "financial_crisis": [r"financial\s+crisis", r"bank\s+crisis", r"credit crunch",
                         r"asset\s+price\s+inflation", r"bubble"],
    "institutional_quality": [r"rule\s+of\s+law", r"institutional\s+quality",
                              r"property\s+rights", r"corruption",
                              r"state\s+capacity"],
    "trade_liberalisation": [r"trade\s+liberalisation", r"tariff", r"free trade",
                              r"openness", r"WTO"],
    "privatisation": [r"privatis", r"privatiz", r"nationalis",
                      r"state[-\s]owned", r"SOE"],
    "regulatory": [r"regulat", r"licens", r"deregulat"],
    "tax": [r"tax\s+cut", r"tax\s+reform", r"marginal\s+rate", r"Laffer",
            r"income\s+tax", r"corporate\s+tax"],
    "monetary_policy": [r"monetary\s+policy", r"interest\s+rate",
                        r"central\s+bank", r"money\s+supply", r"M2",
                        r"base\s+money", r"Fed\b", r"ECB\b"],
    "health_mortality": [r"mortality", r"life\s+expectancy",
                         r"infant\s+mortality", r"morbidity", r"HDI"],
    "energy_climate": [r"electricity\s+price", r"energy\s+cost",
                       r"emissions", r"nuclear", r"renewable", r"carbon"],
    "welfare_state": [r"welfare\s+state", r"welfare\s+reform", r"benefit",
                     r"unemployment\s+insurance", r"pension"],
}


def iter_alias_positions(text: str) -> set[str]:
    """Return all ISO3 codes matched in text by the alias dictionary."""
    out: set[str] = set()
    for alias, iso in COUNTRY_ALIASES.items():
        # Word-boundary match (case-insensitive for multi-word aliases)
        pat = r"\b" + re.escape(alias) + r"\b"
        if re.search(pat, text, re.IGNORECASE):
            out.add(iso)
    # Also pick up explicit ISO3 tokens (e.g. "USA, DEU, CHN" in a claim)
    # Only accept tokens that already appear as ISO3 in our value set to avoid
    # false positives from acronyms (FDI, GDP, etc).
    iso_set = set(COUNTRY_ALIASES.values())
    for m in re.finditer(r"\b[A-Z]{3}\b", text):
        if m.group() in iso_set:
            out.add(m.group())
    return out


def extract_years(text: str) -> set[int]:
    """Return set of years referenced (via explicit numbers + named eras)."""
    years: set[int] = set()
    # Explicit ranges "1979-1990" / "1979–1990"
    for m in re.finditer(r"\b((?:19|20)\d{2})\s*[-–]\s*((?:19|20)\d{2})\b", text):
        y1, y2 = int(m.group(1)), int(m.group(2))
        for y in range(min(y1, y2), max(y1, y2) + 1):
            years.add(y)
    # Bare years
    for m in re.finditer(r"\b(?:19|20)\d{2}\b", text):
        years.add(int(m.group()))
    # "post-1978" style
    for m in re.finditer(r"post[-\s]?((?:19|20)\d{2})", text, re.IGNORECASE):
        y1 = int(m.group(1))
        for y in range(y1, y1 + 10):  # assume ~10-year post-window
            years.add(y)
    # Named eras
    for pat, (y1, y2) in ERA_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            for y in range(y1, y2 + 1):
                years.add(y)
    return years


def extract_outcomes(text: str) -> set[str]:
    """Return set of outcome-family tags matched in text."""
    out: set[str] = set()
    for family, pats in OUTCOME_KEYWORDS.items():
        for p in pats:
            if re.search(p, text, re.IGNORECASE):
                out.add(family)
                break
    return out


# ---------------------------------------------------------------------------
# Hypothesis loading
# ---------------------------------------------------------------------------
def load_hypotheses() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in HYPOTHESES_DIR.glob("*/*.yaml"):
        if p.parent.name == "steelman":
            continue
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        hid = spec.get("hypothesis_id", p.stem)
        out[hid] = {"path": str(p.relative_to(ROOT)), "spec": spec}
    return out


def hypothesis_period(spec: dict) -> tuple[int, int] | None:
    period = (spec.get("sample") or {}).get("period")
    if not isinstance(period, (list, tuple)) or len(period) != 2:
        return None
    try:
        return (int(period[0]), int(period[1]))
    except (TypeError, ValueError):
        return None


def hypothesis_countries(spec: dict) -> set[str]:
    c = (spec.get("sample") or {}).get("countries")
    if not isinstance(c, list):
        return set()
    return {str(x).upper() for x in c if isinstance(x, str)}


def hypothesis_full_text(spec: dict) -> str:
    """Concatenate hypothesis fields that describe what it tests — used to
    match outcome keywords."""
    parts = [str(spec.get("claim", "")),
             str(spec.get("hypothesis_id", "")),
             str(spec.get("topic", ""))]
    # Variable names and notes
    vars_ = spec.get("variables", {}) or {}
    for bucket in ("outcome", "treatment", "controls"):
        for v in vars_.get(bucket, []) or []:
            if isinstance(v, dict):
                parts.append(str(v.get("name", "")))
                parts.append(str(v.get("notes", "")))
    est = spec.get("estimator", {}) or {}
    parts.append(str(est.get("notes", "")))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Scope match evaluation
# ---------------------------------------------------------------------------
def evaluate_link(claim_text: str, spec: dict) -> dict:
    """Return flags + reasons for a claim↔hypothesis pair."""
    flags: list[str] = []
    reasons: list[str] = []

    claim_years = extract_years(claim_text)
    claim_countries = iter_alias_positions(claim_text)
    claim_outcomes = extract_outcomes(claim_text)
    claim_entities = extract_named_entities(claim_text)

    hyp_period = hypothesis_period(spec)
    hyp_countries = hypothesis_countries(spec)
    hyp_text = hypothesis_full_text(spec)
    hyp_outcomes = extract_outcomes(hyp_text)
    hyp_entities = extract_named_entities(hyp_text)

    # ---------- Era alignment ----------
    if claim_years and hyp_period:
        claim_min, claim_max = min(claim_years), max(claim_years)
        hyp_min, hyp_max = hyp_period
        # Consider mismatch if claim year range and hypothesis period
        # have zero overlap at all.
        if claim_max < hyp_min or claim_min > hyp_max:
            flags.append("ERA_MISMATCH")
            reasons.append(
                f"claim refers to {claim_min}-{claim_max}; "
                f"hypothesis period {hyp_min}-{hyp_max}"
            )
        else:
            # Partial coverage: majority of claim years outside period
            inside = sum(1 for y in claim_years if hyp_min <= y <= hyp_max)
            if inside / max(len(claim_years), 1) < 0.25:
                flags.append("ERA_PARTIAL")
                reasons.append(
                    f"only {inside}/{len(claim_years)} claim years "
                    f"fall within hypothesis period {hyp_min}-{hyp_max}"
                )

    # ---------- Geography ----------
    if claim_countries and hyp_countries:
        overlap = claim_countries & hyp_countries
        if not overlap:
            flags.append("GEO_MISMATCH")
            reasons.append(
                f"claim countries {sorted(claim_countries)} not in "
                f"hypothesis sample {sorted(hyp_countries)[:6]}"
                f"{'…' if len(hyp_countries) > 6 else ''}"
            )
    elif claim_countries and not hyp_countries:
        # Hypothesis has no country list (cross-country panel w/ no enumerated
        # sample). Soft flag — can't verify.
        flags.append("GEO_UNVERIFIABLE")
        reasons.append("hypothesis has no sample.countries list")

    # ---------- Outcome family ----------
    if claim_outcomes and hyp_outcomes:
        overlap = claim_outcomes & hyp_outcomes
        if not overlap:
            flags.append("OUTCOME_MISMATCH")
            reasons.append(
                f"claim outcomes {sorted(claim_outcomes)} disjoint from "
                f"hypothesis outcomes {sorted(hyp_outcomes)}"
            )
    elif claim_outcomes and not hyp_outcomes:
        flags.append("OUTCOME_UNVERIFIABLE")
        reasons.append(
            f"no outcome keywords detected in hypothesis; "
            f"claim mentions {sorted(claim_outcomes)}"
        )

    # ---------- Named entities (high-signal policy/actor drift) ----------
    if claim_entities:
        missing = claim_entities - hyp_entities
        # Ignore entity names that also appear as broad generic terms the
        # hypothesis might describe differently (e.g. "marx"/"keynes" as
        # theory names).
        generic_entities = {"marx", "keynes", "hayek", "friedman",
                             "minsky", "solow", "laffer", "phillips_curve"}
        missing -= generic_entities
        if missing:
            flags.append("POLICY_NAMED_ABSENT")
            reasons.append(
                f"claim references {sorted(missing)} — "
                f"not found in hypothesis text (hyp entities: "
                f"{sorted(hyp_entities) if hyp_entities else 'none'})"
            )

    return {
        "flags": flags,
        "reasons": "; ".join(reasons),
        "claim_years": sorted(claim_years),
        "claim_countries": sorted(claim_countries),
        "claim_outcomes": sorted(claim_outcomes),
        "claim_entities": sorted(claim_entities),
        "hyp_period": list(hyp_period) if hyp_period else None,
        "hyp_countries": sorted(hyp_countries),
        "hyp_outcomes": sorted(hyp_outcomes),
        "hyp_entities": sorted(hyp_entities),
    }


# ---------------------------------------------------------------------------
# Audit driver
# ---------------------------------------------------------------------------
def build_audit() -> list[dict]:
    hyps = load_hypotheses()
    rows: list[dict] = []
    for p in sorted(POSITIONS_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        spec = yaml.safe_load(p.read_text())
        if not isinstance(spec, dict):
            continue
        position_id = spec.get("position_id", p.stem)
        claims = spec.get("falsifiable_specific_claims", []) or []
        for i, c in enumerate(claims):
            hid = c.get("linked_hypothesis_id", "")
            claim_text = c.get("claim", "")
            hyp_entry = hyps.get(hid)
            if not hyp_entry:
                rows.append({
                    "position_id": position_id,
                    "claim_index": i,
                    "linked_hypothesis_id": hid,
                    "hypothesis_found": False,
                    "verdict": "NO_HYPOTHESIS",
                    "flags": ["NO_HYPOTHESIS"],
                    "reasons": f"hypothesis '{hid}' not in library",
                    "claim_text": claim_text,
                    "school_prediction": c.get("school_prediction", ""),
                    "current_polarity": c.get("claim_polarity", "aligned"),
                    "claim_years": [],
                    "claim_countries": [],
                    "claim_outcomes": [],
                    "hyp_period": None,
                    "hyp_countries": [],
                    "hyp_outcomes": [],
                })
                continue
            eval_ = evaluate_link(claim_text, hyp_entry["spec"])
            hard_flags = [f for f in eval_["flags"]
                          if f in ("ERA_MISMATCH", "GEO_MISMATCH",
                                   "OUTCOME_MISMATCH", "POLICY_NAMED_ABSENT")]
            soft_flags = [f for f in eval_["flags"]
                          if f in ("ERA_PARTIAL", "GEO_UNVERIFIABLE",
                                   "OUTCOME_UNVERIFIABLE")]
            if hard_flags:
                verdict = "FAIL"
            elif soft_flags:
                verdict = "REVIEW"
            else:
                verdict = "PASS"
            rows.append({
                "position_id": position_id,
                "claim_index": i,
                "linked_hypothesis_id": hid,
                "hypothesis_found": True,
                "verdict": verdict,
                "flags": eval_["flags"],
                "reasons": eval_["reasons"],
                "claim_text": claim_text,
                "school_prediction": c.get("school_prediction", ""),
                "current_polarity": c.get("claim_polarity", "aligned"),
                **{k: eval_[k] for k in ("claim_years", "claim_countries",
                                          "claim_outcomes", "claim_entities",
                                          "hyp_period", "hyp_countries",
                                          "hyp_outcomes", "hyp_entities")},
            })
    return rows


def write_outputs(rows: list[dict]):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    tsv = AUDIT_DIR / "claim_hypothesis_link_audit.tsv"
    headers = [
        "position_id", "claim_index", "linked_hypothesis_id", "verdict",
        "flags", "reasons", "school_prediction", "current_polarity",
        "claim_years_range", "claim_countries", "hyp_period",
        "hyp_countries_count", "claim_outcomes", "hyp_outcomes",
        "claim_entities", "hyp_entities",
        "claim_text",
    ]
    lines = ["\t".join(headers)]
    for r in rows:
        cy = r["claim_years"]
        cy_range = f"{min(cy)}-{max(cy)}" if cy else ""
        hp = r["hyp_period"]
        hp_str = f"{hp[0]}-{hp[1]}" if hp else ""
        vals = [
            r["position_id"],
            str(r["claim_index"]),
            r["linked_hypothesis_id"],
            r["verdict"],
            ",".join(r["flags"]),
            r["reasons"],
            r.get("school_prediction", ""),
            r.get("current_polarity", ""),
            cy_range,
            ",".join(r["claim_countries"]),
            hp_str,
            str(len(r["hyp_countries"])),
            ",".join(r["claim_outcomes"]),
            ",".join(r["hyp_outcomes"]),
            ",".join(r.get("claim_entities", [])),
            ",".join(r.get("hyp_entities", [])),
            r["claim_text"],
        ]
        vals = [str(v).replace("\t", " ").replace("\n", " ") for v in vals]
        lines.append("\t".join(vals))
    tsv.write_text("\n".join(lines) + "\n")
    (AUDIT_DIR / "claim_hypothesis_link_audit.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print(f"Wrote {tsv} ({len(rows)} rows)")


def summarise(rows: list[dict]):
    from collections import Counter
    total = len(rows)
    by_verdict = Counter(r["verdict"] for r in rows)
    print(f"\n=== Scope-alignment audit summary ({total} links) ===")
    for v in ("PASS", "REVIEW", "FAIL", "NO_HYPOTHESIS"):
        n = by_verdict.get(v, 0)
        pct = 100 * n / total if total else 0.0
        print(f"  {v:16s}  {n:4d}  ({pct:5.1f}%)")

    by_flag: Counter[str] = Counter()
    for r in rows:
        for f in r["flags"]:
            by_flag[f] += 1
    print("\nFlag frequency (flags can overlap per row):")
    for flag, n in by_flag.most_common():
        print(f"  {flag:20s}  {n:4d}")

    by_pos_fail: Counter[str] = Counter()
    for r in rows:
        if r["verdict"] == "FAIL":
            by_pos_fail[r["position_id"]] += 1
    print("\nFailing links by position (top 15):")
    for pos, n in by_pos_fail.most_common(15):
        print(f"  {pos:25s}  {n:3d}")


def main(argv: list[str] | None = None) -> int:
    rows = build_audit()
    write_outputs(rows)
    summarise(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
