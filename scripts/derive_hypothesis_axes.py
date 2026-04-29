#!/usr/bin/env python3
"""Derive an index of axes each hypothesis tests.

Each hypothesis in the library is an empirical test of a policy-content
claim. That claim almost always corresponds to one or more canonical axes
from `axes.yaml`. This script derives those axis tags from each
hypothesis's existing content and emits a canonical index at
`hypotheses/_axis_index.yaml` that the frontend consumes to match
policies/movements to the hypotheses that test them.

Signals combined per hypothesis:
  1. Topic folder — primes the candidate channels (fiscal / regulatory / ...).
  2. Direct keyword cues — hand-curated phrase → axis overrides (highest weight).
  3. Axis descriptions + direction semantics — keyword bag for fuzzy match.
  4. Variable names (outcome / treatment / decomposition_channels) — literal
     token match against axis keyword bag.

Output is not authoritative; it is a proposed mapping that a human can
audit and override by editing the generated YAML.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import yaml

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"
POS_ROOT = REPO / "positions"
AXES_FILE = REPO / "axes.yaml"
OUT_FILE = HYP_ROOT / "_axis_index.yaml"
POS_OUT_FILE = POS_ROOT / "_axis_index.yaml"
SKIP_DIRS = {"steelman", "conditional_taxonomy", "country_year_ideology"}

# Per-axis hand-curated phrase cues — the highest-weight signal.
# Phrase → [axis_ids]. Phrases match as whole words (case-insensitive).
PHRASE_CUES: dict[str, list[str]] = {
    # --- fiscal ---
    "tax progressivity": ["fiscal.tax_progressivity"],
    "progressive tax": ["fiscal.tax_progressivity"],
    "top marginal": ["fiscal.tax_progressivity"],
    "eitc": ["fiscal.tax_progressivity"],
    "corporate tax": ["fiscal.tax_corporate"],
    "wealth tax": ["fiscal.tax_capital"],
    "capital gains": ["fiscal.tax_capital"],
    "inheritance tax": ["fiscal.tax_capital"],
    "estate tax": ["fiscal.tax_capital"],
    "transfer programme": ["fiscal.transfer_expansion"],
    "transfer program": ["fiscal.transfer_expansion"],
    "unemployment benefit": ["fiscal.transfer_expansion"],
    "universal basic income": ["fiscal.transfer_expansion"],
    "child benefit": ["fiscal.transfer_expansion"],
    "welfare spending": ["fiscal.transfer_expansion", "fiscal.spending_level"],
    "government spending": ["fiscal.spending_level"],
    "public spending": ["fiscal.spending_level"],
    "fiscal discipline": ["fiscal.spending_level"],
    "austerity": ["fiscal.spending_level"],
    "debt-to-gdp": ["fiscal.spending_level"],
    "industrial policy": ["fiscal.sectoral_subsidy"],
    "industrial subsidy": ["fiscal.sectoral_subsidy"],
    "sectoral subsidy": ["fiscal.sectoral_subsidy"],
    "chips act": ["fiscal.sectoral_subsidy"],
    "ira subsidies": ["fiscal.sectoral_subsidy"],
    "green hydrogen": ["fiscal.sectoral_subsidy"],
    # --- regulatory ---
    "minimum wage": ["regulatory.labour_market_flexibility"],
    "employment protection": ["regulatory.labour_market_flexibility"],
    "hiring and firing": ["regulatory.labour_market_flexibility"],
    "collective bargaining": ["regulatory.labour_market_flexibility"],
    "union density": ["regulatory.labour_market_flexibility"],
    "labour market flexibility": ["regulatory.labour_market_flexibility"],
    "hartz reform": ["regulatory.labour_market_flexibility"],
    "product market regulation": ["regulatory.product_market_competition"],
    "entry barrier": ["regulatory.product_market_competition"],
    "rent control": ["regulatory.product_market_competition"],
    "price control": ["regulatory.product_market_competition"],
    "licensing": ["regulatory.sectoral_licensing"],
    "concession": ["regulatory.sectoral_licensing"],
    "environmental regulation": ["regulatory.environmental_stringency"],
    "emissions cap": ["regulatory.environmental_stringency"],
    "carbon pricing": ["regulatory.environmental_stringency"],
    "carbon tax": ["regulatory.environmental_stringency"],
    "renewable portfolio": ["regulatory.environmental_stringency"],
    "energiewende": [
        "regulatory.environmental_stringency",
        "regulatory.energy_supply_security",
    ],
    "energy supply security": ["regulatory.energy_supply_security"],
    "nuclear phase": ["regulatory.energy_supply_security"],
    "financial regulation": ["regulatory.financial_deregulation"],
    "financial deregulation": ["regulatory.financial_deregulation"],
    "banking deregulation": ["regulatory.financial_deregulation"],
    "basel": ["regulatory.financial_deregulation"],
    "glass-steagall": ["regulatory.financial_deregulation"],
    "immigration": ["regulatory.immigration_openness"],
    "asylum": ["regulatory.immigration_openness"],
    "migration openness": ["regulatory.immigration_openness"],
    "work visa": ["regulatory.immigration_openness"],
    "trade openness": ["regulatory.trade_openness"],
    "tariff": ["regulatory.trade_openness"],
    "free trade": ["regulatory.trade_openness"],
    "protectionism": ["regulatory.trade_openness"],
    "import substitution": ["regulatory.trade_openness"],
    "trade liberalisation": ["regulatory.trade_openness"],
    # --- monetary ---
    "central bank independence": ["monetary.central_bank_independence"],
    "fiscal dominance": ["monetary.central_bank_independence"],
    "money supply": ["monetary.monetary_expansion_direction"],
    "quantitative easing": ["monetary.monetary_expansion_direction"],
    "monetary expansion": ["monetary.monetary_expansion_direction"],
    "m2 expansion": ["monetary.monetary_expansion_direction"],
    "hyperinflation": ["monetary.monetary_expansion_direction"],
    "currency board": ["monetary.central_bank_independence"],
    # --- institutional ---
    "rule of law": ["institutional.rule_of_law"],
    "contract enforcement": ["institutional.rule_of_law"],
    "corruption": ["institutional.rule_of_law"],
    "property rights": ["institutional.property_rights"],
    "expropriation": ["institutional.property_rights"],
    "nationalisation": ["institutional.property_rights"],
    "nationalization": ["institutional.property_rights"],
    "land reform": ["institutional.property_rights"],
    "judicial independence": ["institutional.judicial_independence"],
    "court-packing": ["institutional.judicial_independence"],
    "court packing": ["institutional.judicial_independence"],
    "selective prosecution": ["institutional.judicial_independence"],
    "constitutional chamber": ["institutional.judicial_independence"],
    "supreme court": ["institutional.judicial_independence"],
    "judicial reshuffle": ["institutional.judicial_independence"],
    # --- broad framework / country-regime cases ---
    "shock therapy": [
        "fiscal.spending_level",
        "regulatory.trade_openness",
        "regulatory.product_market_competition",
    ],
    "stabilisation plan": ["monetary.monetary_expansion_direction", "fiscal.spending_level"],
    "stabilization plan": ["monetary.monetary_expansion_direction", "fiscal.spending_level"],
    "central planning": [
        "institutional.property_rights",
        "regulatory.product_market_competition",
    ],
    "planned economy": [
        "institutional.property_rights",
        "regulatory.product_market_competition",
    ],
    "market-oriented": ["regulatory.product_market_competition"],
    "market oriented": ["regulatory.product_market_competition"],
    "market reform": [
        "regulatory.product_market_competition",
        "regulatory.trade_openness",
    ],
    "market liberalisation": [
        "regulatory.product_market_competition",
        "regulatory.trade_openness",
    ],
    "market liberalization": [
        "regulatory.product_market_competition",
        "regulatory.trade_openness",
    ],
    "privatisation": [
        "institutional.property_rights",
        "regulatory.product_market_competition",
    ],
    "privatization": [
        "institutional.property_rights",
        "regulatory.product_market_competition",
    ],
    "fiat expansion": ["monetary.monetary_expansion_direction"],
    "purchasing power": ["monetary.monetary_expansion_direction"],
    "inflation": ["monetary.monetary_expansion_direction"],
    "mass incarceration": ["institutional.rule_of_law"],
    "homicide": ["institutional.rule_of_law"],
    "crime rate": ["institutional.rule_of_law"],
    "rule-of-law": ["institutional.rule_of_law"],
    "investment climate": ["institutional.property_rights", "institutional.rule_of_law"],
    "fdi": ["regulatory.trade_openness", "institutional.property_rights"],
    "foreign direct investment": [
        "regulatory.trade_openness",
        "institutional.property_rights",
    ],
    # --- late additions for recent stubs / agent-added entries ---
    "price liberalisation": [
        "regulatory.product_market_competition",
        "fiscal.spending_level",
    ],
    "price liberalization": [
        "regulatory.product_market_competition",
        "fiscal.spending_level",
    ],
    "indigenous": ["institutional.property_rights", "regulatory.environmental_stringency"],
    "biodiversity": ["regulatory.environmental_stringency"],
    "decoupling": ["regulatory.environmental_stringency"],
    "mini-budget": ["fiscal.spending_level", "monetary.central_bank_independence"],
    "mini budget": ["fiscal.spending_level", "monetary.central_bank_independence"],
    "truss": ["fiscal.spending_level", "monetary.central_bank_independence"],
    "esop": ["institutional.property_rights"],
    "employee ownership": ["institutional.property_rights"],
    "worker cooperative": ["institutional.property_rights"],
    "fiscal multiplier": ["fiscal.spending_level"],
    "zlb": ["monetary.monetary_expansion_direction", "fiscal.spending_level"],
    "zero lower bound": ["monetary.monetary_expansion_direction"],
    "household debt": ["regulatory.financial_deregulation", "fiscal.transfer_expansion"],
    "life expectancy": ["fiscal.transfer_expansion"],
    "mortality": ["fiscal.transfer_expansion"],
    "drug price": ["fiscal.sectoral_subsidy", "regulatory.product_market_competition"],
    "pharmaceutical": ["fiscal.sectoral_subsidy", "regulatory.product_market_competition"],
    "nhs": ["fiscal.transfer_expansion"],
    "single payer": ["fiscal.transfer_expansion"],
    "wellbeing": ["fiscal.transfer_expansion"],
    "r minus g": ["fiscal.tax_capital"],
    "capital accumulation": ["fiscal.tax_capital"],
    "bretton woods": ["monetary.central_bank_independence", "regulatory.trade_openness"],
    "colonial institutions": ["institutional.property_rights", "institutional.rule_of_law"],
    "stagnation": [
        "institutional.rule_of_law",
        "regulatory.product_market_competition",
        "fiscal.spending_level",
    ],
    "great moderation": ["monetary.monetary_expansion_direction"],
    "energy transition": [
        "regulatory.environmental_stringency",
        "regulatory.energy_supply_security",
        "fiscal.sectoral_subsidy",
    ],
}

# Topic folder → default candidate axes (lower weight than phrase cues).
TOPIC_DEFAULTS: dict[str, list[str]] = {
    "fiscal": [
        "fiscal.tax_progressivity",
        "fiscal.spending_level",
        "fiscal.transfer_expansion",
    ],
    "labour": ["regulatory.labour_market_flexibility"],
    "monetary": [
        "monetary.monetary_expansion_direction",
        "monetary.central_bank_independence",
    ],
    "institutional_quality": [
        "institutional.rule_of_law",
        "institutional.property_rights",
        "institutional.judicial_independence",
    ],
    "regulatory": [
        "regulatory.product_market_competition",
        "regulatory.sectoral_licensing",
    ],
    "housing": ["regulatory.product_market_competition"],
    "trade": ["regulatory.trade_openness"],
    "energy": [
        "regulatory.environmental_stringency",
        "regulatory.energy_supply_security",
        "fiscal.sectoral_subsidy",
    ],
    "resource_rents": [
        "institutional.property_rights",
        "fiscal.sectoral_subsidy",
    ],
    "welfare_architecture": [
        "fiscal.transfer_expansion",
        "fiscal.spending_level",
    ],
    "distribution": [
        "fiscal.tax_progressivity",
        "fiscal.transfer_expansion",
    ],
    "growth": [
        "institutional.rule_of_law",
        "institutional.property_rights",
        "regulatory.product_market_competition",
    ],
    "healthcare": ["fiscal.transfer_expansion"],
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z_]+")


def load_axes() -> dict[str, dict]:
    doc = yaml.safe_load(AXES_FILE.read_text())
    return {a["id"]: a for a in doc["axes"]}


def build_axis_keyword_bags(axes: dict[str, dict]) -> dict[str, set[str]]:
    """Keyword bag per axis, pulled from id + description + direction semantics."""
    bags: dict[str, set[str]] = {}
    for aid, a in axes.items():
        words: list[str] = []
        # id tokens (split on . and _)
        words += re.split(r"[._]", aid)
        # description
        if a.get("description"):
            words += WORD_RE.findall(a["description"])
        # direction semantics
        for v in (a.get("direction_semantics") or {}).values():
            words += WORD_RE.findall(str(v))
        # notes
        if a.get("notes"):
            words += WORD_RE.findall(a["notes"])
        # lowercase and filter stop-ish short tokens
        bags[aid] = {w.lower() for w in words if len(w) >= 4}
    return bags


# Common high-frequency words that match too many axes; exclude from scoring.
STOP = {
    "policy", "policies", "rate", "rates", "level", "levels", "share",
    "direction", "index", "indices", "area", "country", "countries",
    "year", "years", "period", "framework", "reform", "reforms",
    "government", "governments", "public", "economic", "economy",
    "effect", "effects", "cause", "outcome", "outcomes", "data",
    "source", "sources", "from", "with", "this", "that", "these",
    "those", "than", "among", "over", "under", "into", "after",
    "before", "while", "between", "against", "across", "through",
    "typical", "targeted", "general", "further", "larger", "higher",
    "lower", "greater", "smaller", "tighter", "looser", "stronger",
    "weaker", "multi", "order", "variable", "variables", "claim",
    "claims", "status", "version", "description", "notes", "value",
    "values", "distinct", "include", "including", "specifically",
    "however", "therefore", "capture", "captured", "captures",
    "measure", "measured", "measures", "separate", "separately",
    "channel", "channels", "change", "changes", "market", "markets",
    "supply", "demand",
}


def load_hypotheses() -> list[tuple[Path, dict]]:
    out = []
    for topic_dir in sorted(HYP_ROOT.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name in SKIP_DIRS:
            continue
        for f in sorted(topic_dir.glob("*.yaml")):
            if f.name.startswith("_"):
                continue
            doc = yaml.safe_load(f.read_text())
            if not isinstance(doc, dict) or "hypothesis_id" not in doc:
                continue
            out.append((f, doc))
    return out


def hypothesis_signal_text(doc: dict) -> str:
    """Concatenated signal surface for a hypothesis."""
    parts: list[str] = []
    for k in ("hypothesis_id", "title", "claim", "description"):
        v = doc.get(k)
        if isinstance(v, str):
            parts.append(v)
    # variable names and notes
    for bucket in ("outcome", "treatment", "decomposition_channels", "controls"):
        for v in (doc.get("variables") or {}).get(bucket, []) or []:
            if isinstance(v, dict):
                if v.get("name"):
                    parts.append(str(v["name"]))
                if v.get("notes"):
                    parts.append(str(v["notes"]))
    # primary_outcome (wave-3 schema)
    po = doc.get("primary_outcome")
    if isinstance(po, dict):
        for k in ("metric", "expected_finding"):
            if isinstance(po.get(k), str):
                parts.append(po[k])
    return " ".join(parts).lower()


def score_axes(
    doc: dict,
    topic: str,
    axis_bags: dict[str, set[str]],
) -> list[tuple[str, float, list[str]]]:
    """Return [(axis_id, score, reasons)] sorted desc."""
    signal = hypothesis_signal_text(doc)
    signal_words = {w for w in WORD_RE.findall(signal) if w.lower() not in STOP}
    signal_lower = {w.lower() for w in signal_words}

    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)

    # 1. Phrase cues (highest weight)
    for phrase, axis_ids in PHRASE_CUES.items():
        if phrase in signal:
            for aid in axis_ids:
                scores[aid] += 5.0
                reasons[aid].append(f"phrase:{phrase}")

    # 2. Topic-default bias
    for aid in TOPIC_DEFAULTS.get(topic, []):
        scores[aid] += 1.0
        reasons[aid].append(f"topic:{topic}")

    # 3. Axis keyword bag overlap
    for aid, bag in axis_bags.items():
        overlap = bag & signal_lower - STOP
        # Exclude very generic tokens by requiring at least 2 meaningful overlaps
        if len(overlap) >= 2:
            scores[aid] += 0.6 * len(overlap)
            reasons[aid].append(f"kw:{','.join(sorted(overlap)[:4])}")

    ranked = sorted(
        ((aid, s, reasons[aid]) for aid, s in scores.items()),
        key=lambda t: -t[1],
    )
    return ranked


def derive_index(
    axes: dict[str, dict],
    hypotheses: list[tuple[Path, dict]],
    min_score: float = 1.0,
    top_k: int = 4,
) -> dict[str, list[dict]]:
    axis_bags = build_axis_keyword_bags(axes)
    index: dict[str, list[dict]] = {}
    for path, doc in hypotheses:
        topic = doc.get("topic") or path.parent.name
        ranked = score_axes(doc, topic, axis_bags)
        kept = [r for r in ranked if r[1] >= min_score][:top_k]
        index[doc["hypothesis_id"]] = [
            {"axis": aid, "score": round(score, 2), "reasons": reasons[:3]}
            for aid, score, reasons in kept
        ]
    return index


def summary_stats(index: dict[str, list[dict]], axes: dict[str, dict]) -> None:
    with_tags = sum(1 for v in index.values() if v)
    total = len(index)
    print(f"\nSummary:")
    print(f"  {with_tags}/{total} hypotheses tagged with ≥1 axis")

    axis_counts: Counter[str] = Counter()
    for tags in index.values():
        for t in tags:
            axis_counts[t["axis"]] += 1
    print(f"\n  axis coverage (hypothesis count per axis):")
    for aid in sorted(axes):
        n = axis_counts.get(aid, 0)
        marker = "  " if n > 0 else "!!"
        print(f"  {marker}  {n:3d}  {aid}")

    untagged = [hid for hid, v in index.items() if not v]
    if untagged:
        print(f"\n  untagged hypotheses ({len(untagged)}):")
        for hid in untagged:
            print(f"    - {hid}")


def load_positions() -> list[tuple[Path, dict]]:
    out = []
    for f in sorted(POS_ROOT.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        doc = yaml.safe_load(f.read_text())
        if not isinstance(doc, dict) or "position_id" not in doc:
            continue
        out.append((f, doc))
    return out


def position_signal_text(doc: dict) -> str:
    """Concatenated signal surface for a position — steelman + all claim texts."""
    parts: list[str] = []
    for k in ("position_id", "school", "short_name", "steelman"):
        v = doc.get(k)
        if isinstance(v, str):
            parts.append(v)
    for c in doc.get("falsifiable_specific_claims", []) or []:
        if isinstance(c, dict):
            for k in ("claim", "linked_hypothesis_id"):
                v = c.get(k)
                if isinstance(v, str):
                    parts.append(v)
    if isinstance(doc.get("empirical_record_summary"), str):
        parts.append(doc["empirical_record_summary"])
    return " ".join(parts).lower()


def score_position_axes(
    doc: dict,
    axis_bags: dict[str, set[str]],
) -> list[tuple[str, float, list[str]]]:
    # Fake a pseudo-hypothesis doc that the existing scorer can handle.
    pseudo = {
        "claim": position_signal_text(doc),
    }
    return score_axes(pseudo, topic="", axis_bags=axis_bags)


def derive_position_index(
    axes: dict[str, dict],
    positions: list[tuple[Path, dict]],
    min_score: float = 3.0,
    top_k: int = 8,
) -> dict[str, list[dict]]:
    axis_bags = build_axis_keyword_bags(axes)
    out: dict[str, list[dict]] = {}
    for _, doc in positions:
        ranked = score_position_axes(doc, axis_bags)
        kept = [r for r in ranked if r[1] >= min_score][:top_k]
        out[doc["position_id"]] = [
            {"axis": aid, "score": round(s, 2), "reasons": reasons[:3]}
            for aid, s, reasons in kept
        ]
    return out


def main() -> None:
    axes = load_axes()
    hyps = load_hypotheses()
    positions = load_positions()
    print(
        f"loaded {len(axes)} axes, {len(hyps)} hypotheses, {len(positions)} positions"
    )

    # hypotheses
    hyp_index = derive_index(axes, hyps)
    hyp_doc = {
        "_note": (
            "Derived by scripts/derive_hypothesis_axes.py. "
            "Human edits override; re-running regenerates the rest."
        ),
        "generated_from": "scripts/derive_hypothesis_axes.py",
        "index": {hid: hyp_index[hid] for hid in sorted(hyp_index)},
    }
    OUT_FILE.write_text(yaml.safe_dump(hyp_doc, sort_keys=False, width=100))
    print(f"wrote {OUT_FILE.relative_to(REPO)}")
    summary_stats(hyp_index, axes)

    # positions
    pos_index = derive_position_index(axes, positions)
    pos_doc = {
        "_note": (
            "Position → axis index. Derived from each position's steelman + "
            "claim texts. Used to surface the hypotheses each school's "
            "predictions speak to, independent of whether the linked "
            "hypothesis_id was ever written."
        ),
        "generated_from": "scripts/derive_hypothesis_axes.py",
        "index": {pid: pos_index[pid] for pid in sorted(pos_index)},
    }
    POS_OUT_FILE.write_text(yaml.safe_dump(pos_doc, sort_keys=False, width=100))
    print(f"wrote {POS_OUT_FILE.relative_to(REPO)}")
    tagged = sum(1 for v in pos_index.values() if v)
    print(f"  {tagged}/{len(pos_index)} positions tagged with ≥1 axis")


if __name__ == "__main__":
    main()
