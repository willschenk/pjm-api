from unittest.mock import patch

from pjm_api.cli import main


def test_cert_doctor_json(tmp_path):
    cert = tmp_path / "missing.p12"
    code = main(["cert-doctor", "--cert", str(cert), "--json", "--cert-password", "x"])
    assert code == 2


def test_cli_install_help():
    with patch("pjm_api.cli.install_cli_zip") as mock_install:
        mock_install.return_value = __import__("pathlib").Path("/tmp/pjm-cli.jar")
        code = main(["cli", "install", "--dir", "/tmp/pjm"])
    assert code == 0


def test_auth_check_native(tmp_path):
    cert = tmp_path / "c.pem"
    cert.write_bytes(b"-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n")
    with patch("pjm_api.cli.load_settings") as mock_load, patch(
        "pjm_api.cli.OasisClient"
    ) as mock_client:
        settings = mock_load.return_value
        settings.validate = lambda: None
        settings.backend = "native"
        settings.certificate_path = cert
        settings.password = "p"
        mock_client.return_value.__enter__ = lambda s: s
        mock_client.return_value.__exit__ = lambda s, *a: None
        mock_client.return_value.authenticate.return_value = "tok"
        code = main(["auth-check", "--cert", str(cert), "--password", "p"])
    assert code == 0
