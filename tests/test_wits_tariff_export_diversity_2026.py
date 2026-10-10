"""Synthetic measurement and gate tests for the frozen WITS export family."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/run_wits_tariff_export_diversity_2026.py'
spec = importlib.util.spec_from_file_location('wits_tariff_export', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def candidate():
    return pd.DataFrame([{'country_iso3':'GBR','year':2010,'delta_tariff_decline':3.0,
                          'decline':1,'increase':0,'log_gdp_pc':10.0,'prior_gdp_change':0.1}])


def write_outcome(tmp_path, case, values):
    path=tmp_path / module.SOURCES[case]['path']
    path.parent.mkdir(parents=True,exist_ok=True)
    selector=module.CASES[case]['selector']
    pd.DataFrame([{'country_iso3':'GBR','year':year,'value':value,**selector}
                  for year,value in zip((2007,2010,2013),values)]).to_parquet(path,index=False)


def test_exported_count_horizon_and_nonnegative_contract(tmp_path):
    write_outcome(tmp_path,'exported_hs6_count',[10,12,18])
    old=module.MIN_YEARS
    module.MIN_YEARS=1
    try:
        panel,gate=module.measured_panel(tmp_path,'exported_hs6_count',candidate())
    finally:
        module.MIN_YEARS=old
    assert gate['valid_rows']==1
    assert math.isclose(panel.iloc[0].forward_change,math.log1p(18)-math.log1p(12))
    assert math.isclose(panel.iloc[0].prior_export_change,math.log1p(12)-math.log1p(10))
    assert module.valid_outcome(-1,'count') is None
    assert module.valid_outcome(2.5,'count') is None


def test_market_hhi_has_favorable_decline_sign(tmp_path):
    write_outcome(tmp_path,'export_market_hhi',[.3,.2,.1])
    old=module.MIN_YEARS
    module.MIN_YEARS=1
    try:
        panel,gate=module.measured_panel(tmp_path,'export_market_hhi',candidate())
    finally:
        module.MIN_YEARS=old
    assert gate['valid_rows']==1
    assert math.isclose(panel.iloc[0].forward_change,.1)
    assert math.isclose(panel.iloc[0].prior_export_change,.1)
    assert module.valid_outcome(1.01,'hhi') is None


def test_frozen_coverage_floor_forbids_estimate():
    gate={'valid_rows':0,'valid_reporters':0,'material_declines':0,
          'material_decline_reporters':0,'material_increases':0,
          'material_increase_reporters':0}
    result=module.estimate('export_product_hhi',pd.DataFrame(),gate)
    assert result['verdict']=='INCONCLUSIVE'
    assert result['primary'] is None
