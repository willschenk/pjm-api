import pytest

from pjm_api.unlock import clear_unlock_cache


@pytest.fixture(autouse=True)
def _reset_unlock_cache():
    clear_unlock_cache()
    yield
    clear_unlock_cache()
