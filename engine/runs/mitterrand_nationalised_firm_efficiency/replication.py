#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "mitterrand_nationalised_firm_efficiency"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRIES = ["FRA", "BEL", "DEU", "ESP", "GBR", "ITA", "NLD"]
PEERS = [c for c in COUNTRIES if c != "FRA"]
START_YEAR = 1981
END_YEAR = 1986


def latest(series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / "pwt").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing pwt:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pwt(path: Path, name: str) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["country_iso3"].isin(COUNTRIES)].dropna(subset=["year"])
    return df[["country_iso3", "country", "year", "value"]].rename(columns={"value": name})


def metric_growth(df: pd.DataFrame, metric: str) -> dict[str, float]:
    wide = df.pivot_table(index="year", columns="country_iso3", values=metric)
    return {
        country: float(wide.loc[END_YEAR, country] / wide.loc[START_YEAR, country] - 1.0)
        for country in COUNTRIES
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "rtfpna": latest("rtfpna"),
        "rgdpo_per_emp": latest("rgdpo_per_emp"),
        "csh_i": latest("csh_i"),
    }

    tfp = load_pwt(paths["rtfpna"], "tfp_index")
    out_worker = load_pwt(paths["rgdpo_per_emp"], "output_per_worker")
    investment = load_pwt(paths["csh_i"], "investment_share")
    panel = tfp.merge(out_worker, on=["country_iso3", "country", "year"], how="outer")
    panel = panel.merge(investment, on=["country_iso3", "country", "year"], how="outer")

    required = panel[panel["year"].isin([START_YEAR, END_YEAR])]
    method_valid = bool(
        set(required["country_iso3"]) >= set(COUNTRIES)
        and required.groupby("country_iso3")[["tfp_index", "output_per_worker"]].apply(lambda x: x.notna().all().all()).all()
    )

    if method_valid:
        tfp_growth = metric_growth(panel, "tfp_index")
        output_worker_growth = metric_growth(panel, "output_per_worker")
        investment_growth = metric_growth(panel, "investment_share")
        tfp_peer_median = float(np.median([tfp_growth[c] for c in PEERS]))
        output_peer_median = float(np.median([output_worker_growth[c] for c in PEERS]))
        inv_peer_median = float(np.median([investment_growth[c] for c in PEERS]))
        tfp_gap_pp = float((tfp_growth["FRA"] - tfp_peer_median) * 100.0)
        output_gap_pp = float((output_worker_growth["FRA"] - output_peer_median) * 100.0)
        inv_gap_pp = float((investment_growth["FRA"] - inv_peer_median) * 100.0)
        if tfp_gap_pp >= -5.0 and output_gap_pp >= -5.0:
            verdict_label = "PARTIAL"
            scope_note = "macro productivity proxy supports no-collapse pattern; firm-level nationalised cohort remains data-gated"
        elif tfp_gap_pp <= -10.0 or output_gap_pp <= -10.0:
            verdict_label = "REFUTED"
            scope_note = "macro productivity proxy shows collapse relative to peers"
        else:
            verdict_label = "PARTIAL"
            scope_note = "macro productivity proxy is mixed"
        verdict_reason = (
            f"FRA TFP growth {tfp_growth['FRA'] * 100:.1f}% vs peer median {tfp_peer_median * 100:.1f}% "
            f"(gap {tfp_gap_pp:.1f}pp); output/worker {output_worker_growth['FRA'] * 100:.1f}% vs "
            f"{output_peer_median * 100:.1f}% (gap {output_gap_pp:.1f}pp), 1981-1986"
        )
    else:
        tfp_growth = output_worker_growth = investment_growth = {}
        tfp_peer_median = output_peer_median = inv_peer_median = None
        tfp_gap_pp = output_gap_pp = inv_gap_pp = None
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
        scope_note = "missing required PWT endpoints"
        verdict_reason = "missing 1981 or 1986 PWT endpoints for France and peer countries"

    panel.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": f"{verdict_label} \u2014 {verdict_reason}",
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "method_valid": method_valid,
        "test": "pwt_france_macro_productivity_vs_western_europe_peers_1981_1986",
        "evidence_type": "macro_productivity_proxy",
        "scope_note": scope_note,
        "causal_attribution": "not identified; no firm-level nationalised-vs-private panel is present locally",
        "estimate": {
            "tfp_growth_1981_1986": tfp_growth,
            "output_per_worker_growth_1981_1986": output_worker_growth,
            "investment_share_growth_1981_1986": investment_growth,
            "tfp_peer_median_growth": tfp_peer_median,
            "output_per_worker_peer_median_growth": output_peer_median,
            "investment_share_peer_median_growth": inv_peer_median,
            "tfp_gap_vs_peer_median_pp": tfp_gap_pp,
            "output_per_worker_gap_vs_peer_median_pp": output_gap_pp,
            "investment_share_gap_vs_peer_median_pp": inv_gap_pp,
        },
        "thresholds": {
            "partial_support_min_gap_each_metric_pp": -5.0,
            "refute_gap_any_metric_pp": -10.0,
        },
        "data_status": {
            "variables_loaded": [
                {"name": "tfp_index", "source": "pwt:rtfpna", "publisher": "pwt"},
                {"name": "output_per_worker", "source": "pwt:rgdpo_per_emp", "publisher": "pwt"},
                {"name": "investment_share", "source": "pwt:csh_i", "publisher": "pwt"},
            ],
            "variables_missing": [
                {"name": "firm_level_tfp", "source": "INSEE BRN/SUSE"},
                {"name": "nationalised_firm_indicator", "source": "constructed firm cohort"},
            ],
        },
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/mitterrand_nationalised_firm_efficiency/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict_label}\n"
        f"reason: {verdict_reason}\n"
        "methodology_note: PWT macro-productivity proxy; firm-level nationalised cohort absent\n"
        "vintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict_label} - {verdict_reason}\n\n"
        "## Predeclared Test\n\n"
        "The v2 diagnostic compares France's 1981-1986 PWT TFP and output-per-worker growth with the "
        "Belgium/Germany/Spain/UK/Italy/Netherlands peer median. It supports only the macro no-collapse "
        "pattern if France is no more than 5 percentage points below the peer median on both metrics.\n\n"
        "## Scope Note\n\n"
        "This cannot identify firm-level treatment effects for the 1981-82 nationalised firms. Full support "
        "requires the firm-level nationalised-vs-private peer panel specified in the original design.\n"
    )
    print(f"verdict: {verdict_label} - {verdict_reason}")


if __name__ == "__main__":
    main()
