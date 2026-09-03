#!/usr/bin/env python3
"""Generate a producer shot list from an IESET release package.

Reads case study / education brief / social hooks / thread (if present) and
writes a single producer-ready markdown file with scene beats, asset paths,
VO skeleton, and a publish checklist. Does not invent statistics — it only
assembles paths and text already on disk.

Usage:
  python3 scripts/generate_video_shot_list.py \\
    --hypothesis-id korean_institutional_divergence_gdp_gap \\
    --case-dir out/case_studies/20260710-korean-institutional-divergence-gdp-gap \\
    --out out/video_wave_20260710/02_korea/SHOT_LIST.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def first_permalink(text: str, hypothesis_id: str) -> str:
    m = re.search(r"https://framework\.ieset\.org/h/[a-z0-9_]+/?", text)
    if m:
        return m.group(0).rstrip("/") + "/"
    return f"https://framework.ieset.org/h/{hypothesis_id}/"


def list_assets(case_dir: Path) -> list[str]:
    assets = case_dir / "assets"
    if not assets.is_dir():
        return []
    out: list[str] = []
    for p in sorted(assets.iterdir()):
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".csv", ".json"}:
            out.append(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p))
    return out


def extract_verdict_line(text: str) -> str:
    for line in text.splitlines():
        if re.search(r"verdict", line, re.I) and (
            "SUPPORTED" in line.upper()
            or "REFUTED" in line.upper()
            or "PARTIAL" in line.upper()
        ):
            return line.strip()
    if "SUPPORTED" in text.upper():
        return "SUPPORTED (see result card)"
    return "See result card"


def extract_tweet_blocks(thread: str) -> list[str]:
    if not thread.strip():
        return []
    parts = re.split(r"\n(?=## (?:Tweet|Post)\s*\d)", thread)
    blocks = [p.strip() for p in parts if re.match(r"## (?:Tweet|Post)", p.strip())]
    return blocks


def build_shot_list(
    *,
    hypothesis_id: str,
    case_dir: Path,
    education_path: Path | None,
    social_path: Path | None,
    title: str,
    duration_hint: str,
) -> str:
    case_dir = case_dir if case_dir.is_absolute() else ROOT / case_dir
    case = read_text(case_dir / "case_study.md")
    thread = read_text(case_dir / "thread.md")
    sources = read_text(case_dir / "sources.md")
    edu = read_text(education_path) if education_path else ""
    social = read_text(social_path) if social_path else ""
    card_path = ROOT / "engine" / "runs" / hypothesis_id / "result_card.md"
    card = read_text(card_path)
    permalink = first_permalink(case + "\n" + social + "\n" + edu, hypothesis_id)
    assets = list_assets(case_dir)
    tweets = extract_tweet_blocks(thread)
    verdict = extract_verdict_line(case or card)

    lines: list[str] = []
    lines.append(f"# Shot list — {title}")
    lines.append("")
    lines.append(f"**Hypothesis:** `{hypothesis_id}`")
    lines.append(f"**Live card:** {permalink}")
    lines.append(f"**Result card:** `engine/runs/{hypothesis_id}/result_card.md`")
    lines.append(f"**Case dir:** `{case_dir.relative_to(ROOT) if case_dir.is_relative_to(ROOT) else case_dir}`")
    lines.append(f"**Verdict (package):** {verdict}")
    lines.append(f"**Target duration:** {duration_hint}")
    lines.append("")
    lines.append("## Integrity rules (on camera)")
    lines.append("- Do not invent numbers absent from the result card / case study.")
    lines.append("- State the verdict tier exactly (SUPPORTED / partial / supported_subset / …).")
    lines.append("- Deliver the steelman or caveats; do not hide pre-window fails.")
    lines.append("- End on the live card URL for audit, not just a slogan.")
    lines.append("")
    lines.append("## Assets on disk")
    if assets:
        for a in assets:
            lines.append(f"- `{a}`")
    else:
        lines.append("- _(no assets/ folder yet — use lower-thirds + live site screenshots)_")
    lines.append("")
    lines.append("## Scene board")
    lines.append("")
    lines.append("| # | Time | Visual | VO / lower-third | Asset |")
    lines.append("|---|---|---|---|---|")

    # Prefer thread beats; else education scene map; else generic 8-beat
    if tweets:
        n = len(tweets)
        slot = max(8, 60 // max(n, 1))
        t0 = 0
        for i, block in enumerate(tweets, 1):
            title_line = block.splitlines()[0].replace("#", "").strip()
            body = " ".join(
                ln.strip()
                for ln in block.splitlines()[1:]
                if ln.strip()
                and not ln.lower().startswith("character check")
                and not ln.lower().startswith("recommended image")
                and not ln.lower().startswith("alt text")
                and not ln.lower().startswith("image:")
            )
            body = re.sub(r"\s+", " ", body)[:180]
            img = ""
            m = re.search(r"(?:Recommended image|Image):\s*`?([^`\n]+)`?", block, re.I)
            if m and m.group(1).strip().lower() not in {"none", "n/a"}:
                img = m.group(1).strip().split()[0]
            t1 = t0 + slot
            lines.append(
                f"| {i} | {t0//60}:{t0%60:02d}–{t1//60}:{t1%60:02d} | {title_line} | {body} | {img or '—'} |"
            )
            t0 = t1
    else:
        generic = [
            ("Cold open", "Hook in one sentence", "cartoon / still"),
            ("Headline number", "State the primary statistic", "chart1"),
            ("Threshold honesty", "Pre-registered gate", "chart threshold"),
            ("Mechanism", "Plain English channel", "split screen"),
            ("Steelman", "Strongest counter", "text cards"),
            ("Caveat", "What this is not", "lower-third"),
            ("Thesis close", "Sharper than slogan", "return chart"),
            ("Live card CTA", permalink, "site screenshot"),
        ]
        for i, (vis, vo, asset) in enumerate(generic, 1):
            lines.append(f"| {i} | beat {i} | {vis} | {vo} | {asset} |")

    lines.append("")
    lines.append("## Short-form cut (45–75s)")
    lines.append("1. Cold open (3–5s)")
    lines.append("2. Hero chart / number (12s)")
    lines.append("3. Threshold or compounding beat (10s)")
    lines.append("4. Mechanism one-liner (10s)")
    lines.append("5. Steelman one-liner (8s)")
    lines.append("6. Live URL end card (5s)")
    lines.append("")
    lines.append("## Publish checklist")
    lines.append("- [ ] VO matches result card numbers")
    lines.append("- [ ] Verdict tier spoken or on-screen")
    lines.append("- [ ] Steelman included")
    lines.append("- [ ] Description has full permalink")
    lines.append("- [ ] Thread draft reviewed for character limits")
    lines.append("- [ ] Human publication gate signed")
    lines.append("")
    if social.strip():
        lines.append("## Social hooks source")
        lines.append(f"`{social_path}`" if social_path else "")
        lines.append("")
        # keep short excerpt
        excerpt = "\n".join(social.strip().splitlines()[:40])
        lines.append("```")
        lines.append(excerpt)
        lines.append("```")
        lines.append("")
    if edu.strip():
        lines.append("## Education brief source")
        lines.append(f"`{education_path}`" if education_path else "")
        lines.append("")
    if sources.strip():
        lines.append("## Sources file present")
        lines.append(f"`{(case_dir / 'sources.md').relative_to(ROOT) if (case_dir / 'sources.md').is_relative_to(ROOT) else case_dir / 'sources.md'}`")
        lines.append("")
    lines.append("---")
    lines.append("Generated by `scripts/generate_video_shot_list.py`. Numbers come from package files only.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hypothesis-id", required=True)
    ap.add_argument("--case-dir", required=True)
    ap.add_argument("--education", default=None)
    ap.add_argument("--social", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--duration", default="60–90s short or 6–9 min long-form")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    edu = Path(args.education) if args.education else None
    if edu and not edu.is_absolute():
        edu = ROOT / edu
    social = Path(args.social) if args.social else None
    if social and not social.is_absolute():
        social = ROOT / social

    title = args.title or args.hypothesis_id.replace("_", " ").title()
    text = build_shot_list(
        hypothesis_id=args.hypothesis_id,
        case_dir=Path(args.case_dir),
        education_path=edu,
        social_path=social,
        title=title,
        duration_hint=args.duration,
    )
    out_path.write_text(text, encoding="utf-8")
    try:
        display = out_path.relative_to(ROOT)
    except ValueError:
        display = out_path
    print(f"wrote {display} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
