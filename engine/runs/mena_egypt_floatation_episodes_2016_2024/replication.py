#!/usr/bin/env python3
"""Annual WDI repair for Egypt floatation episodes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HID = "mena_egypt_floatation_episodes_2016_2024"
EVENTS = [2016, 2022, 2024]


def latest(publisher: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / publisher).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {publisher}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vintage_meta(series: str, label: str) -> tuple[Path, dict]:
    path = latest("world_bank_wdi", series)
    return path, {
        "publisher": "world_bank_wdi",
        "series": series,
        "label": label,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def load_egypt(path: Path, name: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return (
        df[df["country_iso3"].eq("EGY")][["year", "value"]]
        .dropna()
        .assign(year=lambda d: d["year"].astype(int))
        .rename(columns={"value": name})
    )


def value_at(series: dict[int, float], year: int) -> float | None:
    return series.get(year)


def run() -> int:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fx_path, fx_meta = vintage_meta("PA.NUS.FCRF", "Official LCU/USD exchange rate")
    reserves_path, reserves_meta = vintage_meta("FI.RES.TOTL.CD", "Total reserves excluding gold, USD")
    cpi_path, cpi_meta = vintage_meta("FP.CPI.TOTL.ZG", "CPI inflation")
    ca_path, ca_meta = vintage_meta("BN.CAB.XOKA.GD.ZS", "Current-account balance percent of GDP")

    panel = (
        load_egypt(fx_path, "official_usd_rate")
        .merge(load_egypt(reserves_path, "fx_reserves_usd"), on="year", how="outer")
        .merge(load_egypt(cpi_path, "cpi_inflation_yoy"), on="year", how="outer")
        .merge(load_egypt(ca_path, "current_account_gdp"), on="year", how="outer")
        .sort_values("year")
    )
    fx = dict(zip(panel["year"], panel["official_usd_rate"]))
    reserves = dict(zip(panel["year"], panel["fx_reserves_usd"]))
    cpi = dict(zip(panel["year"], panel["cpi_inflation_yoy"]))

    rows = []
    for event in EVENTS:
        pre_year = event - 1
        post_year = event + 1 if event < 2024 else 2024
        pre_res = value_at(reserves, pre_year)
        post_res = value_at(reserves, post_year)
        pre_fx = value_at(fx, pre_year)
        post_fx = value_at(fx, post_year)
        pre_cpi = value_at(cpi, pre_year)
        cpi_candidates = [
            value_at(cpi, y)
            for y in (event, post_year)
            if value_at(cpi, y) is not None
        ]
        peak_cpi = max(cpi_candidates) if cpi_candidates else None
        reserve_ratio = post_res / pre_res if pre_res and post_res else None
        fx_ratio = post_fx / pre_fx if pre_fx and post_fx else None
        cpi_acceleration = peak_cpi - pre_cpi if peak_cpi is not None and pre_cpi is not None else None
        rows.append(
            {
                "event_year": event,
                "pre_year": pre_year,
                "post_year_used": post_year,
                "post_window_incomplete": bool(event == 2024),
                "reserve_ratio_post_to_pre": reserve_ratio,
                "official_fx_rate_ratio_post_to_pre": fx_ratio,
                "cpi_peak_minus_pre_pp": cpi_acceleration,
                "reserve_gate_ge_1_20": bool(reserve_ratio is not None and reserve_ratio >= 1.20),
                "official_devaluation_observed_ge_20pct": bool(fx_ratio is not None and fx_ratio >= 1.20),
                "inflation_gate_ge_8pp": bool(cpi_acceleration is not None and cpi_acceleration >= 8.0),
            }
        )

    reserve_pass = sum(r["reserve_gate_ge_1_20"] for r in rows)
    fx_pass = sum(r["official_devaluation_observed_ge_20pct"] for r in rows)
    inflation_pass = sum(r["inflation_gate_ge_8pp"] for r in rows)
    parallel_gap_loaded = False
    homogeneous = reserve_pass == len(rows) and inflation_pass == len(rows)

    if reserve_pass == 3 and inflation_pass == 3 and parallel_gap_loaded and homogeneous:
        verdict = "SUPPORTED"
        reason = "all annual WDI gates and parallel-gap gate clear"
    elif fx_pass == 3 and (reserve_pass >= 2 or inflation_pass >= 2):
        verdict = "PARTIAL"
        reason = "annual WDI confirms repeated official devaluation and some reserve/inflation response, but reserve/inflation dynamics are heterogeneous and the parallel-rate gap is not locally loaded"
    else:
        verdict = "REFUTED"
        reason = "annual WDI fails the recurrent reserve and inflation-response pattern"

    estimate = {
        "method": "annual WDI event-window repair; post year is t+1 except 2024 where no 2025 vintage is loaded",
        "events": rows,
        "reserve_gate_pass_count": int(reserve_pass),
        "official_devaluation_gate_pass_count": int(fx_pass),
        "inflation_gate_pass_count": int(inflation_pass),
        "parallel_official_rate_gap_loaded": parallel_gap_loaded,
        "homogeneous_annual_pattern": bool(homogeneous),
        "proxy_note": "The registered monthly six-month and parallel-market-rate gates are not locally loaded; this annual repair tests official FX, reserves, and CPI only.",
    }
    vintages = {
        "official_usd_rate": fx_meta,
        "fx_reserves_usd": reserves_meta,
        "cpi_inflation_yoy": cpi_meta,
        "current_account_gdp": ca_meta,
    }
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "event_study_annual_wdi_repair",
        "estimate": estimate,
        "vintages": vintages,
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (OUT / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": HID,
                "run_utc": run_utc,
                "verdict_label": verdict,
                "runner": f"engine/runs/{HID}/replication.py",
                "vintages": vintages,
                "events": rows,
                "proxy_note": estimate["proxy_note"],
            },
            sort_keys=False,
        )
    )
    lines = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Annual Event Gates",
        "",
        "| Event | FX ratio | Reserve ratio | CPI acceleration | Gates |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        gates = []
        if row["official_devaluation_observed_ge_20pct"]:
            gates.append("FX")
        if row["reserve_gate_ge_1_20"]:
            gates.append("reserves")
        if row["inflation_gate_ge_8pp"]:
            gates.append("inflation")
        if row["post_window_incomplete"]:
            gates.append("2025 pending")
        lines.append(
            f"| {row['event_year']} | {row['official_fx_rate_ratio_post_to_pre']:.2f} | "
            f"{row['reserve_ratio_post_to_pre']:.2f} | {row['cpi_peak_minus_pre_pp']:+.1f} pp | "
            f"{', '.join(gates) or 'none'} |"
        )
    lines.extend(["", "## Caveat", estimate["proxy_note"]])
    (OUT / "result_card.md").write_text("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
