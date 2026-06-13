"""Unified configuration for cross-machine PJM integration."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from pjm_api.exceptions import PJMConfigError

Backend = Literal["native", "cli"]
DEFAULT_BACKEND: Backend = "cli"

OASIS_URLS: dict[str, str] = {
    "TRAIN": "https://oasisrefreshtrain.pjm.com/OASIS/",
    "PRODUCTION": "https://pjmoasis.pjm.com/OASIS/",
}

EXTENDED_OASIS_URLS: dict[str, str] = {
    **OASIS_URLS,
    "TEST": "",
    "STAGE": "",
}

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
DEFAULT_TIMEOUT_SEC = 120
_DEFAULT_CLI_JAR = Path("~/.pjm/cli/pjm-cli.jar")


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _default_cli_jar_path() -> Path | None:
    path = _DEFAULT_CLI_JAR.expanduser()
    return path if path.exists() else None


def parse_certificate(value: str) -> tuple[Path, str | None]:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Certificate path is required.")
    if "|" in raw:
        path_part, password_part = raw.split("|", 1)
        return Path(path_part.strip()).expanduser(), password_part or None
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
    return SSO_LOGOUT_URLS.get(environment.upper(), SSO_LOGOUT_URLS["PRODUCTION"])


def resolve_oasis_url(environment: str, custom_url: str = "") -> str:
    if custom_url:
        return custom_url if custom_url.endswith("/") else f"{custom_url}/"
    env_key = environment.upper()
    if env_key not in EXTENDED_OASIS_URLS:
        valid = ", ".join(sorted(EXTENDED_OASIS_URLS))
        raise PJMConfigError(f"Unknown environment {environment!r}. Valid: {valid}")
    url = EXTENDED_OASIS_URLS[env_key]
    if not url:
        raise PJMConfigError(
            f"OASIS URL for {env_key} is not public.",
            fix="Set PJM_OASIS_URL or pass --oasis-url for this private environment.",
        )
    return url


def get_env_url(env: str | None) -> str:
    return resolve_oasis_url(env or DEFAULT_ENVIRONMENT)


def _pfx_installed() -> bool:
    try:
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False


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
    disable_production_warning: bool
    allow_production_write: bool

    def certificate_legacy(self) -> str:
        if not self.certificate_path:
            return ""
        if self.certificate_password:
            return f"{self.certificate_path}|{self.certificate_password}"
        return str(self.certificate_path)

    def missing_for_backend(self) -> list[str]:
        missing: list[str] = []
        if not self.username:
            missing.append("username")
        if not self.password:
            missing.append("password")
        if not self.certificate_path:
            missing.append("cert_path")
        if self.backend == "cli" and not self.jar_path:
            missing.append("PJM_CLI_JAR_PATH")
        return missing

    def preflight(self) -> None:
        missing = self.missing_for_backend()
        if missing:
            raise PJMConfigError(f"Missing: {', '.join(missing)}. Run: pjm-api init")
        if not self.certificate_path:
            raise PJMConfigError("cert_path not set. Run: pjm-api init")
        if not self.certificate_path.exists():
            raise PJMConfigError(
                f"Certificate not found: {self.certificate_path}. Run: pjm-api init"
            )
        if (
            self.backend == "native"
            and self.certificate_path.suffix.lower() in {".p12", ".pfx"}
            and not _pfx_installed()
        ):
            raise PJMConfigError("PKCS#12 requires [pfx] extra: pip install pjm-api[pfx]")

    def validate(self) -> None:
        self.preflight()


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
    disable_production_warning: bool = False,
    allow_production_write: bool = False,
    use_credentials_file: bool = True,
    prompt_unlock: bool = True,
) -> PJMSettings:
    """Load settings: CLI args > encrypted file > .env > legacy aliases."""
    creds = None
    if use_credentials_file:
        from pjm_api.unlock import load_unlocked_credentials

        creds = load_unlocked_credentials(prompt=prompt_unlock)

    resolved_username = (
        username or (creds.username if creds else "") or _env("PJM_USERNAME", "PJM_CLI_USER")
    )
    resolved_password = (
        password or (creds.password if creds else "") or _env("PJM_PASSWORD", "PJM_CLI_PASSWORD")
    )
    resolved_environment = (
        environment
        or (creds.environment if creds else "")
        or _env("PJM_ENV", default=DEFAULT_ENVIRONMENT)
    ).upper()

    cert_password_override = certificate_password or _env("PJM_CERT_PASSWORD")
    cert_path: Path | None
    if creds and creds.cert_path:
        cert_path = Path(creds.cert_path).expanduser()
        cert_password = creds.cert_password or cert_password_override or None
    else:
        cert_raw = certificate or _env("PJM_CERT", "PJM_CLI_CERTIFICATE", "PJM_CERTIFICATE")
        if cert_raw:
            cert_path, cert_password = parse_certificate(cert_raw)
            if cert_password_override:
                cert_password = cert_password_override
        else:
            cert_path_raw = _env("PJM_CERT_PATH")
            cert_path = Path(cert_path_raw).expanduser() if cert_path_raw else None
            cert_password = cert_password_override or None

    resolved_backend = (backend or _env("PJM_BACKEND", default=DEFAULT_BACKEND)).lower()
    if resolved_backend not in ("native", "cli"):
        raise PJMConfigError("PJM_BACKEND must be 'native' or 'cli'.")

    custom_oasis = oasis_url or _env("PJM_OASIS_URL")
    custom_sso = sso_url or _env("PJM_SSO_URL")
    resolved_java = java_path or _env("PJM_CLI_JAVA_PATH") or shutil.which("java") or "java"
    resolved_jar = jar_path or _env("PJM_CLI_JAR_PATH")
    default_jar = _default_cli_jar_path() if not resolved_jar else None
    resolved_downloads = Path(
        downloads_dir or _env("PJM_CLI_DOWNLOADS", default=str(DEFAULT_DOWNLOADS))
    ).expanduser()
    resolved_timeout = timeout_sec or int(_env("PJM_TIMEOUT_SEC", default=str(DEFAULT_TIMEOUT_SEC)))
    resolved_disable_production_warning = disable_production_warning or _truthy(
        _env("PJM_DISABLE_PRODUCTION_WARNING")
    )
    resolved_allow_production_write = allow_production_write or _truthy(
        _env("PJM_ALLOW_PRODUCTION_WRITE")
    )

    return PJMSettings(
        username=resolved_username,
        password=resolved_password,
        certificate_path=cert_path,
        certificate_password=cert_password,
        environment=resolved_environment,
        oasis_base_url=resolve_oasis_url(resolved_environment, custom_oasis),
        sso_url=resolve_sso_url(resolved_environment, custom_sso),
        logout_url=resolve_logout_url(resolved_environment),
        backend=cast(Backend, resolved_backend),
        java_path=resolved_java,
        jar_path=Path(resolved_jar).expanduser() if resolved_jar else default_jar,
        downloads_dir=resolved_downloads,
        timeout_sec=resolved_timeout,
        disable_production_warning=resolved_disable_production_warning,
        allow_production_write=resolved_allow_production_write,
    )


def apply_settings_to_env(settings: PJMSettings) -> None:
    os.environ["PJM_CLI_USER"] = settings.username
    os.environ["PJM_CLI_PASSWORD"] = settings.password
    os.environ["PJM_CLI_CERTIFICATE"] = settings.certificate_legacy()
    os.environ["PJM_CLI_JAVA_PATH"] = settings.java_path
    os.environ["PJM_CLI_DOWNLOADS"] = str(settings.downloads_dir)
    if settings.jar_path:
        os.environ["PJM_CLI_JAR_PATH"] = str(settings.jar_path)
