"""Build a deterministic calendar year-trend vintage for panel trend tests.

Emits `data/vintages/trend/calendar_year_trend@<utc>.parquet` with the
canonical (country_iso3, year, value) layout, where `value = year - 1980`.
NB: served under the plain `trend` publisher (NOT `derived:`, which is a
meta-prefix the runner constructs in-code rather than loading from a file).
Used as the treatment regressor in panel-FE trend specs (e.g. the WID
top-wealth-share post-1980 rise test), so a positive, significant
coefficient on this series == "the outcome trended up over the panel".

The series is purely deterministic (no external fetch); the country roster
mirrors the advanced-economy set used by r_minus_g_wealth_income_ratio_post_1980
and is intersected with whatever wid_clean materialises so the trend source
always aligns with the outcome panel.
"""
from __future__ import annotations

import glob
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
VINTAGES = ROOT / "data" / "vintages"
MANIFESTS = ROOT / "data" / "manifests"

ADVANCED = [
    "USA", "GBR", "FRA", "DEU", "ITA", "ESP", "NLD", "SWE", "JPN",
    "CAN", "AUS", "CHE", "BEL", "AUT", "DNK", "FIN", "NOR", "IRL",
]
BASE_YEAR = 1980
END_YEAR = 2024


def main() -> None:
    # Align the roster to countries actually present in the wid_clean outcome.
    top01 = sorted(glob.glob(str(VINTAGES / "wid_clean" / "top01_wealth_share@*.parquet")))
    if top01:
        present = set(pd.read_parquet(top01[-1])["country_iso3"].unique())
        countries = [c for c in ADVANCED if c in present]
    else:
        countries = list(ADVANCED)

    rows = [
        {"country_iso3": c, "year": y, "value": float(y - BASE_YEAR)}
        for c in countries
        for y in range(BASE_YEAR, END_YEAR + 1)
    ]
    df = pd.DataFrame(rows)

    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_dir = VINTAGES / "trend"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"calendar_year_trend@{utc}.parquet"
    df.to_parquet(out_path, index=False)

    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    manifest = {
        "publisher": "trend",
        "series": "calendar_year_trend",
        "source": "deterministic (value = year - 1980)",
        "vintage_utc": utc,
        "sha256": sha,
        "rows": len(df),
        "countries": countries,
        "period": [BASE_YEAR, END_YEAR],
        "built_by": "scripts/_build_year_trend_vintage.py",
        "purpose": "treatment regressor for panel-FE trend specs",
    }
    (MANIFESTS / f"fetch_run_{utc}_calendar_year_trend.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False)
    )
    print(f"wrote {out_path} ({len(df)} rows, {len(countries)} countries) sha={sha[:12]}")


if __name__ == "__main__":
    main()
