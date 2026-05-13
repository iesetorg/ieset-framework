#!/usr/bin/env python3
"""Discover official publisher file URLs for stubborn IESET data gaps.

This is intentionally a discovery/audit helper, not a broad scraper. It reads a
ZenRows key from stdin when requested, uses the repo's official-source HTTP
fallback stack, and writes a small Markdown/JSON audit with candidate URLs for
manual or automated follow-up.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "engine" / "audits"
sys.path.insert(0, str(ROOT))

from data.fetchers._http import get  # noqa: E402


@dataclass
class Candidate:
    cluster: str
    label: str
    url: str
    transport: str
    status_code: int
    note: str = ""


def _now_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _read_key_from_stdin() -> None:
    key = getpass.getpass("ZenRows API key: ").strip()
    if key:
        os.environ["ZENROWS_API_KEY"] = key


def _links(html: str, base: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    pattern = re.compile(
        r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )
    for href, text in pattern.findall(html):
        clean_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()
        out.append((clean_text, urljoin(base, href)))
    return out


def discover_irena() -> list[Candidate]:
    urls = [
        "https://www.irena.org/Publications/2025/Jun/Renewable-Power-Generation-Costs-in-2024",
        "https://www.irena.org/Digital-Report/Renewable-Power-Generation-Costs-in-2024",
    ]
    candidates: list[Candidate] = []
    for page_url in urls:
        payload = get(page_url, timeout=180, zenrows_js_render=True)
        for text, href in _links(payload.text, page_url):
            blob = f"{text} {href}".lower()
            if any(token in blob for token in ("download data", ".xlsx", ".xls", ".csv", "rpgc", "cost")):
                if any(ext in href.lower() for ext in (".xlsx", ".xls", ".csv", ".zip", ".pdf")) or "download" in blob:
                    candidates.append(
                        Candidate(
                            cluster="renewables_lcoe",
                            label=text or "IRENA link",
                            url=href,
                            transport=payload.transport,
                            status_code=payload.status_code,
                            note="Candidate from IRENA Renewable Power Generation Costs page.",
                        )
                    )
    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[Candidate] = []
    for c in candidates:
        if c.url not in seen:
            unique.append(c)
            seen.add(c.url)
    return unique


def discover_bls_oews() -> list[Candidate]:
    page_url = "https://www.bls.gov/oes/current/oes_pr.htm"
    payload = get(page_url, timeout=180, zenrows_js_render=True)
    candidates: list[Candidate] = []
    for text, href in _links(payload.text, page_url):
        blob = f"{text} {href}".lower()
        if any(token in blob for token in ("state", "all data", "xlsx", "txt", "may 2024", "may 2023", "may 2022", "may 2021", "may 2020", "may 2019")):
            if any(ext in href.lower() for ext in (".xlsx", ".xls", ".txt", ".zip", ".htm")):
                candidates.append(
                    Candidate(
                        cluster="minimum_wage",
                        label=text or "BLS OEWS link",
                        url=href,
                        transport=payload.transport,
                        status_code=payload.status_code,
                        note="Candidate from BLS OEWS tables page for historical state wage percentiles.",
                    )
                )
    seen: set[str] = set()
    unique: list[Candidate] = []
    for c in candidates:
        if c.url not in seen:
            unique.append(c)
            seen.add(c.url)
    return unique


def write_audit(candidates: list[Candidate]) -> tuple[Path, Path]:
    tag = _now_tag()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = AUDIT_DIR / f"data_gap_source_discovery_{tag}.json"
    md_path = AUDIT_DIR / f"data_gap_source_discovery_{tag}.md"
    json_path.write_text(json.dumps([asdict(c) for c in candidates], indent=2) + "\n")
    lines = [
        "# Data-Gap Source Discovery",
        "",
        f"- generated_utc: `{tag}`",
        f"- candidates: {len(candidates)}",
        "",
        "| cluster | label | url | transport | note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in candidates:
        label = c.label.replace("|", "\\|")
        note = c.note.replace("|", "\\|")
        lines.append(f"| `{c.cluster}` | {label} | {c.url} | `{c.transport}` | {note} |")
    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--read-zenrows-key-stdin", action="store_true")
    parser.add_argument(
        "--cluster",
        default="irena,bls_oews",
        help="Comma-separated discovery clusters: irena,bls_oews",
    )
    args = parser.parse_args()

    if args.read_zenrows_key_stdin:
        _read_key_from_stdin()

    clusters = {part.strip() for part in args.cluster.split(",") if part.strip()}
    candidates: list[Candidate] = []
    if "irena" in clusters:
        candidates.extend(discover_irena())
    if "bls_oews" in clusters:
        candidates.extend(discover_bls_oews())

    json_path, md_path = write_audit(candidates)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"candidates={len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
