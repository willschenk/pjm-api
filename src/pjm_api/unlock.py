"""Master password session cache."""

from __future__ import annotations

import getpass
import os

from pjm_api.credentials import StoredCredentials, credentials_exist, load_credentials

_cached_master_password: str | None = None
_cached_credentials: StoredCredentials | None = None


def get_master_password(*, prompt: bool = True) -> str:
    global _cached_master_password
    env_pw = os.getenv("PJM_MASTER_PASSWORD", "")
    if env_pw:
        return env_pw
    if _cached_master_password:
        return _cached_master_password
    if not prompt:
        return ""
    _cached_master_password = getpass.getpass("Master password: ")
    return _cached_master_password


def load_unlocked_credentials(*, prompt: bool = True) -> StoredCredentials | None:
    global _cached_credentials
    if _cached_credentials:
        return _cached_credentials
    if not credentials_exist():
        return None
    password = get_master_password(prompt=prompt)
    if not password:
        return None
    _cached_credentials = load_credentials(password)
    return _cached_credentials


def clear_unlock_cache() -> None:
    global _cached_master_password, _cached_credentials
    _cached_master_password = None
    _cached_credentials = None
