"""Structured logging with secret redaction."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable

LOGGER_NAME = "pjm_api"

_SENSITIVE_PATTERNS = (
    re.compile(r"(password=)[^\s&]+", re.IGNORECASE),
    re.compile(r"(pjmauth=)[^;\s]+", re.IGNORECASE),
    re.compile(r"(tokenId[\"']?\s*:\s*[\"'])[^\"']+", re.IGNORECASE),
)


def redact_secrets(text: str, extra_values: Iterable[str] = ()) -> str:
    result = text
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub(r"\1***REDACTED***", result)
    for value in extra_values:
        if value:
            result = result.replace(value, "***REDACTED***")
    return result


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_secrets(original)


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging(*, verbose: bool = False, quiet: bool = False) -> None:
    logger = get_logger()
    if quiet:
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactingFormatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
