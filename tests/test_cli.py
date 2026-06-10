from unittest.mock import MagicMock, patch

from pjm_api.cli import main


def test_doctor_prompts_for_credential_unlock():
    mock_settings = MagicMock()
    with patch("pjm_api.cli.load_settings", return_value=mock_settings) as mock_load, patch(
        "pjm_api.cli.run_doctor", return_value=([], False)
    ):
        main(["doctor"])
    assert mock_load.call_args.kwargs["prompt_unlock"] is True


def test_cert_doctor_prompts_for_credential_unlock():
    mock_settings = MagicMock()
    mock_settings.certificate_path = "/tmp/cert.p12"
    mock_settings.certificate_password = "secret"
    with patch("pjm_api.cli.load_settings", return_value=mock_settings) as mock_load, patch(
        "pjm_api.cli.inspect_certificate"
    ) as mock_inspect:
        mock_inspect.return_value.healthy = True
        mock_inspect.return_value.path = "/tmp/cert.p12"
        mock_inspect.return_value.kind.value = "pkcs12"
        mock_inspect.return_value.subject = "CN=test"
        mock_inspect.return_value.not_after = None
        mock_inspect.return_value.warnings = []
        mock_inspect.return_value.errors = []
        main(["cert-doctor"])
    assert mock_load.call_args.kwargs["prompt_unlock"] is True


def test_config_does_not_prompt_for_credential_unlock():
    mock_settings = MagicMock()
    mock_settings.backend = "native"
    mock_settings.environment = "TRAIN"
    mock_settings.oasis_base_url = "https://example.test"
    mock_settings.username = ""
    mock_settings.password = ""
    mock_settings.certificate_path = ""
    mock_settings.missing_for_backend.return_value = []
    with patch("pjm_api.cli.load_settings", return_value=mock_settings) as mock_load, patch(
        "pjm_api.cli.credentials_exist", return_value=False
    ):
        main(["config"])
    assert mock_load.call_args.kwargs["prompt_unlock"] is False


def test_cli_config_exit_code():
    code = main(["config"])
    assert code in (0, 1)


def test_cli_templates_list():
    code = main(["templates", "list"])
    assert code == 0
