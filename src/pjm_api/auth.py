"""PKI authentication and session management."""

from __future__ import annotations

import ssl
from types import TracebackType

from pjm_api.certs import NormalizedCertificate, create_ssl_context, normalize_certificate
from pjm_api.config import PJMSettings
from pjm_api.exceptions import PJMAuthError, PJMSessionError
from pjm_api.transport import post_json, request


class PJMSession:
    """Authenticated PJM session with mTLS and SSO token cookie."""

    def __init__(
        self,
        settings: PJMSettings,
        normalized_cert: NormalizedCertificate,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self.settings = settings
        self.normalized_cert = normalized_cert
        self.ssl_context = ssl_context or create_ssl_context(normalized_cert)
        self._token: str | None = None

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def cookie_header(self) -> str:
        if not self._token:
            raise PJMSessionError("Not authenticated")
        return f"pjmauth={self._token}"

    def authenticate(self) -> str:
        payload = post_json(
            self.settings.sso_url,
            ssl_context=self.ssl_context,
            headers={
                "X-OpenAM-Username": self.settings.username,
                "X-OpenAM-Password": self.settings.password,
            },
            timeout=self.settings.timeout_sec,
        )
        token = payload.get("tokenId")
        if not token:
            raise PJMAuthError(
                "No tokenId in authentication response. "
                "Check CAM certificate approval and environment."
            )
        self._token = str(token)
        return self._token

    def logout(self) -> None:
        if not self._token:
            return
        try:
            request(
                "POST",
                self.settings.logout_url,
                ssl_context=self.ssl_context,
                headers={"Cookie": self.cookie_header},
                timeout=self.settings.timeout_sec,
            )
        finally:
            self._token = None

    def __enter__(self) -> PJMSession:
        if not self.is_authenticated:
            self.authenticate()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.logout()


def authenticate(settings: PJMSettings) -> tuple[PJMSession, str]:
    if not settings.certificate_path:
        raise PJMAuthError("Certificate path is required")
    normalized = normalize_certificate(
        settings.certificate_path,
        settings.certificate_password,
    )
    session = PJMSession(settings, normalized)
    token = session.authenticate()
    return session, token


def create_session(settings: PJMSettings) -> PJMSession:
    if not settings.certificate_path:
        raise PJMAuthError("Certificate path is required")
    normalized = normalize_certificate(
        settings.certificate_path,
        settings.certificate_password,
    )
    return PJMSession(settings, normalized)
