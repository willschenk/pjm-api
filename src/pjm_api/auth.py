from __future__ import annotations

from pathlib import Path
from typing import Tuple

import requests

from pjm_api.exceptions import PJMAuthError

SSO_URLS = {
    "production": "https://sso.pjm.com/access/authenticate/pjmauthcert",
    "train": "https://sotrain.pjm.com/access/authenticate/pjmauthcert",
}

CertPaths = Tuple[str | Path, str | Path]


def authenticate(
    username: str,
    password: str,
    certificate: CertPaths,
    *,
    environment: str = "production",
    session: requests.Session | None = None,
) -> str:
    """Authenticate with PJM SSO and return a session token."""
    if environment not in SSO_URLS:
        raise ValueError(f"Unknown environment: {environment!r}. Use 'production' or 'train'.")

    cert = (str(certificate[0]), str(certificate[1]))
    http = session or requests.Session()

    response = http.post(
        SSO_URLS[environment],
        headers={
            "X-OpenAM-Username": username,
            "X-OpenAM-Password": password,
        },
        cert=cert,
        timeout=30,
    )

    if not response.ok:
        raise PJMAuthError(
            f"Authentication failed ({response.status_code}): {response.text.strip()}"
        )

    payload = response.json()
    token = payload.get("tokenId")
    if not token:
        raise PJMAuthError(f"No tokenId in authentication response: {payload}")

    return token
