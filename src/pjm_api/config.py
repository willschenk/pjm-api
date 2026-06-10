"""Unified configuration for cross-machine PJM integration."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pjm_api.exceptions import PJMConfigError

Backend = Literal["native", "cli"]

# Public OASIS environments documented by PJM.
OASIS_URLS: dict[str, str] = {
    "TRAIN": "https://oasis.ac1train.pjm.com/OASIS/",
    "PRODUCTION": "https://pjmoasis.pjm.com/OASIS/",
}

# Additional environments; available via explicit name or override.
EXTENDED_OASIS_URLS: dict[str, str] = {
    **OASIS_URLS,
    "TEST": "https://oasis.test.pjm.com/OASIS/",
    "STAGE": "https://oasis.ac1stage.pjm.com/OASIS/",
}

# SSO certificate-auth endpoints mapped from OASIS environment.
SSO_URLS: dict[str, str] = {
    "TRAIN": "https://sotrain.pjm.com/access/authenticate/pjmauthcert",
    "PRODUCTION": "https://sso.pjm.com/access/authenticate/pjmauthcert",
    "TEST": "https://sotrain.pjm.com/access/authenticate/pjmauthcert",
    "STAGE": "https://sotrain.pjm.com/access/authenticate/pjmauthcert",
}

SSO_LOGOUT_URLS: dict[str, str] = {
    "TRAIN": "https://sotrain.pjm.com/access/logout",
    "PRODUCTION": "https://sso.pjm.com/access/logout",
    "TEST": "https://sotrain.pjm.com/access/logout",
    "STAGE": "https://sotrain.pjm.com/access/logout",
}

DEFAULT_ENVIRONMENT = "TRAIN"
DEFAULT_DOWNLOADS = Path.cwd() / "downloads"
DEFAULT_TIMEOUT_SEC = 30


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def parse_certificate(value: str) -> tuple[Path, str | None]:
    """Parse `path` or legacy `path|password` certificate settings."""
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Certificate path is required.")

    if "|" in raw:
        path_part, password_part = raw.split("|", 1)
        path = Path(path_part.strip()).expanduser()
        password = password_part or None
        return path, password

    return Path(raw).expanduser(), None


def resolve_sso_url(environment: str, custom_url: str = "") -> str:
    if custom_url:
        return custom_url
    env_key = environment.upper()
    if env_key not in SSO_URLS:
        valid = ", ".join(sorted(SSO_URLS))
        raise PJMConfigError(f"Unknown SSO environment {environment!r}. Valid: {valid}")
    return SSO_URLS[env_key]


def resolve_logout_url(environment: str, custom_url: str = "") -> str:
    if custom_url:
        return custom_url
    env_key = environment.upper()
    return SSO_LOGOUT_URLS.get(env_key, SSO_LOGOUT_URLS["PRODUCTION"])


def resolve_oasis_url(environment: str, custom_url: str = "") -> str:
    if custom_url:
        return custom_url if custom_url.endswith("/") else f"{custom_url}/"
    env_key = environment.upper()
    if env_key not in EXTENDED_OASIS_URLS:
        valid = ", ".join(sorted(EXTENDED_OASIS_URLS))
        raise PJMConfigError(f"Unknown environment {environment!r}. Valid: {valid}")
    return EXTENDED_OASIS_URLS[env_key]


def get_env_url(env: str | None) -> str:
    """Return the base OASIS URL for an environment name."""
    return resolve_oasis_url(env or DEFAULT_ENVIRONMENT)


@dataclass(frozen=True)
class PJMSettings:
    username: str
    password: str
    certificate_path: Path | None
    certificate_password: str | None
    environment: str
    oasis_base_url: str
    sso_url: str
    logout_url: str
    backend: Backend
    java_path: str
    jar_path: Path | None
    downloads_dir: Path
    timeout_sec: int

    def certificate_legacy(self) -> str:
        if not self.certificate_path:
            return ""
        if self.certificate_password:
            return f"{self.certificate_path}|{self.certificate_password}"
        return str(self.certificate_path)

    def missing_for_backend(self) -> list[str]:
        missing: list[str] = []
        if not self.username:
            missing.append("PJM_USERNAME")
        if not self.password:
            missing.append("PJM_PASSWORD")
        if not self.certificate_path:
            missing.append("PJM_CERT")
        if self.backend == "cli" and not self.jar_path:
            missing.append("PJM_CLI_JAR_PATH")
        return missing

    def validate(self) -> None:
        missing = self.missing_for_backend()
        if missing:
            raise PJMConfigError("Missing required configuration: " + ", ".join(missing))
        if self.certificate_path and not self.certificate_path.exists():
            raise PJMConfigError(f"Certificate file not found: {self.certificate_path}")


def load_settings(
    *,
    username: str = "",
    password: str = "",
    certificate: str = "",
    certificate_password: str = "",
    environment: str = "",
    oasis_url: str = "",
    sso_url: str = "",
    backend: str = "",
    java_path: str = "",
    jar_path: str = "",
    downloads_dir: str = "",
    timeout_sec: int = 0,
) -> PJMSettings:
    """Load settings from explicit arguments with environment-variable fallbacks."""
    resolved_username = username or _env("PJM_USERNAME", "PJM_CLI_USER")
    resolved_password = password or _env("PJM_PASSWORD", "PJM_CLI_PASSWORD")

    cert_raw = certificate or _env("PJM_CERT", "PJM_CLI_CERTIFICATE", "PJM_CERTIFICATE")
    cert_password_override = certificate_password or _env("PJM_CERT_PASSWORD")

    if cert_raw:
        cert_path, cert_password = parse_certificate(cert_raw)
        if cert_password_override:
            cert_password = cert_password_override
    else:
        cert_path_raw = _env("PJM_CERT_PATH")
        cert_path = Path(cert_path_raw).expanduser() if cert_path_raw else None
        cert_password = cert_password_override or None

    resolved_environment = (environment or _env("PJM_ENV", default=DEFAULT_ENVIRONMENT)).upper()
    resolved_backend = (backend or _env("PJM_BACKEND", default="native")).lower()
    if resolved_backend not in ("native", "cli"):
        raise PJMConfigError("PJM_BACKEND must be 'native' or 'cli'.")

    custom_oasis = oasis_url or _env("PJM_OASIS_URL")
    custom_sso = sso_url or _env("PJM_SSO_URL")

    resolved_java = java_path or _env("PJM_CLI_JAVA_PATH") or shutil.which("java") or "java"
    resolved_jar = jar_path or _env("PJM_CLI_JAR_PATH")
    resolved_downloads = Path(
        downloads_dir or _env("PJM_CLI_DOWNLOADS", default=str(DEFAULT_DOWNLOADS))
    ).expanduser()
    resolved_timeout = timeout_sec or int(_env("PJM_TIMEOUT_SEC", default=str(DEFAULT_TIMEOUT_SEC)))

    return PJMSettings(
        username=resolved_username,
        password=resolved_password,
        certificate_path=cert_path,
        certificate_password=cert_password,
        environment=resolved_environment,
        oasis_base_url=resolve_oasis_url(resolved_environment, custom_oasis),
        sso_url=resolve_sso_url(resolved_environment, custom_sso),
        logout_url=resolve_logout_url(resolved_environment),
        backend=resolved_backend,  # type: ignore[assignment]
        java_path=resolved_java,
        jar_path=Path(resolved_jar).expanduser() if resolved_jar else None,
        downloads_dir=resolved_downloads,
        timeout_sec=resolved_timeout,
    )


def apply_settings_to_env(settings: PJMSettings) -> None:
    """Publish resolved settings to process env for legacy CLI modules."""
    os.environ["PJM_CLI_USER"] = settings.username
    os.environ["PJM_CLI_PASSWORD"] = settings.password
    os.environ["PJM_CLI_CERTIFICATE"] = settings.certificate_legacy()
    os.environ["PJM_CLI_JAVA_PATH"] = settings.java_path
    os.environ["PJM_CLI_DOWNLOADS"] = str(settings.downloads_dir)
    if settings.jar_path:
        os.environ["PJM_CLI_JAR_PATH"] = str(settings.jar_path)
