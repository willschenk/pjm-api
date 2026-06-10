import json

import pytest

from pjm_api.credentials import (
    StoredCredentials,
    credentials_exist,
    load_credentials,
    rotate_master_password,
    save_credentials,
)
from pjm_api.exceptions import PJMConfigError


def test_encrypt_decrypt_roundtrip(tmp_path):
    path = tmp_path / "credentials.enc"
    data = StoredCredentials(
        username="user",
        password="pass",
        cert_path="/tmp/login.p12",
        cert_password="certpw",
        environment="TRAIN",
    )
    save_credentials(data, "master123", path)
    assert credentials_exist(path)
    loaded = load_credentials("master123", path)
    assert loaded.username == "user"
    assert loaded.password == "pass"
    assert loaded.cert_path == "/tmp/login.p12"
    assert loaded.environment == "TRAIN"


def test_wrong_master_password(tmp_path):
    path = tmp_path / "credentials.enc"
    data = StoredCredentials("u", "p", "/c.p12", "cp", "TRAIN")
    save_credentials(data, "correct", path)
    with pytest.raises(PJMConfigError, match="Wrong master password"):
        load_credentials("wrong", path)


def test_rotate_master_password(tmp_path):
    path = tmp_path / "credentials.enc"
    data = StoredCredentials("u", "p", "/c.p12", "cp", "TRAIN")
    save_credentials(data, "old", path)
    rotate_master_password("old", "new", path)
    loaded = load_credentials("new", path)
    assert loaded.username == "u"


def test_redacted_summary():
    data = StoredCredentials("user", "secret", "/cert.p12", "cpw", "TRAIN")
    summary = data.redacted_summary()
    assert summary["username"] == "user"
    assert summary["password"] == "***"
    assert "secret" not in json.dumps(summary)
