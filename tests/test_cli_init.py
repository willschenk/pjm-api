from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from pjm_api.certs import CertificateKind, CertInspectionReport, inspect_certificate
from pjm_api.cli import main
from pjm_api.credentials import StoredCredentials, save_credentials


def _public_cert_pem() -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM)


def _healthy_report(path: Path) -> CertInspectionReport:
    not_after = datetime.now(timezone.utc) + timedelta(days=365)
    return CertInspectionReport(
        path=path,
        kind=CertificateKind.PKCS12_LOGIN,
        subject="CN=test",
        issuer="CN=test",
        thumbprint="abc123",
        not_before=datetime.now(timezone.utc) - timedelta(days=1),
        not_after=not_after,
        days_until_expiry=365,
        warnings=("Login-time PKCS#12 — correct shape for browserless authentication",),
        errors=(),
    )


def test_init_command(tmp_path, monkeypatch):
    path = tmp_path / "credentials.enc"
    cert_path = tmp_path / "login.p12"
    cert_path.write_bytes(b"\x30\x82\x00\x01")
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    inputs = iter(["testuser", str(cert_path), "TRAIN"])
    with patch("builtins.input", lambda _: next(inputs)), patch(
        "getpass.getpass", side_effect=["testpass", "certpass", "master", "master"]
    ), patch("pjm_api.cli.inspect_certificate", return_value=_healthy_report(cert_path)):
        code = main(["init"])
    assert code == 0
    assert path.exists()


def test_init_rejects_missing_certificate(tmp_path, monkeypatch, capsys):
    path = tmp_path / "credentials.enc"
    missing = tmp_path / "missing.p12"
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    inputs = iter(["testuser", str(missing)])
    with patch("builtins.input", lambda _: next(inputs)), patch(
        "getpass.getpass", side_effect=["testpass", "certpass"]
    ), patch("pjm_api.cli.save_credentials") as mock_save:
        code = main(["init"])
    assert code == 2
    assert not path.exists()
    mock_save.assert_not_called()
    assert "not found" in capsys.readouterr().err.lower()


def test_init_rejects_public_only_certificate(tmp_path, monkeypatch, capsys):
    cred_path = tmp_path / "credentials.enc"
    pub_path = tmp_path / "public.crt"
    pub_path.write_bytes(_public_cert_pem())
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(cred_path))
    inputs = iter(["testuser", str(pub_path)])
    with patch("builtins.input", lambda _: next(inputs)), patch(
        "getpass.getpass", side_effect=["testpass", "certpass"]
    ), patch("pjm_api.cli.save_credentials") as mock_save:
        code = main(["init"])
    assert code == 2
    assert not cred_path.exists()
    mock_save.assert_not_called()
    report = inspect_certificate(pub_path)
    assert not report.healthy
    stderr = capsys.readouterr().err
    for error in report.errors:
        assert error in stderr


def test_init_does_not_print_certificate_password(tmp_path, monkeypatch, capsys):
    path = tmp_path / "credentials.enc"
    cert_path = tmp_path / "login.p12"
    cert_path.write_bytes(b"\x30\x82\x00\x01")
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    cert_password = "super-secret-cert-pass"
    inputs = iter(["testuser", str(cert_path), "TRAIN"])
    with patch("builtins.input", lambda _: next(inputs)), patch(
        "getpass.getpass", side_effect=["testpass", cert_password, "master", "master"]
    ), patch("pjm_api.cli.inspect_certificate", return_value=_healthy_report(cert_path)):
        code = main(["init"])
    assert code == 0
    captured = capsys.readouterr()
    assert cert_password not in captured.out
    assert cert_password not in captured.err


def test_doctor_no_credentials():
    code = main(["doctor"])
    assert code == 1


def test_credentials_show(tmp_path, monkeypatch):
    path = tmp_path / "credentials.enc"
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    save_credentials(
        StoredCredentials("user", "pass", "/c.p12", "cp", "TRAIN"),
        "master",
        path,
    )
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")
    code = main(["credentials", "show"])
    assert code == 0
