export const AXIS_LABELS: Record<string, string> = {
  "fiscal.sectoral_subsidy": "Sector subsidies",
  "fiscal.spending_level": "Spending level",
  "fiscal.tax_capital": "Capital taxation",
  "fiscal.tax_corporate": "Corporate taxation",
  "fiscal.tax_progressivity": "Tax progressivity",
  "fiscal.transfer_expansion": "Transfer expansion",
  "institutional.judicial_independence": "Judicial independence",
  "institutional.property_rights": "Property rights",
  "institutional.rule_of_law": "Rule of law",
  "monetary.central_bank_independence": "Central-bank independence",
  "monetary.monetary_expansion_direction": "Monetary expansion",
  "regulatory.energy_supply_security": "Energy supply security",
  "regulatory.environmental_stringency": "Environmental stringency",
  "regulatory.financial_deregulation": "Financial deregulation",
  "regulatory.immigration_openness": "Immigration openness",
  "regulatory.labour_market_flexibility": "Labour-market flexibility",
  "regulatory.product_market_competition": "Product-market competition",
  "regulatory.sectoral_licensing": "Sector licensing",
  "regulatory.trade_openness": "Trade openness",
};

export const AXIS_HINTS: Record<string, string> = {
  "fiscal.sectoral_subsidy": "Direct support, guarantees, industrial aid, or preferential finance for selected sectors.",
  "fiscal.spending_level": "The level or composition of public expenditure.",
  "fiscal.tax_capital": "Taxes on capital gains, wealth, dividends, estates, or financial assets.",
  "fiscal.tax_corporate": "Statutory or effective taxes on business profits.",
  "fiscal.tax_progressivity": "How strongly the tax schedule rises with income or wealth.",
  "fiscal.transfer_expansion": "Cash, in-kind, pension, unemployment, or social-insurance transfers.",
  "institutional.judicial_independence": "Court autonomy, constitutional checks, and legal insulation from executive pressure.",
  "institutional.property_rights": "Security of ownership, contracting, expropriation risk, and asset control.",
  "institutional.rule_of_law": "Governance quality, corruption, arbitrary enforcement, and administrative integrity.",
  "monetary.central_bank_independence": "Institutional insulation of monetary policy from fiscal or political control.",
  "monetary.monetary_expansion_direction": "The direction of money, credit, liquidity, or exchange-rate regime pressure.",
  "regulatory.energy_supply_security": "Reliability, adequacy, and resilience of electricity or fuel supply.",
  "regulatory.environmental_stringency": "Rules, prices, bans, or mandates aimed at environmental outcomes.",
  "regulatory.financial_deregulation": "Restrictions or freedoms in credit, banking, capital markets, or cross-border finance.",
  "regulatory.immigration_openness": "Entry, work, settlement, or asylum restrictions and liberalisations.",
  "regulatory.labour_market_flexibility": "Hiring, firing, hours, wage floors, bargaining, and work-rule flexibility.",
  "regulatory.product_market_competition": "Entry barriers, state monopolies, price controls, privatisation, and competition.",
  "regulatory.sectoral_licensing": "Occupational, professional, industrial, or sector-specific licensing constraints.",
  "regulatory.trade_openness": "Tariffs, quotas, trade agreements, sanctions, and import/export openness.",
};

export const COUNTRY_LABELS: Record<string, string> = {
  AFG: "Afghanistan",
  ARE: "United Arab Emirates",
  ARG: "Argentina",
  AUS: "Australia",
  AUT: "Austria",
  BEL: "Belgium",
  BGD: "Bangladesh",
  BHR: "Bahrain",
  BOL: "Bolivia",
  BRA: "Brazil",
  BWA: "Botswana",
  CAN: "Canada",
  CHE: "Switzerland",
  CHL: "Chile",
  CHN: "China",
  COL: "Colombia",
  CSK: "Czechoslovakia",
  CUB: "Cuba",
  CZE: "Czechia",
  DEU: "Germany",
  DNK: "Denmark",
  ECU: "Ecuador",
  EGY: "Egypt",
  ERI: "Eritrea",
  ESP: "Spain",
  EST: "Estonia",
  ETH: "Ethiopia",
  FIN: "Finland",
  FRA: "France",
  GBR: "United Kingdom",
  GHA: "Ghana",
  GRC: "Greece",
  HUN: "Hungary",
  IDN: "Indonesia",
  IND: "India",
  IRL: "Ireland",
  IRN: "Iran",
  ISR: "Israel",
  ITA: "Italy",
  JPN: "Japan",
  KEN: "Kenya",
  KHM: "Cambodia",
  KOR: "South Korea",
  KWT: "Kuwait",
  LBN: "Lebanon",
  LBY: "Libya",
  LKA: "Sri Lanka",
  LUX: "Luxembourg",
  MEX: "Mexico",
  MYS: "Malaysia",
  NGA: "Nigeria",
  NIC: "Nicaragua",
  NLD: "Netherlands",
  NOR: "Norway",
  NZL: "New Zealand",
  OMN: "Oman",
  PAK: "Pakistan",
  PER: "Peru",
  PHL: "Philippines",
  POL: "Poland",
  PRK: "North Korea",
  PRT: "Portugal",
  PRY: "Paraguay",
  QAT: "Qatar",
  ROU: "Romania",
  RUS: "Russia",
  RWA: "Rwanda",
  SAU: "Saudi Arabia",
  SGP: "Singapore",
  SLV: "El Salvador",
  SUN: "Soviet Union",
  SVK: "Slovakia",
  SWE: "Sweden",
  THA: "Thailand",
  TLS: "Timor-Leste",
  TUR: "Turkiye",
  TWN: "Taiwan",
  TZA: "Tanzania",
  UGA: "Uganda",
  URY: "Uruguay",
  USA: "United States",
  VEN: "Venezuela",
  VNM: "Vietnam",
  YUG: "Yugoslavia",
  ZAF: "South Africa",
  ZMB: "Zambia",
  ZWE: "Zimbabwe",
};

export const POSTURE_LABELS: Record<string, string> = {
  promising: "Promising evidence",
  mixed: "Mixed / context-dependent",
  caution: "Caution signal",
  evidence_gap: "Evidence gap",
};

export const EVIDENCE_STRENGTH_LABELS: Record<string, string> = {
  strong: "Strong design",
  moderate: "Moderate design",
  screening: "Screening signal",
  unresolved: "Unresolved",
};

export const EVIDENCE_STRENGTH_HINTS: Record<string, string> = {
  strong: "Causal or quasi-causal design, such as synthetic control, DiD, event study, or local projections.",
  moderate: "Panel, decomposition, or multi-metric design useful for triangulation but less dispositive.",
  screening: "Descriptive or cross-sectional screen. Useful for triage, not enough alone for strong causal claims.",
  unresolved: "Missing, inconclusive, blocked, or not yet interpretable evidence.",
};

export function axisLabel(axis: string): string {
  return AXIS_LABELS[axis] ?? titleize(axis);
}

export function axisHint(axis: string): string {
  return AXIS_HINTS[axis] ?? axis;
}

export function countryLabel(code: string): string {
  const label = COUNTRY_LABELS[code];
  return label ? `${label} (${code})` : code;
}

export function countryShortLabel(code: string): string {
  return COUNTRY_LABELS[code] ?? code;
}

export function postureLabel(posture: string): string {
  return POSTURE_LABELS[posture] ?? titleize(posture);
}

export function evidenceStrengthLabel(strength: string): string {
  return EVIDENCE_STRENGTH_LABELS[strength] ?? titleize(strength);
}

export function evidenceStrengthHint(strength: string): string {
  return EVIDENCE_STRENGTH_HINTS[strength] ?? strength;
}

export function directionLabel(direction: string): string {
  if (direction === "+") return "higher";
  if (direction === "-") return "lower";
  if (direction === "0") return "no clear move";
  if (direction === "mixed") return "mixed";
  return direction || "unspecified";
}

export function directionGlyph(direction: string): string {
  if (direction === "+") return "+";
  if (direction === "-") return "-";
  if (direction === "0") return "0";
  if (direction === "mixed") return "+/-";
  return "?";
}

export function linkTypeLabel(linkType?: string): string {
  if (linkType === "explicit") return "direct link";
  if (linkType === "inferred") return "inferred analogue";
  if (linkType === "legacy") return "legacy link";
  return "unclassified link";
}

function titleize(value: string): string {
  return value
    .replace(/[._-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();
}
