"""HTTP transport with mTLS support using stdlib only."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass

from pjm_api.exceptions import PJMAuthError, PJMTimeoutError


@dataclass(frozen=True)
class RawHTTPResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes


def request(
    method: str,
    url: str,
    *,
    ssl_context: ssl.SSLContext | None = None,
    headers: Mapping[str, str] | None = None,
    body: bytes | None = None,
    timeout: int = 30,
) -> RawHTTPResponse:
    req = urllib.request.Request(url, data=body, method=method.upper())
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=timeout) as resp:
            content = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return RawHTTPResponse(resp.status, resp_headers, content)
    except urllib.error.HTTPError as exc:
        content = exc.read()
        resp_headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return RawHTTPResponse(exc.code, resp_headers, content)
    except TimeoutError as exc:
        raise PJMTimeoutError(f"Request timed out after {timeout}s: {url}") from exc
    except urllib.error.URLError as exc:
        raise PJMAuthError(f"Request failed: {exc.reason}") from exc


def post_json(
    url: str,
    *,
    ssl_context: ssl.SSLContext | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = 30,
) -> dict:
    merged = dict(headers or {})
    merged.setdefault("Accept", "application/json")
    response = request("POST", url, ssl_context=ssl_context, headers=merged, timeout=timeout)
    if response.status_code >= 400:
        body = response.content.decode(errors="replace").strip()
        raise PJMAuthError(f"Authentication failed ({response.status_code}): {body}")
    try:
        payload = json.loads(response.content.decode())
    except json.JSONDecodeError as exc:
        raise PJMAuthError(f"Invalid JSON in auth response: {response.content!r}") from exc
    if not isinstance(payload, dict):
        raise PJMAuthError(f"Unexpected auth response type: {type(payload)}")
    return payload
