"""Build dated context for the first coded movement in each country.

These observations are levels from external datasets, kept separate from the
movement-direction score. A measurement is an opening observation only when
it is at or before the first coded year and no more than five years earlier.
Later observations are retained with an explicit later-only label.

Normal regeneration uses a small, checked-in extraction of the selected source
rows. Full source vintages are gitignored; --refresh-extraction verifies their
bytes before refreshing the extraction, and --verify-vintages audits it against
those local files. A clean checkout can still verify the public artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DRIFT = ROOT / "data/derived/country_drift.json"
OUTPUT = ROOT / "data/derived/country_drift_starting_context.json"
EXTRACTION = ROOT / "data/inputs/drift_starting_context_observations.json"
OPENING_WINDOW_YEARS = 5

SOURCES = {
    "expense": {
        "path": "data/vintages/world_bank_wdi/GC.XPN.TOTL.GD.ZS@2026-04-30T131014Z.parquet",
        "sha256": "6415fec35cc561ac0d5743aa3ef38de80ea1e8a831eb95dbb214f6f58a5ed9ad",
        "source_url": "https://data.worldbank.org/indicator/GC.XPN.TOTL.GD.ZS",
        "definition_url": "https://databank.worldbank.org/metadataglossary/world-development-indicators/series/GC.XPN.TOTL.GD.ZS",
        "publisher": "World Bank WDI",
        "license": "CC BY 4.0",
        "license_url": "https://datacatalog.worldbank.org/public-licenses#cc-by",
        "metric_id": "government_expense_pct_gdp",
        "label": "Government expense",
        "unit": "% of GDP",
        "caveat": "Expense includes transfers and interest but not all public spending or ownership. Coverage may be central-government only and is not fully comparable across countries.",
        "column": "value",
    },
    "consumption": {
        "path": "data/vintages/world_bank_wdi/NE.CON.GOVT.ZS@2026-05-05T194701Z.parquet",
        "sha256": "a6605c618d3dd91b061c4dae7960c4c0baad66c037125aec44cb6b71ccb6a79d",
        "source_url": "https://data.worldbank.org/indicator/NE.CON.GOVT.ZS",
        "definition_url": "https://databank.worldbank.org/metadataglossary/world-development-indicators/series/NE.CON.GOVT.ZS",
        "publisher": "World Bank WDI",
        "license": "CC BY 4.0",
        "license_url": "https://datacatalog.worldbank.org/public-licenses#cc-by",
        "metric_id": "government_final_consumption_pct_gdp",
        "label": "Government final consumption",
        "unit": "% of GDP",
        "caveat": "Narrower fallback: government purchases of goods and services; it excludes transfers and is not total spending.",
        "column": "value",
    },
    "wgi_regulatory_quality": {
        "path": "data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet",
        "sha256": "4d8084d77990bc1d10f5630cdf8100c9ce2e1b610ade3aa7b46340fb658c8e2e",
        "source_url": "https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators",
        "definition_url": "https://www.worldbank.org/en/publication/worldwide-governance-indicators/frequently-asked-questions",
        "publisher": "World Bank WGI",
        "license": "CC BY 4.0",
        "license_url": "https://datacatalog.worldbank.org/public-licenses#cc-by",
        "metric_id": "wgi_regulatory_quality_estimate",
        "label": "Regulatory Quality estimate",
        "unit": "WGI estimate",
        "caveat": "Perceptions of how regulations support private-sector development; higher means better perceived quality on an approximately −2.5 to +2.5 scale. It is not economic freedom, ownership or an absolute market/state level. Estimates have uncertainty and later publisher vintages may revise history; small differences should not be overread.",
        "column": "value",
    },
}

HISTORICAL_CONTEXTS = {
    ("HRV", 1991): {
        "as_of_year": 1991,
        "summary": (
            "At independence in 1991, Croatia was transforming from the "
            "Yugoslav system of socially-owned enterprises into a sovereign "
            "market economy while confronting war and state-building. The "
            "1991 ownership-transformation law launched privatization, first "
            "through insider and employee ownership. This is a market-transition "
            "starting point under wartime conditions, not a numeric score."
        ),
        "sources": [
            {"label": "Government of Croatia previous governments", "url": "https://www.vlada.gov.hr/previous-governments-16138/16138"},
            {"label": "World Bank Croatia economic memoranda", "url": "https://documents1.worldbank.org/curated/en/977801468770733906/pdf/28600.pdf"},
        ],
    },
    ("GMB", 1994): {
        "as_of_year": 1994,
        "summary": (
            "At the opening point, a military coup had displaced Gambia's "
            "civilian government and donor support was suspended. The new "
            "regime inherited a small market economy, but political authority "
            "became concentrated and public confidence weakened. This is a "
            "qualitative governance and macroeconomic starting context, not a "
            "numeric market/state score."
        ),
        "sources": [
            {"label": "IMF Gambia Policy Framework Paper (1998–2000)", "url": "https://www.imf.org/external/np/pfp/gambia/gam01.htm"},
            {"label": "IMF Gambia democratic transition programme (2017)", "url": "https://www.elibrary.imf.org/view/journals/002/2017/179/article-A001-en.xml"},
        ],
    },
    ("MUS", 1968): {
        "as_of_year": 1968,
        "summary": (
            "At independence in 1968, Mauritius was a low-income, sugar-dependent "
            "economy with high unemployment and limited natural resources. "
            "Subsequent governments used export zones, infrastructure, education, "
            "and tourism to diversify rather than relying only on state ownership. "
            "This is a market economy with a developmental public sector, not a "
            "numeric market/state score."
        ),
        "sources": [
            {"label": "World Bank Mauritius Systematic Country Diagnostic", "url": "https://documents1.worldbank.org/curated/en/866371646406360210/pdf/Mauritius-Systematic-Country-Diagnostic-Update.pdf"},
            {"label": "World Bank Mauritius economic memorandum", "url": "https://documents1.worldbank.org/curated/en/882001468777248636/pdf/multi0page.pdf"},
        ],
    },
    ("OMN", 1970): {
        "as_of_year": 1970,
        "summary": (
            "Qaboos's accession in 1970 began a major period of state formation "
            "in a country with limited infrastructure and a small administrative "
            "system. The government channelled later oil revenues into health, "
            "education, transport, and utilities while retaining an open trade "
            "system and allowing private-sector participation. This is a "
            "state-led development starting point, not a numeric score."
        ),
        "sources": [
            {"label": "IMF Oman Beyond the Oil Horizon", "url": "https://www.elibrary.imf.org/abstract/book/9781557758330/ch01.xml"},
            {"label": "IMF Oman economic development review", "url": "https://www.elibrary.imf.org/view/journals/023/0030/015/article-A007-en.xml"},
        ],
    },
    ("GAB", 2009): {
        "as_of_year": 2009,
        "summary": (
            "The Ali Bongo government began with an oil-dependent economy and "
            "an economic-emergence agenda that aimed to diversify production "
            "and public revenue. Oil income gave the state substantial "
            "development capacity, but the economy remained exposed to price "
            "shocks, arrears, and public-debt pressure. This is a "
            "state-led-development starting context, not a numeric score."
        ),
        "sources": [
            {"label": "IMF Gabon mission statement (2010)", "url": "https://www.imf.org/fr/news/articles/2015/09/14/01/49/pr1090"},
            {"label": "IMF Gabon Extended Fund Facility (2021)", "url": "https://www.imf.org/en/publications/cr/issues/2021/08/25/gabon-request-for-a-three-year-extended-arrangement-under-the-extended-fund-facility-press-464667"},
        ],
    },
    ("FIN", 1977): {
        "as_of_year": 1977,
        "summary": (
            "At this opening point Finland was a market economy with a large "
            "Nordic welfare state and coordinated labour relations. The Sorsa "
            "government used tripartite incomes agreements to coordinate wage "
            "settlements and macroeconomic policy. This is a mixed market and "
            "coordinated-welfare starting context, not a numeric score."
        ),
        "sources": [
            {"label": "Finnish Government Sorsa II chronology", "url": "https://valtioneuvosto.fi/-/60.-sorsa-ii-15.5.1977-26.5.1979-"},
            {"label": "OECD Economic Survey of Finland (1977)", "url": "https://www.oecd.org/content/dam/oecd/en/publications/reports/1977/01/oecd-economic-surveys-finland-1977_g1g16f63/eco_surveys-fin-1977-en.pdf"},
        ],
    },
    ("IRL", 1977): {
        "as_of_year": 1977,
        "summary": (
            "Ireland's opening point here is a small, highly open market "
            "economy in which fiscal policy was increasingly used to support "
            "employment and development. The newly elected Fianna Fáil "
            "government adopted an expansionary budget stance while the public "
            "sector provided a substantial share of investment and social "
            "support. This is a market economy with an expanding fiscal state, "
            "not a numeric score."
        ),
        "sources": [
            {"label": "IMF Fiscal Policy in the Smaller Industrial Countries, Ireland chapter", "url": "https://www.elibrary.imf.org/display/book/9780939934362/ch014.xml"},
        ],
    },
    ("IRN", 1974): {
        "as_of_year": 1974,
        "summary": (
            "Iran entered this period with a mixed economy and rapidly growing "
            "oil revenues financing ambitious state-led development. Political "
            "authority was concentrated in the Shah; in 1975 the government "
            "abolished competing parties and required political affiliation "
            "through the Rastakhiz organisation. This is a state-directed "
            "development economy under authoritarian rule, not a numeric "
            "market/state score."
        ),
        "sources": [
            {"label": "U.S. Department of State historical record (Rastakhiz, 1975)", "url": "https://history.state.gov/historicaldocuments/frus1969-76v27/d111"},
            {"label": "CIA World Factbook (Iran, 1976)", "url": "https://www.cia.gov/readingroom/document/cia-rdp08-00534r000100130001-8"},
        ],
    },
    ("NGA", 1975): {
        "as_of_year": 1975,
        "summary": (
            "Nigeria's opening point is the oil-boom era and launch of the "
            "Third National Development Plan. Oil revenues enabled the "
            "military government to plan large public investment in "
            "infrastructure, agriculture, housing, and social services, "
            "increasing the state's role in development. This is a "
            "state-led-development context, not a numeric market/state score."
        ),
        "sources": [
            {"label": "World Bank (Nigeria Third National Development Plan, 1975–80)", "url": "https://thedocs.worldbank.org/en/doc/925731391205377975-0560011977/original/WorldBankGroupArchivesFolder1772839.pdf"},
        ],
    },
    ("NOR", 1973): {
        "as_of_year": 1973,
        "summary": (
            "Norway's petroleum opening point predates major oil receipts. "
            "The Labour government established public oversight, a deliberate "
            "moderate extraction pace, and regional and industrial policy for "
            "the emerging petroleum sector. The wider economy remained a "
            "market economy with a substantial Nordic welfare state. This is "
            "state-guided development within a market system, not a numeric "
            "score."
        ),
        "sources": [
            {"label": "Norwegian Government, Parliamentary Report No. 25 (1973–74)", "url": "https://www.regjeringen.no/globalassets/upload/FIN/okonomiavdelingen/Stmeld_25_1973-74.pdf"},
            {"label": "Government of Norway petroleum policy review", "url": "https://www.regjeringen.no/en/documents/meld.-st.-28-20102011/id649699/?ch=1"},
        ],
    },
    ("YUG", 1973): {
        "as_of_year": 1973,
        "summary": (
            "Yugoslavia's opening point was a socialist self-management "
            "economy: enterprises were socially owned and workers' councils "
            "participated in management, while investment and growth also "
            "relied heavily on external credit. The 1974 constitution extended "
            "self-management into macroeconomic coordination. This differs "
            "from conventional state ownership and is not a numeric "
            "market/state score."
        ),
        "sources": [
            {"label": "World Bank Yugoslavia self-management planning study", "url": "https://documents1.worldbank.org/curated/en/870961468778151991/pdf/multi0page.pdf"},
            {"label": "World Bank Yugoslavia economic memorandum", "url": "https://documents1.worldbank.org/curated/en/829701468115129670/pdf/multi-page.pdf"},
        ],
    },
    ("CYP", 2004): {
        "as_of_year": 2004,
        "summary": (
            "At EU accession in 2004, Cyprus was a market economy with a large "
            "services and financial sector, while the island remained divided "
            "and the economy was exposed to external and banking shocks. EU "
            "accession and subsequent euro adoption anchored the island's "
            "economic institutions to the European single market and monetary "
            "union. This is a qualitative starting context, not a numeric "
            "market/state score."
        ),
        "sources": [
            {"label": "European Commission (Cyprus accession timeline)", "url": "https://cyprus.representation.ec.europa.eu/about-us/cyprus-eu_en"},
            {"label": "European Commission (Cyprus and the euro)", "url": "https://economy-finance.ec.europa.eu/euro/eu-countries-and-euro/cyprus-and-euro_en"},
        ],
    },
    ("LTU", 1991): {
        "as_of_year": 1991,
        "summary": (
            "At restored independence in 1991, Lithuania was leaving Soviet "
            "central planning and beginning a rapid transition toward private "
            "ownership, market prices, and open trade. This transition started "
            "from a highly state-directed economy and was accompanied by severe "
            "early output and wage losses. It is a qualitative market/state "
            "starting point, not a numeric score."
        ),
        "sources": [
            {"label": "World Bank (Lithuania: The Transition to a Market Economy)", "url": "https://documents.worldbank.org/en/publication/documents-reports/documentdetail/440411468757199694"},
            {"label": "IMF (Lithuania Article IV, 1996)", "url": "https://www.elibrary.imf.org/view/journals/002/1996/072/article-A001-en.xml"},
        ],
    },
    ("MLT", 2004): {
        "as_of_year": 2004,
        "summary": (
            "At EU accession in 2004, Malta was a small mixed economy with a "
            "substantial parastatal sector, a currency peg, and a programme of "
            "fiscal consolidation and market reform. The state was reducing "
            "direct involvement in selected network industries while adopting "
            "European market rules. This is qualitative context, not a numeric "
            "market/state score."
        ),
        "sources": [
            {"label": "IMF Malta Article IV (2005)", "url": "https://www.elibrary.imf.org/view/journals/002/2005/381/article-A001-en.xml"},
            {"label": "IMF Malta Article IV (2008)", "url": "https://www.imf.org/en/news/articles/2015/09/28/04/52/mcs053008"},
        ],
    },
    ("SVN", 1991): {
        "as_of_year": 1991,
        "summary": (
            "At independence in 1991, Slovenia inherited Yugoslav social "
            "ownership and worker-managed firms rather than a conventional "
            "central state-ownership system. It then used a gradual, hybrid "
            "privatisation process to move enterprises toward private "
            "ownership, while preserving a negotiated social-market approach. "
            "This is a qualitative institutional starting point, not a "
            "numeric market/state score."
        ),
        "sources": [
            {"label": "IMF Slovenia Selected Issues (1998)", "url": "https://www.elibrary.imf.org/view/journals/002/1998/020/article-A001-en.xml"},
            {"label": "Government of Slovenia (key dates)", "url": "https://www.gov.si/en/news/2020-12-22-important-dates-for-slovenia/"},
        ],
    },
    ("SGP", 1959): {
        "as_of_year": 1959,
        "summary": (
            "At self-government in 1959, Singapore was a small entrepôt economy "
            "with high unemployment and a narrow industrial base. The incoming "
            "PAP government pursued rapid industrialisation, public housing and "
            "skills development while keeping the economy open to trade and "
            "foreign investment. The opening point is a state-led but outward-facing "
            "development strategy, not a simple market-versus-state score."
        ),
        "sources": [
            {"label": "Singapore Parliament (historical development and self-government)", "url": "https://www.parliament.gov.sg/history/historical-development"},
            {"label": "SG101 (Singapore economy, 1959-1965)", "url": "https://www.sg101.gov.sg/economy/surviving-our-independence/1959-1965/"},
            {"label": "SG101 (industrialisation after independence)", "url": "https://www.sg101.gov.sg/economy/surviving-our-independence/1965-1970/"},
        ],
    },
    ("USA", 1789): {
        "as_of_year": 1789,
        "summary": (
            "The Constitution's federal government began operating in 1789, "
            "replacing an Articles-era center that could request state funds "
            "but lacked enforcement and interstate-commerce powers. The "
            "opening point is a shift from a weak confederation toward a "
            "stronger federal market and fiscal authority, not an economy-wide "
            "market/state score."
        ),
        "sources": [
            {"label": "National Archives (Articles and Constitution)", "url": "https://www.archives.gov/founding-docs/constitution/how-did-it-happen"},
            {"label": "National Archives (government begins in 1789)", "url": "https://www.archives.gov/founding-docs/constitution-q-and-a"},
        ],
    },
    ("FRA", 1789): {
        "as_of_year": 1789,
        "summary": (
            "At the opening of the coded movement, France's Ancien Régime had "
            "estate and provincial privileges, feudal obligations, and "
            "different regional legal traditions. This is a documented "
            "institutional starting point before the Assembly's 1789 legal "
            "reordering, not a numeric market/state score."
        ),
        "sources": [
            {"label": "French National Assembly (abolition of privileges)", "url": "https://www.assemblee-nationale.fr/dyn/histoire-et-patrimoine/revolution-francaise/nuit-du-4-aout-abolition-des-privileges"},
            {"label": "French National Assembly (unified code and prior legal diversity)", "url": "https://www.assemblee-nationale.fr/dyn/histoire-et-patrimoine/consulat-et-premier-empire/la-codification-juridique"},
        ],
    },
    ("DEU", 1871): {
        "as_of_year": 1871,
        "summary": (
            "Germany's opening point is the Prussian-led federal Empire: the "
            "Bundesrat represented 25 states and the Reichstag legislated and "
            "approved budgets, while the Kaiser-appointed Chancellor and "
            "monarchic executive retained extensive power. This is federal "
            "state formation under a dominant monarchy, not parliamentary "
            "democracy or a numeric market/state score."
        ),
        "sources": [
            {"label": "German Bundestag (Empire and Reichstag powers)", "url": "https://www.bundestag.de/en/parliament/history/parliamentarism/empire"},
            {"label": "German Bundestag (1871 Constitution)", "url": "https://www.bundestag.de/besuche/ausstellungen/verfassung/tafel12"},
        ],
    },
    ("CAN", 1867): {
        "as_of_year": 1867,
        "summary": (
            "Canada's opening coded point is Confederation: several British "
            "North American colonies formed a federal Dominion with powers "
            "divided between Parliament and provinces, still within the British "
            "Empire. Its fiscal base relied primarily on customs and excise; "
            "the federal government's assigned role included expensive "
            "infrastructure, while provinces held responsibilities such as "
            "health, education, and welfare. This describes a market-based "
            "colonial economy with a comparatively limited social-program "
            "state, not a measured market/state score. Indigenous peoples were "
            "excluded from the constitutional bargain and faced later federal "
            "expansion."
        ),
        "sources": [
            {"label": "Library of Parliament (Confederation and federal powers)", "url": "https://lop.parl.ca/staticfiles/Learn/Documents/ParliamentaryPrimer/LOP_TimelineBrochEN.pdf"},
            {"label": "Canada Revenue Agency (federal customs and excise before income tax)", "url": "https://www.canada.ca/en/revenue-agency/services/tax/individuals/educational-programs/purpose-taxes.html"},
        ],
    },
    ("ITA", 1861): {
        "as_of_year": 1861,
        "summary": (
            "Italy's opening coded point is national unification under a "
            "constitutional monarchy and Parliament. The electorate was "
            "narrowly restricted by wealth and status, and national integration "
            "was uneven. This is state-formation context, not a numeric "
            "market/state score."
        ),
        "sources": [
            {"label": "Italian Chamber of Deputies (Parliament and unification)", "url": "https://www.camera.it/application/xmanager/projects/leg17/attachments/pubblicazione/pdfs/000/000/778/Montecitorio_ingl_def.pdf"},
        ],
    },
    ("JPN", 1868): {
        "as_of_year": 1868,
        "summary": (
            "Japan's opening coded point is the Meiji government's Charter "
            "Oath and emerging central administration. Domain governments "
            "were abolished and replaced by prefectures in 1871; the new state "
            "promised deliberative government but remained politically "
            "concentrated. This is institutional context, not a numeric "
            "market/state score."
        ),
        "sources": [
            {"label": "National Diet Library (Meiji constitutional state)", "url": "https://www.ndl.go.jp/modern/e/cha1/"},
            {"label": "National Archives of Japan (domain abolition)", "url": "https://www.archives.go.jp/exhibition/digital/modean_state/contents/return/index.html"},
        ],
    },
    ("ZAF", 1948): {
        "as_of_year": 1948,
        "summary": (
            "The opening point is the National Party's 1948 victory and the "
            "formal turn to apartheid. South Africa had a capitalist economy "
            "with private firms, but the state used law and administration to "
            "allocate political rights, residence, land access, and work along "
            "racial lines. This is a coercive racial-capitalist order, not a "
            "simple free-market or state-ownership starting point."
        ),
        "sources": [
            {"label": "South African Government (history)", "url": "https://www.gov.za/about-sa/history"},
            {"label": "South African Department of Basic Education (apartheid timeline)", "url": "https://www.education.gov.za/LinkClick.aspx?fileticket=oRjFfXEp1Ak%3D&mid=2502&portalid=0&tabid=670"},
        ],
    },
    ("BGD", 1972): {
        "as_of_year": 1972,
        "summary": (
            "At independence, the new government adopted a socialist "
            "development orientation and nationalised scheduled industrial "
            "enterprises through President's Order No. 27. The order also "
            "created public corporations to coordinate those firms and "
            "develop new industry. This shows a strong public-sector role in "
            "industry, not a measured claim that the whole economy was "
            "state-owned."
        ),
        "sources": [
            {"label": "Bangladesh Industrial Enterprises (Nationalisation) Order, 1972", "url": "https://bdlaws.minlaw.gov.bd/act-print-378.html"},
            {"label": "World Bank (1980), Bangladesh: Strategy for Sustained Growth", "url": "https://documents1.worldbank.org/curated/en/375571468152966660/pdf/527080PUB0lead101Official0Use0Only1.pdf"},
        ],
    },
    ("NAM", 1990): {
        "as_of_year": 1990,
        "summary": (
            "Namibia became independent under a multiparty constitution that "
            "protected private property while allowing compensated public-"
            "interest expropriation. The new government expanded access to "
            "services previously restricted to a minority and pursued gradual "
            "land reform. The opening point is a mixed market economy with an "
            "active developmental state, not a nationalisation programme."
        ),
        "sources": [
            {"label": "Constitution of the Republic of Namibia, 1990", "url": "https://namiblii.org/akn/na/act/1990/constitution/eng%402014-10-13"},
            {"label": "World Bank (2013), Namibia Poverty and Inequality Assessment", "url": "https://documents1.worldbank.org/curated/en/193361468058501795/pdf/715150ESW0P1120370077B00PUBLIC00ACS.pdf"},
        ],
    },
    ("PRY", 1954): {
        "as_of_year": 1954,
        "summary": (
            "The opening point is Alfredo Stroessner's coup and the beginning "
            "of a long dictatorship dominated by the Colorado Party and armed "
            "forces. Economic policy still relied substantially on private "
            "enterprise and foreign investment, alongside stabilisation and "
            "state-supported infrastructure. Political authoritarianism here "
            "does not mean comprehensive state ownership or a single "
            "market/state direction."
        ),
        "sources": [
            {"label": "OECD Public Governance Review: Paraguay", "url": "https://www.oecd.org/en/publications/oecd-public-governance-reviews-paraguay_9789264301856-en/full-report/component-5.html"},
            {"label": "World Bank, Paraguay: The Role of the State (Report No. 15044-PA)", "url": "https://documents1.worldbank.org/curated/en/348711468757777070/pdf/multi_page.pdf"},
        ],
    },
    ("LBR", 1980): {
        "as_of_year": 1980,
        "summary": (
            "At this coded opening, a military coup replaced the True Whig "
            "Party government with Doe-led military rule. Liberia remained "
            "a mixed export economy with private firms and foreign investment, "
            "while political control and patronage became concentrated in "
            "the state. Authoritarian politics did not mean comprehensive "
            "state ownership."
        ),
        "sources": [
            {"label": "U.S. Department of State, Liberia background (2004)", "url": "https://2009-2017.state.gov/outofdate/bgn/liberia/40628.htm"},
            {"label": "U.S. Department of State, Liberia relations fact sheet (2019)", "url": "https://2017-2021.state.gov/u-s-relations-with-liberia/"},
        ],
    },
    ("ROU", 1990): {
        "as_of_year": 1990,
        "summary": (
            "Romania entered the post-Ceaușescu transition with a highly "
            "centralised planned economy, dominant state enterprises, "
            "administered prices, and extensive controls over production and "
            "trade. The incoming government opted for gradual liberalisation "
            "and privatisation; government expense was about 33.34% of GDP in "
            "the World Bank series for 1990. This describes a large state role "
            "at the transition baseline, not a measure of state ownership."
        ),
        "sources": [
            {"label": "IMF Romania: Ex-Post Assessment of Longer-Term Program Engagement (2004)", "url": "https://www.elibrary.imf.org/view/journals/002/2004/113/article-A001-en.xml"},
            {"label": "World Bank WDI: Government expense (% of GDP)", "url": "https://data.worldbank.org/indicator/GC.XPN.TOTL.GD.ZS?locations=RO"},
        ],
    },
    ("EST", 1994): {
        "as_of_year": 1994,
        "summary": (
            "Estonia's first coded period began during the rapid shift from "
            "Soviet planning toward a small, open market economy. Early "
            "stabilisation and tax reforms were already under way; government "
            "expense was about 21.64% of GDP in the nearest observed World Bank "
            "year, 1991. The figure is a fiscal-size proxy, while the wider "
            "starting point also includes state-enterprise restructuring and "
            "EU accession alignment."
        ),
        "sources": [
            {"label": "European Commission, Estonia and the EU", "url": "https://estonia.representation.ec.europa.eu/tutvustus/eesti-elis_et"},
            {"label": "European Commission, Estonia and the euro", "url": "https://economy-finance.ec.europa.eu/euro/eu-countries-and-euro/estonia-and-euro_en"},
            {"label": "World Bank WDI: Government expense (% of GDP)", "url": "https://data.worldbank.org/indicator/GC.XPN.TOTL.GD.ZS?locations=EE"},
        ],
    },
    ("LKA", 1977): {
        "as_of_year": 1977,
        "summary": (
            "Sri Lanka's 1977 opening coded point marks a sharp turn away from "
            "the preceding import-substitution and state-control period. The "
            "new government began trade liberalisation, exchange-rate reform, "
            "and incentives for export-oriented foreign investment, while the "
            "state continued to finance infrastructure and provide major "
            "public services. The baseline is an outward-opening mixed economy, "
            "not a minimal-state model."
        ),
        "sources": [
            {"label": "IMF Sri Lanka: Economic Policy Orientation, 1970–2018", "url": "https://www.elibrary.imf.org/view/journals/002/2018/176/article-A001-en.xml"},
            {"label": "IMF Sri Lanka Selected Issues (2018 PDF)", "url": "https://www.imf.org/-/media/files/publications/cr/2018/cr18176.pdf"},
        ],
    },
    ("SYR", 1963): {
        "as_of_year": 1963,
        "summary": (
            "The first coded Syrian movement began with the Ba'ath Party's "
            "rise to power and the introduction of emergency rule. The state "
            "expanded public ownership, planning, and agrarian reform, while "
            "party and security institutions concentrated political authority. "
            "The opening point is a state-led, one-party political economy, "
            "rather than a market-led institutional baseline."
        ),
        "sources": [
            {"label": "World Bank, Syria Economic Monitor: Winter 2022/23", "url": "https://www.worldbank.org/en/country/syria/publication/syria-economic-monitor-winter-2022-2023"},
            {"label": "Hinnebusch, Syria: Revolution from Above (2001)", "url": "https://www.routledge.com/Syria-Revolution-from-Above/Hinnebusch/p/book/9780415267797"},
        ],
    },
    ("UKR", 1991): {
        "as_of_year": 1991,
        "summary": (
            "Independent Ukraine inherited a Soviet planned economy dominated "
            "by state ownership, industrial ministries, and inter-republic "
            "supply chains. The new state faced the transition to private "
            "ownership and market prices alongside output collapse and "
            "monetary instability. This is a state-owned transition baseline, "
            "not an estimate of the later quality of market institutions."
        ),
        "sources": [
            {"label": "IMF Ukraine: Restoring Growth with Equity (1999)", "url": "https://www.imf.org/external/pubs/ft/scr/1999/cr99109.pdf"},
            {"label": "IMF Ukraine: 2005 Article IV and Ex-Post Assessment", "url": "https://www.imf.org/external/pubs/ft/scr/2005/cr05415.pdf"},
        ],
    },
    ("ZMB", 1991): {
        "as_of_year": 1991,
        "summary": (
            "At the 1991 political transition, Zambia began moving from a "
            "state-led economy built around nationalised copper production "
            "toward privatisation and structural adjustment. Copper exports "
            "remained central, and the new government inherited a large debt "
            "burden and major public-enterprise exposure. The starting point "
            "is a market transition from a substantial state-enterprise role, "
            "not a completed liberalisation."
        ),
        "sources": [
            {"label": "World Bank, Zambia development report (2003)", "url": "https://documents.worldbank.org/curated/en/150771468764062902/pdf/261620v-1.pdf"},
            {"label": "World Bank, Zambia Country Economic Memorandum (2024)", "url": "https://www.worldbank.org/en/news/feature/2024/06/10/unlocking-productivity-and-economic-transformation-for-better-jobs-in-afe-zambia"},
        ],
    },
    ("MWI", 1964): {
        "as_of_year": 1964,
        "summary": (
            "At independence, Malawi was predominantly agricultural, with "
            "the state beginning to shape development and crop marketing. "
            "Private estate agriculture and firms coexisted with public "
            "administration and parastatal influence. The opening point is a "
            "politically concentrated, state-directed mixed economy, not a "
            "measured ownership share."
        ),
        "sources": [
            {"label": "World Bank, Malawi country economic memorandum", "url": "https://documents1.worldbank.org/curated/en/473381468270033298/pdf/36862.pdf"},
            {"label": "World Bank, Malawi Fiscal Restructuring and Deregulation Program", "url": "https://documents1.worldbank.org/curated/en/784411468048895989/pdf/multi-page.pdf"},
        ],
    },
    ("ZWE", 1980): {
        "as_of_year": 1980,
        "summary": (
            "Independence opened with a mixed economy: private firms and "
            "commercial agriculture operated alongside inherited controls, "
            "state direction, and an expanded social-service agenda. The "
            "government prioritised redressing social inequities, while price "
            "and foreign-exchange controls remained important. This is a "
            "mixed market/state baseline, not an all-state economy."
        ),
        "sources": [
            {"label": "IMF, Zimbabwe recent economic developments (1997)", "url": "https://www.elibrary.imf.org/view/journals/002/1997/059/article-A001-en.xml"},
            {"label": "IMF, Zimbabwe economic and structural adjustment (1996)", "url": "https://www.elibrary.imf.org/view/journals/002/1996/033/article-A001-en.xml"},
        ],
    },
    ("LBY", 1969): {
        "as_of_year": 1969,
        "summary": (
            "The 1969 revolution established a new republic that later became "
            "the Jamahiriya. Oil resources gave the state a dominant role in "
            "public investment and economic allocation; private activity was "
            "restricted, but the economy was not uniformly state-owned. The "
            "starting point is a strongly state-directed oil economy rather "
            "than a numerical market/state score."
        ),
        "sources": [
            {"label": "United Nations, Member States: Libya", "url": "https://www.un.org/en/about-us/member-states/libya"},
            {"label": "World Bank, Libya: From Privilege to Competition (2006)", "url": "https://documents1.worldbank.org/curated/en/918691468053103808/pdf/30295.pdf"},
        ],
    },
    ("MLI", 1960): {
        "as_of_year": 1960,
        "summary": (
            "At independence, Mali's First Republic adopted scientific "
            "socialism, a planned national economy, and single-party rule. "
            "The state sought to direct production and build national "
            "institutions. This is a strongly state-directed political-economic "
            "starting point; the short period and limited historical accounts "
            "do not support a numeric market/state share."
        ),
        "sources": [
            {"label": "UN Committee on the Rights of the Child, Mali report", "url": "https://digitallibrary.un.org/record/582290/files/CRC_C_MLI_2-EN.pdf"},
            {"label": "UNCTAD, Investment policy review: Mali", "url": "https://digitallibrary.un.org/record/428747/files/poiteiitm24-en.pdf"},
        ],
    },
    ("LVA", 1991): {
        "as_of_year": 1991,
        "summary": (
            "Restored independence began the transition from Soviet central "
            "planning toward a market economy. At the opening point, private "
            "ownership and competitive markets were still being rebuilt; "
            "price, trade, privatisation, and monetary reforms unfolded over "
            "the following decade. This starting context describes a "
            "transition from state planning, not the completed market system."
        ),
        "sources": [
            {"label": "European Commission, Latvia Regular Report (1999)", "url": "https://enlargement.ec.europa.eu/system/files/2016-12/latvia_en.pdf"},
            {"label": "EUR-Lex, Latvia accession evaluation", "url": "https://eur-lex.europa.eu/legal-content/summary/latvia.html"},
        ],
    },
}


def verified_rows(spec: dict) -> dict[str, list[tuple[int, float]]]:
    path = ROOT / spec["path"]
    if not path.is_file():
        raise FileNotFoundError(f"required pinned vintage missing: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"pinned vintage hash mismatch: {spec['path']}")
    frame = pd.read_parquet(path, columns=["country_iso3", "year", spec["column"]])
    frame = frame.dropna(subset=["country_iso3", "year", spec["column"]])
    result: dict[str, list[tuple[int, float]]] = {}
    for row in frame.itertuples(index=False, name=None):
        iso3, year, value = row
        if not isinstance(iso3, str) or len(iso3) != 3:
            continue
        result.setdefault(iso3, []).append((int(year), float(value)))
    for observations in result.values():
        observations.sort()
    return result


def select_observation(
    rows: list[tuple[int, float]], first_year: int
) -> tuple[int, float, str] | None:
    opening = [(year, value) for year, value in rows if first_year - OPENING_WINDOW_YEARS <= year <= first_year]
    if opening:
        year, value = max(opening, key=lambda row: row[0])
        return year, value, "opening"
    later = [(year, value) for year, value in rows if year > first_year]
    if later:
        year, value = min(later, key=lambda row: row[0])
        return year, value, "later_only"
    return None


def public_observation(spec: dict, selected: tuple[int, float, str] | None) -> dict | None:
    if selected is None:
        return None
    year, value, relation = selected
    return {
        "metric_id": spec["metric_id"],
        "label": spec["label"],
        "value": round(value, 2),
        "unit": spec["unit"],
        "transformation": "Rounded to two decimals from the pinned vintage; no interpolation.",
        "observed_year": year,
        "relation_to_first_coded_year": relation,
        "source_url": spec["source_url"],
        "definition_url": spec["definition_url"],
        "publisher": spec["publisher"],
        "license": spec["license"],
        "license_url": spec["license_url"],
        "vintage_file": spec["path"],
        "vintage_sha256": spec["sha256"],
        "caveat": spec["caveat"],
    }


def extract_selected_rows(drift: dict, source_rows: dict[str, dict]) -> dict:
    """Retain only rows needed to reconstruct each displayed observation."""
    countries = {}
    for iso3, country in sorted(drift["countries"].items()):
        first_year = country["first_coded_year"]
        if first_year is None:
            continue
        selected = {}
        for source in SOURCES:
            row = select_observation(source_rows[source].get(iso3, []), first_year)
            selected[source] = {"year": row[0], "value": round(row[1], 8)} if row else None
        countries[iso3] = {"first_coded_year": first_year, "sources": selected}
    return {
        "schema": "ieset-country-drift-observation-extraction-v1",
        "selection": "Latest observation within five years at or before first coded year, otherwise earliest later observation.",
        "pinned_sources": {
            key: {"vintage_file": spec["path"], "vintage_sha256": spec["sha256"], "source_url": spec["source_url"]}
            for key, spec in SOURCES.items()
        },
        "countries": countries,
    }


def rows_from_extraction(extraction: dict, drift: dict) -> dict[str, dict]:
    if extraction.get("schema") != "ieset-country-drift-observation-extraction-v1":
        raise ValueError("unsupported starting-context extraction schema")
    for key, spec in SOURCES.items():
        pinned = extraction.get("pinned_sources", {}).get(key) or {}
        if pinned.get("vintage_file") != spec["path"] or pinned.get("vintage_sha256") != spec["sha256"] or pinned.get("source_url") != spec["source_url"]:
            raise ValueError(f"starting-context extraction source drift: {key}")
    current_years = {
        iso3: country["first_coded_year"]
        for iso3, country in drift["countries"].items()
        if country["first_coded_year"] is not None
    }
    extraction_years = {
        iso3: country["first_coded_year"]
        for iso3, country in extraction.get("countries", {}).items()
    }
    unexpected = set(extraction_years) - set(current_years)
    changed = {
        iso3 for iso3 in set(extraction_years) & set(current_years)
        if extraction_years[iso3] != current_years[iso3]
    }
    if unexpected or changed:
        raise ValueError("first coded years changed; refresh the source extraction")
    rows: dict[str, dict[str, list[tuple[int, float]]]] = {key: {} for key in SOURCES}
    for iso3, country in extraction["countries"].items():
        for key in SOURCES:
            observation = country.get("sources", {}).get(key)
            if observation is not None:
                rows[key][iso3] = [(int(observation["year"]), float(observation["value"]))]
    return rows


def build_context(drift: dict, source_rows: dict[str, dict]) -> dict:
    countries = {}
    for iso3, country in sorted(drift["countries"].items()):
        first_year = country["first_coded_year"]
        if first_year is None:
            continue
        expense = select_observation(source_rows["expense"].get(iso3, []), first_year)
        consumption = select_observation(source_rows["consumption"].get(iso3, []), first_year)
        # Use the fuller fiscal expense measure when it is available at the
        # opening. A consumption opening is preferable to a much later expense.
        if expense and expense[2] == "opening":
            fiscal_spec, fiscal_selected = SOURCES["expense"], expense
        elif consumption and consumption[2] == "opening":
            fiscal_spec, fiscal_selected = SOURCES["consumption"], consumption
        elif expense and consumption:
            # With no opening observation, prefer the earliest dated later
            # reference point. A later expense is not an opening baseline.
            fiscal_spec, fiscal_selected = (
                (SOURCES["expense"], expense)
                if expense[0] <= consumption[0]
                else (SOURCES["consumption"], consumption)
            )
        elif expense:
            fiscal_spec, fiscal_selected = SOURCES["expense"], expense
        else:
            fiscal_spec, fiscal_selected = SOURCES["consumption"], consumption
        market = select_observation(source_rows["wgi_regulatory_quality"].get(iso3, []), first_year)
        countries[iso3] = {
            "first_coded_year": first_year,
            "fiscal": public_observation(fiscal_spec, fiscal_selected),
            "fiscal_note": (
                "The pinned extraction lacks a source row for this country; refresh from the full source vintage when available."
                if iso3 not in source_rows["expense"] and iso3 not in source_rows["consumption"]
                else ""
            ),
            "market_institutions": public_observation(SOURCES["wgi_regulatory_quality"], market),
            "market_institutions_note": (
                "The pinned extraction lacks a source row for this country; refresh from the full source vintage when available."
                if market is None and iso3 not in source_rows["wgi_regulatory_quality"]
                else "No observation in the pinned World Bank Regulatory Quality series."
                if market is None else ""
            ),
            "market_institutions_source_url": SOURCES["wgi_regulatory_quality"]["source_url"],
            "historical_context": HISTORICAL_CONTEXTS.get((iso3, first_year)),
        }
    return {
        "schema": "ieset-country-drift-starting-context-v1",
        "opening_window_years": OPENING_WINDOW_YEARS,
        "method": (
            "A source observation is an opening context only when dated at or "
            "before the first coded movement and within five years. Otherwise "
            "the earliest later observation is explicitly marked later-only. "
            "Fiscal and regulatory-quality levels are separate and do not "
            "offset the movement-direction score."
        ),
        "countries": countries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare regenerated output with checked-in JSON")
    parser.add_argument("--refresh-extraction", action="store_true", help="rebuild the checked-in extraction from verified local vintages")
    parser.add_argument("--verify-vintages", action="store_true", help="compare the extraction to verified local vintages")
    args = parser.parse_args()
    drift = json.loads(DRIFT.read_text())
    if args.refresh_extraction:
        full_rows = {key: verified_rows(spec) for key, spec in SOURCES.items()}
        extraction = extract_selected_rows(drift, full_rows)
        EXTRACTION.parent.mkdir(parents=True, exist_ok=True)
        EXTRACTION.write_text(json.dumps(extraction, indent=2, ensure_ascii=False) + "\n")
    else:
        extraction = json.loads(EXTRACTION.read_text())
    if args.verify_vintages:
        full_rows = {key: verified_rows(spec) for key, spec in SOURCES.items()}
        if extract_selected_rows(drift, full_rows) != extraction:
            raise ValueError("checked-in extraction differs from pinned local vintages")
        print("starting-context extraction verified against pinned local vintages")
    source_rows = rows_from_extraction(extraction, drift)
    output = json.dumps(build_context(drift, source_rows), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != output:
            print(f"stale starting context: {OUTPUT.relative_to(ROOT)}")
            return 1
        print(f"starting context current: {len(drift['countries'])} countries")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output)
    print(f"wrote {OUTPUT.relative_to(ROOT)} for {len(drift['countries'])} countries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
