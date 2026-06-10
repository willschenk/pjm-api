"""Encrypted credentials storage."""

from __future__ import annotations

import base64
import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from pjm_api.exceptions import PJMConfigError

DEFAULT_CREDENTIALS_DIR = Path.home() / ".pjm"
DEFAULT_CREDENTIALS_FILE = DEFAULT_CREDENTIALS_DIR / "credentials.enc"
PBKDF2_ITERATIONS = 480_000


@dataclass
class StoredCredentials:
    username: str
    password: str
    cert_path: str
    cert_password: str
    environment: str = "TRAIN"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> StoredCredentials:
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            cert_path=data.get("cert_path", ""),
            cert_password=data.get("cert_password", ""),
            environment=data.get("environment", "TRAIN"),
        )

    def redacted_summary(self) -> dict[str, str]:
        return {
            "username": self.username or "(not set)",
            "cert_path": self.cert_path or "(not set)",
            "environment": self.environment,
            "password": "***" if self.password else "(not set)",
            "cert_password": "***" if self.cert_password else "(not set)",
        }


def credentials_path() -> Path:
    raw = os.getenv("PJM_CREDENTIALS_FILE", "")
    return Path(raw).expanduser() if raw else DEFAULT_CREDENTIALS_FILE


def credentials_exist(path: Path | None = None) -> bool:
    return (path or credentials_path()).is_file()


def _derive_key(master_password: str, salt: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise PJMConfigError(
            "Encryption requires the [pfx] extra: pip install pjm-api[pfx]"
        ) from exc

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))


def save_credentials(
    data: StoredCredentials,
    master_password: str,
    path: Path | None = None,
) -> Path:
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise PJMConfigError(
            "Encryption requires the [pfx] extra: pip install pjm-api[pfx]"
        ) from exc

    target = path or credentials_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    key = _derive_key(master_password, salt)
    fernet = Fernet(key)
    payload = json.dumps(data.to_dict()).encode()
    token = fernet.encrypt(payload)
    blob = base64.urlsafe_b64encode(salt) + b"." + token
    target.write_bytes(blob)
    target.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return target


def load_credentials(master_password: str, path: Path | None = None) -> StoredCredentials:
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError as exc:
        raise PJMConfigError(
            "Encryption requires the [pfx] extra: pip install pjm-api[pfx]"
        ) from exc

    target = path or credentials_path()
    if not target.is_file():
        raise PJMConfigError(f"Credentials file not found: {target}")

    blob = target.read_bytes()
    try:
        salt_b64, token = blob.split(b".", 1)
        salt = base64.urlsafe_b64decode(salt_b64)
        key = _derive_key(master_password, salt)
        payload = Fernet(key).decrypt(token)
    except (InvalidToken, ValueError) as exc:
        raise PJMConfigError("Wrong master password or corrupted credentials file.") from exc

    return StoredCredentials.from_dict(json.loads(payload.decode()))


def rotate_master_password(
    old_password: str,
    new_password: str,
    path: Path | None = None,
) -> Path:
    data = load_credentials(old_password, path)
    return save_credentials(data, new_password, path)
