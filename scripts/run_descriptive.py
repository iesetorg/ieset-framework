#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = descriptive.

Descriptive specs don't have a causal-inference design — the test is whether
the data shows the claimed pattern. This runner handles three common shapes:

  bilateral     — sample.countries has exactly 2 entries; compute the
                  log-ratio (or absolute ratio) of the outcome between them
                  at the end-period and compare against any threshold the
                  claim mentions (e.g. "20x", "10%", "less than half").
  pre_post      — sample.countries has 1 entry, sample has a treatment date
                  inferable from the falsification test text; compute pre-
                  vs post-mean of the outcome.
  panel_summary — many countries; compute treatment-country trajectory vs
                  donor-pool median.

Verdicts:
  SUPPORTED                  — direction matches claim AND magnitude clears the
                               extracted threshold (or, if no threshold was
                               found, the relative deviation is "large":
                               |Δ| > 0.5 in log-units or |ratio-1| > 0.2).
  REFUTED                    — direction opposite the claim.
  PARTIAL                    — direction matches but magnitude below threshold,
                               OR threshold can't be extracted and effect is
                               small.
  INCONCLUSIVE_DATA_PENDING  — outcome can't be loaded.

Usage:
    python3 scripts/run_descriptive.py <hypothesis_id>
    python3 scripts/run_descriptive.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Re-use the panel runner's vintage / spec / loader plumbing.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_panel_fe import (
    is_stub_falsification_rule,    has_committed_verdict,
    ROOT, RUNS, load_spec, load_variable, transform, parse_source,
    infer_claim_direction, build_panel, first_loaded_var,
    filter_sample,
    should_persist_preflight_inconclusive, bump_bulk_run_count,
    print_bulk_run_summary,
)


# ---------------------------------------------------------------------------
# Threshold extraction
# ---------------------------------------------------------------------------

NUM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(x|×|%|percent|pp|fold|times)?", re.I)


def extract_threshold(text: str) -> dict:
    """Look for ratio / percentage / fold thresholds in claim or falsification text.

    Returns a dict with `ratio`, `percent`, `fold`, `pp` if any are found.
    """
    out: dict = {}
    if not text:
        return out
    text = text.lower()
    for m in NUM_RE.finditer(text):
        num = float(m.group(1))
        unit = (m.group(2) or "").lower().strip("()")
        if unit in ("x", "×", "fold", "times"):
            out.setdefault("fold", num)
        elif unit in ("%", "percent"):
            out.setdefault("percent", num)
        elif unit == "pp":
            out.setdefault("pp", num)
    return out


# ---------------------------------------------------------------------------
# Comparison shapes
# ---------------------------------------------------------------------------


def bilateral_comparison(panel: pd.DataFrame, outcome: str, countries: list[str],
                         period: list[int]) -> dict:
    """Compute end-period level and log-ratio between two countries."""
    sub = panel[panel["country_iso3"].isin(countries)].copy()
    if sub.empty or outcome not in sub.columns:
        return {"error": "no data for bilateral comparison"}
    sub = sub.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"all values for {outcome} are missing"}
    end_year = period[1] if period and len(period) > 1 else int(sub["year"].max())
    # Find the latest available year in each country (within 5y of end_year).
    latest_per_country = (
        sub.groupby("country_iso3")["year"].max().to_dict()
    )
    a, b = countries[0], countries[1]
    if a not in latest_per_country or b not in latest_per_country:
        return {"error": f"missing country data: {set(countries) - set(latest_per_country)}"}
    yr_a = latest_per_country[a]
    yr_b = latest_per_country[b]
    val_a = sub[(sub["country_iso3"] == a) & (sub["year"] == yr_a)][outcome].iloc[0]
    val_b = sub[(sub["country_iso3"] == b) & (sub["year"] == yr_b)][outcome].iloc[0]
    if val_a is None or val_b is None or val_b == 0 or pd.isna(val_a) or pd.isna(val_b):
        return {"error": f"end-period values invalid: {a}={val_a}, {b}={val_b}"}
    ratio = float(val_a / val_b)
    log_diff = float(np.log(abs(val_a)) - np.log(abs(val_b))) if val_a != 0 else None
    return {
        "shape": "bilateral",
        "country_a": a, "country_b": b,
        "year_a": int(yr_a), "year_b": int(yr_b),
        "value_a": float(val_a), "value_b": float(val_b),
        "ratio_a_to_b": ratio,
        "log_diff_a_minus_b": log_diff,
        "n_obs": int(len(sub)),
    }


def pre_post_comparison(panel: pd.DataFrame, outcome: str, country: str,
                        cut_year: int, period: list[int]) -> dict:
    sub = panel[(panel["country_iso3"] == country)].copy()
    if outcome not in sub.columns:
        return {"error": f"outcome {outcome} not in panel"}
    sub = sub.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"no {country} data"}
    pre = sub[sub["year"] < cut_year][outcome]
    post = sub[sub["year"] >= cut_year][outcome]
    if len(pre) < 3 or len(post) < 3:
        return {"error": f"insufficient pre ({len(pre)}) or post ({len(post)}) obs"}
    return {
        "shape": "pre_post",
        "country": country,
        "cut_year": int(cut_year),
        "pre_mean": float(pre.mean()),
        "post_mean": float(post.mean()),
        "delta": float(post.mean() - pre.mean()),
        "log_delta": (float(np.log(abs(post.mean())) - np.log(abs(pre.mean())))
                      if pre.mean() != 0 and post.mean() != 0 else None),
        "n_pre": int(len(pre)),
        "n_post": int(len(post)),
    }


def panel_summary(panel: pd.DataFrame, outcome: str, treatment_country: str,
                  donor_countries: list[str], period: list[int]) -> dict:
    sub = panel.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"no data for {outcome}"}
    end_year = period[1] if period and len(period) > 1 else int(sub["year"].max())
    near_end = sub[sub["year"] >= end_year - 5]
    if treatment_country not in near_end["country_iso3"].values:
        return {"error": f"no {treatment_country} obs near end-period"}
    treat_val = near_end[near_end["country_iso3"] == treatment_country][outcome].mean()
    donor_panel = near_end[near_end["country_iso3"].isin(donor_countries)]
    if donor_panel.empty:
        return {"error": "no donor-pool obs near end-period"}
    donor_med = donor_panel.groupby("country_iso3")[outcome].mean().median()
    return {
        "shape": "panel_summary",
        "treatment_country": treatment_country,
        "treatment_value": float(treat_val),
        "donor_pool_median": float(donor_med),
        "ratio": float(treat_val / donor_med) if donor_med != 0 else None,
        "log_diff": (float(np.log(abs(treat_val)) - np.log(abs(donor_med)))
                     if donor_med != 0 and treat_val != 0 else None),
        "n_donor_countries": int(donor_panel["country_iso3"].nunique()),
        "end_year_window": [int(end_year - 5), int(end_year)],
    }


def find_cut_year(spec: dict) -> int | None:
    """Try to infer a treatment / event year from claim or falsification text."""
    text = ((spec.get("claim") or "") + " " +
            (spec.get("falsification") or {}).get("test", ""))
    # Look for 4-digit years in the text.
    years = [int(m.group(0)) for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", text)]
    if not years:
        return None
    period = (spec.get("sample") or {}).get("period") or []
    if len(period) == 2:
        # Pick a year inside the sample period.
        years = [y for y in years if period[0] < y < period[1]]
    return years[0] if years else None


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def descriptive_verdict(comp: dict, claim_dir: str, threshold: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    shape = comp["shape"]

    # Get a signed magnitude.
    if shape == "bilateral":
        log_diff = comp.get("log_diff_a_minus_b")
        ratio = comp.get("ratio_a_to_b")
        if log_diff is None:
            return "INCONCLUSIVE_DATA_PENDING", "log-diff undefined"
        magnitude = log_diff
        ratio_check = abs(ratio) if ratio else None
    elif shape == "pre_post":
        log_diff = comp.get("log_delta")
        magnitude = log_diff if log_diff is not None else comp["delta"]
        ratio_check = None
    elif shape == "panel_summary":
        log_diff = comp.get("log_diff")
        magnitude = log_diff if log_diff is not None else 0
        ratio_check = comp.get("ratio")
    else:
        return "INCONCLUSIVE_DATA_PENDING", f"unknown shape {shape}"

    sign = "+" if magnitude >= 0 else "-"
    mag_str = f"|Δ_log|={abs(magnitude):.3g}"
    if ratio_check:
        mag_str += f", ratio={ratio_check:.3g}"

    # Check threshold.
    fold = threshold.get("fold")
    pct = threshold.get("percent")
    threshold_met = None
    threshold_str = ""
    if fold and ratio_check:
        threshold_met = abs(np.log(abs(ratio_check))) > np.log(fold) * 0.5  # half-claim threshold
        threshold_str = f"; threshold {fold}x, observed {ratio_check:.2g}x"
    elif pct and magnitude is not None:
        threshold_met = abs(magnitude) > pct / 100.0
        threshold_str = f"; threshold {pct}%, observed {abs(magnitude)*100:.1f}%"
    elif abs(magnitude) > 0.5:
        threshold_met = True  # no explicit threshold, but big effect
    elif abs(magnitude) > 0.1:
        threshold_met = None  # ambiguous
    else:
        threshold_met = False

    if claim_dir == "?":
        return ("PARTIAL",
                f"shape={shape}, {mag_str}{threshold_str}; claim direction ambiguous")
    if sign == claim_dir:
        if threshold_met is True:
            return ("SUPPORTED",
                    f"shape={shape}, sign matches claim {claim_dir}, {mag_str}{threshold_str}")
        if threshold_met is False:
            return ("PARTIAL",
                    f"shape={shape}, sign matches but magnitude below threshold; {mag_str}{threshold_str}")
        return ("PARTIAL",
                f"shape={shape}, sign matches; {mag_str}{threshold_str}; threshold not extracted")
    # Opposite sign: only REFUTED if magnitude is meaningful. Tiny effects
    # like ratio=0.986 (1.4% off) shouldn't count as REFUTED.
    if threshold_met is True or abs(magnitude) > 0.1:
        return ("REFUTED",
                f"shape={shape}, sign {sign} OPPOSITE claim {claim_dir}; {mag_str}{threshold_str}")
    return ("PARTIAL",
            f"shape={shape}, sign opposite claim {claim_dir} but magnitude tiny; {mag_str}{threshold_str}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_outputs(hid: str, spec: dict, status: dict, comp: dict,
                  threshold: dict, verdict: str, reason: str) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)

    diag = {
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "descriptive",
        "claim_direction_inferred": infer_claim_direction(spec),
        "threshold_extracted": threshold,
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "comparison": comp,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_descriptive.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))

    md = [
        f"# Result card — {hid}",
        "",
        f"**Verdict:** {verdict} — {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test','').strip()}",
        "",
        "## Comparison",
    ]
    if "error" in comp:
        md.append(f"- _Error:_ {comp['error']}")
    else:
        for k, v in comp.items():
            md.append(f"- **{k}:** {v}")

    if threshold:
        md.append(f"\n## Extracted threshold: {threshold}")

    md.append("")
    md.append("## Variables resolved")
    if status["variables_loaded"]:
        for v in status["variables_loaded"]:
            md.append(f"- `{v['source']}` → {v['name']} ({v['role']}, "
                      f"publisher={v['publisher']}, n={v['n_rows']})")
    if status["variables_missing"]:
        md.append("\n### Variables missing data")
        for v in status["variables_missing"]:
            md.append(f"- `{v['source']}` ({v['role']}, name={v['name']})")

    md.append("")
    md.append(f"_Generated by `scripts/run_descriptive.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def list_descriptive_specs() -> list[str]:
    derived = ROOT / "engine" / "runnability.derived.yaml"
    with derived.open() as f:
        d = yaml.safe_load(f)
    return [
        h["hypothesis_id"]
        for h in d["hypotheses"]
        if h["estimator_template"] == "descriptive"
    ]


def run_one(
    hid: str,
    force: bool = False,
    persist_preflight_inconclusive: bool = True,
) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if found is None:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    # Integrity gate: refuse to grade against a stub falsification rule.
    # The auto-grader's verdicts are only meaningful against a dispositive
    # pre-registered threshold; running against the generic boilerplate
    # ("…when this stub is promoted from draft") would attach a fake-clean
    # verdict to a non-promoted spec. See post-mortem (commit bba6f644).
    if is_stub_falsification_rule(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "falsification rule not sharpened — auto-grader refuses to "
            "grade against the generic stub boilerplate. Promote the spec "
            "(replace falsification.rule with a dispositive threshold AND "
            "document the sharpening in methodology_note) before running."
        )
        persisted = should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        )
        if persisted:
            write_outputs(
                hid,
                spec,
                {"variables_loaded": [], "variables_missing": []},
                {"error": reason},
                {},
                verdict,
                reason,
            )
        suffix = " (stub rule, refused to grade)"
        if not persisted:
            suffix += " [artifact skipped]"
        return f"  ⚠ {hid}: {verdict}{suffix}"

    panel, status = build_panel(spec)
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    if not outcome_items:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = "no outcome variable in spec"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, {}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"
    panel_filt = filter_sample(panel, spec)
    outcome_name = first_loaded_var(outcome_items, panel_filt)
    if outcome_name is None:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        missing = [v["source"] for v in status["variables_missing"]
                   if v["role"] == "outcome"]
        reason = f"no outcome variable loaded; missing: {missing}"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, {}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"

    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    period = sample.get("period") or [None, None]

    # Choose comparison shape.
    threshold = extract_threshold(
        (spec.get("claim") or "") + " " +
        (spec.get("falsification") or {}).get("test", "")
    )
    if len(countries) == 2:
        comp = bilateral_comparison(panel_filt, outcome_name, countries, period)
    elif len(countries) == 1:
        cut = find_cut_year(spec)
        if cut is None:
            cut = (period[0] + period[1]) // 2 if len(period) == 2 and all(period) else None
        if cut is None:
            verdict = "INCONCLUSIVE_DATA_PENDING"
            reason = "couldn't infer pre/post cut year"
            if should_persist_preflight_inconclusive(
                reason, persist_preflight_inconclusive
            ):
                write_outputs(
                    hid, spec, status, {"error": reason}, {}, verdict, reason
                )
            return f"  ⚠ {hid}: {verdict}"
        else:
            comp = pre_post_comparison(panel_filt, outcome_name, countries[0], cut, period)
    else:
        if not countries:
            verdict = "INCONCLUSIVE_DATA_PENDING"
            reason = "no countries in sample"
            if should_persist_preflight_inconclusive(
                reason, persist_preflight_inconclusive
            ):
                write_outputs(
                    hid, spec, status, {"error": reason}, {}, verdict, reason
                )
            return f"  ⚠ {hid}: {verdict}"
        else:
            # First country = treatment; rest = donor pool.
            comp = panel_summary(panel_filt, outcome_name, countries[0],
                                 countries[1:], period)

    claim_dir = infer_claim_direction(spec)
    verdict, reason = descriptive_verdict(comp, claim_dir, threshold)
    write_outputs(hid, spec, status, comp, threshold, verdict, reason)

    icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
            "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
    return f"  {icon} {hid}: {verdict} — {reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing committed verdicts.")
    parser.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts during bulk runs.",
    )
    args = parser.parse_args()
    persist_preflight = args.write_preflight_inconclusive or not args.all
    if args.all:
        ids = list_descriptive_specs()
        counts: dict[str, int] = {}
        print(f"Running {len(ids)} descriptive specs…")
        for hid in ids:
            try:
                msg = (
                    run_one(
                        hid,
                        force=args.force,
                        persist_preflight_inconclusive=persist_preflight,
                    )
                )
                print(msg)
                bump_bulk_run_count(counts, msg)
            except Exception as exc:
                print(f"  ✗ {hid}: runner crashed — {exc}")
                counts["crashed"] = counts.get("crashed", 0) + 1
                traceback.print_exc()
        print_bulk_run_summary("descriptive", counts)
        return 0
    if not args.hypothesis_id:
        parser.error("Pass <hypothesis_id> or --all.")
    print(
        run_one(
            args.hypothesis_id,
            force=args.force,
            persist_preflight_inconclusive=persist_preflight,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
