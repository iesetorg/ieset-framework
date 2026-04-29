#!/usr/bin/env python3
"""Replication — Reduced working-time output and employment effects.

Spec: hypotheses/growth/reduced_working_time_output_employment.yaml v1
Position-claim: degrowth #3 (school predicts: supported)

Tests whether two reduced-working-time experiments — France's 35-hour
week (event year 2000) and Iceland's four-day-week trial (event year
2015) — produced *catastrophic* output or employment consequences, as
the lump-of-labour critique predicts.

DESIGN: per-country interrupted time series (ITS). Fit a linear
pre-trend on the outcome (over a stable pre-window), project forward
into the post-window, compute the mean post-period gap (actual minus
counterfactual). The gap is in log points for GDP and percentage
points for the employment-to-population ratio.

PRIMARY (dispositive):
  SUPPORTED  if BOTH cases show
                  mean_post_log_gdp_gap >= -0.05  (no worse than -5%)
              AND mean_post_unemployment_gap <= +3.0 pp (no worse than +3pp above pre-trend).
  REFUTED    if EITHER case shows
                  mean_post_log_gdp_gap < -0.10   (worse than -10%)
              OR  mean_post_unemployment_gap > +5.0 pp.
  PARTIAL    otherwise (grey zone or one case clears, the other does not).

NOTE on data: the original spec listed employment-to-population ratio
(ilostat:SDG_0111_SEX_AGE_RT_A) but its vintage covers a non-OECD subset
that excludes FRA and ISL. We substitute the unemployment rate
(ilostat:UNE_2EAP_SEX_AGE_RT_A) with the threshold direction inverted
(catastrophe = unemployment SPIKE rather than employment drop).

INFORMATIVE: PWT avg-hours-worked (avh) trajectory — confirms the
treatment was actually delivered. PWT TFP (rtfpna) trajectory.

METHOD_VALID: each case requires >=4 pre-treatment and >=3 post-
treatment annual observations on log-GDP AND on the employment-rate
series. Verdict is `inconclusive` if not met.

Pre/post windows (chosen to avoid global-shock contamination):
  FRA: pre 1990-1999, post 2000-2007 (pre-GFC).
  ISL: pre 2005-2014, post 2015-2019 (pre-COVID).
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "reduced_working_time_output_employment"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Case definitions
CASES = {
    "FRA": {
        "label": "France 35-hour week",
        "event_year": 2000,
        "pre_window": (1990, 1999),
        "post_window": (2000, 2007),  # truncated pre-GFC
    },
    "ISL": {
        "label": "Iceland 4-day-week trial",
        "event_year": 2015,
        "pre_window": (2005, 2014),
        "post_window": (2015, 2019),  # truncated pre-COVID
    },
}

# Dispositive thresholds (log units / percentage points)
GDP_GREY_FLOOR = -0.05      # log-GDP gap >= -5% : no catastrophe (PRIMARY pass for SUPPORTED)
UNEMP_GREY_CEILING = 3.0    # unemployment-rate gap <= +3.0 pp : no catastrophe
GDP_REFUTE_BAR = -0.10      # log-GDP gap < -10% : catastrophic
UNEMP_REFUTE_BAR = 5.0      # unemployment-rate gap > +5 pp : catastrophic
MIN_PRE_OBS = 4
MIN_POST_OBS = 3


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_wdi(path: Path) -> pd.DataFrame:
    """WDI parquet → (country_iso3, year, value)."""
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])[["country_iso3", "year", "value"]]


def load_pwt(path: Path) -> pd.DataFrame:
    """PWT per-variable parquet. Most PWT files use the variable name
    as the value column; normalise to 'value' as the canonical loader does."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])[["country_iso3", "year", "value"]]


# (ILO unemployment loader removed: WDI SL.UEM.TOTL.ZS is used instead — it
# has FRA/ISL coverage from 1991, while the ILO direct indicator
# UNE_2EAP_SEX_AGE_RT_A starts at 2000 for FRA leaving no pre-window.)


def fit_its(country: str, df: pd.DataFrame, value_col: str,
            pre_window: tuple[int, int], post_window: tuple[int, int],
            outcome_label: str) -> dict:
    """Linear pre-trend ITS. Returns mean post-period gap and diagnostics."""
    sub = df[df["country_iso3"] == country].copy().sort_values("year")
    pre = sub[(sub["year"] >= pre_window[0]) & (sub["year"] <= pre_window[1])]
    post = sub[(sub["year"] >= post_window[0]) & (sub["year"] <= post_window[1])]

    n_pre = int(len(pre))
    n_post = int(len(post))
    method_valid = (n_pre >= MIN_PRE_OBS) and (n_post >= MIN_POST_OBS)

    if not method_valid:
        return {
            "outcome": outcome_label,
            "country": country,
            "n_pre": n_pre,
            "n_post": n_post,
            "method_valid": False,
            "error": (
                f"insufficient obs (pre={n_pre} need >={MIN_PRE_OBS}; "
                f"post={n_post} need >={MIN_POST_OBS})"
            ),
        }

    pre_x = pre["year"].astype(float).values
    pre_y = pre[value_col].astype(float).values
    a, b = np.polyfit(pre_x, pre_y, 1)  # y = a*year + b

    post_x = post["year"].astype(float).values
    post_y = post[value_col].astype(float).values
    counterfactual = a * post_x + b
    gap = post_y - counterfactual

    pre_resid = pre_y - (a * pre_x + b)
    pre_sd = float(np.std(pre_resid, ddof=1)) if n_pre > 1 else 0.0
    mean_gap = float(np.mean(gap))
    end_gap = float(gap[-1])

    return {
        "outcome": outcome_label,
        "country": country,
        "method_valid": True,
        "n_pre": n_pre,
        "n_post": n_post,
        "pre_window": list(pre_window),
        "post_window": list(post_window),
        "pre_trend_slope": float(a),
        "pre_trend_intercept": float(b),
        "pre_residual_sd": pre_sd,
        "mean_post_gap": mean_gap,
        "end_post_gap": end_gap,
        "z_mean_gap": (mean_gap / pre_sd) if pre_sd > 0 else None,
        "post_actuals": [float(v) for v in post_y],
        "post_counterfactuals": [float(v) for v in counterfactual],
        "post_years": [int(y) for y in post_x],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----- Load series -----
    gdp_path = latest("world_bank_wdi", "NY.GDP.MKTP.KD")
    une_path = latest("world_bank_wdi", "SL.UEM.TOTL.ZS")
    avh_path = latest("pwt", "avh")
    tfp_path = latest("pwt", "rtfpna")

    manifest = {
        "real_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.MKTP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "unemployment_rate": {
            "publisher": "world_bank_wdi",
            "series": "SL.UEM.TOTL.ZS",
            "vintage_file": str(une_path.relative_to(REPO_ROOT)),
            "sha256": sha256(une_path),
        },
        "pwt_avg_hours_worked": {
            "publisher": "pwt",
            "series": "avh",
            "vintage_file": str(avh_path.relative_to(REPO_ROOT)),
            "sha256": sha256(avh_path),
        },
        "pwt_tfp_rtfpna": {
            "publisher": "pwt",
            "series": "rtfpna",
            "vintage_file": str(tfp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(tfp_path),
        },
    }

    gdp = load_wdi(gdp_path)
    gdp["log_value"] = np.log(gdp["value"])
    gdp_log = gdp[["country_iso3", "year", "log_value"]].rename(columns={"log_value": "value"})
    une = load_wdi(une_path)
    avh = load_pwt(avh_path)
    tfp = load_pwt(tfp_path)

    # ----- Per-case ITS on PRIMARY outcomes -----
    case_results: dict[str, dict] = {}
    for country, info in CASES.items():
        gdp_its = fit_its(
            country, gdp_log, "value",
            info["pre_window"], info["post_window"], "log_real_gdp",
        )
        une_its = fit_its(
            country, une, "value",
            info["pre_window"], info["post_window"], "unemployment_rate",
        )
        # Informative ITS (not gating)
        avh_its = fit_its(
            country, avh, "value",
            info["pre_window"], info["post_window"], "avg_hours_worked_pwt",
        )
        tfp_its = fit_its(
            country, tfp, "value",
            info["pre_window"], info["post_window"], "tfp_rtfpna_pwt",
        )

        # Per-case verdict bucket
        bucket = "unknown"
        if not (gdp_its.get("method_valid") and une_its.get("method_valid")):
            bucket = "inconclusive"
        else:
            g = gdp_its["mean_post_gap"]
            u = une_its["mean_post_gap"]   # unemployment-rate gap (pp)
            catastrophic_gdp = g < GDP_REFUTE_BAR
            catastrophic_une = u > UNEMP_REFUTE_BAR
            ok_gdp = g >= GDP_GREY_FLOOR
            ok_une = u <= UNEMP_GREY_CEILING
            if catastrophic_gdp or catastrophic_une:
                bucket = "catastrophic"
            elif ok_gdp and ok_une:
                bucket = "ok_no_catastrophe"
            else:
                bucket = "grey_zone"

        case_results[country] = {
            "label": info["label"],
            "event_year": info["event_year"],
            "bucket": bucket,
            "log_gdp_its": gdp_its,
            "unemployment_rate_its": une_its,
            "informative_avg_hours_its": avh_its,
            "informative_tfp_its": tfp_its,
        }

    # ----- Cross-case verdict -----
    buckets = [r["bucket"] for r in case_results.values()]
    n_inconclusive = buckets.count("inconclusive")
    n_catastrophic = buckets.count("catastrophic")
    n_ok = buckets.count("ok_no_catastrophe")
    n_grey = buckets.count("grey_zone")

    if n_inconclusive >= 1:
        verdict = (
            f"inconclusive — {n_inconclusive} of 2 treated cases lack sufficient "
            f"pre/post coverage to fit ITS (case method-validity gate: "
            f">={MIN_PRE_OBS} pre, >={MIN_POST_OBS} post). Per-case status: "
            + ", ".join(f"{c}={r['bucket']}" for c, r in case_results.items())
            + "."
        )
    elif n_catastrophic >= 1:
        details = []
        for c, r in case_results.items():
            g = r["log_gdp_its"]["mean_post_gap"]
            u = r["unemployment_rate_its"]["mean_post_gap"]
            details.append(
                f"{c}: log-GDP gap {g*100:+.2f} pp, unemployment gap {u:+.2f} pp"
            )
        verdict = (
            f"refuted — at least one case (of 2) shows a catastrophic post-"
            f"event gap (log-GDP < {GDP_REFUTE_BAR*100:.0f}% or unemployment > "
            f"+{UNEMP_REFUTE_BAR:.0f} pp): "
            + "; ".join(details) + "."
        )
    elif n_ok == 2:
        details = []
        for c, r in case_results.items():
            g = r["log_gdp_its"]["mean_post_gap"]
            u = r["unemployment_rate_its"]["mean_post_gap"]
            details.append(
                f"{c}: log-GDP gap {g*100:+.2f} pp, unemployment gap {u:+.2f} pp"
            )
        verdict = (
            f"SUPPORTED — both treated cases satisfy the no-catastrophe primary "
            f"(log-GDP gap >= {GDP_GREY_FLOOR*100:.0f}% AND unemployment gap <= "
            f"+{UNEMP_GREY_CEILING:.1f} pp). "
            + "; ".join(details) + "."
        )
    else:  # at least one grey-zone case
        details = []
        for c, r in case_results.items():
            g = r["log_gdp_its"]["mean_post_gap"]
            u = r["unemployment_rate_its"]["mean_post_gap"]
            details.append(
                f"{c}={r['bucket']} (log-GDP gap {g*100:+.2f} pp, unemployment gap {u:+.2f} pp)"
            )
        verdict = (
            f"partial — neither case is catastrophic, but at least one falls in "
            f"the grey zone between the SUPPORTED bar (log-GDP >= "
            f"{GDP_GREY_FLOOR*100:.0f}% AND unemployment <= +{UNEMP_GREY_CEILING:.1f} pp) "
            f"and the REFUTED bar. Per-case: " + "; ".join(details) + "."
        )

    diagnostics = {
        "verdict": verdict,
        "thresholds": {
            "gdp_grey_floor_log": GDP_GREY_FLOOR,
            "unemployment_grey_ceiling_pp": UNEMP_GREY_CEILING,
            "gdp_refute_bar_log": GDP_REFUTE_BAR,
            "unemployment_refute_bar_pp": UNEMP_REFUTE_BAR,
            "min_pre_obs": MIN_PRE_OBS,
            "min_post_obs": MIN_POST_OBS,
        },
        "n_cases_total": len(CASES),
        "n_cases_inconclusive": n_inconclusive,
        "n_cases_catastrophic": n_catastrophic,
        "n_cases_ok": n_ok,
        "n_cases_grey": n_grey,
        "cases": case_results,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ----- Chart: log-GDP actual vs counterfactual, per case -----
    series = []
    palette_actual = {"FRA": "#0055A4", "ISL": "#02529C"}
    palette_cf = {"FRA": "#9CA3AF", "ISL": "#9CA3AF"}
    for country, r in case_results.items():
        gdp_sub = (
            gdp_log[gdp_log["country_iso3"] == country][["year", "value"]]
            .dropna().sort_values("year")
        )
        if gdp_sub.empty:
            continue
        # Normalise to the event year value (subtract event-year log-GDP).
        ev = CASES[country]["event_year"]
        ev_rows = gdp_sub[gdp_sub["year"] == ev]
        baseline = float(ev_rows["value"].iloc[0]) if not ev_rows.empty else float(gdp_sub["value"].iloc[0])
        actual_pts = [
            {"x": int(row.year), "y": float(row.value - baseline)}
            for row in gdp_sub.itertuples()
        ]
        series.append({
            "id": f"{country}_actual",
            "label": f"{country} log-GDP (actual, normalised to event year)",
            "color": palette_actual.get(country, "#000000"),
            "treated": True,
            "points": actual_pts,
        })
        # Counterfactual extension: pre-trend slope * year + intercept, normalised
        gdp_its = r["log_gdp_its"]
        if gdp_its.get("method_valid"):
            a = gdp_its["pre_trend_slope"]
            b = gdp_its["pre_trend_intercept"]
            cf_years = list(range(CASES[country]["pre_window"][0],
                                   CASES[country]["post_window"][1] + 1))
            cf_pts = [
                {"x": y, "y": float(a * y + b - baseline)}
                for y in cf_years
            ]
            series.append({
                "id": f"{country}_counterfactual",
                "label": f"{country} pre-trend counterfactual",
                "color": palette_cf.get(country, "#888888"),
                "treated": False,
                "points": cf_pts,
            })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Log real GDP — actual vs pre-trend counterfactual (event-year normalised)",
        "subtitle": " · ".join(
            f"{c}: log-GDP mean post-gap "
            f"{r['log_gdp_its'].get('mean_post_gap', float('nan'))*100:+.2f} pp"
            for c, r in case_results.items()
            if r["log_gdp_its"].get("method_valid")
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Log real GDP minus event-year value", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vertical_line", "x": 2000, "label": "FRA: 35-hour week (2000)"},
            {"type": "vertical_line", "x": 2015, "label": "ISL: 4-day-week trial (2015)"},
            {
                "type": "note",
                "label": (
                    f"Catastrophe bar: log-GDP gap < {GDP_REFUTE_BAR*100:.0f}% "
                    f"or unemployment-rate gap > +{UNEMP_REFUTE_BAR:.0f} pp."
                ),
            },
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ----- Coefficients table -----
    coef_rows = []
    for country, r in case_results.items():
        for spec_label, its in (
            ("primary_log_gdp", r["log_gdp_its"]),
            ("primary_unemployment_rate", r["unemployment_rate_its"]),
            ("informative_avg_hours", r["informative_avg_hours_its"]),
            ("informative_tfp", r["informative_tfp_its"]),
        ):
            if its.get("method_valid"):
                coef_rows.append({
                    "spec": f"{spec_label}_{country}",
                    "term": "mean_post_gap",
                    "estimate": its["mean_post_gap"],
                })
                coef_rows.append({
                    "spec": f"{spec_label}_{country}",
                    "term": "end_post_gap",
                    "estimate": its["end_post_gap"],
                })
                coef_rows.append({
                    "spec": f"{spec_label}_{country}",
                    "term": "pre_residual_sd",
                    "estimate": its["pre_residual_sd"],
                })
            else:
                coef_rows.append({
                    "spec": f"{spec_label}_{country}",
                    "term": "method_invalid",
                    "estimate": float("nan"),
                })
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ----- Manifest -----
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + "".join(
            f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
            + (f"    filter: {v['filter']}\n" if 'filter' in v else "")
            + f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
            for k, v in manifest.items()
        )
    )

    # ----- Result card -----
    card = [
        f"# Reduced working-time experiments — output and employment effects",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Two treated cases tested with per-country interrupted time series:",
        "",
    ]
    for country, r in case_results.items():
        info = CASES[country]
        card.append(f"### {country} — {info['label']} (event year {info['event_year']})")
        card.append("")
        card.append(f"- Bucket: **{r['bucket']}**")
        for label, its in (
            ("PRIMARY log real GDP", r["log_gdp_its"]),
            ("PRIMARY unemployment rate", r["unemployment_rate_its"]),
            ("INFORMATIVE PWT avg hours worked", r["informative_avg_hours_its"]),
            ("INFORMATIVE PWT TFP (rtfpna)", r["informative_tfp_its"]),
        ):
            if its.get("method_valid"):
                unit = "log pp" if "log" in its["outcome"] else "units"
                card.append(
                    f"- {label}: mean post-gap = "
                    f"{its['mean_post_gap']*100:+.2f} pp (log) / "
                    f"{its['mean_post_gap']:+.4g} ({unit}); "
                    f"n_pre={its['n_pre']}, n_post={its['n_post']}, "
                    f"pre-window={its['pre_window']}, post-window={its['post_window']}."
                )
            else:
                card.append(f"- {label}: METHOD-INVALID — {its.get('error','no data')}")
        card.append("")

    card += [
        "## Method",
        "",
        "Per-country interrupted time series. For each treated case "
        "(France 2000, Iceland 2015):",
        "",
        "1. Fit a linear pre-trend on the outcome over the pre-window.",
        "2. Project forward into the post-window.",
        "3. Compute mean post-period gap = mean(actual minus counterfactual).",
        "",
        f"**SUPPORTED** if BOTH cases satisfy: log-GDP gap >= "
        f"{GDP_GREY_FLOOR*100:.0f}% AND unemployment gap <= "
        f"+{UNEMP_GREY_CEILING:.1f} pp.",
        f"**REFUTED** if EITHER case shows: log-GDP gap < "
        f"{GDP_REFUTE_BAR*100:.0f}% OR unemployment gap > "
        f"+{UNEMP_REFUTE_BAR:.1f} pp.",
        "**PARTIAL** otherwise; **inconclusive** if a case lacks "
        f">={MIN_PRE_OBS} pre and >={MIN_POST_OBS} post observations.",
        "",
        "Pre/post windows are truncated to avoid global-shock contamination "
        "(FRA post = 2000-2007 pre-GFC; ISL post = 2015-2019 pre-COVID).",
        "",
        "## Caveats",
        "",
        "- A linear pre-trend extrapolation discards within-window dynamics "
        "(business-cycle, oil shocks). Confidence is low when the pre-window "
        "residual SD is large relative to the measured post-gap.",
        "- 'Catastrophic' is defined ex-ante at -10% log-GDP / -5pp employment "
        "as the REFUTED bar; the SUPPORTED bar (-5% / -3pp) is intentionally "
        "tight given that the original claim emphasises 'catastrophic'.",
        "- Iceland's 4-day-week trial covered ~1.3% of the workforce at peak "
        "and was voluntary; absence of macro effect is mechanically expected. "
        "See `hypotheses/steelman/reduced_working_time_output_employment.md`.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.MKTP.KD",
        f"- world_bank_wdi:SL.UEM.TOTL.ZS (unemployment rate, % total labour force, ILO-modelled)",
        f"- pwt:avh (avg hours worked — informative)",
        f"- pwt:rtfpna (TFP — informative)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
