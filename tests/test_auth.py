import json
import ssl
from unittest.mock import patch

import pytest

from pjm_api.auth import PJMSession
from pjm_api.certs import CertificateKind, NormalizedCertificate
from pjm_api.config import load_settings
from pjm_api.exceptions import PJMAuthError
from pjm_api.transport import RawHTTPResponse, post_json


def test_post_json_success():
    payload = json.dumps({"tokenId": "abc123"}).encode()
    with patch("pjm_api.transport.request") as mock_request:
        mock_request.return_value = RawHTTPResponse(200, {}, payload)
        result = post_json("https://example.com/auth")
    assert result["tokenId"] == "abc123"


def test_post_json_failure():
    with patch("pjm_api.transport.request") as mock_request:
        mock_request.return_value = RawHTTPResponse(401, {}, b"Unauthorized")
        with pytest.raises(PJMAuthError):
            post_json("https://example.com/auth")


def test_session_authenticate(tmp_path):
    cert_pem = tmp_path / "c.pem"
    cert_pem.write_text("dummy")
    settings = load_settings(
        username="u", password="p", certificate=str(cert_pem), backend="native"
    )
    normalized = NormalizedCertificate(
        kind=CertificateKind.PEM_KEYPAIR,
        cert_pem=b"cert",
        key_pem=b"key",
        source_path=cert_pem,
    )
    with (
        patch("pjm_api.auth.post_json") as mock_post,
        patch("pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context()),
    ):
        mock_post.return_value = {"tokenId": "tok"}
        session = PJMSession(settings, normalized)
        token = session.authenticate()
    assert token == "tok"
    assert session.cookie_header == "pjmauth=tok"
