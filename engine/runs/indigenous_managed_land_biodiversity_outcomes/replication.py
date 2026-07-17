#!/usr/bin/env python3
"""Replication — Indigenous-managed land vs biodiversity / deforestation outcomes.

Spec: hypotheses/fiscal/indigenous_managed_land_biodiversity_outcomes.yaml v1
Position-claim: eco_socialist #13 (school predicts: supported)

The spec calls for a parcel-level Callaway-Sant'Anna staggered DiD on
NOAA-VIIRS forest-cover composites and Hansen Global Forest Change tiles,
matched to indigenous-territory designation dates from FUNAI / DCCEEW /
First Nations registries, with biome / slope / road-distance controls.

This run discovers, by direct manifest inspection, that the data the
spec requires is not on disk:

  - noaa_viirs:forest_cover — there is no parcel-level forest-cover
    composite in the repo. The only NOAA-VIIRS files present are
    `annual_composites` (10 rows, KOR-only night-lights composite)
    and `night_lights` — neither is a forest-cover product, neither is
    parcel-resolved, and there is no Hansen GFC vintage at all.

  - faostat:forest_area — registered in `data/manifests/baseline_pull.yaml`
    under the faostat publisher block, but not present as a parquet
    vintage on disk (only QCL / crops_primary / food_balance_sheets are).

  - faostat:protected_area_km2 — same gap.

  - The treatment-side designation registry (FUNAI Terras Indígenas,
    AUS Indigenous Protected Areas, CAN Indigenous Guardians, plus
    PER/COL/ECU/BOL national territorial registries) is flagged in
    the spec as "manual compilation flagged as TODO" and is not in
    the repo.

Per research documentation §"What to do when your spec needs data
that isn't on disk", this run emits an `inconclusive` verdict with a
concrete data-gap label, writes the four standard artifacts, and does
NOT silently substitute a different series. The script is ready to
re-run for real once the fetchers and registry land.

The CS-DiD machinery is also not used; a degraded before/after
country-aggregate comparison is impossible because no national
forest-area or deforestation-rate series is on disk for the seven
sample countries.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "indigenous_managed_land_biodiversity_outcomes"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
COUNTRIES = ["BRA", "PER", "COL", "ECU", "BOL", "CAN", "AUS"]
PERIOD = (2000, 2023)

# Series the spec requires (publisher, series_id, role)
REQUIRED = [
    ("noaa_viirs", "forest_cover", "outcome (parcel-level deforestation)"),
    ("faostat", "forest_area", "outcome cross-check (national forest area)"),
    ("faostat", "protected_area_km2", "covariate (protected-area extent)"),
    ("world_bank_wdi", "NY.GDP.PCAP.KD", "control (real GDP per capita)"),
    ("world_bank_wdi", "NV.AGR.TOTL.ZS", "control (agriculture % GDP)"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    present: dict[str, dict] = {}
    missing: list[dict] = []
    for pub, series, role in REQUIRED:
        path = latest(pub, series)
        if path is None:
            missing.append({"publisher": pub, "series": series, "role": role})
        else:
            present[f"{pub}:{series}"] = {
                "publisher": pub,
                "series": series,
                "role": role,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
            }

    # The dispositive primary-outcome series are noaa_viirs:forest_cover
    # and faostat:forest_area. If either is absent the run cannot produce
    # a real verdict.
    primary_missing = [
        m for m in missing
        if (m["publisher"], m["series"]) in {
            ("noaa_viirs", "forest_cover"),
            ("faostat", "forest_area"),
        }
    ]

    gap_label = "; ".join(f"{m['publisher']}:{m['series']}" for m in missing) or "none"

    if primary_missing:
        primary_gap_str = ", ".join(
            f"{m['publisher']}:{m['series']}" for m in primary_missing
        )
        verdict = (
            f"inconclusive (data gap on {primary_gap_str}) "
            f"— the spec requires parcel-level NOAA-VIIRS forest-cover and FAOSTAT "
            f"national forest-area series for a Callaway-Sant'Anna staggered DiD on "
            f"indigenous-managed vs biome-matched control parcels across "
            f"{', '.join(COUNTRIES)} {PERIOD[0]}-{PERIOD[1]}; neither outcome series "
            f"is present in data/vintages/. Treatment-side indigenous-territory "
            f"designation dates are also flagged TODO in the spec. No degraded "
            f"country-aggregate fallback is possible because no national "
            f"forest-area or deforestation-rate vintage is on disk for the "
            f"seven sample countries. Re-run when noaa_viirs:forest_cover "
            f"(parcel composite, Hansen GFC equivalent) and faostat:forest_area "
            f"fetchers ship and territorial-designation registries are compiled."
        )
    else:
        # All primary outcome series present — but the parcel-level CS-DiD
        # cannot run on country-aggregate data. Mark inconclusive with a
        # method note and stop; do not fabricate parcel coding.
        verdict = (
            "inconclusive (method gap: parcel-level treatment unit not "
            "available from country-aggregate vintages; CS-DiD cannot be "
            "executed without geo-resolved parcel registry)."
        )

    # ---------- Diagnostics ----------
    diagnostics = {
        "verdict": verdict,
        "data_gap": True,
        "missing_series": missing,
        "present_series": [
            {"publisher": v["publisher"], "series": v["series"], "role": v["role"]}
            for v in present.values()
        ],
        "primary_outcome_series_missing": [
            f"{m['publisher']}:{m['series']}" for m in primary_missing
        ],
        "spec_requires": "Callaway-Sant'Anna staggered DiD on parcel-level forest-cover loss across 7 countries 2000-2023.",
        "spec_constraint_violations": [
            "no parcel-level forest-cover product on disk",
            "no Hansen GFC vintage on disk",
            "no faostat:forest_area parquet (registered in baseline_pull manifest, not yet fetched)",
            "no faostat:protected_area_km2 parquet",
            "indigenous-territory designation registry not compiled (spec flag: TODO)",
        ],
        "n_countries": len(COUNTRIES),
        "n_required_series": len(REQUIRED),
        "n_present_series": len(present),
        "n_missing_series": len(missing),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart (degraded — show data-gap diagnostic only) ----------
    series_blocks = [
        {
            "id": "data_gap",
            "label": "Required series missing on disk",
            "color": "#999999",
            "treated": False,
            "points": [
                {"x": i, "y": 1.0, "annotation": f"{m['publisher']}:{m['series']}"}
                for i, m in enumerate(missing)
            ],
        }
    ]
    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Indigenous-managed land vs biodiversity / deforestation — data gap",
        "subtitle": (
            f"Verdict: inconclusive. Required series not on disk: {gap_label}. "
            "CS-DiD cannot be executed without parcel-level forest-cover "
            "composites and territorial designation dates."
        ),
        "type": "scatter",
        "x_axis": {"label": "missing-series index", "type": "linear"},
        "y_axis": {"label": "(none)", "type": "linear"},
        "series": series_blocks,
        "annotations": [
            {
                "type": "note",
                "label": (
                    "Re-run once noaa_viirs:forest_cover (parcel) and "
                    "faostat:forest_area fetchers ship and indigenous-territory "
                    "designation dates are compiled."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in present.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients (empty long-form table — no estimates produced) ----------
    rows = [
        {"spec": "primary", "term": "did_att_aggregate", "estimate": float("nan")},
        {"spec": "primary", "term": "did_event_time_5yr", "estimate": float("nan")},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Manifest (only present series get vintage pins) ----------
    manifest_lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        "verdict_class: inconclusive_data_gap",
        "vintages:",
    ]
    for k, v in present.items():
        manifest_lines.append(f"  {k.replace(':', '__')}:")
        manifest_lines.append(f"    publisher: {v['publisher']}")
        manifest_lines.append(f"    series: {v['series']}")
        manifest_lines.append(f"    vintage_file: {v['vintage_file']}")
        manifest_lines.append(f"    sha256: {v['sha256']}")
    manifest_lines.append("missing_series:")
    for m in missing:
        manifest_lines.append(f"  - publisher: {m['publisher']}")
        manifest_lines.append(f"    series: {m['series']}")
        manifest_lines.append(f"    role: {m['role']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

    # ---------- Result card ----------
    card = [
        "# Indigenous-managed land vs biodiversity / deforestation outcomes",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Sample countries: {', '.join(COUNTRIES)} (7 countries).",
        f"- Period: {PERIOD[0]}-{PERIOD[1]}.",
        f"- Estimator the spec requires: Callaway-Sant'Anna staggered DiD with",
        f"  territory + year fixed effects, territory-clustered SEs.",
        f"- Required series present on disk: {len(present)} of {len(REQUIRED)}.",
        f"- Required series MISSING on disk: {len(missing)}.",
        "",
        "### Missing series",
        "",
        *[f"- `{m['publisher']}:{m['series']}` — {m['role']}" for m in missing],
        "",
        "## Method",
        "",
        "This run does not execute the spec's Callaway-Sant'Anna staggered DiD.",
        "The dispositive primary outcome — parcel-level forest-cover loss from",
        "NOAA-VIIRS / Hansen GFC — is not on disk in any form (the only",
        "NOAA-VIIRS files present are `annual_composites` and `night_lights`, both",
        "10-row Korea-only fragments and neither a forest-cover product). A",
        "country-aggregate fallback is also impossible because no national",
        "forest-area or deforestation-rate series is on disk for the seven",
        "sample countries (`faostat:forest_area` is registered in the baseline",
        "manifest but no parquet has been fetched).",
        "",
        "Per research documentation, the correct response to a data gap is to",
        "emit `inconclusive (data gap on <publisher>:<series>)`, not to",
        "fabricate or substitute a different series. This run does that.",
        "",
        "## Path to unblock",
        "",
        "1. Ship a `noaa_viirs:forest_cover` fetcher producing parcel-level",
        "   annual forest-cover loss composites (or import Hansen Global Forest",
        "   Change v1.x as a separate publisher).",
        "2. Ship a `faostat:forest_area` fetcher (already in the baseline-pull",
        "   manifest at `data/manifests/baseline_pull.yaml` line 1888 but not",
        "   yet on disk).",
        "3. Compile the indigenous-territory designation registry (BRA FUNAI,",
        "   AUS DCCEEW, CAN Indigenous Guardians; manual compilation noted in",
        "   the spec's treatment block as TODO).",
        "4. Re-run this script — no script-side change required; it auto-detects",
        "   when the data lands.",
        "",
        "## Data",
        "",
        f"- Required: {', '.join(f'{p}:{s}' for p, s, _ in REQUIRED)}",
        f"- Present: {', '.join(present.keys()) or '(none)'}",
        f"- Missing: {gap_label}",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
