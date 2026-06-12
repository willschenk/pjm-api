"""Native OASIS client."""

from __future__ import annotations

import ssl
import urllib.parse
from pathlib import Path
from typing import Any

from pjm_api.auth import PJMSession, create_session
from pjm_api.config import PJMSettings
from pjm_api.exceptions import PJMOasisError
from pjm_api.production import assert_production_action_allowed, warn_if_production
from pjm_api.response import OasisResponse
from pjm_api.transport import request

OUTPUT_FORMATS = {"CSV", "DATA", "XML", "JSON", "XLSX", "HTML", "XHTML", "PROTO"}


def normalize_template_name(template: str) -> str:
    value = (template or "").strip()
    if not value:
        raise PJMOasisError("template is required")
    return value.upper()


def build_template_url(base_url: str, template: str) -> str:
    name = normalize_template_name(template).lower()
    base = base_url if base_url.endswith("/") else f"{base_url}/"
    return urllib.parse.urljoin(base, f"rest/secure/{name}")


def build_query_params(
    template: str,
    params: dict[str, str] | None = None,
    *,
    output_format: str | None = None,
    continuation_flag: str | None = None,
    include_template_param: bool = True,
) -> dict[str, str]:
    qparams: dict[str, str] = {}
    if include_template_param:
        qparams["TEMPLATE"] = normalize_template_name(template)
    if output_format:
        fmt = output_format.upper()
        if fmt not in OUTPUT_FORMATS:
            valid = ", ".join(sorted(OUTPUT_FORMATS))
            raise PJMOasisError(f"Unknown OUTPUT_FORMAT {output_format!r}. Valid: {valid}")
        qparams["OUTPUT_FORMAT"] = fmt
    if continuation_flag is not None:
        qparams["CONTINUATION_FLAG"] = continuation_flag
    qparams.update(params or {})
    return qparams


class OasisClient:
    """Native Python OASIS client using PKI mTLS authentication."""

    def __init__(self, settings: PJMSettings, session: PJMSession | None = None) -> None:
        self.settings = settings
        self._session = session or create_session(settings)

    @property
    def session(self) -> PJMSession:
        return self._session

    @property
    def ssl_context(self) -> ssl.SSLContext:
        return self._session.ssl_context

    def authenticate(self) -> str:
        warn_if_production(self.settings, action="authenticate")
        return self._session.authenticate()

    def close(self) -> None:
        self._session.logout()

    def __enter__(self) -> OasisClient:
        if not self._session.is_authenticated:
            self.authenticate()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def request(
        self,
        template: str,
        params: dict[str, str] | None = None,
        *,
        method: str = "GET",
        output_format: str | None = None,
        continuation_flag: str = "N",
        action_override: str | None = None,
        body: bytes | None = None,
        reauth: bool = True,
    ) -> OasisResponse:
        assert_production_action_allowed(self.settings, method=method, template=template)
        if not self._session.is_authenticated:
            self.authenticate()

        url = action_override or build_template_url(self.settings.oasis_base_url, template)
        qparams = build_query_params(
            template,
            params,
            output_format=output_format,
            continuation_flag=continuation_flag,
        )

        method_upper = method.upper()
        if method_upper in ("GET", "POST") and qparams:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urllib.parse.urlencode(qparams)}"

        headers = {"Cookie": self._session.cookie_header}
        if body is not None:
            headers["Content-Type"] = "text/csv"

        response = request(
            method_upper,
            url,
            ssl_context=self.ssl_context,
            headers=headers,
            body=body,
            timeout=self.settings.timeout_sec,
        )

        if reauth and response.status_code == 401:
            self.authenticate()
            headers["Cookie"] = self._session.cookie_header
            response = request(
                method_upper,
                url,
                ssl_context=self.ssl_context,
                headers=headers,
                body=body,
                timeout=self.settings.timeout_sec,
            )

        if response.status_code >= 400:
            raise PJMOasisError(
                f"OASIS request failed ({response.status_code}): "
                f"{response.content.decode(errors='replace')[:500]}"
            )

        return OasisResponse(
            status_code=response.status_code,
            headers=response.headers,
            content=response.content,
            template=normalize_template_name(template),
            environment=self.settings.environment,
            output_format=output_format or qparams.get("OUTPUT_FORMAT"),
        )

    def put_csv(
        self, template: str, csv_path: Path | str, params: dict[str, str] | None = None
    ) -> OasisResponse:
        path = Path(csv_path)
        if not path.exists():
            raise PJMOasisError(f"CSV file not found: {path}")
        return self.request(template, params, method="PUT", body=path.read_bytes())

    def smoke_transserv(self) -> OasisResponse:
        return self.request(
            "TRANSSERV",
            {
                "OUTPUT_FORMAT": "DATA",
                "PRIMARY_PROVIDER_CODE": "PJM",
                "PRIMARY_PROVIDER_DUNS": "073647877",
                "RETURN_TZ": "EP",
                "VERSION": "3.3",
            },
        )

    def submit_transmission_request(
        self,
        csv_path: Path | str,
        params: dict[str, str] | None = None,
    ) -> OasisResponse:
        return self.put_csv("pjmtransreq", csv_path, params)
