#!/usr/bin/env python3
"""Replication — US decoupling under consumption-based emissions accounting,
1980-2020.

Spec: hypotheses/growth/us_decoupling_consumption_based_accounting.yaml v1
Position-claim: eco_socialist #4 (school predicts: supported)

The claim: US GDP growth 1980-2020 did not absolutely decouple from CO2
emissions once offshored manufacturing emissions are attributed via
consumption-based accounting; the 'decoupling' narrative dissolves under
offshoring-corrected (Eora MRIO / Global Carbon Project) emissions.

PRIMARY (dispositive): the hypothesis is SUPPORTED if cumulative US real
GDP growth 1980-2020 (NY.GDP.MKTP.KD) exceeds +50% AND the absolute
change in US consumption-based CO2 (level 2020 vs level 1980) is a
decline of less than 5%. REFUTED if consumption-based CO2 declined by at
least 25% over 1980-2020. PARTIAL otherwise.

INFORMATIVE (not gating): cumulative change in territorial CO2 per capita
and the implied territorial-vs-consumption gap.

METHOD-VALID: requires both world_bank_wdi:NY.GDP.MKTP.KD and a US
1980-2020 consumption-based CO2 series (owid:consumption_co2 or
equivalent GCP/Eora MRIO vintage) on disk. If the consumption-based
series is missing, the run emits 'inconclusive (data gap on
owid:consumption_co2)' and reports the territorial-only descriptive
numbers as informative — per research documentation §"What to do when
your spec needs data that isn't on disk".

DATA-GAP STATUS at first run (2026-04-27): the consumption-based CO2
series is NOT on disk in any vintage under data/vintages/owid/. Only
co2-emissions-per-capita (territorial / production-based) and
co2-intensity are present. The script therefore emits 'inconclusive
(data gap)' as the verdict; the territorial GDP and CO2 numbers are
reported as descriptive context. The script is ready to produce a
dispositive verdict the moment a consumption-based CO2 fetcher lands;
no spec change required at that point.
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
HID = "us_decoupling_consumption_based_accounting"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample (sample.countries from spec)
COUNTRY = "USA"
YEAR_START = 1980
YEAR_END = 2020

# Falsification thresholds (sharpened from spec.falsification)
GDP_GROWTH_FLOOR = 0.50          # cumulative GDP must rise > 50% for primary support
CONSUMPTION_CO2_SUPPORTED_DECLINE_CEILING = -0.05  # CO2 change > -5% (i.e. <5% decline)
CONSUMPTION_CO2_REFUTED_DECLINE_FLOOR = -0.25      # CO2 change <= -25% (>=25% decline) -> refuted

# Candidate publisher:series for consumption-based CO2.  We try several
# common slugs because OWID has used different names over time and the
# spec's `owid:consumption_co2` may be aliased on disk.
CONSUMPTION_CO2_CANDIDATES = [
    ("owid", "consumption_co2"),
    ("owid", "consumption-co2"),
    ("owid", "consumption-co2-per-capita"),
    ("owid", "consumption-based-co2-emissions"),
    ("owid", "consumption-based-co2-emissions-per-capita"),
    ("owid", "co2-consumption-based"),
    ("global_carbon_project", "consumption_co2"),
]


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


def try_latest(pub: str, series: str) -> Path | None:
    try:
        return latest(pub, series)
    except FileNotFoundError:
        return None


def load_long(path: Path) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value) rows. OWID
    uses the metric name as the value column instead of 'value'; treat
    the last non-meta column as the value field. The brief notes that
    OWID schemas may use `entity` instead of `country_iso3`; we handle
    both."""
    t = pq.read_table(path).to_pandas()
    # Normalise entity -> country_iso3 if needed (only if iso3 missing)
    if "country_iso3" not in t.columns and "entity" in t.columns:
        # entity is a country name, not iso3 — we can't convert here without
        # an iso3 mapping table. The OWID fetcher in this repo writes
        # country_iso3 already (verified by reading existing replication
        # scripts), so this branch is defensive only.
        raise ValueError(
            f"{path}: schema uses 'entity' (no country_iso3); fetcher needs to "
            f"emit ISO3 codes before this run can use it."
        )
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


def at_year(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def write_artifacts(
    verdict: str,
    diagnostics: dict,
    chart_data: dict,
    coefficients: pd.DataFrame,
    manifest: dict,
    card_lines: list[str],
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")
    coefficients.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
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
    (OUT_DIR / "result_card.md").write_text("\n".join(card_lines) + "\n")
    print(f"verdict: {verdict}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Required series: real GDP (territorial) ---
    gdp_path = latest("world_bank_wdi", "NY.GDP.MKTP.KD")
    # --- Territorial CO2 per capita (informative) ---
    territorial_path = latest("owid", "co2-emissions-per-capita")

    # --- Consumption-based CO2 (the dispositive series; may be missing) ---
    consumption_path = None
    consumption_publisher = None
    consumption_series = None
    for pub, series in CONSUMPTION_CO2_CANDIDATES:
        p = try_latest(pub, series)
        if p is not None:
            consumption_path = p
            consumption_publisher = pub
            consumption_series = series
            break

    manifest = {
        "real_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.MKTP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "territorial_co2_per_capita": {
            "publisher": "owid",
            "series": "co2-emissions-per-capita",
            "vintage_file": str(territorial_path.relative_to(REPO_ROOT)),
            "sha256": sha256(territorial_path),
        },
    }
    if consumption_path is not None:
        manifest["consumption_based_co2"] = {
            "publisher": consumption_publisher,
            "series": consumption_series,
            "vintage_file": str(consumption_path.relative_to(REPO_ROOT)),
            "sha256": sha256(consumption_path),
        }

    # ---------- Load + compute descriptive context (always run) ----------
    gdp = load_long(gdp_path)
    territorial = load_long(territorial_path)

    gdp_1980 = at_year(gdp, COUNTRY, YEAR_START)
    gdp_2020 = at_year(gdp, COUNTRY, YEAR_END)
    terr_1980 = at_year(territorial, COUNTRY, YEAR_START)
    terr_2020 = at_year(territorial, COUNTRY, YEAR_END)

    if gdp_1980 is None or gdp_2020 is None:
        verdict = (
            f"inconclusive (data gap on world_bank_wdi:NY.GDP.MKTP.KD) — US GDP "
            f"observations missing for {YEAR_START} or {YEAR_END}."
        )
        diag = {
            "verdict": verdict,
            "method_valid": False,
            "data_gap": "world_bank_wdi:NY.GDP.MKTP.KD",
        }
        chart = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "US decoupling under consumption-based accounting (data gap)",
            "subtitle": verdict,
            "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index (1980 = 1.0)", "type": "linear"},
            "series": [],
            "annotations": [{"type": "note", "label": verdict}],
            "sources": [
                {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
                for v in manifest.values()
            ],
            "permalink": f"/h/{HID}",
        }
        coefs = pd.DataFrame([{"spec": "method_valid", "term": "gdp_observations_present", "estimate": 0.0}])
        card = [
            f"# US decoupling under consumption-based accounting, 1980-2020",
            "",
            f"**Verdict:** {verdict}",
            "",
            "GDP observations missing for the boundary years; rerun once WDI vintage is repaired.",
        ]
        write_artifacts(verdict, diag, chart, coefs, manifest, card)
        return

    gdp_ratio = gdp_2020 / gdp_1980
    gdp_growth_pct = gdp_ratio - 1.0
    primary1_gdp_grew = gdp_growth_pct > GDP_GROWTH_FLOOR

    # Territorial change (informative)
    if terr_1980 is not None and terr_2020 is not None and terr_1980 > 0:
        terr_change_pct = (terr_2020 - terr_1980) / terr_1980
    else:
        terr_change_pct = None

    # ---------- METHOD_VALID gate: consumption-based series required ----------
    if consumption_path is None:
        verdict = (
            f"inconclusive (data gap on owid:consumption_co2) — the spec's "
            f"dispositive series, US consumption-based CO2 (Eora-MRIO / Global "
            f"Carbon Project), is not present in data/vintages/. Tried slugs: "
            f"{', '.join(s for _, s in CONSUMPTION_CO2_CANDIDATES)}. "
            f"Informative (territorial-only): US real GDP {YEAR_START}-{YEAR_END} "
            f"grew by {gdp_growth_pct*100:+.0f}% (ratio "
            f"{gdp_ratio:.2f}); US territorial CO2 per capita changed by "
            + (
                f"{terr_change_pct*100:+.0f}%."
                if terr_change_pct is not None
                else "<unavailable>."
            )
            + " Verdict on the offshoring-corrected claim cannot be issued until "
            "the consumption-based fetcher lands."
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "data_gap": "owid:consumption_co2",
            "candidates_tried": [f"{p}:{s}" for p, s in CONSUMPTION_CO2_CANDIDATES],
            "informative_territorial_only": {
                "country": COUNTRY,
                "year_start": YEAR_START,
                "year_end": YEAR_END,
                "gdp_1980": gdp_1980,
                "gdp_2020": gdp_2020,
                "gdp_ratio_2020_1980": gdp_ratio,
                "gdp_growth_pct": gdp_growth_pct,
                "primary1_gdp_grew_above_50pct": primary1_gdp_grew,
                "territorial_co2_pc_1980": terr_1980,
                "territorial_co2_pc_2020": terr_2020,
                "territorial_co2_pc_change_pct": terr_change_pct,
            },
            "thresholds": {
                "gdp_growth_floor": GDP_GROWTH_FLOOR,
                "consumption_co2_supported_decline_ceiling":
                    CONSUMPTION_CO2_SUPPORTED_DECLINE_CEILING,
                "consumption_co2_refuted_decline_floor":
                    CONSUMPTION_CO2_REFUTED_DECLINE_FLOOR,
            },
            "data_gap_note": (
                "The consumption-based CO2 series (owid:consumption_co2 / Global "
                "Carbon Project / Eora MRIO) is not yet in data/vintages/owid/. "
                "Only co2-emissions-per-capita (territorial) and co2-intensity "
                "are present. A dispositive verdict requires the offshoring-"
                "corrected series; the script will produce one automatically once "
                "any of the candidate slugs lands. Per framework convention, this "
                "is an inconclusive verdict — NOT a refutation — and is neutral "
                "on the school scoreboard."
            ),
        }

        # ---------- Chart: territorial-only context ----------
        ts_gdp = gdp[(gdp["country_iso3"] == COUNTRY) & gdp["year"].between(YEAR_START, YEAR_END)]
        ts_terr = territorial[
            (territorial["country_iso3"] == COUNTRY)
            & territorial["year"].between(YEAR_START, YEAR_END)
        ]
        gdp_pts = [
            {"x": int(r.year), "y": float(r.value / gdp_1980)}
            for r in ts_gdp.sort_values("year").itertuples()
        ]
        if terr_1980 is not None and terr_1980 > 0:
            terr_pts = [
                {"x": int(r.year), "y": float(r.value / terr_1980)}
                for r in ts_terr.sort_values("year").itertuples()
            ]
        else:
            terr_pts = []
        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "US real GDP vs territorial CO2 per capita, indexed to 1980",
            "subtitle": (
                f"INCONCLUSIVE — consumption-based CO2 series missing on disk. "
                f"Territorial-only: GDP {gdp_growth_pct*100:+.0f}%; "
                f"territorial CO2 per capita "
                + (f"{terr_change_pct*100:+.0f}%" if terr_change_pct is not None else "n/a")
                + "."
            ),
            "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index (1980 = 1.0)", "type": "linear"},
            "series": [
                {
                    "id": "GDP",
                    "label": "US real GDP (NY.GDP.MKTP.KD)",
                    "color": "#4E79A7",
                    "treated": False,
                    "points": gdp_pts,
                },
                {
                    "id": "TERRITORIAL_CO2_PC",
                    "label": "US territorial CO2 per capita (OWID)",
                    "color": "#E15759",
                    "treated": False,
                    "points": terr_pts,
                },
            ],
            "annotations": [
                {
                    "type": "note",
                    "label": (
                        "Consumption-based (offshoring-corrected) CO2 series not "
                        "yet on disk; verdict is INCONCLUSIVE (data gap). The "
                        "territorial-only series shown here cannot adjudicate "
                        "the spec's central claim."
                    ),
                }
            ],
            "sources": [
                {
                    "publisher_id": v["publisher"],
                    "series_id": v["series"],
                    "vintage_file": v["vintage_file"],
                }
                for v in manifest.values()
            ],
            "permalink": f"/h/{HID}",
        }

        coefs = pd.DataFrame(
            [
                {"spec": "informative", "term": "gdp_ratio_2020_1980", "estimate": gdp_ratio},
                {"spec": "informative", "term": "gdp_growth_pct", "estimate": gdp_growth_pct},
                {
                    "spec": "informative",
                    "term": "territorial_co2_pc_change_pct",
                    "estimate": terr_change_pct if terr_change_pct is not None else float("nan"),
                },
                {
                    "spec": "method_valid",
                    "term": "consumption_co2_series_on_disk",
                    "estimate": 0.0,
                },
            ]
        )

        card = [
            f"# US decoupling under consumption-based accounting, 1980-2020",
            "",
            f"**Verdict:** {verdict}",
            "",
            "## Summary",
            "",
            f"- The spec asks whether US 1980-2020 GDP growth absolutely decoupled "
            f"from CO2 emissions once offshored manufacturing emissions are "
            f"attributed via consumption-based accounting.",
            f"- The dispositive series — US consumption-based CO2 (Eora MRIO / "
            f"Global Carbon Project) — is **not on disk** in this vintage. "
            f"Tried slugs: {', '.join(s for _, s in CONSUMPTION_CO2_CANDIDATES)}.",
            f"- Verdict: **inconclusive (data gap on owid:consumption_co2)**.",
            "",
            "## Informative — territorial only (DOES NOT decide the verdict)",
            "",
            f"- US real GDP (NY.GDP.MKTP.KD) {YEAR_START}-{YEAR_END}: ratio "
            f"**{gdp_ratio:.2f}** (cumulative growth **{gdp_growth_pct*100:+.0f}%**). "
            f"GDP-growth premise (>50%) "
            f"**{'holds' if primary1_gdp_grew else 'does NOT hold'}**.",
            f"- US territorial CO2 per capita (OWID): "
            + (
                f"**{terr_change_pct*100:+.0f}%** change "
                f"({terr_1980:.2f} → {terr_2020:.2f} t per capita)."
                if terr_change_pct is not None
                else "**unavailable** in OWID vintage."
            ),
            "",
            "## Method",
            "",
            "Two boundary-year checks against the sharpened spec falsification:",
            "",
            f"1. PRIMARY-A: GDP ratio {YEAR_END}/{YEAR_START} > "
            f"{1 + GDP_GROWTH_FLOOR:.2f} (i.e. >+50% cumulative).",
            f"2. PRIMARY-B: consumption-based CO2 absolute change "
            f"> {CONSUMPTION_CO2_SUPPORTED_DECLINE_CEILING*100:+.0f}% "
            f"(i.e. less than 5% decline) → SUPPORTED. "
            f"<= {CONSUMPTION_CO2_REFUTED_DECLINE_FLOOR*100:+.0f}% → REFUTED.",
            "",
            "PRIMARY-B cannot be evaluated until the consumption-based CO2 "
            "fetcher lands. Per research documentation (\"What to do when "
            "your spec needs data that isn't on disk\"), the run emits "
            "inconclusive rather than substituting a different series.",
            "",
            "## Steelman (offered because the run is inconclusive)",
            "",
            "Critics of the decoupling-success narrative argue that headline "
            "US territorial CO2 declines from the early 2000s onwards reflect "
            "two structural shifts that consumption-based accounting strips "
            "out: (a) offshoring of energy-intensive manufacturing to China "
            "and other emerging economies whose territorial emissions then "
            "rose, and (b) the coal-to-gas substitution in US electricity, "
            "which lowers domestic CO2 per kWh but does not reduce global "
            "emissions from imported manufactured goods. Under Eora MRIO and "
            "Global Carbon Project consumption-based accounting, US CO2 "
            "emissions are typically reported as ~7-12% higher than "
            "territorial in the 2000s and as having declined LESS than "
            "territorial — by some accounts roughly flat through the 2010s. "
            "If the consumption-based series confirms that pattern across "
            "1980-2020, the spec's PRIMARY would resolve to SUPPORTED. The "
            "inconclusive verdict here is therefore consistent with the "
            "claim being plausible but not yet testable on this repo's data.",
            "",
            "## Data",
            "",
            f"- world_bank_wdi:NY.GDP.MKTP.KD (vintage on disk)",
            f"- owid:co2-emissions-per-capita (territorial; informative only)",
            f"- owid:consumption_co2 (REQUIRED; not on disk; backlog the fetcher)",
        ]

        write_artifacts(verdict, diagnostics, chart_data, coefs, manifest, card)
        return

    # ---------- DISPOSITIVE PATH (only reachable when consumption-based on disk) ----------
    consumption = load_long(consumption_path)
    cons_1980 = at_year(consumption, COUNTRY, YEAR_START)
    cons_2020 = at_year(consumption, COUNTRY, YEAR_END)

    if cons_1980 is None or cons_2020 is None or cons_1980 <= 0:
        verdict = (
            f"inconclusive (data gap on {consumption_publisher}:{consumption_series}) — "
            f"vintage present but US {YEAR_START} or {YEAR_END} observation missing."
        )
        diag = {
            "verdict": verdict,
            "method_valid": False,
            "data_gap": f"{consumption_publisher}:{consumption_series}",
        }
        chart = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "US decoupling — boundary-year gap on consumption series",
            "subtitle": verdict,
            "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index (1980 = 1.0)", "type": "linear"},
            "series": [],
            "annotations": [{"type": "note", "label": verdict}],
            "sources": [
                {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
                for v in manifest.values()
            ],
            "permalink": f"/h/{HID}",
        }
        coefs = pd.DataFrame([{"spec": "method_valid", "term": "consumption_boundary_obs", "estimate": 0.0}])
        card = [
            f"# US decoupling under consumption-based accounting, 1980-2020",
            "",
            f"**Verdict:** {verdict}",
        ]
        write_artifacts(verdict, diag, chart, coefs, manifest, card)
        return

    cons_change_pct = (cons_2020 - cons_1980) / cons_1980

    primary2_supported = cons_change_pct > CONSUMPTION_CO2_SUPPORTED_DECLINE_CEILING
    primary2_refuted = cons_change_pct <= CONSUMPTION_CO2_REFUTED_DECLINE_FLOOR

    if primary1_gdp_grew and primary2_supported:
        verdict = (
            f"SUPPORTED — US real GDP grew {gdp_growth_pct*100:+.0f}% 1980-2020 "
            f"(>50% threshold) AND consumption-based CO2 changed by "
            f"{cons_change_pct*100:+.0f}% (less than 5% decline). The "
            f"decoupling claim dissolves under offshoring-corrected accounting."
        )
    elif primary2_refuted:
        verdict = (
            f"refuted — US consumption-based CO2 fell by {abs(cons_change_pct)*100:.0f}% "
            f"1980-2020 (>=25% decline), with GDP growing {gdp_growth_pct*100:+.0f}%. "
            f"Sustained absolute decoupling is visible even on the offshoring-"
            f"corrected series."
        )
    else:
        # GDP grew but CO2 declined modestly (between 5% and 25%), or GDP did
        # not grow >50% — either way, neither side dispositive
        verdict = (
            f"partial — US real GDP grew {gdp_growth_pct*100:+.0f}% 1980-2020; "
            f"consumption-based CO2 changed by {cons_change_pct*100:+.0f}%. "
            f"Neither the SUPPORTED nor REFUTED threshold met "
            f"(SUPPORTED needs CO2 change > -5%; REFUTED needs CO2 change <= -25%)."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "primary": {
            "gdp_ratio_2020_1980": gdp_ratio,
            "gdp_growth_pct": gdp_growth_pct,
            "consumption_co2_change_pct": cons_change_pct,
            "consumption_co2_1980": cons_1980,
            "consumption_co2_2020": cons_2020,
            "primary1_gdp_grew_above_50pct": primary1_gdp_grew,
            "primary2_consumption_supports_dissolution": primary2_supported,
            "primary2_consumption_refutes_with_decline": primary2_refuted,
        },
        "informative_territorial": {
            "territorial_co2_pc_1980": terr_1980,
            "territorial_co2_pc_2020": terr_2020,
            "territorial_co2_pc_change_pct": terr_change_pct,
        },
        "thresholds": {
            "gdp_growth_floor": GDP_GROWTH_FLOOR,
            "consumption_co2_supported_decline_ceiling":
                CONSUMPTION_CO2_SUPPORTED_DECLINE_CEILING,
            "consumption_co2_refuted_decline_floor":
                CONSUMPTION_CO2_REFUTED_DECLINE_FLOOR,
        },
    }

    # Chart: GDP, territorial CO2, consumption CO2, indexed to 1980
    series_data = []
    for label_id, label, df, base, color in [
        ("GDP", "US real GDP (NY.GDP.MKTP.KD)", gdp, gdp_1980, "#4E79A7"),
        (
            "TERRITORIAL_CO2_PC",
            "US territorial CO2 per capita",
            territorial,
            terr_1980,
            "#E15759",
        ),
        (
            "CONSUMPTION_CO2",
            "US consumption-based CO2",
            consumption,
            cons_1980,
            "#59A14F",
        ),
    ]:
        if base is None or base <= 0:
            continue
        sub = df[
            (df["country_iso3"] == COUNTRY)
            & df["year"].between(YEAR_START, YEAR_END)
        ].sort_values("year")
        pts = [
            {"x": int(r.year), "y": float(r.value / base)} for r in sub.itertuples()
        ]
        series_data.append({
            "id": label_id,
            "label": label,
            "color": color,
            "treated": label_id == "CONSUMPTION_CO2",
            "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US GDP vs territorial vs consumption-based CO2, indexed to 1980",
        "subtitle": (
            f"GDP {gdp_growth_pct*100:+.0f}% · "
            f"Consumption CO2 {cons_change_pct*100:+.0f}% · "
            + (f"Territorial CO2 {terr_change_pct*100:+.0f}%" if terr_change_pct is not None else "Territorial n/a")
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Index (1980 = 1.0)", "type": "linear"},
        "series": series_data,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"SUPPORTED if GDP > +50% AND consumption CO2 > -5%. "
                    f"REFUTED if consumption CO2 <= -25%."
                ),
            }
        ],
        "sources": [
            {
                "publisher_id": v["publisher"],
                "series_id": v["series"],
                "vintage_file": v["vintage_file"],
            }
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }

    coefs = pd.DataFrame(
        [
            {"spec": "primary", "term": "gdp_ratio_2020_1980", "estimate": gdp_ratio},
            {"spec": "primary", "term": "gdp_growth_pct", "estimate": gdp_growth_pct},
            {"spec": "primary", "term": "consumption_co2_change_pct", "estimate": cons_change_pct},
            {
                "spec": "informative",
                "term": "territorial_co2_pc_change_pct",
                "estimate": terr_change_pct if terr_change_pct is not None else float("nan"),
            },
        ]
    )

    card = [
        f"# US decoupling under consumption-based accounting, 1980-2020",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- US real GDP {YEAR_START}-{YEAR_END}: ratio **{gdp_ratio:.2f}** "
        f"(cumulative growth **{gdp_growth_pct*100:+.0f}%**).",
        f"- US consumption-based CO2 {YEAR_START}-{YEAR_END}: change "
        f"**{cons_change_pct*100:+.0f}%** ({cons_1980:.2f} → {cons_2020:.2f}).",
        f"- US territorial CO2 per capita: "
        + (
            f"**{terr_change_pct*100:+.0f}%**."
            if terr_change_pct is not None
            else "unavailable."
        ),
        "",
        "## Method",
        "",
        f"Boundary-year check on the spec's quantitative anchor: SUPPORTED if "
        f"GDP growth > +50% AND consumption-based CO2 change > -5% (i.e. "
        f"<5% decline — decoupling dissolves). REFUTED if consumption-based "
        f"CO2 declined by >=25%. PARTIAL otherwise.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.MKTP.KD",
        f"- owid:co2-emissions-per-capita (territorial; informative)",
        f"- {consumption_publisher}:{consumption_series} (consumption-based; dispositive)",
    ]

    write_artifacts(verdict, diagnostics, chart_data, coefs, manifest, card)


if __name__ == "__main__":
    main()
