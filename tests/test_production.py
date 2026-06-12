from unittest.mock import MagicMock, patch

import pytest

from pjm_api.cli_adapter import CliBackend
from pjm_api.config import load_settings
from pjm_api.exceptions import PJMOasisError
from pjm_api.oasis import OasisClient
from pjm_api.production import reset_production_warning_state


def _cli_settings(tmp_path, **kwargs):
    jar = tmp_path / "pjm-cli.jar"
    jar.write_bytes(b"x")
    return load_settings(
        username="u",
        password="p",
        certificate="/tmp/c.p12|pw",
        environment="PRODUCTION",
        backend="cli",
        jar_path=str(jar),
        downloads_dir=str(tmp_path / "dl"),
        use_credentials_file=False,
        **kwargs,
    )


def test_production_warning_prints_once(tmp_path, capsys):
    reset_production_warning_state()
    backend = CliBackend(_cli_settings(tmp_path))
    with patch.object(backend, "run_cli") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        assert backend.smoke_test(print_results=False)
        assert backend.smoke_test(print_results=False)

    captured = capsys.readouterr()
    assert captured.err.count("WARNING: PRODUCTION environment selected") == 1


def test_production_warning_can_be_disabled(tmp_path, capsys):
    reset_production_warning_state()
    backend = CliBackend(_cli_settings(tmp_path, disable_production_warning=True))
    with patch.object(backend, "run_cli") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        assert backend.smoke_test(print_results=False)

    captured = capsys.readouterr()
    assert "WARNING: PRODUCTION" not in captured.err


def test_native_blocks_production_input_template(tmp_path):
    reset_production_warning_state()
    cert = tmp_path / "cert.pem"
    cert.write_text("dummy")
    settings = load_settings(
        username="u",
        password="p",
        certificate=str(cert),
        environment="PRODUCTION",
        backend="native",
        disable_production_warning=True,
        use_credentials_file=False,
    )
    client = OasisClient(settings, MagicMock())

    with pytest.raises(PJMOasisError, match="Blocked PRODUCTION"):
        client.request("pjmtransreq", method="GET")
