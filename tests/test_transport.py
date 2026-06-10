import ssl
from unittest.mock import patch

import pytest

from pjm_api.auth import authenticate, create_session
from pjm_api.certs import CertificateKind, NormalizedCertificate
from pjm_api.config import load_settings
from pjm_api.exceptions import PJMAuthError, PJMTimeoutError
from pjm_api.transport import RawHTTPResponse, request


def test_request_http_error():
    import urllib.error

    req = urllib.request.Request("https://example.com")
    err = urllib.error.HTTPError("https://example.com", 401, "Unauthorized", {}, None)
    err.fp = __import__("io").BytesIO(b"denied")
    with patch("urllib.request.urlopen", side_effect=err):
        resp = request("GET", "https://example.com")
    assert resp.status_code == 401


def test_request_timeout():
    with patch("urllib.request.urlopen", side_effect=TimeoutError):
        with pytest.raises(PJMTimeoutError):
            request("GET", "https://example.com", timeout=1)


def test_create_session_and_authenticate(tmp_path):
    cert = tmp_path / "c.pem"
    cert.write_text("x")
    settings = load_settings(username="u", password="p", certificate=str(cert))
    normalized = NormalizedCertificate(
        CertificateKind.PEM_KEYPAIR, b"c", b"k", cert
    )
    with patch("pjm_api.auth.normalize_certificate", return_value=normalized), patch(
        "pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context()
    ), patch("pjm_api.auth.post_json", return_value={"tokenId": "abc"}):
        session, token = authenticate(settings)
        assert token == "abc"
        session2 = create_session(settings)
        assert session2 is not None
