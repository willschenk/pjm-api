from pjm_api.exceptions import PJMCertificateError, PJMConfigError
from pjm_api.logging_utils import redact_secrets
from pjm_api.security import audit_subprocess_cmd


def test_exception_hints():
    assert PJMConfigError("x").hint
    assert PJMCertificateError("x").hint


def test_redact_secrets():
    text = redact_secrets("password=secret tokenId: abc")
    assert "secret" not in text
    assert "REDACTED" in text


def test_audit_subprocess_cmd():
    cmd = ["java", "-p", "secret", "-r", "cert|pw"]
    masked = audit_subprocess_cmd(cmd)
    assert "secret" not in masked
