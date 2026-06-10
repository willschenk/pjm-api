from unittest.mock import patch

from pjm_api.cli import main
from pjm_api.credentials import StoredCredentials, save_credentials


def test_init_command(tmp_path, monkeypatch):
    path = tmp_path / "credentials.enc"
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    inputs = iter(
        [
            "testuser",
            "testpass",
            "/tmp/cert.p12",
            "certpass",
            "TRAIN",
            "master",
            "master",
        ]
    )
    with patch("builtins.input", lambda _: next(inputs)), patch(
        "getpass.getpass", side_effect=["testpass", "certpass", "master", "master"]
    ):
        code = main(["init"])
    assert code == 0
    assert path.exists()


def test_doctor_no_credentials():
    code = main(["doctor"])
    assert code == 1


def test_credentials_show(tmp_path, monkeypatch):
    path = tmp_path / "credentials.enc"
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    save_credentials(
        StoredCredentials("user", "pass", "/c.p12", "cp", "TRAIN"),
        "master",
        path,
    )
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")
    code = main(["credentials", "show"])
    assert code == 0
