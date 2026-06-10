"""Setup health checks."""

from __future__ import annotations

from dataclasses import dataclass

from pjm_api.certs import inspect_certificate
from pjm_api.config import PJMSettings
from pjm_api.credentials import credentials_exist, credentials_path
from pjm_api.oasis import OasisClient


@dataclass
class DoctorStep:
    name: str
    ok: bool
    detail: str = ""


def _pfx_available() -> bool:
    try:
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False


def run_doctor(settings: PJMSettings) -> tuple[list[DoctorStep], bool]:
    steps: list[DoctorStep] = []

    cred_path = credentials_path()
    if credentials_exist(cred_path):
        steps.append(DoctorStep("credentials file", True, str(cred_path)))
    elif settings.username and settings.password and settings.certificate_path:
        steps.append(DoctorStep("credentials file", True, "from environment"))
    else:
        steps.append(DoctorStep("credentials file", False, "run: pjm-api init"))
        return steps, False

    cert = settings.certificate_path
    if not cert:
        steps.append(DoctorStep("certificate file", False, "cert_path not set"))
        return steps, False
    if not cert.exists():
        steps.append(DoctorStep("certificate file", False, f"not found: {cert}"))
        return steps, False

    if cert.suffix.lower() in {".p12", ".pfx"} and not _pfx_available():
        steps.append(
            DoctorStep(
                "certificate file",
                False,
                "install [pfx]: pip install pjm-api[pfx]",
            )
        )
        return steps, False

    report = inspect_certificate(cert, settings.certificate_password)
    if not report.healthy:
        detail = report.errors[0] if report.errors else "certificate check failed"
        steps.append(DoctorStep("certificate file", False, detail))
        return steps, False

    expiry = ""
    if report.not_after:
        expiry = f"expires {report.not_after.date().isoformat()}"
    steps.append(DoctorStep("certificate file", True, expiry))

    try:
        with OasisClient(settings) as client:
            client.authenticate()
        steps.append(DoctorStep("SSO authentication", True))
    except Exception as exc:
        steps.append(DoctorStep("SSO authentication", False, str(exc)))
        return steps, False

    try:
        with OasisClient(settings) as client:
            resp = client.smoke_transserv()
        if resp.ok:
            steps.append(DoctorStep(f"TRANSSERV smoke ({settings.environment})", True))
        else:
            steps.append(
                DoctorStep(
                    f"TRANSSERV smoke ({settings.environment})",
                    False,
                    f"HTTP {resp.status_code}",
                )
            )
            return steps, False
    except Exception as exc:
        steps.append(
            DoctorStep(f"TRANSSERV smoke ({settings.environment})", False, str(exc))
        )
        return steps, False

    return steps, True


def format_doctor_report(steps: list[DoctorStep], passed: bool) -> str:
    lines = []
    for i, step in enumerate(steps, 1):
        status = "OK" if step.ok else "FAIL"
        detail = f"  ({step.detail})" if step.detail else ""
        lines.append(f"[{i}/{len(steps)}] {step.name:30} {status}{detail}")
    lines.append("")
    lines.append("All checks passed." if passed else "Doctor failed. See docs/troubleshooting.md")
    return "\n".join(lines)
