/**
 * Map a movement to an ideological tone for chart annotation. The tone is
 * based on the movement's coalition string + axes_summary direction pattern,
 * not on the country or party label. Used by /country/[iso3] to colour
 * the drift-trajectory dots.
 *
 * Heuristic rather than principled — the framework already codes axes
 * direction precisely, but this lookup just tags whether the era pulled
 * the country net-statist (left), net-market (right), centrist (mixed),
 * or authoritarian (when democratic accountability is the salient feature
 * regardless of fiscal direction). For the rare cases the heuristic fails
 * we fall back to "neutral" rather than guess.
 */

export type MovementTone = "left" | "right" | "centrist" | "auth" | "neutral";

interface MovementShape {
  movement_id: string;
  axes_summary?: Array<{ axis: string; direction: string; magnitude?: string }>;
  coalition?: string;
  doctrine?: string;
}

/**
 * Compute a movement's net statist-vs-market signal from its axes_summary.
 * Returns +1 (statist), -1 (market), 0 (mixed/none).
 */
export function statistMarketScore(m: MovementShape): number {
  if (!m.axes_summary) return 0;
  const PRO_STATE = new Set([
    "fiscal.tax_progressivity",
    "fiscal.tax_corporate",
    "fiscal.tax_capital",
    "fiscal.transfer_expansion",
    "fiscal.spending_level",
    "fiscal.sectoral_subsidy",
    "regulatory.environmental_stringency",
    "regulatory.financial_deregulation",
    "regulatory.sectoral_licensing",
    "monetary.monetary_expansion_direction",
  ]);
  const PRO_MARKET = new Set([
    "regulatory.labour_market_flexibility",
    "regulatory.product_market_competition",
    "regulatory.trade_openness",
    "monetary.central_bank_independence",
  ]);
  const MAG: Record<string, number> = { weak: 1, moderate: 2, strong: 3 };
  const SIGN: Record<string, number> = { "+": 1, "-": -1, "0": 0, mixed: 0 };
  let score = 0;
  for (const e of m.axes_summary) {
    const sign = SIGN[e.direction] ?? 0;
    const mag = MAG[e.magnitude ?? ""] ?? 1.5;
    const step = sign * mag;
    if (PRO_STATE.has(e.axis)) score += step;
    else if (PRO_MARKET.has(e.axis)) score -= step;
  }
  return score;
}

/** Keep the existing strong terms. A bare "military" mention in doctrine may
 *  describe defence policy or a prior junta. Keep these rules and reviewed
 *  IDs in scripts/compute_country_drift.py in sync. */
const AUTH_STRONG_KEYWORDS = [
  "junta",
  "dictatorship",
  "authoritarian",
  "single-party",
  "one-party",
  "coup",
  "martial law",
  "kleptocra",
];
const MILITARY_RULE_COALITION_MARKERS = [
  "military regime",
  "military government",
  "military council",
  "military administrative council",
  "military transition",
  "military-appointed",
  "military-civilian regime",
  "military-security state",
  "military-backed",
  "military/palace-backed",
  "civilian-military authorities",
];
const AUTH_MOVEMENT_IDS = new Set([
  "guinea_cnrd_transition_resource_state_2021_present",
  "mmr_burmese_way_to_socialism_1962",
  "peru_fujimori_autogolpe_1992",
  "thailand_surayud_interim_2006_2008",
  "eritrea_pfdj_national_service_state_1994_present",
  "ethiopia_abiy_prosperity_2018_present",
  "iran_pezeshkian_reformist_2024_present",
  "iran_raisi_conservative_2021_2024",
  "malaysia_mahathir_first_term_1981_1988",
  "vietnam_phuc_pm_2016_2021",
  "yemen_saleh_gpc_unification_adjustment_1990_2011",
  "zimbabwe_mnangagwa_zanu_pf_2017_present",
]);
const AUTH_REVIEW_HOLD_IDS = new Set([
  "bolivia_morales_third_crisis_2014_2019",
  "egypt_morsi_muslim_brotherhood_2012_2013",
  "malaysia_najib_bn_2009_2018",
  "pakistan_nawaz_sharif_pmln_ii_1997_1999",
  "pakistan_shehbaz_pmln_coalition_2024_present",
  "russia_gorbachev_perestroika_glasnost_1985_1991",
  "slovakia_fico_fourth_2023_present",
  "srilanka_gotabaya_rajapaksa_slpp_2019_2022",
]);
const NON_AUTH_TRIGGER_IDS = new Set([
  "bulgaria_radev_progressive_bulgaria_2026_present",
  "colombia_barco_liberal_1986_1990",
  "czech_republic_zeman_cssd_1998_2002",
  "denmark_frederiksen_sap_broad_2019_present",
  "denmark_lokke_rasmussen_venstre_2015_2019",
  "greece_mitsotakis_nd_2019_present",
  "japan_hashimoto_ldp_1996_1998",
  "japan_ldp_1976_1982_coalitions",
  "japan_ldp_bubble_era_1987_1993",
  "japan_nakasone_ldp_1982_1987",
  "newzealand_ardern_labour_2017_2023",
  "newzealand_hipkins_labour_2023",
  "norway_bondevik_jagland_transition_1996_2000",
  "norway_store_ap_sp_2021_present",
  "peru_keiko_fujimori_2026_present",
  "srilanka_dissanayake_npp_2024_present",
  "sweden_andersson_sap_2021_2022",
  "sweden_carlsson_sap_return_1994_1996",
  "sweden_persson_sap_1996_2006",
  "us_gilded_age_federal_market_rules_1887_1890",
  "argentina_alfonsin_ucr_1983_1989",
  "argentina_nestor_kirchner_2003_2007",
  "chile_aylwin_concertacion_1990_1994",
  "greece_karamanlis_nd_1974_1980",
  "india_janata_desai_1977_1979",
  "nigeria_shagari_second_republic_1979_1983",
  "philippines_cory_aquino_transition_1986_1992",
  "thailand_yingluck_pheu_thai_2011_2014",
  "zambia_msunwe_structural_adjustment_1991_2001",
]);

function hasAuthStrongTerm(text: string): boolean {
  const unnegated = text.replace(/\b(?:not|no|never)\s+(?:a\s+|an\s+)?(?:single-party|one-party)\b/g, "");
  return AUTH_STRONG_KEYWORDS.some((term) =>
    new RegExp(`(^|[^a-z])${term}(?=$|[^a-z])`).test(unnegated)
  );
}

function hasMilitaryRuleDoctrine(text: string): boolean {
  return /\b(?:governed|ruled|administered)\s+(?:by|through)\s+(?:a|the)\s+military\s+(?:council|junta|government)\b/.test(text);
}

export function classifyMovementTone(m: MovementShape): MovementTone {
  const lcCoalition = (m.coalition ?? "").toLowerCase();
  const lcDoctrine = (m.doctrine ?? "").toLowerCase();
  const isAuth = AUTH_MOVEMENT_IDS.has(m.movement_id) || AUTH_REVIEW_HOLD_IDS.has(m.movement_id) ||
    (!NON_AUTH_TRIGGER_IDS.has(m.movement_id) && (
      MILITARY_RULE_COALITION_MARKERS.some((marker) => lcCoalition.includes(marker)) ||
      hasMilitaryRuleDoctrine(lcDoctrine) ||
      hasAuthStrongTerm(lcCoalition) || hasAuthStrongTerm(lcDoctrine)
    ));
  if (isAuth) return "auth";
  const score = statistMarketScore(m);
  if (score > 1.0) return "left";
  if (score < -1.0) return "right";
  if (score >= -1.0 && score <= 1.0 && m.axes_summary && m.axes_summary.length > 0) {
    return "centrist";
  }
  return "neutral";
}
