from unittest.mock import MagicMock, patch

import pytest

from pjm_api.cli_adapter import CliBackend
from pjm_api.cli_zip import verify_checksum
from pjm_api.config import load_settings
from pjm_api.exceptions import PJMOasisError
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


def test_cli_smoke_command_matches_working_shape(tmp_path):
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
    cmd = CliBackend(settings).build_smoke_test_cmd(outfile="smoke_train.txt")
    assert "-t" not in cmd
    assert cmd[cmd.index("-s") + 2] == "-a"
    assert cmd.index("-o") > max(i for i, part in enumerate(cmd) if part == "-q")
    assert cmd[-4:] == ["-o", "smoke_train.txt", "-z", "180000"]


def test_cli_blocks_production_write_by_default(tmp_path):
    jar = tmp_path / "pjm-cli.jar"
    jar.write_bytes(b"x")
    settings = load_settings(
        username="u",
        password="p",
        certificate="/tmp/c.p12|pw",
        environment="PRODUCTION",
        backend="cli",
        jar_path=str(jar),
        downloads_dir=str(tmp_path / "dl"),
        disable_production_warning=True,
    )
    backend = CliBackend(settings)
    with pytest.raises(PJMOasisError, match="Blocked PRODUCTION"):
        backend.run_template(template="pjmtransreq", method="PUT")


def test_cli_allows_production_write_with_override(tmp_path):
    jar = tmp_path / "pjm-cli.jar"
    jar.write_bytes(b"x")
    settings = load_settings(
        username="u",
        password="p",
        certificate="/tmp/c.p12|pw",
        environment="PRODUCTION",
        backend="cli",
        jar_path=str(jar),
        downloads_dir=str(tmp_path / "dl"),
        disable_production_warning=True,
        allow_production_write=True,
    )
    backend = CliBackend(settings)
    with patch.object(backend, "run_cli") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        result = backend.run_template(template="pjmtransreq", method="PUT")
    assert result.returncode == 0


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
