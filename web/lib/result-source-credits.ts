/** Publisher credits for the two newly public source-locked calibration families. */
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
      "The admitted producer price index rows include FAO estimated and external-source flags; third-party terms can apply to underlying inputs.",
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

export function resultSourceCredits(hypothesisId: string): ResultSourceCredit[] {
  if (/^cckp_faostat_crop\d+_(?:temperature|precipitation)_forward_ppi_2026$/.test(hypothesisId)) {
    return WEATHER_PRICE_CREDITS;
  }
  if (/^bis_reer_stan_/.test(hypothesisId)) {
    return REER_STAN_CREDITS;
  }
  return [];
}
