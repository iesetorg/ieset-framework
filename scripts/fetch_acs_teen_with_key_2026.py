#!/usr/bin/env python3
"""Access-only adapter for the frozen ACS teen-employment registration.

The Census API began requiring a key after the registration. This adapter
supplies CENSUS_API_KEY at request time without editing the registered
hypothesis, runner, requested fields, state keys, or verdict rule. The key is
never included in committed source URLs, raw files, or diagnostics.
"""
from __future__ import annotations

import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_us_state_minimum_wage_bite_teen_employment_2026 as frozen  # noqa: E402


def authenticated_download(canonical_url: str) -> bytes:
    key = os.getenv("CENSUS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("CENSUS_API_KEY is required by the Census API")
    request_url = canonical_url + "&key=" + urllib.parse.quote(key, safe="")
    request = urllib.request.Request(request_url, headers={"User-Agent": "IESET-evidence-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            if response.status != 200:
                raise RuntimeError("Census API did not return HTTP 200")
            body = response.read()
            if response.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise RuntimeError("Census API did not return JSON")
            return body
    except Exception as error:
        # Do not include the request URL: it carries the secret key.
        raise RuntimeError("Census API request failed; no source lock written") from None


def main() -> int:
    frozen.download = authenticated_download
    print(frozen.build_slice())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
