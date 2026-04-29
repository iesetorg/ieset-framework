#!/usr/bin/env python3
"""Replication — Eurozone fiscal-rule departure -> sovereign-spread response.

Spec: hypotheses/fiscal/fiscal_rule_departure_credibility_loss_effect.yaml v1
Position-claim: ordoliberal #8 (school predicts: supported)

Tests the ordoliberal claim that documented periphery EDP-escalation /
SGP-breach / major-budget-revision events in 2009-2012 produced a
mean cumulative h=20 trading-day sovereign-spread response (10y
country yield over the German Bund) of at least +50 bp.

Pre-registered event panel (mirrors hypotheses/steelman/<id>.md):
  GRC 2009-10-20  ELSTAT/Papandreou deficit revision
  GRC 2009-12-08  Fitch downgrade to BBB+
  IRL 2010-09-30  bank-sector recap / EDP intensification
  PRT 2010-04-27  S&P downgrade to A- / EDP intensification
  ESP 2010-04-28  S&P downgrade to AA / EDP escalation
  ITA 2011-08-05  ECB Trichet-Draghi letter / BTP-Bund blowout

Falsification thresholds (made dispositive):
  SUPPORTED — mean cumulative h=20 spread response >= +50 bp.
  PARTIAL   — mean response in (+25, +50) bp range.
  REFUTED   — mean response <= +25 bp OR wrong sign.
  INCONCLUSIVE_DATA_PENDING — per-country eurozone 10y yield series
    or German Bund 10y series missing on disk.

Method-validity gate (per HYPOTHESIS_FRAMEWORK_AUDIT §E2): missing
yield-series data emits `inconclusive (data gap on <publisher>:<series>)`,
NOT a refutation. The current vintage tree contains:
  - ecb/: only BSI (M3 money supply) and EXR (USD/EUR FX). No IRS
    (long-term interest-rate convergence-criteria) family on disk.
  - fred/: only DGS10 (US 10y treasury). No IRLTLT01* country
    re-publications of OECD MEI long-term rates.
  - fred/IRLTLT01DEM156N (Bund 10y) NOT on disk.
The script therefore documents the missing series in the manifest
and emits the dispositive `inconclusive (data gap)` verdict. Once a
fetcher lands the per-country yield series the verdict computation
will run unchanged.

The OMT-activation window 2012-09-06 to 2013-03-31 is excluded so
ECB-backstop news cannot contaminate the fiscal-news signal.
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
HID = "fiscal_rule_departure_credibility_loss_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Pre-registered EDP-escalation / budget-revision event panel.
# (country_iso3, ISO date string, label)
EVENT_PANEL: list[tuple[str, str, str]] = [
    ("GRC", "2009-10-20", "ELSTAT/Papandreou deficit revision"),
    ("GRC", "2009-12-08", "Fitch downgrade GRC to BBB+"),
    ("IRL", "2010-09-30", "IRL bank recap / EDP intensification"),
    ("PRT", "2010-04-27", "S&P downgrade PRT to A-"),
    ("ESP", "2010-04-28", "S&P downgrade ESP to AA"),
    ("ITA", "2011-08-05", "ECB Trichet-Draghi letter / BTP-Bund blowout"),
]
EVENT_HORIZON_DAYS = 20  # trading days; window mechanics walk the daily index

# OMT-activation window — exclude any event whose +20-day horizon
# touches this window (Draghi 'whatever it takes' 2012-07-26;
# OMT formal announcement 2012-09-06; spread compression through
# early 2013).
OMT_WINDOW_START = pd.Timestamp("2012-09-06")
OMT_WINDOW_END = pd.Timestamp("2013-03-31")

# Falsification thresholds (in basis points; positive = spread widened).
THRESHOLD_SUPPORTED_BP = 50.0
THRESHOLD_PARTIAL_FLOOR_BP = 25.0

# Per-country FRED IRLTLT01 series codes (OECD MEI long-term rates,
# monthly, re-published by FRED). Used by the once-fetched runner.
FRED_LT_SERIES: dict[str, str] = {
    "GRC": "IRLTLT01GRM156N",
    "IRL": "IRLTLT01IEM156N",
    "PRT": "IRLTLT01PTM156N",
    "ESP": "IRLTLT01ESM156N",
    "ITA": "IRLTLT01ITM156N",
    "DEU": "IRLTLT01DEM156N",  # Bund 10y, the spread reference
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_optional(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_daily(path: Path) -> pd.DataFrame:
    """Normalise to (date, value).

    FRED on-disk schema: (date, value, realtime_start, realtime_end).
    Monthly series share the same shape; date is the period anchor.
    """
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns or "value" not in t.columns:
        raise ValueError(f"{path}: need (date,value), got {list(t.columns)}")
    t = t[["date", "value"]].copy()
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna().sort_values("date").reset_index(drop=True)


def cumulative_response(yld_country: pd.DataFrame, yld_bund: pd.DataFrame,
                         event_date: pd.Timestamp,
                         horizon: int) -> dict:
    """Compute the spread (country-yield - Bund) at t-1 (last close
    before the event) and at t+horizon trading-day close, return the
    change in basis points. yields are in percent so 1.0 unit = 100 bp."""
    def anchor(df: pd.DataFrame, t0: pd.Timestamp) -> tuple[int, pd.Timestamp]:
        sub = df[df["date"] >= t0 - pd.Timedelta(days=14)]
        sub = sub[sub["date"] <= t0 + pd.Timedelta(days=60)]
        sub = sub.sort_values("date").reset_index(drop=True)
        on_or_after = sub[sub["date"] >= t0]
        if on_or_after.empty:
            return -1, sub
        return on_or_after.index[0], sub

    a_c, sub_c = anchor(yld_country, event_date)
    a_b, sub_b = anchor(yld_bund, event_date)
    if a_c < 0 or a_b < 0:
        return {"error": "no obs at/after event for one of the series"}
    if a_c == 0 or a_b == 0:
        return {"error": "no pre-event obs to anchor t-1 close"}
    pre_c = sub_c.iloc[a_c - 1]
    pre_b = sub_b.iloc[a_b - 1]
    t_c = a_c + horizon
    t_b = a_b + horizon
    if t_c >= len(sub_c) or t_b >= len(sub_b):
        return {"error": f"need {horizon} trading days post-event; insufficient"}
    post_c = sub_c.iloc[t_c]
    post_b = sub_b.iloc[t_b]
    pre_spread_bp = (float(pre_c["value"]) - float(pre_b["value"])) * 100.0
    post_spread_bp = (float(post_c["value"]) - float(post_b["value"])) * 100.0
    return {
        "pre_event_date": pre_c["date"].date().isoformat(),
        "pre_spread_bp": pre_spread_bp,
        "post_event_date": post_c["date"].date().isoformat(),
        "post_spread_bp": post_spread_bp,
        "cumulative_response_bp": post_spread_bp - pre_spread_bp,
    }


def event_in_omt_window(event_date: pd.Timestamp, horizon_days: int) -> bool:
    end_of_window = event_date + pd.Timedelta(days=horizon_days * 2)  # generous
    return (
        (event_date >= OMT_WINDOW_START and event_date <= OMT_WINDOW_END)
        or (end_of_window >= OMT_WINDOW_START and event_date <= OMT_WINDOW_END)
    )


def emit_inconclusive(verdict: str, manifest: dict,
                      missing: list[str]) -> None:
    diagnostics = {
        "verdict": verdict,
        "verdict_label": "inconclusive",
        "primary_outcome": "10y sovereign yield spread vs Bund (bp)",
        "missing_series": missing,
        "event_panel": [
            {"country": c, "event_date": d, "label": lbl}
            for c, d, lbl in EVENT_PANEL
        ],
        "thresholds_bp": {
            "supported_min": THRESHOLD_SUPPORTED_BP,
            "partial_floor": THRESHOLD_PARTIAL_FLOOR_BP,
        },
        "horizon_trading_days": EVENT_HORIZON_DAYS,
        "omt_exclusion_window": [
            OMT_WINDOW_START.date().isoformat(),
            OMT_WINDOW_END.date().isoformat(),
        ],
        "method_valid": {
            "all_country_yields_present": False,
            "bund_present": False,
            "data_gap_explanation": (
                "No eurozone-periphery 10y sovereign-yield series and no "
                "German Bund 10y series are on disk in the current vintage "
                "tree. ECB has only BSI (M3) and EXR (USD/EUR FX); FRED "
                "has only US DGS10. The replication is staged to compute "
                "the dispositive verdict the day a fetcher lands the IRS "
                "or IRLTLT01* series."
            ),
        },
        "manifest": manifest,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=str) + "\n"
    )

    # Empty coefficients table (still emit the artifact for schema parity).
    pd.DataFrame(
        [{"spec": "primary", "term": "data_gap", "estimate": np.nan}]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Eurozone-periphery sovereign spread vs Bund — data unavailable",
        "subtitle": (
            "Per-country 10y yields and the German Bund 10y are not on "
            "disk; verdict is inconclusive (data gap)."
        ),
        "type": "line",
        "x_axis": {"label": "Date", "type": "time"},
        "y_axis": {"label": "Spread vs Bund (bp)", "type": "linear"},
        "series": [],
        "annotations": [
            {"type": "note", "label": verdict},
            {
                "type": "note",
                "label": (
                    "Once fetched, the script computes the cumulative "
                    f"h={EVENT_HORIZON_DAYS}-trading-day spread response "
                    "across the EDP/budget-revision event panel and "
                    f"checks against the +{THRESHOLD_SUPPORTED_BP:.0f} bp "
                    "(SUPPORTED) / "
                    f"+{THRESHOLD_PARTIAL_FLOOR_BP:.0f} bp (partial) "
                    "thresholds."
                ),
            },
        ],
        "sources": [
            {
                "publisher_id": v["publisher"],
                "series_id": v["series"],
                "vintage_file": v.get("vintage_file"),
                "status": v.get("status"),
            }
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        "verdict_label: inconclusive_data_gap",
        "vintages:",
    ]
    for k, v in manifest.items():
        lines.append(f"  {k}:")
        lines.append(f"    publisher: {v['publisher']}")
        lines.append(f"    series: {v['series']}")
        lines.append(f"    status: {v.get('status', 'missing_on_disk')}")
        if v.get("vintage_file"):
            lines.append(f"    vintage_file: {v['vintage_file']}")
            lines.append(f"    sha256: {v['sha256']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n")

    card = [
        f"# Eurozone fiscal-rule departure -> sovereign-spread response",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "The pre-registered event-study test cannot be computed in the "
        "current data state. The PRIMARY outcome — cumulative h=20 "
        "trading-day spread (10y country yield minus 10y Bund) response "
        "across a panel of EDP-escalation / SGP-breach / budget-revision "
        "events for {GRC, IRL, PRT, ESP, ITA} in 2009-2011 — requires "
        "per-country sovereign-yield series and a German Bund 10y series. "
        "Neither is on disk in the current vintage tree:",
        "",
        f"- Missing series ({len(missing)}):",
    ] + [f"  - `{m}`" for m in missing] + [
        "",
        "Per the framework's invariants on provenance and method-validity "
        "(HYPOTHESIS_FRAMEWORK_AUDIT.md §E2), data gaps on the primary "
        "outcome emit `inconclusive`, NOT a refutation. The verdict is "
        "neutral on the scoreboard pending a fetcher pass.",
        "",
        "## Method (will run when data lands)",
        "",
        "Event-study cumulative spread response across the pre-registered",
        "event panel:",
        "",
    ] + [
        f"- {c} {d} — {lbl}" for c, d, lbl in EVENT_PANEL
    ] + [
        "",
        "Spread response = (country_yield_t+20 − bund_t+20) − "
        "(country_yield_t-1 − bund_t-1) in basis points, where t is the "
        "first trading day on or after the event date and t+20 is 20 "
        "trading days later. The OMT activation window "
        f"({OMT_WINDOW_START.date().isoformat()} to "
        f"{OMT_WINDOW_END.date().isoformat()}) is excluded — any event "
        "whose horizon touches the window is dropped from the panel.",
        "",
        "## Thresholds",
        "",
        f"- SUPPORTED: mean panel response ≥ +{THRESHOLD_SUPPORTED_BP:.0f} bp.",
        f"- partial:   +{THRESHOLD_PARTIAL_FLOOR_BP:.0f} to +{THRESHOLD_SUPPORTED_BP:.0f} bp.",
        f"- refuted:   < +{THRESHOLD_PARTIAL_FLOOR_BP:.0f} bp or wrong sign.",
        "",
        "## Data backlog (for the data-agent)",
        "",
        "Add fetchers for:",
        "",
        "- ECB SDW key family `IRS` "
        "(long-term interest-rate convergence criteria, monthly, "
        "by member-state).",
        "- FRED `IRLTLT01{GRC,IRL,PRT,ESP,ITA,DEU}M156N` "
        "(OECD MEI long-term rates re-published monthly).",
        "- (Optional, for daily) Bundesbank BBK01 series for the Bund "
        "10y benchmark and the corresponding national-debt-management-"
        "office series for periphery 10y benchmarks.",
        "",
        "Once any of these lands, re-run this script — no spec change "
        "required.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"verdict: {verdict}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------- Locate vintages (yields) -----------------
    manifest: dict[str, dict] = {}

    def pin(role: str, pub: str, series: str, path: Path | None) -> bool:
        if path is None:
            manifest[role] = {
                "publisher": pub, "series": series,
                "vintage_file": None, "sha256": None,
                "status": "missing_on_disk",
            }
            return False
        manifest[role] = {
            "publisher": pub, "series": series,
            "vintage_file": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256(path),
            "status": "loaded",
        }
        return True

    yield_paths: dict[str, Path | None] = {}
    for iso, fred_code in FRED_LT_SERIES.items():
        p = latest_optional("fred", fred_code)
        # ECB IRS family fallback (key-family pattern):
        if p is None:
            ecb_glob = f"IRS__M.{iso}.L.L40.CI.0000.EUR.N.Z"
            p = latest_optional("ecb", ecb_glob)
        yield_paths[iso] = p
        pin(f"{iso}_10y_yield", "fred", fred_code, p)

    # Always pin VIX as a control if present (useful even when verdict is gap).
    vix_path = latest_optional("fred", "VIXCLS")
    pin("vix", "fred", "VIXCLS", vix_path)

    missing = [
        f"{m['publisher']}:{m['series']}"
        for k, m in manifest.items()
        if k.endswith("_10y_yield") and m.get("status") != "loaded"
    ]

    # ----------------- Method-valid gate -----------------
    if missing:
        verdict = (
            f"inconclusive (data gap on {len(missing)} sovereign-yield "
            f"series: {', '.join(missing[:3])}"
            + ("" if len(missing) <= 3 else f", +{len(missing)-3} more")
            + ") — primary event-study cannot run; per HYPOTHESIS_"
            "FRAMEWORK_AUDIT §E2 a method-validity failure emits "
            "inconclusive rather than refutation. Re-run once a "
            "fetcher lands the ECB IRS or FRED IRLTLT01* series."
        )
        emit_inconclusive(verdict, manifest, missing)
        return

    # ----------------- PRIMARY: event-study spread response -----------------
    bund = load_daily(yield_paths["DEU"])
    rows = []
    for iso, date_str, lbl in EVENT_PANEL:
        event_date = pd.Timestamp(date_str)
        if event_in_omt_window(event_date, EVENT_HORIZON_DAYS):
            rows.append({
                "country": iso, "event_date": date_str, "label": lbl,
                "excluded": True, "exclusion_reason": "omt_window_overlap",
                "cumulative_response_bp": np.nan,
            })
            continue
        country_yld = load_daily(yield_paths[iso])
        result = cumulative_response(country_yld, bund, event_date,
                                      EVENT_HORIZON_DAYS)
        if "error" in result:
            rows.append({
                "country": iso, "event_date": date_str, "label": lbl,
                "excluded": True, "exclusion_reason": result["error"],
                "cumulative_response_bp": np.nan,
            })
            continue
        rows.append({
            "country": iso, "event_date": date_str, "label": lbl,
            "excluded": False, "exclusion_reason": "",
            **result,
        })

    panel_df = pd.DataFrame(rows)
    valid = panel_df[~panel_df["excluded"]]
    if valid.empty:
        verdict = (
            "inconclusive — every event in the panel was excluded "
            "(OMT-window overlap or insufficient observations); cannot "
            "compute mean cumulative response."
        )
        emit_inconclusive(verdict, manifest, missing=[])
        return

    mean_response_bp = float(valid["cumulative_response_bp"].mean())
    median_response_bp = float(valid["cumulative_response_bp"].median())
    n_events = int(len(valid))

    # ----------------- Verdict on PRIMARY -----------------
    if mean_response_bp >= THRESHOLD_SUPPORTED_BP:
        verdict_label = "SUPPORTED"
        verdict = (
            f"SUPPORTED — Mean cumulative h={EVENT_HORIZON_DAYS}-trading-"
            f"day sovereign-spread response across {n_events} pre-"
            f"registered EDP/budget-revision events: "
            f"{mean_response_bp:+.1f} bp (median {median_response_bp:+.1f} "
            f"bp), clearing the +{THRESHOLD_SUPPORTED_BP:.0f} bp "
            f"ordoliberal credibility-loss threshold."
        )
    elif mean_response_bp >= THRESHOLD_PARTIAL_FLOOR_BP:
        verdict_label = "partial"
        verdict = (
            f"partial — Mean cumulative response "
            f"{mean_response_bp:+.1f} bp across {n_events} events; "
            f"directionally consistent with credibility-loss but below "
            f"the +{THRESHOLD_SUPPORTED_BP:.0f} bp dispositive threshold "
            f"(above the +{THRESHOLD_PARTIAL_FLOOR_BP:.0f} bp partial "
            f"floor)."
        )
    elif mean_response_bp >= 0:
        verdict_label = "refuted"
        verdict = (
            f"refuted (small move) — Mean cumulative response only "
            f"{mean_response_bp:+.1f} bp across {n_events} events, below "
            f"the +{THRESHOLD_PARTIAL_FLOOR_BP:.0f} bp partial floor. "
            f"The ordoliberal credibility-loss interpretation is not "
            f"supported at the scale the claim invokes."
        )
    else:
        verdict_label = "refuted"
        verdict = (
            f"refuted (wrong direction) — Mean cumulative response "
            f"{mean_response_bp:+.1f} bp; spreads narrowed rather than "
            f"widened over the event horizon."
        )

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "primary": {
            "outcome": "10y sovereign yield spread vs Bund (bp)",
            "horizon_trading_days": EVENT_HORIZON_DAYS,
            "n_events_used": n_events,
            "n_events_pre_registered": len(EVENT_PANEL),
            "mean_cumulative_response_bp": mean_response_bp,
            "median_cumulative_response_bp": median_response_bp,
            "threshold_supported_bp": THRESHOLD_SUPPORTED_BP,
            "threshold_partial_floor_bp": THRESHOLD_PARTIAL_FLOOR_BP,
        },
        "events": rows,
        "exclusions": {
            "omt_window": [
                OMT_WINDOW_START.date().isoformat(),
                OMT_WINDOW_END.date().isoformat(),
            ],
        },
        "manifest": manifest,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=str) + "\n"
    )

    coef_rows = [
        {"spec": "primary", "term": "mean_cumulative_response_bp",
         "estimate": mean_response_bp},
        {"spec": "primary", "term": "median_cumulative_response_bp",
         "estimate": median_response_bp},
        {"spec": "primary", "term": "threshold_supported_bp",
         "estimate": THRESHOLD_SUPPORTED_BP},
        {"spec": "primary", "term": "threshold_partial_floor_bp",
         "estimate": THRESHOLD_PARTIAL_FLOOR_BP},
    ]
    for r in rows:
        if not r.get("excluded") and "cumulative_response_bp" in r:
            coef_rows.append({
                "spec": "informative",
                "term": f"{r['country']}_{r['event_date']}_response_bp",
                "estimate": float(r["cumulative_response_bp"]),
            })
    pd.DataFrame(coef_rows).to_parquet(
        OUT_DIR / "coefficients.parquet", index=False
    )

    # Build a chart of country yield series across the crisis window.
    series_out = []
    palette = ["#E15759", "#F28E2B", "#4E79A7", "#59A14F", "#B07AA1", "#76B7B2"]
    chart_window_start = pd.Timestamp("2009-01-01")
    chart_window_end = pd.Timestamp("2012-09-01")
    for i, iso in enumerate(["GRC", "IRL", "PRT", "ESP", "ITA", "DEU"]):
        df = load_daily(yield_paths[iso])
        sub = df[(df["date"] >= chart_window_start)
                 & (df["date"] <= chart_window_end)]
        pts = [{"x": d.date().isoformat(), "y": float(v)}
               for d, v in zip(sub["date"], sub["value"])]
        series_out.append({
            "id": iso, "label": f"{iso} 10y yield (%)",
            "color": palette[i % len(palette)],
            "treated": iso != "DEU",
            "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Eurozone periphery 10y sovereign yields, 2009-2012",
        "subtitle": (
            f"Mean cumulative h={EVENT_HORIZON_DAYS}-trading-day spread "
            f"response across {n_events} pre-registered events: "
            f"{mean_response_bp:+.1f} bp. Threshold "
            f"+{THRESHOLD_SUPPORTED_BP:.0f} bp. Verdict: {verdict_label}."
        ),
        "type": "line",
        "x_axis": {"label": "Date", "type": "time"},
        "y_axis": {"label": "10y yield (%)", "type": "linear"},
        "series": series_out,
        "annotations": [
            {"type": "vline", "x": d, "label": f"{c}: {lbl}"}
            for c, d, lbl in EVENT_PANEL
        ] + [
            {"type": "note",
             "label": (f"OMT window {OMT_WINDOW_START.date().isoformat()} "
                       f"to {OMT_WINDOW_END.date().isoformat()} excluded.")}
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values() if v.get("vintage_file")
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # Manifest YAML.
    lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        f"verdict_label: {verdict_label}",
        "vintages:",
    ]
    for k, v in manifest.items():
        lines.append(f"  {k}:")
        lines.append(f"    publisher: {v['publisher']}")
        lines.append(f"    series: {v['series']}")
        lines.append(f"    status: {v.get('status', 'loaded')}")
        if v.get("vintage_file"):
            lines.append(f"    vintage_file: {v['vintage_file']}")
            lines.append(f"    sha256: {v['sha256']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n")

    # Result card.
    card = [
        f"# Eurozone fiscal-rule departure -> sovereign-spread response",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Pre-registered event panel: {len(EVENT_PANEL)} events; "
        f"{n_events} retained after OMT-window / data-coverage exclusions.",
        f"- Mean cumulative h={EVENT_HORIZON_DAYS}-trading-day spread "
        f"response: **{mean_response_bp:+.1f} bp** "
        f"(median {median_response_bp:+.1f} bp).",
        f"- Thresholds: SUPPORTED ≥ +{THRESHOLD_SUPPORTED_BP:.0f} bp; "
        f"partial floor +{THRESHOLD_PARTIAL_FLOOR_BP:.0f} bp.",
        "",
        "## Per-event responses",
        "",
    ]
    for r in rows:
        if r.get("excluded"):
            card.append(f"- {r['country']} {r['event_date']} ({r['label']}): "
                        f"EXCLUDED — {r['exclusion_reason']}.")
        else:
            card.append(f"- {r['country']} {r['event_date']} ({r['label']}): "
                        f"spread {r['pre_spread_bp']:+.0f} → "
                        f"{r['post_spread_bp']:+.0f} bp "
                        f"(Δ {r['cumulative_response_bp']:+.1f} bp).")
    card += [
        "",
        "## Method",
        "",
        f"Spread response = (country_yield_t+{EVENT_HORIZON_DAYS} − "
        f"bund_t+{EVENT_HORIZON_DAYS}) − (country_yield_t-1 − "
        f"bund_t-1) in basis points, where t is the first trading day "
        f"on or after the event date. OMT activation window "
        f"{OMT_WINDOW_START.date().isoformat()} to "
        f"{OMT_WINDOW_END.date().isoformat()} excluded.",
        "",
        "## Data",
        "",
    ]
    for k, v in manifest.items():
        card.append(f"- {v['publisher']}:{v['series']} ({v.get('status')})")
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
