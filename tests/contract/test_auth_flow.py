import ssl
from unittest.mock import patch

import pytest

from pjm_api.auth import PJMSession
from pjm_api.certs import CertificateKind, NormalizedCertificate
from pjm_api.config import load_settings
from pjm_api.transport import RawHTTPResponse


@pytest.fixture
def settings(tmp_path):
    cert = tmp_path / "c.pem"
    cert.write_text("x")
    return load_settings(username="user", password="pass", certificate=str(cert), backend="native")


@pytest.fixture
def normalized(tmp_path):
    return NormalizedCertificate(
        kind=CertificateKind.PEM_KEYPAIR,
        cert_pem=b"cert",
        key_pem=b"key",
        source_path=tmp_path / "c.pem",
    )


def test_auth_flow_token(settings, normalized):
    with (
        patch("pjm_api.auth.post_json") as mock_post,
        patch("pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context()),
    ):
        mock_post.return_value = {"tokenId": "contract-token"}
        session = PJMSession(settings, normalized)
        token = session.authenticate()
    assert token == "contract-token"
    assert session.cookie_header == "pjmauth=contract-token"


def test_logout_clears_token(settings, normalized):
    with (
        patch("pjm_api.auth.post_json") as mock_post,
        patch("pjm_api.auth.request"),
        patch("pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context()),
    ):
        mock_post.return_value = {"tokenId": "t"}
        session = PJMSession(settings, normalized)
        session.authenticate()
        session.logout()
    assert session.token is None


def test_oasis_request_cookie(settings, normalized):
    from pjm_api.oasis import OasisClient

    with (
        patch("pjm_api.auth.post_json") as mock_post,
        patch("pjm_api.oasis.request") as mock_req,
        patch("pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context()),
    ):
        mock_post.return_value = {"tokenId": "t"}
        mock_req.return_value = RawHTTPResponse(200, {}, b"OK")
        client = OasisClient(settings, PJMSession(settings, normalized))
        client.authenticate()
        client.request("TRANSSERV", {"OUTPUT_FORMAT": "DATA"})
        assert mock_req.called
        headers = mock_req.call_args.kwargs.get("headers") or mock_req.call_args[1].get("headers")
        assert headers["Cookie"] == "pjmauth=t"
