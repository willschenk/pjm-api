class PJMError(Exception):
    """Base exception for PJM API errors."""


class PJMAuthError(PJMError):
    """Raised when authentication fails."""
