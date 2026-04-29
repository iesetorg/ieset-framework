"""Compute per-country positional drift trajectories from the movements corpus.

Each movement has an `axes_summary` (axis × direction × magnitude) plus a
country list and a timeframe. Treating each movement as a discrete shift event
at its timeframe.start year, we build a year-by-year cumulative position for
every (country, axis) pair.

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

import json
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
MOV_DIR = REPO / "movements"
AXES_FILE = REPO / "axes.yaml"
OUT_JSON = REPO / "data" / "derived" / "country_drift.json"
OUT_CSV = REPO / "data" / "derived" / "country_drift.csv"

# Clip chart range — the underlying empirical series the framework scrapes
# (WDI, OWID, Maddison, BIS, FRED, etc.) reliably cover only the last ~50
# years. The drift index sums policy moves over time, so showing trajectories
# starting earlier than the comparison data we can ground them in is
# misleading. Earlier movements (India Swadeshi pre-1991, 19th-century
# banking acts) still seed the cumulative index; we just don't emit the
# pre-floor years on the chart.
import datetime as _dt
CHART_FLOOR_YEAR = _dt.date.today().year - 50

# Magnitude weights — translates the qualitative tag into a numeric step.
MAG_WEIGHT = {"weak": 1.0, "moderate": 2.0, "strong": 3.0}
MAG_DEFAULT = 1.5

# Coalition / doctrine keywords that flag an authoritarian era. These get
# tagged separately because their direction-of-drift signal is overshadowed
# by the institutional-takeover signal.
AUTH_KEYWORDS = (
    "junta", "military", "dictatorship", "authoritarian", "single-party",
    "one-party", "coup", "martial law", "kleptocra",
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
        year = m["_start"]
        all_years.add(year)
        for entry in m.get("axes_summary") or []:
            axis = entry.get("axis")
            direction = entry.get("direction")
            if axis is None or direction is None:
                continue
            mag = MAG_WEIGHT.get(entry.get("magnitude", ""), MAG_DEFAULT)
            sign = DIRECTION_SIGN.get(direction, 0.0)
            step = sign * mag
            all_axes.add(axis)

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

    # Build year-by-year cumulative trajectories from year_min to year_max.
    # Pre-CHART_FLOOR_YEAR shifts still accumulate into each country's
    # opening cumulative position; we just don't emit the early years to the
    # output (they'd show as a long flat tail on most countries' charts).
    if not all_years:
        return {"countries": {}, "axes": sorted(all_axes), "year_min": None, "year_max": None}
    raw_min, raw_max = min(all_years), max(all_years)
    year_min = max(raw_min, CHART_FLOOR_YEAR)
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
        for m in movements:
            if country in (m.get("countries") or []):
                m_events.append({
                    "movement_id": m["movement_id"],
                    "name": m.get("name") or m["movement_id"],
                    "year": m["_start"],
                    "end": m.get("_end"),
                    "tone": classify_movement_tone(m),
                })
        m_events.sort(key=lambda e: e["year"])

        countries_out[country] = {
            "axes": per_axis,
            "statist_drift": composite_traj,
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


def write_csv(out, path: Path):
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
    path.write_text("\n".join(rows) + "\n")


def main():
    movements = load_movements()
    out = build_drift(movements)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
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
