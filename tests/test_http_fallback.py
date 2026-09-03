from __future__ import annotations

from dataclasses import dataclass

import pytest

from data.fetchers import _http


@dataclass
class FakeResponse:
    content: bytes
    url: str
    status_code: int = 200
    content_type: str = "text/html"

    @property
    def headers(self) -> dict[str, str]:
        return {"Content-Type": self.content_type}

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_expected_json_falls_through_html_200_to_zenrows(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_get(url: str, **_kwargs) -> FakeResponse:
        calls.append(url)
        if url.startswith("https://api.zenrows.com/"):
            return FakeResponse(
                content=b'{"success": true, "data": []}',
                url=url,
                content_type="application/json",
            )
        return FakeResponse(content=b"<html>challenge</html>", url=url)

    monkeypatch.setattr(_http.requests, "get", fake_get)
    monkeypatch.setattr(_http, "cffi_requests", None)
    monkeypatch.setenv("ZENROWS_API_KEY", "test-key")

    payload = _http.get("https://publisher.example/data", expect_json=True)

    assert payload.transport == "zenrows"
    assert payload.text.startswith('{"success"')
    assert len(calls) == 2


def test_html_is_still_valid_when_json_is_not_required(monkeypatch: pytest.MonkeyPatch):
    def fake_get(url: str, **_kwargs) -> FakeResponse:
        return FakeResponse(content=b"<html>official page</html>", url=url)

    monkeypatch.setattr(_http.requests, "get", fake_get)
    monkeypatch.setattr(_http, "cffi_requests", None)

    payload = _http.get("https://publisher.example/page")

    assert payload.transport == "requests"
    assert payload.text.startswith("<html>")


def test_zenrows_country_is_added_without_changing_target_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ZENROWS_API_KEY", "test-key")

    url = _http._zenrows_url(
        "https://publisher.example/data?x=1",
        premium_proxy=True,
        proxy_country="ae",
    )

    assert "proxy_country=ae" in url
    assert "premium_proxy=true" in url
    assert "url=https%3A%2F%2Fpublisher.example%2Fdata%3Fx%3D1" in url
