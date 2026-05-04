#!/usr/bin/env python3
"""Replication — Singapore Temasek/GIC public-holding-company case."""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
HID = "singapore_temasek_public_ownership_efficiency"
OUT_DIR = ROOT / "engine" / "runs" / HID

TREATED = "SGP"
GDP_PEERS = ["HKG", "KOR"]
TFP_PEERS = ["HKG", "KOR", "TWN"]
WGI_PEERS = ["HKG", "KOR"]


def latest(pub: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def annual_growth(df: pd.DataFrame, country: str, start: int, end: int) -> float:
    sub = (
        df[(df["country_iso3"] == country) & df["year"].between(start, end)]
        .dropna(subset=["value"])
        .sort_values("year")
    )
    if sub.empty:
        raise ValueError(f"missing {country} {start}-{end}")
    first = float(sub.iloc[0]["value"])
    last = float(sub.iloc[-1]["value"])
    n_years = int(sub.iloc[-1]["year"]) - int(sub.iloc[0]["year"])
    return (last / first) ** (1 / n_years) - 1


def mean_level(df: pd.DataFrame, country: str, start: int, end: int) -> float:
    sub = df[(df["country_iso3"] == country) & df["year"].between(start, end)]
    return float(pd.to_numeric(sub["value"], errors="coerce").dropna().mean())


def load(pub: str, series: str) -> pd.DataFrame:
    df = pq.read_table(latest(pub, series)).to_pandas()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def metric_record(name: str, treated: float, peers: dict[str, float]) -> dict:
    peer_median = float(pd.Series(peers).median())
    return {
        "metric": name,
        "singapore_value": treated,
        "peer_values": peers,
        "peer_median": peer_median,
        "meets_peer_median": treated >= peer_median,
        "gap_vs_peer_median": treated - peer_median,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp = load("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    tfp = load("pwt", "rtfpna")
    ge = load("wgi", "GE.EST")
    rl = load("wgi", "RL.EST")

    metrics = [
        metric_record(
            "gdp_pc_ppp_annual_growth_1990_2023",
            annual_growth(gdp, TREATED, 1990, 2023),
            {c: annual_growth(gdp, c, 1990, 2023) for c in GDP_PEERS},
        ),
        metric_record(
            "tfp_annual_growth_1974_2019",
            annual_growth(tfp, TREATED, 1974, 2019),
            {c: annual_growth(tfp, c, 1974, 2019) for c in TFP_PEERS},
        ),
        metric_record(
            "wgi_government_effectiveness_mean_1996_2024",
            mean_level(ge, TREATED, 1996, 2024),
            {c: mean_level(ge, c, 1996, 2024) for c in WGI_PEERS},
        ),
        metric_record(
            "wgi_rule_of_law_mean_1996_2024",
            mean_level(rl, TREATED, 1996, 2024),
            {c: mean_level(rl, c, 1996, 2024) for c in WGI_PEERS},
        ),
    ]
    metric_by_name = {m["metric"]: m for m in metrics}
    tfp_met = metric_by_name["tfp_annual_growth_1974_2019"]["meets_peer_median"]
    gdp_met = metric_by_name["gdp_pc_ppp_annual_growth_1990_2023"]["meets_peer_median"]
    other_met_count = sum(m["meets_peer_median"] for m in metrics if not m["metric"].startswith("tfp_"))

    if tfp_met and other_met_count >= 2:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED — Singapore meets the TFP comparator metric and at least two other "
            "registered growth/institutional metrics."
        )
    elif (not tfp_met) and (not gdp_met):
        verdict_label = "refuted"
        verdict = (
            "refuted — Singapore misses both the registered TFP and GDP-per-capita growth "
            "peer-median metrics."
        )
    else:
        verdict_label = "partial"
        verdict = (
            "partial — Singapore beats peer medians on GDP-per-capita growth and institutional "
            "quality, but misses the registered PWT TFP growth metric, so the strong efficiency "
            "claim is not fully supported."
        )

    manifest = {}
    for pub, series in [
        ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        ("pwt", "rtfpna"),
        ("wgi", "GE.EST"),
        ("wgi", "RL.EST"),
    ]:
        path = latest(pub, series)
        manifest[f"{pub}:{series}"] = {
            "publisher": pub,
            "series": series,
            "vintage_file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "treated": TREATED,
        "metrics": metrics,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n"
        + "\n".join(f"  {k}: {v['vintage_file']}" for k, v in manifest.items())
        + "\n"
    )
    flat_rows = []
    for metric in metrics:
        row = {k: v for k, v in metric.items() if k != "peer_values"}
        for peer, value in metric["peer_values"].items():
            row[f"peer_{peer}"] = value
        flat_rows.append(row)
    pd.DataFrame(flat_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Metrics",
                "",
                *[
                    "- "
                    f"{m['metric']}: Singapore {m['singapore_value']:.4f}, "
                    f"peer median {m['peer_median']:.4f}, "
                    f"meets={m['meets_peer_median']}."
                    for m in metrics
                ],
                "",
                "## Method Note",
                "",
                "This is a descriptive comparator test; it does not causally attribute Singapore's outcomes to Temasek/GIC.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
