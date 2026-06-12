"""Production environment warning and write guards."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from pjm_api.exceptions import PJMOasisError
from pjm_api.templates import get_template_info

if TYPE_CHECKING:
    from pjm_api.config import PJMSettings

READ_METHODS = {"GET", "HEAD", "OPTIONS"}
PRODUCTION_WARNING = (
    "WARNING: PRODUCTION environment selected. Read-only OASIS requests are allowed, "
    "but write/reservation actions are blocked unless explicitly enabled."
)
PRODUCTION_WRITE_BLOCKED_FIX = (
    "Use TRAIN for write/reservation testing, or set PJM_ALLOW_PRODUCTION_WRITE=1 "
    "or pass --allow-production-write when you intentionally need production writes."
)

_production_warning_emitted = False


def reset_production_warning_state() -> None:
    """Reset process-local warning state for tests."""
    global _production_warning_emitted
    _production_warning_emitted = False


def is_production(settings: PJMSettings) -> bool:
    return settings.environment.upper() == "PRODUCTION"


def warn_if_production(settings: PJMSettings, *, action: str = "request") -> None:
    del action
    global _production_warning_emitted
    if not is_production(settings) or settings.disable_production_warning:
        return
    if _production_warning_emitted:
        return
    print(PRODUCTION_WARNING, file=sys.stderr)
    _production_warning_emitted = True


def _is_input_template(template: str) -> bool:
    info = get_template_info(template)
    return bool(info and info.type.lower() == "input")


def assert_production_action_allowed(
    settings: PJMSettings,
    *,
    method: str = "GET",
    template: str = "",
) -> None:
    if not is_production(settings):
        return

    warn_if_production(settings)
    if settings.allow_production_write:
        return

    method_upper = (method or "GET").upper()
    if method_upper not in READ_METHODS or (template and _is_input_template(template)):
        raise PJMOasisError(
            "Blocked PRODUCTION write/reservation action.",
            fix=PRODUCTION_WRITE_BLOCKED_FIX,
        )
