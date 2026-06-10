"""PJM API exception hierarchy."""


class PJMError(Exception):
    """Base exception for PJM API errors."""

    def __init__(self, message: str, *, fix: str = "") -> None:
        super().__init__(message)
        self.fix = fix

    @property
    def hint(self) -> str:
        return self.fix


class PJMConfigError(PJMError):
    def __init__(self, message: str) -> None:
        super().__init__(message, fix="Run: pjm-api init")


class PJMCertificateError(PJMError):
    def __init__(self, message: str) -> None:
        super().__init__(message, fix="Run: pjm-api doctor")


class PJMAuthError(PJMError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            fix="Check username/password and CAM approval in Account Manager",
        )


class PJMSessionError(PJMError):
    def __init__(self, message: str) -> None:
        super().__init__(message, fix="Run: pjm-api doctor")


class PJMOasisError(PJMError):
    def __init__(self, message: str) -> None:
        super().__init__(message, fix="Run: pjm-api doctor")


class PJMTimeoutError(PJMError):
    def __init__(self, message: str) -> None:
        super().__init__(message, fix="Retry or increase PJM_TIMEOUT_SEC")
