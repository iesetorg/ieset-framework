#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd
import pyarrow.parquet as pq
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OWID = REPO_ROOT / "data" / "vintages" / "owid"
ENERGY_DIR = REPO_ROOT / "hypotheses" / "energy"
STEELMAN_DIR = REPO_ROOT / "hypotheses" / "steelman"
RUNS_DIR = REPO_ROOT / "engine" / "runs"


@dataclass(frozen=True)
class WaveSpec:
    hypothesis_id: str
    title: str
    claim: str
    period: tuple[int, int]
    outcome: list[dict]
    treatment: list[dict]
    rule: str
    test: str
    threshold: str
    prior_confidence: float
    disclosure: str
    treatment_tags: list[str]
    steelman: str
    run_kind: str


def latest(series: str) -> Path:
    files = sorted(OWID.glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing owid:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_series(series: str, value_name: str | None = None) -> pd.DataFrame:
    path = latest(series)
    df = pq.read_table(path).to_pandas()
    meta = {"country_name", "country_iso3", "year"}
    value_cols = [c for c in df.columns if c not in meta]
    if value_name is None:
        value_name = series
    if len(value_cols) != 1:
        raise ValueError(f"{series}: expected one value column, got {value_cols}")
    df = df.rename(columns={value_cols[0]: value_name})
    df = df[df["country_iso3"].notna()].copy()
    df["country_iso3"] = df["country_iso3"].astype(str)
    df = df[df["country_iso3"].str.match(r"^[A-Z]{3}$")].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df[value_name] = pd.to_numeric(df[value_name], errors="coerce")
    return df.dropna(subset=["year", value_name])


def load_source_mix() -> pd.DataFrame:
    df = pq.read_table(latest("share-elec-by-source")).to_pandas()
    df = df[df["country_iso3"].notna()].copy()
    df["country_iso3"] = df["country_iso3"].astype(str)
    df = df[df["country_iso3"].str.match(r"^[A-Z]{3}$")].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    for c in ["Coal", "Gas", "Oil", "Wind", "Solar", "Hydropower", "Nuclear", "Other renewables", "Bioenergy"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["year"])


def endpoint_rows(
    panel: pd.DataFrame,
    value_fn: Callable[[pd.Series, pd.Series], dict],
    period: tuple[int, int],
    min_years: int,
    selector: Callable[[dict], bool],
) -> pd.DataFrame:
    rows = []
    y0, y1 = period
    for iso3, g in panel[panel["year"].between(y0, y1)].groupby("country_iso3"):
        g = g.sort_values("year")
        if len(g) < min_years:
            continue
        first = g.iloc[0]
        last = g.iloc[-1]
        row = {
            "country_iso3": iso3,
            "country_name": str(first["country_name"]),
            "start_year": int(first["year"]),
            "end_year": int(last["year"]),
        }
        row.update(value_fn(first, last))
        if selector(row):
            rows.append(row)
    return pd.DataFrame(rows).sort_values("country_iso3").reset_index(drop=True)


def verdict_from(rows: pd.DataFrame, kind: str) -> tuple[str, str, dict]:
    n = len(rows)
    pass_rate = float(rows["passes"].mean()) if n else 0.0
    metrics: dict[str, float | int] = {"n_countries": n, "pass_rate": pass_rate}

    if kind == "renewable_fossil":
        median = float(rows["fossil_change_pp"].median()) if n else 0.0
        metrics["median_fossil_change_pp"] = median
        if n >= 20 and pass_rate >= 0.70 and median <= -15.0:
            verdict = "supported"
        elif pass_rate < 0.50 or median >= -5.0:
            verdict = "refuted"
        else:
            verdict = "partial"
        reason = (
            f"{int(rows['passes'].sum())} of {n} countries passed; "
            f"median fossil electricity share change {median:.1f}pp"
        )
    elif kind == "wind_solar_coal":
        median = float(rows["coal_change_pp"].median()) if n else 0.0
        metrics["median_coal_change_pp"] = median
        if n >= 20 and pass_rate >= 0.60 and median <= -10.0:
            verdict = "supported"
        elif pass_rate < 0.40 or median >= 0.0:
            verdict = "refuted"
        else:
            verdict = "partial"
        reason = (
            f"{int(rows['passes'].sum())} of {n} wind/solar-growth countries passed; "
            f"median coal share change {median:.1f}pp"
        )
    elif kind == "electric_total_renewables":
        median = float(rows["total_renewable_energy_change_pp"].median()) if n else 0.0
        metrics["median_total_renewable_energy_change_pp"] = median
        if n >= 15 and pass_rate >= 0.80 and median >= 8.0:
            verdict = "supported"
        elif pass_rate < 0.60 or median < 3.0:
            verdict = "refuted"
        else:
            verdict = "partial"
        reason = (
            f"{int(rows['passes'].sum())} of {n} electricity-renewables-growth countries passed; "
            f"median total energy renewable-share change {median:.1f}pp"
        )
    elif kind == "g20_co2_intensity":
        median = float(rows["co2_intensity_pct_change"].median()) if n else 0.0
        metrics["median_co2_intensity_pct_change"] = median
        if n >= 18 and pass_rate >= 0.75 and median <= -35.0:
            verdict = "supported"
        elif pass_rate < 0.50 or median > -15.0:
            verdict = "refuted"
        else:
            verdict = "partial"
        reason = (
            f"{int(rows['passes'].sum())} of {n} G20 economies passed; "
            f"median CO2 intensity change {median:.1f}%"
        )
    elif kind == "high_income_co2_pc":
        median = float(rows["co2_per_capita_pct_change"].median()) if n else 0.0
        metrics["median_co2_per_capita_pct_change"] = median
        if n >= 18 and pass_rate >= 0.75 and median <= -25.0:
            verdict = "supported"
        elif pass_rate < 0.50 or median > -10.0:
            verdict = "refuted"
        else:
            verdict = "partial"
        reason = (
            f"{int(rows['passes'].sum())} of {n} high-income economies passed; "
            f"median per-capita CO2 change {median:.1f}%"
        )
    else:
        raise ValueError(kind)
    return verdict, reason, metrics


def write_yaml(spec: WaveSpec, rows: pd.DataFrame) -> None:
    countries = sorted(rows["country_iso3"].unique().tolist())
    doc = {
        "hypothesis_id": spec.hypothesis_id,
        "version": 1,
        "status": "pre_registered",
        "topic": "energy",
        "claim": spec.claim,
        "evidence_type": "descriptive",
        "sample": {
            "countries": countries,
            "period": list(spec.period),
            "temporal_structure": "panel",
        },
        "variables": {
            "outcome": spec.outcome,
            "treatment": spec.treatment,
        },
        "estimator": {
            "template": "descriptive",
            "clustering": "none",
            "notes": (
                "Custom OWID endpoint-panel replication using local vintages on disk. "
                "Countries are selected by the predeclared treatment-threshold rule, "
                "then graded against endpoint change thresholds."
            ),
        },
        "falsification": {
            "rule": spec.rule,
            "test": spec.test,
            "threshold": spec.threshold,
        },
        "prior_confidence": spec.prior_confidence,
        "disclosure": spec.disclosure,
        "steelman": f"hypotheses/steelman/{spec.hypothesis_id}.md",
        "scope": {
            "period": list(spec.period),
            "countries": countries,
            "outcome_dim": ["energy"],
            "policy_family": ["energy_policy"],
            "treatment_tags": spec.treatment_tags,
        },
    }
    text = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
    text += yaml.safe_dump(doc, sort_keys=False, width=88)
    (ENERGY_DIR / f"{spec.hypothesis_id}.yaml").write_text(text)


def write_steelman(spec: WaveSpec) -> None:
    (STEELMAN_DIR / f"{spec.hypothesis_id}.md").write_text(
        f"# Steelman: {spec.title}\n\n{spec.steelman}\n"
    )


def write_run(spec: WaveSpec, rows: pd.DataFrame, sources: list[str]) -> None:
    out = RUNS_DIR / spec.hypothesis_id
    out.mkdir(parents=True, exist_ok=True)
    verdict, reason, metrics = verdict_from(rows, spec.run_kind)

    rows.to_parquet(out / "coefficients.parquet", index=False)
    (out / "diagnostics.json").write_text(
        json.dumps(
            {
                "hypothesis_id": spec.hypothesis_id,
                "verdict": verdict,
                "reason": reason,
                "threshold": spec.threshold,
                "metrics": metrics,
                "countries": rows.to_dict(orient="records"),
                "vintages": {s: str(latest(s).relative_to(REPO_ROOT)) for s in sources},
                "sha256": {s: sha256(latest(s)) for s in sources},
            },
            indent=2,
        )
        + "\n"
    )
    (out / "manifest.yaml").write_text(
        f"hypothesis_id: {spec.hypothesis_id}\n"
        f"status: {verdict}\n"
        f"reason: {reason}\n"
        "vintages:\n"
        + "".join(f"  {s}: {latest(s).relative_to(REPO_ROOT)}\n" for s in sources)
    )

    numeric_cols = [
        c for c in rows.columns
        if c not in {"country_iso3", "country_name", "passes"}
        and pd.api.types.is_numeric_dtype(rows[c])
    ]
    chart = {
        "chart_id": f"{spec.hypothesis_id}/country_endpoints",
        "title": spec.title,
        "type": "scatter",
        "x_axis": {"label": numeric_cols[2] if len(numeric_cols) > 2 else numeric_cols[0]},
        "y_axis": {"label": numeric_cols[-2] if len(numeric_cols) > 3 else numeric_cols[-1]},
        "series": rows.to_dict(orient="records"),
        "sources": [f"owid:{s}" for s in sources],
        "permalink": f"/h/{spec.hypothesis_id}",
    }
    (out / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    metric_lines = "\n".join(f"- {k}: {v}" for k, v in metrics.items())
    table_cols = [c for c in rows.columns if c not in {"passes"}]
    header = "| " + " | ".join(table_cols + ["pass"]) + " |"
    sep = "|" + "|".join(["---"] * (len(table_cols) + 1)) + "|"
    body = "\n".join(
        "| "
        + " | ".join(
            [
                f"{r[c]:.2f}" if isinstance(r[c], float) else str(r[c])
                for c in table_cols
            ]
            + ["yes" if bool(r["passes"]) else "no"]
        )
        + " |"
        for _, r in rows.iterrows()
    )
    card = f"""# Result card - {spec.hypothesis_id}

**Verdict:** {verdict} - {reason}

## Predeclared Threshold

{spec.rule}

Threshold expression: `{spec.threshold}`

## Metrics

{metric_lines}

## Country Endpoints

{header}
{sep}
{body}

## Interpretation

This is a descriptive endpoint-panel test using local OWID vintages. It grades the
predeclared pattern only; it does not identify a policy-level causal effect.
"""
    (out / "result_card.md").write_text(card)

    replication = f'''#!/usr/bin/env python3
"""Regenerate this OWID energy wave run artifact.

This run is generated by scripts/generate_owid_energy_wave.py so the replication
logic stays shared across the small OWID wave while artifacts remain per-run.
"""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[3]
runpy.run_path(str(root / "scripts" / "generate_owid_energy_wave.py"), run_name="__main__")
'''
    (out / "replication.py").write_text(replication)


def build_specs() -> list[tuple[WaveSpec, pd.DataFrame, list[str]]]:
    ren = load_series("share-electricity-renewables", "renewable_electricity_share")
    fossil = load_series("share-electricity-fossil-fuels", "fossil_electricity_share")
    total_ren = load_series("renewable-share-energy", "renewable_energy_share")
    co2_int = load_series("co2-intensity", "co2_intensity")
    co2_pc = load_series("co2-emissions-per-capita", "co2_per_capita")
    by_source = load_source_mix()

    specs: list[tuple[WaveSpec, pd.DataFrame, list[str]]] = []

    h1_panel = ren.merge(fossil, on=["country_iso3", "country_name", "year"], how="inner")
    h1_rows = endpoint_rows(
        h1_panel,
        lambda f, l: {
            "renewable_electricity_change_pp": float(l["renewable_electricity_share"] - f["renewable_electricity_share"]),
            "fossil_change_pp": float(l["fossil_electricity_share"] - f["fossil_electricity_share"]),
            "passes": bool((l["fossil_electricity_share"] - f["fossil_electricity_share"]) <= -10.0),
        },
        (2000, 2024),
        15,
        lambda r: r["renewable_electricity_change_pp"] >= 15.0,
    )
    specs.append((
        WaveSpec(
            "owid_renewable_electricity_fossil_displacement_2000_2024",
            "Renewable electricity growth and fossil electricity displacement, 2000-2024",
            "Among countries where renewable electricity share rose by at least 15 percentage points between 2000 and 2024, fossil-fuel electricity share usually fell materially: at least 70% should show a fossil-share decline of at least 10 percentage points, and the median fossil-share change should be at most -15 percentage points.",
            (2000, 2024),
            [{"name": "fossil_electricity_share", "source": "owid:share-electricity-fossil-fuels", "transformation": "endpoint percentage-point change"}],
            [{"name": "renewable_electricity_share", "source": "owid:share-electricity-renewables", "transformation": "countries selected if endpoint increase >= 15pp"}],
            "SUPPORTED if at least 70% of selected countries have fossil-electricity-share declines of at least 10pp and the median fossil-share change is <= -15pp. REFUTED if fewer than 50% pass or the median decline is less than 5pp. Otherwise PARTIAL.",
            "renewable_electricity_growth_fossil_share_endpoint_change",
            "n >= 20 AND pass_rate >= 0.70 AND median_fossil_change_pp <= -15",
            0.82,
            "The prior expects a strong accounting substitution pattern because electricity shares sum to 100, but hydro variability, nuclear retirements, imports, and demand growth can weaken causal interpretation.",
            ["renewable_electricity", "fossil_electricity_displacement"],
            "A decline in fossil electricity share is partly mechanical when renewable share rises, so this test should not be read as proof that policy caused absolute fossil generation or emissions to fall. Some countries may add renewables while total demand rises, while others may substitute away from nuclear or hydro rather than fossil fuels. Endpoint comparisons also ignore weather cycles, imports, and economic shocks.",
            "renewable_fossil",
        ),
        h1_rows,
        ["share-electricity-renewables", "share-electricity-fossil-fuels"],
    ))

    h2_rows = endpoint_rows(
        by_source.dropna(subset=["Wind", "Solar", "Coal", "Gas", "Oil"]),
        lambda f, l: {
            "wind_solar_change_pp": float((l["Wind"] + l["Solar"]) - (f["Wind"] + f["Solar"])),
            "coal_change_pp": float(l["Coal"] - f["Coal"]),
            "fossil_change_pp": float((l["Coal"] + l["Gas"] + l["Oil"]) - (f["Coal"] + f["Gas"] + f["Oil"])),
            "passes": bool((l["Coal"] - f["Coal"]) <= -5.0),
        },
        (2000, 2024),
        15,
        lambda r: r["wind_solar_change_pp"] >= 10.0,
    )
    specs.append((
        WaveSpec(
            "owid_wind_solar_coal_displacement_2000_2024",
            "Wind and solar growth and coal electricity displacement, 2000-2024",
            "Among countries where wind plus solar electricity share rose by at least 10 percentage points from 2000 to 2024, coal's electricity share should usually fall: at least 60% of selected countries should show a coal-share decline of at least 5 percentage points, with median coal-share change at most -10 percentage points.",
            (2000, 2024),
            [{"name": "coal_electricity_share", "source": "owid:share-elec-by-source", "transformation": "endpoint percentage-point change in Coal column"}],
            [{"name": "wind_plus_solar_share", "source": "owid:share-elec-by-source", "transformation": "countries selected if Wind + Solar endpoint increase >= 10pp"}],
            "SUPPORTED if at least 60% of selected countries have coal-share declines of at least 5pp and the median coal-share change is <= -10pp. REFUTED if fewer than 40% pass or median coal-share change is non-negative. Otherwise PARTIAL.",
            "wind_solar_growth_coal_share_endpoint_change",
            "n >= 20 AND pass_rate >= 0.60 AND median_coal_change_pp <= -10",
            0.58,
            "The prior expects many wind/solar additions to displace coal, but gas, hydro, oil-heavy island grids, and demand growth can absorb renewable gains instead.",
            ["wind_solar_electricity", "coal_displacement"],
            "Wind and solar growth does not have to displace coal specifically. In coal-light systems it can displace oil or gas, in hydro systems it may mostly diversify supply, and in fast-growing systems it can meet incremental demand while coal remains flat or rises. A coal-share endpoint test is therefore a demanding version of the transition claim.",
            "wind_solar_coal",
        ),
        h2_rows,
        ["share-elec-by-source"],
    ))

    h3_panel = ren.merge(total_ren, on=["country_iso3", "country_name", "year"], how="inner")
    h3_rows = endpoint_rows(
        h3_panel,
        lambda f, l: {
            "renewable_electricity_change_pp": float(l["renewable_electricity_share"] - f["renewable_electricity_share"]),
            "total_renewable_energy_change_pp": float(l["renewable_energy_share"] - f["renewable_energy_share"]),
            "passes": bool((l["renewable_energy_share"] - f["renewable_energy_share"]) >= 5.0),
        },
        (2000, 2023),
        15,
        lambda r: r["renewable_electricity_change_pp"] >= 20.0,
    )
    specs.append((
        WaveSpec(
            "owid_electric_renewables_total_energy_followthrough_2000_2023",
            "Electric renewable growth and total-energy renewable follow-through, 2000-2023",
            "Countries with very large renewable-electricity gains should also show visible economy-wide energy transition: among countries where renewable electricity share rose by at least 20 percentage points from 2000 to 2023, at least 80% should increase renewables' share of total energy by at least 5 percentage points, and the median total-energy renewable-share gain should be at least 8 percentage points.",
            (2000, 2023),
            [{"name": "renewable_share_total_energy", "source": "owid:renewable-share-energy", "transformation": "endpoint percentage-point change"}],
            [{"name": "renewable_electricity_share", "source": "owid:share-electricity-renewables", "transformation": "countries selected if endpoint increase >= 20pp"}],
            "SUPPORTED if at least 80% of selected countries have total-energy renewable-share gains >= 5pp and the median total-energy gain is >= 8pp. REFUTED if fewer than 60% pass or the median total-energy gain is below 3pp. Otherwise PARTIAL.",
            "electric_renewables_total_energy_endpoint_followthrough",
            "n >= 15 AND pass_rate >= 0.80 AND median_total_renewable_energy_change_pp >= 8",
            0.70,
            "The prior expects electricity transition leaders to show broader renewable energy gains, but electricity is only one slice of final energy and transport/heat can lag badly.",
            ["renewable_electricity", "total_energy_transition"],
            "Electricity-sector progress can overstate economy-wide transition. A country may decarbonize electricity while oil use in transport, gas use in heating, or industrial fuels remain largely unchanged. Conversely, total-energy renewable share can rise because of bioenergy accounting rather than wind and solar. This test is a broad follow-through screen, not a full energy-system decomposition.",
            "electric_total_renewables",
        ),
        h3_rows,
        ["share-electricity-renewables", "renewable-share-energy"],
    ))

    g20 = ["ARG", "AUS", "BRA", "CAN", "CHN", "FRA", "DEU", "IND", "IDN", "ITA", "JPN", "KOR", "MEX", "RUS", "SAU", "ZAF", "TUR", "GBR", "USA"]
    h4_panel = co2_int[co2_int["country_iso3"].isin(g20)].copy()
    h4_rows = endpoint_rows(
        h4_panel,
        lambda f, l: {
            "co2_intensity_pct_change": float((l["co2_intensity"] / f["co2_intensity"] - 1.0) * 100.0),
            "passes": bool((l["co2_intensity"] / f["co2_intensity"] - 1.0) * 100.0 <= -25.0),
        },
        (1990, 2022),
        20,
        lambda r: True,
    )
    specs.append((
        WaveSpec(
            "owid_g20_co2_intensity_decline_1990_2022",
            "G20 CO2 intensity decline, 1990-2022",
            "Most large economies should show substantial carbon-intensity improvement since 1990: among the 19 country-level G20 economies with local OWID coverage, at least 75% should reduce CO2 emissions per unit of GDP by at least 25% by 2022, and the median decline should be at least 35%.",
            (1990, 2022),
            [{"name": "co2_intensity", "source": "owid:co2-intensity", "transformation": "endpoint percent change"}],
            [{"name": "g20_country_panel", "source": "fixed country list", "transformation": "19 country-level G20 economies"}],
            "SUPPORTED if at least 75% of the G20 country panel reduces CO2 intensity by >=25% and the median decline is >=35%. REFUTED if fewer than 50% pass or the median decline is less than 15%. Otherwise PARTIAL.",
            "g20_co2_intensity_endpoint_percent_change",
            "n >= 18 AND pass_rate >= 0.75 AND median_co2_intensity_pct_change <= -35",
            0.86,
            "The prior expects broad energy efficiency and structural-change gains, but CO2/GDP can improve while absolute emissions keep rising.",
            ["carbon_intensity", "energy_efficiency", "structural_change"],
            "CO2 intensity of GDP is not the same as absolute decarbonization. A country can reduce emissions per dollar while total emissions rise because GDP grows faster. Exchange-rate and PPP measurement choices also affect intensity. This test should be interpreted as evidence on relative carbon productivity, not on whether economies are on a 1.5C-compatible absolute emissions path.",
            "g20_co2_intensity",
        ),
        h4_rows,
        ["co2-intensity"],
    ))

    high_income = ["USA", "CAN", "AUS", "JPN", "KOR", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "SWE", "NOR", "DNK", "FIN", "AUT", "CHE", "IRL", "NZL"]
    h5_panel = co2_pc[co2_pc["country_iso3"].isin(high_income)].copy()
    h5_rows = endpoint_rows(
        h5_panel,
        lambda f, l: {
            "co2_per_capita_pct_change": float((l["co2_per_capita"] / f["co2_per_capita"] - 1.0) * 100.0),
            "passes": bool((l["co2_per_capita"] / f["co2_per_capita"] - 1.0) * 100.0 <= -15.0),
        },
        (2005, 2023),
        15,
        lambda r: True,
    )
    specs.append((
        WaveSpec(
            "owid_high_income_co2_per_capita_decline_2005_2023",
            "High-income per-capita CO2 decline, 2005-2023",
            "Among a fixed panel of 20 high-income economies, per-capita CO2 emissions should mostly fall after the mid-2000s energy-transition inflection: at least 75% should reduce per-capita CO2 by at least 15% from 2005 to 2023, and the median reduction should be at least 25%.",
            (2005, 2023),
            [{"name": "co2_emissions_per_capita", "source": "owid:co2-emissions-per-capita", "transformation": "endpoint percent change"}],
            [{"name": "high_income_country_panel", "source": "fixed country list", "transformation": "20 high-income economies"}],
            "SUPPORTED if at least 75% of the high-income panel reduces per-capita CO2 by >=15% and the median decline is >=25%. REFUTED if fewer than 50% pass or median decline is less than 10%. Otherwise PARTIAL.",
            "high_income_co2_per_capita_endpoint_percent_change",
            "n >= 18 AND pass_rate >= 0.75 AND median_co2_per_capita_pct_change <= -25",
            0.84,
            "The prior expects post-2005 high-income decarbonization, but territorial per-capita emissions omit imported consumption emissions and can be flattered by offshoring.",
            ["per_capita_emissions", "high_income_decarbonization"],
            "Territorial per-capita CO2 declines can reflect deindustrialization, trade leakage, slower growth, weather, or fuel-price shocks rather than domestic clean-energy policy. Consumption-based emissions may fall less. This endpoint test is strongest as evidence that territorial emissions intensity of lifestyles fell, not as proof of globally net emissions cuts.",
            "high_income_co2_pc",
        ),
        h5_rows,
        ["co2-emissions-per-capita"],
    ))

    return specs


def main() -> None:
    for spec, rows, sources in build_specs():
        write_yaml(spec, rows)
        write_steelman(spec)
        write_run(spec, rows, sources)
        verdict, reason, _ = verdict_from(rows, spec.run_kind)
        print(f"{spec.hypothesis_id}: {verdict} - {reason}")


if __name__ == "__main__":
    main()
