#!/usr/bin/env python3
"""Exact replication for trade_lib_bangladesh_apparel_eu_eba_2008."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

HID = "trade_lib_bangladesh_apparel_eu_eba_2008"
ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_wdi(series: str) -> tuple[pd.DataFrame, dict]:
    matches = sorted(WDI.glob(f"{series}@*.parquet"), key=lambda p: p.name)
    if not matches:
        raise FileNotFoundError(f"missing WDI vintage for {series}")
    path = matches[-1]
    return pd.read_parquet(path), {
        "publisher": "world_bank_wdi",
        "series": series,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def window_mean(df: pd.DataFrame, country: str, start: int, end: int) -> dict:
    sub = df[
        (df["country_iso3"].eq(country))
        & (df["year"].astype(int) >= start)
        & (df["year"].astype(int) <= end)
    ].dropna(subset=["value"])
    if sub.empty:
        raise ValueError(f"missing {country} window {start}-{end}")
    return {
        "country": country,
        "window": [start, end],
        "mean": float(sub["value"].mean()),
        "n_years": int(sub["year"].nunique()),
        "year_min": int(sub["year"].min()),
        "year_max": int(sub["year"].max()),
    }


def window_delta(df: pd.DataFrame, country: str) -> dict:
    pre = window_mean(df, country, 2000, 2004)
    post = window_mean(df, country, 2015, 2019)
    return {
        "country": country,
        "pre": pre,
        "post": post,
        "delta_pp": float(post["mean"] - pre["mean"]),
    }


def verdict_from(comparison: dict) -> tuple[str, str]:
    bgd_delta = comparison["manufacturing_share"]["bgd_delta"]["delta_pp"]
    pak_delta = comparison["manufacturing_share"]["pak_delta"]["delta_pp"]
    diff = comparison["manufacturing_share"]["bgd_minus_pak_delta_pp"]
    if pak_delta >= bgd_delta:
        return (
            "REFUTED",
            f"PAK matched or exceeded BGD manufacturing-share change ({pak_delta:+.2f}pp vs {bgd_delta:+.2f}pp)",
        )
    if bgd_delta >= 4.0 and diff >= 2.0:
        return (
            "SUPPORTED",
            f"BGD manufacturing share rose {bgd_delta:+.2f}pp and beat PAK by {diff:+.2f}pp",
        )
    return (
        "PARTIAL",
        f"BGD manufacturing share rose {bgd_delta:+.2f}pp with BGD-PAK differential {diff:+.2f}pp",
    )


def main() -> int:
    manufacturing, manufacturing_meta = latest_wdi("NV.IND.MANF.ZS")
    exports, exports_meta = latest_wdi("NE.EXP.GNFS.ZS")
    real_mfg, real_mfg_meta = latest_wdi("NV.IND.MANF.KD")

    mfg_bgd = window_delta(manufacturing, "BGD")
    mfg_pak = window_delta(manufacturing, "PAK")
    exp_bgd = window_delta(exports, "BGD")
    exp_pak = window_delta(exports, "PAK")

    comparison = {
        "shape": "bangladesh_eba_exact_window_gate",
        "manufacturing_share": {
            "source": "world_bank_wdi:NV.IND.MANF.ZS",
            "bgd_delta": mfg_bgd,
            "pak_delta": mfg_pak,
            "bgd_minus_pak_delta_pp": float(mfg_bgd["delta_pp"] - mfg_pak["delta_pp"]),
            "support_gate_bgd_delta_ge_4pp": bool(mfg_bgd["delta_pp"] >= 4.0),
            "support_gate_bgd_minus_pak_ge_2pp": bool(
                mfg_bgd["delta_pp"] - mfg_pak["delta_pp"] >= 2.0
            ),
            "refute_gate_pak_matched_or_exceeded_bgd": bool(
                mfg_pak["delta_pp"] >= mfg_bgd["delta_pp"]
            ),
        },
        "exports_share_context": {
            "source": "world_bank_wdi:NE.EXP.GNFS.ZS",
            "bgd_delta": exp_bgd,
            "pak_delta": exp_pak,
            "bgd_minus_pak_delta_pp": float(exp_bgd["delta_pp"] - exp_pak["delta_pp"]),
        },
    }
    verdict_label, verdict_reason = verdict_from(comparison)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    manifest = {
        "hypothesis_id": HID,
        "run_utc": now,
        "runner": "engine/runs/trade_lib_bangladesh_apparel_eu_eba_2008/replication.py",
        "verdict_label": verdict_label,
        "vintages": {
            "manufacturing_share_of_gdp": manufacturing_meta,
            "exports_pct_gdp_context": exports_meta,
            "real_manufacturing_value_added_context": real_mfg_meta,
        },
    }
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    diagnostics = {
        "verdict": f"{verdict_label} - {verdict_reason}",
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "hypothesis_id": HID,
        "template": "descriptive_exact_bangladesh_eba",
        "runner": "engine/runs/trade_lib_bangladesh_apparel_eu_eba_2008/replication.py",
        "comparison": comparison,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "outcome",
                    "name": "merchandise_exports_pct_gdp",
                    "source": "world_bank_wdi:NE.EXP.GNFS.ZS",
                    "publisher": "world_bank_wdi",
                    "n_rows": int(exports["value"].notna().sum()),
                },
                {
                    "role": "outcome",
                    "name": "log_manufacturing_value_added",
                    "source": "world_bank_wdi:NV.IND.MANF.KD",
                    "publisher": "world_bank_wdi",
                    "n_rows": int(real_mfg["value"].notna().sum()),
                },
                {
                    "role": "outcome",
                    "name": "manufacturing_share_of_gdp",
                    "source": "world_bank_wdi:NV.IND.MANF.ZS",
                    "publisher": "world_bank_wdi",
                    "n_rows": int(manufacturing["value"].notna().sum()),
                },
            ],
            "variables_missing": [],
        },
        "run_utc": now,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    card = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {verdict_label} - {verdict_reason}",
        "",
        "## Exact Gate",
        "- SUPPORTED if Bangladesh manufacturing-share-of-GDP rises by at least +4pp from 2000-2004 to 2015-2019 and beats Pakistan by at least +2pp.",
        "- REFUTED if Pakistan matches or exceeds Bangladesh's manufacturing-share change.",
        "",
        "## Manufacturing Share",
        f"- BGD delta: `{mfg_bgd['delta_pp']:+.3f}` pp.",
        f"- PAK delta: `{mfg_pak['delta_pp']:+.3f}` pp.",
        f"- BGD minus PAK: `{comparison['manufacturing_share']['bgd_minus_pak_delta_pp']:+.3f}` pp.",
        "",
        "## Export-Share Context",
        f"- BGD exports/GDP delta: `{exp_bgd['delta_pp']:+.3f}` pp.",
        f"- PAK exports/GDP delta: `{exp_pak['delta_pp']:+.3f}` pp.",
        f"- BGD minus PAK: `{comparison['exports_share_context']['bgd_minus_pak_delta_pp']:+.3f}` pp.",
        "",
        "## Vintages",
        f"- Manufacturing share: `{manufacturing_meta['vintage_file']}`.",
        f"- Exports/GDP context: `{exports_meta['vintage_file']}`.",
        f"- Real manufacturing VA context: `{real_mfg_meta['vintage_file']}`.",
        "",
        f"_Generated by run-local exact replication at {now}_",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"{HID}: {verdict_label} - {verdict_reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
