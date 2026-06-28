import type { PolicyBrowserClientRow } from "@/lib/policy-browser";
import { COUNTRY_LABELS } from "@/lib/policy-labels";

export interface PolicyQueryAxisMove {
  axis: string;
  direction: string;
  magnitude: "strong" | "moderate" | "weak";
  reason: string;
  sourceIntentId: string;
  sourceIntentLabel: string;
  confidence: number;
}

export interface PolicyQueryIntent {
  id: string;
  label: string;
  confidence: number;
  matchedTerms: string[];
  axes: PolicyQueryAxisMove[];
}

export interface PolicyQueryCountryHint {
  code: string;
  label: string;
}

export interface PolicyQueryAnalysis {
  raw: string;
  cleaned: string;
  normalized: string;
  tokens: string[];
  anchorTerms: string[];
  searchTerms: string[];
  intents: PolicyQueryIntent[];
  axes: PolicyQueryAxisMove[];
  countryHints: PolicyQueryCountryHint[];
  isAnnouncementLike: boolean;
  hasSemanticSignal: boolean;
}

export interface PolicyQueryMatchedAxis {
  axis: string;
  queryDirection: string;
  rowDirection: string;
  sameDirection: boolean;
  intentLabel: string;
}

export interface PolicyQueryMatch {
  score: number;
  axisScore: number;
  textScore: number;
  evidenceScore: number;
  countryScore: number;
  matchedAxes: PolicyQueryMatchedAxis[];
  matchedTerms: string[];
  matchedCountries: string[];
}

interface QueryIntentDefinition {
  id: string;
  label: string;
  keywords: string[];
  patterns?: RegExp[];
  axes: Omit<PolicyQueryAxisMove, "sourceIntentId" | "sourceIntentLabel" | "confidence">[];
}

export const POLICY_QUERY_EXAMPLES = [
  {
    label: "rent controls",
    query: "rent caps and rent control for landlords",
  },
  {
    label: "price controls",
    query: "cap fuel and grocery prices to stop inflation",
  },
  {
    label: "market liberalisation",
    query: "liberalize markets, cut red tape, and open entry to competition",
  },
  {
    label: "state ownership",
    query: "bring energy and rail into public ownership",
  },
  {
    label: "green regulations",
    query: "net-zero climate rules, emissions caps, and renewable mandates",
  },
] as const;

const STOP_WORDS = new Set([
  "about",
  "after",
  "again",
  "against",
  "also",
  "and",
  "are",
  "because",
  "been",
  "being",
  "but",
  "can",
  "cannot",
  "could",
  "does",
  "for",
  "from",
  "has",
  "have",
  "into",
  "its",
  "more",
  "new",
  "not",
  "now",
  "our",
  "over",
  "policy",
  "politician",
  "should",
  "than",
  "that",
  "the",
  "their",
  "them",
  "there",
  "this",
  "through",
  "tweet",
  "under",
  "will",
  "with",
  "would",
  "you",
]);

const ANNOUNCEMENT_PATTERNS = [
  /\b(i|we|our government|my administration|the government)\b.{0,80}\b(will|plan|plans|pledge|pledges|promise|announces|announce|introduce|ban|cap|cut|raise|lower|nationalize|nationalise|liberalize|liberalise)\b/,
  /\b(today|tomorrow|next year|in government|if elected|day one)\b.{0,80}\b(we|i|our|plan|pledge|promise|announce|introduce)\b/,
];

const INTENT_DEFINITIONS: QueryIntentDefinition[] = [
  {
    id: "rent_control",
    label: "Rent or housing price control",
    keywords: [
      "rent control",
      "rent controls",
      "rent cap",
      "rent caps",
      "cap rents",
      "capped rents",
      "rent freeze",
      "freeze rents",
      "maximum rent",
      "rent ceiling",
      "tenant price cap",
    ],
    patterns: [
      /\b(rent|rents|rental|landlord|landlords|tenant|tenants|housing)\b.{0,48}\b(cap|caps|capped|freeze|freezes|control|controls|ceiling|maximum|limit|limits)\b/,
      /\b(cap|caps|capped|freeze|freezes|control|controls|ceiling|maximum|limit|limits)\b.{0,48}\b(rent|rents|rental|landlord|landlords|tenant|tenants|housing)\b/,
    ],
    axes: [
      {
        axis: "regulatory.product_market_competition",
        direction: "-",
        magnitude: "strong",
        reason: "Administered rents are a price-control move in a product market.",
      },
      {
        axis: "regulatory.sectoral_licensing",
        direction: "+",
        magnitude: "moderate",
        reason: "Rent-control regimes usually add sector-specific housing rules.",
      },
    ],
  },
  {
    id: "price_control",
    label: "Price control",
    keywords: [
      "price control",
      "price controls",
      "price cap",
      "price caps",
      "cap prices",
      "capped prices",
      "price freeze",
      "freeze prices",
      "maximum price",
      "administered price",
      "anti price gouging",
      "anti gouging",
      "fuel cap",
      "energy price cap",
      "grocery price cap",
    ],
    patterns: [
      /\b(price|prices|fuel|energy|gas|electricity|utility|utilities|food|grocery|groceries)\b.{0,48}\b(cap|caps|capped|freeze|freezes|control|controls|ceiling|maximum|limit|limits|gouging)\b/,
      /\b(cap|caps|capped|freeze|freezes|control|controls|ceiling|maximum|limit|limits)\b.{0,48}\b(price|prices|fuel|energy|gas|electricity|utility|utilities|food|grocery|groceries)\b/,
    ],
    axes: [
      {
        axis: "regulatory.product_market_competition",
        direction: "-",
        magnitude: "strong",
        reason: "Price caps reduce market price-setting and competition signals.",
      },
    ],
  },
  {
    id: "price_liberalization",
    label: "Price liberalisation",
    keywords: [
      "price liberalization",
      "price liberalisation",
      "liberalize prices",
      "liberalise prices",
      "free prices",
      "free up prices",
      "remove price controls",
      "abolish price controls",
      "end price controls",
    ],
    patterns: [
      /\b(remove|abolish|scrap|end|lift)\b.{0,40}\b(price control|price controls|price cap|price caps)\b/,
      /\b(price|prices)\b.{0,40}\b(liberalize|liberalise|liberalized|liberalised|free|freed|market based)\b/,
    ],
    axes: [
      {
        axis: "regulatory.product_market_competition",
        direction: "+",
        magnitude: "strong",
        reason: "Removing price controls restores market price-setting.",
      },
    ],
  },
  {
    id: "market_liberalization",
    label: "Market liberalisation or deregulation",
    keywords: [
      "market liberalization",
      "market liberalisation",
      "market liberization",
      "deregulate",
      "deregulation",
      "liberalize markets",
      "liberalise markets",
      "open competition",
      "open the market",
      "cut red tape",
      "slash red tape",
      "remove barriers",
      "lower barriers",
      "entry reform",
      "permit reform",
      "licensing reform",
      "delicensing",
    ],
    patterns: [
      /\b(deregulate|deregulation|liberalize|liberalise|liberalized|liberalised|liberization|delicense|delicensing)\b/,
      /\b(cut|slash|reduce|remove|lower)\b.{0,36}\b(red tape|barriers|permits|licences|licenses|licensing|entry barriers)\b/,
      /\b(open|free)\b.{0,30}\b(market|markets|competition|entry)\b/,
    ],
    axes: [
      {
        axis: "regulatory.product_market_competition",
        direction: "+",
        magnitude: "strong",
        reason: "Lower entry barriers and deregulation are competition-friendly moves.",
      },
      {
        axis: "regulatory.sectoral_licensing",
        direction: "-",
        magnitude: "moderate",
        reason: "Permit and licensing reform loosens sector-specific entry gates.",
      },
    ],
  },
  {
    id: "privatization",
    label: "Privatisation",
    keywords: [
      "privatization",
      "privatisation",
      "privatize",
      "privatise",
      "sell state assets",
      "sell public assets",
      "private ownership",
      "asset sale",
      "state divestment",
    ],
    patterns: [
      /\b(privatize|privatise|privatization|privatisation|private ownership|state divestment)\b/,
      /\b(sell|sell off|divest)\b.{0,36}\b(state assets|public assets|state owned|government owned)\b/,
    ],
    axes: [
      {
        axis: "institutional.property_rights",
        direction: "+",
        magnitude: "moderate",
        reason: "Privatisation moves assets toward private ownership and control.",
      },
      {
        axis: "regulatory.product_market_competition",
        direction: "+",
        magnitude: "moderate",
        reason: "Privatisation often exposes incumbents to more competition.",
      },
      {
        axis: "regulatory.sectoral_licensing",
        direction: "-",
        magnitude: "weak",
        reason: "Many privatisation packages loosen state-controlled entry.",
      },
    ],
  },
  {
    id: "state_ownership",
    label: "State ownership or nationalisation",
    keywords: [
      "state ownership",
      "public ownership",
      "state owenership",
      "nationalization",
      "nationalisation",
      "nationalize",
      "nationalise",
      "renationalize",
      "renationalise",
      "state owned",
      "state-owned",
      "government owned",
      "public enterprise",
      "state enterprise",
      "bring into public ownership",
      "take public",
      "expropriate",
      "expropriation",
    ],
    patterns: [
      /\b(nationalize|nationalise|nationalized|nationalised|renationalize|renationalise|expropriate|expropriation)\b/,
      /\b(public|state|government)\b.{0,20}\b(ownership|owned|enterprise|control)\b/,
      /\b(bring|take)\b.{0,36}\b(public ownership|state ownership|under public control|under state control)\b/,
    ],
    axes: [
      {
        axis: "institutional.property_rights",
        direction: "-",
        magnitude: "strong",
        reason: "Nationalisation and state ownership reduce private control over assets.",
      },
      {
        axis: "regulatory.product_market_competition",
        direction: "-",
        magnitude: "moderate",
        reason: "State ownership often reduces product-market contestability.",
      },
      {
        axis: "regulatory.sectoral_licensing",
        direction: "+",
        magnitude: "moderate",
        reason: "State ownership normally increases sector-specific state gating.",
      },
    ],
  },
  {
    id: "green_regulation",
    label: "Green regulation",
    keywords: [
      "green regulation",
      "green regulations",
      "climate regulation",
      "climate rules",
      "environmental regulation",
      "environmental standards",
      "emissions cap",
      "emission cap",
      "carbon price",
      "carbon tax",
      "net zero",
      "renewable mandate",
      "clean energy standard",
      "ev mandate",
      "phase out coal",
      "phaseout coal",
      "fossil fuel ban",
      "green deal",
    ],
    patterns: [
      /\b(carbon price|carbon tax|emissions? cap|net zero|renewable mandate|clean energy standard|ev mandate|green deal)\b/,
      /\b(climate|environmental|green|emissions?|fossil fuel|coal|gas boilers?)\b.{0,48}\b(rule|rules|regulation|regulations|standard|standards|ban|mandate|cap|phase out|phaseout)\b/,
    ],
    axes: [
      {
        axis: "regulatory.environmental_stringency",
        direction: "+",
        magnitude: "strong",
        reason: "Climate standards, caps, bans, or carbon prices raise environmental stringency.",
      },
    ],
  },
  {
    id: "green_subsidy",
    label: "Green industrial subsidy",
    keywords: [
      "green subsidy",
      "green subsidies",
      "clean energy subsidy",
      "renewable subsidy",
      "green tax credit",
      "clean energy tax credit",
      "green industrial policy",
      "green hydrogen subsidy",
      "battery subsidy",
    ],
    patterns: [
      /\b(green|clean energy|renewable|battery|hydrogen|solar|wind)\b.{0,48}\b(subsidy|subsidies|tax credit|tax credits|industrial policy|grant|grants)\b/,
    ],
    axes: [
      {
        axis: "regulatory.environmental_stringency",
        direction: "+",
        magnitude: "moderate",
        reason: "Green subsidies are attached to environmental objectives.",
      },
      {
        axis: "fiscal.sectoral_subsidy",
        direction: "+",
        magnitude: "strong",
        reason: "Targeted green aid expands sectoral subsidies.",
      },
    ],
  },
  {
    id: "trade_liberalization",
    label: "Trade liberalisation",
    keywords: [
      "free trade",
      "trade liberalization",
      "trade liberalisation",
      "lower tariffs",
      "cut tariffs",
      "remove tariffs",
      "free trade agreement",
      "fta",
      "open trade",
    ],
    patterns: [
      /\b(free trade|trade liberalization|trade liberalisation|open trade|free trade agreement)\b/,
      /\b(cut|lower|remove|abolish|scrap|reduce)\b.{0,30}\b(tariff|tariffs|quotas|import barriers)\b/,
    ],
    axes: [
      {
        axis: "regulatory.trade_openness",
        direction: "+",
        magnitude: "strong",
        reason: "Lower tariffs and FTAs increase trade openness.",
      },
    ],
  },
  {
    id: "protectionism",
    label: "Tariffs or protectionism",
    keywords: [
      "tariff",
      "tariffs",
      "import tariff",
      "raise tariffs",
      "protect domestic industry",
      "import quota",
      "trade protection",
      "protectionism",
      "import ban",
    ],
    patterns: [
      /\b(raise|increase|impose|new)\b.{0,30}\b(tariff|tariffs|import duties|duties|quotas)\b/,
      /\b(protectionism|trade protection|import ban|import quota|protect domestic industry)\b/,
    ],
    axes: [
      {
        axis: "regulatory.trade_openness",
        direction: "-",
        magnitude: "strong",
        reason: "Tariffs, quotas, and import bans reduce trade openness.",
      },
    ],
  },
  {
    id: "minimum_wage",
    label: "Minimum wage or wage floor",
    keywords: [
      "minimum wage",
      "wage floor",
      "living wage",
      "raise wages by law",
      "statutory wage",
      "wage mandate",
    ],
    patterns: [
      /\b(minimum wage|wage floor|living wage|statutory wage|wage mandate)\b/,
      /\b(raise|increase|mandate)\b.{0,30}\b(wages|pay)\b/,
    ],
    axes: [
      {
        axis: "regulatory.labour_market_flexibility",
        direction: "-",
        magnitude: "moderate",
        reason: "A higher statutory wage floor makes labour-market rules less flexible.",
      },
    ],
  },
];

const INTENT_ANCHOR_TERMS: Record<string, string[]> = {
  rent_control: [
    "rent",
    "rents",
    "rental",
    "landlord",
    "tenant",
    "housing",
    "price control",
    "price controls",
    "price cap",
    "price caps",
    "price freeze",
  ],
  price_control: [
    "price control",
    "price controls",
    "price cap",
    "price caps",
    "price freeze",
    "administered price",
    "wage price controls",
    "fuel cap",
    "energy price cap",
    "grocery price",
  ],
  price_liberalization: [
    "price liberalization",
    "price controls",
    "price reform",
    "market prices",
    "liberalize prices",
  ],
  market_liberalization: [
    "liberalization",
    "deregulation",
    "deregulate",
    "liberalize",
    "delicensing",
    "market reform",
    "entry reform",
    "free zone",
    "red tape",
  ],
  privatization: [
    "privatization",
    "privatize",
    "private ownership",
    "asset sale",
    "divestment",
    "state assets",
  ],
  state_ownership: [
    "nationalization",
    "nationalize",
    "state ownership",
    "public ownership",
    "state owned",
    "government owned",
    "public enterprise",
    "state enterprise",
    "expropriation",
  ],
  green_regulation: [
    "climate",
    "emissions",
    "emission",
    "carbon",
    "renewable",
    "environmental",
    "green",
    "net zero",
    "clean energy",
    "fossil fuel",
  ],
  green_subsidy: [
    "green subsidy",
    "clean energy",
    "renewable",
    "battery",
    "hydrogen",
    "solar",
    "wind",
    "tax credit",
  ],
  trade_liberalization: [
    "free trade",
    "trade liberalization",
    "tariff",
    "tariffs",
    "free trade agreement",
    "trade openness",
    "customs union",
  ],
  protectionism: [
    "tariff",
    "tariffs",
    "import quota",
    "import ban",
    "protectionism",
    "trade protection",
  ],
  minimum_wage: [
    "minimum wage",
    "wage floor",
    "living wage",
    "statutory wage",
    "wage mandate",
  ],
};

const COUNTRY_ALIASES: Record<string, string> = {
  america: "USA",
  american: "USA",
  britain: "GBR",
  british: "GBR",
  england: "GBR",
  uae: "ARE",
  uk: "GBR",
  "u k": "GBR",
  unitedstates: "USA",
  "united states": "USA",
  us: "USA",
  usa: "USA",
};

function normalizeText(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/[@#]\w+/g, " ")
    .replace(/&/g, " and ")
    .replace(/[’']/g, "")
    .toLowerCase()
    .replace(/\bliberalisation\b/g, "liberalization")
    .replace(/\bliberalise(d|s|r|rs)?\b/g, "liberalize")
    .replace(/\bliberisation\b/g, "liberalization")
    .replace(/\bliberization\b/g, "liberalization")
    .replace(/\bprivatisation\b/g, "privatization")
    .replace(/\bprivatise(d|s|r|rs)?\b/g, "privatize")
    .replace(/\bnationalisation\b/g, "nationalization")
    .replace(/\bnationalise(d|s|r|rs)?\b/g, "nationalize")
    .replace(/\bowenership\b/g, "ownership")
    .replace(/\bpolciy\b/g, "policy")
    .replace(/\bpolciies\b/g, "policies")
    .replace(/[^a-z0-9.+-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function containsPhrase(text: string, phrase: string): boolean {
  const normalizedPhrase = normalizeText(phrase);
  if (!normalizedPhrase) return false;
  const pattern = new RegExp(`(?:^| )${escapeRegExp(normalizedPhrase).replace(/\s+/g, "\\s+")}(?: |$)`);
  return pattern.test(text);
}

function containsWord(text: string, word: string): boolean {
  const normalizedWord = normalizeText(word);
  if (!normalizedWord) return false;
  return new RegExp(`(?:^| )${escapeRegExp(normalizedWord)}(?: |$)`).test(text);
}

function tokenize(normalized: string): string[] {
  return normalized
    .split(" ")
    .map((token) => token.trim())
    .filter((token) => token.length >= 3 && !STOP_WORDS.has(token))
    .slice(0, 80);
}

function compactUnique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function magnitudeWeight(magnitude?: string): number {
  if (magnitude === "strong") return 1.2;
  if (magnitude === "moderate") return 1;
  if (magnitude === "weak") return 0.75;
  return 0.9;
}

function strengthWeight(strength?: string): number {
  if (strength === "strong") return 4;
  if (strength === "moderate") return 3;
  if (strength === "screening") return 1.5;
  return 0;
}

function rowOwnText(row: PolicyBrowserClientRow): string {
  return normalizeText(
    [
      row.policy_id,
      row.title,
      row.description ?? "",
      row.countries.join(" "),
      row.axes.map((axis) => axis.axis).join(" "),
    ].join(" ")
  );
}

function rowEvidenceText(row: PolicyBrowserClientRow): string {
  return normalizeText(
    [
      row.schools.join(" "),
      row.search_terms.join(" "),
      row.top_hypotheses.map((h) => h.hypothesis_id).join(" "),
      row.top_hypotheses.map((h) => h.topic).join(" "),
      row.top_hypotheses.map((h) => h.claim ?? "").join(" "),
    ].join(" ")
  );
}

function analyzeCountries(normalized: string): PolicyQueryCountryHint[] {
  const hints: PolicyQueryCountryHint[] = [];

  for (const [alias, code] of Object.entries(COUNTRY_ALIASES)) {
    if (containsPhrase(normalized, alias)) {
      hints.push({ code, label: COUNTRY_LABELS[code] ?? code });
    }
  }

  for (const [code, label] of Object.entries(COUNTRY_LABELS)) {
    if (containsWord(normalized, code.toLowerCase()) || containsPhrase(normalized, label)) {
      hints.push({ code, label });
    }
  }

  const seen = new Set<string>();
  return hints.filter((hint) => {
    if (seen.has(hint.code)) return false;
    seen.add(hint.code);
    return true;
  });
}

function analyzeIntents(normalized: string): PolicyQueryIntent[] {
  const intents: PolicyQueryIntent[] = [];

  for (const definition of INTENT_DEFINITIONS) {
    const matchedTerms = compactUnique(
      definition.keywords.filter((keyword) => containsPhrase(normalized, keyword))
    );
    const patternHits =
      definition.patterns?.filter((pattern) => pattern.test(normalized)).map((pattern) => pattern.source) ?? [];

    if (matchedTerms.length === 0 && patternHits.length === 0) continue;

    const rawScore = matchedTerms.length * 1.15 + patternHits.length * 1.4;
    const confidence = Math.min(1, Math.max(0.35, rawScore / 3.4));
    intents.push({
      id: definition.id,
      label: definition.label,
      confidence,
      matchedTerms: compactUnique([...matchedTerms, ...patternHits.map(() => definition.label.toLowerCase())]),
      axes: definition.axes.map((axis) => ({
        ...axis,
        sourceIntentId: definition.id,
        sourceIntentLabel: definition.label,
        confidence,
      })),
    });
  }

  return intents.sort((a, b) => b.confidence - a.confidence || a.label.localeCompare(b.label));
}

function dedupeAxes(intents: PolicyQueryIntent[]): PolicyQueryAxisMove[] {
  const byKey = new Map<string, PolicyQueryAxisMove>();
  for (const intent of intents) {
    for (const axis of intent.axes) {
      const key = `${axis.axis}:${axis.direction}`;
      const current = byKey.get(key);
      if (!current || axis.confidence * magnitudeWeight(axis.magnitude) > current.confidence * magnitudeWeight(current.magnitude)) {
        byKey.set(key, axis);
      }
    }
  }
  return [...byKey.values()].sort(
    (a, b) =>
      b.confidence * magnitudeWeight(b.magnitude) - a.confidence * magnitudeWeight(a.magnitude) ||
      a.axis.localeCompare(b.axis)
  );
}

function anchorTermsForIntents(intents: PolicyQueryIntent[]): string[] {
  return compactUnique(
    intents.flatMap((intent) => INTENT_ANCHOR_TERMS[intent.id] ?? intent.matchedTerms)
  ).map(normalizeText).filter(Boolean);
}

export function analyzePolicyQuery(raw: string): PolicyQueryAnalysis {
  const cleaned = raw
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const normalized = normalizeText(cleaned);
  const intents = analyzeIntents(normalized);
  const axes = dedupeAxes(intents);
  const tokens = tokenize(normalized);
  const anchorTerms = anchorTermsForIntents(intents);
  const countryHints = analyzeCountries(normalized);
  const isAnnouncementLike = ANNOUNCEMENT_PATTERNS.some((pattern) => pattern.test(normalized));

  return {
    raw,
    cleaned,
    normalized,
    tokens,
    anchorTerms,
    searchTerms: compactUnique([
      ...anchorTerms,
      ...tokens.filter((token) => token.length >= 4),
      ...intents.flatMap((intent) => intent.matchedTerms),
      ...axes.map((axis) => axis.axis),
    ]).slice(0, 80),
    intents,
    axes,
    countryHints,
    isAnnouncementLike,
    hasSemanticSignal: intents.length > 0 || axes.length > 0,
  };
}

export function scorePolicyQuery(
  row: PolicyBrowserClientRow,
  analysis: PolicyQueryAnalysis
): PolicyQueryMatch {
  if (!analysis.normalized) {
    return {
      score: 0,
      axisScore: 0,
      textScore: 0,
      evidenceScore: 0,
      countryScore: 0,
      matchedAxes: [],
      matchedTerms: [],
      matchedCountries: [],
    };
  }

  const ownText = rowOwnText(row);
  const evidenceText = rowEvidenceText(row);
  const rowAxes = new Map(row.axes.map((axis) => [axis.axis, axis]));
  const matchedAxes: PolicyQueryMatchedAxis[] = [];
  let axisScore = 0;

  for (const queryAxis of analysis.axes) {
    const axis = rowAxes.get(queryAxis.axis);
    if (!axis) continue;
    const sameDirection = axis.direction === queryAxis.direction;
    const rowDirection = axis.direction || "";
    const directionWeight = sameDirection ? 10 : rowDirection === "mixed" || rowDirection === "0" ? 4.5 : 5.25;
    const contribution =
      directionWeight *
      magnitudeWeight(queryAxis.magnitude) *
      magnitudeWeight(axis.magnitude) *
      Math.max(0.45, queryAxis.confidence);
    axisScore += contribution;
    matchedAxes.push({
      axis: queryAxis.axis,
      queryDirection: queryAxis.direction,
      rowDirection,
      sameDirection,
      intentLabel: queryAxis.sourceIntentLabel,
    });
  }

  let textScore = 0;
  let ownAnchorScore = 0;
  let evidenceAnchorScore = 0;
  const matchedTerms: string[] = [];
  if (analysis.normalized.length <= 140 && containsPhrase(ownText, analysis.normalized)) {
    textScore += 9;
    matchedTerms.push(analysis.normalized);
  }

  for (const term of analysis.anchorTerms) {
    if (term.length < 4) continue;
    const ownMatched = term.includes(" ") ? containsPhrase(ownText, term) : containsWord(ownText, term);
    if (ownMatched) {
      matchedTerms.push(term);
      const contribution = term.includes(" ") ? 5.25 : 2.8;
      ownAnchorScore += contribution;
      textScore += contribution;
      continue;
    }
    const evidenceMatched = term.includes(" ") ? containsPhrase(evidenceText, term) : containsWord(evidenceText, term);
    if (evidenceMatched) {
      matchedTerms.push(term);
      const contribution = term.includes(" ") ? 1.4 : 0.65;
      evidenceAnchorScore += contribution;
      textScore += contribution;
    }
  }

  for (const term of analysis.searchTerms) {
    if (term.length < 4) continue;
    if (analysis.anchorTerms.includes(term)) continue;
    const ownMatched = term.includes(" ") ? containsPhrase(ownText, term) : containsWord(ownText, term);
    const evidenceMatched = term.includes(" ") ? containsPhrase(evidenceText, term) : containsWord(evidenceText, term);
    if (!ownMatched && !evidenceMatched) continue;
    matchedTerms.push(term);
    textScore += ownMatched ? (term.includes(" ") ? 2.5 : 1.1) : (term.includes(" ") ? 0.8 : 0.35);
  }
  textScore = Math.min(textScore, analysis.hasSemanticSignal ? 9 : 22);

  const matchedCountries = analysis.countryHints
    .filter((hint) => row.countries.includes(hint.code))
    .map((hint) => hint.code);
  const countryScore = matchedCountries.length ? 5 + Math.min(4, matchedCountries.length * 1.5) : 0;

  const baseScore = axisScore + textScore + countryScore;
  const hasPolicyFamilyText = ownAnchorScore > 0 || (!analysis.hasSemanticSignal && textScore > 0);
  const hasUsefulEvidenceText = evidenceAnchorScore >= 2.4;
  if (baseScore <= 0 || (analysis.hasSemanticSignal && !hasPolicyFamilyText && !hasUsefulEvidenceText)) {
    return {
      score: 0,
      axisScore: 0,
      textScore: 0,
      evidenceScore: 0,
      countryScore: 0,
      matchedAxes: [],
      matchedTerms: [],
      matchedCountries: [],
    };
  }

  const testedBoost =
    row.tested_hypothesis_count > 0
      ? 8 + Math.min(6, row.tested_hypothesis_count * 0.85)
      : analysis.hasSemanticSignal
        ? -4
        : 0;
  const evidenceScore = testedBoost + strengthWeight(row.best_available_evidence);
  const announcementBoost = analysis.isAnnouncementLike && row.tested_hypothesis_count > 0 ? 2 : 0;

  return {
    score: baseScore + evidenceScore + announcementBoost,
    axisScore,
    textScore,
    evidenceScore: evidenceScore + announcementBoost,
    countryScore,
    matchedAxes,
    matchedTerms: compactUnique(matchedTerms).slice(0, 12),
    matchedCountries,
  };
}
