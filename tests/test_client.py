import ssl
from unittest.mock import MagicMock, patch

import pytest

from pjm_api.certs import CertificateKind, NormalizedCertificate
from pjm_api.config import load_settings
from pjm_api.oasis import OasisClient


@pytest.fixture
def settings(tmp_path):
    cert = tmp_path / "cert.pem"
    cert.write_text("dummy")
    return load_settings(username="u", password="p", certificate=str(cert))


@pytest.fixture
def normalized(tmp_path):
    return NormalizedCertificate(
        kind=CertificateKind.PEM_KEYPAIR,
        cert_pem=b"c",
        key_pem=b"k",
        source_path=tmp_path / "cert.pem",
    )


@patch("pjm_api.auth.post_json", return_value={"tokenId": "token123"})
@patch("pjm_api.oasis.request")
@patch("pjm_api.auth.create_ssl_context", return_value=ssl.create_default_context())
def test_client_authenticates_before_request(
    mock_ssl, mock_request, mock_auth, settings, normalized
):
    mock_request.return_value = MagicMock(status_code=200, content=b"ok", headers={})
    from pjm_api.auth import PJMSession

    session = PJMSession(settings, normalized)
    client = OasisClient(settings, session)
    client.request("TRANSSERV", {})
    mock_auth.assert_called_once()
