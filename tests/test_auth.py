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


def test_post_json_401_specific_message():
    with patch("pjm_api.transport.request") as mock_request:
        mock_request.return_value = RawHTTPResponse(401, {}, b"Unauthorized")
        with pytest.raises(PJMAuthError, match="Authentication failed \\(401\\)") as exc_info:
            post_json("https://example.com/auth")
    assert "CAM certificate approval" in str(exc_info.value)


def test_post_json_other_http_error_includes_status_and_body():
    body = b"Server error: upstream unavailable"
    with patch("pjm_api.transport.request") as mock_request:
        mock_request.return_value = RawHTTPResponse(503, {}, body)
        with pytest.raises(PJMAuthError, match="Authentication failed \\(503\\)") as exc_info:
            post_json("https://example.com/auth")
    assert "upstream unavailable" in str(exc_info.value)


def test_post_json_invalid_json_specific_message():
    with patch("pjm_api.transport.request") as mock_request:
        mock_request.return_value = RawHTTPResponse(200, {}, b"not-json")
        with pytest.raises(PJMAuthError, match="was not JSON") as exc_info:
            post_json("https://example.com/auth")
    assert "SSO URL" in str(exc_info.value)


def test_post_json_error_body_redacts_secrets():
    body = b'{"error":"bad","tokenId":"super-secret-token"}'
    with patch("pjm_api.transport.request") as mock_request:
        mock_request.return_value = RawHTTPResponse(500, {}, body)
        with pytest.raises(PJMAuthError) as exc_info:
            post_json("https://example.com/auth")
    message = str(exc_info.value)
    assert "super-secret-token" not in message
    assert "REDACTED" in message


def test_session_missing_token_id_specific_message(tmp_path):
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
        patch("pjm_api.auth.post_json", return_value={"message": "ok"}),
        patch("pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context()),
    ):
        session = PJMSession(settings, normalized)
        with pytest.raises(PJMAuthError, match="No tokenId") as exc_info:
            session.authenticate()
    assert "CAM certificate approval" in str(exc_info.value)
    assert '"message"' not in str(exc_info.value)


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
