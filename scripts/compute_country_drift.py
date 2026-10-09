"""Compute per-country positional drift trajectories from the movements corpus.

Each movement has an `axes_summary` (axis × direction × magnitude) plus a
country list and a timeframe. Most entries are attributed to the movement's
start year as a period-summary proxy, not as an enacted-policy date. An entry
with a documented `drift_attribution_year` is placed in that year instead.
The resulting cumulative series is a map of coded country-level movement direction,
not an annual policy-implementation or outcome series. Subnational movements
remain in the corpus but do not contribute to country trajectories.
Full-length numeric arrays use zero as a storage placeholder before a country's
`first_coded_year`; consumers must treat those values as unobserved.

We also compute a composite *statist drift index* that captures the user's
working hypothesis: liberal democracies experience monotonic drift toward more
state spending, more transfers, more regulation. Higher index ⇒ more statist;
lower ⇒ more market-oriented. The composite is a weighted sum across the 15
axes that have a clear pro-state vs pro-market valence.

Output:
- data/derived/country_drift.json: per-country axis trajectories + composite
- data/derived/country_drift.csv: long-form for spreadsheet inspection
- engine/audits/country_drift_timing_review.json: later-year rationale review

Re-run when movement coding changes. Static (deterministic) given the corpus.
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
OUT_TIMING_AUDIT = REPO / "engine" / "audits" / "country_drift_timing_review.json"

# Emit the full coded history. The first year comes from the earliest movement
# in the corpus, so readers can inspect the actual opening step instead of a
# later chart window that silently inherits earlier movements.

# Magnitude weights — translates the qualitative tag into a numeric step.
MAG_WEIGHT = {"weak": 1.0, "moderate": 2.0, "strong": 3.0}
MAG_DEFAULT = 1.5

# Coalition / doctrine keywords that flag an authoritarian era. These get
# tagged separately because their direction-of-drift signal is overshadowed
# by the institutional-takeover signal.
AUTH_KEYWORDS = (
    "junta", "military rule", "military government", "military regime",
    "military transition", "military council", "dictatorship", "authoritarian",
    "single-party", "one-party", "coup", "martial law", "kleptocra",
)


def classify_movement_tone(m: dict) -> str:
    """Return one of: left / right / centrist / auth / neutral."""
    coalition = (m.get("coalition") or "").lower()
    doctrine = (m.get("doctrine") or "").lower()
    if any(kw in coalition or kw in doctrine for kw in AUTH_KEYWORDS):
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
    "regulatory.price_control_intensity",
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
YEAR_MENTION = re.compile(r"\b(?:18|19|20)\d{2}\b")


def axis_attribution_year(movement: dict, entry: dict) -> int:
    """Use a reviewed axis year only; never infer timing from rationale text."""
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


def timing_review(movements: list[dict]) -> dict:
    """Flag later years for human review without guessing an event date."""
    rows = []
    explicit_count = 0
    proxy_count = 0
    for movement in movements:
        start = movement["_start"]
        for entry in movement.get("axes_summary") or []:
            if not isinstance(entry, dict) or not entry.get("axis"):
                continue
            year = axis_attribution_year(movement, entry)
            explicitly_dated = entry.get("drift_attribution_year") is not None
            if explicitly_dated:
                explicit_count += 1
            else:
                proxy_count += 1
            mentioned = sorted({
                int(value) for value in YEAR_MENTION.findall(str(entry.get("rationale") or ""))
                if int(value) > start + 1
            })
            manual_note = str(entry.get("drift_timing_review_note") or "").strip()
            if (mentioned or manual_note) and not explicitly_dated:
                rows.append({
                    "movement_id": movement["movement_id"],
                    "axis": entry["axis"],
                    "movement_start": start,
                    "later_years_mentioned": mentioned,
                    "manual_review_note": manual_note or None,
                    "rationale": entry.get("rationale") or "",
                })
    rows.sort(key=lambda row: (row["movement_start"], row["movement_id"], row["axis"]))
    return {
        "schema": "ieset-country-drift-timing-review-v1",
        "method": (
            "Only manually documented drift_attribution_year overrides move an axis step. "
            "A later year in rationale text is a review clue, not proof of enactment timing."
        ),
        "summary": {
            "explicit_axis_year_entries": explicit_count,
            "movement_start_proxy_entries": proxy_count,
            "unresolved_later_year_rationale_entries": sum(
                bool(row["later_years_mentioned"]) for row in rows
            ),
            "manual_review_note_entries": sum(
                bool(row["manual_review_note"]) for row in rows
            ),
            "review_queue_entries": len(rows),
            "unresolved_movements": len({row["movement_id"] for row in rows}),
        },
        "review_queue": rows,
    }


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


def country_drift_movements(movements):
    """Use one country-level coding per policy episode in the plotted series."""
    by_id = {movement.get("movement_id"): movement for movement in movements}
    for movement in movements:
        if movement.get("country_drift_role") != "context_only":
            continue
        primary_id = movement.get("country_drift_primary_movement")
        primary = by_id.get(primary_id)
        if not primary or primary.get("country_drift_role") == "context_only":
            raise ValueError(
                f"{movement.get('movement_id')}: missing primary country drift movement {primary_id}"
            )
        if not set(movement.get("countries") or []).issubset(primary.get("countries") or []):
            raise ValueError(
                f"{movement.get('movement_id')}: primary {primary_id} has different countries"
            )
    return [
        movement for movement in movements
        if movement.get("scope", "national") != "subnational"
        and movement.get("country_drift_role", "primary") != "context_only"
    ]


def build_drift(movements, review=None):
    # A country's ISO code on a state/province record locates that record; it
    # does not make its policy direction representative of the whole country.
    country_movements = country_drift_movements(movements)
    review = review if review is not None else timing_review(country_movements)
    # Collect every (country, axis, year) shift event with signed magnitude.
    # `events[country][axis] = list[(year, signed_step, movement_id)]`
    events = defaultdict(lambda: defaultdict(list))
    composite_events = defaultdict(list)  # events[country] = list[(year, delta, movement_id)]

    all_years = set()
    all_countries = set()
    all_axes = set()

    for m in country_movements:
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

    # Build year-by-year cumulative trajectories across the entire coded
    # movement span. Chart consumers can begin each country's line at its
    # first movement year without changing these full-length numeric series.
    if not all_years:
        return {
            "countries": {}, "axes": sorted(all_axes), "year_min": None,
            "year_max": None, "timing_model": "movement_start_proxy_with_reviewed_axis_years",
            "timing_summary": review["summary"],
        }
    raw_min, raw_max = min(all_years), max(all_years)
    year_min = raw_min
    year_max = raw_max
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
        for m in country_movements:
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

        explicit_axis_timing = []
        for m in country_movements:
            if country not in (m.get("countries") or []):
                continue
            for entry in m.get("axes_summary") or []:
                if not isinstance(entry, dict) or not entry.get("axis"):
                    continue
                year = axis_attribution_year(m, entry)
                if entry.get("drift_attribution_year") is not None:
                    explicit_axis_timing.append({
                        "movement_id": m["movement_id"],
                        "axis": entry["axis"],
                        "movement_start": m["_start"],
                        "attribution_year": year,
                        "basis": entry["drift_attribution_basis"],
                    })
        explicit_axis_timing.sort(key=lambda row: (row["attribution_year"], row["movement_id"], row["axis"]))

        countries_out[country] = {
            "axes": per_axis,
            "statist_drift": composite_traj,
            "movements": m_events,
            "movement_count": len(m_events),
            "first_coded_year": m_events[0]["year"] if m_events else None,
            "explicit_axis_timing": explicit_axis_timing,
        }

    return {
        "year_min": year_min,
        "year_max": year_max,
        "years": years,
        "axes": sorted(all_axes),
        "countries": countries_out,
        "pro_state_axes": sorted(PRO_STATE_AXES),
        "pro_market_axes": sorted(PRO_MARKET_AXES),
        "timing_model": "movement_start_proxy_with_reviewed_axis_years",
        "timing_summary": review["summary"],
    }


def csv_text(out):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the checked-in JSON or CSV differs from the movement corpus",
    )
    args = parser.parse_args()
    movements = load_movements()
    review = timing_review(country_drift_movements(movements))
    out = build_drift(movements, review)
    json_output = json.dumps(out, indent=2)
    csv_output = csv_text(out)
    audit_output = json.dumps(review, indent=2) + "\n"

    if args.check:
        stale = [
            path for path, expected in (
                (OUT_JSON, json_output),
                (OUT_CSV, csv_output),
                (OUT_TIMING_AUDIT, audit_output),
            )
            if not path.exists() or path.read_text() != expected
        ]
        if stale:
            for path in stale:
                print(f"stale drift artifact: {path.relative_to(REPO)}")
            return 1
        print(f"drift artifacts current: {len(out['countries'])} countries, {out['year_min']}–{out['year_max']}")
        return 0

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_output)
    OUT_CSV.write_text(csv_output)
    OUT_TIMING_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TIMING_AUDIT.write_text(audit_output)

    print(f"countries:   {len(out['countries'])}")
    print(f"axes:        {len(out['axes'])}")
    print(f"year range:  {out['year_min']} → {out['year_max']}")
    print(f"timing:      {review['summary']}")
    print(f"output:      {OUT_JSON.relative_to(REPO)}")
    print(f"             {OUT_CSV.relative_to(REPO)}")
    print(f"             {OUT_TIMING_AUDIT.relative_to(REPO)}")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
