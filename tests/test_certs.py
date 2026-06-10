import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from pjm_api.certs import (
    PUBLIC_CERT_FIX,
    PUBLIC_CERT_MESSAGE,
    CertificateKind,
    inspect_certificate,
    normalize_certificate,
)
from pjm_api.exceptions import PJMCertificateError


def _make_pem_keypair(include_key: bool = True) -> tuple[bytes, bytes]:
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
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    if include_key:
        key_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        combined = cert_pem + key_pem
        return combined, combined
    return cert_pem, cert_pem


def test_inspect_missing_file(tmp_path):
    report = inspect_certificate(tmp_path / "missing.p12")
    assert not report.healthy
    assert report.errors


def test_normalize_pem_keypair(tmp_path):
    cert_pem, _ = _make_pem_keypair(include_key=True)
    path = tmp_path / "combined.pem"
    path.write_bytes(cert_pem)
    normalized = normalize_certificate(path)
    assert normalized.kind == CertificateKind.PEM_KEYPAIR
    assert normalized.subject


def _assert_public_only_rejected(exc_info):
    assert str(exc_info.value) == PUBLIC_CERT_MESSAGE
    assert exc_info.value.fix == PUBLIC_CERT_FIX


@pytest.mark.parametrize("suffix", [".crt", ".cer", ".pem"])
def test_public_only_files_rejected(tmp_path, suffix):
    cert_pem, _ = _make_pem_keypair(include_key=False)
    path = tmp_path / f"public{suffix}"
    path.write_bytes(cert_pem)
    with pytest.raises(PJMCertificateError) as exc_info:
        normalize_certificate(path)
    _assert_public_only_rejected(exc_info)


def test_pem_with_private_key_not_public_only(tmp_path):
    cert_pem, _ = _make_pem_keypair(include_key=True)
    path = tmp_path / "login.pem"
    path.write_bytes(cert_pem)
    normalized = normalize_certificate(path)
    assert normalized.kind == CertificateKind.PEM_KEYPAIR


def test_missing_certificate_file_has_init_fix(tmp_path):
    path = tmp_path / "missing.p12"
    with pytest.raises(PJMCertificateError, match="not found") as exc_info:
        normalize_certificate(path)
    assert exc_info.value.fix == "Re-run pjm-api init with the correct certificate path"


def test_inspect_public_cert_warns(tmp_path):
    cert_pem, _ = _make_pem_keypair(include_key=False)
    path = tmp_path / "public.crt"
    path.write_bytes(cert_pem)
    report = inspect_certificate(path)
    assert any("Account Manager" in w for w in report.warnings)
    assert PUBLIC_CERT_MESSAGE in report.errors[0]
    assert not report.healthy


def test_inspect_json_output(tmp_path):
    cert_pem, _ = _make_pem_keypair()
    path = tmp_path / "key.pem"
    path.write_bytes(cert_pem)
    report = inspect_certificate(path)
    data = report.to_dict()
    assert "healthy" in data
    json.dumps(data)
