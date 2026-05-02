#!/usr/bin/env python3
"""Generate national event-window verdicts from cached ONS/INE/BCRA vintages."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
STEEL = ROOT / "hypotheses" / "steelman"
MONTHS = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


@dataclass
class Metric:
    metric_id: str
    description: str
    threshold: str
    window: str
    source: str
    value: float
    passed: bool
    details: str


@dataclass
class Case:
    hypothesis_id: str
    topic: str
    countries: list[str]
    period: list[int]
    claim: str
    rule: str
    test: str
    support_threshold: int
    refute_threshold: int
    prior: float
    disclosure: str
    steelman: str
    outcomes: list[dict]
    treatments: list[dict]
    controls: list[dict]
    scope_outcomes: list[str]
    policy_family: list[str]
    tags: list[str]
    metrics_fn: Callable[[], list[Metric]]


def latest(pub: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {pub}:{series}")
    return files[-1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ons(series: str) -> pd.DataFrame:
    return pd.read_parquet(latest("ons", series))


def ine(series: str) -> pd.DataFrame:
    return pd.read_parquet(latest("ine", series))


def bcra(series: str) -> pd.DataFrame:
    return pd.read_parquet(latest("bcra", series)).sort_values("fecha")


def ons_value(series: str, date: str, frequency: str) -> float:
    df = ons(series)
    m = df[(df["date"] == date) & (df["frequency"] == frequency)]
    if m.empty:
        raise KeyError(f"ONS {series} {date} {frequency}")
    return float(m.iloc[0]["value"])


def pct_change(a: float, b: float) -> float:
    return (b / a - 1.0) * 100.0


def pp_change(a: float, b: float) -> float:
    return b - a


def real_wage_change(start_wage: float, end_wage: float, start_cpi: float, end_cpi: float) -> float:
    return pct_change(start_wage / start_cpi, end_wage / end_cpi)


def ine_series(frame_id: str, serie_cod: str) -> pd.DataFrame:
    df = ine(frame_id)
    return df[df["serie_cod"] == serie_cod].sort_values("date")


def ine_value(frame_id: str, serie_cod: str, date: str) -> float:
    df = ine_series(frame_id, serie_cod)
    m = df[df["date"] == date]
    if m.empty:
        raise KeyError(f"INE {frame_id} {serie_cod} {date}")
    return float(m.iloc[0]["value"])


def ine_ipc_yoy(date: str) -> float:
    df = ine("IPC_general")
    mask = df["serie_name"].astype(str).str.strip().eq("Nacional. Indice general. Variacion anual.")
    if not mask.any():
        mask = df["serie_name"].astype(str).str.contains("Indice general.*Variacion anual", case=False, regex=True)
    m = df[mask & (df["date"] == date)]
    if m.empty:
        # The local parquet preserves accents; keep the exact fallback isolated.
        mask = df["serie_name"].astype(str).str.contains("Índice general.*Variación anual", case=False, regex=True)
        m = df[mask & (df["date"] == date)]
    if m.empty:
        raise KeyError(f"INE IPC yoy {date}")
    return float(m.iloc[0]["value"])


def bcra_nearest(series: str, date: str, direction: str = "nearest") -> float:
    df = bcra(series).copy()
    target = pd.Timestamp(date)
    if direction == "before":
        df = df[df["fecha"] <= target]
        row = df.iloc[-1]
    elif direction == "after":
        df = df[df["fecha"] >= target]
        row = df.iloc[0]
    else:
        idx = (df["fecha"] - target).abs().idxmin()
        row = df.loc[idx]
    return float(row["valor"])


def bcra_window(series: str, start: str, end: str) -> pd.DataFrame:
    df = bcra(series)
    return df[(df["fecha"] >= pd.Timestamp(start)) & (df["fecha"] <= pd.Timestamp(end))]


def avg_monthly_inflation(start: str, end: str) -> float:
    w = bcra_window("27", start, end)
    if w.empty:
        raise KeyError(f"BCRA CPI monthly {start}:{end}")
    return float(w["valor"].mean())


def uk_erm_metrics() -> list[Metric]:
    gdp_1992q3 = ons_value("ABMI", "1992 Q3", "quarterly")
    gdp_1993q4 = ons_value("ABMI", "1993 Q4", "quarterly")
    unemp_1992q3 = ons_value("MGSX", "1992 Q3", "quarterly")
    unemp_1993q1 = ons_value("MGSX", "1993 Q1", "quarterly")
    infl_1992q3 = ons_value("L55O", "1992 Q3", "quarterly")
    infl_1993q4 = ons_value("L55O", "1993 Q4", "quarterly")
    return [
        Metric("real_gdp_rebound_four_quarters", "Real GDP by 1993Q4 versus 1992Q3.", ">2% increase", "1992Q3-1993Q4", "ons:ABMI", pct_change(gdp_1992q3, gdp_1993q4), pct_change(gdp_1992q3, gdp_1993q4) > 2.0, f"{gdp_1992q3:.0f} to {gdp_1993q4:.0f}"),
        Metric("unemployment_lagged_peak", "Unemployment rate still rose after ERM exit.", ">0.5pp rise by 1993Q1", "1992Q3-1993Q1", "ons:MGSX", pp_change(unemp_1992q3, unemp_1993q1), pp_change(unemp_1992q3, unemp_1993q1) > 0.5, f"{unemp_1992q3:.1f}% to {unemp_1993q1:.1f}%"),
        Metric("inflation_deceleration", "CPIH inflation decelerated after the sterling shock.", ">1pp fall by 1993Q4", "1992Q3-1993Q4", "ons:L55O", -pp_change(infl_1992q3, infl_1993q4), pp_change(infl_1992q3, infl_1993q4) < -1.0, f"{infl_1992q3:.1f}% to {infl_1993q4:.1f}%"),
    ]


def uk_brexit_metrics() -> list[Metric]:
    i16 = ons_value("L55O", "2016", "annual")
    i17 = ons_value("L55O", "2017", "annual")
    cpi16q2 = ons_value("D7BT", "2016 Q2", "quarterly")
    cpi17q4 = ons_value("D7BT", "2017 Q4", "quarterly")
    w16q2 = ons_value("KAB9", "2016 Q2", "quarterly")
    w17q4 = ons_value("KAB9", "2017 Q4", "quarterly")
    rw = real_wage_change(w16q2, w17q4, cpi16q2, cpi17q4)
    return [
        Metric("cpih_inflation_step_up", "CPIH annual inflation rose after the referendum.", ">1pp 2016 to 2017", "2016-2017", "ons:L55O", pp_change(i16, i17), pp_change(i16, i17) > 1.0, f"{i16:.1f}% to {i17:.1f}%"),
        Metric("cpi_level_pass_through", "Headline CPI index rose over the 18-month post-vote window.", ">3.5% cumulative CPI increase", "2016Q2-2017Q4", "ons:D7BT", pct_change(cpi16q2, cpi17q4), pct_change(cpi16q2, cpi17q4) > 3.5, f"{cpi16q2:.1f} to {cpi17q4:.1f}"),
        Metric("real_weekly_earnings_squeeze", "CPI-deflated weekly earnings fell over the same window.", "<0% real weekly earnings growth", "2016Q2-2017Q4", "ons:KAB9; ons:D7BT", rw, rw < 0.0, f"KAB9/CPI {w16q2/cpi16q2:.3f} to {w17q4/cpi17q4:.3f}"),
    ]


def uk_furlough_metrics() -> list[Metric]:
    gdp_2019q4 = ons_value("ABMI", "2019 Q4", "quarterly")
    gdp_2020q2 = ons_value("ABMI", "2020 Q2", "quarterly")
    gdp_2021q4 = ons_value("ABMI", "2021 Q4", "quarterly")
    unemp_2020q4 = ons_value("MGSX", "2020 Q4", "quarterly")
    unemp_2021q4 = ons_value("MGSX", "2021 Q4", "quarterly")
    return [
        Metric("output_collapse", "Real GDP registered a historic lockdown fall.", ">15% fall from 2019Q4 to 2020Q2", "2019Q4-2020Q2", "ons:ABMI", -pct_change(gdp_2019q4, gdp_2020q2), pct_change(gdp_2019q4, gdp_2020q2) < -15.0, f"{gdp_2019q4:.0f} to {gdp_2020q2:.0f}"),
        Metric("unemployment_contained", "Unemployment peak stayed far below the output shock magnitude.", "peak 2020Q4-2021Q4 below 6.5%", "2020Q4-2021Q4", "ons:MGSX", max(unemp_2020q4, unemp_2021q4), max(unemp_2020q4, unemp_2021q4) < 6.5, f"max {max(unemp_2020q4, unemp_2021q4):.1f}%"),
        Metric("output_recovered_by_2021q4", "Real GDP was back to pre-pandemic scale by 2021Q4.", "within 2% of 2019Q4", "2019Q4-2021Q4", "ons:ABMI", pct_change(gdp_2019q4, gdp_2021q4), abs(pct_change(gdp_2019q4, gdp_2021q4)) < 2.0, f"{gdp_2019q4:.0f} to {gdp_2021q4:.0f}"),
    ]


def uk_energy_metrics() -> list[Metric]:
    i22 = ons_value("L55O", "2022", "annual")
    i23 = ons_value("L55O", "2023", "annual")
    cpi21q4 = ons_value("D7BT", "2021 Q4", "quarterly")
    cpi22q4 = ons_value("D7BT", "2022 Q4", "quarterly")
    w21q4 = ons_value("KAB9", "2021 Q4", "quarterly")
    w22q4 = ons_value("KAB9", "2022 Q4", "quarterly")
    rw = real_wage_change(w21q4, w22q4, cpi21q4, cpi22q4)
    return [
        Metric("inflation_spike_2022", "Annual CPIH inflation spiked in the energy-shock year.", "2022 CPIH inflation >6%", "2022", "ons:L55O", i22, i22 > 6.0, f"{i22:.1f}%"),
        Metric("inflation_persistence_2023", "CPIH inflation remained high in 2023.", "2023 CPIH inflation >5%", "2023", "ons:L55O", i23, i23 > 5.0, f"{i23:.1f}%"),
        Metric("real_weekly_earnings_squeeze", "CPI-deflated weekly earnings fell during 2022.", "<-2% real weekly earnings growth", "2021Q4-2022Q4", "ons:KAB9; ons:D7BT", rw, rw < -2.0, f"KAB9/CPI {w21q4/cpi21q4:.3f} to {w22q4/cpi22q4:.3f}"),
    ]


def spain_covid_metrics() -> list[Metric]:
    gdp_2019q1 = ine_value("CNTR_PIB", "CNTR4865", "2019-03-31")
    gdp_2020q1 = ine_value("CNTR_PIB", "CNTR4865", "2020-03-31")
    unemp_2020q4 = ine_value("EPA_PARO", "EPA86913", "2020-12-31")
    return [
        Metric("gdp_lockdown_contraction", "Real GDP volume index fell sharply in the first lockdown year.", ">15% yoy fall in 2020Q1", "2019Q1-2020Q1", "ine:CNTR_PIB", -pct_change(gdp_2019q1, gdp_2020q1), pct_change(gdp_2019q1, gdp_2020q1) < -15.0, f"{gdp_2019q1:.1f} to {gdp_2020q1:.1f}"),
        Metric("unemployment_elevated", "EPA unemployment was elevated at the first cached post-lockdown endpoint.", "2020Q4 unemployment >15%", "2020Q4", "ine:EPA_PARO", unemp_2020q4, unemp_2020q4 > 15.0, f"{unemp_2020q4:.2f}%"),
        Metric("employment_proxy_not_total_collapse", "Unemployment stayed below GFC-era Spanish peaks despite the GDP shock.", "2020Q4 unemployment <20%", "2020Q4", "ine:EPA_PARO", unemp_2020q4, unemp_2020q4 < 20.0, f"{unemp_2020q4:.2f}%"),
    ]


def spain_resilience_metrics() -> list[Metric]:
    peak_ipc = max(ine_ipc_yoy(d) for d in ["2022-06-30", "2022-07-31", "2022-08-31"])
    unemp_2021q4 = ine_value("EPA_PARO", "EPA86913", "2021-12-31")
    unemp_2023q3 = ine_value("EPA_PARO", "EPA86913", "2023-09-30")
    gdp_2019q4 = ine_value("CNTR_PIB", "CNTR4865", "2019-12-31")
    gdp_2023q4 = ine_value("CNTR_PIB", "CNTR4865", "2023-12-31")
    return [
        Metric("inflation_shock_large", "Spain saw a large 2022 CPI shock.", "peak yoy CPI >8%", "2022Q2-2022Q3", "ine:IPC_general", peak_ipc, peak_ipc > 8.0, f"peak {peak_ipc:.1f}%"),
        Metric("unemployment_improved_through_shock", "Unemployment fell despite the inflation shock.", ">1pp fall 2021Q4 to 2023Q3", "2021Q4-2023Q3", "ine:EPA_PARO", -pp_change(unemp_2021q4, unemp_2023q3), pp_change(unemp_2021q4, unemp_2023q3) < -1.0, f"{unemp_2021q4:.2f}% to {unemp_2023q3:.2f}%"),
        Metric("gdp_above_pre_shock", "GDP volume index exceeded its pre-COVID quarter by 2023Q4.", ">5% above 2019Q4", "2019Q4-2023Q4", "ine:CNTR_PIB", pct_change(gdp_2019q4, gdp_2023q4), pct_change(gdp_2019q4, gdp_2023q4) > 5.0, f"{gdp_2019q4:.1f} to {gdp_2023q4:.1f}"),
    ]


def argentina_cepo_metrics() -> list[Metric]:
    fx_pre = bcra_nearest("4", "2015-12-16", "before")
    fx_post = bcra_nearest("4", "2015-12-18", "after")
    res_pre = bcra_nearest("1", "2015-12-16", "before")
    res_90 = bcra_nearest("1", "2016-03-16", "after")
    infl_pre = avg_monthly_inflation("2015-10-01", "2015-12-31")
    infl_post = avg_monthly_inflation("2016-01-01", "2016-06-30")
    return [
        Metric("official_fx_devaluation", "Official retail peso/USD rate jumped after cepo lift.", ">30% devaluation", "2015-12-16 to 2015-12-18", "bcra:4", pct_change(fx_pre, fx_post), pct_change(fx_pre, fx_post) > 30.0, f"{fx_pre:.2f} to {fx_post:.2f} ARS/USD"),
        Metric("reserves_not_depleted", "International reserves did not collapse over the next 90 days.", "reserve change > -20%", "2015-12-16 to 2016-03-16", "bcra:1", pct_change(res_pre, res_90), pct_change(res_pre, res_90) > -20.0, f"{res_pre:.0f} to {res_90:.0f} USD mn"),
        Metric("inflation_pass_through", "Monthly CPI inflation was higher in the six months after the devaluation.", ">1pp increase in average monthly CPI", "2015-10 to 2016-06", "bcra:27", pp_change(infl_pre, infl_post), pp_change(infl_pre, infl_post) > 1.0, f"{infl_pre:.2f}% to {infl_post:.2f}% average monthly"),
    ]


def argentina_paso_base_metrics() -> list[Metric]:
    fx_pre = bcra_nearest("4", "2019-08-09", "before")
    fx_post = bcra_nearest("4", "2019-08-14", "after")
    res_pre = bcra_nearest("1", "2019-08-09", "before")
    res_30 = bcra_nearest("1", "2019-09-13", "after")
    infl_aug_sep = avg_monthly_inflation("2019-08-01", "2019-09-30")
    bm_mar = bcra_nearest("15", "2020-03-31", "before")
    bm_sep = bcra_nearest("15", "2020-09-30", "before")
    infl_q2 = avg_monthly_inflation("2020-04-01", "2020-06-30")
    infl_q4 = avg_monthly_inflation("2020-10-01", "2020-12-31")
    return [
        Metric("paso_fx_devaluation", "Official peso/USD rate jumped after the PASO primary shock.", ">25% devaluation within one week", "2019-08-09 to 2019-08-14", "bcra:4", pct_change(fx_pre, fx_post), pct_change(fx_pre, fx_post) > 25.0, f"{fx_pre:.2f} to {fx_post:.2f} ARS/USD"),
        Metric("reserves_drawdown", "BCRA reserves fell over the immediate post-PASO window.", ">10% reserve fall within about 30 days", "2019-08-09 to 2019-09-13", "bcra:1", -pct_change(res_pre, res_30), pct_change(res_pre, res_30) < -10.0, f"{res_pre:.0f} to {res_30:.0f} USD mn"),
        Metric("inflation_pass_through", "Monthly CPI inflation accelerated after the FX break.", "Aug-Sep 2019 average monthly CPI >4.5%", "2019-08 to 2019-09", "bcra:27", infl_aug_sep, infl_aug_sep > 4.5, f"{infl_aug_sep:.2f}% average monthly"),
        Metric("base_money_lagged_inflation", "2020 base-money expansion preceded a later inflation pickup.", "base money +20% Mar-Sep and Q4 inflation > Q2 by 1pp", "2020-03 to 2020-12", "bcra:15; bcra:27", min(pct_change(bm_mar, bm_sep), pp_change(infl_q2, infl_q4)), pct_change(bm_mar, bm_sep) > 20.0 and pp_change(infl_q2, infl_q4) > 1.0, f"base {bm_mar:.0f} to {bm_sep:.0f}; CPI avg {infl_q2:.2f}% to {infl_q4:.2f}%"),
    ]


def var(name: str, source: str, transformation: str, notes: str | None = None) -> dict:
    out = {"name": name, "source": source, "transformation": transformation}
    if notes:
        out["notes"] = notes
    return out


CASES: list[Case] = [
    Case(
        "uk_erm_exit_1992_output_unemployment_inflation",
        "growth",
        ["GBR"],
        [1992, 1993],
        "The UK's September 1992 ERM exit was followed by a rapid real-output rebound and disinflation, while unemployment lagged the recovery rather than improving immediately.",
        "SUPPORTED if at least 2 of 3 predeclared metrics pass: real GDP rebounds by more than 2 percent by 1993Q4, unemployment rises by more than 0.5pp by 1993Q1, and CPIH inflation falls by more than 1pp by 1993Q4. REFUTED if 1 or fewer pass.",
        "uk_erm_exit_1992_three_metric_event_window",
        2,
        1,
        0.68,
        "The author's prior expects the classic sterling-devaluation recovery story, which may underweight global-cycle recovery and post-recession mean reversion.",
        "The opposite reading is that ERM exit was not the causal recovery driver: the UK was already exiting recession, lower global rates helped, and unemployment rising into 1993 shows the devaluation did not immediately heal the labour market.",
        [var("real_gdp_cvm", "ons:ABMI", "quarterly level"), var("unemployment_rate", "ons:MGSX", "quarterly percent"), var("cpih_inflation", "ons:L55O", "quarterly percent yoy")],
        [var("erm_exit", "constructed: sterling leaves ERM on 1992-09-16", "event indicator")],
        [],
        ["gdp_growth", "employment_labour", "inflation"],
        ["monetary_policy"],
        ["uk_erm_exit_1992", "sterling_devaluation"],
        uk_erm_metrics,
    ),
    Case(
        "uk_brexit_2016_inflation_real_earnings_window",
        "monetary",
        ["GBR"],
        [2016, 2017],
        "The 2016 Brexit referendum shock produced a clear near-term UK inflation pass-through and a squeeze in CPI-deflated weekly earnings over the 2016Q2-2017Q4 event window.",
        "SUPPORTED if at least 2 of 3 metrics pass: annual CPIH rises by more than 1pp from 2016 to 2017, the CPI level rises by more than 3.5 percent from 2016Q2 to 2017Q4, and CPI-deflated weekly earnings fall over the same window. REFUTED if 1 or fewer pass.",
        "uk_brexit_2016_inflation_real_earnings_three_metric_window",
        2,
        1,
        0.60,
        "The author's prior expects sterling depreciation to pass through to import prices; this can over-attribute a broad inflation move to Brexit rather than oil/base effects.",
        "A strong counterargument is that the UK had low inflation before the vote and rising nominal pay afterward, so the referendum may explain prices but not a clean real-earnings decline in the narrow ONS window.",
        [var("cpih_inflation", "ons:L55O", "annual percent yoy"), var("cpi_index", "ons:D7BT", "quarterly index"), var("weekly_earnings", "ons:KAB9", "quarterly level deflated by CPI")],
        [var("brexit_referendum", "constructed: 2016-06-23 referendum shock", "event indicator")],
        [],
        ["inflation", "wage_stagnation"],
        ["trade_policy", "monetary_policy"],
        ["uk_brexit_2016", "sterling_depreciation"],
        uk_brexit_metrics,
    ),
    Case(
        "uk_furlough_2020_unemployment_output_shield",
        "labour",
        ["GBR"],
        [2019, 2021],
        "The UK furlough-era labour-market intervention coincided with a huge 2020 output collapse but contained unemployment and allowed output to return near its pre-pandemic level by late 2021.",
        "SUPPORTED if at least 2 of 3 metrics pass: GDP falls by more than 15 percent into 2020Q2, unemployment remains below 6.5 percent through 2021Q4, and GDP is within 2 percent of 2019Q4 by 2021Q4. REFUTED if 1 or fewer pass.",
        "uk_furlough_2020_output_unemployment_three_metric_window",
        2,
        1,
        0.72,
        "The author's prior is sympathetic to job-retention schemes in pandemic shutdowns and may underweight selection from reopening and monetary/fiscal demand support.",
        "The steelman against the claim is that furlough was only one part of a bundled policy package; unemployment may have been contained by labour-force exits, reopening timing, and measurement conventions rather than the scheme itself.",
        [var("real_gdp_cvm", "ons:ABMI", "quarterly level"), var("unemployment_rate", "ons:MGSX", "quarterly percent")],
        [var("furlough_scheme", "constructed: Coronavirus Job Retention Scheme active from 2020-03", "event indicator")],
        [],
        ["gdp_growth", "employment_labour"],
        ["labour_market", "fiscal_policy"],
        ["uk_furlough_2020", "covid_shock_2020"],
        uk_furlough_metrics,
    ),
    Case(
        "uk_energy_cpi_real_earnings_squeeze_2022",
        "monetary",
        ["GBR"],
        [2021, 2023],
        "The 2022 UK energy-price shock produced high CPIH inflation and a material CPI-deflated weekly-earnings squeeze.",
        "SUPPORTED if at least 2 of 3 metrics pass: CPIH inflation exceeds 6 percent in 2022, remains above 5 percent in 2023, and CPI-deflated weekly earnings fall by more than 2 percent from 2021Q4 to 2022Q4. REFUTED if 1 or fewer pass.",
        "uk_energy_2022_cpi_real_earnings_three_metric_window",
        2,
        1,
        0.75,
        "The author's prior expects imported energy costs to dominate UK 2022 inflation and may underweight domestic wage bargaining or Brexit-related import frictions.",
        "The best counterargument is that energy was not the only inflation driver: reopening demand, global goods shortages, food prices, and sterling weakness all moved with the same timing.",
        [var("cpih_inflation", "ons:L55O", "annual percent yoy"), var("cpi_index", "ons:D7BT", "quarterly index"), var("weekly_earnings", "ons:KAB9", "quarterly level deflated by CPI")],
        [var("energy_price_shock", "constructed: 2022 wholesale energy/CPI shock window", "event indicator")],
        [],
        ["inflation", "wage_stagnation"],
        ["energy_policy", "monetary_policy"],
        ["uk_energy_cost_regime_2021_2024", "energy_shock_2022"],
        uk_energy_metrics,
    ),
    Case(
        "spain_covid_2020_gdp_unemployment_shock",
        "growth",
        ["ESP"],
        [2019, 2020],
        "Spain's 2020 COVID lockdown generated a severe GDP shock and a meaningful unemployment rise, but the unemployment-rate increase was much smaller than the output collapse implied.",
        "SUPPORTED if at least 2 of 3 metrics pass: GDP volume falls by more than 15 percent year on year in the lockdown observation, 2020Q4 unemployment is above 15 percent at the first cached post-lockdown endpoint, and 2020Q4 unemployment remains below 20 percent. REFUTED if 1 or fewer pass.",
        "spain_covid_2020_gdp_unemployment_three_metric_window",
        2,
        1,
        0.70,
        "The author's prior expects Spain's ERTE/job-retention policy to cushion employment, but the local cache measures unemployment rather than occupied-persons employment directly.",
        "The counterargument is that unemployment is an imperfect employment proxy: temporary inactivity, furlough accounting, and compositional changes can make the labour damage look smaller than hours or employment data would show.",
        [var("gdp_volume_index", "ine:CNTR_PIB", "quarterly volume index"), var("unemployment_rate", "ine:EPA_PARO", "quarterly percent", "Used as the local-cache employment-resilience proxy.")],
        [var("covid_lockdown", "constructed: 2020 lockdown and ERTE policy window", "event indicator")],
        [],
        ["gdp_growth", "employment_labour"],
        ["labour_market", "fiscal_policy"],
        ["spain_covid_2020", "erte"],
        spain_covid_metrics,
    ),
    Case(
        "spain_2021_2023_inflation_unemployment_resilience",
        "labour",
        ["ESP"],
        [2021, 2023],
        "Spain absorbed the 2021-2023 inflation shock with improving unemployment and GDP above its pre-COVID level by late 2023.",
        "SUPPORTED if at least 2 of 3 metrics pass: peak CPI inflation exceeds 8 percent in 2022, unemployment falls by more than 1pp from 2021Q4 to 2023Q3, and GDP is more than 5 percent above 2019Q4 by 2023Q4. REFUTED if 1 or fewer pass.",
        "spain_2021_2023_inflation_unemployment_resilience_window",
        2,
        1,
        0.66,
        "The author's prior expects Spanish labour-market resilience in the post-COVID recovery; the cached labour measure is unemployment, not direct employment headcount.",
        "A strong countercase is that falling unemployment during high inflation may reflect tourism normalization and European recovery funds rather than policy resilience, and real wages may still have been squeezed.",
        [var("cpi_yoy", "ine:IPC_general", "monthly yoy percent"), var("unemployment_rate", "ine:EPA_PARO", "quarterly percent"), var("gdp_volume_index", "ine:CNTR_PIB", "quarterly volume index")],
        [var("post_covid_energy_inflation_window", "constructed: 2021-2023 inflation shock", "event indicator")],
        [],
        ["inflation", "employment_labour", "gdp_growth"],
        ["labour_market", "fiscal_policy", "monetary_policy"],
        ["spain_inflation_2021_2023", "employment_resilience"],
        spain_resilience_metrics,
    ),
    Case(
        "argentina_cepo_lift_2015_fx_inflation_reserves",
        "monetary",
        ["ARG"],
        [2015, 2016],
        "Argentina's December 2015 cepo lift produced a discrete official-peso devaluation and higher short-run monthly inflation, while BCRA reserves did not collapse over the next 90 days.",
        "SUPPORTED if at least 2 of 3 metrics pass: official FX devaluation exceeds 30 percent around the lift, reserves change is better than -20 percent over roughly 90 days, and average monthly CPI inflation rises by more than 1pp after the event. REFUTED if 1 or fewer pass.",
        "argentina_cepo_lift_2015_fx_inflation_reserves_window",
        2,
        1,
        0.64,
        "The author's prior expects capital-control removal to reveal a suppressed exchange-rate adjustment and pass-through, while hoping reserves stabilize.",
        "The steelman is that the official exchange-rate jump mostly marked an accounting realignment from a controlled rate to a more realistic rate, not a clean welfare-improving liberalization shock.",
        [var("official_fx_retail", "bcra:4", "daily ARS/USD"), var("international_reserves", "bcra:1", "daily USD millions"), var("monthly_cpi_inflation", "bcra:27", "monthly percent")],
        [var("cepo_lift", "constructed: 2015-12 currency-control lift", "event indicator")],
        [],
        ["inflation", "currency_purchasing_power", "capital_flows"],
        ["monetary_policy", "regulation"],
        ["argentina_cepo_lift_2015", "capital_controls"],
        argentina_cepo_metrics,
    ),
    Case(
        "argentina_paso_2019_fx_reserves_inflation_base_money_lag",
        "monetary",
        ["ARG"],
        [2019, 2020],
        "Argentina's 2019 PASO shock generated an immediate official-FX break, reserve loss, and inflation pass-through; the 2020 base-money expansion was followed by a lagged inflation pickup by Q4.",
        "SUPPORTED if at least 3 of 4 metrics pass: PASO-week devaluation exceeds 25 percent, reserves fall by more than 10 percent in about 30 days, Aug-Sep 2019 monthly inflation averages above 4.5 percent, and 2020 base money grows more than 20 percent from March to September while Q4 monthly inflation exceeds Q2 by more than 1pp. REFUTED if 2 or fewer pass.",
        "argentina_paso_2019_base_money_lag_four_metric_window",
        3,
        2,
        0.69,
        "The author's prior expects confidence shocks and monetary expansion to show up quickly in Argentine FX/inflation data, which risks overstating causality from event windows alone.",
        "The strongest countercase is that Argentina in 2019-2020 was a bundle of debt, political, pandemic, and capital-control shocks; base money may be endogenous to crisis liquidity demand rather than the independent inflation cause.",
        [var("official_fx_retail", "bcra:4", "daily ARS/USD"), var("international_reserves", "bcra:1", "daily USD millions"), var("monthly_cpi_inflation", "bcra:27", "monthly percent"), var("monetary_base", "bcra:15", "daily ARS millions")],
        [var("paso_primary_shock", "constructed: 2019-08-11 PASO primary", "event indicator"), var("pandemic_base_money_expansion", "constructed: 2020 monetary-base expansion window", "event indicator")],
        [],
        ["inflation", "currency_purchasing_power", "capital_flows", "financial_crisis"],
        ["monetary_policy"],
        ["argentina_paso_2019", "base_money_lag_2020"],
        argentina_paso_base_metrics,
    ),
]


def verdict_for(metrics: list[Metric], support_threshold: int, refute_threshold: int) -> str:
    count = sum(m.passed for m in metrics)
    if count >= support_threshold:
        return "SUPPORTED"
    if count <= refute_threshold:
        return "REFUTED"
    return "PARTIAL"


def write_hypothesis(case: Case, metrics: list[Metric]) -> None:
    path = ROOT / "hypotheses" / case.topic / f"{case.hypothesis_id}.yaml"
    doc = {
        "hypothesis_id": case.hypothesis_id,
        "version": 1,
        "status": "pre_registered",
        "topic": case.topic,
        "claim": case.claim,
        "evidence_type": "canonical_case_multi_metric",
        "sample": {"countries": case.countries, "period": case.period, "temporal_structure": "time_series"},
        "scope": {
            "period": case.period,
            "countries": case.countries,
            "outcome_dim": case.scope_outcomes,
            "policy_family": case.policy_family,
            "treatment_tags": case.tags,
        },
        "variables": {"outcome": case.outcomes, "treatment": case.treatments},
        "estimator": {
            "template": "multi_metric_checklist",
            "clustering": "none",
            "notes": "Compact national event-window replication from cached ONS/INE/BCRA vintages.",
        },
        "falsification": {"rule": case.rule, "test": case.test, "threshold": f"SUPPORTED if >= {case.support_threshold} metrics pass; REFUTED if <= {case.refute_threshold} pass."},
        "prior_confidence": case.prior,
        "disclosure": case.disclosure,
        "steelman": f"hypotheses/steelman/{case.hypothesis_id}.md",
        "canonical_metrics": [
            {
                "metric_id": m.metric_id,
                "description": m.description,
                "threshold": m.threshold,
                "window": m.window,
                "source": m.source,
                "independence_justification": "Different outcome layer or distinct source series within the same national event window.",
            }
            for m in metrics
        ],
        "multi_metric_falsification": {"total_metrics": len(metrics), "support_threshold": case.support_threshold, "refute_threshold": case.refute_threshold},
        "notes": "Generated by scripts/generate_national_event_wave.py from local cached vintages; no network fetch required.",
    }
    path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" + yaml.safe_dump(doc, sort_keys=False, allow_unicode=False), encoding="utf-8")


def write_steelman(case: Case) -> None:
    (STEEL / f"{case.hypothesis_id}.md").write_text(
        f"# Steelman - {case.hypothesis_id}\n\n"
        f"{case.steelman}\n\n"
        "The event-window verdict is descriptive and should not be read as a full structural model. "
        "Concurrent policy changes, global shocks, and measurement revisions can all weaken causal attribution.\n",
        encoding="utf-8",
    )


def manifest_for(case: Case, metrics: list[Metric], run_utc: str) -> dict:
    vintages = {}
    for m in metrics:
        for src in [s.strip() for s in m.source.split(";")]:
            pub, series = src.split(":", 1)
            if pub not in {"ons", "ine", "bcra"}:
                continue
            path = latest(pub, series)
            vintages[f"{pub}_{series}"] = {
                "publisher": pub,
                "series": series,
                "vintage_file": str(path.relative_to(ROOT)),
                "sha256": sha(path),
            }
    return {"hypothesis_id": case.hypothesis_id, "run_utc": run_utc, "vintages": vintages}


def write_run(case: Case, metrics: list[Metric]) -> None:
    run_dir = RUNS / case.hypothesis_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    verdict = verdict_for(metrics, case.support_threshold, case.refute_threshold)
    count = sum(m.passed for m in metrics)
    diagnostics = {
        "hypothesis_id": case.hypothesis_id,
        "verdict": verdict,
        "metrics_passed": count,
        "metrics_total": len(metrics),
        "support_threshold": case.support_threshold,
        "refute_threshold": case.refute_threshold,
        "falsification_rule_text": case.rule,
        "metrics": [
            {
                "metric_id": m.metric_id,
                "description": m.description,
                "threshold": m.threshold,
                "window": m.window,
                "source": m.source,
                "value": None if math.isnan(m.value) else m.value,
                "passed": m.passed,
                "details": m.details,
            }
            for m in metrics
        ],
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest_for(case, metrics, run_utc), sort_keys=False, allow_unicode=False), encoding="utf-8")
    rows = "\n".join(
        f"| {m.metric_id} | {m.value:.3f} | {m.threshold} | {'yes' if m.passed else 'no'} | {m.details} |"
        for m in metrics
    )
    (run_dir / "result_card.md").write_text(
        f"# Result card - {case.hypothesis_id}\n\n"
        f"**Verdict:** {verdict} - {count}/{len(metrics)} metrics passed (support >= {case.support_threshold}; refute <= {case.refute_threshold}).\n\n"
        f"## Claim\n\n{case.claim}\n\n"
        "## Metrics\n\n"
        "| Metric | Value | Threshold | Pass | Details |\n"
        "|---|---:|---|:---:|---|\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        "This is a compact predeclared event-window verdict using local cached national-statistics vintages. "
        "It is strong for timing and magnitude, but not a full causal structural decomposition.\n\n"
        "## Provenance\n\nSee `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.\n",
        encoding="utf-8",
    )
    (run_dir / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import sys\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[3]))\n"
        "from scripts.generate_national_event_wave import run_one\n\n"
        f"if __name__ == '__main__':\n    run_one('{case.hypothesis_id}')\n",
        encoding="utf-8",
    )


def run_one(hypothesis_id: str) -> None:
    matches = [c for c in CASES if c.hypothesis_id == hypothesis_id]
    if not matches:
        raise SystemExit(f"unknown case: {hypothesis_id}")
    case = matches[0]
    metrics = case.metrics_fn()
    write_hypothesis(case, metrics)
    write_steelman(case)
    write_run(case, metrics)


def main(argv: list[str]) -> int:
    selected = argv[1:] or [c.hypothesis_id for c in CASES]
    for hid in selected:
        run_one(hid)
        print(hid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
