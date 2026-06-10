"""Backward-compatible alias for OasisClient."""

from pjm_api.oasis import OasisClient

PJMClient = OasisClient


def create_client(**kwargs) -> OasisClient:
    from pjm_api.config import load_settings

    return OasisClient(load_settings(**kwargs))
