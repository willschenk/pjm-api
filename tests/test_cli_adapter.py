from unittest.mock import MagicMock, patch

from pjm_api.cli_adapter import CliBackend
from pjm_api.cli_zip import verify_checksum
from pjm_api.config import load_settings
from pjm_api.security import audit_subprocess_cmd, ensure_private_file


def test_cli_backend_smoke(tmp_path):
    jar = tmp_path / "pjm-cli.jar"
    jar.write_bytes(b"x")
    settings = load_settings(
        username="u",
        password="p",
        certificate="/tmp/c.p12|pw",
        backend="cli",
        jar_path=str(jar),
        downloads_dir=str(tmp_path / "dl"),
    )
    backend = CliBackend(settings)
    with patch.object(backend, "run_cli") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        assert backend.smoke_test(print_results=False)


def test_verify_checksum():
    data = b"hello"
    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    assert verify_checksum(data, digest)


def test_security_helpers(tmp_path):
    f = tmp_path / "secret.pem"
    f.write_text("x")
    ensure_private_file(f)
    masked = audit_subprocess_cmd(["-p", "secret"])
    assert "secret" not in masked
