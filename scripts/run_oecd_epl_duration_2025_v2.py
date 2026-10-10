#!/usr/bin/env python3
"""Frozen 2023 OECD EPL -> actual 2025 Eurostat duration holdout.

Only selected source values are opened after separate registration and source-lock
commits. The sole model, sample rules and decision gates are frozen in the YAML.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_epl_2023_eurostat_longterm_unemployment_2025_v2"
SPEC = f"hypotheses/labour/{ID}.yaml"
ROSTER = "data/pinned_evidence/epl_duration_2025_temporal_holdout_v2_key_roster.csv"
LOCK = f"data/pinned_evidence/{ID}.source.json"
RUN_DIR = f"engine/runs/{ID}"
RUNNER = "scripts/run_oecd_epl_duration_2025_v2.py"
AUDIT = "engine/audits/epl_duration_2025_holdout_result_2026-10-10.md"
FAMILY_SIZE = 1


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return p.stdout


def frozen_source() -> tuple[dict, str, str, list[dict]]:
    lock_path = ROOT / LOCK
    lock = json.loads(lock_path.read_text())
    lock_commit = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", LOCK).decode().strip()
    if not lock_commit or "\n" in lock_commit or git("show", f"{lock_commit}:{LOCK}") != lock_path.read_bytes():
        raise ValueError("source lock is not the exact first committed blob")
    reg = lock.get("registration_commit")
    if not isinstance(reg, str) or not reg or "\n" in reg:
        raise ValueError("missing registration commit")
    git("merge-base", "--is-ancestor", reg, lock_commit)
    git("merge-base", "--is-ancestor", lock_commit, "HEAD")
    if git("show", f"{reg}:{SPEC}") != (ROOT / SPEC).read_bytes():
        raise ValueError("frozen hypothesis differs from first registration")
    if (lock.get("hypothesis_id") != ID or lock.get("family_size") != FAMILY_SIZE
            or lock.get("key_roster_path") != ROSTER
            or lock.get("key_roster_sha256") != sha(ROOT / ROSTER)):
        raise ValueError("source lock roster or hypothesis mismatch")
    with (ROOT / ROSTER).open(newline="", encoding="utf-8") as f:
        roster = list(csv.DictReader(f))
    if len(roster) != 25 or len({r["country_iso3"] for r in roster}) != 25:
        raise ValueError("frozen country roster is not the exact 25-country set")
    expected_roles = {"outcome_longterm", "denominator_unemployment", "treatment_epl"}
    sources = lock.get("source_files") or {}
    if set(sources) != expected_roles:
        raise ValueError("locked source roles differ")
    if lock.get("source_sha256") != sources["outcome_longterm"].get("sha256"):
        raise ValueError("primary source hash differs")
    for role, src in sources.items():
        relative = src.get("path")
        manifest_rel = src.get("manifest")
        if (not isinstance(relative, str) or not relative.startswith("data/vintages/")
                or not isinstance(manifest_rel, str) or not manifest_rel.startswith("data/manifests/")
                or ".." in Path(relative).parts or ".." in Path(manifest_rel).parts):
            raise ValueError(f"invalid {role} paths")
        if sha(ROOT / relative) != src.get("sha256"):
            raise ValueError(f"{role} source bytes differ from lock")
        if sha(ROOT / manifest_rel) != src.get("manifest_sha256"):
            raise ValueError(f"{role} original fetch manifest bytes differ")
        if git("show", f"{lock_commit}:{manifest_rel}") != (ROOT / manifest_rel).read_bytes():
            raise ValueError(f"{role} fetch manifest not exact at lock commit")
        doc = yaml.safe_load((ROOT / manifest_rel).read_text()) or {}
        matches = [row for row in doc.get("entries", [])
                   if isinstance(row, dict) and row.get("publisher") == src.get("publisher")
                   and row.get("series_id") == src.get("series_id")
                   and row.get("parquet_path") == relative
                   and row.get("sha256") == src.get("sha256")
                   and row.get("source_url") == src.get("url")]
        if len(matches) != 1:
            raise ValueError(f"{role} source not uniquely present in original fetch manifest")
    return lock, reg, lock_commit, roster


def exact_selected(table: pd.DataFrame, key: str, roster_keys: set[str]) -> dict[str, float | None]:
    """One value per national key; missing/duplicate/invalid cells are not guessed."""
    out: dict[str, float | None] = {}
    for country in roster_keys:
        vals = table.loc[table[key] == country, "value"]
        out[country] = float(vals.iloc[0]) if len(vals) == 1 and pd.notna(vals.iloc[0]) else None
    return out


def evaluate(lock: dict, roster: list[dict]) -> dict:
    src = lock["source_files"]
    epl = pq.read_table(ROOT / src["treatment_epl"]["path"], columns=["country", "year", "indicator", "value"]).to_pandas()
    ltu = pq.read_table(ROOT / src["outcome_longterm"]["path"], columns=["freq", "indic_em", "age", "sex", "unit", "geo_code", "period", "value"]).to_pandas()
    unemp = pq.read_table(ROOT / src["denominator_unemployment"]["path"], columns=["freq", "age", "sex", "unit", "geo_code", "period", "value"]).to_pandas()
    epl = epl[(epl["year"] == 2023) & (epl["indicator"] == "EPR_V1")]
    ltu = ltu[(ltu["freq"] == "A") & (ltu["indic_em"] == "LTU")
              & (ltu["age"] == "Y15-74") & (ltu["sex"] == "T") & (ltu["unit"] == "PC_ACT")]
    unemp = unemp[(unemp["freq"] == "A") & (unemp["age"] == "Y15-74")
                  & (unemp["sex"] == "T") & (unemp["unit"] == "PC_ACT")]
    epr = exact_selected(epl, "country", {r["oecd_name"] for r in roster})
    ltu_by_year = {y: exact_selected(ltu[ltu["period"] == str(y)], "geo_code",
                                     {r["eurostat_geo"] for r in roster}) for y in (2023, 2025)}
    u_by_year = {y: exact_selected(unemp[unemp["period"] == str(y)], "geo_code",
                                   {r["eurostat_geo"] for r in roster}) for y in (2023, 2025)}
    valid = []
    exclusions = []
    for r in roster:
        g, name = r["eurostat_geo"], r["oecd_name"]
        x = epr[name]
        q = {year: (ltu_by_year[year][g], u_by_year[year][g]) for year in (2023, 2025)}
        if x is None or not math.isfinite(x) or not 0 <= x <= 6:
            exclusions.append({"country": r["country_iso3"], "reason": "missing_or_invalid_2023_epr"})
            continue
        bad = False
        shares = {}
        for year, (l, u) in q.items():
            if (l is None or u is None or not math.isfinite(l) or not math.isfinite(u)
                    or not 0 <= l <= 100 or not 0 < u <= 100 or l > u + 0.15):
                exclusions.append({"country": r["country_iso3"], "reason": f"missing_or_invalid_{year}_duration_fraction"})
                bad = True
                break
            shares[year] = 100.0 * l / u
            if not 0 <= shares[year] <= 100.0 + 1e-10:
                exclusions.append({"country": r["country_iso3"], "reason": f"out_of_range_{year}_duration_fraction"})
                bad = True
                break
        if not bad:
            valid.append({"country": r["country_iso3"], "epr": x,
                          "baseline_share": shares[2023], "outcome_share": shares[2025]})
    gate = {"roster_countries": len(roster), "valid_countries": len(valid),
            "excluded": exclusions, "selected_years": [2023, 2025],
            "selected_duration_indicator": "une_ltu_a:LTU"}
    failures = []
    if len(valid) < 24:
        failures.append("fewer_than_24_complete_countries")
    if len(valid) < 4:
        return {"verdict": "INCONCLUSIVE", "reason": "too few complete countries", "gate_failures": failures,
                "gate_checks": gate, "primary": None}
    x = np.array([r["epr"] for r in valid], dtype=float)
    b = np.array([r["baseline_share"] for r in valid], dtype=float)
    y = np.array([r["outcome_share"] for r in valid], dtype=float)
    iqr = float(np.percentile(x, 75) - np.percentile(x, 25))
    ssx = float(np.sum((x - np.mean(x)) ** 2))
    concentration = float(np.max((x - np.mean(x)) ** 2) / ssx) if ssx > 0 else math.inf
    gate["epr_iqr"] = iqr
    gate["max_country_centered_epr_share"] = concentration
    if iqr < 0.5:
        failures.append("epr_iqr_below_0.5")
    if concentration > 0.25:
        failures.append("epr_variation_concentrated")
    X = np.column_stack([np.ones(len(x)), x, b])
    if np.linalg.matrix_rank(X) != 3:
        failures.append("rank_deficient")
        return {"verdict": "INCONCLUSIVE", "reason": "; ".join(failures),
                "gate_failures": failures, "gate_checks": gate, "primary": None}
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    resid = y - X @ beta
    hat = np.sum((X @ xtx_inv) * X, axis=1)
    max_hat = float(np.max(hat))
    ssr = float(np.sum(resid ** 2))
    max_resid = float(np.max(resid ** 2) / ssr) if ssr > 0 else math.inf
    gate["max_ols_leverage"] = max_hat
    gate["max_country_residual_variance_share"] = max_resid
    if max_hat > 0.35:
        failures.append("ols_leverage_exceeds_0.35")
    if max_resid > 0.30:
        failures.append("residual_variance_concentrated")
    with np.errstate(divide="ignore", invalid="ignore"):
        adj = resid / (1.0 - hat)
        cov = xtx_inv @ ((X * (adj ** 2)[:, None]).T @ X) @ xtx_inv
        se = float(np.sqrt(cov[1, 1]))
    if not math.isfinite(se) or se <= 0:
        failures.append("hc3_uncertainty_invalid")
    if failures:
        return {"verdict": "INCONCLUSIVE", "reason": "; ".join(failures),
                "gate_failures": failures, "gate_checks": gate, "primary": None}
    b_epr = float(beta[1])
    p = float(2 * norm.sf(abs(b_epr / se)))
    z99 = float(norm.ppf(0.995))
    primary = {"coefficient_pp_per_epr_point": b_epr, "std_error_hc3": se,
               "p_two_sided_normal": p, "ci_99_lower": b_epr - z99 * se,
               "ci_99_upper": b_epr + z99 * se,
               "n_countries": len(valid),
               "method": "2025 long-term share on 2023 EPR and 2023 long-term share; OLS HC3"}
    if b_epr >= 1.0 and p <= 0.01:
        verdict, reason = "SUPPORTED", "positive material EPR association clears frozen p<=0.01"
    elif b_epr <= -1.0 and p <= 0.01:
        verdict, reason = "REFUTED", "negative material EPR association clears frozen p<=0.01"
    else:
        verdict, reason = "PARTIAL", "method-valid holdout does not clear the frozen directional threshold"
    return {"verdict": verdict, "reason": reason, "gate_failures": [],
            "gate_checks": gate, "primary": primary}


def card(result: dict, reg: str, lock_commit: str) -> str:
    p = result["primary"]
    estimate = "No directional coefficient released because a frozen method gate failed."
    if p is not None:
        estimate = (f"EPR coefficient {p['coefficient_pp_per_epr_point']:+.6g} share points "
                    f"per EPR index point; HC3 SE {p['std_error_hc3']:.6g}; "
                    f"two-sided p {p['p_two_sided_normal']:.6g}; "
                    f"99% CI [{p['ci_99_lower']:+.6g}, {p['ci_99_upper']:+.6g}].")
    return (f"# OECD EPL and 2025 long-term unemployment holdout\n\n"
            f"Registration `{reg}`; source lock `{lock_commit}`.\n\n"
            f"**{result['verdict']}** — {result['reason']}.\n\n"
            f"{result['gate_checks']['valid_countries']} of 25 roster countries have complete source-matched cells. "
            f"{estimate}\n\n"
            "The outcome is the share of unemployed people with spells of at least 12 months, "
            "derived from Eurostat's actual long-term and total unemployment rates. "
            "This later-year country association has zero causal, policy, school, position, or featured credit. "
            "It does not repair or reclassify the old mismeasured result.\n")


def payloads(result: dict, reg: str, lock_commit: str, lock: dict, stamp: str) -> dict:
    diag = {"hypothesis_id": ID, "registration_commit": reg,
            "source_lock_commit": lock_commit, "source_sha256": lock["source_sha256"],
            "source_key_roster_sha256": lock["key_roster_sha256"],
            "family_size": FAMILY_SIZE, "run_utc": stamp, "runner": RUNNER,
            "result": result}
    diag_bytes = (json.dumps(diag, indent=2, ensure_ascii=False) + "\n").encode()
    sources = [{field: src[field] for field in ("path", "sha256", "manifest", "url")}
               for src in lock["source_files"].values()]
    source = {"source_sha256": lock["source_sha256"], "source_lock_commit": lock_commit,
              "source_lock_manifest": LOCK, "key_roster_sha256": lock["key_roster_sha256"],
              "input_vintages": sources}
    packet = {"hypothesis_id": ID, "preregistration": {"spec_commit": reg,
              "source_lock_commit": lock_commit, "key_roster": ROSTER,
              "family_size": FAMILY_SIZE}, "source": source, "result": result,
              "reproduction": {"command": f"python3 {RUNNER} --verify",
                               "result_sha256": hashlib.sha256(diag_bytes).hexdigest()},
              "limitations": "Associational 25-country temporal holdout; no causal, policy, school, position, or featured credit; Eurostat cell flags not preserved."}
    manifest = {"hypothesis_id": ID, "status": result["verdict"],
                "preregistration_commit": reg, "run_utc": stamp,
                "source": source, "runner": RUNNER}
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess, sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    return {"diagnostics": diag, "diagnostics_bytes": diag_bytes,
            "packet": packet, "manifest": manifest, "wrapper": wrapper,
            "card": card(result, reg, lock_commit)}


def run() -> None:
    lock, reg, lock_commit, roster = frozen_source()
    target = ROOT / RUN_DIR
    if target.exists() or (ROOT / AUDIT).exists():
        raise FileExistsError("result already exists; use --verify")
    result = evaluate(lock, roster)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    p = payloads(result, reg, lock_commit, lock, stamp)
    target.mkdir(parents=True)
    (target / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (target / "diagnostics.json").write_bytes(p["diagnostics_bytes"])
    (target / "manifest.yaml").write_text(yaml.safe_dump(p["manifest"], sort_keys=False))
    (target / "evidence_packet.yaml").write_text(yaml.safe_dump(p["packet"], sort_keys=False))
    (target / "replication.py").write_text(p["wrapper"])
    (target / "result_card.md").write_text(p["card"])
    (target / "chart_data.json").write_text(json.dumps({"hypothesis_id": ID,
          "verdict": result["verdict"], "primary": result["primary"]}, indent=2) + "\n")
    (ROOT / AUDIT).write_text(p["card"] + "\nThe registered source-quality and interpretation limits remain in "
                              "`engine/audits/epl_duration_2025_holdout_prereg_2026-10-10.md`; "
                              "the old result remains separately quarantined.\n")
    print(json.dumps({"verdict": result["verdict"], "valid_countries": result["gate_checks"]["valid_countries"],
                      "gate_failures": result["gate_failures"], "primary": result["primary"]}, indent=2))


def verify() -> None:
    lock, reg, lock_commit, roster = frozen_source()
    target = ROOT / RUN_DIR
    saved = json.loads((target / "diagnostics.json").read_text())
    if saved.get("registration_commit") != reg or saved.get("source_lock_commit") != lock_commit:
        raise AssertionError("saved chronology differs")
    if saved.get("source_sha256") != lock["source_sha256"] or saved.get("source_key_roster_sha256") != lock["key_roster_sha256"]:
        raise AssertionError("saved source custody differs")
    result = evaluate(lock, roster)
    if result != saved.get("result"):
        raise AssertionError("exact result replay differs")
    p = payloads(result, reg, lock_commit, lock, saved["run_utc"])
    checks = {"diagnostics.json": p["diagnostics_bytes"],
              "manifest.yaml": yaml.safe_dump(p["manifest"], sort_keys=False).encode(),
              "evidence_packet.yaml": yaml.safe_dump(p["packet"], sort_keys=False).encode(),
              "replication.py": p["wrapper"].encode(), "result_card.md": p["card"].encode(),
              "hypothesis.yaml": (ROOT / SPEC).read_bytes()}
    for name, expected in checks.items():
        if (target / name).read_bytes() != expected:
            raise AssertionError(f"{name} does not replay exactly")
    print(json.dumps({"verified": True, "verdict": result["verdict"],
                      "valid_countries": result["gate_checks"]["valid_countries"]}))


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.run:
        run()
    else:
        verify()


if __name__ == "__main__":
    main()
