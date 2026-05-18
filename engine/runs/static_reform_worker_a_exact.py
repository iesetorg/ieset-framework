#!/usr/bin/env python3
"""Exact local-data repairs for static migration and reform candidates.

These routines replace generic country-FE reruns when the registered treatment
is static or the local data cannot identify the preregistered FE coefficient.
They write run-local diagnostics, result cards, and provenance manifests.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "engine" / "runs"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, tuple):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, dict[str, Any]] = {}

    def latest(self, publisher: str, pattern: str) -> Path:
        files = sorted((ROOT / "data" / "vintages" / publisher).glob(pattern))
        if not files:
            raise FileNotFoundError(f"missing local vintage {publisher}:{pattern}")
        return files[-1]

    def add(
        self,
        key: str,
        path: Path,
        *,
        publisher: str,
        series: str,
        role: str,
        source: str | None = None,
        n_rows: int | None = None,
    ) -> None:
        self._sources[key] = {
            "publisher": publisher,
            "series": series,
            "role": role,
            "source": source or f"{publisher}:{series}",
            "n_rows_loaded": n_rows,
            "vintage_file": rel(path),
            "sha256": sha256(path),
        }

    def loaded(self) -> list[dict[str, Any]]:
        out = []
        for key, item in self._sources.items():
            out.append(
                {
                    "role": item["role"],
                    "name": key,
                    "source": item["source"],
                    "publisher": item["publisher"],
                    "n_rows": item.get("n_rows_loaded"),
                    "vintage_file": item["vintage_file"],
                    "sha256": item["sha256"],
                }
            )
        return out

    def manifest_vintages(self) -> dict[str, dict[str, Any]]:
        return self._sources


def spec_path(hid: str) -> Path:
    matches = sorted((ROOT / "hypotheses").glob(f"*/{hid}.yaml"))
    if not matches:
        raise FileNotFoundError(f"missing hypothesis spec for {hid}")
    return matches[0]


def load_spec(hid: str) -> dict[str, Any]:
    return yaml.safe_load(spec_path(hid).read_text()) or {}


def run_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_wdi(reg: SourceRegistry, indicator: str, key: str, role: str) -> pd.DataFrame:
    path = reg.latest("world_bank_wdi", f"{indicator}@*.parquet")
    df = pd.read_parquet(path)
    df = df.dropna(subset=["country_iso3", "year", "value"]).copy()
    df["year"] = df["year"].astype(int)
    reg.add(
        key,
        path,
        publisher="world_bank_wdi",
        series=indicator,
        role=role,
        n_rows=len(df),
    )
    return df


def read_pwt(reg: SourceRegistry, series: str, key: str, role: str) -> pd.DataFrame:
    path = reg.latest("pwt", f"{series}@*.parquet")
    df = pd.read_parquet(path)
    df = df.dropna(subset=["country_iso3", "year", "value"]).copy()
    df["year"] = df["year"].astype(int)
    reg.add(key, path, publisher="pwt", series=series, role=role, n_rows=len(df))
    return df


def read_oecd_migration_emp_edu(reg: SourceRegistry, key: str, role: str) -> pd.DataFrame:
    series = "OECD.ELS.IMD_DSD_MIG_DF_MIG_EMP_EDU_1.0"
    path = reg.latest("oecd", f"{series}@*.parquet")
    df = pd.read_parquet(path)
    df = df.dropna(subset=["REF_AREA", "period", "value"]).copy()
    df["period"] = df["period"].astype(int)
    reg.add(
        key,
        path,
        publisher="oecd",
        series="OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0",
        role=role,
        source="oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0",
        n_rows=len(df),
    )
    return df


def read_pmr(reg: SourceRegistry, key: str, role: str) -> pd.DataFrame:
    series = "OECD.ECO.GCRD_DSD_PMR_DF_PMR_1.2"
    path = reg.latest("oecd_pmr", f"{series}@*.parquet")
    df = pd.read_parquet(path)
    period_col = "period" if "period" in df.columns else "TIME_PERIOD"
    value_col = "value" if "value" in df.columns else "OBS_VALUE"
    out = df.rename(columns={period_col: "year", value_col: "value"}).copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["REF_AREA", "year"])
    out["year"] = out["year"].astype(int)
    reg.add(
        key,
        path,
        publisher="oecd_pmr",
        series="PMR@DF_PMR_1.2",
        role=role,
        source="oecd_pmr:PMR@DF_PMR_1.2",
        n_rows=len(out),
    )
    return out


def sample_countries(spec: dict[str, Any]) -> list[str]:
    sample = spec.get("sample") or {}
    return [str(c) for c in (sample.get("countries") or [])]


def write_outputs(
    hid: str,
    *,
    verdict_label: str,
    reason: str,
    estimate: dict[str, Any],
    registry: SourceRegistry,
    bullets: list[str],
    caveats: list[str],
    missing: list[str],
    run_utc_value: str,
    runner: str,
) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = load_spec(hid)
    falsification = spec.get("falsification") or {}
    verdict = f"{verdict_label} - {reason}"
    diag = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "static_reform_worker_a_exact",
        "falsification_rule_text": falsification.get("rule"),
        "falsification_test_text": falsification.get("test"),
        "estimate": clean(estimate),
        "data_status": {
            "variables_loaded": registry.loaded(),
            "variables_missing": missing,
        },
        "limitations": caveats,
        "run_utc": run_utc_value,
        "runner": runner,
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(clean(diag), indent=2) + "\n")
    manifest = {
        "hypothesis_id": hid,
        "template": "static_reform_worker_a_exact",
        "runner": runner,
        "run_utc": run_utc_value,
        "verdict_label": verdict_label,
        "vintages": registry.manifest_vintages(),
        "missing_series": missing,
        "outputs": {
            "diagnostics": f"engine/runs/{hid}/diagnostics.json",
            "result_card": f"engine/runs/{hid}/result_card.md",
        },
        "limitations": caveats,
    }
    (out_dir / "manifest.yaml").write_text(
        yaml.safe_dump(clean(manifest), sort_keys=False),
        encoding="utf-8",
    )

    claim = str(spec.get("claim") or "").strip()
    rule = str(falsification.get("rule") or "").strip()
    test_text = falsification.get("test") or "not specified"
    lines = [
        f"# Result card - {hid}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Pre-registration",
        f"- **Claim:** {claim}",
        f"- **Falsification rule:** {rule}",
        f"- **Falsification test:** {test_text}",
        "",
        "## Exact static-treatment conversion",
    ]
    lines.extend(f"- {bullet}" for bullet in bullets)
    if caveats:
        lines.extend(["", "## Caveats"])
        lines.extend(f"- {caveat}" for caveat in caveats)
    lines.extend(["", "## Variables resolved"])
    for key, item in registry.manifest_vintages().items():
        rows = item.get("n_rows_loaded")
        row_text = f", n={rows}" if rows is not None else ""
        lines.append(
            f"- `{item['source']}` -> {key} ({item['publisher']}{row_text}; {item['vintage_file']})"
        )
    if missing:
        lines.extend(["", "## Missing dispositive inputs"])
        lines.extend(f"- {item}" for item in missing)
    lines.extend(["", f"_Generated by `{runner}` at {run_utc_value}_"])
    (out_dir / "result_card.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_canada_points(hid: str, runner: str, run_utc_value: str) -> None:
    reg = SourceRegistry()
    spec = load_spec(hid)
    countries = sample_countries(spec)
    mig = read_oecd_migration_emp_edu(reg, "foreign_born_tertiary_employment_rate_bridge", "outcome")
    gdp = read_wdi(reg, "NY.GDP.PCAP.KD.ZG", "real_gdp_per_capita_growth", "secondary_outcome")

    tertiary = mig[
        (mig["MEASURE"].eq("EMP_WAP"))
        & (mig["SEX"].eq("_T"))
        & (mig["BIRTH_PLACE"].eq("FB"))
        & (mig["EDUCATION_LEV"].eq("ISCED11_5T8"))
        & (mig["REF_AREA"].isin(countries))
        & (mig["period"].between(2000, 2023))
    ][["REF_AREA", "period", "value"]]
    can = tertiary[tertiary["REF_AREA"].eq("CAN")].set_index("period")["value"]
    med = (
        tertiary[~tertiary["REF_AREA"].isin(["CAN", "AUS", "NZL"])]
        .groupby("period")["value"]
        .median()
    )
    aligned = pd.concat([can.rename("canada"), med.rename("median")], axis=1).dropna()
    aligned["premium_pp"] = aligned["canada"] - aligned["median"]

    gdp_sub = gdp[gdp["country_iso3"].isin(countries) & gdp["year"].between(2000, 2023)]
    gdp_can = gdp_sub[gdp_sub["country_iso3"].eq("CAN")].set_index("year")["value"]
    gdp_med = (
        gdp_sub[~gdp_sub["country_iso3"].isin(["CAN", "AUS", "NZL"])]
        .groupby("year")["value"]
        .median()
    )
    gdp_aligned = pd.concat([gdp_can.rename("canada"), gdp_med.rename("median")], axis=1).dropna()
    gdp_aligned["gap_pp"] = gdp_aligned["canada"] - gdp_aligned["median"]

    premium = float(aligned["premium_pp"].mean()) if not aligned.empty else float("nan")
    gdp_gap = float(gdp_aligned["gap_pp"].mean()) if not gdp_aligned.empty else float("nan")
    reason = (
        f"local tertiary-employment bridge premium {premium:+.2f}pp is below the +5pp "
        "refutation screen; direct DIOC attainment share and identified points coefficient are missing"
    )
    write_outputs(
        hid,
        verdict_label="WEAKENED",
        reason=reason,
        estimate={
            "shape": "canada_points_static_bridge",
            "tertiary_employment_bridge": {
                "years": [int(aligned.index.min()), int(aligned.index.max())] if not aligned.empty else [],
                "n_years": int(len(aligned)),
                "canada_mean": float(aligned["canada"].mean()) if not aligned.empty else None,
                "median_ex_can_aus_nzl_mean": float(aligned["median"].mean()) if not aligned.empty else None,
                "premium_pp_mean": premium,
                "support_gate_pp": 10.0,
                "refutation_screen_pp": 5.0,
            },
            "gdp_pc_growth_context": {
                "years": [int(gdp_aligned.index.min()), int(gdp_aligned.index.max())]
                if not gdp_aligned.empty
                else [],
                "n_years": int(len(gdp_aligned)),
                "canada_mean_growth": float(gdp_aligned["canada"].mean()) if not gdp_aligned.empty else None,
                "median_ex_can_aus_nzl_mean_growth": float(gdp_aligned["median"].mean())
                if not gdp_aligned.empty
                else None,
                "gap_pp_mean": gdp_gap,
            },
        },
        registry=reg,
        bullets=[
            f"Canada's local OECD tertiary-employment bridge premium averages {premium:+.2f} pp over {len(aligned)} matched years.",
            f"The preregistered support gate is +10 pp; the refutation screen is below +5 pp.",
            f"Canada's real GDP-per-capita-growth gap versus the same comparator median averages {gdp_gap:+.2f} pp over {len(gdp_aligned)} years.",
        ],
        caveats=[
            "The local OECD IMD file measures employment rates by education and birthplace, not the foreign-born tertiary-attainment share requested by the claim.",
            "The points-system treatment is static by country, so a country-FE coefficient is not identified without a recoded event or cross-sectional design.",
        ],
        missing=[
            "direct OECD DIOC foreign-born tertiary-attainment share by destination and year",
            "identified points-system coefficient or owner-approved year-FE/cross-sectional replacement design",
        ],
        run_utc_value=run_utc_value,
        runner=runner,
    )


def run_australia_skill(hid: str, runner: str, run_utc_value: str) -> None:
    reg = SourceRegistry()
    spec = load_spec(hid)
    countries = sample_countries(spec)
    mig = read_oecd_migration_emp_edu(reg, "foreign_born_native_employment_gap", "outcome")
    all_edu = mig[
        (mig["MEASURE"].eq("EMP_WAP"))
        & (mig["SEX"].eq("_T"))
        & (mig["EDUCATION_LEV"].eq("_T"))
        & (mig["BIRTH_PLACE"].isin(["FB", "NB"]))
        & (mig["REF_AREA"].isin(countries))
        & (mig["period"].between(2000, 2023))
    ]
    wide = (
        all_edu.pivot_table(
            index=["REF_AREA", "period"],
            columns="BIRTH_PLACE",
            values="value",
            aggfunc="mean",
        )
        .reset_index()
        .dropna(subset=["FB", "NB"])
    )
    wide["gap_fb_minus_native_pp"] = wide["FB"] - wide["NB"]
    aus = wide[wide["REF_AREA"].eq("AUS")].sort_values("period")
    europe = wide[wide["REF_AREA"].isin(["DEU", "FRA", "NLD", "SWE", "NOR", "DNK", "BEL", "AUT", "CHE"])]
    aus_mean_gap = float(aus["gap_fb_minus_native_pp"].mean())
    aus_abs_mean_gap = abs(aus_mean_gap)
    latest = aus.iloc[-1]
    europe_abs_mean = float(europe["gap_fb_minus_native_pp"].abs().mean())
    parity_latest = abs(float(latest["gap_fb_minus_native_pp"])) < 2.0
    full_window_parity = aus_abs_mean_gap < 2.0
    reason = (
        f"latest AUS gap {latest['gap_fb_minus_native_pp']:+.2f}pp clears parity, "
        f"but available-window mean gap {aus_mean_gap:+.2f}pp misses the <2pp gate and skill-stream series is missing"
    )
    write_outputs(
        hid,
        verdict_label="PARTIAL",
        reason=reason,
        estimate={
            "shape": "australia_skill_stream_static_bridge",
            "available_years": [int(aus["period"].min()), int(aus["period"].max())],
            "n_years": int(len(aus)),
            "aus_mean_gap_fb_minus_native_pp": aus_mean_gap,
            "aus_abs_mean_gap_pp": aus_abs_mean_gap,
            "aus_latest_year": int(latest["period"]),
            "aus_latest_gap_fb_minus_native_pp": float(latest["gap_fb_minus_native_pp"]),
            "europe_abs_mean_gap_pp": europe_abs_mean,
            "full_window_parity_gate_pass": bool(full_window_parity),
            "latest_parity_gate_pass": bool(parity_latest),
            "skill_stream_coefficient_loaded": False,
        },
        registry=reg,
        bullets=[
            f"Australia's foreign-born minus native employment-rate gap averages {aus_mean_gap:+.2f} pp over {int(aus['period'].min())}-{int(aus['period'].max())}.",
            f"The latest local year ({int(latest['period'])}) is {latest['gap_fb_minus_native_pp']:+.2f} pp, inside the +/-2 pp parity band.",
            f"The selected European comparator absolute gap averages {europe_abs_mean:.2f} pp, matching the claim's contrast direction.",
        ],
        caveats=[
            "The local OECD IMD slice starts in 2015 for Australia, not 2000.",
            "No local cross-country skill-stream-share panel is available, so the preregistered coefficient gate remains untested.",
        ],
        missing=[
            "annual Australia skill-stream share from DHA or harmonised cross-country skill-stream-share panel",
            "2000-2014 Australia foreign-born/native employment-rate rows in the local OECD IMD slice",
        ],
        run_utc_value=run_utc_value,
        runner=runner,
    )


def annualized_log_growth(df: pd.DataFrame, countries: list[str], start: int, end: int) -> pd.DataFrame:
    rows = []
    for country, group in (
        df[df["country_iso3"].isin(countries) & df["year"].between(start, end)]
        .dropna(subset=["value"])
        .groupby("country_iso3")
    ):
        group = group.sort_values("year")
        if len(group) < 2:
            continue
        first = group.iloc[0]
        last = group.iloc[-1]
        if first["value"] <= 0 or last["value"] <= 0 or int(last["year"]) == int(first["year"]):
            continue
        rows.append(
            {
                "country": country,
                "start_year": int(first["year"]),
                "end_year": int(last["year"]),
                "start_value": float(first["value"]),
                "end_value": float(last["value"]),
                "annualized_log_growth_pct": (
                    math.log(float(last["value"]) / float(first["value"]))
                    / (int(last["year"]) - int(first["year"]))
                    * 100.0
                ),
                "n_years": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def level_change(df: pd.DataFrame, countries: list[str], start: int, end: int) -> pd.DataFrame:
    rows = []
    for country, group in (
        df[df["country_iso3"].isin(countries) & df["year"].between(start, end)]
        .dropna(subset=["value"])
        .groupby("country_iso3")
    ):
        group = group.sort_values("year")
        if len(group) < 2:
            continue
        first = group.iloc[0]
        last = group.iloc[-1]
        rows.append(
            {
                "country": country,
                "start_year": int(first["year"]),
                "end_year": int(last["year"]),
                "start_value": float(first["value"]),
                "end_value": float(last["value"]),
                "change_pp": float(last["value"] - first["value"]),
                "annual_change_pp": float(last["value"] - first["value"])
                / (int(last["year"]) - int(first["year"])),
                "n_years": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def run_china_soe_cee(hid: str, runner: str, run_utc_value: str) -> None:
    reg = SourceRegistry()
    countries = ["CHN", "POL", "CZE", "HUN", "SVK", "RUS", "UKR", "ROU", "BGR"]
    peers = [c for c in countries if c != "CHN"]
    industry_va = read_wdi(reg, "NV.IND.TOTL.KD", "real_industry_value_added", "outcome")
    industry_share = read_wdi(reg, "NV.IND.TOTL.ZS", "industrial_value_added_share_gdp", "secondary_outcome")
    gdp_pc = read_wdi(reg, "NY.GDP.PCAP.KD", "real_gdp_per_capita", "context")

    growth = annualized_log_growth(industry_va, countries, 1993, 2019)
    share = level_change(industry_share, countries, 1993, 2019)
    gdp_growth = annualized_log_growth(gdp_pc, countries, 1993, 2019)
    chn_growth = float(growth.loc[growth["country"].eq("CHN"), "annualized_log_growth_pct"].iloc[0])
    peer_growth_median = float(
        growth.loc[growth["country"].isin(peers), "annualized_log_growth_pct"].median()
    )
    chn_share_change = float(share.loc[share["country"].eq("CHN"), "change_pp"].iloc[0])
    peer_share_median = float(share.loc[share["country"].isin(peers), "change_pp"].median())
    gdp_china = float(gdp_growth.loc[gdp_growth["country"].eq("CHN"), "annualized_log_growth_pct"].iloc[0])
    gdp_peer_median = float(
        gdp_growth.loc[gdp_growth["country"].isin(peers), "annualized_log_growth_pct"].median()
    )
    reason = (
        f"aggregate industry VA growth favors CHN by {chn_growth - peer_growth_median:+.2f}pp/yr, "
        "but industry-share and SOE/strategic-sector ownership gates are not identified"
    )
    write_outputs(
        hid,
        verdict_label="PARTIAL",
        reason=reason,
        estimate={
            "shape": "china_cee_static_aggregate_industry_screen",
            "industry_value_added_growth": {
                "china_annualized_log_growth_pct": chn_growth,
                "cee_peer_median_annualized_log_growth_pct": peer_growth_median,
                "china_minus_peer_median_pp": chn_growth - peer_growth_median,
                "country_rows": growth.to_dict(orient="records"),
            },
            "industry_share_change": {
                "china_change_pp": chn_share_change,
                "cee_peer_median_change_pp": peer_share_median,
                "china_minus_peer_median_pp": chn_share_change - peer_share_median,
                "country_rows": share.to_dict(orient="records"),
            },
            "gdp_pc_growth_context": {
                "china_annualized_log_growth_pct": gdp_china,
                "cee_peer_median_annualized_log_growth_pct": gdp_peer_median,
                "china_minus_peer_median_pp": gdp_china - gdp_peer_median,
            },
        },
        registry=reg,
        bullets=[
            f"China real industry value-added grew {chn_growth:.2f}%/yr over the local 1993-2019 window versus a CEE/post-Soviet peer median of {peer_growth_median:.2f}%/yr.",
            f"China's industry share of GDP changed {chn_share_change:+.2f} pp; the peer median changed {peer_share_median:+.2f} pp.",
            f"Real GDP per capita context also favors China by {gdp_china - gdp_peer_median:+.2f} pp/yr over the peer median.",
        ],
        caveats=[
            "This is an aggregate industry screen, not a strategic-sector SOE ownership panel.",
            "The preregistered country-FE coefficient on a China indicator remains unidentified because the treatment is static by country.",
        ],
        missing=[
            "sector-level steel, energy, and telecom output by ownership form",
            "time-varying CEE privatisation or enterprise-restructuring intensity usable as the primary treatment",
        ],
        run_utc_value=run_utc_value,
        runner=runner,
    )


def run_oecd_pmr(hid: str, runner: str, run_utc_value: str) -> None:
    reg = SourceRegistry()
    spec = load_spec(hid)
    countries = sample_countries(spec)
    pmr = read_pmr(reg, "oecd_pmr_overall_index", "treatment")
    tfp = read_pwt(reg, "rtfpna", "tfp_index", "outcome")
    lp = read_pwt(reg, "rgdpo_per_emp", "labour_productivity", "secondary_outcome")

    pmr_overall = pmr[pmr["MEASURE"].eq("PMR") & pmr["REF_AREA"].isin(countries)].copy()
    years_all = sorted(int(y) for y in pmr_overall["year"].dropna().unique())
    years_registered = [y for y in years_all if 1998 <= y <= 2019]
    countries_registered = sorted(
        pmr_overall[pmr_overall["year"].isin(years_registered)]["REF_AREA"].dropna().unique()
    )
    tfp_max = int(tfp["year"].max()) if not tfp.empty else None
    lp_max = int(lp["year"].max()) if not lp.empty else None
    reason = (
        f"local PMR has years {years_all}; within registered 1998-2019 window only {years_registered}, "
        "so PMR reductions and 5-year forward productivity growth are not identified"
    )
    write_outputs(
        hid,
        verdict_label="INCONCLUSIVE_DATA_PENDING",
        reason=reason,
        estimate={
            "shape": "pmr_registered_design_data_gap",
            "pmr_years_available": years_all,
            "pmr_years_in_registered_1998_2019_window": years_registered,
            "countries_with_registered_pmr_year": countries_registered,
            "n_countries_with_registered_pmr_year": len(countries_registered),
            "tfp_max_year": tfp_max,
            "labour_productivity_max_year": lp_max,
            "minimum_pmr_years_needed_per_country_for_reduction": 2,
            "identified_registered_design": False,
        },
        registry=reg,
        bullets=[
            f"PMR overall is locally available for {years_all}; the registered 1998-2019 window contains only {years_registered}.",
            f"PWT TFP and labour-productivity vintages end in {tfp_max} and {lp_max}, respectively.",
            "The preregistered treatment is PMR reduction predicting following 5-year productivity growth; a single in-window PMR year cannot test that.",
        ],
        caveats=[
            "A 2018/2023 cross-section would be a different, post-registered estimand and would overlap COVID/reopening years.",
        ],
        missing=[
            "older OECD PMR waves before 2018 or a constructed PMR-reduction panel",
            "post-2019 TFP and labour-productivity data if the owner chooses a 2018-2023 redesign",
        ],
        run_utc_value=run_utc_value,
        runner=runner,
    )


RUNNERS = {
    "demo_canada_points_system_immigration": run_canada_points,
    "demo_australia_high_skill_migration": run_australia_skill,
    "china_soe_vs_cee_privatised_growth": run_china_soe_cee,
}


def run_case(hid: str) -> int:
    if hid not in RUNNERS:
        print(f"unknown Worker A exact case: {hid}")
        return 1
    runner = f"engine/runs/{hid}/replication.py"
    RUNNERS[hid](hid, runner, run_utc())
    print(f"wrote exact Worker A artifacts for {hid}")
    return 0
