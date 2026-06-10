from pjm_api.exceptions import PJMCertificateError, PJMConfigError, PJMError
from pjm_api.logging_utils import redact_secrets
from pjm_api.security import audit_subprocess_cmd


def test_exception_fix_hints():
    assert PJMConfigError("x").fix == "Run: pjm-api init"
    assert PJMCertificateError("x").fix == "Run: pjm-api doctor"
    assert PJMError("x", fix="custom").fix == "custom"


def test_redact_secrets():
    text = redact_secrets("password=secret tokenId: abc")
    assert "secret" not in text
    assert "REDACTED" in text


def test_audit_subprocess_cmd():
    cmd = ["java", "-p", "secret", "-r", "cert|pw"]
    masked = audit_subprocess_cmd(cmd)
    assert "secret" not in masked
