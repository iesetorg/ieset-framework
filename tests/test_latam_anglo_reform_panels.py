"""Tests for the 2026-09-03 LatAm-reform / Anglo-stagnation data panels.

Drives the real builder logic (fixture-injected where a live API is
involved) and asserts the landed repository artifacts are internally
consistent with their manifests.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_argentina_milei_stabilisation_panel as arg_builder  # noqa: E402
import build_el_salvador_bukele_growth_panel as sv_builder  # noqa: E402
import build_anglo_public_private_stagnation_panel as anglo_builder  # noqa: E402


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_argentina_panel_builder_nulls_forward_filled_cpi(tmp_path: Path):
    months = pd.date_range("2024-01-01", periods=20, freq="MS")

    def fetch(series_id, publisher_id="bcra", desde=None, limit=5000):
        assert publisher_id in {"bcra", "indec"}
        if publisher_id == "indec":
            # CPI index stops publishing 3 months before the panel end
            values = list(range(100, 100 + 17)) + [116] * 3
            frame = pd.DataFrame({"fecha": months, "valor": values})
        else:
            name = arg_builder.BCRA_SERIES[series_id]
            frame = pd.DataFrame({"fecha": months, "valor": range(1, 21)})
        path = tmp_path / f"{publisher_id}_{series_id}.parquet"
        frame.to_parquet(path, index=False)

        class Result:
            parquet_path = path

            def as_manifest_entry(self):
                return {"series": series_id, "publisher": publisher_id}

        return Result()

    result = arg_builder.build(
        fetch=fetch,
        run_utc=datetime(2026, 9, 3, tzinfo=timezone.utc),
        root=tmp_path,
    )
    panel = pd.read_parquet(tmp_path / result["panel"])
    assert len(panel) == 20
    # observed months have real m/m stats (the first month has no base — NaN by design)
    observed = panel[panel["cpi_observed"]]
    assert observed["cpi_mom_pct"].iloc[1:].notna().all()
    assert (observed["cpi_mom_pct"].iloc[1:] > 0).all()
    # the 3 forward-filled months must be null, never fake 0%
    stale = panel[~panel["cpi_observed"]]
    assert len(stale) == 3
    assert stale["cpi_mom_pct"].isna().all()
    assert stale["cpi_yoy_pct"].isna().all()
    assert stale["cpi_12m_annualised_pct"].isna().all()
    manifest = yaml.safe_load((tmp_path / result["manifest"]).read_text())
    assert manifest["pipeline"] == "argentina_milei_stabilisation_panel"
    assert manifest["milei_window_from"] == "2023-12-10"


def test_el_salvador_panel_landed_with_peer_contrast():
    path = REPO_ROOT / "data" / "derived" / "el_salvador_bukele_growth_panel.parquet"
    panel = pd.read_parquet(path)
    slv = panel[panel["country_iso3"].eq("SLV")]
    assert set(panel["country_iso3"]) >= set(sv_builder.PEERS) | {"SLV"}
    assert slv["year"].between(2010, 2025).all()
    # the security collapse is visible in the real data
    early = slv.loc[slv["year"] <= 2018, "homicide_rate_per_100k"].max()
    late = slv.loc[slv["year"] >= 2022, "homicide_rate_per_100k"].min()
    assert early > 30 and late < 15
    # bukele_regime flag only flags SLV from 2019
    assert panel.loc[panel["bukele_regime"], "country_iso3"].eq("SLV").all()
    assert panel.loc[panel["bukele_regime"], "year"].min() == 2019
    assert panel["slv_growth_premium_vs_peers_pp"].notna().any()


def test_anglo_panel_landed_with_stagnation_columns():
    path = REPO_ROOT / "data" / "derived" / "anglo_public_private_stagnation_panel.parquet"
    panel = pd.read_parquet(path)
    assert set(panel["country_iso3"]) == set(anglo_builder.COUNTRIES)
    assert panel["year"].between(2000, 2024).all()
    # the welfare-anglo flag excludes the USA contrast unit
    assert set(panel.loc[panel["welfare_anglo"], "country_iso3"]) == set(anglo_builder.WELFARE_ANGLO)
    gbr_money = panel.loc[panel["country_iso3"].eq("GBR") & panel["year"].between(2020, 2022), "broad_money_growth_pct"]
    assert (gbr_money > 5).all(), "2020-22 UK broad money growth should be visibly elevated"
    # money_growth_above_5pct flag matches its definition
    flagged = panel["money_growth_above_5pct"].fillna(False)
    assert (flagged == (panel["broad_money_growth_pct"] > 5.0)).all()


def test_panel_manifests_match_landed_artifacts():
    for glob_pattern, panel_name in [
        ("fetch_run_*_el_salvador_bukele_panel.yaml", "el_salvador_bukele_growth_panel.parquet"),
        ("fetch_run_*_anglo_stagnation_panel.yaml", "anglo_public_private_stagnation_panel.parquet"),
        ("fetch_run_*_argentina_milei_panel.yaml", "argentina_milei_stabilisation_panel.parquet"),
    ]:
        manifests = sorted((REPO_ROOT / "data" / "manifests").glob(glob_pattern))
        assert manifests, glob_pattern
        manifest = yaml.safe_load(manifests[-1].read_text())
        panel_path = REPO_ROOT / manifest["artifacts"]["panel_parquet"]
        assert panel_path.name == panel_name
        assert panel_path.exists()
        assert manifest["artifacts"]["panel_sha256"] == sha256_path(panel_path)
