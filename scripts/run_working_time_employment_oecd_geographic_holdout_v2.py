#!/usr/bin/env python3
"""Source-pinned OECD working-hours holdout with a guarded, read-only replay.

--preflight reads only country/year keys. --run cannot read held-out values
until the new hypothesis, steelman, and this runner share an unchanged
first-addition Git commit. --check re-estimates and compares every stored
substantive run artifact without writing files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
HID = "working_time_employment_oecd_geographic_holdout_v2"
OLD_ID = "working_time_reduction_employment_neutral_oecd"
OLD_COMMIT = "9db22f489a1709911fca79175efeb14dd1a70646"
SPEC_REL = f"hypotheses/labour/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = "scripts/run_working_time_employment_oecd_geographic_holdout_v2.py"
RUN_REL = f"engine/runs/{HID}"
OLD_COUNTRIES = frozenset(
    "AUS AUT BEL CAN CHE DEU DNK ESP FIN FRA GBR GRC IRL ISL ITA JPN KOR "
    "NLD NOR NZL PRT SWE USA".split()
)
HOLDOUT_COUNTRIES = frozenset(
    "CHL COL CRI CZE EST HUN ISR LTU LUX LVA MEX POL SVK SVN TUR".split()
)
ROLES = ("hours", "employment", "income", "population", "trade", "services")
PERIOD = (1990, 2019)
MIN_YEARS = 8
MIN_COUNTRIES = 10
MIN_OBSERVATIONS = 150
MARGIN = 0.5
CONFIDENCE = 0.90
MAX_HALF_WIDTH = 0.5
SOURCE_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
COEFFICIENT_COLUMNS = (
    "term", "coefficient", "std_error", "p_value", "ci90",
    "n_obs", "n_countries", "r_squared", "method",
)


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"], cwd=ROOT,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def declared_sources(spec: dict[str, Any], status: str) -> dict[str, dict[str, str]]:
    """Preserve registered pins even when local custody cannot be verified."""
    pins = spec["falsification"]["threshold"]["source_files"]
    return {
        role: {
            "source": pins[role]["source"],
            "vintage_file": pins[role]["path"],
            "sha256": pins[role]["sha256"],
            "source_manifest": pins[role]["source_manifest"],
            "verification_status": status,
        }
        for role in ROLES
    }


def failure_record(phase: str, error: BaseException) -> dict[str, str]:
    return {"phase": phase, "type": type(error).__name__, "message": str(error)}


def unverified_gate(phase: str, error: BaseException,
                    source_custody_verified: bool,
                    outcome_values_loaded: bool | None) -> dict[str, Any]:
    return {
        "observations": None, "countries": None,
        "min_years_per_country": MIN_YEARS,
        "old_country_overlap": None, "years": [], "sample_passed": False,
        "source_custody_verified": source_custody_verified,
        "outcome_values_loaded": outcome_values_loaded,
        "value_read_attempted": phase == "panel_construction",
        "estimation_attempted": False,
        "failure": failure_record(phase, error),
    }


def validate_spec() -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    old_path = f"hypotheses/labour/{OLD_ID}.yaml"
    old_spec = yaml.safe_load(git_show(OLD_COMMIT, old_path))
    old_runner = git_show(OLD_COMMIT, "scripts/run_panel_fe.py").decode()
    old_diagnostic = json.loads(git_show(
        OLD_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"
    ))
    if set(old_spec["sample"]["countries"]) != OLD_COUNTRIES:
        raise ValueError("historical old-country roster mismatch")
    if not all(fragment in old_runner for fragment in (
        'out = out[out["country_iso3"].isin(countries)]',
        "panel_filt = filter_sample(panel, spec)",
        "est = run_panel_ols(\n        panel_filt,",
    )):
        raise ValueError("historical runner did not restrict the old sample")
    if old_diagnostic["verdict_label"] != "PARTIAL" or (
        old_diagnostic["estimate"]["n_countries"] > len(OLD_COUNTRIES)
    ):
        raise ValueError("historical run record changed")
    if spec["hypothesis_id"] != HID or spec["status"] != "pre_registered":
        raise ValueError("new ID/status changed")
    if spec.get("evidence_type") != "associational" or spec.get("covers_claims") != []:
        raise ValueError("evidence scope or claim links changed")
    if set(spec["sample"]["countries"]) != HOLDOUT_COUNTRIES or (
        tuple(spec["sample"]["period"]) != PERIOD
    ):
        raise ValueError("registered holdout roster or years changed")
    if HOLDOUT_COUNTRIES & OLD_COUNTRIES:
        raise ValueError("old and holdout countries overlap")
    if spec.get("steelman") != STEELMAN_REL or not (ROOT / STEELMAN_REL).is_file():
        raise ValueError("steelman missing")
    estimator = spec["estimator"]
    if estimator.get("template") != "panel_fe" or (
        estimator.get("fixed_effects") != ["country", "year"]
    ) or estimator.get("clustering") != "country":
        raise ValueError("estimator changed")
    threshold = spec["falsification"]["threshold"]
    expected = {
        "old_hypothesis_id": OLD_ID, "old_result_bucket": "PARTIAL",
        "old_run_commit": OLD_COMMIT,
        "old_country_ids": sorted(OLD_COUNTRIES),
        "holdout_country_ids": sorted(HOLDOUT_COUNTRIES),
        "years": list(PERIOD),
        "margin_absolute_elasticity": MARGIN,
        "equivalence_alpha": 0.05, "confidence_level": CONFIDENCE,
        "min_observations": MIN_OBSERVATIONS,
        "min_countries": MIN_COUNTRIES,
        "min_years_per_country": MIN_YEARS,
        "max_ci_half_width": MAX_HALF_WIDTH,
    }
    if any(threshold.get(key) != value for key, value in expected.items()):
        raise ValueError("registered decision or sample threshold changed")
    if set(threshold["source_files"]) != set(ROLES):
        raise ValueError("source roles changed")
    source_ids = {
        item["name"]: item["source"]
        for block in ("outcome", "treatment", "controls")
        for item in spec["variables"].get(block, [])
    }
    registered = {
        "hours": "log_annual_hours_worked",
        "employment": "log_employment_to_population_ratio",
        "income": "log_real_gdp_per_capita",
        "population": "log_population",
        "trade": "trade_openness",
        "services": "services_share",
    }
    if any(source_ids.get(name) != threshold["source_files"][role]["source"]
           for role, name in registered.items()):
        raise ValueError("variable/source mapping changed")
    return spec


def verified_sources(spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    manifest = yaml.safe_load((ROOT / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    manifest_entries = {
        (item["parquet_path"], item["sha256"])
        for item in manifest["entries"] if item.get("parquet_path") and item.get("sha256")
    }
    pins = spec["falsification"]["threshold"]["source_files"]
    for role in ROLES:
        pin = pins[role]
        relative = Path(pin["path"])
        absolute = (ROOT / relative).resolve()
        if not absolute.is_relative_to(ROOT.resolve()) or not absolute.is_file():
            raise ValueError(f"missing or nonlocal source: {relative}")
        if pin["source_manifest"] != SOURCE_MANIFEST or (
            str(relative), pin["sha256"]
        ) not in manifest_entries:
            raise ValueError(f"source manifest mismatch: {relative}")
        if absolute.suffix != ".parquet" or sha256(absolute) != pin["sha256"]:
            raise ValueError(f"source SHA-256 mismatch: {relative}")
    return declared_sources(spec, "verified")


def load_keys(record: dict[str, str]) -> set[tuple[str, int]]:
    """Read key columns only; keep value and null status outside preflight."""
    import pyarrow.parquet as pq

    table = pq.read_table(ROOT / record["vintage_file"], columns=["country_iso3", "year"])
    frame = table.to_pydict()
    keys = [
        (country, int(year))
        for country, year in zip(frame["country_iso3"], frame["year"])
        if country in HOLDOUT_COUNTRIES and year is not None
        and PERIOD[0] <= int(year) <= PERIOD[1]
    ]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate country-year keys: {record['vintage_file']}")
    return set(keys)


def key_envelope(sources: dict[str, dict[str, str]]) -> set[tuple[str, int]]:
    keys = set.intersection(*(load_keys(sources[role]) for role in ROLES))
    counts: dict[str, int] = {}
    for country, _ in keys:
        counts[country] = counts.get(country, 0) + 1
    return {(country, year) for country, year in keys
            if counts[country] >= MIN_YEARS}


def preflight() -> dict[str, Any]:
    spec = validate_spec()
    sources = verified_sources(spec)
    keys = key_envelope(sources)
    countries = {country for country, _ in keys}
    return {
        "key_country_years_upper_bound": len(keys),
        "key_countries_upper_bound": len(countries),
        "old_country_overlap": len(countries & OLD_COUNTRIES),
        "complete_case_coverage_verified": False,
        "counts_are_upper_bounds": True,
        "outcome_values_loaded": False,
        "coefficient_estimated": False,
        "key_envelope_passed": len(keys) >= MIN_OBSERVATIONS
        and len(countries) >= MIN_COUNTRIES and not (countries & OLD_COUNTRIES),
    }


def registration_commit() -> str:
    """The first-addition commit must freeze every substantive input to this run."""
    files = (SPEC_REL, STEELMAN_REL, RUNNER_REL)
    for relative in files:
        if git_show("HEAD", relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"commit preregistration before any held-out fit: {relative}")
    additions = []
    for relative in files:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"missing first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("spec, steelman, and runner require one preregistration commit")
    commit = additions[0]
    for relative in files:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration bytes differ from first addition: {relative}")
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", RUN_REL],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode or result.stdout.strip():
        raise RuntimeError("run artifacts existed in preregistration commit")
    return commit


def load_values(record: dict[str, str], role: str) -> pd.DataFrame:
    import numpy as np
    import pandas as pd

    source_column = "avh" if role == "hours" else "value"
    frame = pd.read_parquet(
        ROOT / record["vintage_file"],
        columns=["country_iso3", "year", source_column],
    )
    frame = frame[frame["country_iso3"].isin(HOLDOUT_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[role] = pd.to_numeric(frame[source_column], errors="coerce")
    frame = frame[frame["year"].between(*PERIOD) & np.isfinite(frame[role])].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country-year values: {record['vintage_file']}")
    return frame[["country_iso3", "year", role]]


def build_panel(sources: dict[str, dict[str, str]]) -> pd.DataFrame:
    """Value columns may be opened only after registration_commit succeeds."""
    import numpy as np

    frames = {role: load_values(sources[role], role) for role in ROLES}
    panel = frames[ROLES[0]]
    for role in ROLES[1:]:
        panel = panel.merge(frames[role], on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[(panel["hours"] > 0) & (panel["employment"] > 0)
                  & (panel["income"] > 0) & (panel["population"] > 0)].copy()
    panel["log_annual_hours_worked"] = np.log(panel["hours"])
    panel["log_employment_to_population_ratio"] = np.log(panel["employment"])
    panel["log_real_gdp_per_capita"] = np.log(panel["income"])
    panel["log_population"] = np.log(panel["population"])
    panel["trade_openness"] = panel["trade"]
    panel["services_share"] = panel["services"]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=[
        "log_annual_hours_worked", "log_employment_to_population_ratio",
        "log_real_gdp_per_capita", "log_population", "trade_openness", "services_share",
    ])
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_YEARS].copy()
    if set(panel["country_iso3"]) & OLD_COUNTRIES:
        raise AssertionError("old-country overlap in fitted panel")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def classify(ci90: list[float], half_width: float) -> tuple[str, str]:
    if not math.isfinite(half_width) or half_width > MAX_HALF_WIDTH:
        return "INCONCLUSIVE", "registered precision gate failed"
    if -MARGIN < ci90[0] and ci90[1] < MARGIN:
        return "SUPPORTED", "90% clustered interval wholly inside the equivalence margin"
    if ci90[0] >= MARGIN or ci90[1] <= -MARGIN:
        return "REFUTED", "90% clustered interval wholly outside the equivalence margin"
    return "PARTIAL", "90% clustered interval overlaps an equivalence boundary"


def fit_model(panel: pd.DataFrame) -> dict[str, Any]:
    import statsmodels.formula.api as smf
    from scipy.stats import t as student_t

    term = "log_annual_hours_worked"
    formula = (
        "log_employment_to_population_ratio ~ log_annual_hours_worked "
        "+ log_real_gdp_per_capita + log_population + trade_openness "
        "+ services_share + C(country_iso3) + C(year)"
    )
    fit = smf.ols(formula, data=panel).fit(
        cov_type="cluster",
        cov_kwds={"groups": panel["country_iso3"], "use_correction": True},
    )
    if fit.model.rank != fit.model.exog.shape[1]:
        raise ValueError("rank-deficient fixed-effects design")
    coefficient = float(fit.params[term])
    std_error = float(fit.bse[term])
    p_value = float(fit.pvalues[term])
    critical = float(student_t.ppf((1 + CONFIDENCE) / 2, int(panel["country_iso3"].nunique()) - 1))
    half_width = critical * std_error
    ci90 = [coefficient - half_width, coefficient + half_width]
    numbers = (coefficient, std_error, p_value, critical, half_width, *ci90, float(fit.rsquared))
    if std_error <= 0 or not all(math.isfinite(number) for number in numbers):
        raise ValueError("nonfinite or zero clustered uncertainty")
    return {
        "coefficient": coefficient, "std_error": std_error,
        "p_value": p_value, "ci90": ci90, "ci90_half_width": half_width,
        "n_obs": len(panel), "n_countries": int(panel["country_iso3"].nunique()),
        "r_squared": float(fit.rsquared),
        "method": "country/year FE OLS; country-clustered CR1; t interval df=clusters-1",
    }


def estimate_one(sources: dict[str, dict[str, str]]) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    try:
        panel = build_panel(sources)
    except Exception as error:
        gate = unverified_gate("panel_construction", error, True, None)
        return gate, "INCONCLUSIVE", (
            f"panel construction failed before estimation: {type(error).__name__}: {error}"
        ), None
    countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": len(panel), "countries": countries,
        "min_years_per_country": MIN_YEARS, "old_country_overlap": 0,
        "years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
        "sample_passed": len(panel) >= MIN_OBSERVATIONS and countries >= MIN_COUNTRIES,
        "source_custody_verified": True, "outcome_values_loaded": True,
        "value_read_attempted": True, "estimation_attempted": False,
        "failure": None,
    }
    if not gate["sample_passed"]:
        gate["failure"] = failure_record("sample_gate", ValueError("below registered complete-case floor"))
        return gate, "INCONCLUSIVE", "registered complete-case sample gate failed", None
    gate["estimation_attempted"] = True
    try:
        estimate = fit_model(panel)
    except Exception as error:
        gate["failure"] = failure_record("estimator", error)
        return gate, "INCONCLUSIVE", f"estimator failed: {type(error).__name__}: {error}", None
    verdict, reason = classify(estimate["ci90"], estimate["ci90_half_width"])
    if verdict == "INCONCLUSIVE":
        gate["failure"] = failure_record("precision_gate", ValueError(reason))
    sensitivity_panel = panel[~panel["year"].between(2008, 2010)].copy()
    if len(sensitivity_panel) >= MIN_OBSERVATIONS and (
        sensitivity_panel["country_iso3"].nunique() >= MIN_COUNTRIES
    ):
        try:
            sensitivity = fit_model(sensitivity_panel)
            sensitivity["verdict"] = None
        except Exception as error:
            sensitivity = {"error": f"{type(error).__name__}: {error}", "verdict": None}
    else:
        sensitivity = {"error": "fixed GFC-exclusion sample gate failed", "verdict": None}
    estimate["gfc_2008_2010_exclusion_sensitivity"] = sensitivity
    return gate, verdict, reason, estimate


def render_card(prereg_commit: str, gate: dict[str, Any], verdict: str,
                reason: str, estimate: dict[str, Any] | None) -> str:
    if gate["observations"] is None:
        sample_line = "Complete-case sample not evaluated; registered rosters are country-disjoint.\n"
    else:
        sample_line = (
            f"New sample: {gate['observations']} country-years and {gate['countries']} "
            "countries; zero historical-country overlap.\n"
        )
    card = (
        f"# Result card: {HID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
        f"Known historical result: `{OLD_ID}` PARTIAL.\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        f"{sample_line}"
        "Equivalence margin: absolute elasticity < 0.5; 90% country-clustered interval "
        "fully inside the margin, with a separate precision gate.\n"
    )
    if gate.get("failure"):
        card += "Evidence state: **UNVERIFIED INCONCLUSIVE**; no hypothesis graduation.\n"
    if estimate is not None:
        card += (
            f"Primary elasticity {estimate['coefficient']:+.6g}; clustered SE "
            f"{estimate['std_error']:.6g}; 90% interval "
            f"[{estimate['ci90'][0]:+.6g}, {estimate['ci90'][1]:+.6g}].\n"
        )
    return card + (
        "\nAssociation only. WDI modeled employment replaces the old ILOSTAT identifier. "
        "No France policy effect or school-score claim is identified.\n"
    )


def render_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


def artifact_records(prereg_commit: str, sources: dict[str, dict[str, str]],
                     gate: dict[str, Any], verdict: str, reason: str,
                     estimate: dict[str, Any] | None, stamp: str
                     ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any],
                                str, str, dict[str, Any], list[dict[str, Any]]]:
    source_list = [{"role": role, **sources[role]} for role in ROLES]
    limitations = [
        "The historical PARTIAL result was visible before registration.",
        "Country-disjoint association, not a shorter-hours policy effect.",
        "WDI modeled employment replaces the original ILOSTAT identifier.",
        "An inconclusive or broad interval cannot support near-neutrality.",
    ]
    failure = gate.get("failure")
    evidence_state = "UNVERIFIED_INCONCLUSIVE" if failure else "PENDING_READ_ONLY_REPLAY"
    if failure:
        limitations.append(
            f"Run stopped at {failure['phase']}: {failure['type']}: {failure['message']}"
        )
    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "panel_fe",
        "preflight": gate, "estimate": estimate, "evidence_state": evidence_state,
        "data_status": {"variables_missing": [], "input_vintages": source_list,
                        "source_custody_verified": gate["source_custody_verified"]},
        "limitations": limitations,
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": verdict,
        "old_hypothesis_id": OLD_ID, "old_verdict": "PARTIAL",
        "old_run_commit": OLD_COMMIT, "vintages": source_list,
        "derived_panel": gate, "evidence_state": evidence_state,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "labour"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --check"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason,
                    "evidence_state": evidence_state},
        "data": {"inputs": source_list,
                 "old_country_overlap": gate["old_country_overlap"],
                 "source_custody_verified": gate["source_custody_verified"]},
        "results": estimate, "limitations": limitations,
    }
    card = render_card(prereg_commit, gate, verdict, reason, estimate)
    wrapper = render_wrapper()
    chart = {
        "hypothesis_id": HID, "verdict": verdict,
        "coefficient": estimate["coefficient"] if estimate else None,
        "ci90": estimate["ci90"] if estimate else None,
        "equivalence_margin": MARGIN,
        "evidence_state": evidence_state,
    }
    rows = [{
        "term": "log_annual_hours_worked",
        **{name: estimate[name] for name in COEFFICIENT_COLUMNS if name != "term"},
    }] if estimate else []
    return diagnostics, manifest, packet, card, wrapper, chart, rows


def assert_records_match(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label} fields mismatch")
        for key, value in expected.items():
            assert_records_match(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            raise AssertionError(f"{label} length mismatch")
        for index, value in enumerate(expected):
            assert_records_match(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, int):
        if isinstance(actual, bool) or not isinstance(actual, int) or actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, float):
        try:
            value = float(actual)
        except (TypeError, ValueError) as error:
            raise AssertionError(f"{label} not numeric") from error
        if not math.isfinite(value) or not math.isfinite(expected) or not math.isclose(
            value, expected, rel_tol=1e-8, abs_tol=1e-10
        ):
            raise AssertionError(f"{label} mismatch")
    elif actual != expected:
        raise AssertionError(f"{label} mismatch")


def read_coefficient_rows(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_parquet(path)
    if list(frame.columns) != list(COEFFICIENT_COLUMNS):
        raise AssertionError("stored coefficient columns mismatch")
    return [
        {key: value.tolist() if hasattr(value, "tolist") else value
         for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def write_run(prereg_commit: str, sources: dict[str, dict[str, str]],
              gate: dict[str, Any], verdict: str, reason: str,
              estimate: dict[str, Any] | None) -> dict[str, Any]:
    import pandas as pd

    run_dir = ROOT / RUN_REL
    if run_dir.exists():
        raise FileExistsError(f"existing run: {RUN_REL}")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostic, manifest, packet, card, wrapper, chart, rows = artifact_records(
        prereg_commit, sources, gate, verdict, reason, estimate, stamp,
    )
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{HID}.tmp-", dir=run_dir.parent))
    try:
        (staging_dir / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
        (staging_dir / "diagnostics.json").write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
        (staging_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        (staging_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
        (staging_dir / "result_card.md").write_text(card, encoding="utf-8")
        (staging_dir / "replication.py").write_text(wrapper, encoding="utf-8")
        (staging_dir / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
        pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS).to_parquet(
            staging_dir / "coefficients.parquet", index=False,
        )
        # The sibling rename publishes only a complete packet on this filesystem.
        os.replace(staging_dir, run_dir)
    except BaseException:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    return {"hypothesis_id": HID, "verdict": verdict, "run_dir": RUN_REL,
            "evidence_state": diagnostic["evidence_state"]}


def run_one() -> dict[str, Any]:
    prereg_commit = registration_commit()
    if (ROOT / RUN_REL).exists():
        raise FileExistsError(f"existing run: {RUN_REL}")
    spec = validate_spec()
    try:
        sources = verified_sources(spec)
    except Exception as error:
        sources = declared_sources(spec, "unverified")
        gate = unverified_gate("source_custody", error, False, False)
        reason = f"source custody failed before value access: {type(error).__name__}: {error}"
        return write_run(prereg_commit, sources, gate, "INCONCLUSIVE", reason, None)
    try:
        keys = key_envelope(sources)
        countries = {country for country, _ in keys}
        if len(keys) < MIN_OBSERVATIONS or len(countries) < MIN_COUNTRIES:
            raise ValueError("key-only envelope below registered sample floor")
    except Exception as error:
        gate = unverified_gate("key_preflight", error, True, False)
        return write_run(prereg_commit, sources, gate, "INCONCLUSIVE", (
            f"key preflight failed before value access: {type(error).__name__}: {error}"
        ), None)
    gate, verdict, reason, estimate = estimate_one(sources)
    return write_run(prereg_commit, sources, gate, verdict, reason, estimate)


def check_one() -> dict[str, Any]:
    prereg_commit = registration_commit()
    run_dir = ROOT / RUN_REL
    if not run_dir.is_dir():
        raise FileNotFoundError(f"missing run: {RUN_REL}")
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text(encoding="utf-8"))
    packet = yaml.safe_load((run_dir / "evidence_packet.yaml").read_text(encoding="utf-8"))
    chart = json.loads((run_dir / "chart_data.json").read_text(encoding="utf-8"))
    card = (run_dir / "result_card.md").read_text(encoding="utf-8")
    wrapper = (run_dir / "replication.py").read_text(encoding="utf-8")
    if (run_dir / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes():
        raise AssertionError("stored hypothesis snapshot mismatch")
    coefficients = read_coefficient_rows(run_dir / "coefficients.parquet")
    stored_gate = diagnostics["preflight"]
    stored_verdict = diagnostics["verdict_label"]
    stored_reason = diagnostics["verdict_reason"]
    stored_estimate = diagnostics["estimate"]
    spec = validate_spec()
    phase = (stored_gate.get("failure") or {}).get("phase")
    sources = (declared_sources(spec, "unverified") if phase == "source_custody"
               else verified_sources(spec))
    expected = artifact_records(
        prereg_commit, sources, stored_gate, stored_verdict, stored_reason,
        stored_estimate, diagnostics["run_utc"],
    )
    for label, actual, want in zip(
        ("diagnostics", "manifest", "packet", "chart", "coefficients"),
        (diagnostics, manifest, packet, chart, coefficients),
        (expected[0], expected[1], expected[2], expected[5], expected[6]),
    ):
        assert_records_match(actual, want, label)
    if card != expected[3] or wrapper != expected[4]:
        raise AssertionError("result card or replication wrapper mismatch")
    if phase == "source_custody":
        try:
            verified_sources(spec)
        except Exception as error:
            gate = unverified_gate("source_custody", error, False, False)
            verdict = "INCONCLUSIVE"
            reason = f"source custody failed before value access: {type(error).__name__}: {error}"
            estimate = None
        else:
            raise AssertionError("stored source-custody failure no longer reproduces")
    elif phase == "key_preflight":
        try:
            keys = key_envelope(sources)
            countries = {country for country, _ in keys}
            if len(keys) < MIN_OBSERVATIONS or len(countries) < MIN_COUNTRIES:
                raise ValueError("key-only envelope below registered sample floor")
        except Exception as error:
            gate = unverified_gate("key_preflight", error, True, False)
            verdict = "INCONCLUSIVE"
            reason = f"key preflight failed before value access: {type(error).__name__}: {error}"
            estimate = None
        else:
            raise AssertionError("stored key-preflight failure no longer reproduces")
    elif phase == "panel_construction":
        key_envelope(sources)
        try:
            build_panel(sources)
        except Exception as error:
            gate = unverified_gate("panel_construction", error, True, None)
            verdict = "INCONCLUSIVE"
            reason = f"panel construction failed before estimation: {type(error).__name__}: {error}"
            estimate = None
        else:
            raise AssertionError("stored panel-construction failure no longer reproduces")
    else:
        key_envelope(sources)
        gate, verdict, reason, estimate = estimate_one(sources)
    assert_records_match(stored_gate, gate, "sample gate")
    assert_records_match(stored_verdict, verdict, "verdict")
    assert_records_match(stored_reason, reason, "verdict reason")
    assert_records_match(stored_estimate, estimate, "estimate")
    return {"hypothesis_id": HID, "replay_verified": True,
            "failure_reproduced": phase is not None,
            "evidence_state": diagnostics["evidence_state"],
            "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = preflight()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["key_envelope_passed"] else 1
    result = check_one() if args.check else run_one()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
