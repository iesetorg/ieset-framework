#!/usr/bin/env python3
"""Multi-metric checklist evaluator for canonical-case hypotheses.

Loads a hypothesis yaml with evidence_type=canonical_case_multi_metric,
evaluates each pre-registered metric against available vintages, and
writes the standard run outputs to engine/runs/<hypothesis_id>/.

Each metric is assigned one of:
    MET             — threshold evaluated and satisfied
    NOT_MET         — threshold evaluated and NOT satisfied
    PENDING_DATA    — required source not yet in vintages (flag for fetcher)
    PENDING_EVAL    — data present but threshold requires human/LLM judgment
                      (e.g. complex consecutive-month conditions, count of
                      discrete events, archival narrative observations)

Hypothesis-level verdict:
    SUPPORTED     — MET >= support_threshold
    REFUTED       — (MET + POTENTIAL_MET) < support_threshold AND
                    (total_metrics - MET - PENDING_DATA - PENDING_EVAL)
                    >= refute_threshold  (i.e. NOT_MET confirmed count is
                    large enough to commit to refutation regardless of
                    pending resolution)
    INCONCLUSIVE  — otherwise; often means "too many pending metrics"

Usage:
    scripts/run_multi_metric_checklist.py <hypothesis_id>
    scripts/run_multi_metric_checklist.py --all
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
VINTAGES_DIR = REPO_ROOT / "data" / "vintages"
RUNS_DIR = REPO_ROOT / "engine" / "runs"
HYPOTHESES_DIR = REPO_ROOT / "hypotheses"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_hypothesis(hid: str) -> Path:
    """Find <hid>.yaml anywhere under hypotheses/."""
    hits = list(HYPOTHESES_DIR.glob(f"*/{hid}.yaml"))
    if not hits:
        raise FileNotFoundError(f"No hypothesis file found for id '{hid}'")
    if len(hits) > 1:
        raise RuntimeError(f"Multiple matches for '{hid}': {hits}")
    return hits[0]


def latest_vintage(publisher: str, series: str) -> Optional[Path]:
    """Return newest parquet vintage for publisher:series, else None."""
    d = VINTAGES_DIR / publisher
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def parse_source(src: str) -> list[tuple[str, str]]:
    """Parse source string into list of (publisher, series) pairs.

    Accepts:
        'publisher:series'
        'publisher1:series1; publisher2:series2'
        'manual:...'      -> [('manual', '...')]
        'derived:...'     -> [('derived', '...')]
    """
    out = []
    for part in src.split(";"):
        part = part.strip()
        if not part:
            continue
        # Some sources include trailing "(VEN)" or parens — keep first ':' split
        if ":" in part:
            pub, _, series = part.partition(":")
            # Strip country-qualifier trailing parens
            series = re.sub(r"\s*\([A-Z]{3}.*?\)\s*$", "", series).strip()
            out.append((pub.strip(), series))
    return out


def _tidy_maddison(t: pd.DataFrame, series: str) -> pd.DataFrame:
    """Maddison MPD has (country_iso3, country, year, gdppc, pop).
    series 'mpd2020' or 'mpd2020_gdppc' -> gdppc
    series 'mpd2020_pop' -> pop
    """
    col = "pop" if series.endswith("_pop") else "gdppc"
    if col not in t.columns:
        return pd.DataFrame(columns=["country", "year", "value"])
    # Drop human-readable 'country' column first so rename of country_iso3 does
    # not create a duplicate-named column (which breaks groupby downstream).
    t = t.drop(columns=[c for c in ("country",) if c in t.columns])
    out = t.rename(columns={"country_iso3": "country", col: "value"})[["country", "year", "value"]]
    return out


def _tidy_unhcr(t: pd.DataFrame, series: str) -> pd.DataFrame:
    """UNHCR population_origin has country_of_origin_iso3 + refugees/asylum_seekers.
    UNHCR population has country_of_asylum_iso3 + refugees/asylum_seekers/idps/stateless."""
    country_col = None
    for c in ("country_of_origin_iso3", "country_of_asylum_iso3", "country_iso3"):
        if c in t.columns:
            country_col = c
            break
    if country_col is None:
        return pd.DataFrame(columns=["country", "year", "value"])
    val_col = "refugees" if "refugees" in t.columns else None
    if val_col is None:
        return pd.DataFrame(columns=["country", "year", "value"])
    out = t.rename(columns={country_col: "country", val_col: "value"})[["country", "year", "value"]]
    return out


def _tidy_default(t: pd.DataFrame, series: str) -> pd.DataFrame:
    # If both country_iso3 and a separate human-readable country column are
    # present, prefer the ISO code as the grouping key and drop the name to
    # avoid creating a duplicate-named column after rename.
    if "country_iso3" in t.columns:
        if "country" in t.columns:
            t = t.drop(columns=["country"])
        t = t.rename(columns={"country_iso3": "country"})
    elif "iso3" in t.columns:
        if "country" in t.columns:
            t = t.drop(columns=["country"])
        t = t.rename(columns={"iso3": "country"})
    required = {"country", "year", "value"}
    if not required.issubset(set(t.columns)):
        return pd.DataFrame(columns=["country", "year", "value"])
    return t[["country", "year", "value"]].copy()


# Publisher-specific tidying adapters. Used when the vintage file does not
# ship a native (country, year, value) tidy panel.
PUBLISHER_TIDY_ADAPTERS: dict = {
    "maddison": _tidy_maddison,
    "unhcr": _tidy_unhcr,
}


def load_panel_series(publisher: str, series: str) -> Optional[pd.DataFrame]:
    """Load a vintage as a tidy panel: country, year, value.

    Returns None if no vintage present. Returns empty df if vintage is malformed.
    """
    path = latest_vintage(publisher, series)
    if path is None:
        return None
    try:
        t = pq.read_table(path).to_pandas()
    except Exception as e:
        print(f"  WARN: failed to read {path.name}: {e}", file=sys.stderr)
        return pd.DataFrame(columns=["country", "year", "value"])

    adapter = PUBLISHER_TIDY_ADAPTERS.get(publisher, _tidy_default)
    out = adapter(t, series)
    if out is None or out.empty:
        # Try default fallback if publisher-specific adapter returned nothing
        if adapter is not _tidy_default:
            out = _tidy_default(t, series)
    if out is None or out.empty:
        return pd.DataFrame(columns=["country", "year", "value"])
    out = out.copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["year"])
    # De-duplicate on (country, year) — some sources (e.g. WHO GHO with
    # sex=male/female/both rows) carry multiple rows per cell. Take the
    # max as a conservative default; a stratified-friendly adapter can
    # override per-publisher later if needed.
    if not out.empty:
        out = (
            out.groupby(["country", "year"], as_index=False)["value"]
            .max()
        )
    return out


# ---------------------------------------------------------------------------
# Threshold interpretation
# ---------------------------------------------------------------------------

NUMBER_RE = re.compile(r"(-?\d+(?:\.\d+)?)")


def parse_first_number(text: str) -> Optional[float]:
    m = NUMBER_RE.search(text)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Peer sets (ISO3) — used by the complex-threshold evaluator for peer-median
# and rank comparisons. Membership reflects the canonical-case hypotheses'
# benchmark groups (LatAm peers in Cuba/Venezuela cases, FSU/CEE in Soviet
# case, etc.). ISO3 codes are sourced from the country_year_ideology and
# movement YAMLs. Keep these lists conservative: better to under-include
# than to dilute the peer median with a tangential country.
# ---------------------------------------------------------------------------
PEER_SETS: dict[str, list[str]] = {
    "LatAm": [
        "ARG", "BOL", "BRA", "CHL", "COL", "CRI", "DOM", "ECU", "SLV",
        "GTM", "HND", "JAM", "MEX", "NIC", "PAN", "PRY", "PER", "URY", "VEN",
    ],
    "Eastern_Europe": [
        "ALB", "BGR", "BIH", "HRV", "CZE", "EST", "HUN", "LVA", "LTU",
        "MKD", "MNE", "POL", "ROU", "SRB", "SVK", "SVN",
    ],
    "advanced_economies": [
        "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN",
        "FRA", "GBR", "GRC", "IRL", "ISL", "ISR", "ITA", "JPN", "KOR",
        "LUX", "NLD", "NOR", "NZL", "PRT", "SWE", "USA",
    ],
    "Asian_tigers": ["HKG", "KOR", "SGP", "TWN"],
    "OECD": [
        "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK",
        "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR",
        "ITA", "JPN", "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL",
        "NOR", "POL", "PRT", "SVK", "SVN", "ESP", "SWE", "CHE", "TUR",
        "GBR", "USA",
    ],
}

# Known ISO3 codes referenced by canonical-case hypotheses (deep-reform vs
# shallow-reform peer sets in the Soviet hypothesis are typed inline).
_KNOWN_ISO3 = {
    code for codes in PEER_SETS.values() for code in codes
} | {
    "CUB", "VEN", "ZWE", "PRK", "KOR", "CHN", "RUS", "DDR", "DEU",
    "BLR", "UKR", "UZB", "TKM", "AZE", "ARM", "GEO", "MDA", "TJK", "KGZ", "KAZ",
}


def _value_at_year(df: pd.DataFrame, country: str, year: int,
                   tolerance: int = 5) -> Optional[tuple[float, int]]:
    """Return (value, year_used) for the closest available year within
    +/- tolerance. None if no data within tolerance. Used to soften
    'CUB 2023' lookups against panels that only run to 2018."""
    sub = df[(df["country"] == country)].dropna(subset=["value"])
    if sub.empty:
        return None
    if year in sub["year"].values:
        v = float(sub.loc[sub["year"] == year, "value"].iloc[0])
        return v, year
    # nearest-year fallback within tolerance
    sub = sub.assign(_d=(sub["year"].astype(int) - year).abs())
    sub = sub[sub["_d"] <= tolerance]
    if sub.empty:
        return None
    row = sub.sort_values("_d").iloc[0]
    return float(row["value"]), int(row["year"])


def _peer_median_value(df: pd.DataFrame, peer_codes: list[str], year: int,
                       tolerance: int = 5) -> Optional[float]:
    vals = []
    for code in peer_codes:
        got = _value_at_year(df, code, year, tolerance=tolerance)
        if got is not None:
            vals.append(got[0])
    if len(vals) < 3:  # need a usable median
        return None
    s = pd.Series(vals)
    return float(s.median())


def _compare(op: str, lhs: float, rhs: float) -> bool:
    if op == "<":
        return lhs < rhs
    if op == "<=":
        return lhs <= rhs
    if op == ">":
        return lhs > rhs
    if op == ">=":
        return lhs >= rhs
    if op in ("=", "=="):
        return abs(lhs - rhs) < 1e-9
    raise ValueError(f"unknown op {op!r}")


# Regex helpers for clause-level parsing
_OP_RE = r"(>=|<=|>|<|==|=)"
_NUM_RE = r"(-?\d+(?:\.\d+)?)"
_ISO3 = r"([A-Z]{3})"
_YEAR = r"(\d{4})"

# CUB 2023 GDP pc / CUB 1960 GDP pc < 1.5
_RATIO_SAME_COUNTRY_RE = re.compile(
    rf"^{_ISO3}\s+{_YEAR}\s+(.+?)\s*/\s*\1\s+{_YEAR}\s+\3\s*{_OP_RE}\s*{_NUM_RE}$"
)
# LatAm peer median 2023/1960 ratio > 3.0
_PEER_RATIO_RE = re.compile(
    rf"^([A-Za-z_]+)\s+peer\s+median\s+(?:(.+?)\s+)?{_YEAR}\s*/\s*{_YEAR}\s+ratio\s*{_OP_RE}\s*{_NUM_RE}$"
)
# CUB HDI 2022 - CUB HDI 1990 < 0.03
_DIFF_SAME_COUNTRY_RE = re.compile(
    rf"^{_ISO3}\s+(.+?)\s+{_YEAR}\s*-\s*\1\s+\2\s+{_YEAR}\s*{_OP_RE}\s*{_NUM_RE}$"
)
# LatAm peer median HDI 2022 - 1990 > 0.10
_PEER_DIFF_RE = re.compile(
    rf"^([A-Za-z_]+)\s+peer\s+median\s+(.+?)\s+{_YEAR}\s*-\s*{_YEAR}\s*{_OP_RE}\s*{_NUM_RE}$"
)
# CUB rank in top 5 (1958)
_RANK_TOP_RE = re.compile(
    rf"^{_ISO3}\s+rank\s+in\s+top\s+(\d+)(?:\s+of\s+(\d+))?\s*\(\s*{_YEAR}\s*\)$",
    re.IGNORECASE,
)
# CUB rank in bottom 10 out of 20 LatAm (2023)
_RANK_BOTTOM_RE = re.compile(
    rf"^{_ISO3}\s+rank\s+in\s+bottom\s+(\d+)(?:\s+(?:out\s+of|of)\s+(\d+))?\s*([A-Za-z_]+)?\s*\(\s*{_YEAR}\s*\)$",
    re.IGNORECASE,
)
# >=2 ... in a 30-year window
_EVENT_COUNT_RE = re.compile(
    rf"^{_OP_RE}\s*(\d+)\s+(.+?)\s+in\s+a\s+(\d+)-year\s+window",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Parser-extension regexes added to close Korea / Soviet inconclusive runs.
# All additive — they are tried after the existing same-country / peer-median
# clauses fall through. None alter behaviour on already-MET expressions.
# ---------------------------------------------------------------------------

# Country code alias map (informal name in threshold -> ISO3 in panels).
_COUNTRY_ALIAS = {
    "ROK": "KOR",
    "DPRK": "PRK",
    "FRG": "DEU",
    "GDR": "DDR",
    "USSR": "RUS",
}

def _canon_iso3(code: str) -> str:
    return _COUNTRY_ALIAS.get(code, code)

# Two-list peer set definitions. Each entry holds two ISO3 lists used for
# "<set-A> median ... vs <set-B> median ..." comparisons (Soviet metric 10).
TWO_LIST_PEERS: dict[str, list[str]] = {
    "deep_reform_set": ["EST", "LVA", "POL", "CZE", "LTU", "SVK"],
    "shallow_reform_set": ["BLR", "RUS", "UKR", "MDA", "KAZ", "UZB", "TKM"],
}

# Two-country direct ratio (op-prefix form). The expression must lead with
# an op-num-x token (e.g. ">100x", ">15x") so that this regex doesn't
# accidentally swallow gap/diff expressions. The trailing word "ratio"
# is optional — "share of world" / "radiance per unit area" type
# expressions are also accepted because the leading "Nx" reading is
# unambiguously a ratio.
#   ">15x ROK/DPRK GDP per capita PPP ratio in 2023"
#   ">5x DPRK/ROK infant mortality ratio"
#   ">100x ROK/DPRK manufacturing export share of world"
_TWO_COUNTRY_RATIO_PREFIX_RE = re.compile(
    rf"^\s*{_OP_RE}\s*{_NUM_RE}\s*x\s+([A-Z]{{2,4}})\s*/\s*([A-Z]{{2,4}})\b.*$",
    re.IGNORECASE,
)
# Two-country direct ratio (op-suffix form):
#   "ROK/DPRK nightlights radiance per unit area >100x"
_TWO_COUNTRY_RATIO_SUFFIX_RE = re.compile(
    rf"^\s*([A-Z]{{2,4}})\s*/\s*([A-Z]{{2,4}})\b(.*?)\s*{_OP_RE}\s*{_NUM_RE}\s*x?\s*$",
    re.IGNORECASE,
)
# Two-country direct difference / gap:
#   ">8 year ROK-minus-DPRK life expectancy gap"
#   ">90 percentage-point ROK-minus-DPRK internet penetration gap"
_TWO_COUNTRY_DIFF_RE = re.compile(
    rf"^\s*{_OP_RE}\s*{_NUM_RE}\s*\S*\s+([A-Z]{{2,4}})\s*-\s*minus\s*-\s*([A-Z]{{2,4}})\b.*$",
    re.IGNORECASE,
)
# Two-country gap with parenthetical orientation:
#   ">3cm adult male height gap (ROK > DPRK)"
_TWO_COUNTRY_PAREN_GAP_RE = re.compile(
    rf"^\s*{_OP_RE}\s*{_NUM_RE}\s*\S*\s+(.+?)\s+gap\s+\(\s*([A-Z]{{2,4}})\s*>\s*([A-Z]{{2,4}})\s*\)\s*$",
    re.IGNORECASE,
)
# Dual-country "has" comparison (single-clause; AND-split handles the
# bipartite form). Matches "ROK has >=5 ... firms" or "DPRK has 0".
_HAS_COUNT_RE = re.compile(
    rf"^\s*([A-Z]{{2,4}})\s+has\s+(?:{_OP_RE})?\s*(\d+)(?:\s+(.+))?$",
    re.IGNORECASE,
)
# Two-list peer-set median comparison (Soviet metric 10):
#   ">20 percentage point gap in 2000-GDP-pc-relative-to-1989 between
#    deep-reform (EST, LVA, POL, CZE) and shallow-reform (BLR, UKR, UZB, TKM) ..."
_TWO_LIST_GAP_RE = re.compile(
    rf"^\s*{_OP_RE}\s*{_NUM_RE}.*?\bbetween\b\s+([\w-]+)\s*\(([^)]+)\)\s*and\s+([\w-]+)\s*\(([^)]+)\).*$",
    re.IGNORECASE,
)
# Event-count threshold with explicit window-years (Soviet metric 9, Korea
# famine, etc.):
#   ">=2 major currency-regime events ... within a 10-year window"
#   ">=2 consecutive calendar years of >500% annualised CPI inflation 1992-1995"
#   "DPRK has >=1 documented peacetime famine event 1953-2023; ROK has 0"
_EVENT_COUNT_WINDOW_RE = re.compile(
    rf"^\s*(?:within\s+a\s+)?{_OP_RE}\s*(\d+)\s+(.+?)\s+(?:within\s+a\s+|in\s+a\s+)?(\d+)-year\s+window",
    re.IGNORECASE,
)
# >=2 consecutive calendar years of >500% ... 1992-1995
_CONSEC_INFLATION_RE = re.compile(
    rf"^\s*{_OP_RE}\s*(\d+)\s+consecutive\s+(?:calendar\s+)?years?\s+of\s+{_OP_RE}\s*{_NUM_RE}\s*%?\s*(.+?)\s+{_YEAR}\s*-\s*{_YEAR}\s*$",
    re.IGNORECASE,
)
# Word-boundary keyword classifier helpers (replaces brittle substring tests
# in evaluate_metric). Returns True when the word actually appears as a
# whole token, not e.g. "ratio" buried inside "emigration".
def _has_word(text: str, word: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE) is not None


def _split_logical(expr: str) -> tuple[str, list[str]]:
    """Split a threshold expression on top-level AND/OR (case-insensitive).

    Returns (combinator, clauses). combinator is 'AND', 'OR', or 'SINGLE'.
    Mixed AND/OR is rare in our metric set; if present, AND binds tighter
    in practice but we keep this simple: prefer AND-split if both occur.

    Parenthetical content is masked before splitting so that an "or" inside
    a list (e.g. "(redenomination, FX-regime switch, or >100% inflation)")
    does not get treated as a top-level OR.
    """
    # Mask parenthetical content with placeholder tokens so AND/OR matchers
    # ignore them. We re-substitute originals onto each clause at the end.
    placeholders: list[str] = []

    def _mask(m):
        placeholders.append(m.group(0))
        return f"__PAREN{len(placeholders) - 1}__"

    masked = re.sub(r"\([^()]*\)", _mask, expr)

    def _restore(s: str) -> str:
        for i, orig in enumerate(placeholders):
            s = s.replace(f"__PAREN{i}__", orig)
        return s

    # NOTE: AND/OR are split case-SENSITIVELY (uppercase only). Lower-case
    # "and"/"or" in natural-language threshold prose ("between deep-reform ...
    # and shallow-reform ...") must NOT be split as logical operators.
    has_and = re.search(r"\s+AND\s+", masked) is not None
    has_or = re.search(r"\s+OR\s+", masked) is not None
    has_semi = ";" in masked
    if has_and:
        parts = re.split(r"\s+AND\s+", masked)
        return "AND", [_restore(p.strip()) for p in parts]
    if has_semi:
        # Treat semicolon-separated clauses as AND-conjunctions (used in
        # canonical-case thresholds like "DPRK has >=1 famine event ...; ROK has 0").
        parts = [p for p in masked.split(";") if p.strip()]
        return "AND", [_restore(p.strip()) for p in parts]
    if has_or:
        parts = re.split(r"\s+OR\s+", masked)
        return "OR", [_restore(p.strip()) for p in parts]
    return "SINGLE", [_restore(masked.strip())]


def _latest_common_year(df: pd.DataFrame, codes: list[str],
                        window: Optional[tuple[int, int]] = None) -> Optional[int]:
    """Return the most recent year (within window) where every ISO3 in
    codes has a value. Returns None if no such year exists."""
    if df is None or df.empty:
        return None
    sub = df[df["country"].isin(codes)].dropna(subset=["value"])
    if sub.empty:
        return None
    if window:
        sub = sub[(sub["year"] >= window[0]) & (sub["year"] <= window[1])]
    if sub.empty:
        return None
    by_year = sub.groupby("year")["country"].nunique()
    needed = len(set(codes))
    candidates = by_year[by_year >= needed]
    if candidates.empty:
        return None
    return int(candidates.index.max())


def _evaluate_clause(clause: str, country: str, panel_df: pd.DataFrame,
                     window: Optional[tuple[int, int]] = None
                     ) -> tuple[Optional[bool], str]:
    """Evaluate a single clause. Returns (verdict, note).

    verdict: True/False/None (None means clause not recognised or data missing).
    """
    s = clause.strip()

    # --- Same-country ratio: CUB 2023 GDP pc / CUB 1960 GDP pc < 1.5
    m = _RATIO_SAME_COUNTRY_RE.match(s)
    if m:
        ctry, y1, _series, y2, op, num = m.group(1), int(m.group(2)), m.group(3), int(m.group(4)), m.group(5), float(m.group(6))
        v1 = _value_at_year(panel_df, ctry, y1)
        v2 = _value_at_year(panel_df, ctry, y2)
        if v1 is None or v2 is None or v2[0] == 0:
            return None, f"missing data for {ctry} ratio {y1}/{y2}"
        ratio = v1[0] / v2[0]
        return _compare(op, ratio, num), (
            f"{ctry} {y1}/{y2} ratio = {ratio:.3f} (used years {v1[1]}/{v2[1]})"
        )

    # --- Same-country difference: CUB HDI 2022 - CUB HDI 1990 < 0.03
    m = _DIFF_SAME_COUNTRY_RE.match(s)
    if m:
        ctry, _series, y1, y2, op, num = m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5), float(m.group(6))
        v1 = _value_at_year(panel_df, ctry, y1)
        v2 = _value_at_year(panel_df, ctry, y2)
        if v1 is None or v2 is None:
            return None, f"missing data for {ctry} diff {y1}-{y2}"
        diff = v1[0] - v2[0]
        return _compare(op, diff, num), (
            f"{ctry} {y1}-{y2} diff = {diff:.3f} (used {v1[1]}, {v2[1]})"
        )

    # --- Peer-median ratio: LatAm peer median 2023/1960 ratio > 3.0
    m = _PEER_RATIO_RE.match(s)
    if m:
        peer_name, _series, y1, y2, op, num = m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5), float(m.group(6))
        peers = PEER_SETS.get(peer_name)
        if peers is None:
            return None, f"unknown peer set {peer_name!r}"
        # Compute per-country ratio, then median
        ratios = []
        for code in peers:
            v1 = _value_at_year(panel_df, code, y1)
            v2 = _value_at_year(panel_df, code, y2)
            if v1 is not None and v2 is not None and v2[0] != 0:
                ratios.append(v1[0] / v2[0])
        if len(ratios) < 3:
            return None, f"insufficient {peer_name} peers with data ({len(ratios)})"
        med = float(pd.Series(ratios).median())
        return _compare(op, med, num), (
            f"{peer_name} peer median {y1}/{y2} ratio = {med:.3f} (n={len(ratios)})"
        )

    # --- Peer-median difference: LatAm peer median HDI 2022 - 1990 > 0.10
    m = _PEER_DIFF_RE.match(s)
    if m:
        peer_name, _series, y1, y2, op, num = m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5), float(m.group(6))
        peers = PEER_SETS.get(peer_name)
        if peers is None:
            return None, f"unknown peer set {peer_name!r}"
        diffs = []
        for code in peers:
            v1 = _value_at_year(panel_df, code, y1)
            v2 = _value_at_year(panel_df, code, y2)
            if v1 is not None and v2 is not None:
                diffs.append(v1[0] - v2[0])
        if len(diffs) < 3:
            return None, f"insufficient {peer_name} peers with data ({len(diffs)})"
        med = float(pd.Series(diffs).median())
        return _compare(op, med, num), (
            f"{peer_name} peer median {y1}-{y2} diff = {med:.3f} (n={len(diffs)})"
        )

    # --- Rank: CUB rank in top 5 (1958)
    m = _RANK_TOP_RE.match(s)
    if m:
        ctry, n_top, _of, year = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        rank = _country_rank(panel_df, ctry, year, descending=True)
        if rank is None:
            return None, f"cannot compute rank for {ctry} {year}"
        return rank <= n_top, f"{ctry} rank in {year} = {rank} (top {n_top} required)"

    # --- Rank bottom: CUB rank in bottom 10 out of 20 LatAm (2023)
    m = _RANK_BOTTOM_RE.match(s)
    if m:
        ctry = m.group(1)
        n_bottom = int(m.group(2))
        peer_name = m.group(4)
        year = int(m.group(5))
        peers = PEER_SETS.get(peer_name) if peer_name else None
        rank = _country_rank(panel_df, ctry, year, descending=True, peer_codes=peers)
        if rank is None:
            return None, f"cannot compute rank for {ctry} {year}"
        # Universe size:
        universe = peers if peers else None
        if universe:
            total = sum(1 for c in universe if _value_at_year(panel_df, c, year) is not None)
        else:
            sub = panel_df[panel_df["year"] == year].dropna(subset=["value"])
            total = sub["country"].nunique()
        bottom_rank_threshold = total - n_bottom + 1
        ok = rank >= bottom_rank_threshold
        return ok, f"{ctry} rank in {year} = {rank}/{total} (bottom {n_bottom} requires rank >= {bottom_rank_threshold})"

    # ----------------------------------------------------------------
    # Two-country direct ratio (op-prefix form):
    #   ">15x ROK/DPRK GDP per capita PPP ratio in 2023"
    # ----------------------------------------------------------------
    m = _TWO_COUNTRY_RATIO_PREFIX_RE.match(s)
    if m:
        op, num, c1, c2 = m.group(1), float(m.group(2)), m.group(3), m.group(4)
        a, b = _canon_iso3(c1), _canon_iso3(c2)
        # Try to lift an explicit year from the clause first; else use latest
        # common year (within window if provided).
        explicit_year = re.search(r"\bin\s+(\d{4})\b", s)
        if explicit_year:
            yr = int(explicit_year.group(1))
        else:
            yr = _latest_common_year(panel_df, [a, b], window=window)
        if yr is None:
            return None, f"no common year for {a}/{b}"
        v1 = _value_at_year(panel_df, a, yr)
        v2 = _value_at_year(panel_df, b, yr)
        if v1 is None or v2 is None or v2[0] == 0:
            return None, f"missing data for {a}/{b} ratio @{yr}"
        ratio = v1[0] / v2[0]
        return _compare(op, ratio, num), (
            f"{a}/{b} ratio = {ratio:.3f} @{yr} ({v1[1]}/{v2[1]})"
        )

    # ----------------------------------------------------------------
    # Two-country direct ratio (op-suffix form):
    #   "ROK/DPRK nightlights radiance per unit area >100x"
    # ----------------------------------------------------------------
    m = _TWO_COUNTRY_RATIO_SUFFIX_RE.match(s)
    if m:
        c1, c2, _series, op, num = m.group(1), m.group(2), m.group(3), m.group(4), float(m.group(5))
        a, b = _canon_iso3(c1), _canon_iso3(c2)
        yr = _latest_common_year(panel_df, [a, b], window=window)
        if yr is None:
            return None, f"no common year for {a}/{b}"
        v1 = _value_at_year(panel_df, a, yr)
        v2 = _value_at_year(panel_df, b, yr)
        if v1 is None or v2 is None or v2[0] == 0:
            return None, f"missing data for {a}/{b} ratio @{yr}"
        ratio = v1[0] / v2[0]
        return _compare(op, ratio, num), (
            f"{a}/{b} ratio = {ratio:.3f} @{yr}"
        )

    # ----------------------------------------------------------------
    # Two-country direct difference / gap:
    #   ">8 year ROK-minus-DPRK life expectancy gap"
    # ----------------------------------------------------------------
    m = _TWO_COUNTRY_DIFF_RE.match(s)
    if m:
        op, num, c1, c2 = m.group(1), float(m.group(2)), m.group(3), m.group(4)
        a, b = _canon_iso3(c1), _canon_iso3(c2)
        yr = _latest_common_year(panel_df, [a, b], window=window)
        if yr is None:
            return None, f"no common year for {a}-{b} diff"
        v1 = _value_at_year(panel_df, a, yr)
        v2 = _value_at_year(panel_df, b, yr)
        if v1 is None or v2 is None:
            return None, f"missing data for {a}-{b} diff @{yr}"
        diff = v1[0] - v2[0]
        return _compare(op, diff, num), (
            f"{a}-{b} diff = {diff:.3f} @{yr}"
        )

    # ----------------------------------------------------------------
    # Two-country gap with parenthetical orientation:
    #   ">3cm adult male height gap (ROK > DPRK)"
    # ----------------------------------------------------------------
    m = _TWO_COUNTRY_PAREN_GAP_RE.match(s)
    if m:
        op, num, _series, c1, c2 = m.group(1), float(m.group(2)), m.group(3), m.group(4), m.group(5)
        a, b = _canon_iso3(c1), _canon_iso3(c2)
        yr = _latest_common_year(panel_df, [a, b], window=window)
        if yr is None:
            return None, f"no common year for {a}-{b} gap"
        v1 = _value_at_year(panel_df, a, yr)
        v2 = _value_at_year(panel_df, b, yr)
        if v1 is None or v2 is None:
            return None, f"missing data for {a}-{b} gap @{yr}"
        diff = v1[0] - v2[0]
        return _compare(op, diff, num), (
            f"{a}-{b} gap = {diff:.3f} @{yr}"
        )

    # ----------------------------------------------------------------
    # Two-list peer-set median comparison (Soviet metric 10):
    #   ">20 percentage point gap in 2000-GDP-pc-relative-to-1989 between
    #    deep-reform (EST, LVA, POL, CZE) and shallow-reform (BLR, UKR, UZB, TKM) ..."
    # ----------------------------------------------------------------
    m = _TWO_LIST_GAP_RE.match(s)
    if m:
        op = m.group(1)
        num = float(m.group(2))
        _name1 = m.group(3)
        list1 = [c.strip().upper() for c in m.group(4).split(",") if c.strip()]
        _name2 = m.group(5)
        list2 = [c.strip().upper() for c in m.group(6).split(",") if c.strip()]
        # Lift two reference years from the prefix (e.g. "2000-GDP-pc-relative-to-1989")
        years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", s)]
        if len(years) < 2:
            return None, f"two-list peer-set: need two reference years in expression"
        # Heuristic: numerator-year is the *later* of the first two found,
        # denominator-year is the earlier (so 2000/1989 -> 2000 over 1989).
        y_num = max(years[0], years[1])
        y_den = min(years[0], years[1])

        def _set_median_index(codes: list[str]) -> Optional[float]:
            ratios = []
            for c in codes:
                a = _value_at_year(panel_df, c, y_num)
                b = _value_at_year(panel_df, c, y_den)
                if a is not None and b is not None and b[0] != 0:
                    ratios.append(100.0 * a[0] / b[0])
            if len(ratios) < 2:
                return None
            return float(pd.Series(ratios).median())

        med1 = _set_median_index(list1)
        med2 = _set_median_index(list2)
        if med1 is None or med2 is None:
            return None, "two-list peer-set: insufficient peer data"
        gap = med1 - med2
        return _compare(op, abs(gap), num), (
            f"two-list gap = {gap:.2f} pp ({_name1} median {med1:.1f} vs "
            f"{_name2} median {med2:.1f}; ref {y_num}/{y_den})"
        )

    # ----------------------------------------------------------------
    # Dual-country "has" comparison: "ROK has >=5 Fortune Global 500 firms"
    # / "DPRK has 0". Combined via AND-splitting at the top level.
    # ----------------------------------------------------------------
    m = _HAS_COUNT_RE.match(s)
    if m:
        ctry = _canon_iso3(m.group(1))
        op = m.group(2) or ">="
        num = float(m.group(3))
        # Compare against most recent observation for that country (within
        # window if provided).
        sub = panel_df[panel_df["country"] == ctry].dropna(subset=["value"])
        if window:
            sub = sub[(sub["year"] >= window[0]) & (sub["year"] <= window[1])]
        if sub.empty:
            return None, f"{ctry} has-clause: no data"
        latest = sub.sort_values("year").iloc[-1]
        observed = float(latest["value"])
        # If the threshold number is 0 and op is ">=" / unspecified, the
        # natural reading is "exactly 0", so use == comparison.
        if num == 0.0 and (m.group(2) is None or op == ">=" or op == "="):
            ok = observed == 0.0
        else:
            ok = _compare(op, observed, num)
        return ok, f"{ctry} has {observed:g} ({int(latest['year'])}); threshold {op}{num:g}"

    # ----------------------------------------------------------------
    # Consecutive-years-above-level event count (Soviet metric 4):
    #   ">=2 consecutive calendar years of >500% annualised CPI inflation 1992-1995"
    # ----------------------------------------------------------------
    m = _CONSEC_INFLATION_RE.match(s)
    if m:
        op_n, n_required = m.group(1), int(m.group(2))
        op_l, level = m.group(3), float(m.group(4))
        y0, y1 = int(m.group(6)), int(m.group(7))
        sub = panel_df[panel_df["country"] == country].dropna(subset=["value"])
        sub = sub[(sub["year"] >= y0) & (sub["year"] <= y1)].sort_values("year")
        if sub.empty:
            return None, f"consec-inflation: no {country} data in {y0}-{y1}"
        # Run-length of consecutive years matching the level threshold.
        run = 0
        max_run = 0
        prev_year = None
        for _, row in sub.iterrows():
            yr = int(row["year"])
            v = float(row["value"])
            ok = _compare(op_l, v, level)
            if ok and (prev_year is None or yr == prev_year + 1):
                run += 1
            elif ok:
                run = 1
            else:
                run = 0
            max_run = max(max_run, run)
            prev_year = yr
        return _compare(op_n, max_run, n_required), (
            f"max consecutive years {op_l}{level} = {max_run} in {y0}-{y1}"
        )

    # ----------------------------------------------------------------
    # Event count over an explicit calendar window (Korea famine; or
    # ">=N <event> ... in <YYYY>-<YYYY>"). The data substrate is a
    # one-row-per-event panel (cuba_manual:monetary_regime_events shape):
    # value=1 per event-year. Cumulative-count panels (cbr:official_decrees
    # shape) are also handled via max_in_window.
    # ----------------------------------------------------------------
    explicit_window = re.search(r"\b(\d{4})\s*-\s*(\d{4})\b", s)
    leading_cnt = re.match(rf"^\s*{_OP_RE}\s*(\d+)\b", s)
    if leading_cnt and explicit_window and re.search(r"\bevent|episode|reform|change|year\b", s, re.IGNORECASE):
        op = leading_cnt.group(1)
        n_req = int(leading_cnt.group(2))
        y0, y1 = int(explicit_window.group(1)), int(explicit_window.group(2))
        sub = panel_df[panel_df["country"] == country].dropna(subset=["value"])
        sub = sub[(sub["year"] >= y0) & (sub["year"] <= y1)]
        if sub.empty:
            return None, f"event-count: no {country} data {y0}-{y1}"
        # Heuristic: if values look like a cumulative running count
        # (monotone non-decreasing, integer-valued, max <= y1-y0+1) we read
        # max as the count. Else (one row per event with value=1) we sum.
        vals = sub.sort_values("year")["value"].tolist()
        is_cum = all(vals[i] <= vals[i+1] for i in range(len(vals)-1)) and max(vals) > 1
        is_event_log = all(v in (0.0, 1.0) for v in vals) and len(vals) > 1
        if is_cum:
            count = float(max(vals))
            stat = "max_cumulative"
        elif is_event_log:
            count = float(sum(1 for v in vals if v == 1.0))
            stat = "event_log_sum"
        else:
            count = float(max(vals))
            stat = "max_value"
        return _compare(op, count, n_req), (
            f"event-count [{stat}] = {count:g} in {y0}-{y1}; threshold {op}{n_req}"
        )

    # ----------------------------------------------------------------
    # Event count with N-year window AND a metric.window override (Soviet
    # metric 9: ">=2 ... within a 10-year window" with metric.window=1989-1998).
    # When the caller provides an explicit calendar window we can count
    # events on the underlying data substrate.
    # ----------------------------------------------------------------
    m_window = _EVENT_COUNT_WINDOW_RE.match(s) or _EVENT_COUNT_RE.match(s)
    if m_window and window is not None:
        op = m_window.group(1)
        n_req = int(m_window.group(2))
        y0, y1 = window
        sub = panel_df[panel_df["country"] == country].dropna(subset=["value"])
        sub = sub[(sub["year"] >= y0) & (sub["year"] <= y1)]
        if not sub.empty:
            vals = sub.sort_values("year")["value"].tolist()
            is_cum = all(vals[i] <= vals[i+1] for i in range(len(vals)-1)) and max(vals) > 1
            is_event_log = all(v in (0.0, 1.0) for v in vals) and len(vals) > 1
            if is_cum:
                count = float(max(vals))
                stat = "max_cumulative"
            elif is_event_log:
                count = float(sum(1 for v in vals if v == 1.0))
                stat = "event_log_sum"
            else:
                count = float(max(vals))
                stat = "max_value"
            return _compare(op, count, n_req), (
                f"event-count [{stat}] = {count:g} in {y0}-{y1}; threshold {op}{n_req}"
            )
        return None, "event_count_request: " + s

    # --- Event count: >=2 ... in a 30-year window (no calendar window)
    m = _EVENT_COUNT_RE.match(s)
    if m:
        # Defer to human curation; signal recognition via diagnostic note.
        return None, "event_count_request: " + s

    return None, ""  # unrecognised


def _country_rank(df: pd.DataFrame, country: str, year: int,
                  descending: bool = True,
                  peer_codes: Optional[list[str]] = None,
                  tolerance: int = 5) -> Optional[int]:
    """Return 1-indexed rank of `country` in `year` (descending = highest is rank 1).

    Uses nearest-year fallback for the target country and each peer.
    """
    if peer_codes:
        universe = list(peer_codes)
        if country not in universe:
            universe = [country] + universe
    else:
        universe = sorted(set(df["country"].dropna()))
    pairs = []
    for code in universe:
        got = _value_at_year(df, code, year, tolerance=tolerance)
        if got is not None:
            pairs.append((code, got[0]))
    if not pairs or country not in {c for c, _ in pairs}:
        return None
    pairs.sort(key=lambda kv: kv[1], reverse=descending)
    for i, (code, _v) in enumerate(pairs, start=1):
        if code == country:
            return i
    return None


def _evaluate_complex_threshold(threshold: str, country: str,
                                panel_df: pd.DataFrame,
                                window: Optional[tuple[int, int]] = None,
                                ) -> Optional[dict]:
    """Evaluate a multi-clause threshold expression.

    Returns None if expression is not recognised by any clause-handler
    (caller should fall back to existing parser). Returns a dict with:
        {
          "met": bool,
          "note": str,
          "diagnostics": list[str],
          "event_count_request": Optional[str],
        }
    """
    combinator, clauses = _split_logical(threshold)
    clause_results: list[Optional[bool]] = []
    notes: list[str] = []
    event_request: Optional[str] = None
    any_recognised = False

    for c in clauses:
        verdict, note = _evaluate_clause(c, country, panel_df, window=window)
        if note.startswith("event_count_request:"):
            event_request = note[len("event_count_request:"):].strip()
            any_recognised = True
        if note:
            notes.append(note)
        if verdict is not None or note.startswith("event_count_request:"):
            any_recognised = True
        clause_results.append(verdict)

    if not any_recognised:
        return None  # let caller fall back

    # If any clause failed to evaluate (verdict is None and not event_count),
    # we can't deliver a final True/False unless combinator allows shortcut.
    if combinator == "AND":
        if any(v is False for v in clause_results):
            met = False
        elif all(v is True for v in clause_results):
            met = True
        else:
            return {
                "met": None,
                "note": "; ".join(notes) if notes else "AND-clause evaluation incomplete",
                "diagnostics": notes,
                "event_count_request": event_request,
            }
    elif combinator == "OR":
        if any(v is True for v in clause_results):
            met = True
        elif all(v is False for v in clause_results):
            met = False
        else:
            return {
                "met": None,
                "note": "; ".join(notes) if notes else "OR-clause evaluation incomplete",
                "diagnostics": notes,
                "event_count_request": event_request,
            }
    else:  # SINGLE
        if clause_results and clause_results[0] is not None:
            met = clause_results[0]
        else:
            return {
                "met": None,
                "note": "; ".join(notes) if notes else "single-clause unevaluable",
                "diagnostics": notes,
                "event_count_request": event_request,
            }

    return {
        "met": met,
        "note": "; ".join(notes),
        "diagnostics": notes,
        "event_count_request": event_request,
    }


def parse_window(win: str) -> Optional[tuple[int, int]]:
    """Parse '2013-2019' or '2014Q1-2019Q4' -> (start_year, end_year)."""
    if not win:
        return None
    years = re.findall(r"(\d{4})", win)
    if len(years) >= 2:
        return int(years[0]), int(years[1])
    if len(years) == 1:
        return int(years[0]), int(years[0])
    return None


@dataclass
class MetricResult:
    metric_id: str
    status: str              # MET / NOT_MET / PENDING_DATA / PENDING_EVAL
    threshold: str
    window: str
    source: str
    direction: str = "supports_claim"
    observed_value: Optional[float] = None
    observed_stat_name: Optional[str] = None
    observed_year: Optional[int] = None
    vintage_files: list[str] = field(default_factory=list)
    vintage_sha256: list[str] = field(default_factory=list)
    notes: str = ""


# Heuristic keyword classifiers used by evaluate_metric()
DECLINE_KEYWORDS = ("decline", "contraction", "collapse", "loss", "drop", "fall", "reversal", "reduction")
INCREASE_KEYWORDS = ("increase", "rise", "surge", "growth", "gap", "exceed", "greater", "higher")
LEVEL_RATE_KEYWORDS = ("rate in any year", "at any point", "threshold in any year", "any single year", "in any year", "during", "of population")


def _apply_numeric_threshold(observed: float, threshold_text: str) -> Optional[bool]:
    """Given a numeric observed value and a threshold string like '>60%' or '>=7',
    return True/False if parseable, None if threshold not recognisable."""
    m = re.match(r"\s*(>=|>|<=|<|=)\s*(-?\d+(?:\.\d+)?)", threshold_text.strip())
    if not m:
        return None
    op, num = m.group(1), float(m.group(2))
    if op in ("<", "<="):
        return observed < num if op == "<" else observed <= num
    if op in (">", ">="):
        return observed > num if op == ">" else observed >= num
    if op == "=":
        return abs(observed - num) < 1e-9
    return None


def evaluate_metric(metric: dict, country: str) -> MetricResult:
    """Attempt to auto-evaluate a canonical_metric.

    Returns a MetricResult with status and observed value if possible.
    """
    mid = metric["metric_id"]
    threshold = metric["threshold"]
    window = metric.get("window", "")
    src = metric.get("source", "")
    direction = metric.get("direction", "supports_claim")

    pairs = parse_source(src)
    if not pairs:
        return MetricResult(mid, "PENDING_EVAL", threshold, window, src, direction,
                            notes="source string unparseable")

    # Accumulate vintage provenance even for failed loads
    vintage_files = []
    vintage_shas = []
    panel_dfs = []
    non_tidy_sources = []
    missing_sources = []
    for pub, series in pairs:
        if pub in ("manual", "derived"):
            missing_sources.append(f"{pub}:{series}")
            continue
        path = latest_vintage(pub, series)
        if path is None:
            missing_sources.append(f"{pub}:{series}")
            continue
        vintage_files.append(str(path.relative_to(REPO_ROOT)))
        try:
            vintage_shas.append(sha256(path))
        except Exception:
            vintage_shas.append("")
        df = load_panel_series(pub, series)
        if df is None or df.empty:
            non_tidy_sources.append(f"{pub}:{series}")
            continue
        panel_dfs.append(df)

    if not panel_dfs:
        status = "PENDING_DATA" if missing_sources else "PENDING_EVAL"
        note = ""
        if missing_sources:
            note = f"No usable vintage for: {', '.join(missing_sources)}"
        if non_tidy_sources:
            note = (note + "; " if note else "") + f"Non-tidy (needs custom parser): {', '.join(non_tidy_sources)}"
        return MetricResult(mid, status, threshold, window, src, direction,
                            vintage_files=vintage_files, vintage_sha256=vintage_shas,
                            notes=note)

    # Concatenate all loaded panels (first match wins for country-year)
    df = pd.concat(panel_dfs, ignore_index=True)

    # ---- NEW: try the complex-expression evaluator first ----
    # Recognises AND/OR clauses, peer-median, ratios, rank, event-count.
    # Falls through to the legacy classifier when not recognised.
    win_for_complex = parse_window(window)
    complex_res = _evaluate_complex_threshold(threshold, country, df,
                                              window=win_for_complex)
    if complex_res is not None:
        if complex_res["met"] is True:
            return MetricResult(
                mid, "MET", threshold, window, src, direction,
                vintage_files=vintage_files, vintage_sha256=vintage_shas,
                observed_stat_name="complex_threshold",
                notes=complex_res["note"],
            )
        if complex_res["met"] is False:
            return MetricResult(
                mid, "NOT_MET", threshold, window, src, direction,
                vintage_files=vintage_files, vintage_sha256=vintage_shas,
                observed_stat_name="complex_threshold",
                notes=complex_res["note"],
            )
        # met is None -> partial; PENDING_EVAL with structured diagnostic
        ev_note = complex_res["note"]
        if complex_res.get("event_count_request"):
            ev_note = (ev_note + "; " if ev_note else "") + (
                f"event_count_request: {complex_res['event_count_request']}"
            )
        return MetricResult(
            mid, "PENDING_EVAL", threshold, window, src, direction,
            vintage_files=vintage_files, vintage_sha256=vintage_shas,
            notes=ev_note or "complex threshold partially evaluable",
        )

    sub = df[df["country"] == country].dropna(subset=["value"]).copy()
    if sub.empty:
        return MetricResult(mid, "PENDING_DATA", threshold, window, src, direction,
                            vintage_files=vintage_files, vintage_sha256=vintage_shas,
                            notes=f"No {country} observations in loaded vintages")

    win = parse_window(window)
    if win:
        sub = sub[(sub["year"] >= win[0]) & (sub["year"] <= win[1])]
    if sub.empty:
        return MetricResult(mid, "PENDING_DATA", threshold, window, src, direction,
                            vintage_files=vintage_files, vintage_sha256=vintage_shas,
                            notes=f"No {country} observations in window {window}")

    sub = sub.sort_values("year").reset_index(drop=True)

    # ---------- Classifier: pick summary statistic ----------
    tl = threshold.lower()
    dl = (metric.get("description") or "").lower()
    combo = tl + " " + dl

    observed_value = None
    observed_stat_name = None
    observed_year = None

    # Case A: peak-to-trough decline (declining value over window)
    if any(k in combo for k in DECLINE_KEYWORDS) or "loss" in tl:
        # Handle 'absolute decline' for HDI-style metrics
        if "absolute" in tl or "absolute" in dl:
            baseline = sub["value"].iloc[0]
            trough = sub["value"].min()
            observed_value = baseline - trough
            observed_stat_name = "absolute_decline"
        else:
            baseline = sub["value"].iloc[0]  # use first observation in window as baseline
            # Or use the max (peak) if value appears to rise first then fall
            peak = sub["value"].max()
            trough = sub["value"].min()
            if peak == 0:
                observed_value = 0
            else:
                observed_value = (peak - trough) / peak * 100  # percent decline
            observed_stat_name = "peak_to_trough_pct_decline"
            observed_year = int(sub.loc[sub["value"].idxmin(), "year"]) if not sub.empty else None

    # Case B: 'gap' or 'ratio' between countries — need cross-country comparison
    # Use word-boundary matching so 'emigration' (which contains 'ratio' as a
    # substring) does NOT trigger this branch.
    elif _has_word(combo, "gap") or _has_word(combo, "ratio") or _has_word(combo, "difference"):
        return MetricResult(mid, "PENDING_EVAL", threshold, window, src, direction,
                            vintage_files=vintage_files, vintage_sha256=vintage_shas,
                            notes="cross-country gap/ratio requires dedicated cross-country evaluator; data present")

    # Case C: level threshold 'in any year' (e.g. poverty >70% in any year)
    elif any(k in combo for k in LEVEL_RATE_KEYWORDS):
        observed_value = float(sub["value"].max())
        observed_stat_name = "max_in_window"
        observed_year = int(sub.loc[sub["value"].idxmax(), "year"])

    # Case D: increase/reversal
    elif any(k in combo for k in INCREASE_KEYWORDS):
        baseline = sub["value"].iloc[0]
        peak = sub["value"].max()
        if baseline == 0:
            observed_value = None
        else:
            observed_value = (peak - baseline) / baseline * 100
        observed_stat_name = "pct_increase_from_baseline"
        observed_year = int(sub.loc[sub["value"].idxmax(), "year"])

    # Case E: count ('>=3 blackouts', '>=2 redenominations') — need external source
    elif any(k in tl for k in ("count", "number", "documented")) or re.search(r">=\s*\d+", tl):
        # If the data is a time-series, we can't auto-count discrete events
        return MetricResult(mid, "PENDING_EVAL", threshold, window, src, direction,
                            vintage_files=vintage_files, vintage_sha256=vintage_shas,
                            notes="count-based threshold requires event log; data not sufficient to auto-count",
                            observed_value=float(sub["value"].max()) if not sub.empty else None,
                            observed_stat_name="max_loaded_value")

    # Fallback: use max
    else:
        observed_value = float(sub["value"].max())
        observed_stat_name = "max_in_window_fallback"
        observed_year = int(sub.loc[sub["value"].idxmax(), "year"])

    # ---------- Apply threshold ----------
    met = _apply_numeric_threshold(observed_value, threshold)
    if met is None:
        return MetricResult(mid, "PENDING_EVAL", threshold, window, src, direction,
                            observed_value=observed_value,
                            observed_stat_name=observed_stat_name,
                            observed_year=observed_year,
                            vintage_files=vintage_files, vintage_sha256=vintage_shas,
                            notes="threshold expression unparseable by regex")
    return MetricResult(mid, "MET" if met else "NOT_MET", threshold, window, src, direction,
                        observed_value=observed_value,
                        observed_stat_name=observed_stat_name,
                        observed_year=observed_year,
                        vintage_files=vintage_files, vintage_sha256=vintage_shas)


# ---------------------------------------------------------------------------
# Hypothesis-level aggregation
# ---------------------------------------------------------------------------

def compute_verdict(results: list[MetricResult], support_threshold: int, refute_threshold: int) -> dict:
    """Apply the support/refute/inconclusive decision rule.

    The `direction` field on each metric flips MET/NOT_MET contribution:
    a refutes_claim metric that is MET is evidence AGAINST the hypothesis,
    so we invert its contribution when tallying.
    """
    met = 0
    not_met = 0
    pending_data = 0
    pending_eval = 0
    for r in results:
        if r.status == "MET":
            if r.direction == "refutes_claim":
                not_met += 1
            else:
                met += 1
        elif r.status == "NOT_MET":
            if r.direction == "refutes_claim":
                met += 1
            else:
                not_met += 1
        elif r.status == "PENDING_DATA":
            pending_data += 1
        else:  # PENDING_EVAL
            pending_eval += 1

    total = len(results)
    # Optimistic ceiling: if every pending resolved in favour of the hypothesis
    optimistic_met = met + pending_data + pending_eval
    # Pessimistic floor: currently MET only
    pessimistic_met = met

    if pessimistic_met >= support_threshold:
        verdict = "SUPPORTED"
        reason = f"{met} of {total} metrics met threshold (support threshold {support_threshold})"
    elif not_met >= (total - support_threshold + 1):
        # Mathematically impossible to reach support_threshold even if all pending MET
        verdict = "REFUTED"
        reason = f"{not_met} metrics failed and {pending_data + pending_eval} pending; cannot reach {support_threshold}"
    elif not_met <= refute_threshold and optimistic_met >= support_threshold:
        verdict = "INCONCLUSIVE_PENDING_DATA"
        reason = f"{met} metrics met, {pending_data + pending_eval} pending; {support_threshold - met} more need resolution"
    elif optimistic_met < support_threshold:
        verdict = "REFUTED"
        reason = f"Even with all pending resolving favourably ({optimistic_met} of {total}), cannot reach support threshold {support_threshold}"
    else:
        verdict = "INCONCLUSIVE"
        reason = f"{met} met / {not_met} failed / {pending_data} pending-data / {pending_eval} pending-eval"

    return {
        "verdict": verdict,
        "reason": reason,
        "counts": {
            "total": total,
            "met": met,
            "not_met": not_met,
            "pending_data": pending_data,
            "pending_eval": pending_eval,
            "optimistic_met_ceiling": optimistic_met,
        },
        "thresholds": {
            "support_threshold": support_threshold,
            "refute_threshold": refute_threshold,
        },
    }


# ---------------------------------------------------------------------------
# Run orchestration
# ---------------------------------------------------------------------------

def primary_country(spec: dict) -> str:
    """Return the primary ISO3 country for single-country canonical cases;
    for two-country system-comparison cases, return the first listed."""
    countries = spec.get("sample", {}).get("countries", [])
    return countries[0] if countries else "???"


def run_hypothesis(hid: str) -> dict:
    spec_path = find_hypothesis(hid)
    spec = yaml.safe_load(spec_path.read_text())

    if spec.get("evidence_type") != "canonical_case_multi_metric":
        raise ValueError(
            f"{hid} has evidence_type={spec.get('evidence_type')!r}; "
            f"this runner only handles canonical_case_multi_metric"
        )

    country = primary_country(spec)
    mmf = spec.get("multi_metric_falsification", {})
    support_threshold = mmf.get("support_threshold", 7)
    refute_threshold = mmf.get("refute_threshold", 3)

    metrics = spec.get("canonical_metrics", [])
    results: list[MetricResult] = []
    for m in metrics:
        r = evaluate_metric(m, country)
        results.append(r)

    agg = compute_verdict(results, support_threshold, refute_threshold)

    # ---------- Outputs ----------
    out_dir = RUNS_DIR / hid
    out_dir.mkdir(parents=True, exist_ok=True)

    # results table
    rows = [asdict(r) for r in results]
    pd.DataFrame(rows).to_parquet(out_dir / "metric_results.parquet", index=False)

    # diagnostics
    diag = {
        "hypothesis_id": hid,
        "evidence_type": "canonical_case_multi_metric",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "country": country,
        "verdict": agg["verdict"],
        "reason": agg["reason"],
        "counts": agg["counts"],
        "thresholds": agg["thresholds"],
        "metrics": rows,
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str) + "\n")

    # manifest (vintage pins)
    vintages = {}
    for r in results:
        for vf, sh in zip(r.vintage_files, r.vintage_sha256):
            vintages[vf] = sh
    (out_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": hid,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "evidence_type": "canonical_case_multi_metric",
        "vintages": [{"path": k, "sha256": v} for k, v in sorted(vintages.items())],
    }, sort_keys=False))

    # result card
    lines = _build_result_card(hid, spec, results, agg, country)
    (out_dir / "result_card.md").write_text("\n".join(lines) + "\n")

    return diag


def _build_result_card(hid: str, spec: dict, results: list[MetricResult], agg: dict, country: str) -> list[str]:
    verdict = agg["verdict"]
    counts = agg["counts"]
    supp_t = agg["thresholds"]["support_threshold"]
    refute_t = agg["thresholds"]["refute_threshold"]

    verdict_emoji = {
        "SUPPORTED": "supported",
        "REFUTED": "refuted",
        "INCONCLUSIVE": "inconclusive",
        "INCONCLUSIVE_PENDING_DATA": "inconclusive (data gaps)",
    }.get(verdict, verdict)

    claim = " ".join((spec.get("claim") or "").split())

    lines = [
        f"# Result card — {hid}",
        "",
        f"**Verdict:** {verdict_emoji}",
        "",
        f"**Reason:** {agg['reason']}",
        "",
        f"Pre-registered rule: SUPPORT if >= {supp_t} of {counts['total']} metrics met; "
        f"REFUTE if <= {refute_t} met (impossible to hit support).",
        "",
        f"**Counts:** {counts['met']} MET · {counts['not_met']} NOT_MET · "
        f"{counts['pending_data']} PENDING_DATA · {counts['pending_eval']} PENDING_EVAL",
        "",
        f"**Primary country:** {country}",
        "",
        "## Metric-by-metric",
        "",
        "| # | Metric | Status | Observed | Threshold | Notes |",
        "|---|---|:---:|---:|---|---|",
    ]
    for i, r in enumerate(results, 1):
        obs = ""
        if r.observed_value is not None:
            obs = f"{r.observed_value:.3g}"
            if r.observed_year:
                obs += f" ({r.observed_year})"
            if r.observed_stat_name:
                obs += f" [{r.observed_stat_name}]"
        notes = r.notes or ""
        if r.direction == "refutes_claim":
            notes = ("↔ refutes_claim direction; " + notes).strip("; ")
        lines.append(
            f"| {i} | {r.metric_id} | {r.status} | {obs} | `{r.threshold}` | {notes} |"
        )
    lines += [
        "",
        "## Claim",
        "",
        f"> {claim}",
        "",
        "## Interpretation",
        "",
    ]
    if verdict == "SUPPORTED":
        lines.append(
            f"The canonical-case pattern match is satisfied: {counts['met']} of {counts['total']} "
            f"pre-registered metrics meet their thresholds, above the support threshold of {supp_t}. "
            "Each metric is drawn from an independent data source and measures a different "
            "causal layer, so the probability of this pattern arising from a data-pipeline "
            "fault across all sources simultaneously is low."
        )
    elif verdict == "REFUTED":
        lines.append(
            f"The canonical-case pattern match is not satisfied: only {counts['met']} of "
            f"{counts['total']} metrics met their thresholds, below the support threshold "
            f"of {supp_t}. Note that for canonical-case hypotheses, a refutation can "
            "indicate either that the hypothesis is genuinely weak, that the metric set "
            "is mis-calibrated (too strict), or that the data substrate has systematic "
            "gaps. Review the PENDING_DATA / PENDING_EVAL metrics before accepting the "
            "refutation."
        )
    else:
        lines.append(
            f"Verdict is **{verdict_emoji}** — {counts['pending_data']} metric(s) cannot "
            f"be evaluated because the underlying data source is not yet in the vintages "
            f"pipeline, and {counts['pending_eval']} metric(s) have data but a threshold "
            f"expression the auto-evaluator does not recognise (complex conditions, "
            "discrete event counts, cross-country gaps). Close these gaps then re-run."
        )

    lines += [
        "",
        "## Steelman live concerns",
        "",
        f"See `{spec.get('steelman','')}` for the strongest opposing arguments. "
        "Canonical-case multi-metric evidence is a pattern match, not a causal "
        "identification — the result card should be read as 'outcome trajectory "
        "matches the predicted pattern to degree X' rather than 'policy P caused "
        "the outcome'.",
        "",
        "## Provenance",
        "",
        "Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in "
        "`diagnostics.json`. Machine-readable results in `metric_results.parquet`.",
    ]
    return lines


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def list_multi_metric_hypotheses() -> list[str]:
    """Find every hypothesis yaml with evidence_type: canonical_case_multi_metric."""
    out = []
    for p in HYPOTHESES_DIR.glob("*/*.yaml"):
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if isinstance(spec, dict) and spec.get("evidence_type") == "canonical_case_multi_metric":
            out.append(spec.get("hypothesis_id", p.stem))
    return sorted(set(out))


def _has_committed_bespoke_verdict(hid: str) -> bool:
    """True if engine/runs/<hid>/diagnostics.json is git-tracked AND has a
    non-empty `verdict` field that isn't a vanilla INCONCLUSIVE / 0-metrics
    placeholder. Prevents this generic runner from clobbering hand-tuned
    bespoke runs (e.g. japan_stagnation_wellbeing_outcomes' detailed
    supported_subset analysis with 6/7 indicator-results)."""
    diag_path = RUNS_DIR / hid / "diagnostics.json"
    if not diag_path.exists():
        return False
    try:
        import subprocess as _sp
        ls = _sp.run(
            ["git", "ls-files", "--error-unmatch", str(diag_path)],
            cwd=str(diag_path.parent.parent.parent),
            capture_output=True, text=True, timeout=5,
        )
        if ls.returncode != 0:
            return False  # not committed
        import json as _json
        d = _json.loads(diag_path.read_text())
    except Exception:
        return False
    verdict = (d.get("verdict") or "").upper()
    counts = d.get("counts") or {}
    total_met_or_not = (counts.get("met", 0) + counts.get("not_met", 0))
    # Skip if verdict is a real label (any non-INCONCLUSIVE) AND has at least
    # one resolved metric, OR has a custom verdict label like "supported_subset".
    if not verdict:
        return False
    if verdict.startswith("INCONCLUSIVE"):
        return False  # always OK to refresh INCONCLUSIVE
    if total_met_or_not > 0:
        return True   # bespoke run with real metrics — preserve
    if any(k in verdict.lower() for k in ("subset", "partial", "bespoke")):
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("hypothesis_id", nargs="?", help="hypothesis_id to run")
    g.add_argument("--all", action="store_true", help="run every canonical_case_multi_metric hypothesis")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite committed bespoke verdicts (default: skip).")
    args = ap.parse_args()

    if args.all:
        hids = list_multi_metric_hypotheses()
        print(f"Running {len(hids)} canonical_case_multi_metric hypotheses...")
    else:
        hids = [args.hypothesis_id]

    results_summary = []
    exit_code = 0
    for hid in hids:
        if not args.force and _has_committed_bespoke_verdict(hid):
            print(f"  · {hid}: skipped (committed bespoke verdict already on disk)")
            continue
        try:
            diag = run_hypothesis(hid)
            counts = diag["counts"]
            line = (
                f"  {diag['verdict']:<28s} {hid}  "
                f"[{counts['met']}M/{counts['not_met']}N/{counts['pending_data']}PD/{counts['pending_eval']}PE]"
            )
            print(line)
            results_summary.append({"hid": hid, "verdict": diag["verdict"], "counts": counts})
        except Exception as e:
            print(f"  ERROR {hid}: {e}", file=sys.stderr)
            exit_code = 1
            results_summary.append({"hid": hid, "verdict": "ERROR", "error": str(e)})

    if args.all:
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for s in results_summary:
            if "error" in s:
                print(f"  {s['hid']:<60s} ERROR: {s['error']}")
            else:
                c = s["counts"]
                print(
                    f"  {s['hid']:<60s} {s['verdict']:<28s} "
                    f"{c['met']}/{c['total']} met  "
                    f"({c['pending_data']} pending-data, {c['pending_eval']} pending-eval)"
                )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
