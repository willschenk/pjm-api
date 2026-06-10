from unittest.mock import patch

from pjm_api.cli import main


def test_cli_config_exit_code():
    with patch("pjm_api.cli.load_settings") as mock_settings:
        settings = mock_settings.return_value
        settings.missing_for_backend.return_value = ["PJM_USERNAME"]
        settings.backend = "native"
        settings.environment = "TRAIN"
        settings.oasis_base_url = "https://example.com/"
        settings.sso_url = "https://sso.example.com/"
        settings.username = ""
        settings.password = ""
        settings.certificate_path = None
        settings.certificate_password = None
        settings.downloads_dir = "/tmp"
        settings.java_path = "java"
        settings.jar_path = None
        code = main(["config"])
    assert code == 1


def test_cli_templates_list():
    code = main(["templates", "list"])
    assert code == 0
