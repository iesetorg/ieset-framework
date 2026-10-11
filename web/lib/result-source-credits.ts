/** Publisher credits for newly public source-locked result families. */
export interface ResultSourceCredit {
  publisher: string;
  citation: string;
  sourceUrl: string;
  rightsUrl: string;
  custodyNote?: string;
}

const WEATHER_PRICE_CREDITS: ResultSourceCredit[] = [
  {
    publisher: "FAO",
    citation:
      "FAO (2025), FAOSTAT: Agricultural producer prices, December 2025 update. IESET source archive accessed 2 May 2026. Licence: CC BY 4.0.",
    sourceUrl: "https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1",
    rightsUrl: "https://www.fao.org/contact-us/terms/db-terms-of-use/en",
    custodyNote:
      "All admitted producer price index rows carry FAO's E (estimated) flag. Third-party terms can still apply to underlying dataset inputs and must be checked in the publisher metadata.",
  },
  {
    publisher: "World Bank CCKP",
    citation:
      "World Bank Climate Change Knowledge Portal, CRU TS4.10 historical annual country temperature and precipitation. IESET raw-source snapshot 10 October 2026. Licence: CC BY 4.0; credit also to CRU, University of East Anglia and the UK Met Office.",
    sourceUrl: "https://climateknowledgeportal.worldbank.org/download-data",
    rightsUrl: "https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
  },
];

const REER_STAN_CREDITS: ResultSourceCredit[] = [
  {
    publisher: "BIS",
    citation:
      "Bank for International Settlements, effective exchange rates (WS_EER), monthly real broad-basket series. IESET source fetched 23 July 2026.",
    sourceUrl: "https://data.bis.org/topics/WS_EER",
    rightsUrl: "https://www.bis.org/about/legal/permitted-use-statistics",
  },
  {
    publisher: "OECD",
    citation:
      "OECD, Structural Analysis (STAN) database, dataflow OECD.STI.PIE:DSD_STAN@DF_STAN(1.0). IESET's partial local source cache is dated 2 May 2026 and contains 2015–2019 keys; its original fetch manifest is unavailable.",
    sourceUrl: "https://www.oecd.org/en/data/datasets/structural-analysis-database.html",
    rightsUrl: "https://www.oecd.org/en/about/terms-conditions.html",
    custodyNote:
      "OECD data can carry third-party restrictions; the exact rights metadata for this partial local extract have not been independently reconstructed.",
  },
];

const WDI_RIGHTS_URL = "https://data.worldbank.org/summary-terms-of-use";
const EUROSTAT_RIGHTS_URL = "https://ec.europa.eu/eurostat/help/copyright-notice";
const CEPII_RIGHTS_URL = "https://www.etalab.gouv.fr/wp-content/uploads/2018/11/open-licence.pdf";

function wdiCredit(indicator: string, fetched: string): ResultSourceCredit {
  return {
    publisher: `World Bank WDI (${indicator})`,
    citation: `The World Bank, World Development Indicators, ${indicator}. IESET source fetched ${fetched}. Licence: CC BY 4.0 unless indicator metadata states otherwise.`,
    sourceUrl: `https://data.worldbank.org/indicator/${indicator}`,
    rightsUrl: WDI_RIGHTS_URL,
    custodyNote: "IESET uses transformed source series in its own statistical analysis; the World Bank does not endorse the result.",
  };
}

function eurostatCredit(datacode: string, fetched: string): ResultSourceCredit {
  return {
    publisher: `Eurostat (${datacode})`,
    citation: `Eurostat, dataset ${datacode}. IESET source fetched ${fetched}. IESET filters and transforms the source data for this analysis; Eurostat is not responsible for the resulting estimates.`,
    sourceUrl: `https://ec.europa.eu/eurostat/databrowser/view/${datacode}`,
    rightsUrl: EUROSTAT_RIGHTS_URL,
    custodyNote: "Eurostat's reuse notice calls for source acknowledgement and a clear modification statement; source-specific exceptions still apply.",
  };
}

const CEPII_GRAVITY_CREDIT: ResultSourceCredit = {
  publisher: "CEPII Gravity",
  citation:
    "Conte, M., P. Cotterlaz and T. Mayer (2022), The CEPII Gravity database, CEPII Working Paper 2022-05, dataset V202211. IESET source archive processed 15 May 2026. Licence: Etalab Open Licence 2.0.",
  sourceUrl: "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8",
  rightsUrl: CEPII_RIGHTS_URL,
  custodyNote: "IESET derives country-year exposures or event indicators from the CEPII country-pair data; CEPII does not endorse these results.",
};

const CEPII_BACI_CREDIT: ResultSourceCredit = {
  publisher: "CEPII BACI",
  citation:
    "Gaulier, G. and S. Zignago (2010), BACI: International Trade Database at the Product-Level, CEPII Working Paper 2010-23. This result uses the tradeflow_baci field included in CEPII Gravity V202211.",
  sourceUrl: "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37",
  rightsUrl: CEPII_RIGHTS_URL,
};

const WITS_HS6_CREDIT: ResultSourceCredit = {
  publisher: "World Bank WITS",
  citation:
    "World Bank, World Integrated Trade Solution (WITS), TradeStatsTrade indicator NMBR-XPRT-HS6-PRDCT (number of exported HS6 products). IESET source fetched 23 July 2026.",
  sourceUrl:
    "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/all/year/1988-2023/indicator/NMBR-XPRT-HS6-PRDCT",
  rightsUrl: "https://wits.worldbank.org/WITS/wits/registration/TermsAndCondtions.aspx",
  custodyNote:
    "The result reports a statistical estimate, not the WITS source panel. WITS notes restrictions on redistribution of underlying UN Comtrade data.",
};

const CEPII_WDI_CREDITS: Record<string, ResultSourceCredit[]> = {
  cepii_foreign_market_potential_trade_open_change_holdout_2026: [
    wdiCredit("NE.TRD.GNFS.ZS", "5 May 2026"),
    wdiCredit("NY.GDP.PCAP.KD", "5 May 2026"),
  ],
  cepii_fta_market_potential_private_investment_change_holdout_2026: [
    wdiCredit("NE.GDI.FPRV.ZS", "30 April 2026"),
    wdiCredit("NY.GDP.PCAP.KD", "5 May 2026"),
  ],
  cepii_fta_partner_gdp_hightech_export_change_holdout_2026: [
    wdiCredit("TX.VAL.TECH.MF.ZS", "5 May 2026"),
    wdiCredit("NY.GDP.PCAP.KD", "5 May 2026"),
  ],
  cepii_new_fta_partners_manufactures_share_forward_2026: [
    wdiCredit("TX.VAL.MANF.ZS.UN", "30 April 2026"),
  ],
};

const CEPII_GRAVITY_IDS = new Set([
  "cepii_foreign_market_potential_trade_open_change_holdout_2026",
  "cepii_fta_market_potential_private_investment_change_holdout_2026",
  "cepii_fta_partner_gdp_hightech_export_change_holdout_2026",
  "cepii_new_fta_partners_manufactures_share_forward_2026",
  "cepii_rta_partner_expansion_export_hs6_change_2026",
  "korea_us_fta_bilateral_exports_2012_v2",
]);

export function resultSourceCredits(hypothesisId: string): ResultSourceCredit[] {
  if (/^cckp_faostat_crop\d+_(?:temperature|precipitation)_forward_ppi_2026$/.test(hypothesisId)) {
    return WEATHER_PRICE_CREDITS;
  }
  if (/^bis_reer_stan_/.test(hypothesisId)) {
    return REER_STAN_CREDITS;
  }
  const labour = /^wdi_internet_eurostat_(activity|employment)_(?:nat|for)_[mf]_\d{2}_\d{2}_forward_2026$/.exec(hypothesisId);
  if (labour) {
    return [
      wdiCredit("IT.NET.USER.ZS", "5 May 2026"),
      eurostatCredit(labour[1] === "activity" ? "lfsa_argan" : "lfsa_ergan", "30 April 2026"),
    ];
  }
  if (/^wdi_growth_eurostat_immigration_citizenship_[a-z]{2}_forward_2026$/.test(hypothesisId)) {
    return [
      wdiCredit("NY.GDP.PCAP.KD", "5 May 2026"),
      eurostatCredit("migr_imm1ctz", "5 May 2026"),
    ];
  }
  if (CEPII_GRAVITY_IDS.has(hypothesisId)) {
    return [
      CEPII_GRAVITY_CREDIT,
      ...(CEPII_WDI_CREDITS[hypothesisId] ?? []),
      ...(hypothesisId === "korea_us_fta_bilateral_exports_2012_v2" ? [CEPII_BACI_CREDIT] : []),
      ...(hypothesisId === "cepii_rta_partner_expansion_export_hs6_change_2026" ? [WITS_HS6_CREDIT] : []),
    ];
  }
  return [];
}
