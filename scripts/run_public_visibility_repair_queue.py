#!/usr/bin/env python3
"""Execute public-visibility repair queue reruns for supported estimators.

This runner consumes a queue file produced by
`scripts/plan_public_visibility_repair_queue.py`, executes the
`needs_successful_rerun` subset, and emits a compact execution audit.

Methodology guardrails:
- Does not mutate school links, scores, polarity, or claim text.
- Uses each hypothesis' registered estimator template for dispatch.
- Surfaces unsupported estimator templates explicitly instead of guessing.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_descriptive
import run_did_callaway_santanna
import run_event_study
import run_local_projections
import run_multi_metric_checklist
import run_panel_fe
import run_cointegration_vecm
import run_synth_did


DEFAULT_QUEUE = ROOT / "engine" / "audits" / f"public_visibility_repair_queue_{date.today().isoformat()}.json"
REAL_VERDICT_PREFIXES = (
    "SUPPORTED", "REFUTED", "PARTIAL", "MIXED", "WEAKLY",
    "WEAKENED", "NOT SUPPORTED", "NOT_SUPPORTED", "BLOCKED",
)


def count_verdict(counts: Counter[str], verdict: str) -> str:
    text = str(verdict or "").strip().upper()
    if text.startswith("INCONCLUSIVE") or "INCONCLUSIVE_DATA_PENDING" in text:
        counts["inconclusive_persisted"] += 1
        return "inconclusive_persisted"
    for prefix in REAL_VERDICT_PREFIXES:
        if text.startswith(prefix):
            counts[prefix.lower().replace(" ", "_")] += 1
            return prefix.lower().replace(" ", "_")
    counts["other"] += 1
    return "other"


def resolve_template(hid: str, row_template: str | None) -> str:
    if row_template and row_template != "unknown":
        return row_template
    found = run_panel_fe.load_spec(hid)
    if not found:
        return "unknown"
    _, spec = found
    return str((spec.get("estimator") or {}).get("template") or "unknown").strip() or "unknown"


def replication_path(hid: str) -> Path:
    return ROOT / "engine" / "runs" / hid / "replication.py"


def is_generated_replication_wrapper(path: Path) -> bool:
    """Return True for thin wrappers emitted by backfill_replication_wrappers.py.

    Handcrafted run-level replications often contain hypothesis-specific gates
    that are stricter than the generic estimator template. Generated wrappers,
    by contrast, intentionally route back to a canonical script and should not
    be treated as bespoke methodology.
    """
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return False
    return "from _replication_runner import rerun" in text and "RUNNER =" in text


def run_replication_script(hid: str, replication: Path) -> dict | str:
    result = subprocess.run(
        [sys.executable, str(replication)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        raise RuntimeError(stderr or stdout or f"replication.py exited {result.returncode}")
    diag_path = ROOT / "engine" / "runs" / hid / "diagnostics.json"
    if diag_path.exists():
        try:
            diag = json.loads(diag_path.read_text())
            return {
                "verdict": diag.get("verdict") or diag.get("verdict_label"),
                "runner": f"engine/runs/{hid}/replication.py",
            }
        except Exception:
            pass
    return f"  · {hid}: replicated via engine/runs/{hid}/replication.py"


def run_by_template(
    hid: str,
    template: str,
    *,
    force: bool,
    persist_preflight_inconclusive: bool,
):
    replication = replication_path(hid)
    if replication.exists() and not is_generated_replication_wrapper(replication):
        return run_replication_script(hid, replication)

    if template in ("panel_fe", "panel_fe_decomposition"):
        return run_panel_fe.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template == "descriptive":
        return run_descriptive.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template in ("did_callaway_santanna", "did_chaisemartin"):
        return run_did_callaway_santanna.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template == "event_study":
        return run_event_study.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template == "local_projections":
        return run_local_projections.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template == "cointegration_vecm":
        return run_cointegration_vecm.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template in ("synth_did", "synthetic_control"):
        return run_synth_did.run_one(
            hid,
            force=force,
            persist_preflight_inconclusive=persist_preflight_inconclusive,
        )
    if template == "multi_metric_checklist":
        return run_multi_metric_checklist.run_hypothesis(hid)

    replication = replication_path(hid)
    if replication.exists():
        return run_replication_script(hid, replication)
    raise ValueError(f"unsupported template={template}")


def load_rows(queue_json: Path, reason: str, limit: int | None) -> list[dict]:
    payload = json.loads(queue_json.read_text())
    rows = [r for r in payload.get("queue", []) if r.get("reason") == reason]
    rows.sort(key=lambda r: (-float(r.get("priority_score") or 0), str(r.get("hypothesis_id") or "")))
    dedup: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        hid = row.get("hypothesis_id")
        if not hid or hid in seen:
            continue
        seen.add(hid)
        dedup.append(row)
    if limit is not None:
        dedup = dedup[:limit]
    return dedup


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-json", default=str(DEFAULT_QUEUE))
    ap.add_argument("--reason", default="needs_successful_rerun")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--write-preflight-inconclusive", action="store_true")
    ap.add_argument(
        "--out-base",
        default=str(ROOT / "engine" / "audits" / f"public_visibility_repair_wave_{date.today().isoformat()}"),
    )
    args = ap.parse_args()

    queue_json = Path(args.queue_json)
    if not queue_json.exists():
        raise SystemExit(f"Queue JSON not found: {queue_json}")

    rows = load_rows(queue_json, args.reason, args.limit)
    counts: Counter[str] = Counter()
    unresolved: list[dict] = []
    executed: list[dict] = []

    print(f"Executing {len(rows)} queue hypothesis reruns (reason={args.reason})")
    for row in rows:
        hid = row["hypothesis_id"]
        if not args.force and run_panel_fe.has_committed_verdict(hid):
            print(f"  · {hid}: skipped (committed verdict already on disk)")
            counts["committed_skip"] += 1
            continue
        template = resolve_template(hid, row.get("template"))
        try:
            out = run_by_template(
                hid,
                template,
                force=args.force,
                persist_preflight_inconclusive=args.write_preflight_inconclusive,
            )
            if isinstance(out, dict):
                verdict = str(out.get("verdict") or "INCONCLUSIVE_DATA_PENDING")
                bucket = count_verdict(counts, verdict)
                prefix = "·" if bucket != "inconclusive_persisted" else "⚠"
                print(f"  {prefix} {hid}: {verdict}")
                executed.append(
                    {
                        "hypothesis_id": hid,
                        "template": template,
                        "status": verdict,
                        "bucket": bucket,
                        "runner": out.get("runner"),
                    }
                )
            else:
                print(out)
                run_panel_fe.bump_bulk_run_count(counts, out)
                executed.append({"hypothesis_id": hid, "template": template, "status": out.strip()})
        except ValueError as exc:
            msg = str(exc)
            print(f"  ✗ {hid}: {msg}")
            counts["unsupported_template"] += 1
            unresolved.append({"hypothesis_id": hid, "template": template, "error": msg})
        except Exception as exc:
            print(f"  ✗ {hid}: runner crashed — {exc}")
            counts["crashed"] += 1
            unresolved.append({"hypothesis_id": hid, "template": template, "error": str(exc)})

    run_panel_fe.print_bulk_run_summary("public-visibility repair wave", dict(counts))

    out_base = Path(args.out_base)
    report = {
        "generated_at": date.today().isoformat(),
        "queue_json": str(queue_json),
        "reason": args.reason,
        "limit": args.limit,
        "counts": dict(counts),
        "unresolved": unresolved,
        "executed": executed,
    }
    out_json = out_base.with_suffix(".json")
    out_md = out_base.with_suffix(".md")
    out_json.write_text(json.dumps(report, indent=2))

    lines = [
        "# Public Visibility Repair Wave",
        "",
        f"Generated: {date.today().isoformat()}",
        f"- Queue: `{queue_json}`",
        f"- Reason: `{args.reason}`",
        f"- Limit: `{args.limit}`",
        "",
        "## Counts",
        "",
    ]
    for k, v in sorted(counts.items()):
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Unresolved Templates", ""])
    if not unresolved:
        lines.append("- none")
    else:
        for row in unresolved:
            lines.append(f"- `{row['hypothesis_id']}` ({row['template']}): {row['error']}")
    out_md.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
