"""Compute per-country positional drift trajectories from the movements corpus.

Each movement has an `axes_summary` (axis × direction × magnitude) plus a
country list and a timeframe. Each axis step is placed at the movement's
start year unless a source-reviewed drift_attribution_year identifies a
different decision year. We build a year-by-year cumulative position for
every (country, axis) pair. These are coded decisions, not observed outcomes.

We also compute a composite *statist drift index* that captures the user's
working hypothesis: liberal democracies experience monotonic drift toward more
state spending, more transfers, more regulation. Higher index ⇒ more statist;
lower ⇒ more market-oriented. The composite is a weighted sum across the 14
axes that have a clear pro-state vs pro-market valence.

Output:
- data/derived/country_drift.json: per-country axis trajectories + composite
- data/derived/country_drift.csv: long-form for spreadsheet inspection

Re-run on every `make build`. Static (deterministic) given the corpus.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
MOV_DIR = REPO / "movements"
AXES_FILE = REPO / "axes.yaml"
OUT_JSON = REPO / "data" / "derived" / "country_drift.json"
OUT_CSV = REPO / "data" / "derived" / "country_drift.csv"

# This is a constructed movement-coding series, not an empirical outcome panel.
# Its range follows the authored movement corpus, independently of the shorter
# windows used by particular registered empirical tests.

# Magnitude weights — translates the qualitative tag into a numeric step.
MAG_WEIGHT = {"weak": 1.0, "moderate": 2.0, "strong": 3.0}
MAG_DEFAULT = 1.5

# Keep the existing strong terms, but a bare mention of "military" in doctrine
# often describes defence policy or a prior junta rather than the government.
# Keep these rules and the reviewed IDs in web/lib/movement_tone.ts in sync.
AUTH_STRONG_KEYWORDS = (
    "junta", "dictatorship", "authoritarian", "single-party",
    "one-party", "coup", "martial law", "kleptocra",
)
MILITARY_RULE_COALITION_MARKERS = (
    "military regime", "military government", "military council",
    "military administrative council", "military transition",
    "military-appointed", "military-civilian regime",
    "military-security state", "military-backed",
    "military/palace-backed", "civilian-military authorities",
)
AUTH_MOVEMENT_IDS = {
    # Reviewed governing-regime evidence is stronger than a text substring.
    "guinea_cnrd_transition_resource_state_2021_present",
    "mmr_burmese_way_to_socialism_1962",
    "peru_fujimori_autogolpe_1992",
    "thailand_surayud_interim_2006_2008",
    # Authored current-regime evidence is stronger than a bare military mention.
    "eritrea_pfdj_national_service_state_1994_present",
    "ethiopia_abiy_prosperity_2018_present",
    "iran_pezeshkian_reformist_2024_present",
    "iran_raisi_conservative_2021_2024",
    "malaysia_mahathir_first_term_1981_1988",
    "vietnam_phuc_pm_2016_2021",
    "yemen_saleh_gpc_unification_adjustment_1990_2011",
    "zimbabwe_mnangagwa_zanu_pf_2017_present",
}
AUTH_REVIEW_HOLD_IDS = {
    # Preserve the prior tone pending a regime criterion and source review;
    # a single multi-year label is especially coarse for transitions.
    "bolivia_morales_third_crisis_2014_2019",
    "egypt_morsi_muslim_brotherhood_2012_2013",
    "malaysia_najib_bn_2009_2018",
    "pakistan_nawaz_sharif_pmln_ii_1997_1999",
    "pakistan_shehbaz_pmln_coalition_2024_present",
    "russia_gorbachev_perestroika_glasnost_1985_1991",
    "slovakia_fico_fourth_2023_present",
    "srilanka_gotabaya_rajapaksa_slpp_2019_2022",
}
NON_AUTH_TRIGGER_IDS = {
    # The term describes an elected parliamentary majority/minority, an
    # opposition, or a negated one-party claim; it is not regime evidence.
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
    # These doctrines describe a predecessor's junta/dictatorship, a coup
    # against the government, or restoration after one-party rule.
    "argentina_alfonsin_ucr_1983_1989",
    "argentina_nestor_kirchner_2003_2007",
    "chile_aylwin_concertacion_1990_1994",
    "greece_karamanlis_nd_1974_1980",
    "india_janata_desai_1977_1979",
    "nigeria_shagari_second_republic_1979_1983",
    "philippines_cory_aquino_transition_1986_1992",
    "thailand_yingluck_pheu_thai_2011_2014",
    "zambia_msunwe_structural_adjustment_1991_2001",
}


def has_auth_strong_term(text: str) -> bool:
    """Match whole terms, so `coup` does not match coupled or coupons."""
    return any(
        re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", text)
        for term in AUTH_STRONG_KEYWORDS
    )


def classify_movement_tone(m: dict) -> str:
    """Return one of: left / right / centrist / auth / neutral."""
    coalition = (m.get("coalition") or "").lower()
    doctrine = (m.get("doctrine") or "").lower()
    if (
        m.get("movement_id") in AUTH_MOVEMENT_IDS | AUTH_REVIEW_HOLD_IDS
        or (
            m.get("movement_id") not in NON_AUTH_TRIGGER_IDS
            and (
                any(marker in coalition for marker in MILITARY_RULE_COALITION_MARKERS)
                or has_auth_strong_term(coalition)
                or has_auth_strong_term(doctrine)
            )
        )
    ):
        return "auth"

    score = 0.0
    has_axes = False
    for entry in m.get("axes_summary") or []:
        axis = entry.get("axis")
        direction = entry.get("direction")
        if axis is None or direction is None:
            continue
        has_axes = True
        sign = DIRECTION_SIGN.get(direction, 0.0)
        mag = MAG_WEIGHT.get(entry.get("magnitude", ""), MAG_DEFAULT)
        step = sign * mag
        if axis in PRO_STATE_AXES:
            score += step
        elif axis in PRO_MARKET_AXES:
            score -= step

    if score > 1.0:
        return "left"
    if score < -1.0:
        return "right"
    if has_axes:
        return "centrist"
    return "neutral"


def movement_leader_label(m: dict) -> str | None:
    """Return the first leader's name, stripped of role/date detail."""
    leaders = m.get("leaders") or []
    if not leaders:
        return None
    raw = str(leaders[0]).strip()
    if not raw:
        return None
    return raw.split("(", 1)[0].strip().rstrip(",-;") or None

# Axes whose `+` direction indicates the state expanding (more spending,
# transfers, regulation, monetisation). Index contribution sign = +1.
PRO_STATE_AXES = {
    "fiscal.tax_progressivity",
    "fiscal.tax_corporate",
    "fiscal.tax_capital",
    "fiscal.transfer_expansion",
    "fiscal.spending_level",
    "fiscal.sectoral_subsidy",
    "regulatory.environmental_stringency",
    # The schema describes financial_deregulation's `+` direction as "tighter
    # financial regulation" (it's labelled by the lever, not the verb). So +1.
    "regulatory.financial_deregulation",
    "regulatory.sectoral_licensing",
    "monetary.monetary_expansion_direction",
}

# Axes whose `+` direction indicates the state retreating. Index contribution
# sign = -1 (so + on these subtracts from the statist index).
PRO_MARKET_AXES = {
    "regulatory.labour_market_flexibility",
    "regulatory.product_market_competition",
    "regulatory.trade_openness",
    "monetary.central_bank_independence",
}

DIRECTION_SIGN = {"+": 1.0, "-": -1.0, "0": 0.0, "mixed": 0.0}


def axis_attribution_year(movement: dict, entry: dict) -> int:
    """Use a documented axis year; never infer an event date from prose."""
    start = movement["_start"]
    override = entry.get("drift_attribution_year")
    if override is None:
        return start
    if isinstance(override, bool) or not isinstance(override, int):
        raise ValueError(f"{movement['movement_id']}: invalid drift_attribution_year {override!r}")
    end = movement.get("_end")
    if override < start or (end is not None and override > end):
        raise ValueError(
            f"{movement['movement_id']}: drift_attribution_year {override} "
            f"outside movement {start}–{end or 'ongoing'}"
        )
    if not str(entry.get("drift_attribution_basis") or "").strip():
        raise ValueError(f"{movement['movement_id']}: explicit axis year needs a basis")
    return override


def load_movements():
    out = []
    for f in sorted(MOV_DIR.glob("*.yaml")):
        try:
            d = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        if not d:
            continue
        if not d.get("movement_id") or not d.get("countries"):
            continue
        tf = d.get("timeframe") or {}
        start = tf.get("start")
        end_raw = tf.get("end")
        if not isinstance(start, int):
            continue
        end = end_raw if isinstance(end_raw, int) else None  # ongoing → leave open
        d["_start"] = start
        d["_end"] = end
        out.append(d)
    return out


def build_drift(movements):
    # Country trajectories represent national decisions. State/municipal and
    # supranational movements remain in the source corpus, but their member
    # or parent country lists do not establish a national policy step.
    movements = [m for m in movements if m.get("scope", "national") == "national"]

    # Collect every (country, axis, year) shift event with signed magnitude.
    # `events[country][axis] = list[(year, signed_step, movement_id)]`
    events = defaultdict(lambda: defaultdict(list))
    composite_events = defaultdict(list)  # events[country] = list[(year, delta, movement_id)]

    all_years = set()
    all_countries = set()
    all_axes = set()

    for m in movements:
        countries = m.get("countries") or []
        all_countries.update(countries)
        all_years.add(m["_start"])
        for entry in m.get("axes_summary") or []:
            axis = entry.get("axis")
            direction = entry.get("direction")
            if axis is None or direction is None:
                continue
            mag = MAG_WEIGHT.get(entry.get("magnitude", ""), MAG_DEFAULT)
            sign = DIRECTION_SIGN.get(direction, 0.0)
            step = sign * mag
            all_axes.add(axis)
            year = axis_attribution_year(m, entry)
            all_years.add(year)

            for c in countries:
                events[c][axis].append((year, step, m["movement_id"]))

                # Composite contribution for the statist-drift index.
                if axis in PRO_STATE_AXES:
                    contrib = +step  # + direction = more state
                elif axis in PRO_MARKET_AXES:
                    contrib = -step  # + direction = less state
                else:
                    contrib = 0.0
                if contrib != 0.0:
                    composite_events[c].append((year, contrib, m["movement_id"]))

    # Build the complete authored movement span. Countries first coded later
    # retain zeroes in the raw aligned arrays for downstream calculations; the
    # chart masks their pre-coverage years using the first actually coded
    # composite or axis step, not merely the first authored movement.
    if not all_years:
        return {"countries": {}, "axes": sorted(all_axes), "year_min": None, "year_max": None}
    year_min, year_max = min(all_years), max(all_years)
    years = list(range(year_min, year_max + 1))

    countries_out = {}
    for country in sorted(all_countries):
        per_axis = {}
        for axis in sorted(all_axes):
            ev = sorted(events[country].get(axis, []), key=lambda x: x[0])
            cum = 0.0
            i = 0
            traj = []
            for y in years:
                while i < len(ev) and ev[i][0] <= y:
                    cum += ev[i][1]
                    i += 1
                traj.append(round(cum, 3))
            per_axis[axis] = traj

        # Composite trajectory.
        ev = sorted(composite_events.get(country, []), key=lambda x: x[0])
        cum = 0.0
        i = 0
        composite_traj = []
        for y in years:
            while i < len(ev) and ev[i][0] <= y:
                cum += ev[i][1]
                i += 1
            composite_traj.append(round(cum, 3))

        # Movement event log for tooltip-style render.
        m_events = []
        for m in movements:
            if country in (m.get("countries") or []):
                m_events.append({
                    "movement_id": m["movement_id"],
                    "name": m.get("name") or m["movement_id"],
                    "leader_label": movement_leader_label(m),
                    "year": m["_start"],
                    "end": m.get("_end"),
                    "tone": classify_movement_tone(m),
                })
        m_events.sort(key=lambda e: e["year"])

        countries_out[country] = {
            "axes": per_axis,
            "axis_first_year": {
                axis: min(year for year, _step, _id in axis_events)
                for axis, axis_events in events[country].items()
                if axis_events
            },
            "statist_drift": composite_traj,
            # A country may have national movement prose but no valenced axis
            # step. Equal and opposite steps still establish coding coverage,
            # even when the net composite remains at zero.
            "composite_first_year": min((year for year, _step, _id in ev), default=None),
            "movements": m_events,
            "movement_count": len(m_events),
        }

    return {
        "year_min": year_min,
        "year_max": year_max,
        "years": years,
        "axes": sorted(all_axes),
        "countries": countries_out,
        "pro_state_axes": sorted(PRO_STATE_AXES),
        "pro_market_axes": sorted(PRO_MARKET_AXES),
    }


def render_csv(out) -> str:
    """Long-form CSV: country, axis, year, value (cumulative drift).

    Includes statist_drift as a pseudo-axis so spreadsheet users can pivot.
    """
    rows = ["country,axis,year,cumulative_drift"]
    for country, data in out["countries"].items():
        for axis, traj in data["axes"].items():
            for y, v in zip(out["years"], traj):
                if v != 0.0:
                    rows.append(f"{country},{axis},{y},{v}")
        for y, v in zip(out["years"], data["statist_drift"]):
            if v != 0.0:
                rows.append(f"{country},statist_drift,{y},{v}")
    return "\n".join(rows) + "\n"


def write_csv(out, path: Path):
    path.write_text(render_csv(out))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify both generated outputs without writing them")
    args = parser.parse_args()
    movements = load_movements()
    out = build_drift(movements)

    json_text = json.dumps(out, indent=2)
    csv_text = render_csv(out)
    if args.check:
        if not OUT_JSON.exists() or OUT_JSON.read_text() != json_text:
            raise SystemExit(f"stale or missing {OUT_JSON.relative_to(REPO)}")
        if not OUT_CSV.exists() or OUT_CSV.read_text() != csv_text:
            raise SystemExit(f"stale or missing {OUT_CSV.relative_to(REPO)}")
    else:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json_text)
        write_csv(out, OUT_CSV)

    print(f"countries:   {len(out['countries'])}")
    print(f"axes:        {len(out['axes'])}")
    print(f"year range:  {out['year_min']} → {out['year_max']}")
    print(f"output:      {OUT_JSON.relative_to(REPO)}")
    print(f"             {OUT_CSV.relative_to(REPO)}")

    # Print a quick statist-drift leaderboard so we can sanity-check.
    by_drift = sorted(
        ((c, d["statist_drift"][-1]) for c, d in out["countries"].items() if d["movement_count"] >= 5),
        key=lambda x: -x[1],
    )
    print()
    print(f"  {'country':<5}  {'movements':>9}  {'final statist drift'}")
    print(f"  {'-'*5}  {'-'*9}  {'-'*22}")
    for c, drift in by_drift[:10]:
        n = out["countries"][c]["movement_count"]
        print(f"  {c:<5}  {n:>9}  {drift:+.2f}")
    print("  ...")
    for c, drift in by_drift[-10:]:
        n = out["countries"][c]["movement_count"]
        print(f"  {c:<5}  {n:>9}  {drift:+.2f}")


if __name__ == "__main__":
    main()
