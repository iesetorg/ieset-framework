"""Replication for fiscal_rule_presence_dampens_statist_drift.

Compute per-decade drift slope for each liberal democracy from
data/derived/country_drift.json. Compare slopes between rule-bound and
rule-free countries with a one-sided Mann-Whitney U test.
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DRIFT_JSON = REPO / "data" / "derived" / "country_drift.json"

# Hand-coded fiscal-rule binary (see YAML for citations).
FISCAL_RULE_BOUND = {
    "DEU": 1, "CHE": 1, "SWE": 1, "NLD": 1, "FIN": 1, "AUT": 1,
    "DNK": 1, "IRL": 1, "GRC": 1, "ESP": 1, "ITA": 1, "POL": 1,
    "CZE": 1, "HUN": 1,
    "KOR": 0, "USA": 0, "GBR": 0, "FRA": 0, "BEL": 0, "PRT": 0,
    "AUS": 0, "NZL": 0, "CAN": 0, "JPN": 0, "ISR": 0, "NOR": 0,
}


def ols_slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den != 0 else 0.0


def mann_whitney_u_one_sided(group_a: list[float], group_b: list[float]) -> tuple[float, float]:
    """Return (U_a, p_one_sided) for H1: group_a stochastically less than group_b."""
    n_a, n_b = len(group_a), len(group_b)
    combined = [(v, "a") for v in group_a] + [(v, "b") for v in group_b]
    combined.sort(key=lambda x: x[0])
    # Assign average ranks (handle ties)
    ranks = {}
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    rank_sum_a = sum(ranks[k] for k, (_v, lbl) in enumerate(combined) if lbl == "a")
    u_a = rank_sum_a - n_a * (n_a + 1) / 2
    # Normal approximation
    mu = n_a * n_b / 2
    sigma = math.sqrt(n_a * n_b * (n_a + n_b + 1) / 12)
    z = (u_a - mu) / sigma if sigma > 0 else 0.0
    # One-sided p: H1 is u_a < mu (i.e., group_a slopes lower)
    # Use normal CDF approximation
    p_one = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return u_a, p_one


def main():
    data = json.loads(DRIFT_JSON.read_text())
    years = data["years"]
    countries = data["countries"]

    rows = []
    for iso3, treat in FISCAL_RULE_BOUND.items():
        if iso3 not in countries:
            continue
        traj = countries[iso3]["statist_drift"]
        first_nonzero = next((i for i, v in enumerate(traj) if v != 0), None)
        if first_nonzero is None:
            slope_per_decade = 0.0
        else:
            sub_xs = [float(y) for y in years[first_nonzero:]]
            sub_ys = [float(v) for v in traj[first_nonzero:]]
            slope_per_decade = ols_slope(sub_xs, sub_ys) * 10.0
        rows.append({
            "iso3": iso3,
            "rule_bound": treat,
            "slope_per_decade": slope_per_decade,
            "movements": countries[iso3]["movement_count"],
        })

    bound = [r["slope_per_decade"] for r in rows if r["rule_bound"] == 1]
    free = [r["slope_per_decade"] for r in rows if r["rule_bound"] == 0]
    median_bound = statistics.median(bound)
    median_free = statistics.median(free)
    median_gap = median_bound - median_free  # negative ⇒ rule-bound has lower slope

    u_bound, p_one = mann_whitney_u_one_sided(bound, free)

    rule_a = median_gap <= -1.0  # bound countries' median slope is at least 1 lower
    rule_b = p_one < 0.10

    if rule_a and rule_b:
        verdict = (
            f"SUPPORTED — median per-decade slope: rule-bound = {median_bound:+.2f}, "
            f"rule-free = {median_free:+.2f} (gap {median_gap:+.2f} ≤ −1.0), "
            f"Mann-Whitney one-sided p = {p_one:.4f} (< 0.10)."
        )
    elif median_gap < 0 and not rule_a:
        verdict = (
            f"PARTIAL — gap is in the predicted direction (rule-bound "
            f"{median_bound:+.2f} vs rule-free {median_free:+.2f}, gap {median_gap:+.2f}) "
            f"but does not meet the −1.0 magnitude threshold; Mann-Whitney "
            f"p = {p_one:.4f}."
        )
    elif median_gap < 0 and not rule_b:
        verdict = (
            f"PARTIAL — gap is in the predicted direction (rule-bound "
            f"{median_bound:+.2f} vs rule-free {median_free:+.2f}, gap {median_gap:+.2f}) "
            f"but Mann-Whitney one-sided p = {p_one:.4f} fails to reject 0.10."
        )
    else:
        verdict = (
            f"REFUTED — rule-bound countries' median per-decade slope ({median_bound:+.2f}) "
            f"is not lower than rule-free countries' ({median_free:+.2f}). The corpus "
            f"does not show fiscal-rule presence dampening drift."
        )

    print(f"verdict: {verdict}")
    print(f"  rule-bound n={len(bound)}, rule-free n={len(free)}")
    print(f"  median rule-bound slope/decade: {median_bound:+.2f}")
    print(f"  median rule-free slope/decade:  {median_free:+.2f}")
    print(f"  gap (bound − free): {median_gap:+.2f}")
    print(f"  Mann-Whitney one-sided p: {p_one:.4f}")

    diagnostics = {
        "verdict": verdict,
        "method": "two-sample Mann-Whitney U on per-decade drift slopes",
        "n_rule_bound": len(bound),
        "n_rule_free": len(free),
        "median_slope_rule_bound": round(median_bound, 3),
        "median_slope_rule_free": round(median_free, 3),
        "median_gap_bound_minus_free": round(median_gap, 3),
        "mann_whitney_u_bound": round(u_bound, 1),
        "mann_whitney_one_sided_p": round(p_one, 4),
        "falsification_legs": {
            "median_gap_below_minus_1": rule_a,
            "p_below_010": rule_b,
        },
        "rows": rows,
    }
    (HERE / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))

    # Manifest + result card
    rule_bound_rows = sorted([r for r in rows if r["rule_bound"] == 1], key=lambda r: r["slope_per_decade"])
    rule_free_rows = sorted([r for r in rows if r["rule_bound"] == 0], key=lambda r: r["slope_per_decade"])
    rb_table = "\n".join(
        f"| [{r['iso3']}](/country/{r['iso3']}) | {r['slope_per_decade']:+.2f} | {r['movements']} |"
        for r in rule_bound_rows
    )
    rf_table = "\n".join(
        f"| [{r['iso3']}](/country/{r['iso3']}) | {r['slope_per_decade']:+.2f} | {r['movements']} |"
        for r in rule_free_rows
    )

    card = [
        "# Result card — fiscal_rule_presence_dampens_statist_drift",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Group statistics",
        "",
        f"| Group | n | Median slope/decade | Mean slope/decade |",
        f"|---|---:|---:|---:|",
        f"| Rule-bound | {len(bound)} | {median_bound:+.2f} | {sum(bound)/len(bound):+.2f} |",
        f"| Rule-free  | {len(free)} | {median_free:+.2f} | {sum(free)/len(free):+.2f} |",
        f"| Gap (bound − free) | | **{median_gap:+.2f}** | |",
        "",
        f"Mann-Whitney one-sided p (H1: bound < free): **{p_one:.4f}**",
        "",
        "## Rule-bound countries",
        "",
        "| Country | Slope/decade | Movements |",
        "|---|---:|---:|",
        rb_table,
        "",
        "## Rule-free countries",
        "",
        "| Country | Slope/decade | Movements |",
        "|---|---:|---:|",
        rf_table,
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/fiscal_rule_presence_dampens_statist_drift.md`.",
        "Particularly relevant: rule-presence is endogenous to fiscal preferences,",
        "the binary lumps biting + non-biting rules together, and Sondervermögen-",
        "style off-balance-sheet vehicles can circumvent rules without flipping the",
        "treatment indicator.",
        "",
        "## Provenance",
        "",
        "Reproduces from `data/derived/country_drift.json` + the FISCAL_RULE_BOUND",
        "dictionary in this script. Edit the dictionary + re-run to test alternative",
        "codings (every assignment carries a citation in the YAML).",
        "",
    ]
    (HERE / "result_card.md").write_text("\n".join(card))
    (HERE / "manifest.yaml").write_text(
        "\n".join([
            "hypothesis_id: fiscal_rule_presence_dampens_statist_drift",
            "inputs:",
            "  - path: data/derived/country_drift.json",
            "    description: Built by scripts/compute_country_drift.py",
            "treatment_coding:",
            "  rule_bound: " + ", ".join(sorted([k for k, v in FISCAL_RULE_BOUND.items() if v])),
            "  rule_free:  " + ", ".join(sorted([k for k, v in FISCAL_RULE_BOUND.items() if not v])),
            "",
        ])
    )

    print(f"\nartifacts written to {HERE}")


if __name__ == "__main__":
    main()
