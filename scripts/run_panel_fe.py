#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = panel_fe (or
panel_fe_decomposition).

For each spec, this script:

  1. Resolves variable source tokens (publisher:series) against
     data/vintages/<publisher>/<series>/<latest>.parquet.
  2. Normalises each variable parquet to (country_iso3, year, value).
  3. Pivots into a long-form panel (country × year × {outcome, treatment,
     controls}).
  4. Fits a PanelOLS regression with the spec's `estimator.fixed_effects`
     and country-clustered SEs.
  5. Compares the treatment coefficient direction + p-value to the
     `falsification.rule` and writes a verdict.
  6. Writes engine/runs/<hid>/result_card.md and diagnostics.json.

Verdicts:
  SUPPORTED                  — coefficient sign matches the claim AND p < 0.10.
  REFUTED                    — coefficient sign opposite the claim AND p < 0.10.
  PARTIAL                    — coefficient sign matches but p >= 0.10, OR
                                opposite sign with p >= 0.10.
  INCONCLUSIVE_DATA_PENDING  — outcome variable could not be loaded from
                                vintages (data not yet fetched / publisher
                                schema unknown).

Usage:
    python3 scripts/run_panel_fe.py <hypothesis_id>
    python3 scripts/run_panel_fe.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages"
RUNS = ROOT / "engine" / "runs"

# ---------------------------------------------------------------------------
# Vintage resolution
# ---------------------------------------------------------------------------


def latest_vintage(publisher: str, series: str) -> Path | None:
    """Return the most recent .parquet under data/vintages/<publisher>/<series>/.

    Different fetchers use different on-disk layouts:
      - world_bank_wdi: data/vintages/world_bank_wdi/<series>@<utc>.parquet
      - eurostat:       data/vintages/eurostat/<dataset>@<utc>.parquet
      - oecd:           data/vintages/oecd/<full-SDMX-URN-with-dots-and-commas-mangled>@<utc>.parquet
        (e.g. "OECD.SDD.TPS,DSD_TU@DF_TUD,1.0" becomes "OECD.SDD.TPS_DSD_TU_DF_TUD_1.0")
      - fred / boj / ecb: a few use nested <series>/<utc>.parquet directories.

    Try several patterns:
      1. Exact: data/vintages/<pub>/<series>@*.parquet
      2. Nested: data/vintages/<pub>/<series>/*.parquet
      3. Fuzzy contains: any file whose name (with @ and , and : stripped) contains the series.
    """
    pub_dir = VINTAGES / publisher
    if not pub_dir.exists():
        return None

    # 1. Exact prefix match: <series>@... or <series>.parquet
    candidates = list(pub_dir.glob(f"{series}@*.parquet"))
    candidates.extend(pub_dir.glob(f"{series}.parquet"))
    # 2. Nested directory layout
    nested = pub_dir / series
    if nested.exists():
        candidates.extend(nested.glob("*.parquet"))
    # 3. Fuzzy: normalise both filename and series, look for substring containment.
    if not candidates:
        def norm(s: str) -> str:
            return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
        target = norm(series)
        for f in pub_dir.glob("*.parquet"):
            stem = f.stem.split("@", 1)[0]  # drop UTC stamp
            if target and target in norm(stem):
                candidates.append(f)
        # Also peek into one level of subdirectory
        for sub in pub_dir.iterdir():
            if sub.is_dir():
                for f in sub.glob("*.parquet"):
                    stem = f.stem.split("@", 1)[0]
                    if target and (target in norm(stem) or target in norm(sub.name)):
                        candidates.append(f)
    if not candidates:
        return None
    # Lexicographic max picks most recent UTC stamp.
    return max(candidates, key=lambda p: p.name)


def normalise_panel(df: pd.DataFrame, publisher: str) -> pd.DataFrame | None:
    """Project an arbitrary publisher's parquet schema onto (country_iso3, year, value).

    Returns None if the schema can't be normalised.
    """
    cols = {c.lower(): c for c in df.columns}
    # Discover the country column.
    country_col = None
    for cand in ("country_iso3", "iso3", "geo_code", "country", "ref_area"):
        if cand in cols:
            country_col = cols[cand]
            break
    if country_col is None:
        # Single-country fetchers (FRED, BoE) — country defaults to a publisher-specific code.
        single_country_fallback = {
            "fred": "USA", "bls": "USA", "boe": "GBR", "boj": "JPN",
            "shiller": "USA", "rba": "AUS", "apra": "AUS", "statcan": "CAN",
            "bcra": "ARG", "bcv": "VEN", "cbr": "RUS", "cia": "USA",
            "destatis": "DEU", "destatis_germany": "DEU",
        }
        if publisher in single_country_fallback:
            df = df.copy()
            df["country_iso3"] = single_country_fallback[publisher]
            country_col = "country_iso3"
        else:
            return None
    # Discover the year column.
    year_col = None
    for cand in ("year", "period", "date", "obs_date", "time_period"):
        if cand in cols:
            year_col = cols[cand]
            break
    if year_col is None:
        return None
    # Discover the value column.
    value_col = None
    for cand in ("value", "obs_value", "gdppc", "rgdpe", "rgdpe_pc", "rtfpna",
                 "labsh", "v2x_polyarchy", "polity2", "freedom_house_score"):
        if cand in cols:
            value_col = cols[cand]
            break
    if value_col is None:
        # Maddison-style: pick the first numeric column that isn't year/pop.
        for c in df.columns:
            if c not in (country_col, year_col) and pd.api.types.is_numeric_dtype(df[c]):
                value_col = c
                break
    if value_col is None:
        return None

    out = df[[country_col, year_col, value_col]].copy()
    out.columns = ["country_iso3", "year", "value"]
    # Coerce year — eurostat 'period' is sometimes "2020-Q1" or "2020-01"; take year prefix.
    if not pd.api.types.is_numeric_dtype(out["year"]):
        out["year"] = pd.to_datetime(out["year"], errors="coerce").dt.year
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["country_iso3", "year", "value"])
    # If multiple rows per (country, year), aggregate via mean (handles SDMX dim duplicates).
    out = out.groupby(["country_iso3", "year"], as_index=False)["value"].mean()
    return out


def parse_source(token: str) -> tuple[str, str] | None:
    """Parse a SINGLE 'publisher:series' token. For multi-fallback strings
    (e.g. 'ons:CDKO; world_bank_wdi:FP.CPI.TOTL.ZG'), use parse_sources()."""
    m = re.match(r"^\s*([a-z][a-z0-9_]*)\s*:\s*(.+?)\s*$", token)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def parse_sources(source: str) -> list[tuple[str, str]]:
    """Parse a source string into one or more (publisher, series) candidates.

    Many hypothesis specs use ';'-delimited fallback chains, e.g.
    'ons:CDKO; world_bank_wdi:FP.CPI.TOTL.ZG'. Loaders should iterate these
    candidates in order, returning the first one whose vintage resolves.
    """
    out: list[tuple[str, str]] = []
    for raw in (source or "").split(";"):
        part = raw.strip()
        if not part or ":" not in part:
            continue
        pub, _, series = part.partition(":")
        # Trim trailing country qualifiers like '(VEN)' or '(GBR, USA)'
        series = re.sub(r"\s*\([^)]*\)\s*$", "", series).strip()
        # Drop any trailing punctuation
        series = series.rstrip(",.; ")
        if pub.strip() and series:
            out.append((pub.strip(), series))
    return out


_META_PREFIXES = {"constructed", "derived", "manual", "academic", "proxies",
                  "fallback", "microdata", "dates"}


def load_variable(source: str) -> tuple[pd.DataFrame, str] | None:
    """Try each candidate (publisher, series) in the source string in order
    and return the first one whose vintage exists and parses.

    Supports ';'-delimited fallback chains.
    """
    for pub, series in parse_sources(source):
        if pub in _META_PREFIXES:
            continue
        path = latest_vintage(pub, series)
        if path is None:
            continue
        try:
            df = pd.read_parquet(path)
        except Exception:
            continue
        panel = normalise_panel(df, pub)
        if panel is None or panel.empty:
            continue
        return panel, pub
    return None


def transform(s: pd.Series, kind: str) -> pd.Series:
    kind = (kind or "level").lower()
    if kind in ("level", "raw"):
        return s
    if kind == "log":
        return np.log(s.where(s > 0))
    if kind in ("diff", "first_diff"):
        return s.diff()
    if kind in ("yoy", "log_diff"):
        return np.log(s.where(s > 0)).diff()
    return s


# ---------------------------------------------------------------------------
# Spec loading
# ---------------------------------------------------------------------------


def load_spec(hid: str) -> tuple[Path, dict] | None:
    for p in (ROOT / "hypotheses").glob(f"**/{hid}.yaml"):
        with p.open() as f:
            return p, yaml.safe_load(f)
    return None


_STUB_RULE_MARKER = "when this stub is promoted from draft"


def is_stub_falsification_rule(spec: dict) -> bool:
    """True iff the spec's falsification.rule is still the generic stub-promotion
    boilerplate AND the methodology_note doesn't document the dispositive
    sharpening. Runners use this to refuse to grade — they emit
    `inconclusive — falsification rule not sharpened` instead, so auto-grader
    output never gets attached to a non-promoted spec.

    See post-mortem in commit bba6f644 for the failure mode this prevents.
    """
    rule = ((spec.get("falsification") or {}).get("rule") or "").lower()
    if _STUB_RULE_MARKER not in rule:
        return False
    mn = (spec.get("methodology_note") or "").lower()
    if any(k in mn for k in ("dispositive", "sharpened", "primary (dispositive")):
        return False
    return True


def list_panel_fe_specs() -> list[str]:
    derived = ROOT / "engine" / "runnability.derived.yaml"
    with derived.open() as f:
        d = yaml.safe_load(f)
    return [
        h["hypothesis_id"]
        for h in d["hypotheses"]
        if h["estimator_template"] in ("panel_fe", "panel_fe_decomposition")
    ]


# ---------------------------------------------------------------------------
# Estimator
# ---------------------------------------------------------------------------


def build_panel(spec: dict) -> tuple[pd.DataFrame, dict]:
    """Build (country, year)-indexed panel from spec's variables.

    Returns (long_panel, status) where status records which variables loaded
    or failed.
    """
    status: dict = {"variables_loaded": [], "variables_missing": []}
    frames: list[pd.DataFrame] = []
    var_blocks = spec.get("variables") or {}
    for role in ("outcome", "treatment", "controls"):
        items = var_blocks.get(role) or []
        for item in items:
            name = item.get("name")
            source = item.get("source", "")
            kind = item.get("transformation", "level")
            if not name or not source:
                continue
            res = load_variable(source)
            if res is None:
                status["variables_missing"].append(
                    {"role": role, "name": name, "source": source}
                )
                continue
            df, pub = res
            df = df.copy()
            df["value"] = transform(df["value"], kind)
            df.rename(columns={"value": name}, inplace=True)
            df["_role"] = role
            frames.append(df[["country_iso3", "year", name]])
            status["variables_loaded"].append(
                {"role": role, "name": name, "source": source, "publisher": pub,
                 "n_rows": int(len(df))}
            )

    if not frames:
        return pd.DataFrame(), status

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country_iso3", "year"], how="outer")
    return panel, status


def filter_sample(panel: pd.DataFrame, spec: dict) -> pd.DataFrame:
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    period = sample.get("period") or [None, None]
    out = panel.copy()
    if countries:
        out = out[out["country_iso3"].isin(countries)]
    if period[0] is not None:
        out = out[out["year"] >= int(period[0])]
    if period[1] is not None:
        out = out[out["year"] <= int(period[1])]
    return out


def run_panel_ols(
    panel: pd.DataFrame, spec: dict, outcome_name: str, treatment_name: str
) -> dict:
    """Fit a panel regression of outcome on treatment (+ controls) with FE.

    Falls back to dummy-encoded OLS if linearmodels isn't available.
    """
    var_blocks = spec.get("variables") or {}
    control_names = [c["name"] for c in (var_blocks.get("controls") or []) if c.get("name")]
    fe_spec = (spec.get("estimator") or {}).get("fixed_effects", []) or []
    cluster_spec = (spec.get("estimator") or {}).get("clustering", "country")

    # Drop rows missing outcome or treatment.
    needed = [outcome_name, treatment_name] + [c for c in control_names if c in panel.columns]
    sub = panel[["country_iso3", "year"] + needed].dropna()
    if sub.empty or len(sub) < 30:
        return {"error": f"insufficient observations after listwise deletion ({len(sub)})"}

    try:
        from linearmodels.panel import PanelOLS

        sub = sub.set_index(["country_iso3", "year"])
        rhs = [treatment_name] + [c for c in control_names if c in sub.columns]
        exog = sub[rhs]
        endog = sub[outcome_name]
        entity = "country" in [str(x).lower() for x in fe_spec]
        time = "year" in [str(x).lower() for x in fe_spec]
        # Default to two-way FE if unspecified.
        if not entity and not time:
            entity, time = True, True
        mod = PanelOLS(endog, exog, entity_effects=entity, time_effects=time,
                       drop_absorbed=True)
        cluster_kw = {}
        if "country" in cluster_spec.lower():
            cluster_kw = {"cov_type": "clustered", "cluster_entity": True}
        elif "year" in cluster_spec.lower():
            cluster_kw = {"cov_type": "clustered", "cluster_time": True}
        else:
            cluster_kw = {"cov_type": "robust"}
        res = mod.fit(**cluster_kw)
        coef = float(res.params[treatment_name])
        se = float(res.std_errors[treatment_name])
        pval = float(res.pvalues[treatment_name])
        nobs = int(res.nobs)
        return {
            "coefficient": coef,
            "std_error": se,
            "p_value": pval,
            "n_obs": nobs,
            "n_countries": int(sub.index.get_level_values(0).nunique()),
            "r_squared_within": float(res.rsquared_within or 0),
            "fe_entity": entity,
            "fe_time": time,
            "cluster": cluster_spec,
            "method": "linearmodels.PanelOLS",
        }
    except Exception as exc:
        return {"error": f"linearmodels failed: {exc}"}


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

# Verb-based claim-direction lexicon. Tuned for first-sentence parsing of
# typical IESET claims ("X increased Y", "X reduced Y", etc). Words appear
# all over the disclosure/notes/falsification text, which is why the previous
# whole-text counter produced spurious "ambiguous" verdicts. We restrict to
# the FIRST SENTENCE of `claim` and look only for predicate verbs.
_PLUS_VERBS = {
    "increased", "increases", "increase", "raised", "raises", "raise",
    "rose", "rises", "rise", "boosted", "boosts", "boost",
    "expanded", "expands", "expand", "accelerated", "accelerates",
    "acceleration", "growth",
    "improved", "improves", "improve", "elevated", "elevates",
    "higher", "more", "exceeds", "exceeded",
    "lifts", "lifted", "grew", "grows",
    "outpaced", "outperformed", "outperforms",
    "larger", "stronger", "greater",
    "predict", "predicts", "predicted",  # cross-sectional claims
}
_MINUS_VERBS = {
    "decreased", "decreases", "decrease", "reduced", "reduces", "reduce",
    "declined", "declines", "decline", "lowered", "lowers", "lower",
    "fell", "falls", "fall", "shrank", "shrinks", "shrink",
    "weakened", "weakens", "weaken", "compressed", "compresses",
    "less", "fewer", "below",
    "worsened", "worsens", "worsen", "deteriorated", "deteriorates",
    "underperformed", "underperforms",
    "depressed", "depresses",
    "smaller", "weaker", "lower", "stagnated", "stagnates",
    "collapsed", "collapses", "collapse",
}

# Hypothesis-ID suffix shortcuts — many specs encode direction in the slug.
_ID_SUFFIX_DIR = {
    "growth_acceleration": "+", "growth_collapse": "-",
    "expansion": "+", "decline": "-", "contraction": "-",
    "improvement": "+", "deterioration": "-",
    "rise": "+", "fall": "-",
    "outperforms": "+", "underperforms": "-",
    "above": "+", "below": "-",
}


def infer_claim_direction(spec: dict) -> str:
    """Return '+' / '-' / '?' for the first-sentence prediction direction.

    Strategy:
      1. Read explicit `claim_direction` field if present (preferred).
      2. Else: look at FIRST sentence of `claim` only (typically the
         testable prediction). Count predicate verbs from the +/- lexicons.
      3. Falsification.test as tiebreaker.
    """
    explicit = spec.get("claim_direction")
    if explicit in ("+", "-", "?"):
        return explicit
    if explicit in ("plus", "positive", "increase", "supported"):
        return "+"
    if explicit in ("minus", "negative", "decrease", "refuted"):
        return "-"

    import re as _re

    # 1. Slug-suffix shortcut. Many hypothesis_ids encode direction.
    hid = (spec.get("hypothesis_id") or "").lower()
    for suffix, d in _ID_SUFFIX_DIR.items():
        if suffix in hid:
            return d

    claim = (spec.get("claim") or "").strip()
    if not claim:
        return "?"
    # 2. First sentence of `claim`
    first = _re.split(r"(?<=[.!?])\s+", claim, maxsplit=1)[0].lower()
    plus = sum(1 for v in _PLUS_VERBS if _re.search(rf"\b{v}\b", first))
    minus = sum(1 for v in _MINUS_VERBS if _re.search(rf"\b{v}\b", first))
    if plus > minus:
        return "+"
    if minus > plus:
        return "-"
    # 3. Falsification.test as tiebreaker
    test = ((spec.get("falsification") or {}).get("test") or "").lower()
    if test:
        plus_t = sum(1 for v in _PLUS_VERBS if _re.search(rf"\b{v}\b", test))
        minus_t = sum(1 for v in _MINUS_VERBS if _re.search(rf"\b{v}\b", test))
        if plus_t > minus_t: return "+"
        if minus_t > plus_t: return "-"
    return "?"


def verdict_from_estimate(est: dict, claim_dir: str) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]
    coef = est["coefficient"]
    pval = est["p_value"]
    sign = "+" if coef >= 0 else "-"
    alpha = 0.10
    if pval < alpha:
        if claim_dir == "?":
            return ("PARTIAL",
                    f"coef={coef:+.4g}, p={pval:.3g}; claim direction not auto-inferred")
        if sign == claim_dir:
            return ("SUPPORTED",
                    f"coef={coef:+.4g} (sign matches claim {claim_dir}), p={pval:.3g}")
        return ("REFUTED",
                f"coef={coef:+.4g} (sign opposite claim {claim_dir}), p={pval:.3g}")
    return ("PARTIAL",
            f"coef={coef:+.4g}, p={pval:.3g} (above α=0.10); direction inconclusive")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_outputs(hid: str, spec: dict, status: dict, est: dict,
                  verdict: str, reason: str) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)

    diag = {
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": (spec.get("estimator") or {}).get("template"),
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": est,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_panel_fe.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))

    md = [
        f"# Result card — {hid}",
        "",
        f"**Verdict:** {verdict} — {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test','').strip()}",
        "",
        "## Estimate",
    ]
    if "error" in est:
        md.append(f"- _Error:_ {est['error']}")
    else:
        md.extend([
            f"- Method: {est.get('method')}",
            f"- Coefficient (treatment): **{est['coefficient']:+.4g}**",
            f"- Std error: {est['std_error']:.4g}",
            f"- p-value: **{est['p_value']:.3g}**",
            f"- Observations: {est['n_obs']}, countries: {est['n_countries']}",
            f"- Within R²: {est['r_squared_within']:.3g}",
            f"- Fixed effects: entity={est['fe_entity']}, time={est['fe_time']}",
            f"- Clustering: {est['cluster']}",
        ])
    md.append("")
    md.append("## Variables resolved")
    if status["variables_loaded"]:
        for v in status["variables_loaded"]:
            md.append(f"- `{v['source']}` → {v['name']} ({v['role']}, "
                      f"publisher={v['publisher']}, n={v['n_rows']})")
    if status["variables_missing"]:
        md.append("\n### Variables missing data")
        for v in status["variables_missing"]:
            md.append(f"- `{v['source']}` ({v['role']}, name={v['name']}) — vintage not on disk")

    md.append("")
    md.append(f"_Generated by `scripts/run_panel_fe.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


_REAL_VERDICT_PREFIXES = (
    "SUPPORTED", "REFUTED", "PARTIAL", "MIXED", "WEAKLY",
    "WEAKENED", "NOT SUPPORTED", "NOT_SUPPORTED", "BLOCKED",
)


def has_committed_verdict(hid: str) -> bool:
    """True if engine/runs/<hid>/diagnostics.json exists with a real prior
    verdict (not INCONCLUSIVE). Used to prevent generic-runner output from
    clobbering bespoke prior run artifacts.

    Reads BOTH `verdict_label` (new schema) and `verdict` (legacy free-text,
    case-insensitive) so handcrafted artifacts like 'refuted — gap +0.74...'
    are properly protected.
    """
    diag = RUNS / hid / "diagnostics.json"
    if not diag.exists():
        return False
    try:
        import json as _json
        d = _json.loads(diag.read_text())
    except Exception:
        return False
    label = (d.get("verdict_label") or "").upper()
    free_text = (d.get("verdict") or "").upper().lstrip()
    is_inconclusive = (
        label == "INCONCLUSIVE_DATA_PENDING"
        or free_text.startswith("INCONCLUSIVE")
    )
    if is_inconclusive:
        return False  # OK to overwrite — was waiting on data, may have it now
    is_real = (
        label in _REAL_VERDICT_PREFIXES
        or any(free_text.startswith(p) for p in _REAL_VERDICT_PREFIXES)
    )
    if is_real:
        # Real verdict — protect from overwrite regardless of git-tracking
        # status (uncommitted handcrafted artifacts also worth preserving).
        return True
    if label or free_text:
        # Some other verdict label we don't recognise — be conservative,
        # check git-tracked status as a tiebreaker.
        import subprocess
        try:
            r = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(diag.relative_to(ROOT))],
                cwd=str(ROOT), capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0
        except Exception:
            return True  # Conservative: assume committed
    return False


def run_one(hid: str, verbose: bool = True, force: bool = False) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if found is None:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    # Integrity gate: refuse to grade against a stub falsification rule.
    # The auto-grader's verdicts are only meaningful against a dispositive
    # pre-registered threshold; running against the generic boilerplate
    # ("…when this stub is promoted from draft") would attach a fake-clean
    # verdict to a non-promoted spec. See post-mortem (commit bba6f644).
    if is_stub_falsification_rule(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "falsification rule not sharpened — auto-grader refuses to "
            "grade against the generic stub boilerplate. Promote the spec "
            "(replace falsification.rule with a dispositive threshold AND "
            "document the sharpening in methodology_note) before running."
        )
        write_outputs(hid, spec, {"variables_loaded": [], "variables_missing": []}, {"error": reason}, {}, verdict, reason, None)
        return f"  ⚠ {hid}: {verdict} (stub rule, refused to grade)"

    panel, status = build_panel(spec)

    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    treatment_items = var_blocks.get("treatment") or []
    if not outcome_items or not treatment_items:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = "no outcome or no treatment variable in spec"
        write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ⚠ {hid}: {verdict} — {reason}"

    outcome_name = outcome_items[0]["name"]
    treatment_name = treatment_items[0]["name"]
    if outcome_name not in panel.columns:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        missing = [v["source"] for v in status["variables_missing"]
                   if v["role"] == "outcome"]
        reason = f"outcome '{outcome_name}' not loaded; missing: {missing}"
        write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"
    if treatment_name not in panel.columns:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        missing = [v["source"] for v in status["variables_missing"]
                   if v["role"] == "treatment"]
        reason = f"treatment '{treatment_name}' not loaded; missing: {missing}"
        write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"

    panel_filt = filter_sample(panel, spec)
    est = run_panel_ols(panel_filt, spec, outcome_name, treatment_name)
    claim_dir = infer_claim_direction(spec)
    verdict, reason = verdict_from_estimate(est, claim_dir)
    write_outputs(hid, spec, status, est, verdict, reason)

    icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
            "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
    return f"  {icon} {hid}: {verdict} — {reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?")
    parser.add_argument("--all", action="store_true",
                        help="Run every panel_fe / panel_fe_decomposition spec.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing committed verdicts (default skips).")
    args = parser.parse_args()

    if args.all:
        ids = list_panel_fe_specs()
        print(f"Running {len(ids)} panel_fe specs…")
        for hid in ids:
            try:
                print(run_one(hid, force=args.force))
            except Exception as exc:
                print(f"  ✗ {hid}: runner crashed — {exc}")
                traceback.print_exc()
        return 0
    if not args.hypothesis_id:
        parser.error("Pass <hypothesis_id> or --all.")
    print(run_one(args.hypothesis_id, force=args.force))
    return 0


if __name__ == "__main__":
    sys.exit(main())
