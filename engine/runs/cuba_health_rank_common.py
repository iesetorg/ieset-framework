#!/usr/bin/env python3
"""Shared replication helpers for Cuba health rank companion specs."""
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

REPO_ROOT = Path(__file__).resolve().parents[2]
VINTAGES = REPO_ROOT / "data" / "vintages"
TREATED = "CUB"
BASELINE_YEAR = 1960
FINAL_YEAR = 2000
SOVIET_END = 1991
PALETTE = [
    "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
    "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    root = VINTAGES / pub
    files = sorted(root.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_long(path: Path, explicit_value_col: str | None = None) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    if "country_iso3" not in df.columns or "year" not in df.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns")
    value_col = explicit_value_col
    if value_col is None:
        if "value" in df.columns:
            value_col = "value"
        else:
            meta = {"country_iso3", "country_name", "year"}
            candidates = [c for c in df.columns if c not in meta and "Annotations" not in c]
            if not candidates:
                raise ValueError(f"{path}: unable to infer value column from {list(df.columns)}")
            value_col = candidates[-1]
    if value_col != "value":
        df = df.rename(columns={value_col: "value"})
    df = df[df["country_iso3"].notna()].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["year", "value"])


def country_year_value(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def build_rank_table(df: pd.DataFrame, countries: list[str], year: int, higher_is_better: bool) -> pd.DataFrame:
    sub = df[(df["country_iso3"].isin(countries)) & (df["year"] == year)][["country_iso3", "value"]].copy()
    if sub.empty:
        return pd.DataFrame(columns=["country_iso3", "value", "rank"])
    sub = sub.groupby("country_iso3", as_index=False)["value"].mean()
    sub = sub.sort_values("value", ascending=not higher_is_better, kind="mergesort").reset_index(drop=True)
    sub["rank"] = sub.index + 1
    return sub


def f(value: float | None, fmt: str) -> str:
    return "n/a" if value is None or pd.isna(value) else format(float(value), fmt)


def build_run(config: dict) -> int:
    hid = config["hid"]
    out_dir = REPO_ROOT / "engine" / "runs" / hid
    out_dir.mkdir(parents=True, exist_ok=True)

    peers = config["peers"]
    countries = [TREATED] + peers
    advanced_subgroup = config.get("advanced_subgroup")

    le_path = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    imr_path = latest("world_bank_wdi", "SP.DYN.IMRT.IN")
    gdp_path = latest(config["income_publisher"], config["income_series"])

    manifest = {
        "life_expectancy": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.LE00.IN",
            "vintage_file": str(le_path.relative_to(REPO_ROOT)),
            "sha256": sha256(le_path),
        },
        "infant_mortality": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.IMRT.IN",
            "vintage_file": str(imr_path.relative_to(REPO_ROOT)),
            "sha256": sha256(imr_path),
        },
        "income_rank_context": {
            "publisher": config["income_publisher"],
            "series": config["income_series"],
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
    }

    le = load_long(le_path)
    imr = load_long(imr_path)
    gdp = load_long(gdp_path, explicit_value_col=config.get("income_value_col"))

    le = le[(le["country_iso3"].isin(countries)) & le["year"].between(BASELINE_YEAR, FINAL_YEAR)].copy()
    imr = imr[(imr["country_iso3"].isin(countries)) & imr["year"].between(BASELINE_YEAR, FINAL_YEAR)].copy()
    gdp = gdp[(gdp["country_iso3"].isin(countries)) & gdp["year"].between(BASELINE_YEAR, FINAL_YEAR)].copy()
    le["year"] = le["year"].astype(int)
    imr["year"] = imr["year"].astype(int)
    gdp["year"] = gdp["year"].astype(int)

    le_1960 = build_rank_table(le, countries, BASELINE_YEAR, higher_is_better=True)
    le_2000 = build_rank_table(le, countries, FINAL_YEAR, higher_is_better=True)
    imr_1960 = build_rank_table(imr, countries, BASELINE_YEAR, higher_is_better=False)
    imr_2000 = build_rank_table(imr, countries, FINAL_YEAR, higher_is_better=False)
    gdp_2000 = build_rank_table(gdp, countries, FINAL_YEAR, higher_is_better=True)

    le_rank_2000 = int(le_2000.loc[le_2000["country_iso3"] == TREATED, "rank"].iloc[0]) if TREATED in set(le_2000["country_iso3"]) else None
    imr_rank_2000 = int(imr_2000.loc[imr_2000["country_iso3"] == TREATED, "rank"].iloc[0]) if TREATED in set(imr_2000["country_iso3"]) else None
    gdp_rank_2000 = int(gdp_2000.loc[gdp_2000["country_iso3"] == TREATED, "rank"].iloc[0]) if TREATED in set(gdp_2000["country_iso3"]) else None

    le_rank_1960 = int(le_1960.loc[le_1960["country_iso3"] == TREATED, "rank"].iloc[0]) if TREATED in set(le_1960["country_iso3"]) else None
    imr_rank_1960 = int(imr_1960.loc[imr_1960["country_iso3"] == TREATED, "rank"].iloc[0]) if TREATED in set(imr_1960["country_iso3"]) else None

    rank_summary = le_2000[["country_iso3", "value", "rank"]].rename(columns={"value": "life_expectancy_2000", "rank": "le_rank_2000"})
    rank_summary = rank_summary.merge(
        imr_2000[["country_iso3", "value", "rank"]].rename(columns={"value": "infant_mortality_2000", "rank": "imr_rank_2000"}),
        on="country_iso3",
        how="outer",
    )
    rank_summary = rank_summary.merge(
        gdp_2000[["country_iso3", "value", "rank"]].rename(columns={"value": "income_2000", "rank": "gdp_rank_2000"}),
        on="country_iso3",
        how="outer",
    )
    rank_summary["mean_health_rank_2000"] = (rank_summary["le_rank_2000"] + rank_summary["imr_rank_2000"]) / 2.0
    rank_summary["income_minus_health_rank"] = rank_summary["gdp_rank_2000"] - rank_summary["mean_health_rank_2000"]
    rank_summary = rank_summary.sort_values(["mean_health_rank_2000", "le_rank_2000", "country_iso3"], kind="mergesort").reset_index(drop=True)

    cuba_row = rank_summary[rank_summary["country_iso3"] == TREATED].iloc[0]
    mean_health_rank = float(cuba_row["mean_health_rank_2000"])
    income_gap = float(cuba_row["income_minus_health_rank"])

    peer_coverage = {
        "le_peers_with_data_2000": int(le_2000["country_iso3"].isin(peers).sum()),
        "imr_peers_with_data_2000": int(imr_2000["country_iso3"].isin(peers).sum()),
        "gdp_peers_with_data_2000": int(gdp_2000["country_iso3"].isin(peers).sum()),
        "n_peers_total": len(peers),
        "min_peer_coverage": config["min_peer_coverage"],
    }

    method_valid = all([
        le_rank_2000 is not None,
        imr_rank_2000 is not None,
        gdp_rank_2000 is not None,
        peer_coverage["le_peers_with_data_2000"] >= config["min_peer_coverage"],
        peer_coverage["imr_peers_with_data_2000"] >= config["min_peer_coverage"],
        peer_coverage["gdp_peers_with_data_2000"] >= config["min_peer_coverage"],
    ])

    primary1 = method_valid and le_rank_2000 <= config["le_rank_threshold"]
    primary2 = method_valid and imr_rank_2000 <= config["imr_rank_threshold"]
    primary3 = method_valid and income_gap >= config["income_gap_threshold"]
    primary_hits = int(primary1) + int(primary2) + int(primary3)

    le_1991 = country_year_value(le, TREATED, SOVIET_END)
    le_2000_value = country_year_value(le, TREATED, FINAL_YEAR)
    imr_1991 = country_year_value(imr, TREATED, SOVIET_END)
    imr_2000_value = country_year_value(imr, TREATED, FINAL_YEAR)

    peer_mean_by_year = le.groupby("year", as_index=False)["value"].mean()

    subgroup_summary = None
    if advanced_subgroup:
        le_adv = build_rank_table(le, advanced_subgroup, FINAL_YEAR, higher_is_better=True)
        imr_adv = build_rank_table(imr, advanced_subgroup, FINAL_YEAR, higher_is_better=False)
        gdp_adv = build_rank_table(gdp, advanced_subgroup, FINAL_YEAR, higher_is_better=True)
        subgroup_summary = le_adv[["country_iso3", "rank"]].rename(columns={"rank": "le_rank_2000"})
        subgroup_summary = subgroup_summary.merge(imr_adv[["country_iso3", "rank"]].rename(columns={"rank": "imr_rank_2000"}), on="country_iso3")
        subgroup_summary = subgroup_summary.merge(gdp_adv[["country_iso3", "rank"]].rename(columns={"rank": "gdp_rank_2000"}), on="country_iso3")
        subgroup_summary["mean_health_rank_2000"] = (subgroup_summary["le_rank_2000"] + subgroup_summary["imr_rank_2000"]) / 2.0
        subgroup_summary["income_minus_health_rank"] = subgroup_summary["gdp_rank_2000"] - subgroup_summary["mean_health_rank_2000"]
        subgroup_summary = subgroup_summary.sort_values(["mean_health_rank_2000", "le_rank_2000", "country_iso3"], kind="mergesort").reset_index(drop=True)

    if not method_valid:
        verdict = (
            "INCONCLUSIVE_DATA_PENDING — endpoint rank table is incomplete: "
            f"LE peers {peer_coverage['le_peers_with_data_2000']}/{len(peers)}, "
            f"IMR peers {peer_coverage['imr_peers_with_data_2000']}/{len(peers)}, "
            f"income peers {peer_coverage['gdp_peers_with_data_2000']}/{len(peers)}; "
            f"need at least {config['min_peer_coverage']} non-Cuban comparators on each series."
        )
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
    elif primary_hits == 3:
        verdict = (
            f"SUPPORTED — Cuba ranks #{le_rank_2000}/{len(le_2000)} on life expectancy, "
            f"#{imr_rank_2000}/{len(imr_2000)} on infant mortality, and its mean health rank "
            f"{mean_health_rank:.1f} beats its income rank #{gdp_rank_2000} by {income_gap:.1f} places."
        )
        verdict_label = "SUPPORTED"
    elif primary_hits == 2:
        held = []
        missed = []
        held.append(f"LE rank #{le_rank_2000}" if primary1 else f"missed LE cutoff with rank #{le_rank_2000}")
        held.append(f"IMR rank #{imr_rank_2000}" if primary2 else f"missed IMR cutoff with rank #{imr_rank_2000}")
        held.append(f"income gap {income_gap:.1f}" if primary3 else f"missed income-gap cutoff with {income_gap:.1f}")
        if not primary1:
            missed.append(f"LE rank need <= {config['le_rank_threshold']}")
        if not primary2:
            missed.append(f"IMR rank need <= {config['imr_rank_threshold']}")
        if not primary3:
            missed.append(f"income-gap need >= {config['income_gap_threshold']:.1f}")
        verdict = (
            f"PARTIAL — Cuba clears two of the three harder gates in the {config['pool_label']}. "
            f"Ranks: LE #{le_rank_2000}/{len(le_2000)}, IMR #{imr_rank_2000}/{len(imr_2000)}, "
            f"income #{gdp_rank_2000}/{len(gdp_2000)}; mean-health-vs-income gap {income_gap:.1f}. "
            f"Missed: {'; '.join(missed)}."
        )
        verdict_label = "PARTIAL"
    else:
        verdict = (
            f"REFUTED — Cuba does not clear the advanced cutoff in the {config['pool_label']}. "
            f"Ranks: LE #{le_rank_2000}/{len(le_2000)}, IMR #{imr_rank_2000}/{len(imr_2000)}, "
            f"income #{gdp_rank_2000}/{len(gdp_2000)}; mean-health-vs-income gap {income_gap:.1f}."
        )
        verdict_label = "REFUTED"

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "all_pass": verdict_label == "SUPPORTED",
        "method_valid": method_valid,
        "primary_checks": {
            "life_expectancy_rank_cutoff": primary1,
            "infant_mortality_rank_cutoff": primary2,
            "health_vs_income_gap_cutoff": primary3,
        },
        "thresholds": {
            "le_rank_threshold": config["le_rank_threshold"],
            "imr_rank_threshold": config["imr_rank_threshold"],
            "income_gap_threshold": config["income_gap_threshold"],
        },
        "ranks_1960": {
            "le_rank_1960": le_rank_1960,
            "imr_rank_1960": imr_rank_1960,
            "pool_size": int(max(len(le_1960), len(imr_1960))),
        },
        "ranks_2000": {
            "le_rank_2000": le_rank_2000,
            "imr_rank_2000": imr_rank_2000,
            "gdp_rank_2000": gdp_rank_2000,
            "mean_health_rank_2000": mean_health_rank,
            "income_minus_health_rank": income_gap,
            "pool_size": int(len(rank_summary)),
        },
        "peer_coverage": peer_coverage,
        "rank_table_2000": rank_summary.to_dict(orient="records"),
        "subperiod": {
            "cuba_life_expectancy_1991": le_1991,
            "cuba_life_expectancy_2000": le_2000_value,
            "cuba_infant_mortality_1991": imr_1991,
            "cuba_infant_mortality_2000": imr_2000_value,
        },
        "advanced_subgroup_2000": None if subgroup_summary is None else subgroup_summary.to_dict(orient="records"),
        "data_quality_caveat": config["data_quality_caveat"],
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    if len(countries) <= 12:
        series = []
        for idx, country in enumerate(countries):
            sub = le[le["country_iso3"] == country][["year", "value"]].dropna().sort_values("year")
            if sub.empty:
                continue
            series.append({
                "id": country,
                "label": f"{country} (treated)" if country == TREATED else country,
                "color": "#C0392B" if country == TREATED else PALETTE[idx % len(PALETTE)],
                "treated": country == TREATED,
                "points": [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()],
            })
        chart_title = config["chart_title"]
        chart_subtitle = config["chart_subtitle_template"].format(
            le_rank=le_rank_2000,
            le_pool=len(le_2000),
            imr_rank=imr_rank_2000,
            imr_pool=len(imr_2000),
            gdp_rank=gdp_rank_2000,
            gdp_pool=len(gdp_2000),
            income_gap=income_gap,
        )
    else:
        broad_mean = le[le["country_iso3"].isin(peers)].groupby("year", as_index=False)["value"].mean()
        series = [{
            "id": "CUB",
            "label": "CUB (treated)",
            "color": "#C0392B",
            "treated": True,
            "points": [{"x": int(r.year), "y": float(r.value)} for r in le[le["country_iso3"] == TREATED][["year", "value"]].sort_values("year").itertuples()],
        }, {
            "id": "peer_mean",
            "label": config["peer_mean_label"],
            "color": "#4E79A7",
            "treated": False,
            "points": [{"x": int(r.year), "y": float(r.value)} for r in broad_mean.itertuples()],
        }]
        if advanced_subgroup:
            adv_peers = [c for c in advanced_subgroup if c != TREATED]
            adv_mean = le[le["country_iso3"].isin(adv_peers)].groupby("year", as_index=False)["value"].mean()
            series.append({
                "id": "advanced_mean",
                "label": config["advanced_mean_label"],
                "color": "#59A14F",
                "treated": False,
                "points": [{"x": int(r.year), "y": float(r.value)} for r in adv_mean.itertuples()],
            })
        chart_title = config["chart_title"]
        chart_subtitle = config["chart_subtitle_template"].format(
            le_rank=le_rank_2000,
            le_pool=len(le_2000),
            imr_rank=imr_rank_2000,
            imr_pool=len(imr_2000),
            gdp_rank=gdp_rank_2000,
            gdp_pool=len(gdp_2000),
            income_gap=income_gap,
        )

    chart_data = {
        "kind": "result",
        "chart_id": f"{hid}/fig1",
        "title": chart_title,
        "subtitle": chart_subtitle,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Life expectancy at birth (years)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 1959, "label": "Cuban revolution"},
            {"type": "vline", "x": 1962, "label": "US embargo"},
            {"type": "vline", "x": SOVIET_END, "label": "Soviet subsidies end"},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{hid}",
    }
    (out_dir / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    coeffs = pd.DataFrame([
        {"spec": hid, "term": "le_rank_2000", "estimate": le_rank_2000},
        {"spec": hid, "term": "imr_rank_2000", "estimate": imr_rank_2000},
        {"spec": hid, "term": "gdp_rank_2000", "estimate": gdp_rank_2000},
        {"spec": hid, "term": "mean_health_rank_2000", "estimate": mean_health_rank},
        {"spec": hid, "term": "income_minus_health_rank", "estimate": income_gap},
        {"spec": hid, "term": "le_rank_1960", "estimate": le_rank_1960},
        {"spec": hid, "term": "imr_rank_1960", "estimate": imr_rank_1960},
    ])
    coeffs.to_parquet(out_dir / "coefficients.parquet", index=False)

    (out_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": hid,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    table_rows = [
        "| Country | LE rank | IMR rank | Income rank | Mean health rank | Income minus health |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rank_summary.itertuples(index=False):
        table_rows.append(
            f"| {row.country_iso3} | {f(row.le_rank_2000, '.0f')} | {f(row.imr_rank_2000, '.0f')} | "
            f"{f(row.gdp_rank_2000, '.0f')} | {f(row.mean_health_rank_2000, '.1f')} | {f(row.income_minus_health_rank, '+.1f')} |"
        )

    subgroup_lines = []
    if subgroup_summary is not None:
        subgroup_lines.extend([
            "",
            f"## {config['advanced_subgroup_heading']}",
            "",
            "| Country | LE rank | IMR rank | Income rank | Mean health rank | Income minus health |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for row in subgroup_summary.itertuples(index=False):
            subgroup_lines.append(
                f"| {row.country_iso3} | {f(row.le_rank_2000, '.0f')} | {f(row.imr_rank_2000, '.0f')} | "
                f"{f(row.gdp_rank_2000, '.0f')} | {f(row.mean_health_rank_2000, '.1f')} | {f(row.income_minus_health_rank, '+.1f')} |"
            )

    card = [
        f"# {config['card_title']}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Primary thresholds",
        "",
        f"- Life expectancy rank in 2000 must be <= {config['le_rank_threshold']} within the {config['pool_size_label']}.",
        f"- Infant mortality rank in 2000 must be <= {config['imr_rank_threshold']} within the {config['pool_size_label']}.",
        f"- Cuba's mean health rank must beat its income rank by at least {config['income_gap_threshold']:.1f} places.",
        "",
        "## Cuba's standings",
        "",
        f"- 1960 ranks: LE #{f(le_rank_1960, '.0f')}, IMR #{f(imr_rank_1960, '.0f')}.",
        f"- 2000 ranks: LE #{le_rank_2000}/{len(le_2000)}, IMR #{imr_rank_2000}/{len(imr_2000)}, income #{gdp_rank_2000}/{len(gdp_2000)}.",
        f"- Mean health rank in 2000: {mean_health_rank:.1f}.",
        f"- Income minus health-rank gap: {income_gap:+.1f} places.",
        "",
        "## 2000 rank table",
        "",
        *table_rows,
        *subgroup_lines,
        "",
        "## Soviet-subsidy sub-period",
        "",
        f"- Cuba life expectancy: {f(le_1991, '.1f')} in 1991 -> {f(le_2000_value, '.1f')} in 2000.",
        f"- Cuba infant mortality: {f(imr_1991, '.1f')} in 1991 -> {f(imr_2000_value, '.1f')} in 2000.",
        "",
        "## Method",
        "",
        config["method_note"],
        "",
        "## Caveats",
        "",
        f"- {config['data_quality_caveat']}",
        f"- {config['income_caveat']}",
        f"- {config['causal_caveat']}",
        "",
        "## Provenance",
        "",
        "- world_bank_wdi:SP.DYN.LE00.IN",
        "- world_bank_wdi:SP.DYN.IMRT.IN",
        f"- {config['income_publisher']}:{config['income_series']}",
        "",
        "See `manifest.yaml` for exact vintages. Reproduces from `replication.py`.",
    ]
    (out_dir / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")
    print(f"  LE rank 2000: {le_rank_2000}/{len(le_2000)}")
    print(f"  IMR rank 2000: {imr_rank_2000}/{len(imr_2000)}")
    print(f"  income rank 2000: {gdp_rank_2000}/{len(gdp_2000)}")
    print(f"  health minus income gap: {income_gap:+.1f}")
    return 0
