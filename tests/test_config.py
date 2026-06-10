from pathlib import Path

import pytest

from pjm_api.config import (
    EXTENDED_OASIS_URLS,
    SSO_URLS,
    load_settings,
    parse_certificate,
    resolve_oasis_url,
    resolve_sso_url,
)
from pjm_api.exceptions import PJMConfigError


def test_parse_certificate_with_password():
    cert = Path("/tmp/cert.p12")
    path, password = parse_certificate(f"{cert}|secret")
    assert path == cert
    assert password == "secret"


def test_parse_certificate_path_only():
    cert = Path("/tmp/cert.p12")
    path, password = parse_certificate(str(cert))
    assert path == cert
    assert password is None


def test_resolve_oasis_url_train():
    assert resolve_oasis_url("train") == EXTENDED_OASIS_URLS["TRAIN"]


def test_resolve_sso_url_train():
    assert resolve_sso_url("TRAIN") == SSO_URLS["TRAIN"]


def test_load_settings_from_env(monkeypatch):
    monkeypatch.setenv("PJM_USERNAME", "user")
    monkeypatch.setenv("PJM_PASSWORD", "pass")
    monkeypatch.setenv("PJM_CERT", "/tmp/cert.p12|pw")
    monkeypatch.setenv("PJM_ENV", "TRAIN")
    monkeypatch.setenv("PJM_BACKEND", "native")

    settings = load_settings(use_credentials_file=False)
    assert settings.username == "user"
    assert settings.backend == "native"
    assert settings.sso_url == SSO_URLS["TRAIN"]


def test_legacy_cli_env_aliases(monkeypatch):
    legacy_cert = Path("/tmp/legacy.p12")
    monkeypatch.setenv("PJM_CLI_USER", "legacy-user")
    monkeypatch.setenv("PJM_CLI_PASSWORD", "legacy-pass")
    monkeypatch.setenv("PJM_CLI_CERTIFICATE", f"{legacy_cert}|legacy-pw")

    settings = load_settings(use_credentials_file=False)
    assert settings.username == "legacy-user"
    assert settings.certificate_legacy() == f"{legacy_cert}|legacy-pw"


def test_invalid_backend_raises(monkeypatch):
    monkeypatch.setenv("PJM_BACKEND", "invalid")
    with pytest.raises(PJMConfigError):
        load_settings()
