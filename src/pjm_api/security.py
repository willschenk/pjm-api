"""Security helpers and audit notes."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterable
from pathlib import Path

SECRET_ENV_VARS = (
    "PJM_PASSWORD",
    "PJM_CERT_PASSWORD",
    "PJM_CLI_PASSWORD",
    "PJM_CLI_CERTIFICATE",
)

NEVER_COMMIT = (
    ".env",
    "test.py",
    "GUIDANCE.md",
    "*.p12",
    "*.pfx",
    "*.pem",
    "*.key",
)


def ensure_private_file(path: Path) -> None:
    """Set restrictive permissions on sensitive files (best effort)."""
    if not path.exists():
        return
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def scrub_env_from_process(keys: Iterable[str] = SECRET_ENV_VARS) -> None:
    for key in keys:
        if key in os.environ:
            os.environ[key] = "***"


def audit_subprocess_cmd(cmd: list[str]) -> list[str]:
    """Return cmd with known secret flags redacted for logging."""
    masked = list(cmd)
    for flag in ("-p", "-r"):
        if flag in masked:
            idx = masked.index(flag)
            if idx + 1 < len(masked):
                masked[idx + 1] = "***REDACTED***"
    return masked
