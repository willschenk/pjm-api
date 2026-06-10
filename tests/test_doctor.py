from unittest.mock import patch

import pytest

from pjm_api.config import load_settings
from pjm_api.credentials import StoredCredentials, save_credentials
from pjm_api.doctor import run_doctor


@pytest.fixture
def creds_file(tmp_path, monkeypatch):
    path = tmp_path / "credentials.enc"
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    data = StoredCredentials("user", "pass", str(tmp_path / "cert.p12"), "cpw", "TRAIN")
    save_credentials(data, "master", path)
    (tmp_path / "cert.p12").write_bytes(b"\x30\x82\x00\x01")
    return path


def test_doctor_fails_missing_cert(creds_file, monkeypatch):
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")
    settings = load_settings(prompt_unlock=False)
    steps, passed = run_doctor(settings)
    assert not passed
    assert steps[0].ok


def test_doctor_fails_no_credentials(monkeypatch):
    monkeypatch.delenv("PJM_CREDENTIALS_FILE", raising=False)
    settings = load_settings(use_credentials_file=False)
    steps, passed = run_doctor(settings)
    assert not passed
    assert "init" in steps[0].detail


def test_doctor_sso_step(creds_file, monkeypatch, tmp_path):
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")
    settings = load_settings(prompt_unlock=False)

    with patch("pjm_api.doctor.inspect_certificate") as mock_inspect, patch(
        "pjm_api.doctor.OasisClient"
    ) as mock_client:
        mock_inspect.return_value.healthy = True
        mock_inspect.return_value.errors = ()
        mock_inspect.return_value.not_after = None
        mock_client.return_value.__enter__ = lambda s: s
        mock_client.return_value.__exit__ = lambda s, *a: None
        mock_client.return_value.authenticate.return_value = "tok"
        mock_client.return_value.smoke_transserv.return_value.ok = True
        mock_client.return_value.smoke_transserv.return_value.status_code = 200
        steps, passed = run_doctor(settings)
    assert any(s.name == "SSO authentication" for s in steps)
