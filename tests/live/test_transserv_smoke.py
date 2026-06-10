import os

import pytest

pytestmark = pytest.mark.live


def _live_enabled() -> bool:
    return os.getenv("PJM_LIVE_TEST") == "1" and bool(os.getenv("PJM_USERNAME"))


@pytest.mark.skipif(
    not _live_enabled(), reason="Live tests require PJM_LIVE_TEST=1 and credentials"
)
def test_transserv_smoke_native():
    from pjm_api import OasisClient, load_settings

    settings = load_settings(environment="TRAIN", backend="native")
    with OasisClient(settings) as client:
        response = client.smoke_transserv()
    assert response.ok


@pytest.mark.skipif(not _live_enabled(), reason="Live tests require credentials")
def test_native_cli_parity():
    from pjm_api import OasisClient, load_settings
    from pjm_api.cli_adapter import CliBackend

    native_settings = load_settings(environment="TRAIN", backend="native")
    cli_settings = load_settings(environment="TRAIN", backend="cli")

    if not cli_settings.jar_path:
        pytest.skip("PJM_CLI_JAR_PATH not configured")

    with OasisClient(native_settings) as client:
        native_resp = client.smoke_transserv()

    backend = CliBackend(cli_settings)
    cli_ok = backend.smoke_test(print_results=False)
    assert native_resp.ok == cli_ok
