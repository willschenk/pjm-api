from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pjm_api.auth import authenticate
from pjm_api.client import PJMClient
from pjm_api.exceptions import PJMAuthError


def test_authenticate_returns_token():
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {"tokenId": "abc123"}

    session = MagicMock()
    session.post.return_value = mock_response

    token = authenticate(
        "user",
        "pass",
        ("/path/cert.crt", "/path/key.key"),
        session=session,
    )

    assert token == "abc123"
    session.post.assert_called_once()


def test_authenticate_raises_on_failure():
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    session = MagicMock()
    session.post.return_value = mock_response

    with pytest.raises(PJMAuthError, match="Authentication failed"):
        authenticate("user", "pass", ("/cert.crt", "/key.key"), session=session)


@patch("pjm_api.client.authenticate", return_value="token123")
def test_client_authenticates_before_request(mock_auth):
    client = PJMClient("user", "pass", (Path("/cert.crt"), Path("/key.key")))
    client._session.request = MagicMock(
        return_value=MagicMock(status_code=200, ok=True)
    )

    response = client.get("https://example.pjm.com/api")

    mock_auth.assert_called_once()
    assert response.status_code == 200
