"""CLI ZIP bootstrap with checksum verification."""

from __future__ import annotations

import hashlib
import io
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from pjm_api.exceptions import PJMConfigError

# Placeholder checksums — update when PJM publishes new CLI ZIP versions.
CLI_ZIP_URL = "https://www.pjm.com/-/media/etools/oasis/pjm-cli.zip"
KNOWN_SHA256: dict[str, str] = {}


def verify_checksum(data: bytes, expected_sha256: str) -> bool:
    digest = hashlib.sha256(data).hexdigest()
    return digest.lower() == expected_sha256.lower()


def install_cli_zip(target_dir: Path, *, force: bool = False) -> Path:
    target_dir = target_dir.expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    jar_path = target_dir / "pjm-cli.jar"
    if jar_path.exists() and not force:
        return jar_path

    try:
        with urllib.request.urlopen(CLI_ZIP_URL, timeout=120) as resp:
            data = resp.read()
    except urllib.error.URLError as exc:
        raise PJMConfigError(
            f"Failed to download PJM CLI ZIP: {exc.reason}. "
            "Download manually from PJM eTools and set PJM_CLI_JAR_PATH."
        ) from exc

    if KNOWN_SHA256:
        for _version, expected in KNOWN_SHA256.items():
            if verify_checksum(data, expected):
                break
        else:
            raise PJMConfigError("CLI ZIP checksum verification failed")

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        jar_members = [n for n in zf.namelist() if n.endswith("pjm-cli.jar")]
        if not jar_members:
            raise PJMConfigError("pjm-cli.jar not found in downloaded ZIP")
        jar_path.write_bytes(zf.read(jar_members[0]))

    return jar_path
