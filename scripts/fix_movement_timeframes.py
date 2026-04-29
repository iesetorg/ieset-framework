#!/usr/bin/env python3
"""Fix movement YAMLs whose timeframe.end says 'ongoing' but whose filename
encodes a real end year (e.g. cardoso_stabilisation_1994_2002.yaml).

Pattern: filename ends with ..._<start>_<end>.yaml where end is a 4-digit
year < current year. When YAML.timeframe.end is "ongoing" / "present" but
the filename says end=<year>, rewrite the YAML's end to <year>.

This is purely a data correction — these movements clearly ended, the
'ongoing' marker is a stub-mining artefact.
"""
from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
NOW = datetime.utcnow().year

# filename pattern with explicit end year as last token
TWO_YEAR_RE = re.compile(r"_(\d{4})_(\d{4})$")


def main() -> None:
    fixed = 0
    skipped = 0
    for path in sorted((REPO / "movements").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        stem = path.stem
        m = TWO_YEAR_RE.search(stem)
        if not m:
            continue
        start_yr, end_yr = int(m.group(1)), int(m.group(2))
        # only fix when the filename's end year is in the past
        if end_yr >= NOW:
            continue
        raw = path.read_text()
        header_lines = []
        for line in raw.splitlines():
            if line.startswith("#") or line.strip() == "":
                header_lines.append(line)
            else:
                break
        doc = yaml.safe_load(raw)
        if not isinstance(doc, dict):
            continue
        tf = doc.get("timeframe") or {}
        end_field = tf.get("end")
        if end_field in ("ongoing", "present", None):
            tf["end"] = end_yr
            doc["timeframe"] = tf
            body = yaml.safe_dump(doc, sort_keys=False, width=100, allow_unicode=True)
            path.write_text("\n".join(header_lines + [body]) if header_lines else body)
            fixed += 1
            print(f"  {path.name}: end ongoing → {end_yr}")
        else:
            skipped += 1

    print(f"\nfixed {fixed} timeframes; skipped {skipped} (already had explicit end)")


if __name__ == "__main__":
    main()
