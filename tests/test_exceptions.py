import pytest

from pjm_api.exceptions import (
    PJMAuthError,
    PJMCertificateError,
    PJMConfigError,
    PJMOasisError,
    PJMSessionError,
    PJMTimeoutError,
)


@pytest.mark.parametrize(
    ("exc_type", "default_fix"),
    [
        (PJMConfigError, "Run: pjm-api init"),
        (PJMCertificateError, "Run: pjm-api doctor"),
        (PJMAuthError, "Check username/password and CAM approval in Account Manager"),
        (PJMSessionError, "Run: pjm-api doctor"),
        (PJMOasisError, "Run: pjm-api doctor"),
        (PJMTimeoutError, "Retry or increase PJM_TIMEOUT_SEC"),
    ],
)
def test_exception_default_fix(exc_type, default_fix):
    exc = exc_type("something went wrong")
    assert exc.fix == default_fix
    assert exc.hint == default_fix


@pytest.mark.parametrize(
    "exc_type",
    [
        PJMConfigError,
        PJMCertificateError,
        PJMAuthError,
        PJMSessionError,
        PJMOasisError,
        PJMTimeoutError,
    ],
)
def test_exception_custom_fix_overrides_default(exc_type):
    exc = exc_type("something went wrong", fix="Do this instead")
    assert exc.fix == "Do this instead"
