#!/usr/bin/env python3
"""Replication — UK Thatcher-era labour-share first-order gate."""
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
HID = "uk_thatcher_era_labour_share_decline_1979_1990"
OUT_DIR = ROOT / "engine" / "runs" / HID
COUNTRY = "GBR"
START_YEAR = 1979
END_YEAR = 1990


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


def load_panel(pub: str, series: str) -> pd.DataFrame:
    path = latest(pub, series)
    df = pq.read_table(path).to_pandas()
    out = df[df["country_iso3"].eq(COUNTRY)][["year", "value"]].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["year", "value"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    labsh_path = latest("pwt", "labsh")
    labsh = load_panel("pwt", "labsh")
    window = labsh[labsh["year"].between(START_YEAR, END_YEAR)].sort_values("year")
    start = float(window.loc[window["year"].eq(START_YEAR), "value"].iloc[0])
    end = float(window.loc[window["year"].eq(END_YEAR), "value"].iloc[0])
    change = end - start

    if change > -0.02:
        verdict_label = "refuted"
        verdict = (
            f"refuted — PWT labsh for GBR does not show the registered Thatcher-era "
            f"labour-share decline: {START_YEAR}={start*100:.1f}%, "
            f"{END_YEAR}={end*100:.1f}%, change {change*100:+.1f}pp."
        )
    elif change <= -0.03:
        verdict_label = "partial"
        verdict = (
            f"partial — PWT labsh falls {change*100:+.1f}pp, clearing the first-order "
            "decline gate, but local ONS sector shift-share data are still unavailable."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            f"weakened — PWT labsh falls only {change*100:+.1f}pp, between the refutation "
            "and support bands."
        )

    rows = [
        {"year": int(r.year), "labour_share": float(r.value)}
        for r in window.itertuples()
    ]
    manifest = {
        "labsh": {
            "publisher": "pwt",
            "series": "labsh",
            "vintage_file": str(labsh_path.relative_to(ROOT)),
            "sha256": sha256(labsh_path),
        }
    }
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "country": COUNTRY,
        "start_year": START_YEAR,
        "end_year": END_YEAR,
        "labsh_start": start,
        "labsh_end": end,
        "change": change,
        "refute_threshold_change": -0.02,
        "support_threshold_change": -0.03,
        "series": rows,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"inputs:\n  labsh: {manifest['labsh']['vintage_file']}\n  sha256: {manifest['labsh']['sha256']}\n"
    )
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Registered First-Order Gate",
                "",
                "- Data: Penn World Table `labsh`, GBR.",
                "- Refute if 1990 minus 1979 labour share is greater than -2pp.",
                "- Full attribution to Thatcher reform channels still requires sector shift-share data.",
                "",
                "## Key Numbers",
                "",
                f"- 1979 labour share: {start*100:.2f}%.",
                f"- 1990 labour share: {end*100:.2f}%.",
                f"- Change: {change*100:+.2f}pp.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
