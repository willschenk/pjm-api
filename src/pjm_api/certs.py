"""Certificate inspection and normalization."""

from __future__ import annotations

import ssl
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pjm_api.exceptions import PJMCertificateError

PUBLIC_CERT_FIX = (
    "Use your .p12 or .pfx login file for runtime auth; "
    "upload public .cer/.crt only in Account Manager"
)
MISSING_CERT_FIX = "Re-run pjm-api init with the correct certificate path"

PKCS12_EXTENSIONS = {".p12", ".pfx"}
PUBLIC_EXTENSIONS = {".cer", ".crt", ".pem"}
EXPIRY_WARN_DAYS = 30


class CertificateKind(str, Enum):
    PKCS12_LOGIN = "pkcs12_login"
    PEM_KEYPAIR = "pem_keypair"
    PUBLIC_ONLY = "public_only"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NormalizedCertificate:
    kind: CertificateKind
    cert_pem: bytes
    key_pem: bytes
    source_path: Path
    subject: str = ""
    issuer: str = ""
    thumbprint: str = ""
    not_before: datetime | None = None
    not_after: datetime | None = None


@dataclass(frozen=True)
class CertInspectionReport:
    path: Path
    kind: CertificateKind
    subject: str
    issuer: str
    thumbprint: str
    not_before: datetime | None
    not_after: datetime | None
    days_until_expiry: int | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "kind": self.kind.value,
            "subject": self.subject,
            "issuer": self.issuer,
            "thumbprint": self.thumbprint,
            "not_before": self.not_before.isoformat() if self.not_before else None,
            "not_after": self.not_after.isoformat() if self.not_after else None,
            "days_until_expiry": self.days_until_expiry,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "healthy": self.healthy,
        }


def _detect_kind(path: Path) -> CertificateKind:
    suffix = path.suffix.lower()
    if suffix in PKCS12_EXTENSIONS:
        return CertificateKind.PKCS12_LOGIN
    if suffix in PUBLIC_EXTENSIONS:
        content = path.read_bytes()
        if b"BEGIN PRIVATE KEY" in content or b"BEGIN RSA PRIVATE KEY" in content:
            return CertificateKind.PEM_KEYPAIR
        return CertificateKind.PUBLIC_ONLY
    if path.exists() and path.read_bytes()[:2] == b"\x30\x82":
        return CertificateKind.PKCS12_LOGIN
    return CertificateKind.UNKNOWN


def _load_pkcs12(path: Path, password: str | None) -> tuple[bytes, bytes, bytes]:
    try:
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            pkcs12,
        )
    except ImportError as exc:
        raise PJMCertificateError(
            "PKCS#12 support requires the [pfx] extra: pip install pjm-api[pfx]"
        ) from exc

    data = path.read_bytes()
    pwd = (password or "").encode() or None
    try:
        key, cert, _additional = pkcs12.load_key_and_certificates(data, pwd)
    except Exception as exc:
        raise PJMCertificateError(f"Failed to decrypt PKCS#12 file: {exc}") from exc

    if key is None or cert is None:
        raise PJMCertificateError("PKCS#12 file does not contain both key and certificate")

    cert_pem = cert.public_bytes(Encoding.PEM)
    key_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    return cert_pem, key_pem, cert_pem


def _parse_pem_metadata(
    cert_pem: bytes,
) -> tuple[str, str, str, datetime | None, datetime | None]:
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes as crypto_hashes
    except ImportError:
        return "", "", "", None, None

    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    subject = cert.subject.rfc4514_string()
    issuer = cert.issuer.rfc4514_string()
    thumbprint = cert.fingerprint(crypto_hashes.SHA256()).hex()
    not_before = cert.not_valid_before_utc
    not_after = cert.not_valid_after_utc
    return subject, issuer, thumbprint, not_before, not_after


def _load_pem_pair(path: Path, key_path: Path | None = None) -> tuple[bytes, bytes]:
    cert_pem = path.read_bytes()
    if b"BEGIN PRIVATE KEY" in cert_pem or b"BEGIN RSA PRIVATE KEY" in cert_pem:
        return cert_pem, cert_pem

    if key_path and key_path.exists():
        return cert_pem, key_path.read_bytes()

    if b"BEGIN CERTIFICATE" in cert_pem and b"BEGIN" not in cert_pem.split(b"CERTIFICATE", 1)[1]:
        raise PJMCertificateError(
            "Public certificate only — use Account Manager upload, not runtime login",
            fix=PUBLIC_CERT_FIX,
        )
    raise PJMCertificateError("PEM file must contain private key or provide PJM_KEY_PATH")


def normalize_certificate(
    path: Path,
    password: str | None = None,
    *,
    key_path: Path | None = None,
) -> NormalizedCertificate:
    if not path.exists():
        raise PJMCertificateError(
            f"Certificate file not found: {path}",
            fix=MISSING_CERT_FIX,
        )

    kind = _detect_kind(path)
    if kind == CertificateKind.PKCS12_LOGIN:
        cert_pem, key_pem, _ = _load_pkcs12(path, password)
    elif kind == CertificateKind.PEM_KEYPAIR:
        cert_pem, key_pem = _load_pem_pair(path, key_path)
    elif kind == CertificateKind.PUBLIC_ONLY:
        raise PJMCertificateError(
            "Public certificate only — use Account Manager upload, not runtime login",
            fix=PUBLIC_CERT_FIX,
        )
    else:
        raise PJMCertificateError(f"Unknown certificate type: {path.suffix}")

    subject, issuer, thumbprint, not_before, not_after = _parse_pem_metadata(cert_pem)
    return NormalizedCertificate(
        kind=kind,
        cert_pem=cert_pem,
        key_pem=key_pem,
        source_path=path,
        subject=subject,
        issuer=issuer,
        thumbprint=thumbprint,
        not_before=not_before,
        not_after=not_after,
    )


def inspect_certificate(path: Path, password: str | None = None) -> CertInspectionReport:
    warnings: list[str] = []
    errors: list[str] = []

    if not path.exists():
        return CertInspectionReport(
            path=path,
            kind=CertificateKind.UNKNOWN,
            subject="",
            issuer="",
            thumbprint="",
            not_before=None,
            not_after=None,
            days_until_expiry=None,
            warnings=(),
            errors=(f"File not found: {path}",),
        )

    kind = _detect_kind(path)
    if kind == CertificateKind.PUBLIC_ONLY and path.suffix.lower() in {".cer", ".crt"}:
        warnings.append("Public certificate — for Account Manager upload, not runtime login")

    if kind == CertificateKind.PKCS12_LOGIN and not password:
        warnings.append("No certificate password configured for PKCS#12 file")

    try:
        normalized = normalize_certificate(path, password)
        subject = normalized.subject
        issuer = normalized.issuer
        thumbprint = normalized.thumbprint
        not_before = normalized.not_before
        not_after = normalized.not_after
    except PJMCertificateError as exc:
        return CertInspectionReport(
            path=path,
            kind=kind,
            subject="",
            issuer="",
            thumbprint="",
            not_before=None,
            not_after=None,
            days_until_expiry=None,
            warnings=tuple(warnings),
            errors=(str(exc),),
        )

    days_until_expiry: int | None = None
    if not_after:
        days_until_expiry = (not_after - datetime.now(timezone.utc)).days
        if days_until_expiry < 0:
            errors.append(f"Certificate expired {abs(days_until_expiry)} days ago")
        elif days_until_expiry < EXPIRY_WARN_DAYS:
            warnings.append(f"Certificate expires in {days_until_expiry} days")

    if kind == CertificateKind.PKCS12_LOGIN:
        warnings.append("Login-time PKCS#12 — correct shape for browserless authentication")

    return CertInspectionReport(
        path=path,
        kind=kind,
        subject=subject,
        issuer=issuer,
        thumbprint=thumbprint,
        not_before=not_before,
        not_after=not_after,
        days_until_expiry=days_until_expiry,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


@contextmanager
def temp_pem_material(cert: NormalizedCertificate) -> Iterator[tuple[Path, Path]]:
    """Write short-lived PEM files for SSLContext loading."""
    cert_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False)
    key_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False)
    cert_path = Path(cert_file.name)
    key_path = Path(key_file.name)
    try:
        cert_file.write(cert.cert_pem)
        key_file.write(cert.key_pem)
        cert_file.close()
        key_file.close()
        cert_path.chmod(0o600)
        key_path.chmod(0o600)
        yield cert_path, key_path
    finally:
        cert_path.unlink(missing_ok=True)
        key_path.unlink(missing_ok=True)


def create_ssl_context(cert: NormalizedCertificate) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    with temp_pem_material(cert) as (cert_path, key_path):
        ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    return ctx
