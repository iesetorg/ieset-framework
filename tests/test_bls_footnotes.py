"""Regression test: BLS returns [{}] footnotes for older windows; parquet write must not crash."""
import pandas as pd

from data.fetchers.bls import _normalise_footnotes


def test_normalise_shapes():
    assert _normalise_footnotes([{}]) == [{"code": None, "text": None}]
    assert _normalise_footnotes([]) == [{"code": None, "text": None}]
    assert _normalise_footnotes(None) == [{"code": None, "text": None}]
    assert _normalise_footnotes([{"code": "P", "text": "preliminary"}]) == [{"code": "P", "text": "preliminary"}]


def test_empty_struct_footnotes_write_parquet(tmp_path):
    df = pd.DataFrame({"year": [2010, 2026], "period": ["M01", "M09"], "value": [1.0, 2.0],
                       "footnotes": [[{}], [{"code": "P", "text": "preliminary"}]]})
    df["footnotes"] = df["footnotes"].map(_normalise_footnotes)
    out = tmp_path / "x.parquet"
    df.to_parquet(out, engine="pyarrow", index=False)
    back = pd.read_parquet(out)
    assert len(back) == 2 and back.footnotes.iloc[1][0]["code"] == "P"


def test_all_empty_window_writes(tmp_path):
    df = pd.DataFrame({"year": [2010, 2011], "value": [1.0, 2.0], "footnotes": [[{}], [{}]]})
    df["footnotes"] = df["footnotes"].map(_normalise_footnotes)
    df.to_parquet(tmp_path / "y.parquet", engine="pyarrow", index=False)
