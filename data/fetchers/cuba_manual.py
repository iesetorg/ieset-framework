"""Cuba manual data fetcher.

Hand-curated Cuba-specific series sourced from academic monographs (Mesa-Lago,
"Cuba's Economy" 2014 and follow-ups), Cuban official gazette regulations
(Resoluciones MINCIN, BCC, MFP), and journalistic reporting (OnCuba, 14ymedio,
Reuters/AP archive). Each series has a provenance markdown under
data/manual/cuba/<series>.md documenting the citation chain.

Series shipped:

  libreta_persistence       — years_active=62 (1962-present, single row CUB/2023)
  monetary_regime_events    — count=4 (1961, 1994, 2004, 2021), each as a row
  mlc_retail_persistence    — years_active=5 (2019-present, single row CUB/2024)

The fetcher reads YAML/JSON inputs under data/manual/cuba/ and writes a tidy
parquet under data/vintages/cuba_manual/<series>@<utc>.parquet with columns
(country_iso3, year, value).

Threshold-evaluation note: each series stores the *cumulative* indicator
value (years active, event count) rather than a time-series, so when the
runner looks up "max in window" it gets the indicator directly. This keeps
the runner code path unchanged.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import MANUAL_ROOT, ManualDropError

LICENSE = "academic_citation + Cuban official gazette (public-domain regulations)"
METHODOLOGY = "data/manual/cuba/_provenance.md"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ManualDropError(f"missing {path.relative_to(MANUAL_ROOT.parent.parent)}")
    return yaml.safe_load(path.read_text())


def _series_libreta_persistence(reference_year: int = 2023) -> pd.DataFrame:
    """Cuban libreta (ration card) has been in continuous force since 1962.
    Value = number of continuous years active as of reference_year."""
    data = _load_yaml(MANUAL_ROOT / "cuba" / "libreta_persistence.yaml")
    start = int(data["start_year"])
    end = int(data.get("end_year") or reference_year)
    years_active = end - start + 1
    return pd.DataFrame(
        [{"country_iso3": "CUB", "year": end, "value": float(years_active)}]
    )


def _series_monetary_regime_events() -> pd.DataFrame:
    """Each major monetary-regime change is a row. The runner's 'count'
    interpretation falls back to max-value, so we ALSO emit a synthetic
    summary row with value = total count (so the threshold >=2 evaluates
    against the count). Real event rows precede it for provenance."""
    data = _load_yaml(MANUAL_ROOT / "cuba" / "monetary_regime_events.yaml")
    events = data["events"]
    rows = [
        {"country_iso3": "CUB", "year": int(e["year"]), "value": 1.0}
        for e in events
    ]
    # Summary row: place the cumulative count at the latest event year so the
    # window-aware runner picks it up as the max-in-window observation.
    last_year = max(int(e["year"]) for e in events)
    rows.append({"country_iso3": "CUB", "year": last_year, "value": float(len(events))})
    return pd.DataFrame(rows)


def _series_private_sector_years_under_25pct() -> pd.DataFrame:
    """Cuban private-sector employment share — emit the COUNT of years in
    1960-2023 with share <25% as the indicator value (matches the metric's
    "for >=40 years of the window" threshold semantics)."""
    data = _load_yaml(MANUAL_ROOT / "cuba" / "private_sector_share.yaml")
    obs = sorted(data["observations"], key=lambda o: o["year"])
    # Reconstruct annual series via piecewise-linear interpolation between
    # the dated observations.
    years = list(range(1960, 2024))
    annual = {}
    for y in years:
        # find bracketing observations
        prev = next((o for o in reversed(obs) if o["year"] <= y), None)
        nxt = next((o for o in obs if o["year"] >= y), None)
        if prev is None and nxt is not None:
            v = nxt["value"]
        elif nxt is None and prev is not None:
            v = prev["value"]
        elif prev["year"] == nxt["year"] or prev["year"] == y:
            v = prev["value"]
        else:
            # linear interp
            span = nxt["year"] - prev["year"]
            frac = (y - prev["year"]) / span if span else 0
            v = prev["value"] + frac * (nxt["value"] - prev["value"])
        # Pre-1981 default: assume identical-to-1981 (revolutionary suppression
        # of private sector was largely complete by 1968 with the
        # "Revolutionary Offensive" expropriations).
        if y < 1981:
            v = 4.4  # Mesa-Lago 2014 baseline
        annual[y] = v

    years_under = sum(1 for y, v in annual.items() if v < 25.0)
    # Emit a single summary row at the latest year. Value = years_under_25pct.
    return pd.DataFrame(
        [{"country_iso3": "CUB", "year": 2023, "value": float(years_under)}]
    )


def _series_emigration_share_pct() -> pd.DataFrame:
    """Cuban cumulative emigrant stock as % of notional population
    (residents + diaspora). Sourced from UN DESA IMS 2020 + Pew/MPI."""
    data = _load_yaml(MANUAL_ROOT / "cuba" / "emigration_share_pct.yaml")
    rows = [
        {"country_iso3": "CUB", "year": int(o["year"]), "value": float(o["value"])}
        for o in data["observations"]
    ]
    return pd.DataFrame(rows)


def _series_food_import_caloric_share() -> pd.DataFrame:
    """Cuban food-supply import share by caloric value, point-estimate
    citations from Mesa-Lago 2022, Nova-Gonzalez 2020, MINAG official 2021/23."""
    data = _load_yaml(MANUAL_ROOT / "cuba" / "food_import_caloric_share.yaml")
    rows = [
        {"country_iso3": "CUB", "year": int(o["year"]), "value": float(o["value"])}
        for o in data["observations"]
    ]
    return pd.DataFrame(rows)


def _series_mlc_retail_persistence(reference_year: int = 2024) -> pd.DataFrame:
    """MLC (Moneda Libremente Convertible) USD-only retail decreed via
    Resolucion 115/2019 (foreign-currency stores) extended by Resolucion
    423/2020. Value = years operating as of reference_year."""
    data = _load_yaml(MANUAL_ROOT / "cuba" / "mlc_retail.yaml")
    start = int(data["start_year"])
    end = int(data.get("end_year") or reference_year)
    years_active = end - start + 1
    return pd.DataFrame(
        [{"country_iso3": "CUB", "year": end, "value": float(years_active)}]
    )


_SERIES = {
    "libreta_persistence": _series_libreta_persistence,
    "monetary_regime_events": _series_monetary_regime_events,
    "mlc_retail_persistence": _series_mlc_retail_persistence,
    "food_import_caloric_share": _series_food_import_caloric_share,
    "private_sector_years_under_25pct": _series_private_sector_years_under_25pct,
    "emigration_share_pct": _series_emigration_share_pct,
}


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id not in _SERIES:
        raise ManualDropError(
            f"unknown cuba_manual series '{series_id}'. Known: {sorted(_SERIES)}"
        )
    fetch_ts = utc_now()
    df = _SERIES[series_id]()

    path_out, sha = write_vintage(
        publisher="cuba_manual",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="cuba_manual",
        series_id=series_id,
        source_url=f"manual://cuba_manual/{series_id}",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="manual",
        units="per series provenance",
        currency=None,
        start_date=str(int(df["year"].min())) if len(df) else None,
        end_date=str(int(df["year"].max())) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "provenance": str((MANUAL_ROOT / "cuba" / f"{series_id}.md").relative_to(MANUAL_ROOT.parent.parent))
            if (MANUAL_ROOT / "cuba" / f"{series_id}.md").exists() else None,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("series", choices=list(_SERIES.keys()))
    args = p.parse_args()
    res = fetch(args.series)
    print(f"OK series={res.series_id} rows={res.rows} {res.start_date}->{res.end_date}")
    print(f"   {res.parquet_path}")
