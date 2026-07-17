#!/usr/bin/env python3
"""Replication — Spain reported sexual-assault rate, definition-controlled.

Spec:     hypotheses/labour/spain_reported_sexual_assault_rate_definition_controlled.yaml
Steelman: hypotheses/steelman/spain_reported_sexual_assault_rate_definition_controlled.md

The hypothesis pre-registers a TWO-PART measurement-discipline test around
the 7 October 2022 entry-into-force of LO 10/2022 ("solo si es si"):

  Q1 (cross-country panel, 2015-2021, pre-reform):
      log(rate_per_100k) ~ Spain_dummy + country_FE + year_FE
      SUPPORTED if |beta_Spain| < 0.10 log points and p > 0.10
      (Spain's pre-reform trajectory tracks the European pool).

  Q2 (within-Spain event study, 2018-2023):
      log(rate) = a + beta * post_2022_10_07 + delta * trend_break + FE
      SUPPORTED if beta > 0 AND the DEFINITIONAL component (sum of
      pre-reform abuso + agresion cells matched to the post-reform
      consolidated cell) accounts for > 50% of beta.

Both tests require:
  (i)  Eurostat `crim_off_cat` (police-recorded sexual-offence rate per
       100k, harmonised) — NOT present in `data/vintages/eurostat/`.
  (ii) Spain Ministerio del Interior `Sistema Estadistico de Criminalidad`
       Anales / Balances Trimestrales with category labels preserved
       across the 2022-10-07 reform — NOT present (manual-drop required;
       `data/manual/spain_mi/` does not exist).
  (iii) INE Estadistica de Condenados (convictions-based triangulation)
       — NOT present.

Without (i) Q1 cannot be estimated and a fortiori the Spain-vs-Europe
trajectory test is undefined. Without (ii) the (DEFINITIONAL, RESIDUAL)
decomposition for Q2 is mechanically impossible (Eurostat's harmonised
aggregate absorbs the Spanish category re-mapping into its post-2022
cells, so the same-definition reconstructed series cannot be built from
Eurostat alone). The framework's pre-registered position is that any
direct level comparison across the reform date is illegitimate; we
honour that by NOT substituting an unrelated series and labelling it
"sexual-assault rate".

This replication therefore returns INCONCLUSIVE (data gap on
eurostat:crim_off_cat plus manual:spain_mi). It still produces all four
artifacts (chart_data.json, diagnostics.json, coefficients.parquet,
manifest.yaml, result_card.md) so the run is structurally complete and
the framework's scoreboard renders the hypothesis with the correct
neutral colour. The chart shows the available CONTROLS panel
(WDI population / urbanisation / unemployment / migrant share for the
8 sample countries) so the surface area of what *was* loadable is
visible to a reader.

Per research documentation and DISCLOSURE.md: data-gap inconclusive is
the honest output rather than substituting a different series. v2
unblocks when (i) the Eurostat `crim_off_cat` fetcher is added and
(ii) the Ministerio del Interior category-preserved tables land in
`data/manual/spain_mi/`.
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
HID = "spain_reported_sexual_assault_rate_definition_controlled"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


def _data_root() -> Path:
    """Locate the data root.

    Vintages are gitignored, so they live in the main repo working tree
    rather than in per-feature worktrees. Prefer the local repo's
    `data/vintages` if it has any parquet files, otherwise fall back to
    the main checkout next door."""
    local = REPO_ROOT / "data"
    local_v = local / "vintages"
    if local_v.exists() and any(local_v.rglob("*.parquet")):
        return local
    # Worktrees live under <main>/.claude/worktrees/<name>; walk up.
    parts = REPO_ROOT.parts
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == ".claude" and i + 1 < len(parts) and parts[i + 1] == "worktrees":
            candidate = Path(*parts[:i]) / "data"
            if (candidate / "vintages").exists():
                return candidate
            break
    return local


DATA_ROOT = _data_root()

# Sample from the spec (sample.countries)
TREATED = "ESP"
COMPARATORS = ["FRA", "ITA", "PRT", "DEU", "SWE", "NLD", "BEL"]
COUNTRIES = [TREATED] + COMPARATORS

# Q1 window: pre-reform panel
Q1_WINDOW = (2015, 2021)
# Q2 window: within-Spain event study
Q2_WINDOW = (2018, 2023)
REFORM_EFFECTIVE_YEAR = 2023  # year-resolution coding; reform 2022-10-07

# Falsification thresholds from spec.falsification (made dispositive)
Q1_BETA_BAND = 0.10  # log points
Q1_P_THRESHOLD = 0.10
Q2_DEFINITIONAL_SHARE_THRESHOLD = 0.50

# Required outcome series — checked at runtime
REQUIRED_OUTCOMES = [
    ("eurostat", "crim_off_cat"),
]
REQUIRED_MANUAL = [
    "manual/spain_mi",  # Ministerio del Interior, category-preserved (relative to DATA_ROOT)
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = DATA_ROOT / "vintages" / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    return files[-1]


def load_long(path: Path) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value) rows."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Step 1: probe required outcome data ----------
    missing_outcomes: list[str] = []
    found_outcomes: dict[str, Path] = {}
    for pub, series in REQUIRED_OUTCOMES:
        p = latest(pub, series)
        if p is None:
            missing_outcomes.append(f"{pub}:{series}")
        else:
            found_outcomes[f"{pub}:{series}"] = p

    missing_manual: list[str] = []
    for rel in REQUIRED_MANUAL:
        if not (DATA_ROOT / rel).exists():
            missing_manual.append(f"data/{rel}")

    # ---------- Step 2: load whatever IS available (controls) ----------
    control_specs = [
        ("world_bank_wdi", "SP.POP.TOTL", "log_population", True),
        ("world_bank_wdi", "SP.URB.TOTL.IN.ZS", "urbanisation", False),
        ("world_bank_wdi", "SL.UEM.TOTL.ZS", "unemployment_rate", False),
        ("world_bank_wdi", "SM.POP.TOTL.ZS", "migrant_share", False),
    ]
    control_frames: dict[str, pd.DataFrame] = {}
    control_paths: dict[str, Path] = {}
    missing_controls: list[str] = []
    for pub, series, name, take_log in control_specs:
        p = latest(pub, series)
        if p is None:
            missing_controls.append(f"{pub}:{series}")
            continue
        df = load_long(p)
        df = df[df["country_iso3"].isin(COUNTRIES)].copy()
        if take_log:
            df["value"] = np.log(df["value"])
        control_frames[name] = df.rename(columns={"value": name})[
            ["country_iso3", "year", name]
        ]
        control_paths[name] = p

    # Build the merged controls panel for diagnostics + chart
    if control_frames:
        panel = None
        for name, frame in control_frames.items():
            panel = frame if panel is None else panel.merge(frame, on=["country_iso3", "year"], how="outer")
        panel = panel[panel["year"].between(Q1_WINDOW[0], Q2_WINDOW[1])].copy()
    else:
        panel = pd.DataFrame(columns=["country_iso3", "year"])

    # ---------- Step 3: manifest ----------
    manifest_entries: dict[str, dict[str, str]] = {}
    for name, p in control_paths.items():
        try:
            rel_str = str(p.relative_to(DATA_ROOT.parent))
        except ValueError:
            rel_str = str(p)
        manifest_entries[name] = {
            "publisher": p.parent.name,
            "series": p.name.split("@")[0],
            "vintage_file": rel_str,
            "sha256": sha256(p),
        }

    # ---------- Step 4: verdict (data-gap inconclusive) ----------
    gaps = []
    if missing_outcomes:
        gaps.append("eurostat:crim_off_cat")
    if missing_manual:
        gaps.append("manual:spain_mi")

    verdict = (
        "inconclusive (data gap on eurostat:crim_off_cat and "
        "manual:spain_mi) — Q1 (Spain-vs-Europe pre-reform panel) and "
        "Q2 (within-Spain definitional decomposition of the 2022-10-07 "
        "level-shift) both require police-recorded sexual-offence series "
        "that are not present in vintages. Per the spec's measurement "
        "discipline the framework refuses to substitute an unrelated "
        "proxy. Controls panel (population, urbanisation, unemployment, "
        "migrant-share) loaded for the 8 sample countries; outcome "
        f"series unavailable. Method gates: outcome-presence FAILED "
        f"({len(missing_outcomes)} required series missing, "
        f"{len(missing_manual)} required manual drops missing)."
    )

    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "outcome_data_present": False,
        "manual_data_present": False,
        "method_valid": False,
        "missing_outcome_series": missing_outcomes,
        "missing_manual_paths": missing_manual,
        "missing_control_series": missing_controls,
        "controls_loaded": list(control_frames.keys()),
        "controls_country_year_obs": int(len(panel)) if not panel.empty else 0,
        "sample_countries": COUNTRIES,
        "q1_window": list(Q1_WINDOW),
        "q2_window": list(Q2_WINDOW),
        "q1_beta_band_logpoints": Q1_BETA_BAND,
        "q1_p_threshold": Q1_P_THRESHOLD,
        "q2_definitional_share_threshold": Q2_DEFINITIONAL_SHARE_THRESHOLD,
        "primary_q1_beta_spain_pre_reform": None,
        "primary_q1_p_value": None,
        "primary_q2_level_shift_beta": None,
        "primary_q2_definitional_share": None,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Step 5: chart (controls trajectories — neutral, no false outcome) ----------
    palette = [
        "#E15759", "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2",
        "#EDC948", "#9C755F",
    ]
    series = []
    if "unemployment_rate" in control_frames:
        ur = control_frames["unemployment_rate"]
        for i, c in enumerate(COUNTRIES):
            sub = ur[ur["country_iso3"] == c].sort_values("year")
            if sub.empty:
                continue
            pts = [
                {"x": int(r.year), "y": float(r.unemployment_rate)}
                for r in sub.itertuples()
                if Q1_WINDOW[0] <= int(r.year) <= Q2_WINDOW[1]
            ]
            if not pts:
                continue
            series.append(
                {
                    "id": c,
                    "label": c,
                    "color": palette[i % len(palette)],
                    "treated": (c == TREATED),
                    "points": pts,
                }
            )

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": (
            "Spain LO 10/2022 — controls panel (outcome series UNAVAILABLE)"
        ),
        "subtitle": (
            "Verdict: inconclusive (data gap on eurostat:crim_off_cat and "
            "manual:spain_mi). Chart shows the harmonised unemployment "
            "control series across the 8-country sample to demonstrate the "
            "panel that loaded; the outcome series itself (police-recorded "
            "sexual-offence rate per 100k) is not in vintages, so neither "
            "Q1 nor Q2 of the pre-registered test can be evaluated."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Unemployment rate (%)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    "OUTCOME SERIES NOT LOADED. Required: eurostat:"
                    "crim_off_cat (Q1 cross-country panel) AND Ministerio "
                    "del Interior category-preserved tables under "
                    "data/manual/spain_mi/ (Q2 definitional decomposition). "
                    "Run reports inconclusive rather than substituting an "
                    "unrelated proxy."
                ),
            },
            {
                "type": "vertical_line",
                "x": 2022,
                "label": "LO 10/2022 effective 2022-10-07",
            },
        ],
        "sources": [
            {
                "publisher_id": v["publisher"],
                "series_id": v["series"],
                "vintage_file": v["vintage_file"],
            }
            for v in manifest_entries.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Step 6: coefficients (record the gates that failed) ----------
    coef_rows = [
        {
            "spec": "primary_q1",
            "term": "beta_spain_pre_reform_logpoints",
            "estimate": np.nan,
            "p_value": np.nan,
            "status": "unestimated_data_gap",
        },
        {
            "spec": "primary_q2",
            "term": "level_shift_beta_2022_10_07",
            "estimate": np.nan,
            "p_value": np.nan,
            "status": "unestimated_data_gap",
        },
        {
            "spec": "primary_q2",
            "term": "definitional_component_share_of_beta",
            "estimate": np.nan,
            "p_value": np.nan,
            "status": "unestimated_data_gap",
        },
        {
            "spec": "method_gate",
            "term": "outcome_series_present",
            "estimate": 0.0,
            "p_value": np.nan,
            "status": f"missing: {', '.join(missing_outcomes) or 'none'}",
        },
        {
            "spec": "method_gate",
            "term": "manual_drop_present",
            "estimate": 0.0,
            "p_value": np.nan,
            "status": f"missing: {', '.join(missing_manual) or 'none'}",
        },
        {
            "spec": "method_gate",
            "term": "control_series_loaded",
            "estimate": float(len(control_frames)),
            "p_value": np.nan,
            "status": ", ".join(control_frames.keys()) or "none",
        },
    ]
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Step 7: manifest.yaml ----------
    lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        "verdict_class: inconclusive_data_gap",
        "missing_outcome_series:",
    ]
    for s in (missing_outcomes or ["(none)"]):
        lines.append(f"  - {s}")
    lines.append("missing_manual_paths:")
    for s in (missing_manual or ["(none)"]):
        lines.append(f"  - {s}")
    lines.append("vintages:")
    for k, v in manifest_entries.items():
        lines.extend(
            [
                f"  {k}:",
                f"    publisher: {v['publisher']}",
                f"    series: {v['series']}",
                f"    vintage_file: {v['vintage_file']}",
                f"    sha256: {v['sha256']}",
            ]
        )
    if not manifest_entries:
        lines.append("  {}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n")

    # ---------- Step 8: result_card.md ----------
    card = [
        "# Spain reported sexual-assault rate, definition-controlled",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "- The hypothesis pre-registers a two-part measurement-discipline "
        "test: Q1 a Spain-vs-Europe panel on the pre-reform 2015-2021 window "
        "and Q2 a within-Spain event study around the 2022-10-07 entry "
        "into force of LO 10/2022 with a definitional/residual "
        "decomposition.",
        "- Both parts require police-recorded sexual-offence rate series "
        "that are NOT present in `data/vintages/`. Specifically:",
        f"  - Q1 needs **eurostat:crim_off_cat** — missing"
        f" ({'present' if not missing_outcomes else 'NOT present'}).",
        "  - Q2 needs the Ministerio del Interior `Sistema Estadistico "
        "de Criminalidad` Anales/Balances Trimestrales tables with the "
        "*pre-2022 abuso/agresion category labels preserved* "
        "(`data/manual/spain_mi/`)"
        f" ({'present' if not missing_manual else 'NOT present'}).",
        "- The framework refuses to substitute an unrelated proxy and "
        "label it 'sexual-assault rate'. Per the spec's pre-registered "
        "discipline, raw pre/post comparison of any series across the "
        "reform date is itself the framing the hypothesis is constructed "
        "to discourage.",
        "- Controls panel (population, urbanisation, unemployment, "
        f"migrant share) loaded for {len(COUNTRIES)} sample countries: "
        f"{', '.join(sorted(set(panel['country_iso3']))) if not panel.empty else 'none'}.",
        "",
        "## Verdict semantics",
        "",
        "Per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2, missing-data outcomes are "
        "`inconclusive` (method-validity failure), NOT `refuted`. "
        "Refutation requires a confidently-estimated primary statistic "
        "in the wrong direction; an unestimable primary cannot refute.",
        "",
        "## What v2 needs to unblock",
        "",
        "1. Add a Eurostat fetcher entry for `crim_off_cat` (police-"
        "recorded offences, harmonised) and rerun the loader so a vintage "
        "lands under `data/vintages/eurostat/crim_off_cat@*.parquet`. "
        "Q1 (TWFE on log-rate, 2015-2021, country and year FE, Spain "
        "indicator) is then a one-line estimation against the existing "
        "panel infrastructure.",
        "2. Manual-drop the Ministerio del Interior `Sistema Estadistico "
        "de Criminalidad` Anales / Balances Trimestrales tables for "
        "2018-2024 under `data/manual/spain_mi/`, preserving the *pre-"
        "reform* category split between `abuso sexual` and `agresion "
        "sexual` and the *post-reform* consolidated `agresion sexual` "
        "cell. Q2 (interrupted time series with definitional "
        "decomposition: pre-reform sum of abuso+agresion vs post-reform "
        "consolidated agresion) requires the category-preserved series; "
        "Eurostat's harmonised aggregate absorbs the Spanish category "
        "re-mapping into post-2022 cells and so cannot do this job.",
        "3. (Optional, strengthens Q2) INE Estadistica de Condenados as "
        "a convictions-based triangulation; fetched manually under "
        "`data/manual/spain_ine_condenados/`.",
        "4. (Optional, strengthens Q2 (b)) Encuesta Nacional de "
        "Violencia contra la Mujer post-reform wave to bound the "
        "reporting-propensity component of any residual.",
        "",
        "## Method (when v2 unblocks)",
        "",
        "- **Q1:** TWFE panel on the 8-country sample, 2015-2021. "
        "Outcome: log(rate per 100k). Specification: `log_rate ~ "
        "is_spain + country_FE + year_FE + log_pop + urbanisation + "
        "unemployment + migrant_share`. Test: `|beta_spain| < 0.10` and "
        f"`p > {Q1_P_THRESHOLD}` (Spain not distinguishable from "
        "European trend). Cluster s.e. by country.",
        "- **Q2:** Within-Spain interrupted time series 2018-2023 (annual "
        "Eurostat) plus monthly Ministerio del Interior series where "
        "available. Specification: `log(rate_t) = a + beta * post_t + "
        "gamma * t + delta * (t - t_reform) * post_t + month_FE + e`. "
        "Definitional decomposition: estimate the same regression on "
        "(pre-reform abuso + agresion summed) vs (post-reform "
        "consolidated agresion); the residual gap between the raw beta "
        "and the same-definition beta is the definitional component. "
        f"SUPPORTED if beta > 0 AND definitional component > "
        f"{int(Q2_DEFINITIONAL_SHARE_THRESHOLD*100)}% of beta.",
        "",
        "## Data",
        "",
        "Loaded:",
    ]
    for k, v in manifest_entries.items():
        card.append(f"- {v['publisher']}:{v['series']} ({k})")
    if not manifest_entries:
        card.append("- (none)")
    card.extend([
        "",
        "Required but missing (the gap that drove the inconclusive verdict):",
        "- eurostat:crim_off_cat (police-recorded sexual offences, "
        "harmonised; primary outcome for Q1 and Q2)",
        "- data/manual/spain_mi/ (Ministerio del Interior category-"
        "preserved tables; required for the Q2 definitional/residual "
        "decomposition)",
    ])
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
