from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pjm_api.cli import main


def _template_argv(**extra):
    argv = [
        "template",
        "TRANSSERV",
        "--username",
        "u",
        "--password",
        "p",
        "--cert",
        "/tmp/cert.pem",
    ]
    for key, value in extra.items():
        flag = f"--{key.replace('_', '-')}"
        argv.extend([flag, str(value)])
    return argv


def _template_settings(downloads_dir: Path):
    settings = MagicMock()
    settings.backend = "native"
    settings.validate = MagicMock()
    settings.downloads_dir = downloads_dir
    return settings


def _template_response(*, text: str = "template-preview", ok: bool = True):
    resp = MagicMock()
    resp.ok = ok
    resp.text.return_value = text
    resp.save.return_value = Path("/saved/path")
    return resp


def _run_template(argv, downloads_dir: Path, *, text: str = "template-preview", ok: bool = True):
    settings = _template_settings(downloads_dir)
    resp = _template_response(text=text, ok=ok)
    with patch("pjm_api.cli.load_settings", return_value=settings), patch(
        "pjm_api.cli.OasisClient"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = resp
        code = main(argv)
    return code, resp


def test_template_without_save_flags_does_not_write_file(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    code, resp = _run_template(_template_argv(), downloads)
    captured = capsys.readouterr()
    assert code == 0
    resp.save.assert_not_called()
    assert "Saved:" not in captured.out
    assert "template-preview" in captured.out
    resp.text.assert_called_once()


def test_template_default_preview_is_2000_chars(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    body = "x" * 3000
    code, _resp = _run_template(_template_argv(), downloads, text=body)
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out.strip() == "x" * 2000


def test_template_custom_preview_chars(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    body = "y" * 1000
    code, _resp = _run_template(_template_argv(preview_chars=500), downloads, text=body)
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out.strip() == "y" * 500


def test_template_zero_preview_chars_prints_no_body(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    body = "preview-body"
    code, _resp = _run_template(_template_argv(preview_chars=0), downloads, text=body, ok=False)
    captured = capsys.readouterr()
    assert code == 1
    assert "preview-body" not in captured.out


def test_template_negative_preview_chars_fails():
    with pytest.raises(SystemExit):
        main(_template_argv(preview_chars=-1))


def test_template_invalid_query_param_fails_before_request(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    argv = _template_argv()
    argv.extend(["--query-param", "BAD"])
    with patch("pjm_api.cli.load_settings", return_value=_template_settings(downloads)), patch(
        "pjm_api.cli.OasisClient"
    ) as mock_client_class:
        code = main(argv)
    captured = capsys.readouterr()
    assert code == 2
    mock_client_class.assert_not_called()
    assert "Invalid query parameter 'BAD'. Use KEY=VALUE." in captured.err


def test_template_outfile_saves_to_downloads_dir(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    argv = _template_argv(outfile="result.txt")
    code, resp = _run_template(argv, downloads)
    assert code == 0
    resp.save.assert_called_once_with(downloads / "result.txt")
    assert "Saved:" in capsys.readouterr().out


def test_template_save_uses_exact_path(tmp_path, capsys):
    downloads = tmp_path / "downloads"
    save_path = tmp_path / "result.txt"
    argv = _template_argv(save=str(save_path))
    code, resp = _run_template(argv, downloads)
    assert code == 0
    resp.save.assert_called_once_with(save_path)
    assert "Saved:" in capsys.readouterr().out


def test_doctor_prompts_for_credential_unlock():
    mock_settings = MagicMock()
    with patch("pjm_api.cli.load_settings", return_value=mock_settings) as mock_load, patch(
        "pjm_api.cli.run_doctor", return_value=([], False)
    ):
        main(["doctor"])
    assert mock_load.call_args.kwargs["prompt_unlock"] is True


def test_doctor_offline_passes_flag_to_run_doctor():
    mock_settings = MagicMock()
    with patch("pjm_api.cli.load_settings", return_value=mock_settings), patch(
        "pjm_api.cli.run_doctor", return_value=([], True)
    ) as mock_run, patch("pjm_api.cli.format_doctor_report", return_value="report") as mock_format:
        code = main(
            ["doctor", "--offline", "--username", "u", "--password", "p", "--cert", "/tmp/cert.pem"]
        )
    assert code == 0
    mock_run.assert_called_once_with(mock_settings, offline=True)
    mock_format.assert_called_once_with([], True, offline=True)


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
