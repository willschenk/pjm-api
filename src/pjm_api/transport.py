"""HTTP transport with mTLS support using stdlib only."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass

from pjm_api.exceptions import PJMAuthError, PJMTimeoutError
from pjm_api.logging_utils import redact_secrets

_AUTH_401_MESSAGE = (
    "Authentication failed (401). Check PJM username, password, environment, "
    "and CAM certificate approval."
)
_INVALID_JSON_MESSAGE = (
    "Authentication response was not JSON. Check the SSO URL and environment."
)
_BODY_SNIPPET_LIMIT = 200


def _safe_body_snippet(content: bytes) -> str:
    text = content.decode(errors="replace").strip()
    if not text:
        return "(empty response)"
    snippet = text[:_BODY_SNIPPET_LIMIT]
    if len(text) > _BODY_SNIPPET_LIMIT:
        snippet += "..."
    return redact_secrets(snippet)


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
        if response.status_code == 401:
            raise PJMAuthError(_AUTH_401_MESSAGE)
        raise PJMAuthError(
            f"Authentication failed ({response.status_code}): "
            f"{_safe_body_snippet(response.content)}"
        )
    try:
        payload = json.loads(response.content.decode())
    except json.JSONDecodeError as exc:
        raise PJMAuthError(_INVALID_JSON_MESSAGE) from exc
    if not isinstance(payload, dict):
        raise PJMAuthError(f"Unexpected auth response type: {type(payload)}")
    return payload
