import urllib.error

from pjm_api.cli_zip import install_cli_zip
from pjm_api.exceptions import PJMConfigError


def test_install_cli_zip_offline(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    try:
        install_cli_zip(tmp_path)
        assert False
    except PJMConfigError as exc:
        assert "Failed to download" in str(exc)
