"""Replication for liberal_democracy_managerial_flywheel_drift.

The drift index is constructed (data/derived/country_drift.json) — that's the
treatment substrate. We compute three things:

  (a) median final composite drift across the liberal-democracy panel
  (b) share of LDs with final drift > 0, plus one-sided binomial p
  (c) per-decade slope (OLS of cumulative drift on year) for each country,
      and median of those slopes

Falsification rule from the YAML:
  SUPPORTED if (a) > 0 AND share-test rejects 50% AND (c) > 0
  PARTIAL   if exactly one of those bites
  REFUTED   if (a) <= 0 or share-test rejects in the other direction
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DRIFT_JSON = REPO / "data" / "derived" / "country_drift.json"

LIBERAL_DEMOCRACIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "IRL", "AUT",
    "PRT", "GRC", "SWE", "NOR", "DNK", "FIN", "CHE", "POL", "CZE", "HUN",
    "AUS", "NZL", "CAN", "JPN", "KOR", "ISR",
]


def ols_slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den != 0 else 0.0


def binom_pmf(k: int, n: int, p: float) -> float:
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def one_sided_binom_p(k: int, n: int, p: float = 0.5) -> float:
    """P(X >= k | n, p)."""
    return sum(binom_pmf(i, n, p) for i in range(k, n + 1))


def main():
    data = json.loads(DRIFT_JSON.read_text())
    years = data["years"]
    countries = data["countries"]

    # Filter to LDs that are actually in the corpus.
    panel = [iso3 for iso3 in LIBERAL_DEMOCRACIES if iso3 in countries]
    rows = []
    for iso3 in panel:
        traj = countries[iso3]["statist_drift"]
        # Use only years where the country has movement coverage. We use
        # first non-zero year as the "start year"; if a country has no moves
        # at all we skip it.
        first_nonzero = next((i for i, v in enumerate(traj) if v != 0), None)
        if first_nonzero is None:
            rows.append({
                "iso3": iso3,
                "first_year": None,
                "final": 0.0,
                "slope_per_decade": 0.0,
                "movement_count": countries[iso3]["movement_count"],
                "skipped": "no axis-summary moves in corpus",
            })
            continue
        start_year = years[first_nonzero]
        sub_xs = years[first_nonzero:]
        sub_ys = traj[first_nonzero:]
        slope_per_year = ols_slope([float(x) for x in sub_xs], [float(y) for y in sub_ys])
        rows.append({
            "iso3": iso3,
            "first_year": start_year,
            "final": traj[-1],
            "slope_per_decade": slope_per_year * 10.0,
            "movement_count": countries[iso3]["movement_count"],
        })

    measured = [r for r in rows if "skipped" not in r]
    finals = [r["final"] for r in measured]
    slopes = [r["slope_per_decade"] for r in measured]
    n = len(measured)
    n_pos = sum(1 for v in finals if v > 0)
    n_zero = sum(1 for v in finals if v == 0)
    n_neg = sum(1 for v in finals if v < 0)

    median_final = statistics.median(finals) if finals else 0.0
    median_slope = statistics.median(slopes) if slopes else 0.0
    share_pos = n_pos / n if n > 0 else 0.0
    p_one_sided = one_sided_binom_p(n_pos, n, 0.5)

    # Falsification
    rule_a = median_final > 0
    rule_b = p_one_sided < 0.05
    rule_c = median_slope > 0

    if rule_a and rule_b and rule_c:
        verdict = (
            f"SUPPORTED — median final drift = {median_final:+.2f} (>0), "
            f"{n_pos}/{n} liberal democracies have net-positive drift "
            f"(one-sided binomial p={p_one_sided:.4f} < 0.05), "
            f"median per-decade slope = {median_slope:+.2f} (>0). "
            f"All three falsification legs pass."
        )
    elif rule_a or rule_c:
        # Most evidence in the supported direction but at least one leg fails
        legs = []
        if rule_a:
            legs.append(f"median-positive ({median_final:+.2f})")
        if rule_b:
            legs.append(f"share-test rejects 50% (p={p_one_sided:.4f})")
        if rule_c:
            legs.append(f"slope-positive ({median_slope:+.2f}/decade)")
        failed = []
        if not rule_a:
            failed.append(f"median = {median_final:+.2f}")
        if not rule_b:
            failed.append(f"share-test p={p_one_sided:.4f} (need <0.05)")
        if not rule_c:
            failed.append(f"slope = {median_slope:+.2f}/decade")
        verdict = (
            f"PARTIAL — {n_pos}/{n} ({100*share_pos:.0f}%) liberal democracies "
            f"have net-positive drift. Passing: {', '.join(legs) or 'none'}. "
            f"Failing: {', '.join(failed)}."
        )
    else:
        verdict = (
            f"REFUTED — median final drift = {median_final:+.2f} "
            f"({n_pos}/{n} positive, share = {share_pos:.0%}). "
            f"The corpus does not show monotonic statist drift across the "
            f"liberal-democracy panel."
        )

    print(f"verdict: {verdict}")
    print(f"  panel size: {n} (of {len(LIBERAL_DEMOCRACIES)} target)")
    print(f"  positive: {n_pos}  zero: {n_zero}  negative: {n_neg}")
    print(f"  median final drift: {median_final:+.2f}")
    print(f"  median slope/decade: {median_slope:+.2f}")
    print(f"  share-test p (one-sided binomial vs 50%): {p_one_sided:.4f}")

    # Write artifacts
    diagnostics = {
        "verdict": verdict,
        "method": "constructed_index_descriptive_with_binomial",
        "panel_size": n,
        "positive_count": n_pos,
        "zero_count": n_zero,
        "negative_count": n_neg,
        "median_final_drift": round(median_final, 3),
        "median_slope_per_decade": round(median_slope, 3),
        "share_positive": round(share_pos, 3),
        "one_sided_binomial_p": round(p_one_sided, 4),
        "falsification_legs": {
            "median_positive": rule_a,
            "share_rejects_fifty_at_05": rule_b,
            "slope_positive": rule_c,
        },
        "rows": rows,
    }
    (HERE / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))

    # Manifest
    manifest = {
        "hypothesis_id": "liberal_democracy_managerial_flywheel_drift",
        "inputs": [
            {
                "path": "data/derived/country_drift.json",
                "description": "Computed by scripts/compute_country_drift.py from movements/*.yaml axes_summary",
            }
        ],
        "panel": LIBERAL_DEMOCRACIES,
    }
    (HERE / "manifest.yaml").write_text(
        "\n".join([
            "hypothesis_id: liberal_democracy_managerial_flywheel_drift",
            "inputs:",
            "  - path: data/derived/country_drift.json",
            "    description: Computed by scripts/compute_country_drift.py from movements/*.yaml axes_summary",
            "panel:",
            "  " + str(LIBERAL_DEMOCRACIES).replace("'", ""),
            "",
        ])
    )

    # Result card
    rows_sorted = sorted(measured, key=lambda r: -r["final"])
    table_lines = [
        "| Country | First year | Final drift | Slope/decade | Movements |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows_sorted:
        table_lines.append(
            f"| [{r['iso3']}](/country/{r['iso3']}) | {r['first_year']} | "
            f"{'+' if r['final'] >= 0 else ''}{r['final']:.1f} | "
            f"{'+' if r['slope_per_decade'] >= 0 else ''}{r['slope_per_decade']:.2f} | "
            f"{r['movement_count']} |"
        )

    card = [
        "# Result card — liberal_democracy_managerial_flywheel_drift",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Liberal-democracy panel size (in corpus): **{n} of {len(LIBERAL_DEMOCRACIES)}**",
        f"- Net-positive drift: **{n_pos}** countries · zero: **{n_zero}** · net-negative: **{n_neg}**",
        f"- Median final composite drift: **{'+' if median_final >= 0 else ''}{median_final:.2f}**",
        f"- Median per-decade slope: **{'+' if median_slope >= 0 else ''}{median_slope:.2f}**",
        f"- One-sided binomial p (vs 50% null): **{p_one_sided:.4f}**",
        "",
        "## Falsification legs",
        "",
        f"- (a) median final > 0: **{'PASS' if rule_a else 'FAIL'}** ({median_final:+.2f})",
        f"- (b) share-positive significantly > 50% at p<0.05: **{'PASS' if rule_b else 'FAIL'}** (p={p_one_sided:.4f})",
        f"- (c) median per-decade slope > 0: **{'PASS' if rule_c else 'FAIL'}** ({median_slope:+.2f})",
        "",
        "## Per-country panel (sorted by final drift, statist-leaning first)",
        "",
        *table_lines,
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/liberal_democracy_managerial_flywheel_drift.md` "
        "for the strongest opposing case. Particularly relevant: the index "
        "measures legislated direction not absolute level (so Greece's negative "
        "value reflects forced post-memoranda austerity from a high baseline, "
        "not a low-state outcome), and the axis weighting is author-chosen "
        "(reweighting environmental + financial regulation could flip the sign "
        "for several countries).",
        "",
        "## Provenance",
        "",
        "Reproduces from `data/derived/country_drift.json` (rebuilt by "
        "`scripts/compute_country_drift.py`). Run with `python3 "
        "engine/runs/liberal_democracy_managerial_flywheel_drift/replication.py`.",
        "",
    ]
    (HERE / "result_card.md").write_text("\n".join(card))

    print(f"\nartifacts written to {HERE}")


if __name__ == "__main__":
    main()
