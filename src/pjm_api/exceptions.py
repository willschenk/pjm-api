"""PJM API exception hierarchy."""


class PJMError(Exception):
    """Base exception for PJM API errors."""

    def __init__(self, message: str, *, hint: str = "") -> None:
        super().__init__(message)
        self.hint = hint


class PJMConfigError(PJMError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, hint="Run: pjm-api config")


class PJMCertificateError(PJMError):
    """Raised when certificate handling fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, hint="Run: pjm-api cert-doctor")


class PJMAuthError(PJMError):
    """Raised when authentication fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, hint="Run: pjm-api auth-check")


class PJMSessionError(PJMError):
    """Raised when session/token handling fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, hint="Re-authenticate with pjm-api auth-check")


class PJMOasisError(PJMError):
    """Raised when OASIS template requests fail."""


class PJMTimeoutError(PJMError):
    """Raised when a request or subprocess times out."""
