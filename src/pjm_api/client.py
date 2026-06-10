from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from pjm_api.auth import CertPaths, authenticate


class PJMClient:
    """Client for authenticated requests to PJM APIs."""

    def __init__(
        self,
        username: str,
        password: str,
        certificate: CertPaths,
        *,
        environment: str = "production",
        session: requests.Session | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.certificate = (Path(certificate[0]), Path(certificate[1]))
        self.environment = environment
        self._session = session or requests.Session()
        self._token: str | None = None

    @property
    def session(self) -> requests.Session:
        return self._session

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    def authenticate(self) -> str:
        """Authenticate with PJM SSO and store the session token."""
        self._token = authenticate(
            self.username,
            self.password,
            self.certificate,
            environment=self.environment,
            session=self._session,
        )
        return self._token

    def request(
        self,
        method: str,
        url: str,
        *,
        reauth: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        """Send an authenticated request to a PJM API endpoint."""
        if not self.is_authenticated:
            self.authenticate()

        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Cookie", f"pjmauth={self._token}")

        response = self._session.request(
            method,
            url,
            headers=headers,
            cert=(str(self.certificate[0]), str(self.certificate[1])),
            **kwargs,
        )

        if reauth and response.status_code == 401:
            self.authenticate()
            headers["Cookie"] = f"pjmauth={self._token}"
            response = self._session.request(
                method,
                url,
                headers=headers,
                cert=(str(self.certificate[0]), str(self.certificate[1])),
                **kwargs,
            )

        return response

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)
