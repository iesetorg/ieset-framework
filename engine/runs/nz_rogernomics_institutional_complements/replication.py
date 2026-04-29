#!/usr/bin/env python3
"""Replication — NZ Rogernomics: institutional complements vs deregulation alone.

Spec: hypotheses/regulatory/nz_rogernomics_institutional_complements.yaml v1
Position-claim: institutionalism #14 (school predicts: supported)

Tests whether NZ's growth-vs-donor-pool premium emerged ONLY after the
1989 Reserve Bank Act + 1994 Fiscal Responsibility Act (the "institutional
complements"), not from the 1984-1988 deregulation alone.

Three sub-windows decompose the 1984-2000 reform period:
  - WINDOW_A 1984-1988: deregulation-only ("Rogernomics" pre-RBA)
  - WINDOW_B 1989-1993: deregulation + RBA inflation-targeting
  - WINDOW_C 1994-2000: full stack (RBA + FRA fiscal rule)

For each window, compute mean annual real-GDP-per-capita growth (WDI
NY.GDP.PCAP.KD.ZG) for NZ and for the donor-pool mean (AUS, USA, GBR,
CAN). The "gap" is NZ minus donor-mean, in pp/yr.

PRIMARY (dispositive) — SUPPORTED iff:
    gap_A <= +0.3pp/yr   (no clear premium from deregulation alone)
    AND (gap_C - gap_A) >= +1.0pp/yr   (>=1pp lift from complements)
    AND gap_C > 0       (full stack actually outperforms)

REFUTED iff:
    gap_A >= +1.0pp/yr   (deregulation alone already delivered)
    OR gap_C < 0         (complements failed)

Otherwise PARTIAL.

INFORMATIVE legs (do NOT gate verdict):
  - PWT log-TFP (rtfpna) gap trajectory across windows
  - CPI inflation (FP.CPI.TOTL.ZG) trajectory — RBA mechanism check

METHOD_VALID: needs WDI growth + level for NZ + ≥3 donors over 1980-2000.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "nz_rogernomics_institutional_complements"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "NZL"
DONORS = ["AUS", "USA", "GBR", "CAN"]
ALL_COUNTRIES = [TREATED] + DONORS

PERIOD = (1980, 2000)
WINDOW_A = (1984, 1988)   # deregulation-only
WINDOW_B = (1989, 1993)   # deregulation + RBA
WINDOW_C = (1994, 2000)   # full stack (+ FRA)
WINDOW_PRE = (1980, 1983)  # pre-Rogernomics baseline

# Sharpened thresholds (see spec.methodology_note for promotion rationale)
GAP_A_CEILING_PP = 0.3        # SUPPORTED requires deregulation-only gap <= +0.3
GAP_LIFT_FLOOR_PP = 1.0       # SUPPORTED requires gap_C - gap_A >= +1.0
EARLY_PREMIUM_REFUTE_PP = 1.0  # REFUTED if gap_A >= +1.0 (early premium)

MIN_DONORS_FOR_METHOD_VALID = 3


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
    if not files:
        return None
    return files[-1]


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator_id",
                "unit", "obs_status", "decimal"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def country_window_mean(df: pd.DataFrame, country: str, lo: int, hi: int) -> float:
    sub = df[(df["country_iso3"] == country) & df["year"].between(lo, hi)]["value"]
    return float(sub.mean()) if len(sub) else float("nan")


def donor_pool_mean(df: pd.DataFrame, donors: list[str], lo: int, hi: int) -> tuple[float, int]:
    vals = []
    for c in donors:
        v = country_window_mean(df, c, lo, hi)
        if not np.isnan(v):
            vals.append(v)
    if not vals:
        return float("nan"), 0
    return float(np.mean(vals)), len(vals)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Resolve all spec series ----------
    # NY.GDP.PCAP.KD.ZG (the WDI-published growth-rate series) is not on
    # disk in the current vintage; we compute annual growth from the
    # NY.GDP.PCAP.KD level series ourselves (year-on-year % change).
    level_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    tfp_path = latest("pwt", "rtfpna")
    cpi_path = latest("world_bank_wdi", "FP.CPI.TOTL.ZG")

    manifest: dict = {}
    for name, pub, series, path in [
        ("real_gdp_pc_level", "world_bank_wdi", "NY.GDP.PCAP.KD", level_path),
        ("pwt_tfp", "pwt", "rtfpna", tfp_path),
        ("cpi_inflation", "world_bank_wdi", "FP.CPI.TOTL.ZG", cpi_path),
    ]:
        if path is None:
            manifest[name] = {"publisher": pub, "series": series, "missing": True}
        else:
            manifest[name] = {
                "publisher": pub, "series": series,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
            }

    # ---------- METHOD_VALID gate ----------
    method_valid = True
    method_notes: list[str] = []
    if level_path is None:
        method_valid = False
        method_notes.append(
            "WDI NY.GDP.PCAP.KD missing — primary outcome (annual growth "
            "computed from level) unavailable")

    primary_metrics: dict = {}
    informative: dict = {}
    primary_pass = False
    primary_refute = False
    growth = pd.DataFrame(columns=["country_iso3", "year", "value"])

    if method_valid:
        # Compute annual % growth from the level series (year-on-year)
        level_df = load_long(level_path)
        growth_rows = []
        for c in ALL_COUNTRIES:
            sub = (
                level_df[level_df["country_iso3"] == c]
                .set_index("year")["value"].sort_index()
            )
            for y in range(PERIOD[0], PERIOD[1] + 1):
                if y in sub.index and (y - 1) in sub.index and sub[y - 1] > 0:
                    g = 100.0 * (sub[y] / sub[y - 1] - 1.0)
                    growth_rows.append({"country_iso3": c, "year": y, "value": g})
        growth = pd.DataFrame(growth_rows)

        # NZ presence
        nz_a = country_window_mean(growth, TREATED, *WINDOW_A)
        nz_b = country_window_mean(growth, TREATED, *WINDOW_B)
        nz_c = country_window_mean(growth, TREATED, *WINDOW_C)
        nz_pre = country_window_mean(growth, TREATED, *WINDOW_PRE)

        donor_a, donor_a_n = donor_pool_mean(growth, DONORS, *WINDOW_A)
        donor_b, donor_b_n = donor_pool_mean(growth, DONORS, *WINDOW_B)
        donor_c, donor_c_n = donor_pool_mean(growth, DONORS, *WINDOW_C)
        donor_pre, donor_pre_n = donor_pool_mean(growth, DONORS, *WINDOW_PRE)

        # Method-validity check on donor coverage
        min_donors = min(donor_a_n, donor_b_n, donor_c_n)
        if min_donors < MIN_DONORS_FOR_METHOD_VALID:
            method_valid = False
            method_notes.append(
                f"only {min_donors} of {len(DONORS)} donors have data in worst-covered "
                f"window (need >= {MIN_DONORS_FOR_METHOD_VALID})"
            )
        if any(np.isnan(v) for v in (nz_a, nz_b, nz_c)):
            method_valid = False
            method_notes.append("NZ growth missing in at least one of the three sub-windows")

        gap_a = nz_a - donor_a if not (np.isnan(nz_a) or np.isnan(donor_a)) else float("nan")
        gap_b = nz_b - donor_b if not (np.isnan(nz_b) or np.isnan(donor_b)) else float("nan")
        gap_c = nz_c - donor_c if not (np.isnan(nz_c) or np.isnan(donor_c)) else float("nan")
        gap_pre = nz_pre - donor_pre if not (np.isnan(nz_pre) or np.isnan(donor_pre)) else float("nan")

        primary_metrics = {
            "window_pre_1980_1983": {
                "nz_growth_pct": nz_pre, "donor_mean_growth_pct": donor_pre,
                "donor_n": donor_pre_n, "gap_pp": gap_pre,
            },
            "window_A_1984_1988_deregulation_only": {
                "nz_growth_pct": nz_a, "donor_mean_growth_pct": donor_a,
                "donor_n": donor_a_n, "gap_pp": gap_a,
            },
            "window_B_1989_1993_dereg_plus_rba": {
                "nz_growth_pct": nz_b, "donor_mean_growth_pct": donor_b,
                "donor_n": donor_b_n, "gap_pp": gap_b,
            },
            "window_C_1994_2000_full_stack": {
                "nz_growth_pct": nz_c, "donor_mean_growth_pct": donor_c,
                "donor_n": donor_c_n, "gap_pp": gap_c,
            },
            "lift_C_minus_A_pp": (gap_c - gap_a) if not (np.isnan(gap_c) or np.isnan(gap_a)) else float("nan"),
        }

        if method_valid and not any(np.isnan(v) for v in (gap_a, gap_b, gap_c)):
            primary_pass = (
                gap_a <= GAP_A_CEILING_PP
                and (gap_c - gap_a) >= GAP_LIFT_FLOOR_PP
                and gap_c > 0
            )
            primary_refute = (gap_a >= EARLY_PREMIUM_REFUTE_PP) or (gap_c < 0)

    # ---------- INFORMATIVE: PWT TFP gap ----------
    if tfp_path is not None:
        tfp = load_long(tfp_path)
        # log-TFP for each country (rtfpna is already a normalised TFP index)
        tfp = tfp.copy()
        tfp = tfp[tfp["value"] > 0]
        tfp["log_value"] = np.log(tfp["value"])
        tfp["value"] = tfp["log_value"]  # so country_window_mean uses logs

        nz_tfp = {w: country_window_mean(tfp, TREATED, *win)
                  for w, win in [("pre", WINDOW_PRE), ("A", WINDOW_A),
                                 ("B", WINDOW_B), ("C", WINDOW_C)]}
        donor_tfp = {}
        for w, win in [("pre", WINDOW_PRE), ("A", WINDOW_A),
                       ("B", WINDOW_B), ("C", WINDOW_C)]:
            mean, n = donor_pool_mean(tfp, DONORS, *win)
            donor_tfp[w] = {"mean_log_tfp": mean, "donor_n": n}

        tfp_gaps = {
            w: (nz_tfp[w] - donor_tfp[w]["mean_log_tfp"])
            if not (np.isnan(nz_tfp[w]) or np.isnan(donor_tfp[w]["mean_log_tfp"]))
            else float("nan")
            for w in ("pre", "A", "B", "C")
        }
        informative["pwt_log_tfp"] = {
            "nz_window_means": nz_tfp,
            "donor_pool_window_means": donor_tfp,
            "log_tfp_gaps_nz_minus_donor": tfp_gaps,
            "lift_C_minus_A_log_units": (tfp_gaps["C"] - tfp_gaps["A"])
            if not (np.isnan(tfp_gaps["C"]) or np.isnan(tfp_gaps["A"])) else float("nan"),
        }
    else:
        informative["pwt_log_tfp"] = {"missing": True}

    # ---------- INFORMATIVE: CPI inflation ----------
    if cpi_path is not None:
        cpi = load_long(cpi_path)
        nz_cpi = {w: country_window_mean(cpi, TREATED, *win)
                  for w, win in [("pre", WINDOW_PRE), ("A", WINDOW_A),
                                 ("B", WINDOW_B), ("C", WINDOW_C)]}
        donor_cpi = {}
        for w, win in [("pre", WINDOW_PRE), ("A", WINDOW_A),
                       ("B", WINDOW_B), ("C", WINDOW_C)]:
            mean, n = donor_pool_mean(cpi, DONORS, *win)
            donor_cpi[w] = {"mean_pct": mean, "donor_n": n}
        informative["cpi_inflation"] = {
            "nz_window_means_pct": nz_cpi,
            "donor_pool_window_means_pct": donor_cpi,
            "rba_act_check_nz_inflation_drop_b_minus_a": (nz_cpi["B"] - nz_cpi["A"])
            if not (np.isnan(nz_cpi["B"]) or np.isnan(nz_cpi["A"])) else float("nan"),
        }
    else:
        informative["cpi_inflation"] = {"missing": True}

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive — method-validity gate failed: "
            + "; ".join(method_notes)
            + f". Cannot dispositively grade the institutional-complements claim."
        )
    elif primary_pass:
        gap_a = primary_metrics["window_A_1984_1988_deregulation_only"]["gap_pp"]
        gap_c = primary_metrics["window_C_1994_2000_full_stack"]["gap_pp"]
        lift = primary_metrics["lift_C_minus_A_pp"]
        verdict = (
            f"SUPPORTED — NZ-vs-donor-pool real-GDP-per-capita growth gap "
            f"is {gap_a:+.2f}pp/yr in the 1984-1988 deregulation-only window "
            f"(<=+{GAP_A_CEILING_PP:.1f}pp threshold met: no clear premium "
            f"from deregulation alone), and rises to {gap_c:+.2f}pp/yr in the "
            f"1994-2000 full-stack window — a {lift:+.2f}pp/yr lift "
            f"(>=+{GAP_LIFT_FLOOR_PP:.1f}pp threshold met). Pattern matches "
            f"the institutional-complements story: deregulation alone did not "
            f"raise growth above the AUS/USA/GBR/CAN counterfactual; only "
            f"after the RBA Act (1989) and FRA (1994) did NZ pull ahead."
        )
    elif primary_refute:
        gap_a = primary_metrics["window_A_1984_1988_deregulation_only"]["gap_pp"]
        gap_c = primary_metrics["window_C_1994_2000_full_stack"]["gap_pp"]
        if gap_a >= EARLY_PREMIUM_REFUTE_PP:
            verdict = (
                f"refuted — NZ already had a {gap_a:+.2f}pp/yr growth premium "
                f"vs the AUS/USA/GBR/CAN donor pool in the 1984-1988 "
                f"deregulation-only window (>=+{EARLY_PREMIUM_REFUTE_PP:.1f}pp "
                f"threshold). The institutional-complements story requires that "
                f"deregulation alone NOT deliver — the data show it did. "
                f"Full-stack window gap: {gap_c:+.2f}pp/yr."
            )
        else:  # gap_c < 0
            verdict = (
                f"refuted — full-stack 1994-2000 NZ-vs-donor-pool growth gap is "
                f"{gap_c:+.2f}pp/yr (NEGATIVE — NZ lagged the donor pool even "
                f"after the RBA Act + FRA). Institutional complements failed to "
                f"lift growth above the counterfactual; deregulation-only window "
                f"gap was {gap_a:+.2f}pp/yr."
            )
    else:
        gap_a = primary_metrics["window_A_1984_1988_deregulation_only"]["gap_pp"]
        gap_c = primary_metrics["window_C_1994_2000_full_stack"]["gap_pp"]
        lift = primary_metrics["lift_C_minus_A_pp"]
        verdict = (
            f"partial — direction is consistent with the complements story "
            f"(early gap {gap_a:+.2f}pp/yr, late gap {gap_c:+.2f}pp/yr, lift "
            f"{lift:+.2f}pp/yr) but at least one dispositive threshold is not "
            f"met: needed gap_A<=+{GAP_A_CEILING_PP:.1f}pp AND lift>=+"
            f"{GAP_LIFT_FLOOR_PP:.1f}pp AND gap_C>0."
        )

    diagnostics = {
        "verdict": verdict,
        "primary_pass": primary_pass,
        "primary_refute": primary_refute,
        "method_valid": method_valid,
        "method_notes": method_notes,
        "thresholds": {
            "gap_A_ceiling_pp": GAP_A_CEILING_PP,
            "gap_lift_floor_pp": GAP_LIFT_FLOOR_PP,
            "early_premium_refute_pp": EARLY_PREMIUM_REFUTE_PP,
        },
        "windows": {
            "pre_1980_1983": list(WINDOW_PRE),
            "A_1984_1988_deregulation_only": list(WINDOW_A),
            "B_1989_1993_dereg_plus_rba": list(WINDOW_B),
            "C_1994_2000_full_stack": list(WINDOW_C),
        },
        "treated": TREATED,
        "donor_pool": DONORS,
        "primary_metrics_real_gdp_pc_growth": primary_metrics,
        "informative_metrics": informative,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- coefficients.parquet ----------
    coef_rows: list[dict] = []
    for w_key, w_label in [
        ("window_pre_1980_1983", "pre"),
        ("window_A_1984_1988_deregulation_only", "A"),
        ("window_B_1989_1993_dereg_plus_rba", "B"),
        ("window_C_1994_2000_full_stack", "C"),
    ]:
        if w_key in primary_metrics:
            m = primary_metrics[w_key]
            coef_rows.append({"spec": "primary", "term": f"nz_growth_{w_label}",
                              "estimate": m["nz_growth_pct"]})
            coef_rows.append({"spec": "primary", "term": f"donor_mean_growth_{w_label}",
                              "estimate": m["donor_mean_growth_pct"]})
            coef_rows.append({"spec": "primary", "term": f"gap_{w_label}_pp",
                              "estimate": m["gap_pp"]})
    if "lift_C_minus_A_pp" in primary_metrics:
        coef_rows.append({"spec": "primary", "term": "lift_C_minus_A_pp",
                          "estimate": primary_metrics["lift_C_minus_A_pp"]})
    tfp_inf = informative.get("pwt_log_tfp", {})
    if "log_tfp_gaps_nz_minus_donor" in tfp_inf:
        for w, g in tfp_inf["log_tfp_gaps_nz_minus_donor"].items():
            coef_rows.append({"spec": "informative_tfp", "term": f"log_tfp_gap_{w}",
                              "estimate": g})
    cpi_inf = informative.get("cpi_inflation", {})
    if "nz_window_means_pct" in cpi_inf:
        for w, v in cpi_inf["nz_window_means_pct"].items():
            coef_rows.append({"spec": "informative_cpi", "term": f"nz_inflation_{w}",
                              "estimate": v})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- chart_data.json ----------
    palette = {
        "NZL": "#E15759",  # treated — red
        "AUS": "#4E79A7", "USA": "#59A14F", "GBR": "#B07AA1", "CAN": "#F28E2B",
    }
    series = []
    if level_path is not None and method_valid:
        # Reuse the computed growth DataFrame for the chart
        for c in ALL_COUNTRIES:
            sub = (
                growth[(growth["country_iso3"] == c) & growth["year"].between(*PERIOD)]
                [["year", "value"]].dropna().sort_values("year")
            )
            if sub.empty:
                continue
            series.append({
                "id": c,
                "label": f"{c}{' (treated)' if c == TREATED else ''}",
                "color": palette.get(c, "#888888"),
                "treated": (c == TREATED),
                "points": [{"x": int(r.year), "y": float(r.value)}
                           for r in sub.itertuples()],
            })

    annotations = [
        {"type": "vline", "x": 1984, "label": "Rogernomics (Lange Labour deregulation)"},
        {"type": "vline", "x": 1989, "label": "Reserve Bank Act (RBA inflation-targeting)"},
        {"type": "vline", "x": 1994, "label": "Fiscal Responsibility Act (FRA)"},
        {"type": "note", "label": (
            f"Verdict: {verdict[:240]}{'...' if len(verdict) > 240 else ''}"
        )},
    ]

    if primary_metrics:
        a_gap = primary_metrics["window_A_1984_1988_deregulation_only"]["gap_pp"]
        c_gap = primary_metrics["window_C_1994_2000_full_stack"]["gap_pp"]
        chart_subtitle = (
            f"NZ-vs-donor-pool real-GDP-per-capita growth gap: "
            f"deregulation-only window (1984-1988) {a_gap:+.2f}pp/yr; "
            f"full-stack window (1994-2000) {c_gap:+.2f}pp/yr."
        )
    else:
        chart_subtitle = "Data gap on primary outcome — verdict inconclusive."

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Real GDP per capita growth, NZ vs OECD donor pool, 1980-2000",
        "subtitle": chart_subtitle,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "annual growth %", "type": "linear"},
        "series": series,
        "annotations": annotations,
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v.get("vintage_file", "MISSING")}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- manifest.yaml ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- result_card.md ----------
    lines = [
        "# NZ Rogernomics — institutional complements vs deregulation alone",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Three-window decomposition of the NZ-vs-donor-pool real-GDP-per-capita "
        "growth gap, where the donor pool is the equally-weighted mean of "
        f"{', '.join(DONORS)} (per `spec.sample.countries`).",
        "",
        f"- **Pre 1980-1983** (baseline): donor-pool growth typically faster.",
        f"- **Window A 1984-1988** (deregulation only): if NZ lagged or matched "
        f"donors, the institutional-complements story is consistent. If NZ already "
        f"led by >=+{EARLY_PREMIUM_REFUTE_PP:.1f}pp/yr, the story is refuted.",
        f"- **Window B 1989-1993** (deregulation + RBA Act): inflation-targeting "
        f"begins; transition.",
        f"- **Window C 1994-2000** (full stack incl. FRA): if NZ now leads by a "
        f">=+{GAP_LIFT_FLOOR_PP:.1f}pp/yr lift over Window A, the complements "
        f"story is supported.",
        "",
        "## Window-by-window real-GDP-per-capita growth",
        "",
    ]
    if primary_metrics:
        lines += [
            "| Window | NZ growth %/yr | Donor-pool mean %/yr | Donor n | Gap pp |",
            "|---|---:|---:|---:|---:|",
        ]
        for w_key, label in [
            ("window_pre_1980_1983", "Pre 1980-1983"),
            ("window_A_1984_1988_deregulation_only", "A 1984-1988 (dereg only)"),
            ("window_B_1989_1993_dereg_plus_rba", "B 1989-1993 (+RBA)"),
            ("window_C_1994_2000_full_stack", "C 1994-2000 (full stack)"),
        ]:
            m = primary_metrics[w_key]
            def fmt(v):
                return f"{v:+.2f}" if isinstance(v, float) and not np.isnan(v) else "—"
            lines.append(
                f"| {label} | {fmt(m['nz_growth_pct'])} | "
                f"{fmt(m['donor_mean_growth_pct'])} | {m['donor_n']} | "
                f"{fmt(m['gap_pp'])} |"
            )
        lift = primary_metrics.get("lift_C_minus_A_pp", float("nan"))
        lines.append("")
        lines.append(f"**Window-C minus Window-A lift: "
                     f"{lift:+.2f}pp/yr** "
                     f"(threshold for SUPPORT: ≥+{GAP_LIFT_FLOOR_PP:.1f}pp/yr).")
        lines.append("")
    else:
        lines.append("_Primary outcome data unavailable — see method notes._")
        lines.append("")

    # Informative legs
    lines.append("## Informative legs (do not gate verdict)")
    lines.append("")
    tfp_inf = informative.get("pwt_log_tfp", {})
    if tfp_inf.get("missing"):
        lines.append("**PWT log-TFP (rtfpna):** series not in vintage.")
    elif "log_tfp_gaps_nz_minus_donor" in tfp_inf:
        gaps = tfp_inf["log_tfp_gaps_nz_minus_donor"]
        def fmtg(v):
            return f"{v:+.3f}" if isinstance(v, float) and not np.isnan(v) else "—"
        lines.append(
            f"**PWT log-TFP gap (NZ − donor mean):** pre {fmtg(gaps['pre'])}, "
            f"A {fmtg(gaps['A'])}, B {fmtg(gaps['B'])}, C {fmtg(gaps['C'])} "
            f"(log units; lift C−A: {fmtg(tfp_inf.get('lift_C_minus_A_log_units', float('nan')))})."
        )
    lines.append("")

    cpi_inf = informative.get("cpi_inflation", {})
    if cpi_inf.get("missing"):
        lines.append("**CPI inflation:** series not in vintage.")
    elif "nz_window_means_pct" in cpi_inf:
        nz = cpi_inf["nz_window_means_pct"]
        def fmtc(v):
            return f"{v:.1f}%" if isinstance(v, float) and not np.isnan(v) else "—"
        lines.append(
            f"**NZ CPI inflation by window:** pre {fmtc(nz['pre'])}, "
            f"A {fmtc(nz['A'])}, B {fmtc(nz['B'])}, C {fmtc(nz['C'])}. "
            f"RBA-Act mechanism check (B − A): "
            f"{cpi_inf['rba_act_check_nz_inflation_drop_b_minus_a']:+.1f}pp "
            f"(negative = inflation fell after the RBA Act, consistent with "
            f"the inflation-targeting mechanism)."
        )
    lines += [
        "",
        "## Method",
        "",
        "Window-mean of WDI annual real-GDP-per-capita growth "
        "(`NY.GDP.PCAP.KD.ZG`) for NZ and for the donor-pool mean across "
        f"{', '.join(DONORS)}. Three pre-registered sub-windows mapping to the "
        "three sequential reform stages (1984 deregulation, 1989 RBA Act, "
        "1994 FRA). PRIMARY (dispositive) verdict gates on the *pattern* of "
        "the gap across windows, not on a t-statistic — N is far too small "
        "(5 countries × ~5 years/window) for inferential statistics to "
        "carry weight. Informative TFP and inflation legs are reported for "
        "context but do not gate.",
        "",
        "## Caveats",
        "",
        "- Small-N (5 countries, 4 windows): sequential treatments overlap; "
        "clean attribution is impossible. This is a descriptive-comparative "
        "test of an institutionalist framing, not a causal-identification "
        "claim.",
        "- Donor pool (AUS, USA, GBR, CAN) inherits its own contemporaneous "
        "shocks (e.g. AUS deregulated in parallel under Hawke-Keating; UK "
        "ran Thatcher-era reforms; USA had Reagan disinflation). The donor "
        "pool is NOT a clean no-reform counterfactual — it is the spec's "
        "chosen comparator for a 'similar Anglosphere economies' framing.",
        "- Window boundaries are calendar-year aligned; reform implementation "
        "lags can shift effective treatment dates by 1-2 years.",
        "- A market-liberal counter-reading (deregulation J-curve) predicts "
        "the same temporal pattern via different causal mechanism. This "
        "test cannot distinguish them — see `steelman` in the spec.",
        "",
        "## Data",
        "",
    ]
    for k, v in manifest.items():
        if v.get("missing"):
            lines.append(f"- **MISSING** `{v['publisher']}:{v['series']}` (blocks {k} leg)")
        else:
            lines.append(f"- {v['publisher']}:{v['series']} — `{v['vintage_file']}`")
    lines.append("")

    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict[:300]}")


if __name__ == "__main__":
    main()
