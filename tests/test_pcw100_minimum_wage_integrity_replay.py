"""Regression checks for the audited minimum-wage bite/p10 screen.

These checks read the pinned, tracked derived panels and never rewrite the run.
They guard against confusing state labels with state-year contrast rows or
mistaking the separately measured p10 wage for the bite denominator.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "pcw100_us_mw_bite_ratio_p10_wage"
RUN = ROOT / "engine" / "runs" / RUN_ID
SPEC = importlib.util.spec_from_file_location(
    "policy_contrast_wave_100", ROOT / "scripts" / "policy_contrast_wave_100.py"
)
assert SPEC and SPEC.loader
wave = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wave)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pinned_inputs_and_contrast_rows_have_no_overlap() -> None:
    manifest = yaml.safe_load((RUN / "manifest.yaml").read_text(encoding="utf-8"))
    for vintage in manifest["vintages"]:
        assert _sha256(ROOT / vintage["vintage_file"]) == vintage["sha256"]

    config = wave.config_lookup()[RUN_ID]
    frame = wave.analysis_frame(config)
    assert len(frame) == 459
    assert not frame.duplicated(["state_abbr", "year"]).any()
    q25, q75 = frame["treatment"].quantile([0.25, 0.75])
    assert q25 < q75
    low = frame.loc[frame["treatment"] <= q25]
    high = frame.loc[frame["treatment"] >= q75]
    assert len(low) == len(high) == 115
    assert not set(zip(low.state_abbr, low.year)) & set(zip(high.state_abbr, high.year))
    assert set(low.state_abbr) & set(high.state_abbr) == {"HI", "MA", "MD", "MS", "NY"}


def test_bite_denominator_is_median_and_read_only_fit_replays() -> None:
    config = wave.config_lookup()[RUN_ID]
    frame = wave.analysis_frame(config)
    keys = ["state_abbr", "year"]
    minimum_wage = pd.read_parquet(ROOT / wave.STATE_MIN_WAGE)
    labor = pd.read_parquet(ROOT / wave.STATE_LABOR)
    joined = frame.merge(
        minimum_wage[keys + ["effective_minimum_wage", "bite_denominator_wage"]],
        on=keys,
        validate="one_to_one",
    ).merge(
        labor[keys + ["median_hourly_wage", "p10_hourly_wage"]],
        on=keys,
        validate="one_to_one",
    )
    assert len(joined) == 459
    assert (joined["bite_denominator_wage"] == joined["median_hourly_wage"]).all()
    assert (
        joined["treatment"]
        == joined["effective_minimum_wage"] / joined["median_hourly_wage"]
    ).all()
    assert (joined["p10_hourly_wage"] != joined["bite_denominator_wage"]).all()

    high = joined.loc[joined["treatment"] >= joined["treatment"].quantile(0.75)]
    gap = (high["p10_hourly_wage"] - high["effective_minimum_wage"]).abs()
    assert (gap <= 0.0100001).sum() == 2
    assert (gap == 0).sum() == 0

    stored = json.loads((RUN / "diagnostics.json").read_text(encoding="utf-8"))
    assert wave.preflight_one(config) == stored["preflight"]
    estimate = wave.estimate(config, frame)
    assert estimate == stored["estimate"]
    assert wave.verdict(config, estimate) == (
        stored["verdict"],
        stored["verdict_reason"],
    )
