"""PJM API exception hierarchy."""

_DEFAULT_AUTH_FIX = "Check username/password and CAM approval in Account Manager"
_DEFAULT_TIMEOUT_FIX = "Retry or increase PJM_TIMEOUT_SEC"


class PJMError(Exception):
    """Base exception for PJM API errors."""

    def __init__(self, message: str, *, fix: str = "") -> None:
        super().__init__(message)
        self.fix = fix

    @property
    def hint(self) -> str:
        return self.fix


class PJMConfigError(PJMError):
    def __init__(self, message: str, *, fix: str | None = None) -> None:
        super().__init__(message, fix=fix if fix is not None else "Run: pjm-api init")


class PJMCertificateError(PJMError):
    def __init__(self, message: str, *, fix: str | None = None) -> None:
        super().__init__(message, fix=fix if fix is not None else "Run: pjm-api doctor")


class PJMAuthError(PJMError):
    def __init__(self, message: str, *, fix: str | None = None) -> None:
        super().__init__(
            message,
            fix=fix if fix is not None else _DEFAULT_AUTH_FIX,
        )


class PJMSessionError(PJMError):
    def __init__(self, message: str, *, fix: str | None = None) -> None:
        super().__init__(message, fix=fix if fix is not None else "Run: pjm-api doctor")


class PJMOasisError(PJMError):
    def __init__(self, message: str, *, fix: str | None = None) -> None:
        super().__init__(message, fix=fix if fix is not None else "Run: pjm-api doctor")


class PJMTimeoutError(PJMError):
    def __init__(self, message: str, *, fix: str | None = None) -> None:
        super().__init__(
            message,
            fix=fix if fix is not None else _DEFAULT_TIMEOUT_FIX,
        )
