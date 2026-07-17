#!/usr/bin/env python3
"""Replication — US 1945-1973 labour compact: productivity-compensation tracking.

Spec: hypotheses/growth/us_1945_1973_labour_compact_productivity_wage_link.yaml v1
Position-claim: social_democratic #2 (school predicts: supported)

Tests the social-democratic claim that the US postwar 'labour compact'
held real compensation per hour in tight tracking with labour
productivity over 1945-1973. Effective evaluation window is
1947Q1-1973Q4 because both FRED series (OPHNFB, COMPRNFB) start at
1947Q1.

  PRIMARY 1 (cumulative wedge): the absolute cumulative log wedge
             between productivity and real compensation per hour from
             window-start to window-end is below 10pp.
  PRIMARY 2 (correlation):       the within-window Pearson correlation
             between the two log-index series exceeds 0.85.

SUPPORTED iff BOTH primaries hold.
REFUTED   iff abs(wedge) > 25pp OR correlation < 0.5.
PARTIAL   in between.
INCONCLUSIVE if either FRED series is unavailable (data gap), per the
             framework's METHOD_VALID gate.
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
HID = "us_1945_1973_labour_compact_productivity_wage_link"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Effective window — spec says 1945-1973, but OPHNFB and COMPRNFB are
# 1947Q1+ so we evaluate 1947Q1 through 1973Q4.
WINDOW_START = pd.Timestamp("1947-01-01")
WINDOW_END = pd.Timestamp("1973-12-31")

# Falsification thresholds (spec.falsification.threshold)
WEDGE_SUPPORTED_BOUND = 0.10   # |cumulative log wedge| < 10pp
WEDGE_REFUTED_BOUND = 0.25     # |cumulative log wedge| > 25pp
CORR_SUPPORTED_BOUND = 0.85    # corr > 0.85
CORR_REFUTED_BOUND = 0.50      # corr < 0.50
MIN_QUARTERLY_OBS = 100        # METHOD_VALID gate


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_fred_quarterly(path: Path) -> pd.DataFrame:
    """FRED parquet. Native schema is (date, value, realtime_start,
    realtime_end). Returns columns (date, value) with date as Timestamp."""
    t = pq.read_table(path).to_pandas()
    cols = set(t.columns)
    if "date" in cols and "value" in cols:
        df = t[["date", "value"]].copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().sort_values("date").reset_index(drop=True)
    if "year" in cols and "value" in cols:
        # Fallback if some normaliser produced annual rows.
        df = t[["year", "value"]].copy()
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().sort_values("year").reset_index(drop=True)
        df["date"] = pd.to_datetime(df["year"].astype(int).astype(str) + "-01-01")
        return df[["date", "value"]]
    raise ValueError(f"{path}: unsupported FRED schema ({list(t.columns)})")


def emit_inconclusive(missing: list[str], manifest: dict) -> None:
    """Write all six artifacts with an inconclusive verdict for a data gap.
    The script must still run end-to-end and produce real artifacts so
    downstream tooling sees a real run, per research documentation
    'What to do when your spec needs data that isn't on disk'."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gap_str = ", ".join(missing)
    verdict = (
        f"inconclusive — data gap on {gap_str}. The replication is "
        f"ready to run as-soon-as the FRED fetcher publishes the "
        f"missing series; no other change is needed. Falsification "
        f"thresholds and method are pinned in the spec."
    )

    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "method_valid": False,
        "missing_series": missing,
        "primary1_wedge_supported": None,
        "primary2_correlation_supported": None,
        "cumulative_log_wedge": None,
        "pearson_correlation_log_levels": None,
        "n_quarterly_observations": 0,
        "wedge_supported_bound": WEDGE_SUPPORTED_BOUND,
        "wedge_refuted_bound": WEDGE_REFUTED_BOUND,
        "corr_supported_bound": CORR_SUPPORTED_BOUND,
        "corr_refuted_bound": CORR_REFUTED_BOUND,
        "window_start": str(WINDOW_START.date()),
        "window_end": str(WINDOW_END.date()),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US labour productivity vs real compensation per hour, 1947Q1-1973Q4",
        "subtitle": (
            f"DATA GAP: missing {gap_str}. Chart will populate once "
            f"the FRED fetcher publishes the series."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Index (1947Q1 = 1.0)", "type": "linear"},
        "series": [],
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Replication blocked on data availability. Missing: "
                    f"{gap_str}."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [
            {"spec": "primary1", "term": "cumulative_log_wedge", "estimate": float("nan")},
            {"spec": "primary2", "term": "pearson_correlation_log_levels", "estimate": float("nan")},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        f"status: inconclusive_data_gap\n"
        f"missing_series:\n"
        + "".join(f"  - {m}\n" for m in missing)
        + "vintages:\n"
        + (
            "".join(
                f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
                f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
                for k, v in manifest.items()
            )
            if manifest
            else "  {}\n"
        )
    )

    card = [
        f"# US 1945-1973 labour compact: productivity-compensation tracking",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Replication blocked on missing FRED series: **{gap_str}**.",
        f"- Falsification thresholds remain pinned in the spec "
        f"(SUPPORTED if |cumulative log wedge| < {WEDGE_SUPPORTED_BOUND*100:.0f}pp "
        f"AND Pearson correlation > {CORR_SUPPORTED_BOUND}; REFUTED if "
        f"wedge > {WEDGE_REFUTED_BOUND*100:.0f}pp OR correlation < "
        f"{CORR_REFUTED_BOUND}).",
        f"- Effective window: 1947Q1-1973Q4 (FRED series start 1947Q1).",
        "",
        "## Method",
        "",
        "Per the spec the test is descriptive: index OPHNFB and COMPRNFB",
        "to 1947Q1 = 1.0, take logs, and compute (1) the cumulative log",
        "wedge at 1973Q4 and (2) the within-window Pearson correlation",
        "of the two log-index series. SUPPORTED iff |wedge|<10pp AND",
        "corr>0.85. The script runs as written once the FRED fetcher",
        "lands the missing series — no code change required.",
        "",
        "## Data",
        "",
        f"- fred:OPHNFB (output per hour, nonfarm business, quarterly) — MISSING from `data/vintages/fred/`.",
        f"- fred:COMPRNFB (real compensation per hour, nonfarm business, quarterly) — MISSING from `data/vintages/fred/`.",
        "",
        "Add these series to the FRED fetcher worklist and rerun.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"verdict: {verdict}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ophnfb_path = latest("fred", "OPHNFB")
    comprnfb_path = latest("fred", "COMPRNFB")

    manifest: dict = {}
    missing: list[str] = []
    if ophnfb_path is None:
        missing.append("fred:OPHNFB")
    else:
        manifest["labour_productivity"] = {
            "publisher": "fred",
            "series": "OPHNFB",
            "vintage_file": str(ophnfb_path.relative_to(REPO_ROOT)),
            "sha256": sha256(ophnfb_path),
        }
    if comprnfb_path is None:
        missing.append("fred:COMPRNFB")
    else:
        manifest["real_compensation_per_hour"] = {
            "publisher": "fred",
            "series": "COMPRNFB",
            "vintage_file": str(comprnfb_path.relative_to(REPO_ROOT)),
            "sha256": sha256(comprnfb_path),
        }

    if missing:
        emit_inconclusive(missing, manifest)
        return

    # ---------- Load + window ----------
    prod = load_fred_quarterly(ophnfb_path)
    comp = load_fred_quarterly(comprnfb_path)

    prod = prod[(prod["date"] >= WINDOW_START) & (prod["date"] <= WINDOW_END)].reset_index(drop=True)
    comp = comp[(comp["date"] >= WINDOW_START) & (comp["date"] <= WINDOW_END)].reset_index(drop=True)

    merged = pd.merge(
        prod.rename(columns={"value": "productivity"}),
        comp.rename(columns={"value": "compensation"}),
        on="date",
        how="inner",
    ).sort_values("date").reset_index(drop=True)

    n_obs = len(merged)
    method_valid = n_obs >= MIN_QUARTERLY_OBS

    if not method_valid:
        # Treat as inconclusive (method gate failure, not refutation).
        verdict = (
            f"inconclusive — only {n_obs} overlapping quarterly "
            f"observations between OPHNFB and COMPRNFB in the "
            f"1947Q1-1973Q4 window (need >={MIN_QUARTERLY_OBS}). "
            f"Method-validity gate failed; not a refutation."
        )
        diagnostics = {
            "verdict": verdict,
            "all_pass": False,
            "method_valid": False,
            "n_quarterly_observations": int(n_obs),
            "wedge_supported_bound": WEDGE_SUPPORTED_BOUND,
            "wedge_refuted_bound": WEDGE_REFUTED_BOUND,
            "corr_supported_bound": CORR_SUPPORTED_BOUND,
            "corr_refuted_bound": CORR_REFUTED_BOUND,
            "window_start": str(WINDOW_START.date()),
            "window_end": str(WINDOW_END.date()),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        # Minimal chart + artifacts then exit.
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "US labour productivity vs real compensation per hour",
            "subtitle": verdict, "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index (1947Q1 = 1.0)", "type": "linear"},
            "series": [], "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        pd.DataFrame([
            {"spec": "primary1", "term": "cumulative_log_wedge", "estimate": float("nan")},
            {"spec": "primary2", "term": "pearson_correlation_log_levels", "estimate": float("nan")},
        ]).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nrun_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
            f"status: inconclusive_method_gate\nvintages:\n"
            + "".join(
                f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
                f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
                for k, v in manifest.items()
            )
        )
        (OUT_DIR / "result_card.md").write_text(
            f"# US 1945-1973 labour compact\n\n**Verdict:** {verdict}\n"
        )
        print(f"verdict: {verdict}")
        return

    # ---------- Index to window-start ----------
    base_prod = float(merged["productivity"].iloc[0])
    base_comp = float(merged["compensation"].iloc[0])
    merged["prod_index"] = merged["productivity"] / base_prod
    merged["comp_index"] = merged["compensation"] / base_comp
    merged["log_prod"] = np.log(merged["prod_index"])
    merged["log_comp"] = np.log(merged["comp_index"])

    # ---------- PRIMARY 1: cumulative log wedge at window-end ----------
    log_wedge = float(merged["log_prod"].iloc[-1] - merged["log_comp"].iloc[-1])
    abs_wedge = abs(log_wedge)
    primary1_supported = abs_wedge < WEDGE_SUPPORTED_BOUND
    primary1_refuted = abs_wedge > WEDGE_REFUTED_BOUND

    # ---------- PRIMARY 2: Pearson correlation of log-index series ----------
    corr = float(np.corrcoef(merged["log_prod"], merged["log_comp"])[0, 1])
    primary2_supported = corr > CORR_SUPPORTED_BOUND
    primary2_refuted = corr < CORR_REFUTED_BOUND

    # ---------- Verdict ----------
    if primary1_supported and primary2_supported:
        verdict = (
            f"SUPPORTED — Cumulative log wedge from 1947Q1 to 1973Q4 is "
            f"{log_wedge*100:+.2f}pp (|{abs_wedge*100:.2f}|pp < "
            f"{WEDGE_SUPPORTED_BOUND*100:.0f}pp threshold). Pearson "
            f"correlation of log-index series is {corr:.3f} (> "
            f"{CORR_SUPPORTED_BOUND} threshold). Productivity and real "
            f"compensation tracked tightly across the postwar labour-"
            f"compact era as the social-democratic claim predicts."
        )
    elif primary1_refuted or primary2_refuted:
        why = []
        if primary1_refuted:
            why.append(f"|wedge| {abs_wedge*100:.1f}pp > {WEDGE_REFUTED_BOUND*100:.0f}pp")
        if primary2_refuted:
            why.append(f"corr {corr:.3f} < {CORR_REFUTED_BOUND}")
        verdict = (
            f"refuted — Cumulative log wedge {log_wedge*100:+.2f}pp, "
            f"correlation {corr:.3f}. Refutation triggers: "
            f"{'; '.join(why)}. Productivity-compensation tracking "
            f"failed across the 1947-1973 window."
        )
    else:
        verdict = (
            f"partial — Cumulative log wedge {log_wedge*100:+.2f}pp "
            f"(in 10-25pp band) and/or correlation {corr:.3f} (in "
            f"0.5-0.85 band). Tracking is real but weaker than the "
            f"strong-form social-democratic claim requires."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": primary1_supported and primary2_supported,
        "method_valid": True,
        "primary1_wedge_supported": primary1_supported,
        "primary2_correlation_supported": primary2_supported,
        "cumulative_log_wedge": log_wedge,
        "abs_cumulative_log_wedge": abs_wedge,
        "pearson_correlation_log_levels": corr,
        "n_quarterly_observations": int(n_obs),
        "wedge_supported_bound": WEDGE_SUPPORTED_BOUND,
        "wedge_refuted_bound": WEDGE_REFUTED_BOUND,
        "corr_supported_bound": CORR_SUPPORTED_BOUND,
        "corr_refuted_bound": CORR_REFUTED_BOUND,
        "window_start": str(WINDOW_START.date()),
        "window_end": str(WINDOW_END.date()),
        "productivity_index_start": float(merged["prod_index"].iloc[0]),
        "productivity_index_end": float(merged["prod_index"].iloc[-1]),
        "compensation_index_start": float(merged["comp_index"].iloc[0]),
        "compensation_index_end": float(merged["comp_index"].iloc[-1]),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    series = [
        {
            "id": "PROD",
            "label": "Labour productivity (FRED OPHNFB, 1947Q1=1.0)",
            "color": "#4E79A7",
            "treated": True,
            "points": [
                {"x": r.date.year + (r.date.month - 1) / 12.0, "y": float(r.prod_index)}
                for r in merged.itertuples()
            ],
        },
        {
            "id": "COMP",
            "label": "Real compensation per hour (FRED COMPRNFB, 1947Q1=1.0)",
            "color": "#E15759",
            "treated": False,
            "points": [
                {"x": r.date.year + (r.date.month - 1) / 12.0, "y": float(r.comp_index)}
                for r in merged.itertuples()
            ],
        },
    ]
    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US labour productivity vs real compensation per hour, 1947Q1-1973Q4",
        "subtitle": (
            f"Cumulative log wedge at 1973Q4: {log_wedge*100:+.2f}pp · "
            f"Pearson correlation of log-index series: {corr:.3f} · "
            f"n={n_obs} quarterly obs."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Index (1947Q1 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"SUPPORTED if |wedge|<{WEDGE_SUPPORTED_BOUND*100:.0f}pp "
                    f"AND corr>{CORR_SUPPORTED_BOUND}; REFUTED if "
                    f"|wedge|>{WEDGE_REFUTED_BOUND*100:.0f}pp OR corr<"
                    f"{CORR_REFUTED_BOUND}. Window starts 1947Q1 because "
                    f"both FRED series begin then."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [
            {"spec": "primary1", "term": "cumulative_log_wedge", "estimate": log_wedge},
            {"spec": "primary1", "term": "abs_cumulative_log_wedge", "estimate": abs_wedge},
            {"spec": "primary2", "term": "pearson_correlation_log_levels", "estimate": corr},
            {"spec": "diagnostic", "term": "n_quarterly_observations", "estimate": float(n_obs)},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + "".join(
            f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
            f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
            for k, v in manifest.items()
        )
    )

    card = [
        f"# US 1945-1973 labour compact: productivity-compensation tracking",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Effective window 1947Q1-1973Q4 ({n_obs} overlapping quarterly obs).",
        f"- Productivity index 1973Q4: **{merged['prod_index'].iloc[-1]:.3f}** "
        f"(× the 1947Q1 baseline).",
        f"- Real compensation index 1973Q4: **{merged['comp_index'].iloc[-1]:.3f}**.",
        f"- Cumulative log wedge: **{log_wedge*100:+.2f}pp** "
        f"(SUPPORTED if |·|<{WEDGE_SUPPORTED_BOUND*100:.0f}pp; "
        f"REFUTED if >{WEDGE_REFUTED_BOUND*100:.0f}pp).",
        f"- Pearson correlation of log-index series: **{corr:.3f}** "
        f"(SUPPORTED if >{CORR_SUPPORTED_BOUND}; REFUTED if <"
        f"{CORR_REFUTED_BOUND}).",
        "",
        "## Method",
        "",
        "Index OPHNFB (output per hour, nonfarm business) and COMPRNFB",
        "(real compensation per hour, nonfarm business) to 1947Q1 = 1.0,",
        "take logs, and compute (1) the cumulative log wedge between the",
        "two log-index series at 1973Q4 and (2) the within-window",
        "Pearson correlation. Quarterly frequency preserved. Spec window",
        "is 1945-1973 but the canonical FRED series start at 1947Q1 — see",
        "`methodology_note` in the spec.",
        "",
        "## Data",
        "",
        f"- fred:OPHNFB (output per hour, nonfarm business, quarterly).",
        f"- fred:COMPRNFB (real compensation per hour, nonfarm business, quarterly).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
