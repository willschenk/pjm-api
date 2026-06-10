from dataclasses import replace
from unittest.mock import patch

import pytest

from pjm_api.config import load_settings
from pjm_api.credentials import StoredCredentials, save_credentials
from pjm_api.doctor import DoctorStep, format_doctor_report, run_doctor


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
    assert steps[0].fix == "Run: pjm-api init"


def test_doctor_failure_steps_include_fix(creds_file, monkeypatch):
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")
    settings = replace(load_settings(prompt_unlock=False), certificate_path=None)
    steps, passed = run_doctor(settings)
    assert not passed
    failed = [step for step in steps if not step.ok]
    assert failed
    assert all(step.fix for step in failed)
    assert failed[0].fix == "Run: pjm-api init and provide a .p12 or .pfx login certificate"


def test_format_doctor_report_shows_fix_for_failures():
    steps = [
        DoctorStep("credentials file", False, "not configured", fix="Run: pjm-api init"),
        DoctorStep("certificate file", True, "expires 2026-01-01"),
    ]
    report = format_doctor_report(steps, passed=False)
    assert "[1/2] credentials file" in report
    assert "FAIL  (not configured)" in report
    assert "      Fix: Run: pjm-api init" in report
    assert report.count("Fix:") == 1
    assert "Doctor failed. See docs/troubleshooting.md" in report


def test_format_doctor_report_success_has_no_fix_lines():
    steps = [
        DoctorStep("credentials file", True, "/tmp/credentials.enc"),
        DoctorStep("certificate file", True, "expires 2026-01-01"),
        DoctorStep("SSO authentication", True),
    ]
    report = format_doctor_report(steps, passed=True)
    assert "Fix:" not in report
    assert "All checks passed." in report


def test_format_doctor_report_offline_success():
    steps = [
        DoctorStep("credentials file", True, "/tmp/credentials.enc"),
        DoctorStep("certificate file", True, "expires 2026-01-01"),
    ]
    report = format_doctor_report(steps, passed=True, offline=True)
    assert "Offline checks passed. Network checks skipped." in report
    assert "All checks passed." not in report


def test_doctor_offline_skips_network_checks(creds_file, monkeypatch):
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")
    settings = load_settings(prompt_unlock=False)

    with patch("pjm_api.doctor.inspect_certificate") as mock_inspect, patch(
        "pjm_api.doctor.OasisClient"
    ) as mock_client:
        mock_inspect.return_value.healthy = True
        mock_inspect.return_value.errors = ()
        mock_inspect.return_value.not_after = None
        steps, passed = run_doctor(settings, offline=True)

    mock_client.assert_not_called()
    assert passed
    assert len(steps) == 2
    assert steps[0].name == "credentials file"
    assert steps[1].name == "certificate file"
    assert not any("SSO" in step.name or "TRANSSERV" in step.name for step in steps)


def test_doctor_offline_still_fails_local_errors(monkeypatch):
    monkeypatch.delenv("PJM_CREDENTIALS_FILE", raising=False)
    settings = load_settings(use_credentials_file=False)
    with patch("pjm_api.doctor.OasisClient") as mock_client:
        steps, passed = run_doctor(settings, offline=True)
    mock_client.assert_not_called()
    assert not passed
    assert steps[0].name == "credentials file"


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
