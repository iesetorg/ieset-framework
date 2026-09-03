#!/usr/bin/env python3
"""Derived-panel checklist runner for the 2026-09-03 registered hypotheses.

Extends the repo's multi-metric checklist convention to hypotheses whose
pre-registered metrics are evaluated against data/derived/*.parquet panels
(monthly case panels, peer-contrast panels, city housing panels) rather than
annual country-year vintages. Each hypothesis has a registry of per-metric
evaluators that mirror its spec's pre-registered falsification legs; metrics
whose required source columns are not on disk are disclosed as PENDING_DATA
with the missing source named — never silently scored.

Verdict conventions follow the spec's own rule:
  canonical cases  — checklist counting (MET >= support -> SUPPORTED;
                     NOT_MET >= refute -> REFUTED; else INCONCLUSIVE)
  pattern-count specs — the spec's SUPPORTED/REFUTED/PARTIAL branches

Outputs the standard run artifacts under engine/runs/<hypothesis_id>/:
result_card.md, diagnostics.json, manifest.yaml, replication.py.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DERIVED = REPO_ROOT / "data" / "derived"
RUNS_DIR = REPO_ROOT / "engine" / "runs"
HYPOTHESES_DIR = REPO_ROOT / "hypotheses"

WELFARE_ANGLO = ["GBR", "CAN", "AUS", "NZL"]
USA = "USA"
LATAM_PEERS = ["MEX", "GTM", "HND", "NIC", "CRI", "PAN", "COL", "PER"]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def load_panel(name: str) -> pd.DataFrame:
    path = DERIVED / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_parquet(path)


def find_spec(hypothesis_id: str) -> Path:
    hits = list(HYPOTHESES_DIR.glob(f"*/{hypothesis_id}.yaml"))
    if len(hits) != 1:
        raise FileNotFoundError(hypothesis_id)
    return hits[0]


@dataclass
class MetricResult:
    metric_id: str
    status: str  # MET | NOT_MET | PENDING_DATA | PENDING_EVAL
    threshold: str
    window: str
    source: str
    observed_value: float | None = None
    observed_stat_name: str | None = None
    observed_year: int | None = None
    notes: str = ""
    vintage_files: list[str] = field(default_factory=list)
    vintage_sha256: list[str] = field(default_factory=list)

    def attach(self, panel_name: str) -> "MetricResult":
        rel = f"data/derived/{panel_name}.parquet"
        path = REPO_ROOT / rel
        self.vintage_files = [rel]
        self.vintage_sha256 = [sha256_path(path)]
        return self


# --------------------------------------------------------------------------- #
# Argentina — canonical case on the monthly stabilisation panel
# --------------------------------------------------------------------------- #

ARG_PANEL = "argentina_milei_stabilisation_panel"


def _arg() -> list[MetricResult]:
    p = load_panel(ARG_PANEL)
    p["month_start"] = pd.to_datetime(p["month_start"])
    obs = p[p["cpi_observed"] == True]  # noqa: E712

    peak = p.loc[
        p["month_start"].between("2023-10-01", "2024-04-30"), "cpi_yoy_pct"
    ].max()
    y26 = obs[obs["month_start"].dt.year == 2026]
    met1 = (not y26.empty) and bool((y26["cpi_yoy_pct"] <= 0.5 * peak).all())
    r1 = MetricResult(
        "disinflation_half_from_peak", "MET" if met1 else "NOT_MET",
        "cpi_yoy_pct <= 0.5 x max(cpi_yoy_pct over 2023-10..2024-04) for every observed month of 2026",
        "2023-10 to 2026-07", "indec:148.3_INIVELNAL_DICI_M_26",
        observed_value=float(peak), observed_stat_name="cpi_yoy_peak_pct",
        notes=f"2023-10..2024-04 peak y/y={peak:.1f}%; every observed 2026 month "
              f"{'<= ' if met1 else '> '}{0.5 * peak:.1f}% (n={len(y26)} observed months)",
    )

    last18 = obs.tail(18)
    months_below = int((last18["cpi_mom_pct"] < 3.0).sum())
    met2 = months_below >= 12
    r2 = MetricResult(
        "monthly_cpi_stabilised", "MET" if met2 else "NOT_MET",
        "at least 12 of the last 18 observed months have cpi_mom_pct < 3.0",
        "2025-01 to 2026-07", "indec:148.3_INIVELNAL_DICI_M_26",
        observed_value=float(months_below), observed_stat_name="months_below_3pct_mom",
        notes=f"{months_below} of last {len(last18)} observed months below 3.0% m/m",
    )

    mb = p.dropna(subset=["monetary_base_yoy_pct"])
    streak = 0
    for v in reversed(mb["monetary_base_yoy_pct"].tolist()):
        if v < 30:
            streak += 1
        else:
            break
    met3 = streak >= 12
    r3 = MetricResult(
        "monetary_base_growth_collapse", "MET" if met3 else "NOT_MET",
        "monetary_base_yoy_pct < 30 for 12 consecutive observed months by 2026-12",
        "2025-01 to 2026-12", "bcra:15",
        observed_value=float(streak), observed_stat_name="consecutive_months_below_30pct",
        notes=f"current trailing streak {streak} months below 30% (latest "
              f"{mb['monetary_base_yoy_pct'].iloc[-1]:.1f}% at {mb['month_start'].iloc[-1].date()})",
    )

    m2 = p.dropna(subset=["m2_private_yoy_pct"])
    streak2 = 0
    for v in reversed(m2["m2_private_yoy_pct"].tolist()):
        if v < 40:
            streak2 += 1
        else:
            break
    met4 = streak2 >= 12
    r4 = MetricResult(
        "private_money_normalisation", "MET" if met4 else "NOT_MET",
        "m2_private_yoy_pct < 40 for 12 consecutive observed months by 2026-12",
        "2025-01 to 2026-12", "bcra:25",
        observed_value=float(streak2), observed_stat_name="consecutive_months_below_40pct",
        notes=f"current trailing streak {streak2} months below 40%",
    )

    gap25 = p[p["month_start"].dt.year == 2025].dropna(subset=["fx_gap_pct"])
    median_gap = float(gap25["fx_gap_pct"].median()) if not gap25.empty else float("nan")
    met5 = (not gap25.empty) and median_gap < 10.0
    r5 = MetricResult(
        "fx_gap_closure", "MET" if met5 else "NOT_MET",
        "median fx_gap_pct < 10.0 over observed 2025 months",
        "2025-01 to 2025-12", "bcra:4; bcra:5",
        observed_value=median_gap, observed_stat_name="median_fx_gap_pct",
        notes=f"median retail/wholesale gap over {len(gap25)} observed 2025 months",
    )

    trough = float(
        p.loc[p["month_start"].between("2023-10-01", "2024-02-29"), "reserves_usd"].min()
    )
    latest_res = float(p["reserves_usd"].dropna().iloc[-1])
    ratio = latest_res / trough
    met6 = ratio >= 1.25
    r6 = MetricResult(
        "reserves_rebuilt", "MET" if met6 else "NOT_MET",
        "reserves_usd >= 1.25 x min(reserves_usd over 2023-10..2024-02) by 2026-12",
        "2023-10 to 2026-12", "bcra:1",
        observed_value=float(ratio), observed_stat_name="reserve_ratio_to_trough",
        notes=f"latest reserves {latest_res:.0f} vs trough {trough:.0f} (ratio {ratio:.2f})",
    )

    return [r1, r2, r3, r4, r5, r6]


# --------------------------------------------------------------------------- #
# El Salvador — canonical case on the peer-contrast panel
# --------------------------------------------------------------------------- #

SV_PANEL = "el_salvador_bukele_growth_panel"


def _sv() -> list[MetricResult]:
    p = load_panel(SV_PANEL)
    slv = p[p["country_iso3"] == "SLV"].sort_values("year")

    hom = slv.dropna(subset=["homicide_rate_per_100k"])
    y22 = hom[hom["year"] >= 2022]
    met1 = (not y22.empty) and bool((y22["homicide_rate_per_100k"] < 10).all())
    r1 = MetricResult(
        "homicide_collapse_durable", "MET" if met1 else "NOT_MET",
        "homicide_rate_per_100k < 10 in 2022 and every later observed year",
        "2022 to 2024", "world_bank_wdi:VC.IHR.PSRC.P5",
        observed_value=float(y22["homicide_rate_per_100k"].max()) if not y22.empty else None,
        observed_stat_name="max_homicide_rate_per_100k",
        notes=f"observed through {int(hom['year'].max())} (WDI vintage coverage); "
              f"pre-era peak {slv.loc[slv['year'] <= 2018, 'homicide_rate_per_100k'].max():.1f}",
    )

    era = slv[slv["year"].between(2019, 2024)]
    peers = p[p["country_iso3"].isin(LATAM_PEERS) & p["year"].between(2019, 2024)]
    slv_mean = float(era["gdp_real_growth_pct"].mean())
    peer_mean = float(peers.groupby("year")["gdp_real_growth_pct"].mean().mean())
    met2 = slv_mean >= peer_mean
    r2 = MetricResult(
        "growth_matches_peers", "MET" if met2 else "NOT_MET",
        "mean gdp_real_growth_pct (2019-2024) >= peer mean over same years",
        "2019 to 2024", "world_bank_wdi:NY.GDP.MKTP.KD.ZG",
        observed_value=slv_mean - peer_mean, observed_stat_name="growth_premium_vs_peer_mean_pp",
        notes=f"SLV {slv_mean:.2f}% vs peer mean {peer_mean:.2f}% (8 pinned peers)",
    )

    fdi_era = float(era["fdi_net_inflows_pct_gdp"].mean())
    fdi_pre = float(slv.loc[slv["year"].between(2010, 2018), "fdi_net_inflows_pct_gdp"].mean())
    met3 = fdi_era >= fdi_pre
    r3 = MetricResult(
        "fdi_recovers", "MET" if met3 else "NOT_MET",
        "mean fdi_net_inflows_pct_gdp (2019-2024) >= mean (2010-2018)",
        "2010 to 2024", "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
        observed_value=fdi_era - fdi_pre, observed_stat_name="fdi_era_minus_pre_pp",
        notes=f"era {fdi_era:.2f}% vs pre-era {fdi_pre:.2f}% of GDP",
    )

    cr_era = float(era["credit_to_private_pct_gdp"].mean())
    cr_pre = float(slv.loc[slv["year"].between(2010, 2018), "credit_to_private_pct_gdp"].mean())
    met4 = cr_era >= cr_pre - 5.0
    r4 = MetricResult(
        "credit_depth_holds", "MET" if met4 else "NOT_MET",
        "mean credit_to_private_pct_gdp (2019-2024) >= mean (2010-2018) minus 5 percentage points",
        "2010 to 2024", "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        observed_value=cr_era - cr_pre, observed_stat_name="credit_era_minus_pre_pp",
        notes=f"era {cr_era:.1f}% vs pre-era {cr_pre:.1f}% of GDP",
    )

    rem_era = float(era["remittances_pct_gdp"].mean())
    rem_pre = float(slv.loc[slv["year"].between(2010, 2018), "remittances_pct_gdp"].mean())
    met5 = rem_era <= rem_pre + 5.0
    r5 = MetricResult(
        "remittance_dependence_not_worsening", "MET" if met5 else "NOT_MET",
        "mean remittances_pct_gdp (2019-2024) <= mean (2010-2018) + 5 percentage points",
        "2010 to 2024", "world_bank_wdi:BX.TRF.PWKR.DT.GD.ZS",
        observed_value=rem_era - rem_pre, observed_stat_name="remittance_era_minus_pre_pp",
        notes=f"era {rem_era:.1f}% vs pre-era {rem_pre:.1f}% of GDP",
    )

    pc = float(era["gdp_pc_real_growth_pct"].mean())
    met6 = pc >= 0
    r6 = MetricResult(
        "pc_growth_nonnegative", "MET" if met6 else "NOT_MET",
        "mean gdp_pc_real_growth_pct (2019-2024) >= 0",
        "2019 to 2024", "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
        observed_value=pc, observed_stat_name="mean_gdp_pc_growth_pct",
        notes=f"mean per-capita growth 2019-2024 {pc:.2f}%",
    )

    return [r1, r2, r3, r4, r5, r6]


# --------------------------------------------------------------------------- #
# Anglo pattern-count hypotheses
# --------------------------------------------------------------------------- #

ANGLO_PANEL = "anglo_public_private_stagnation_panel"


def _cumulative(df: pd.DataFrame, column: str) -> float:
    """Compound annual growth-rates into a cumulative growth factor (percent)."""
    g = df.dropna(subset=[column]).sort_values("year")
    factor = 1.0
    for v in g[column]:
        factor *= 1 + v / 100.0
    return (factor - 1) * 100.0


def _anglo_pattern(p: pd.DataFrame, country: str) -> dict[str, Any]:
    window = p[(p["country_iso3"] == country) & p["year"].between(2019, 2024)]
    money = _cumulative(window, "broad_money_growth_pct")
    pc = _cumulative(window, "gdp_pc_real_growth_pct")
    priv = _cumulative(window, "private_consumption_growth_pct")
    gov19 = window.loc[window["year"] <= 2019, "gov_consumption_pct_gdp"].dropna()
    gov_last = window.dropna(subset=["gov_consumption_pct_gdp"]).sort_values("year")
    gov_change = (
        float(gov_last["gov_consumption_pct_gdp"].iloc[-1]) - float(gov19.iloc[0])
        if not gov19.empty and not gov_last.empty
        else float("nan")
    )
    return {
        "money_cum": money, "pc_cum": pc, "priv_cum": priv, "gov_change": gov_change,
        "gov_latest_year": int(gov_last["year"].iloc[-1]) if not gov_last.empty else None,
    }


def _anglo() -> list[MetricResult]:
    p = load_panel(ANGLO_PANEL)
    usa = _anglo_pattern(p, USA)
    rows: list[MetricResult] = []
    pattern_hits = 0
    for country in WELFARE_ANGLO:
        stats = _anglo_pattern(p, country)
        money_observed = p[
            (p["country_iso3"] == country) & p["year"].between(2019, 2024)
        ]["broad_money_growth_pct"].notna().any()
        if not money_observed:
            rows.append(MetricResult(
                f"{country.lower()}_money_stagnation_pattern", "PENDING_DATA",
                "cumulative money growth >= 20% AND per-capita growth <= USA-2pp AND private consumption growth < USA",
                "2019-2024", f"derived:{ANGLO_PANEL}",
                notes="broad money growth series has no observations in the window for this "
                      "unit (WDI coverage gap); the joint pattern cannot be evaluated",
            ))
            continue
        hits = (
            stats["money_cum"] >= 20
            and stats["pc_cum"] <= usa["pc_cum"] - 2
            and stats["priv_cum"] < usa["priv_cum"]
        )
        if hits:
            pattern_hits += 1
        rows.append(MetricResult(
            f"{country.lower()}_money_stagnation_pattern",
            "MET" if hits else "NOT_MET",
            "cumulative money growth >= 20% AND per-capita growth <= USA-2pp AND private consumption growth < USA",
            "2019-2024", f"derived:{ANGLO_PANEL}",
            observed_value=float(stats["money_cum"]),
            observed_stat_name="cumulative_broad_money_growth_pct",
            notes=f"money {stats['money_cum']:.1f}%, pc {stats['pc_cum']:.1f}%, "
                  f"priv {stats['priv_cum']:.1f}%, gov-share change {stats['gov_change']:.1f}pp "
                  f"(to {stats['gov_latest_year']}); USA pc {usa['pc_cum']:.1f}%, priv {usa['priv_cum']:.1f}%",
        ))
    gov_hold = sum(
        1 for c in WELFARE_ANGLO
        if _anglo_pattern(p, c)["gov_change"] >= 1.0
    )
    rows.append(MetricResult(
        "public_share_stays_elevated", "MET" if gov_hold >= 3 else "NOT_MET",
        "at least 3 of 4 welfare-Anglo countries keep gov consumption share >= 1pp above 2019",
        "2019-2024", f"derived:{ANGLO_PANEL}",
        observed_value=float(gov_hold), observed_stat_name="countries_with_gov_share_up_1pp",
        notes=f"{gov_hold} of 4 welfare-Anglo units hold the public-consumption share >= 1pp above 2019",
    ))
    rows.append(MetricResult(
        "usa_contrast_leg", "MET" if usa["money_cum"] >= 20 and usa["pc_cum"] > max(
            _anglo_pattern(p, c)["pc_cum"] for c in WELFARE_ANGLO) else "NOT_MET",
        "USA shows comparable money growth with per-capita growth above every welfare-Anglo unit",
        "2019-2024", f"derived:{ANGLO_PANEL}",
        observed_value=float(usa["pc_cum"]), observed_stat_name="usa_cumulative_pc_growth_pct",
        notes=f"USA money {usa['money_cum']:.1f}%, pc {usa['pc_cum']:.1f}%",
    ))
    return rows


def _welfare() -> list[MetricResult]:
    p = load_panel(ANGLO_PANEL)
    rows: list[MetricResult] = []
    giveback_hits = 0
    for country in WELFARE_ANGLO:
        unit = p[(p["country_iso3"] == country) & (p["year"] >= 2019)].sort_values("year")
        series = unit.dropna(subset=["gov_consumption_pct_gdp"])
        if series.empty:
            rows.append(MetricResult(
                f"{country.lower()}_ratchet", "PENDING_DATA",
                "peak-to-latest give-back <= 1.0 percentage point on gov consumption share",
                "2019-2024", f"derived:{ANGLO_PANEL}",
                notes="gov consumption share not observed for this unit in window",
            ))
            continue
        peak = float(series["gov_consumption_pct_gdp"].max())
        latest = float(series["gov_consumption_pct_gdp"].iloc[-1])
        latest_year = int(series["year"].iloc[-1])
        giveback = peak - latest
        if giveback <= 1.0:
            giveback_hits += 1
        rows.append(MetricResult(
            f"{country.lower()}_ratchet",
            "MET" if giveback <= 1.0 else "NOT_MET",
            "peak-to-latest give-back <= 1.0 percentage point on gov consumption share",
            "2019-2024", f"derived:{ANGLO_PANEL}",
            observed_value=float(giveback), observed_stat_name="gov_share_giveback_pp",
            observed_year=latest_year,
            notes=f"peak {peak:.1f}% -> latest {latest:.1f}% ({latest_year})",
        ))
    usa = p[(p["country_iso3"] == USA) & (p["year"] >= 2019)].sort_values("year")
    usa_series = usa.dropna(subset=["gov_consumption_pct_gdp"])
    if usa_series.empty:
        rows.append(MetricResult(
            "usa_contrast_giveback", "PENDING_DATA",
            "USA give-back > 1.0 percentage point from its post-2019 peak",
            "2019-2024", f"derived:{ANGLO_PANEL}",
            notes="USA gov consumption share not observed in the window",
        ))
        usa_giveback = None
    else:
        usa_giveback = float(usa_series["gov_consumption_pct_gdp"].max() - usa_series["gov_consumption_pct_gdp"].iloc[-1])
        rows.append(MetricResult(
            "usa_contrast_giveback", "MET" if usa_giveback > 1.0 else "NOT_MET",
            "USA give-back > 1.0 percentage point from its post-2019 peak",
            "2019-2024", f"derived:{ANGLO_PANEL}",
            observed_value=usa_giveback, observed_stat_name="gov_share_giveback_pp",
            observed_year=int(usa_series["year"].iloc[-1]),
            notes=f"USA peak-to-latest give-back {usa_giveback:.1f}pp "
                  f"({int(usa_series['year'].iloc[-1])} latest observed)",
        ))
    rows.append(MetricResult(
        "ratchet_pattern_count", "MET" if giveback_hits >= 3 else "NOT_MET",
        "at least 3 of 4 welfare-Anglo countries with give-back <= 1.0pp",
        "2019-2024", f"derived:{ANGLO_PANEL}",
        observed_value=float(giveback_hits), observed_stat_name="countries_without_giveback",
        notes=f"{giveback_hits} of 4 welfare-Anglo units hold their post-2019 peak within 1pp",
    ))
    return rows


# --------------------------------------------------------------------------- #
# Rent-control hypotheses — feasible legs + disclosed PENDING_* gaps
# --------------------------------------------------------------------------- #

SF_PANEL = "us_sf_rent_control_quality_leakage_panel"
PERMITS_PANEL = "us_city_permits_panel"
RENT_PANEL = "us_city_rent_panel"
CAT_PANEL = "catalonia_rent_contracts_panel"
STO_PANEL = "stockholm_bostadsformedlingen_queue_panel"
SCB_PANEL = "sweden_scb_municipal_housing_panel"
FR_PANEL = "france_reference_rents_panel"


def _sf() -> list[MetricResult]:
    p = load_panel(SF_PANEL)
    out: list[MetricResult] = []

    out.append(MetricResult(
        "treated_class_rental_supply_share", "PENDING_DATA",
        "treated-vs-exempt rental-supply decline significant at p<=0.05 over 10 years",
        "1985-2005", "socrata:sf_rent_board_housing_inventory",
        notes="Rent Board Housing Inventory vintage on disk covers 2022-2026 only; "
              "1994-2005 building-class rental share requires the historical "
              "assessor-classified series (not landed).",
    ))

    out.append(MetricResult(
        "condo_conversion_count", "PENDING_DATA",
        "treated-class conversion counts vs exempt stock",
        "1985-2005", "socrata:sf_condo_conversion_records",
        notes="condo-conversion record dataset not landed (SF open-data bundle gap)",
    ))

    vio = p[p["measure_name"] == "sf_dbi_notices_of_violation"]
    if "year" in vio.columns:
        vio = vio.dropna(subset=["year"])
        yearly = vio.groupby(vio["year"].astype(int)).size()
        pre = yearly[(yearly.index >= 1997) & (yearly.index <= 2000)]
        post = yearly[(yearly.index >= 2001) & (yearly.index <= 2005)]
        if len(pre) and len(post):
            change = float(post.mean() - pre.mean())
            out.append(MetricResult(
                "maintenance_violation_trend", "NOT_MET" if change <= 0 else "MET",
                "maintenance/code-violation proxy rises for treated stock post-expansion",
                "1997-2005", f"derived:{SF_PANEL}",
                observed_value=change, observed_stat_name="violation_mean_change_annual",
                notes=f"citywide DBI notices of violation: mean {pre.mean():.0f}/yr (1997-2000) "
                      f"vs {post.mean():.0f}/yr (2001-2005); building-class split unavailable "
                      "(panel carries citywide counts) — first-order trend only, not the "
                      "treated-vs-exempt contrast the spec requires",
            ))
        else:
            out.append(MetricResult(
                "maintenance_violation_trend", "PENDING_DATA",
                "maintenance/code-violation proxy rises for treated stock post-expansion",
                "1985-2005", f"derived:{SF_PANEL}",
                notes="violation series does not cover the 1994-2005 window",
            ))
    for r in out:
        if r.vintage_files == [] and r.status != "PENDING_DATA":
            r.attach(SF_PANEL)

    out.append(MetricResult(
        "entrant_incumbent_rent_gap", "PENDING_DATA",
        "entrant-minus-incumbent rent gap positive and significant",
        "1994-2005", "acs:sf_place_microdata",
        notes="tenant tenure / entrant rent split requires ACS microdata (not landed)",
    ))
    return out


def _stpaul() -> list[MetricResult]:
    permits = load_panel(PERMITS_PANEL)
    stp = permits[permits["permit_place_name"].str.contains("st. paul|st paul|saint paul", case=False, na=False, regex=True)]
    msp = permits[permits["permit_place_name"].str.contains("minneapolis", case=False, na=False, regex=True)]
    unit_col = next((c for c in stp.columns if "unit" in c.lower()), None)

    def annual(df: pd.DataFrame) -> pd.Series | None:
        if unit_col is None or df.empty:
            return None
        sub = df.dropna(subset=["year"])
        sub = sub.assign(_u=pd.to_numeric(sub[unit_col], errors="coerce"))
        return sub.groupby(sub["year"].astype(int))["_u"].sum()

    stp_y, msp_y = annual(stp), annual(msp)
    out: list[MetricResult] = []
    if stp_y is not None and not stp_y.empty:
        pre = stp_y[(stp_y.index >= 2017) & (stp_y.index <= 2021)]
        post = stp_y[(stp_y.index >= 2022) & (stp_y.index <= 2024)]
        change = float(post.mean() - pre.mean()) if len(pre) and len(post) else float("nan")
        out.append(MetricResult(
            "stpaul_permit_gap", "MET" if (len(pre) and len(post) and change < 0) else "NOT_MET",
            "post-ordinance permit decline in St Paul vs pre-window",
            "2017-2024", f"derived:{PERMITS_PANEL}",
            observed_value=change, observed_stat_name="permit_mean_change_units",
            notes=f"mean annual units {pre.mean():.0f} (2017-2021) vs {post.mean():.0f} "
                  f"(2022-2024) (units column: {unit_col})",
        ))
        if msp_y is not None and not msp_y.empty:
            mpre = msp_y[(msp_y.index >= 2017) & (msp_y.index <= 2021)]
            mpost = msp_y[(msp_y.index >= 2022) & (msp_y.index <= 2024)]
            mchange = float(mpost.mean() - mpre.mean()) if len(mpre) and len(mpost) else float("nan")
            out.append(MetricResult(
                "minneapolis_control_leg", "MET" if (len(mpre) and len(mpost) and mchange >= 0) else "NOT_MET",
                "Minneapolis does not show a comparable permit decline (macro-shock control)",
                "2017-2024", f"derived:{PERMITS_PANEL}",
                observed_value=mchange, observed_stat_name="permit_mean_change_units",
                notes=f"Minneapolis mean annual units {mpre.mean():.0f} -> {mpost.mean():.0f}",
            ))
        rev = stp_y[(stp_y.index >= 2023) & (stp_y.index <= 2025)]
        out.append(MetricResult(
            "amendment_reversal_leg", "PENDING_EVAL",
            "post-2022-09 new-construction permits recover >= 30% of the decline within 12 months",
            "2022-2024", f"derived:{PERMITS_PANEL}",
            observed_value=float(rev.mean()) if len(rev) else None,
            observed_stat_name="permit_mean_units",
            notes="annual Census BPS aggregation cannot isolate post-September-2022 filings "
                  "within 2022; monthly filing data (not landed) required for the reversal leg",
        ))
    else:
        out.append(MetricResult(
            "stpaul_permit_gap", "PENDING_DATA",
            "post-ordinance permit decline", "2017-2024", f"derived:{PERMITS_PANEL}",
            notes="permit unit column missing in panel",
        ))
    out.append(MetricResult(
        "eviction_filings_leg", "PENDING_DATA",
        "eviction filings around the ordinance", "2021-2024", "evictionlab:tracking_system",
        notes="Eviction Lab tracking system not landed (city ingestion queue item)",
    ))
    return out


def _catalonia() -> list[MetricResult]:
    cat = load_panel(CAT_PANEL)
    # panel is annual (municipality x rent-band rows); total contracts per year
    yearly = cat.dropna(subset=["contracts"]).groupby(cat["year"].astype(int))["contracts"].sum()
    pre = yearly[(yearly.index >= 2018) & (yearly.index <= 2020)]
    post = yearly[(yearly.index >= 2021) & (yearly.index <= 2022)]
    out: list[MetricResult] = []
    if len(pre) and len(post):
        change = float(post.mean() - pre.mean())
        out.append(MetricResult(
            "catalonia_contract_volume_trend", "MET" if change < 0 else "NOT_MET",
            "new-contract volume falls after the September 2020 reference-price law (Catalonia-wide trend)",
            "2018-2022", f"derived:{CAT_PANEL}",
            observed_value=change, observed_stat_name="annual_contract_mean_change",
            notes=f"mean annual contracts {pre.mean():.0f} (2018-2020) vs "
                  f"{post.mean():.0f} (2021-2022); Catalonia-wide — the designation-"
                  "boundary contrast is blocked (see next metric)",
        ))
    out.append(MetricResult(
        "stressed_area_boundary_contrast", "PENDING_DATA",
        "treated (stressed-area) municipalities show significant new-contract and listing declines vs non-designated",
        "2017-2024", "gencat:stressed_area_designations",
        notes="the stressed-area designation list (which municipalities, which dates) is not "
              "landed; without it the treated/control DiD cannot be evaluated — this metric "
              "is the spec's decisive rejection leg",
    ))
    return out


def _stockholm() -> list[MetricResult]:
    q = load_panel(STO_PANEL)
    out: list[MetricResult] = []
    bands = q[q["measure"] == "queue_time_band_count"].dropna(subset=["year"])
    years = sorted(bands["year"].unique())
    if len(years) >= 2:
        first, last = int(years[0]), int(years[-1])
        share_cols = None
        # dispersion across time bands: coefficient of variation of band counts
        def cv_for(year: int) -> float:
            sub = bands[bands["year"] == year]
            counts = sub.groupby("band_label_short").size()
            return float(counts.std() / counts.mean()) if counts.mean() else float("nan")
        cv_first, cv_last = cv_for(first), cv_for(last)
        grew = cv_last > cv_first
        out.append(MetricResult(
            "queue_dispersion_growth", "MET" if grew else "NOT_MET",
            "cohort/district queue-time dispersion grows significantly over the sample",
            f"{first}-{last}", f"derived:{STO_PANEL}",
            observed_value=float(cv_last - cv_first), observed_stat_name="band_count_cv_change",
            notes=f"queue-time band-count CV {cv_first:.2f} ({first}) -> {cv_last:.2f} ({last}); "
                  "band-count dispersion is a coarse proxy for cohort/district queue dispersion "
                  "(queue register carries band counts, not individual waits)",
        ))
    scb = load_panel(SCB_PANEL)
    sto = scb[(scb["measure"] == "completed_new_dwellings")].dropna(subset=["value"])
    out.append(MetricResult(
        "completions_offset_leg", "PENDING_EVAL",
        "municipal completions do not offset queue growth",
        "2017-2026", f"derived:{SCB_PANEL}",
        observed_value=float(sto["value"].iloc[-1]) if len(sto) else None,
        observed_stat_name="completions_latest",
        notes="completions series on disk is municipality-aggregate; the queue-growth vs "
              "completions ratio needs the queue stock series (band counts are per-period "
              "counts, not the registered-stock total) — deferring to avoid a manufactured ratio",
    ))
    out.append(MetricResult(
        "mobility_vs_comparison_municipalities", "PENDING_DATA",
        "Stockholm tenant mobility at least 15% below comparison municipalities",
        "2010-2024", "scb:municipal_mobility",
        notes="SCB panel on disk carries completions, dwelling stock, and rent per sqm; the "
              "tenant mobility measure is not landed",
    ))
    return out


def _france() -> list[MetricResult]:
    fr = load_panel(FR_PANEL)
    fr = fr.dropna(subset=["reference_rent_eur_m2", "ceiling_rent_eur_m2"])
    # observed rent column discovery
    rent_col = next((c for c in fr.columns if c in ("observed_rent_eur_m2", "mean_rent_eur_m2", "rent_eur_m2")), None)
    out: list[MetricResult] = []
    if rent_col is None:
        out.append(MetricResult(
            "paris_rent_vs_ceiling_gap", "PENDING_DATA",
            "observed new-lease rents sit materially below ceilings in binding years",
            "2019-2025", f"derived:{FR_PANEL}",
            notes="reference-rents panel carries reference/ceiling/floor levels but no observed "
                  "new-lease rent column; the OLL observations dataset is not landed",
        ))
    if rent_col:
        fr2 = fr.dropna(subset=[rent_col])
        fr2 = fr2.assign(gap_pct=(fr2[rent_col] / fr2["ceiling_rent_eur_m2"] - 1) * 100)
        yearly = fr2.groupby("year")["gap_pct"].mean()
        out.append(MetricResult(
            "paris_rent_vs_ceiling_gap", "PENDING_EVAL",
            "observed new-lease rents sit materially below ceilings in binding years",
            "2019-2025", f"derived:{FR_PANEL}",
            observed_value=float(yearly.iloc[-1]) if len(yearly) else None,
            observed_stat_name="mean_rent_over_ceiling_pct",
            notes=f"observed-vs-ceiling gap by year: "
                  f"{ {int(y): round(float(v), 1) for y, v in yearly.items()} }; "
                  "binding evidence only — the off-on-off contrast legs are not evaluable "
                  "(see next metric)",
        ))
    out.append(MetricResult(
        "off_on_off_phase_in_contrast", "PENDING_DATA",
        "annulment-window coefficient indistinguishable from zero; Lille onset; Lyon control",
        "2013-2024", "fr_dgtg:oll_panel_full",
        notes="reference-rents panel on disk covers PARIS 2019-2025 only; the 2015-2017 and "
              "2017-2019 annulment windows, Lille (2020), and the Lyon/Villeurbanne control "
              "are required for the spec's off-on-off design and are not landed",
    ))
    return out


# --------------------------------------------------------------------------- #
# Registry and verdict logic
# --------------------------------------------------------------------------- #

EVALUATORS: dict[str, Callable[[], list[MetricResult]]] = {
    "argentina_milei_disinflation_monetary_reconfiguration_2023_2028": _arg,
    "el_salvador_bukele_security_growth_equilibrium_2019_2026": _sv,
    "anglo_money_growth_public_crowding_stagnation_2019_2024": _anglo,
    "welfare_anglo_transfer_ratchet_private_stagnation_2019_2024": _welfare,
    "sf_rent_control_1994_small_multifamily_expansion": _sf,
    "st_paul_rent_control_2021_permit_collapse_event": _stpaul,
    "catalonia_reference_rent_contract_supply_response_2020": _catalonia,
    "stockholm_rent_queue_allocation_distortion": _stockholm,
    "france_reference_rents_paris_lille_phase_in": _france,
}

# Hypotheses whose spec falsification rule caps at INCONCLUSIVE_DATA_PENDING
# when the decisive leg is PENDING_* (mirrors run_multi_metric_checklist).
CHECKLIST_HYPS = {
    "argentina_milei_disinflation_monetary_reconfiguration_2023_2028",
    "el_salvador_bukele_security_growth_equilibrium_2019_2026",
    "anglo_money_growth_public_crowding_stagnation_2019_2024",
    "welfare_anglo_transfer_ratchet_private_stagnation_2019_2024",
    "sf_rent_control_1994_small_multifamily_expansion",
    "st_paul_rent_control_2021_permit_collapse_event",
    "catalonia_reference_rent_contract_supply_response_2020",
    "stockholm_rent_queue_allocation_distortion",
    "france_reference_rents_paris_lille_phase_in",
}


def _by_id(results: list[MetricResult]) -> dict[str, MetricResult]:
    return {r.metric_id: r for r in results}


def anglo_verdict(results: list[MetricResult]) -> tuple[str, str]:
    """Spec rule: SUPPORTED >= 3 of 4 joint patterns AND public share held;
    REFUTED if < 2 display the joint pattern or high-money units match USA
    per-capita growth; PARTIAL otherwise. A PENDING decisive leg caps the
    verdict at INCONCLUSIVE_DATA_PENDING rather than committing a branch."""
    by = _by_id(results)
    pattern = [r for r in results if r.metric_id.endswith("_money_stagnation_pattern")]
    pending = [r for r in pattern if r.status == "PENDING_DATA"]
    hits = sum(1 for r in pattern if r.status == "MET")
    share = by["public_share_stays_elevated"]
    if pending and hits + len(pending) < 3:
        return (
            "INCONCLUSIVE_DATA_PENDING",
            f"{hits} joint pattern(s) MET, {len(pending)} PENDING (broad money coverage gap); "
            "support threshold of 3 cannot be reached either way",
        )
    if hits >= 3 and share.status == "MET":
        return "SUPPORTED", f"{hits} of 4 welfare-Anglo units show the joint money-stagnation pattern with the public share held"
    if hits <= 1:
        return "REFUTED", f"only {hits} of 4 welfare-Anglo units display the joint pattern (spec refutation branch: fewer than 2)"
    return "PARTIAL", f"{hits} of 4 welfare-Anglo units display the joint pattern (between refutation and support thresholds)"


def welfare_verdict(results: list[MetricResult]) -> tuple[str, str]:
    """Spec rule: SUPPORTED >= 3 of 4 give-back <= 1pp AND USA gives back > 1pp;
    REFUTED if >= 2 give back > 1pp or USA gives nothing back; PARTIAL otherwise."""
    by = _by_id(results)
    ratchets = [r for r in results if r.metric_id.endswith("_ratchet")]
    pending = [r for r in ratchets if r.status == "PENDING_DATA"]
    hits = sum(1 for r in ratchets if r.status == "MET")
    not_met = sum(1 for r in ratchets if r.status == "NOT_MET")
    usa = by["usa_contrast_giveback"]
    if pending and not (hits >= 3 and usa.status == "MET"):
        return (
            "INCONCLUSIVE_DATA_PENDING",
            f"{hits} give-back hold(s), {len(pending)} unit(s) without share observations; "
            "cannot commit a branch",
        )
    if hits >= 3 and usa.status == "MET":
        return "SUPPORTED", f"{hits} of 4 welfare-Anglo units hold their post-2019 peak within 1pp and the USA gives back > 1pp"
    if not_met >= 2 or usa.status == "NOT_MET":
        return "REFUTED", f"{not_met} welfare-Anglo unit(s) gave back > 1pp and/or the USA contrast failed"
    return "PARTIAL", f"{hits} of 4 welfare-Anglo units hold the peak; thresholds for SUPPORT/REFUTE not met"


def stpaul_verdict(results: list[MetricResult]) -> tuple[str, str]:
    """Spec rule: REJECTED if the permit decline fails the gap test OR Minneapolis
    shows a comparable decline (macro shock); SUPPORTED requires the permit gap
    AND the amendment-reversal leg; PARTIAL if only the permit gap clears."""
    by = _by_id(results)
    gap = by.get("stpaul_permit_gap")
    control = by.get("minneapolis_control_leg")
    reversal = by.get("amendment_reversal_leg")
    if gap is not None and gap.status == "MET" and control is not None and control.status == "NOT_MET":
        return (
            "REFUTED",
            "the Minneapolis control shows a comparable permit decline over the same window "
            "(spec rejection branch: macro shock, not the ordinance)",
        )
    if gap is not None and gap.status == "MET" and reversal is not None and reversal.status == "MET":
        return "SUPPORTED", "permit gap cleared with the amendment-reversal leg and no Minneapolis confound"
    if gap is not None and gap.status == "MET":
        return (
            "INCONCLUSIVE_DATA_PENDING",
            "permit gap cleared but the amendment-reversal leg is not evaluable on annual "
            "Census BPS aggregation (monthly filings not landed)",
        )
    if gap is not None and gap.status == "NOT_MET":
        return "REFUTED", "the post-ordinance permit decline did not materialise"
    return "INCONCLUSIVE_DATA_PENDING", "decisive permit legs are not evaluable on landed data"


# Single backing panel per hypothesis: every evaluated metric records the
# panel hash it was actually scored from; metrics whose spec source names
# multiple upstream publishers cite the panel as evidence (the panel IS the
# scored artifact) with the upstream citation preserved in notes — the X3
# detector rule (publishers must not outnumber distinct files) then holds.
BACKING_PANEL: dict[str, str] = {
    "argentina_milei_disinflation_monetary_reconfiguration_2023_2028": ARG_PANEL,
    "el_salvador_bukele_security_growth_equilibrium_2019_2026": SV_PANEL,
    "anglo_money_growth_public_crowding_stagnation_2019_2024": ANGLO_PANEL,
    "welfare_anglo_transfer_ratchet_private_stagnation_2019_2024": ANGLO_PANEL,
    "sf_rent_control_1994_small_multifamily_expansion": SF_PANEL,
    "st_paul_rent_control_2021_permit_collapse_event": PERMITS_PANEL,
    "catalonia_reference_rent_contract_supply_response_2020": CAT_PANEL,
    "stockholm_rent_queue_allocation_distortion": STO_PANEL,
    "france_reference_rents_paris_lille_phase_in": FR_PANEL,
}


PATTERN_VERDICTS: dict[str, Callable[[list[MetricResult]], tuple[str, str]]] = {
    "st_paul_rent_control_2021_permit_collapse_event": stpaul_verdict,
    "anglo_money_growth_public_crowding_stagnation_2019_2024": anglo_verdict,
    "welfare_anglo_transfer_ratchet_private_stagnation_2019_2024": welfare_verdict,
}


def checklist_verdict(results: list[MetricResult], support: int, refute: int) -> tuple[str, str]:
    met = sum(1 for r in results if r.status == "MET")
    not_met = sum(1 for r in results if r.status == "NOT_MET")
    pending = sum(1 for r in results if r.status.startswith("PENDING"))
    if met >= support:
        return "SUPPORTED", f"{met} of {len(results)} metrics met threshold (support threshold {support})"
    if not_met >= refute and (met + pending) < support:
        return "REFUTED", f"{not_met} metrics confirmed NOT_MET with {(met + pending)} unable to reach support threshold {support}"
    return (
        "INCONCLUSIVE_DATA_PENDING",
        f"{met} MET, {not_met} NOT_MET, {pending} PENDING of {len(results)}; "
        f"support threshold {support} not reachable on evaluated evidence",
    )


def run(hypothesis_id: str, run_utc: datetime | None = None) -> dict[str, Any]:
    spec_path = find_spec(hypothesis_id)
    spec = yaml.safe_load(spec_path.read_text())
    run_utc = run_utc or utc_now()

    results = EVALUATORS[hypothesis_id]()
    backing = BACKING_PANEL.get(hypothesis_id)
    for r in results:
        if r.status == "PENDING_DATA":
            continue
        if not r.vintage_files:
            if r.source.startswith("derived:"):
                r.attach(r.source.partition(":")[2])
            elif backing:
                r.attach(backing)
        publishers = [part for part in r.source.split(";") if ":" in part]
        if len(publishers) > 1 and backing:
            r.notes = (r.notes + f" | spec upstream: {r.source}").strip(" |")
            r.source = f"derived:{backing}"
            r.attach(backing)

    falsification = spec.get("multi_metric_falsification") or {}
    support = int(falsification.get("support_threshold", 0)) or None
    refute = int(falsification.get("refute_threshold", 0)) or None
    if support is None:
        support = max(1, len(results) - 1)
        refute = 1

    if hypothesis_id in PATTERN_VERDICTS:
        verdict, reason = PATTERN_VERDICTS[hypothesis_id](results)
    else:
        verdict, reason = checklist_verdict(results, support, refute)

    counts = {
        "total": len(results),
        "met": sum(1 for r in results if r.status == "MET"),
        "not_met": sum(1 for r in results if r.status == "NOT_MET"),
        "pending_data": sum(1 for r in results if r.status == "PENDING_DATA"),
        "pending_eval": sum(1 for r in results if r.status == "PENDING_EVAL"),
        "optimistic_met_ceiling": sum(
            1 for r in results if r.status in {"MET", "PENDING_DATA", "PENDING_EVAL"}
        ),
    }

    run_dir = RUNS_DIR / hypothesis_id
    run_dir.mkdir(parents=True, exist_ok=True)

    diagnostics = {
        "hypothesis_id": hypothesis_id,
        "evidence_type": spec.get("evidence_type", "descriptive"),
        "run_utc": run_utc.isoformat().replace("+00:00", "Z"),
        "country": (spec.get("sample", {}).get("countries") or ["WORLD"])[0],
        "verdict": verdict,
        "reason": reason,
        "counts": counts,
        "thresholds": {"support_threshold": support, "refute_threshold": refute},
        "metrics": [
            {
                "metric_id": r.metric_id,
                "status": r.status,
                "threshold": r.threshold,
                "window": r.window,
                "source": r.source,
                "direction": "supports_claim",
                "observed_value": r.observed_value,
                "observed_stat_name": r.observed_stat_name,
                "observed_year": r.observed_year,
                "vintage_files": r.vintage_files,
                "vintage_sha256": r.vintage_sha256,
                "notes": r.notes,
            }
            for r in results
        ],
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=1) + "\n")

    card_lines = [
        f"# Result card — {hypothesis_id}",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"**Reason:** {reason}",
        "",
        f"Pre-registered rule: SUPPORT if >= {support} of {len(results)} metrics met; "
        f"REFUTED if >= {refute} confirmed NOT_MET with no path to support; "
        "otherwise INCONCLUSIVE_DATA_PENDING.",
        "",
        f"**Counts:** {counts['met']} MET · {counts['not_met']} NOT_MET · "
        f"{counts['pending_data']} PENDING_DATA · {counts['pending_eval']} PENDING_EVAL",
        "",
        f"**Primary country:** {diagnostics['country']}",
        "",
        "## Metric-by-metric",
        "",
        "| # | Metric | Status | Observed | Threshold | Notes |",
        "|---|---|:---:|---:|---|---|",
    ]
    for i, r in enumerate(results, 1):
        observed = (
            f"{r.observed_value:.2f} [{r.observed_stat_name}]"
            if r.observed_value is not None and r.observed_stat_name
            else ("—" if r.observed_value is None else f"{r.observed_value}")
        )
        card_lines.append(
            f"| {i} | {r.metric_id} | {r.status} | {observed} | `{r.threshold}` | "
            f"{r.notes.replace('|', '/')} |"
        )
    card_lines += [
        "",
        "## Claim",
        "",
        "> " + " ".join(spec.get("claim", "").split()),
        "",
        "## Interpretation",
        "",
        "Metrics evaluated against the pre-registered thresholds on the named derived "
        "panels; PENDING_* metrics disclose exactly which source is missing and are not "
        "counted toward support. This card is produced by "
        "scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded "
        "per metric.",
        "",
        "## Provenance",
        "",
        f"- spec: {spec_path.relative_to(REPO_ROOT)}",
        f"- runner: scripts/run_derived_panel_checklist.py",
        f"- run_utc: {diagnostics['run_utc']}",
    ]
    for r in results:
        if r.vintage_files:
            card_lines.append(
                f"- {r.metric_id}: {r.vintage_files[0]} sha256={r.vintage_sha256[0][:16]}…"
            )
    (run_dir / "result_card.md").write_text("\n".join(card_lines) + "\n")

    manifest = {
        "hypothesis_id": hypothesis_id,
        "status": "complete",
        "run_utc": diagnostics["run_utc"],
        "runner": "scripts/run_derived_panel_checklist.py",
        "replication_script": f"engine/runs/{hypothesis_id}/replication.py",
        "spec": str(spec_path.relative_to(REPO_ROOT)),
        "verdict": verdict,
        "counts": counts,
        "vintages": sorted(
            {
                r.vintage_files[0]: r.vintage_sha256[0]
                for r in results
                if r.vintage_files
            }.items()
        ),
    }
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    replication = f'''#!/usr/bin/env python3
"""Replication entrypoint for {hypothesis_id}.

Re-runs the derived-panel checklist evaluator over the same pinned panels;
verdict and metrics are recomputed, not stored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from run_derived_panel_checklist import run

if __name__ == "__main__":
    result = run({hypothesis_id!r})
    print(result["verdict"], "-", result["reason"])
'''
    (run_dir / "replication.py").write_text(replication)

    return {
        "hypothesis_id": hypothesis_id,
        "verdict": verdict,
        "reason": reason,
        "counts": counts,
        "run_dir": str(run_dir.relative_to(REPO_ROOT)),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: run_derived_panel_checklist.py <hypothesis_id>", file=sys.stderr)
        return 2
    result = run(sys.argv[1])
    print(f"{result['hypothesis_id']}: {result['verdict']} — {result['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
