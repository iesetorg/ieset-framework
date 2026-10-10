"""Focused tests for the frozen top-PIT / disposable-Gini calibration."""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_oecd_top_pit_disposable_gini_forward_2026.py"
spec = importlib.util.spec_from_file_location("top_pit_gini", SCRIPT)
assert spec is not None and spec.loader is not None
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_symmetric_tax_categories_have_stable_middle() -> None:
    assert study.categories(-1.0) == (0, 1)
    assert study.categories(1.0) == (1, 0)
    assert study.categories(-0.999999) == (0, 0)
    assert study.categories(0.999999) == (0, 0)
    assert study.categories(-12.0) == (0, 1)
    assert study.categories(12.0) == (1, 0)


def synthetic_panel(hike_effect: float) -> tuple[pd.DataFrame, dict]:
    rows = []
    for country in range(30):
        for year in range(2007, 2019):
            slot = (country + 3 * (year - 2007)) % 10
            hike, cut = int(slot == 0), int(slot == 1)
            noise = 0.001 * math.sin(country * 2.31 + year * 0.81)
            rows.append({
                "country_iso3": f"C{country:02d}", "year": year,
                "hike": hike, "cut": cut,
                "gini_forward_change": hike_effect * hike + 0.002 * cut
                + 0.0003 * country + 0.0002 * (year - 2007) + noise,
            })
    panel = pd.DataFrame(rows)
    hikes, cuts = panel.loc[panel.hike.eq(1)], panel.loc[panel.cut.eq(1)]
    gate = {
        "valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
        "hike_rows": len(hikes), "hike_countries": hikes.country_iso3.nunique(),
        "cut_rows": len(cuts), "cut_countries": cuts.country_iso3.nunique(),
    }
    return panel, gate


def test_synthetic_sign_and_inconclusive_gates() -> None:
    negative, negative_gate = synthetic_panel(-0.012)
    shares = study.partialled_hike_concentration(negative)
    assert shares is not None
    assert shares["top_one_percent_share"] < study.MAX_TOP_1PCT
    assert shares["top_country_share"] < study.MAX_COUNTRY
    assert shares["top_year_share"] < study.MAX_YEAR
    supported = study.estimate(negative, negative_gate)
    assert supported["verdict"] == "SUPPORTED"
    assert supported["primary"]["coefficient"] < -study.MEANINGFUL_BETA
    assert supported["primary"]["p_value_two_sided"] < study.P_MAX

    positive, positive_gate = synthetic_panel(0.012)
    refuted = study.estimate(positive, positive_gate)
    assert refuted["verdict"] == "REFUTED"
    assert refuted["primary"]["coefficient"] > study.MEANINGFUL_BETA
    assert refuted["primary"]["p_value_two_sided"] < study.P_MAX

    too_few = dict(negative_gate)
    too_few["valid_rows"] = study.MIN_ROWS - 1
    inconclusive = study.estimate(negative, too_few)
    assert inconclusive["verdict"] == "INCONCLUSIVE"
    assert inconclusive["primary"] is None


def test_preflight_projects_only_gini_dimensions_and_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the actual source-key reader and reject any outcome-value projection."""
    outcome_path = ROOT / study.SOURCES["outcome"]["path"]
    if not outcome_path.exists():
        pytest.skip("pinned local raw files unavailable in this checkout")
    real_read = study.pd.read_parquet
    seen = []

    def checked_read(path: Path, *args, **kwargs):
        if Path(path) == outcome_path:
            columns = kwargs.get("columns")
            assert columns is not None
            assert set(columns) == {"REF_AREA", "period", *study.SELECTOR}
            assert not {"value", "Observation value", "OBS_STATUS", "Observation status"} & set(columns)
            seen.append(tuple(columns))
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(study.pd, "read_parquet", checked_read)
    rates, keys = study.source_keys()
    assert len(rates) == 950
    assert len(keys) == 656
    assert len(seen) == 1


def test_full_artifact_replay_detects_nonprimary_tampering(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    panel, gate = synthetic_panel(-0.012)
    result = study.estimate(panel, gate)
    monkeypatch.setattr(study, "ROOT", tmp_path)
    spec_path = tmp_path / study.SPEC
    spec_path.parent.mkdir(parents=True)
    spec_path.write_text("synthetic frozen spec\n")
    (tmp_path / study.SUMMARY).parent.mkdir(parents=True)
    registration, lock_commit = "a" * 40, "b" * 40
    study.write_artifacts(result, registration, lock_commit)
    study.verify_artifacts(result, registration, lock_commit)

    chart_path = tmp_path / study.RUN_DIR / "chart_data.json"
    chart = json.loads(chart_path.read_text())
    chart["family_id"] = "tampered"
    chart_path.write_text(json.dumps(chart) + "\n")
    with pytest.raises(AssertionError, match="chart_data"):
        study.verify_artifacts(result, registration, lock_commit)


def test_registration_is_required_before_outcome_access() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", study.SPEC],
        cwd=ROOT, capture_output=True,
    ).returncode == 0
    if tracked:
        assert len(study.registration_commit()) == 40
    else:
        with pytest.raises(RuntimeError, match="first-addition commit"):
            study.registration_commit()
