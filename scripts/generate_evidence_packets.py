#!/usr/bin/env python3
"""Generate public verification packets for hypothesis runs.

Evidence packets are the bridge between backend research artifacts and a
policy-facing evidence browser. They normalize scattered run files into a
single audit object:

  - verdict and preregistration pointers
  - input data vintages and source-manifest references
  - hash verification status for local artifacts
  - missing data gates and caveats
  - reproduction commands and human-readable references

The generator is intentionally tolerant of older run manifest shapes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
HYPOTHESES = ROOT / "hypotheses"
FETCH_MANIFESTS = ROOT / "data" / "manifests"
INDEX_JSON = ROOT / "engine" / "evidence_packets_index.json"
INDEX_MD = ROOT / "engine" / "evidence_packets_index.md"

PACKET_VERSION = 1
LEGACY_HYPOTHESIS_ID_MAP = {
    "oecd_minimum_wage_bite_low_education_unemployment": "oecd_low_education_unemployment_minimum_wage_bite",
    "us_qcew_county_food_service_minimum_wage_panel": "bls_qcew_county_food_service_minimum_wage_growth",
}
RUN_ARTIFACTS = [
    "hypothesis.yaml",
    "manifest.yaml",
    "diagnostics.json",
    "result_card.md",
    "replication.py",
    "coefficients.parquet",
    "chart_data.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except Exception as exc:  # keep packet generation robust
        return {"_load_error": str(exc)}
    return doc if isinstance(doc, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {"_load_error": str(exc)}
    return doc if isinstance(doc, dict) else {}


def verdict_bucket(raw: object) -> str:
    text = str(raw or "").strip().lower()
    if text.startswith(("supported", "weakly supported")):
        return "supported"
    if text.startswith(("refuted", "falsified", "not supported")):
        return "refuted"
    if text.startswith(("partial", "mixed", "weakened")):
        return "partial"
    if text.startswith("inconclusive"):
        return "inconclusive"
    if text.startswith("blocked"):
        return "blocked"
    if not text:
        return "missing"
    return "other"


def git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None
    return out.strip() or None


def canonical_hypothesis_id(hypothesis_id: str) -> str:
    return LEGACY_HYPOTHESIS_ID_MAP.get(hypothesis_id, hypothesis_id)


def hypothesis_path(hypothesis_id: str) -> Path | None:
    hypothesis_id = canonical_hypothesis_id(hypothesis_id)
    for path in HYPOTHESES.glob("*/*.yaml"):
        if path.parent.name in {"steelman", "conditional_taxonomy"}:
            continue
        if path.stem == hypothesis_id:
            return path
        doc = load_yaml(path)
        if doc.get("hypothesis_id") == hypothesis_id:
            return path
    return None


def hypothesis_lookup() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in HYPOTHESES.glob("*/*.yaml"):
        if path.parent.name in {"steelman", "conditional_taxonomy"}:
            continue
        out[path.stem] = path
        doc = load_yaml(path)
        hid = doc.get("hypothesis_id")
        if hid:
            out[str(hid)] = path
    for legacy, canonical in LEGACY_HYPOTHESIS_ID_MAP.items():
        if canonical in out:
            out[legacy] = out[canonical]
    return out


def fetch_manifest_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for path in sorted(FETCH_MANIFESTS.glob("*.yaml")):
        doc = load_yaml(path)
        entries = doc.get("entries") or []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            parquet = entry.get("parquet_path")
            if not parquet:
                continue
            item = dict(entry)
            item["_fetch_manifest"] = rel(path)
            item["_fetch_manifest_run_utc"] = doc.get("run_utc")
            lookup[str(parquet)] = item
    return lookup


def normalise_vintage_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    vintages = manifest.get("vintages")
    items: list[dict[str, Any]] = []
    if isinstance(vintages, list):
        for i, item in enumerate(vintages):
            if isinstance(item, str):
                items.append({"name": f"input_{i + 1}", "vintage_file": item})
            elif isinstance(item, dict):
                path = item.get("vintage_file") or item.get("path") or item.get("parquet_path")
                rows = dict(item)
                if path:
                    rows["vintage_file"] = path
                rows.setdefault("name", f"input_{i + 1}")
                items.append(rows)
    elif isinstance(vintages, dict):
        for name, item in vintages.items():
            if isinstance(item, str):
                items.append({"name": str(name), "vintage_file": item})
            elif isinstance(item, dict):
                rows = dict(item)
                path = rows.get("vintage_file") or rows.get("path") or rows.get("parquet_path")
                if path:
                    rows["vintage_file"] = path
                rows.setdefault("name", str(name))
                items.append(rows)
    return [item for item in items if item.get("vintage_file")]


def infer_source_from_path(vintage_file: str) -> dict[str, Any]:
    parts = Path(vintage_file).parts
    publisher = parts[2] if len(parts) >= 4 and parts[0] == "data" and parts[1] == "vintages" else None
    stem = Path(vintage_file).name.rsplit("@", 1)[0]
    return {"publisher": publisher, "series_id": stem}


def source_type(source_url: str | None) -> str:
    text = str(source_url or "")
    if text.startswith("manual://"):
        return "manual"
    if text.startswith("derived://") or text.startswith("constructed:"):
        return "derived"
    if text.startswith("http://") or text.startswith("https://"):
        return "official"
    return "unknown"


def build_data_input(
    item: dict[str, Any],
    lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    vintage_file = str(item.get("vintage_file"))
    source_manifest = lookup.get(vintage_file, {})
    inferred = infer_source_from_path(vintage_file)
    path = ROOT / vintage_file
    computed = sha256(path)
    declared = (
        item.get("sha256")
        or source_manifest.get("sha256")
        or item.get("hash")
        or source_manifest.get("hash")
    )
    if computed and declared:
        hash_status = "match" if str(computed) == str(declared) else "mismatch"
    elif computed:
        hash_status = "computed_only"
    elif declared:
        hash_status = "declared_only"
    else:
        hash_status = "missing"

    publisher = item.get("publisher") or source_manifest.get("publisher") or inferred["publisher"]
    series_id = item.get("series") or item.get("series_id") or source_manifest.get("series_id") or inferred["series_id"]
    source_url = item.get("source_url") or source_manifest.get("source_url")
    methodology_url = item.get("methodology_url") or source_manifest.get("methodology_url")

    return {
        "name": item.get("name") or series_id,
        "publisher": publisher,
        "series_id": series_id,
        "vintage_file": vintage_file,
        "exists_locally": path.exists(),
        "hash": {
            "declared_sha256": declared,
            "computed_sha256": computed,
            "status": hash_status,
        },
        "source": {
            "type": source_type(source_url),
            "url": source_url,
            "methodology_url": methodology_url,
            "license": item.get("license") or source_manifest.get("license"),
            "fetch_utc": item.get("fetch_utc") or source_manifest.get("fetch_utc"),
            "fetch_manifest": source_manifest.get("_fetch_manifest"),
        },
        "coverage": {
            "start_date": item.get("start_date") or source_manifest.get("start_date"),
            "end_date": item.get("end_date") or source_manifest.get("end_date"),
            "frequency": item.get("frequency") or source_manifest.get("frequency"),
            "rows": item.get("rows") or source_manifest.get("rows"),
            "units": item.get("units") or source_manifest.get("units"),
            "currency": item.get("currency") or source_manifest.get("currency"),
        },
        "extra": item.get("extra") or source_manifest.get("extra") or {},
    }


def artifact_entry(run_dir: Path, name: str) -> dict[str, Any] | None:
    path = run_dir / name
    digest = sha256(path)
    if digest is None:
        return None
    return {
        "path": rel(path),
        "sha256": digest,
        "bytes": path.stat().st_size,
    }


def build_packet(
    run_dir: Path,
    lookup: dict[str, dict[str, Any]],
    commit: str | None,
    hypotheses: dict[str, Path] | None = None,
) -> dict[str, Any]:
    run_hid = run_dir.name
    hid = canonical_hypothesis_id(run_hid)
    diagnostics = load_json(run_dir / "diagnostics.json")
    manifest = load_yaml(run_dir / "manifest.yaml")
    hyp_path = (hypotheses or {}).get(hid) or hypothesis_path(hid)
    hypothesis = load_yaml(hyp_path) if hyp_path else {}
    raw_verdict = (
        diagnostics.get("verdict_label")
        or diagnostics.get("verdict")
        or diagnostics.get("status")
        or manifest.get("status")
        or ""
    )
    missing = (
        manifest.get("missing_series")
        or diagnostics.get("missing_series")
        or diagnostics.get("missing_inputs")
        or []
    )
    if isinstance(missing, dict):
        missing = list(missing.values())
    if not isinstance(missing, list):
        missing = [str(missing)]

    data_inputs = [
        build_data_input(item, lookup)
        for item in normalise_vintage_items(manifest)
    ]
    references = []
    seen_refs = set()
    for source in data_inputs:
        for kind, url in (
            ("source", source["source"].get("url")),
            ("methodology", source["source"].get("methodology_url")),
        ):
            if url and url not in seen_refs:
                seen_refs.add(url)
                references.append(
                    {
                        "kind": kind,
                        "publisher": source.get("publisher"),
                        "series_id": source.get("series_id"),
                        "url": url,
                    }
                )

    artifacts = [artifact_entry(run_dir, name) for name in RUN_ARTIFACTS]
    artifacts = [item for item in artifacts if item is not None]
    if hyp_path:
        h_entry = artifact_entry(hyp_path.parent, hyp_path.name)
        if h_entry:
            artifacts.insert(0, h_entry)
    steelman = hypothesis.get("steelman")
    if steelman:
        s_path = ROOT / str(steelman)
        s_digest = sha256(s_path)
        if s_digest:
            artifacts.append({"path": rel(s_path), "sha256": s_digest, "bytes": s_path.stat().st_size})

    prereg = {
        "claim": hypothesis.get("claim"),
        "falsification_rule": (hypothesis.get("falsification") or {}).get("rule")
        if isinstance(hypothesis.get("falsification"), dict)
        else hypothesis.get("falsification"),
        "threshold": (hypothesis.get("falsification") or {}).get("threshold")
        if isinstance(hypothesis.get("falsification"), dict)
        else None,
        "estimator": hypothesis.get("estimator"),
        "steelman": steelman,
    }

    return {
        "packet_version": PACKET_VERSION,
        "generated_utc": utc_now(),
        "repository": {
            "root": str(ROOT),
            "git_commit": commit,
        },
        "hypothesis": {
            "id": hid,
            "legacy_id": run_hid if run_hid != hid else None,
            "path": rel(hyp_path) if hyp_path else None,
            "school": hypothesis.get("school"),
            "topic": hypothesis.get("topic") or hypothesis.get("category"),
            "claim": hypothesis.get("claim"),
        },
        "verdict": {
            "raw": raw_verdict,
            "bucket": verdict_bucket(raw_verdict),
            "reason": diagnostics.get("reason") or diagnostics.get("verdict_reason") or manifest.get("reason"),
            "status": diagnostics.get("status") or manifest.get("status"),
        },
        "preregistration": prereg,
        "reproduction": {
            "run_dir": rel(run_dir),
            "runner": manifest.get("runner"),
            "replication_script": rel(run_dir / "replication.py") if (run_dir / "replication.py").exists() else None,
            "suggested_command": f"python {rel(run_dir / 'replication.py')}"
            if (run_dir / "replication.py").exists()
            else None,
        },
        "data": {
            "inputs": data_inputs,
            "missing_series": [str(x) for x in missing],
            "data_quality": summarize_data_quality(data_inputs, missing),
        },
        "artifacts": artifacts,
        "references": references,
        "caveats": caveats(data_inputs, missing, diagnostics, manifest),
    }


def summarize_data_quality(data_inputs: list[dict[str, Any]], missing: list[Any]) -> dict[str, Any]:
    statuses = [item["hash"]["status"] for item in data_inputs]
    official = sum(1 for item in data_inputs if item["source"]["type"] == "official")
    manual = sum(1 for item in data_inputs if item["source"]["type"] == "manual")
    verified = sum(1 for status in statuses if status == "match")
    if missing:
        grade = "incomplete"
    elif data_inputs and verified == len(data_inputs):
        grade = "reproducible_hash_verified"
    elif data_inputs:
        grade = "partial_provenance"
    else:
        grade = "no_input_vintages_recorded"
    return {
        "grade": grade,
        "input_count": len(data_inputs),
        "official_source_count": official,
        "manual_source_count": manual,
        "hash_status_counts": {status: statuses.count(status) for status in sorted(set(statuses))},
        "missing_series_count": len(missing),
    }


def caveats(
    data_inputs: list[dict[str, Any]],
    missing: list[Any],
    diagnostics: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    out: list[str] = []
    if missing:
        out.append("Run has unresolved missing-series gates; verdict should not be treated as dispositive.")
    if not data_inputs:
        out.append("Run manifest records no input vintages; provenance is limited to result artifacts.")
    if any(item["hash"]["status"] == "mismatch" for item in data_inputs):
        out.append("At least one local vintage hash does not match its declared manifest hash.")
    if any(item["source"]["type"] == "manual" for item in data_inputs):
        out.append("At least one input is a manual-drop source; verify the referenced source document and row-level notes.")
    for key in ("caveats", "limitations", "deviations"):
        value = diagnostics.get(key) or manifest.get(key)
        if isinstance(value, list):
            out.extend(str(v) for v in value)
        elif value:
            out.append(str(value))
    return sorted(dict.fromkeys(out))


def write_packet(
    run_dir: Path,
    lookup: dict[str, dict[str, Any]],
    commit: str | None,
    hypotheses: dict[str, Path],
) -> dict[str, Any]:
    packet = build_packet(run_dir, lookup, commit, hypotheses)
    out = run_dir / "evidence_packet.yaml"
    out.write_text(yaml.safe_dump(packet, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return packet


def discover_runs(args: argparse.Namespace) -> list[Path]:
    if args.run:
        return [RUNS / rid for rid in args.run]
    if args.all:
        return sorted(p for p in RUNS.iterdir() if p.is_dir())
    recent = sorted(
        [p for p in RUNS.iterdir() if p.is_dir() and (p / "diagnostics.json").exists()],
        key=lambda p: (p / "diagnostics.json").stat().st_mtime,
        reverse=True,
    )
    return recent[: args.limit]


def write_index(packets: list[dict[str, Any]]) -> None:
    rows = []
    for packet in packets:
        rows.append(
            {
                "hypothesis_id": packet["hypothesis"]["id"],
                "verdict_bucket": packet["verdict"]["bucket"],
                "verdict": packet["verdict"]["raw"],
                "run_dir": packet["reproduction"]["run_dir"],
                "packet_path": f"{packet['reproduction']['run_dir']}/evidence_packet.yaml",
                "data_quality": packet["data"]["data_quality"]["grade"],
                "input_count": packet["data"]["data_quality"]["input_count"],
                "missing_series_count": packet["data"]["data_quality"]["missing_series_count"],
                "reference_count": len(packet["references"]),
            }
        )
    payload = {
        "generated_utc": utc_now(),
        "packet_version": PACKET_VERSION,
        "packet_count": len(rows),
        "packets": sorted(rows, key=lambda r: (r["verdict_bucket"], r["hypothesis_id"])),
    }
    INDEX_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Evidence Packets Index",
        "",
        f"- Packets indexed: {len(rows)}",
        f"- Generated UTC: {payload['generated_utc']}",
        "",
        "| hypothesis | verdict | data quality | inputs | missing | packet |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["packets"][:200]:
        lines.append(
            f"| `{row['hypothesis_id']}` | {row['verdict_bucket']} | {row['data_quality']} | "
            f"{row['input_count']} | {row['missing_series_count']} | `{row['packet_path']}` |"
        )
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", help="Hypothesis/run id to packetize. Can be repeated.")
    parser.add_argument("--all", action="store_true", help="Packetize every engine/runs directory.")
    parser.add_argument("--limit", type=int, default=25, help="Default recent-run limit when --run/--all is omitted.")
    parser.add_argument("--no-index", action="store_true", help="Do not rewrite the global packet index.")
    args = parser.parse_args()

    lookup = fetch_manifest_lookup()
    hypotheses = hypothesis_lookup()
    commit = git_commit()
    packets = []
    for run_dir in discover_runs(args):
        if not run_dir.exists() or not run_dir.is_dir():
            print(f"skip missing run: {run_dir}")
            continue
        packet = write_packet(run_dir, lookup, commit, hypotheses)
        packets.append(packet)
        print(
            f"wrote {packet['reproduction']['run_dir']}/evidence_packet.yaml "
            f"({packet['verdict']['bucket']}, {packet['data']['data_quality']['grade']})"
        )
    if not args.no_index:
        write_index(packets)
        print(f"index: {rel(INDEX_JSON)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
