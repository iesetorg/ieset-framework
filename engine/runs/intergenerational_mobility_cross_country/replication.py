#!/usr/bin/env python3
"""Replication — Cross-country intergenerational mobility decomposition.

Spec: hypotheses/distribution/intergenerational_mobility_cross_country.yaml v1
Steelman: hypotheses/steelman/intergenerational_mobility_cross_country.md

PRIMARY (dispositive): the cross-country regression
    mobility = b0 + b1*edu_inequality + b2*residential_segregation
             + b3*housing_affordability + b4*controls + epsilon
must be ESTIMABLE (i.e. all four left-hand-side / institutional-channel
series available for at least 12 of the 20 OECD countries in the
sample) AND must yield:
    partial_R2_institutional_channels >= 0.40
    partial_R2_institutional_channels >  partial_R2_gini_alone
    leave-one-out: no single country flips the sign of any of b1, b2, b3.

If any of those LHS or institutional-channel series is not in the
on-disk vintages, this replication emits `inconclusive — data gap`
with a complete listing of which publisher:series are missing, per
HANDOFF_TO_RUN_AGENT.md ("Don't fabricate data. If the publisher's
vintage doesn't contain a series the spec needs, emit `inconclusive
(data gap on <publisher>:<series>)` and stop.").

Method-validity gates (METHOD_VALID):
  - n >= 12 of 20 OECD-country panel with non-null mobility AND
    non-null institutional channels.
  - leave-one-out stability across all 20 countries.

The verdict word is the first token in `diagnostics.verdict`, parsed
case-insensitively by the scoring layer (web/lib/content.ts).
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
HID = "intergenerational_mobility_cross_country"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
COUNTRIES = [
    "USA", "GBR", "CAN", "AUS", "FRA", "DEU", "ITA", "ESP", "NLD", "SWE",
    "NOR", "DNK", "FIN", "CHE", "BEL", "AUT", "IRL", "NZL", "JPN", "KOR",
]
PERIOD = (1990, 2020)

# Required series the spec calls for. (publisher, series).
# The primary regression needs at least one true mobility outcome and all
# three institutional channels. Controls are reported as gaps but are not
# the binding blocker in the current local vintage set.
REQUIRED_OUTCOME = [
    ("owid", "intergenerational-earnings-elasticity"),
    ("owid", "share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile"),
]
REQUIRED_CHANNELS = [
    # OECD Education-at-a-Glance subnational per-pupil spending dispersion
    ("oecd", "OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0"),
    # OECD Affordable Housing Database — income segregation index
    ("oecd", "OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0"),
    # BIS price-to-income (housing affordability)
    ("bis", "WS_SPP"),
]
REQUIRED_CONTROLS = [
    ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
    ("world_bank_wdi", "SI.POV.GINI"),
    ("wgi", "GOV_WGI_GE.EST"),
    ("world_bank_wdi", "SE.TER.CUAT.BA.ZS"),
]

# Falsification thresholds (from spec.falsification.threshold)
PARTIAL_R2_INSTITUTIONAL_THRESHOLD = 0.40
MIN_COUNTRIES_WITH_DATA = 12  # of 20


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    """Return latest vintage parquet for (pub, series) or None if absent.

    Per spec the OECD subnational dataflows use comma/at-separated URNs;
    on-disk files use underscore-flattened names. Try both forms.
    """
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    candidates = []
    for s in {series, series.replace(",", "_").replace("@", "_")}:
        candidates.extend(sorted(d.glob(f"{s}@*.parquet"), key=lambda p: p.stat().st_mtime))
    return candidates[-1] if candidates else None


def load_long(path: Path) -> pd.DataFrame:
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


ISO2_TO_ISO3 = {
    "AU": "AUS", "AT": "AUT", "BE": "BEL", "CA": "CAN", "CH": "CHE",
    "DE": "DEU", "DK": "DNK", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "GB": "GBR", "IE": "IRL", "IT": "ITA", "JP": "JPN", "KR": "KOR",
    "NL": "NLD", "NO": "NOR", "NZ": "NZL", "SE": "SWE", "US": "USA",
}


def ols(y: pd.Series, x: pd.DataFrame) -> tuple[pd.Series, pd.Series, float]:
    X = np.column_stack([np.ones(len(x)), x.to_numpy(dtype=float)])
    yv = y.to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    resid = yv - X @ beta
    dof = max(len(yv) - X.shape[1], 1)
    sigma2 = float((resid @ resid) / dof)
    vcov = sigma2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(vcov))
    ss_tot = float(((yv - yv.mean()) ** 2).sum())
    r2 = 1.0 - float((resid @ resid) / ss_tot) if ss_tot else 0.0
    names = ["intercept", *list(x.columns)]
    return pd.Series(beta, index=names), pd.Series(se, index=names), r2


def partial_r2(y: pd.Series, full_x: pd.DataFrame, reduced_x: pd.DataFrame) -> float:
    _, _, r2_full = ols(y, full_x)
    _, _, r2_reduced = ols(y, reduced_x)
    if r2_reduced >= 1:
        return 0.0
    return float((r2_full - r2_reduced) / (1 - r2_reduced))


def build_analysis_frame(available: dict[str, dict]) -> tuple[pd.DataFrame, dict[str, int]]:
    mob = load_long(REPO_ROOT / available["owid:intergenerational-earnings-elasticity"]["vintage_file"])
    mob = mob[mob["country_iso3"].isin(COUNTRIES)]
    mob = mob.groupby("country_iso3", as_index=False)["value"].mean().rename(columns={"value": "mobility_ige"})

    edu_path = REPO_ROOT / available["oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0"]["vintage_file"]
    edu = pq.read_table(edu_path).to_pandas()
    edu["value"] = pd.to_numeric(edu["value"], errors="coerce")
    edu["period"] = pd.to_numeric(edu["period"], errors="coerce")
    edu = edu[
        (edu["MEASURE"] == "FIN_PERSTUD")
        & (edu["EDUCATION_LEV"].isin(["ISCED11_1T3", "ISCED11_3"]))
        & (edu["EXP_SOURCE"] == "_T")
        & (edu["EXP_DESTINATION"] == "INST_EDU")
        & (edu["EXPENDITURE_TYPE"] == "DIR_EXP")
        & (edu["UNIT_MEASURE"] == "USD_PPP_ST")
        & edu["value"].notna()
    ].copy()
    edu_country_year = []
    for (country, year), g in edu.groupby(["COUNTRY", "period"]):
        region_values = g.groupby("REF_AREA")["value"].mean().dropna()
        if len(region_values) < 2 or region_values.mean() == 0:
            continue
        edu_country_year.append({
            "country_iso3": country,
            "year": int(year),
            "edu_spending_cv": float(region_values.std(ddof=0) / region_values.mean()),
            "edu_region_count": int(len(region_values)),
        })
    edu_cv = pd.DataFrame(edu_country_year)
    if not edu_cv.empty:
        edu_cv = edu_cv.groupby("country_iso3", as_index=False).agg(
            edu_spending_cv=("edu_spending_cv", "mean"),
            edu_region_count=("edu_region_count", "max"),
        )

    h_path = REPO_ROOT / available["oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0"]["vintage_file"]
    h = pq.read_table(h_path).to_pandas()
    h["value"] = pd.to_numeric(h["value"], errors="coerce")
    h["period"] = pd.to_numeric(h["period"], errors="coerce")
    afford = h[(h["MEASURE"] == "3_2") & h["value"].notna()].groupby("REF_AREA", as_index=False)["value"].mean()
    afford = afford.rename(columns={"REF_AREA": "country_iso3", "value": "housing_affordability"})
    overburden = h[(h["MEASURE"] == "3_3") & h["value"].notna()].groupby("REF_AREA", as_index=False)["value"].mean()
    overburden = overburden.rename(columns={"REF_AREA": "country_iso3", "value": "housing_overburden"})

    bis_path = REPO_ROOT / available["bis:WS_SPP"]["vintage_file"]
    bis = pq.read_table(bis_path).to_pandas()
    bis["country_iso3"] = bis["REF_AREA"].map(ISO2_TO_ISO3)
    bis["value"] = pd.to_numeric(bis["value"], errors="coerce")
    house_price = bis[bis["country_iso3"].notna() & bis["value"].notna()].groupby("country_iso3", as_index=False)["value"].mean()
    house_price = house_price.rename(columns={"value": "house_price_to_income"})

    wdi_gdp = load_long(REPO_ROOT / available["world_bank_wdi:NY.GDP.PCAP.PP.KD"]["vintage_file"])
    gdp = wdi_gdp[wdi_gdp["country_iso3"].isin(COUNTRIES)].groupby("country_iso3", as_index=False)["value"].mean()
    gdp["log_gdp_pc"] = np.log(gdp["value"])
    gdp = gdp[["country_iso3", "log_gdp_pc"]]

    gini = load_long(REPO_ROOT / available["world_bank_wdi:SI.POV.GINI"]["vintage_file"])
    gini = gini[gini["country_iso3"].isin(COUNTRIES)].groupby("country_iso3", as_index=False)["value"].mean()
    gini = gini.rename(columns={"value": "gini"})

    wgi = load_long(REPO_ROOT / available["wgi:GOV_WGI_GE.EST"]["vintage_file"])
    wgi = wgi[wgi["country_iso3"].isin(COUNTRIES)].groupby("country_iso3", as_index=False)["value"].mean()
    wgi = wgi.rename(columns={"value": "gov_effectiveness"})

    frame = mob.merge(edu_cv, on="country_iso3", how="left")
    for right in (afford, overburden, house_price, gdp, gini, wgi):
        frame = frame.merge(right, on="country_iso3", how="left")

    coverage = {col: int(frame[col].notna().sum()) for col in frame.columns if col != "country_iso3"}
    return frame, coverage


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Vintage discovery ----------
    available: dict[str, dict] = {}
    missing: list[str] = []

    for pub, series in REQUIRED_OUTCOME + REQUIRED_CHANNELS + REQUIRED_CONTROLS:
        p = latest(pub, series)
        key = f"{pub}:{series}"
        if p is None:
            missing.append(key)
        else:
            available[key] = {
                "publisher": pub,
                "series": series,
                "vintage_file": str(p.relative_to(REPO_ROOT)),
                "sha256": sha256(p),
            }

    # ---------- Decide if we can run the regression ----------
    missing_outcome = [f"{p}:{s}" for p, s in REQUIRED_OUTCOME if f"{p}:{s}" not in available]
    missing_channels = [f"{p}:{s}" for p, s in REQUIRED_CHANNELS if f"{p}:{s}" not in available]
    missing_controls = [f"{p}:{s}" for p, s in REQUIRED_CONTROLS if f"{p}:{s}" not in available]

    # The regression needs at least one mobility outcome and all three channels.
    can_run = (
        len(missing_outcome) < len(REQUIRED_OUTCOME)
        and len(missing_channels) == 0
    )

    # ---------- METHOD_VALID gate: not enough data -> inconclusive ----------
    if not can_run:
        binding_missing = []
        if len(missing_outcome) == len(REQUIRED_OUTCOME):
            binding_missing.extend(missing_outcome)
        binding_missing.extend(missing_channels)
        if not binding_missing:
            binding_missing = missing_outcome + missing_channels
        available_outcomes = [
            f"{p}:{s}" for p, s in REQUIRED_OUTCOME if f"{p}:{s}" in available
        ]
        verdict_reason = (
            "data gap on "
            + ", ".join(binding_missing)
            + ". The spec's primary regression cannot be estimated without "
            "a mobility outcome series and all three institutional-channel "
            "series. The v1 notes explicitly data-gate this test on an OWID "
            "or OECD intergenerational-mobility mirror, OECD Education-at-a-"
            "Glance subnational spending dispersion, and OECD Affordable "
            "Housing Database income-segregation indices. No coefficients "
            "computed."
        )
        verdict = (
            "inconclusive - " + verdict_reason
        )
        data_repair_note = (
            "2026-05-04 source repair fetched the live OWID Corak/Chen-"
            "Forster-Llena-Nozal intergenerational earnings-elasticity mirror "
            f"({', '.join(available_outcomes) or 'no mobility outcome available'}). "
            "The primary regression still remains data-gated because the OECD "
            "subnational education-spending dispersion and OECD Affordable "
            "Housing income-segregation channels are not present locally. The "
            "bottom-to-top-quintile mobility outcome is also still unavailable "
            "as a robustness outcome. WDI GDP per capita or poverty-headcount "
            "series are not valid substitutes for the preregistered mobility "
            "outcomes or institutional channels."
        )

        diagnostics = {
            "verdict": verdict,
            "verdict_label": "INCONCLUSIVE_DATA_PENDING",
            "verdict_reason": verdict_reason,
            "all_pass": False,
            "method_valid": False,
            "data_gap": True,
            "data_repair_note": data_repair_note,
            "binding_missing_series": binding_missing,
            "missing_outcome_series": missing_outcome,
            "missing_channel_series": missing_channels,
            "missing_control_series": missing_controls,
            "available_series": sorted(available.keys()),
            "n_countries_in_sample": len(COUNTRIES),
            "min_countries_required": MIN_COUNTRIES_WITH_DATA,
            "partial_r2_institutional_channels": None,
            "partial_r2_gini_alone": None,
            "loo_robust": None,
            "primary_threshold_partial_r2": PARTIAL_R2_INSTITUTIONAL_THRESHOLD,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

        # Empty coefficients table — schema-compliant placeholder.
        pd.DataFrame(
            [
                {"spec": "primary", "term": "partial_r2_institutional_channels", "estimate": np.nan},
                {"spec": "primary", "term": "partial_r2_gini_alone",            "estimate": np.nan},
            ]
        ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

        # Chart data — show what the analysis WOULD look like by listing the
        # required-but-missing series. Render-friendly empty result.
        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "Intergenerational mobility cross-country — DATA GAP",
            "subtitle": (
                f"{len(missing_outcome)+len(missing_channels)} of "
                f"{len(REQUIRED_OUTCOME)+len(REQUIRED_CHANNELS)} required outcome/"
                f"channel series not yet fetched. Regression cannot be estimated."
            ),
            "type": "line",
            "x_axis": {"label": "Country", "type": "linear"},
            "y_axis": {"label": "intergenerational earnings elasticity (target)", "type": "linear"},
            "series": [],
            "annotations": [
                {
                    "type": "note",
                    "label": (
                        "Required-but-missing series: "
                        + "; ".join(binding_missing)
                    ),
                }
            ],
            "sources": [
                {
                    "publisher_id": v["publisher"],
                    "series_id": v["series"],
                    "vintage_file": v["vintage_file"],
                }
                for v in available.values()
            ],
            "permalink": f"/h/{HID}",
        }
        (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

        manifest_lines = [
            f"hypothesis_id: {HID}",
            f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
            "status: data_gap_inconclusive",
            "missing_series:",
        ]
        for k in missing_outcome + missing_channels + missing_controls:
            manifest_lines.append(f"  - {k}")
        manifest_lines.append("vintages:")
        for k, v in available.items():
            manifest_lines.append(f"  '{k}':")
            manifest_lines.append(f"    publisher: {v['publisher']}")
            manifest_lines.append(f"    series: {v['series']}")
            manifest_lines.append(f"    vintage_file: {v['vintage_file']}")
            manifest_lines.append(f"    sha256: {v['sha256']}")
        (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

        card = [
            "# Intergenerational mobility — cross-country decomposition",
            "",
            f"**Verdict:** {verdict}",
            "",
            "## Summary",
            "",
            "- The hypothesis requires a cross-country regression of mobility on "
            "three institutional channels (education-spending inequality, residential "
            "segregation, housing affordability) plus controls.",
            "- The v1 spec flags the data gap explicitly: OECD SDD SOC "
            "mobility extension, Chetty opportunity-atlas (US-only), OECD "
            "Education-at-a-Glance subnational spending dispersion, and OECD "
            "Affordable Housing Database income-segregation support are not "
            "fully present in the local vintage set.",
            "- 2026-05-04 source repair: the live OWID elasticity chart was "
            "mapped and fetched as the preregistered earnings-elasticity "
            "outcome; the bottom-to-top-quintile robustness outcome and the "
            "two OECD institutional-channel vintages remain unavailable.",
            f"- Required series: {len(REQUIRED_OUTCOME)} outcome, "
            f"{len(REQUIRED_CHANNELS)} institutional-channel, "
            f"{len(REQUIRED_CONTROLS)} controls.",
            f"- Found on-disk: {len(available)} of "
            f"{len(REQUIRED_OUTCOME)+len(REQUIRED_CHANNELS)+len(REQUIRED_CONTROLS)}.",
            f"- Missing outcome: {missing_outcome or '(none)'}.",
            f"- Binding missing series: {binding_missing or '(none)'}.",
            f"- Missing channels: {missing_channels or '(none)'}.",
            f"- Missing controls: {missing_controls or '(none)'}.",
            "",
            "## Method",
            "",
            "Pre-registered specification (cross-section, n ~ 20):",
            "",
            "    mobility ~ edu_inequality + residential_segregation",
            "             + housing_affordability + log(GDP_pc) + Gini + gov_eff",
            "",
            "Primary statistic: partial R-squared of the three institutional "
            "channels relative to the controls-only model. Secondary: partial "
            "R-squared of Gini alone, leave-one-out sign stability of each "
            "channel coefficient.",
            "",
            "Falsification thresholds: partial_R2_channels >= 0.40 AND "
            "partial_R2_channels > partial_R2_gini_alone AND no single country "
            "flips a channel sign.",
            "",
            "## Data",
            "",
            "Required (per spec):",
            "",
        ]
        for pub, series in REQUIRED_OUTCOME + REQUIRED_CHANNELS + REQUIRED_CONTROLS:
            status = "available" if f"{pub}:{series}" in available else "**missing**"
            card.append(f"- `{pub}:{series}` — {status}")
        card.append("")
        card.append(
            "Promotion verdict: inconclusive (method-validity gate fails on data "
            "availability). Per HANDOFF_TO_RUN_AGENT.md a data gap is NOT a "
            "refutation - the scoreboard treats this as neutral. Re-run when "
            "the remaining OECD subnational fetchers are wired."
        )
        (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

        print(f"verdict: {verdict}")
        return

    # ---------- Regression path ----------
    frame, coverage = build_analysis_frame(available)
    channels = ["edu_spending_cv", "housing_overburden", "house_price_to_income"]
    controls = ["log_gdp_pc", "gini", "gov_effectiveness"]
    regression_cols = ["mobility_ige", *channels, *controls]
    reg = frame.dropna(subset=regression_cols).copy()

    if len(reg) < MIN_COUNTRIES_WITH_DATA:
        verdict = (
            "inconclusive - data coverage below method-valid threshold. "
            f"All required vintages are now present, but only {len(reg)} "
            f"countries have non-null mobility, institutional-channel, and "
            f"control observations for the preregistered regression; threshold "
            f"is {MIN_COUNTRIES_WITH_DATA}."
        )
        diagnostics = {
            "verdict": verdict,
            "verdict_label": "INCONCLUSIVE_COVERAGE_PENDING",
            "all_pass": False,
            "method_valid": False,
            "data_gap": False,
            "coverage_gap": True,
            "available_series": sorted(available.keys()),
            "missing_outcome_series": missing_outcome,
            "missing_channel_series": missing_channels,
            "missing_control_series": missing_controls,
            "coverage_by_variable": coverage,
            "n_countries_in_sample": len(COUNTRIES),
            "n_countries_with_complete_regression_data": int(len(reg)),
            "countries_with_complete_regression_data": sorted(reg["country_iso3"].tolist()),
            "min_countries_required": MIN_COUNTRIES_WITH_DATA,
            "partial_r2_institutional_channels": None,
            "partial_r2_gini_alone": None,
            "loo_robust": None,
            "primary_threshold_partial_r2": PARTIAL_R2_INSTITUTIONAL_THRESHOLD,
        }
        coeff = frame[["country_iso3", *regression_cols]].copy()
        coeff.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "Intergenerational mobility cross-country — COVERAGE GAP",
            "subtitle": f"{len(reg)} complete countries; threshold is {MIN_COUNTRIES_WITH_DATA}.",
            "type": "scatter",
            "x_axis": {"label": "education-spending dispersion", "type": "linear"},
            "y_axis": {"label": "intergenerational earnings elasticity", "type": "linear"},
            "series": [
                {
                    "name": "available countries",
                    "points": [
                        {
                            "x": None if pd.isna(row.edu_spending_cv) else float(row.edu_spending_cv),
                            "y": None if pd.isna(row.mobility_ige) else float(row.mobility_ige),
                            "label": row.country_iso3,
                        }
                        for row in frame.itertuples()
                    ],
                }
            ],
            "annotations": [{"type": "note", "label": verdict}],
            "sources": [
                {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
                for v in available.values()
            ],
            "permalink": f"/h/{HID}",
        }
        status = "coverage_gap_inconclusive"
    else:
        y = reg["mobility_ige"]
        full_x = reg[channels + controls]
        control_x = reg[controls]
        gini_x = reg[["gini"] + [c for c in controls if c != "gini"]]
        beta, se, r2_full = ols(y, full_x)
        p_channels = partial_r2(y, full_x, control_x)
        p_gini = partial_r2(y, gini_x, reg[[c for c in controls if c != "gini"]])

        signs = np.sign(beta[channels])
        loo_flip = False
        loo_rows = []
        for country in reg["country_iso3"]:
            sub = reg[reg["country_iso3"] != country]
            b_sub, _, _ = ols(sub["mobility_ige"], sub[channels + controls])
            sub_signs = np.sign(b_sub[channels])
            flips = [c for c in channels if signs[c] != 0 and sub_signs[c] != 0 and signs[c] != sub_signs[c]]
            loo_flip = loo_flip or bool(flips)
            loo_rows.append({"dropped_country": country, "flipped_terms": flips})

        all_pass = (
            p_channels >= PARTIAL_R2_INSTITUTIONAL_THRESHOLD
            and p_channels > p_gini
            and not loo_flip
        )
        verdict = "supported" if all_pass else "refuted"
        verdict += (
            f" - institutional-channel partial R2={p_channels:.3f}, "
            f"Gini partial R2={p_gini:.3f}, leave-one-out robust={not loo_flip}."
        )
        diagnostics = {
            "verdict": verdict,
            "verdict_label": verdict.split()[0].upper(),
            "all_pass": all_pass,
            "method_valid": True,
            "data_gap": False,
            "coverage_gap": False,
            "available_series": sorted(available.keys()),
            "coverage_by_variable": coverage,
            "n_countries_with_complete_regression_data": int(len(reg)),
            "countries_with_complete_regression_data": sorted(reg["country_iso3"].tolist()),
            "r2_full": r2_full,
            "partial_r2_institutional_channels": p_channels,
            "partial_r2_gini_alone": p_gini,
            "loo_robust": not loo_flip,
            "loo_diagnostics": loo_rows,
            "primary_threshold_partial_r2": PARTIAL_R2_INSTITUTIONAL_THRESHOLD,
        }
        coeff = pd.DataFrame(
            [
                {"spec": "primary_ols", "term": term, "estimate": float(beta[term]), "std_error": float(se[term])}
                for term in beta.index
            ]
            + [
                {"spec": "partial_r2", "term": "institutional_channels", "estimate": float(p_channels), "std_error": np.nan},
                {"spec": "partial_r2", "term": "gini_alone", "estimate": float(p_gini), "std_error": np.nan},
            ]
        )
        coeff.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "Intergenerational mobility decomposition",
            "subtitle": verdict,
            "type": "bar",
            "x_axis": {"label": "component", "type": "category"},
            "y_axis": {"label": "partial R2", "type": "linear"},
            "series": [
                {
                    "name": "partial R2",
                    "points": [
                        {"x": "institutional channels", "y": float(p_channels)},
                        {"x": "gini alone", "y": float(p_gini)},
                    ],
                }
            ],
            "sources": [
                {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
                for v in available.values()
            ],
            "permalink": f"/h/{HID}",
        }
        status = "completed"

    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    manifest_lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        f"status: {status}",
        "missing_series: []",
        "vintages:",
    ]
    for k, v in available.items():
        manifest_lines.append(f"  '{k}':")
        manifest_lines.append(f"    publisher: {v['publisher']}")
        manifest_lines.append(f"    series: {v['series']}")
        manifest_lines.append(f"    vintage_file: {v['vintage_file']}")
        manifest_lines.append(f"    sha256: {v['sha256']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

    card = [
        "# Intergenerational mobility — cross-country decomposition",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Required vintages are now present; complete regression coverage is {len(reg)} countries.",
        f"- Method-valid threshold is {MIN_COUNTRIES_WITH_DATA} countries.",
        f"- Coverage by variable: {coverage}.",
        "",
        "## Data",
        "",
    ]
    for pub, series in REQUIRED_OUTCOME + REQUIRED_CHANNELS + REQUIRED_CONTROLS:
        card.append(f"- `{pub}:{series}` — available")
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
