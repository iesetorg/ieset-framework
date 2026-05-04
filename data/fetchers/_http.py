"""HTTP helpers for official sources with hostile edge protection.

Fetchers should prefer direct publisher APIs. This module is only for the
cases where the official URL is public but blocks plain Python clients with
403/Cloudflare/Akamai challenges. The fallback order is intentionally explicit:

1. ``requests`` with a browser-shaped user agent.
2. ``curl_cffi`` Chrome impersonation, if installed.
3. ZenRows, if ``ZENROWS_API_KEY`` is present.

Every caller still records the publisher's official URL in the FetchResult.
Callers can put the returned ``transport`` value in ``extra`` when they need
to disclose that a proxy transport was used.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlencode

import requests

try:  # optional; listed in data/fetchers/requirements.txt
    from curl_cffi import requests as cffi_requests
except Exception:  # noqa: BLE001
    cffi_requests = None

try:  # optional local .env support for ZenRows keys
    from dotenv import load_dotenv
except Exception:  # noqa: BLE001
    load_dotenv = None


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/csv,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class BlockedSourceError(RuntimeError):
    pass


@dataclass
class HttpPayload:
    content: bytes
    url: str
    status_code: int
    transport: str
    content_type: str | None = None

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _zenrows_url(url: str, *, js_render: bool = False, premium_proxy: bool = True) -> str:
    _load_env()
    key = os.environ.get("ZENROWS_API_KEY")
    if not key:
        raise BlockedSourceError("ZENROWS_API_KEY is not set")
    params = {
        "apikey": key,
        "url": url,
        "premium_proxy": "true" if premium_proxy else "false",
    }
    if js_render:
        params["js_render"] = "true"
    return "https://api.zenrows.com/v1/?" + urlencode(params)


def _err(exc: Exception) -> str:
    text = str(exc)
    key = os.environ.get("ZENROWS_API_KEY")
    if key:
        text = text.replace(key, "<ZENROWS_API_KEY>")
    return text


def _looks_blocked(status_code: int, body: bytes) -> bool:
    if status_code in {401, 403, 407, 429, 503}:
        return True
    sample = body[:8192].lower()
    return any(
        marker in sample
        for marker in (
            b"cloudflare",
            b"cf-chl",
            b"akamai",
            b"access denied",
            b"attention required",
            b"just a moment",
        )
    )


def get(
    url: str,
    *,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = 120,
    allow_zenrows: bool = True,
    zenrows_js_render: bool = False,
    return_http_errors: bool = False,
) -> HttpPayload:
    """GET ``url`` with explicit fallbacks for public-but-blocked sources.

    Non-blocked HTTP errors are not fallback candidates by default: a real 404
    should not silently become a proxy request. Callers that need to inspect
    ordinary HTTP status codes can opt into ``return_http_errors``.
    """
    merged_headers = {**DEFAULT_HEADERS, **dict(headers or {})}
    errors: list[str] = []

    try:
        r = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"requests:{type(exc).__name__}:{_err(exc)}")
    else:
        if not _looks_blocked(r.status_code, r.content):
            if r.status_code >= 400 and not return_http_errors:
                r.raise_for_status()
            return HttpPayload(
                content=r.content,
                url=r.url,
                status_code=r.status_code,
                transport="requests",
                content_type=r.headers.get("Content-Type"),
            )
        errors.append(f"requests:{r.status_code}")

    if cffi_requests is not None:
        try:
            r = cffi_requests.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=timeout,
                impersonate="chrome",
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"curl_cffi:{type(exc).__name__}:{_err(exc)}")
        else:
            if not _looks_blocked(r.status_code, r.content):
                if r.status_code >= 400 and not return_http_errors:
                    r.raise_for_status()
                return HttpPayload(
                    content=r.content,
                    url=r.url,
                    status_code=r.status_code,
                    transport="curl_cffi.chrome",
                    content_type=r.headers.get("Content-Type"),
                )
            errors.append(f"curl_cffi:{r.status_code}")

    if allow_zenrows:
        try:
            target = requests.Request("GET", url, params=params).prepare().url or url
            zr = requests.get(
                _zenrows_url(target, js_render=zenrows_js_render),
                timeout=max(timeout, 180),
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"zenrows:{type(exc).__name__}:{_err(exc)}")
        else:
            if not _looks_blocked(zr.status_code, zr.content):
                if zr.status_code >= 400 and not return_http_errors:
                    zr.raise_for_status()
                return HttpPayload(
                    content=zr.content,
                    url=target,
                    status_code=zr.status_code,
                    transport="zenrows.js" if zenrows_js_render else "zenrows",
                    content_type=zr.headers.get("Content-Type"),
                )
            errors.append(f"zenrows:{zr.status_code}")

    raise BlockedSourceError(f"blocked or failed GET for {url}: {', '.join(errors)}")
