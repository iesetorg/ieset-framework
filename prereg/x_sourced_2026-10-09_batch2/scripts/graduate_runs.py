"""Write engine/runs/<id>/ artifacts (diagnostics.json, result_card.md, replication.py, manifest.yaml)
for the X-sourced batches from their committed prereg results.  Usage: graduate_runs.py --batch 1|2"""
import argparse, glob, hashlib, json, pathlib, re, datetime, yaml
ROOT = pathlib.Path(__file__).resolve().parents[3]
BATCH = {
 "1": dict(dir="prereg/x_sourced_2026-10-09", runner="prereg/x_sourced_2026-10-09/scripts/run_x_hypotheses.py", spec_commit="5ce9b12c2",
   fetch_note="Inputs are the vintages listed below (data/vintages is gitignored); re-fetch with the publisher fetchers in data/fetchers/ before replicating.",
   timing=("Falsification thresholds were frozen in a local SHA-256 ledger (prereg/x_sourced_2026-10-09/PREREG_LEDGER.json, 2026-10-09 12:21:22 UTC) "
           "before the analysis script ran. The spec was committed to git (5ce9b12c2) only AFTER the analysis had run. Git history shows the spec "
           "before this run directory, but the thresholds were not git-timestamped before the run: treat this as a locally frozen test, not an "
           "independently timestamped pre-registration. Spec status remains draft.")),
 "2": dict(dir="prereg/x_sourced_2026-10-09_batch2", runner="prereg/x_sourced_2026-10-09_batch2/scripts/run_batch2.py", spec_commit="b79b1fb1e",
   fetch_note="Re-fetch inputs with prereg/x_sourced_2026-10-09_batch2/scripts/fetch_batch2.py (needs FRED/EIA keys in .env), then run the runner.",
   timing=("Spec and SHA-256 ledger committed to git in b79b1fb1e (2026-10-09 17:40 UTC) before any input for this test was fetched "
           "(first fetch 17:41 UTC); results committed afterwards in 3659330be. Thresholds were written by the drafting agent after "
           "reading the source post, so the claimed figures were known; the data were not.")),
}
OWN = {"california_fast_food_20_wage_restaurant_employment"}
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def fmt(v):
    if isinstance(v, float): return f"{v:,.3f}".rstrip("0").rstrip(".")
    if isinstance(v, (list, dict)): return json.dumps(v, default=str)[:400]
    return str(v)
def steel(hid):
    t = (ROOT / f"hypotheses/steelman/{hid}.md").read_text()
    m = re.search(r"Strongest opposing case:\s*(.+?)(?:\n\n|$)", t, re.S); return m.group(1).strip() if m else ""
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--batch", required=True, choices=["1", "2"]); a = ap.parse_args(); B = BATCH[a.batch]
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for rp in sorted(glob.glob(str(ROOT / B["dir"] / "runs/*/results.json"))):
        r = json.loads(pathlib.Path(rp).read_text()); hid = r["hypothesis_id"]
        spec_p = next(ROOT.glob(f"hypotheses/*/{hid}.yaml")); spec = yaml.safe_load(spec_p.read_text())
        label = r["verdict"].split(",")[0].strip().upper(); verdict = f"{label} — {r['headline']}"
        urls = [] if hid in OWN else spec.get("source_provenance", {}).get("archive_refs", [])
        src = ("Our own addition — no source post. (The batch-1 spec lists a Seattle post as context only.)" if hid in OWN else "; ".join(urls))
        out = ROOT / "engine/runs" / hid; out.mkdir(parents=True, exist_ok=True)
        rel_results = str(pathlib.Path(rp).relative_to(ROOT))
        diag = dict(hypothesis_id=hid, evidence_type=spec.get("evidence_type"), template=spec.get("estimator", {}).get("template"),
                    run_utc=r["run_utc"], country=(spec["sample"]["countries"][0] if len(spec["sample"]["countries"]) == 1 else spec["sample"]["countries"]),
                    verdict=verdict, verdict_label=label, verdict_reason=r["headline"], falsification_rule_text=spec["falsification"]["rule"],
                    metrics=r["metrics"], inputs=r["inputs"], runner=B["runner"], results_file=rel_results,
                    preregistration=dict(ledger=f"{B['dir']}/PREREG_LEDGER.json", spec_commit=B["spec_commit"], timing_note=B["timing"]),
                    source_posts=urls, source_note=("our own addition" if hid in OWN else "X post(s) that prompted the test"))
        (out / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=float, ensure_ascii=False) + "\n")
        met = "\n".join(f"- **{k}:** {fmt(v)}" for k, v in r["metrics"].items())
        ins = "\n".join(f"- `{i}`" for i in r["inputs"])
        card = f"""# Result card — {hid}

**Verdict:** {verdict}

## Claim tested
{spec['claim']}

Evidence type: {spec.get('evidence_type')} (not a causal test).

## Pre-registration
- **Falsification rule:** {spec['falsification']['rule']}
- **Spec:** `{spec_p.relative_to(ROOT)}` (status: {spec.get('status')}); ledger `{B['dir']}/PREREG_LEDGER.json`; spec commit {B['spec_commit']}
- **Timing:** {B['timing']}

## Result
{r['headline']}

{met}

## Source
{src}

## Strongest objection (steelman)
{steel(hid)}

## Inputs
{ins}

## Replication
{B['fetch_note']} Then run `python engine/runs/{hid}/replication.py` from the repo root (it runs `{B['runner']}` and prints this hypothesis's result from `{rel_results}`).

_Generated by `{B['dir']}/../x_sourced_2026-10-09_batch2/scripts/graduate_runs.py` at {now}_
""".replace(f"{B['dir']}/../x_sourced_2026-10-09_batch2", "prereg/x_sourced_2026-10-09_batch2")
        (out / "result_card.md").write_text(card)
        (out / "replication.py").write_text(f'''#!/usr/bin/env python3
"""Replicate {hid} (X-sourced batch {a.batch}). Re-runs the committed runner and prints this hypothesis's result."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[3]

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "{B['runner']}"), run_name="__main__")
    print(json.dumps(json.loads((ROOT / "{rel_results}").read_text()), indent=1))
''')
        man = dict(hypothesis_id=hid, spec=str(spec_p.relative_to(ROOT)), spec_sha256=sha(spec_p), spec_commit=B["spec_commit"],
                   ledger=f"{B['dir']}/PREREG_LEDGER.json", runner=B["runner"], results=rel_results, run_utc=r["run_utc"],
                   inputs=[dict(path=i, sha256=(sha(ROOT / i) if (ROOT / i).exists() else None)) for i in r["inputs"]], generated_utc=now)
        (out / "manifest.yaml").write_text(yaml.safe_dump(man, sort_keys=False))
        print(label, hid)
main()
