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
    fix: str = ""


def _pfx_available() -> bool:
    try:
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False


def run_doctor(settings: PJMSettings, *, offline: bool = False) -> tuple[list[DoctorStep], bool]:
    steps: list[DoctorStep] = []

    cred_path = credentials_path()
    if credentials_exist(cred_path):
        steps.append(DoctorStep("credentials file", True, str(cred_path)))
    elif settings.username and settings.password and settings.certificate_path:
        steps.append(DoctorStep("credentials file", True, "from environment"))
    else:
        steps.append(
            DoctorStep(
                "credentials file",
                False,
                "not configured",
                fix="Run: pjm-api init",
            )
        )
        return steps, False

    cert = settings.certificate_path
    if not cert:
        steps.append(
            DoctorStep(
                "certificate file",
                False,
                "cert_path not set",
                fix="Run: pjm-api init and provide a .p12 or .pfx login certificate",
            )
        )
        return steps, False
    if not cert.exists():
        steps.append(
            DoctorStep(
                "certificate file",
                False,
                f"not found: {cert}",
                fix="Re-run pjm-api init with the correct certificate path",
            )
        )
        return steps, False

    if cert.suffix.lower() in {".p12", ".pfx"} and not _pfx_available():
        steps.append(
            DoctorStep(
                "certificate file",
                False,
                "PKCS#12 support not installed",
                fix='Install with: python -m pip install -e ".[pfx]"',
            )
        )
        return steps, False

    report = inspect_certificate(cert, settings.certificate_password)
    if not report.healthy:
        detail = report.errors[0] if report.errors else "certificate check failed"
        steps.append(
            DoctorStep(
                "certificate file",
                False,
                detail,
                fix="Re-run pjm-api init with a valid .p12 or .pfx login certificate",
            )
        )
        return steps, False

    expiry = ""
    if report.not_after:
        expiry = f"expires {report.not_after.date().isoformat()}"
    steps.append(DoctorStep("certificate file", True, expiry))

    if offline:
        return steps, True

    try:
        with OasisClient(settings) as client:
            client.authenticate()
        steps.append(DoctorStep("SSO authentication", True))
    except Exception as exc:
        steps.append(
            DoctorStep(
                "SSO authentication",
                False,
                str(exc),
                fix="Check PJM login details, CAM certificate approval, and environment",
            )
        )
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
                    fix="Authentication worked; check OASIS access and template parameters",
                )
            )
            return steps, False
    except Exception as exc:
        steps.append(
            DoctorStep(
                f"TRANSSERV smoke ({settings.environment})",
                False,
                str(exc),
                fix="Authentication worked; check OASIS access and template parameters",
            )
        )
        return steps, False

    return steps, True


def format_doctor_report(steps: list[DoctorStep], passed: bool, *, offline: bool = False) -> str:
    lines = []
    for i, step in enumerate(steps, 1):
        status = "OK" if step.ok else "FAIL"
        detail = f"  ({step.detail})" if step.detail else ""
        lines.append(f"[{i}/{len(steps)}] {step.name:30} {status}{detail}")
        if not step.ok and step.fix:
            lines.append(f"      Fix: {step.fix}")
    lines.append("")
    if passed and offline:
        lines.append("Offline checks passed. Network checks skipped.")
    elif passed:
        lines.append("All checks passed.")
    else:
        lines.append("Doctor failed. See docs/troubleshooting.md")
    return "\n".join(lines)
