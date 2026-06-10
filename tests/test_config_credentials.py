from pjm_api.config import load_settings
from pjm_api.credentials import StoredCredentials, save_credentials


def test_credentials_file_beats_env(monkeypatch, tmp_path):
    path = tmp_path / "credentials.enc"
    monkeypatch.setenv("PJM_CREDENTIALS_FILE", str(path))
    monkeypatch.setenv("PJM_USERNAME", "env-user")
    monkeypatch.setenv("PJM_PASSWORD", "env-pass")
    monkeypatch.setenv("PJM_MASTER_PASSWORD", "master")

    save_credentials(
        StoredCredentials("file-user", "file-pass", "/c.p12", "cp", "TRAIN"),
        "master",
        path,
    )

    settings = load_settings(prompt_unlock=False)
    assert settings.username == "file-user"
    assert settings.password == "file-pass"
